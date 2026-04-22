"""Graph management layer for Intelligent Storage Nexus.

Phase 4A: Apache AGE Cypher integration with NetworkX fallback
Provides a unified interface for graph operations regardless of backend.
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional

import networkx as nx
import numpy as np

from config import EMBED_MODEL, GRAPH_AUTO_TUNE_THRESHOLD, GRAPH_MIN_EDGE_SIM_THRESHOLD
from db import get_conn

logger = logging.getLogger(__name__)


class GraphManager:
    """Manages knowledge graph operations using AGE (preferred) or NetworkX (fallback)."""

    def __init__(self):
        self._use_age = False
        self._graph: Optional[nx.Graph] = None
        self._graph_built = False
        self._age_available = False
        self._build_task: Optional[asyncio.Task[None]] = None
        self._build_lock = asyncio.Lock()
        self._build_started_at: Optional[float] = None
        self._build_completed_at: Optional[float] = None
        self._last_build_error: Optional[str] = None

        self._node_limit = int(os.environ.get("ISN_GRAPH_NODE_LIMIT", "5000"))
        self._embedding_limit = int(os.environ.get("ISN_GRAPH_EMBED_LIMIT", "1000"))
        self._edge_window = int(os.environ.get("ISN_GRAPH_EDGE_WINDOW", "10"))
        self._edge_similarity_threshold = float(
            os.environ.get("ISN_GRAPH_EDGE_SIM_THRESHOLD", "0.85")
        )
        self._base_edge_similarity_threshold = self._edge_similarity_threshold
        self._active_edge_similarity_threshold = self._edge_similarity_threshold
        self._auto_tune_threshold = GRAPH_AUTO_TUNE_THRESHOLD
        self._min_edge_similarity_threshold = GRAPH_MIN_EDGE_SIM_THRESHOLD
        self._auto_tune_applied = False
        self._query_wait_timeout = float(
            os.environ.get("ISN_GRAPH_QUERY_WAIT_TIMEOUT_SEC", "5.0")
        )

    async def initialize(self) -> bool:
        """Initialize graph backend. Try AGE first, fallback to NetworkX.

        Returns:
            True if initialization succeeded
        """
        # Try AGE first
        try:
            async with get_conn() as conn:
                # Try to load AGE extension
                await conn.execute("LOAD 'age';")
                await conn.execute("SET search_path = ag_catalog, public;")

                graph_exists = await conn.fetchval(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM ag_catalog.ag_graph WHERE name = 'storage_graph'
                    )
                    """
                )
                if not graph_exists:
                    await conn.fetchval(
                        "SELECT ag_catalog.create_graph('storage_graph')"
                    )

                # Test with a simple query
                await conn.fetchval(
                    """SELECT * FROM cypher('storage_graph', $$RETURN 1$$) as (v agtype)"""
                )

                self._use_age = True
                self._age_available = True
                logger.info("✅ Graph: Using Apache AGE Cypher backend")
                return True

        except Exception as e:
            logger.warning(
                f"⚠️  Graph: AGE not available ({e}), using NetworkX fallback"
            )
            self._use_age = False
            self._age_available = False

            # Build NetworkX graph in background (non-blocking startup).
            self._start_background_build()
            return True

    def _start_background_build(self) -> None:
        """Kick off graph build if no build task is running."""
        if self._graph_built:
            return

        if self._build_task and not self._build_task.done():
            return

        self._build_task = asyncio.create_task(self._build_networkx_graph())

    async def _ensure_networkx_graph_ready(self, wait_timeout: Optional[float]) -> None:
        """Ensure a NetworkX graph exists; optionally wait for build completion."""
        if self._graph_built:
            return

        self._start_background_build()
        if wait_timeout is None or self._build_task is None:
            return

        try:
            await asyncio.wait_for(self._build_task, timeout=wait_timeout)
        except asyncio.TimeoutError:
            logger.debug(
                f"Graph build still in progress after {wait_timeout:.1f}s timeout"
            )
        except Exception as e:
            logger.error(f"Graph build failed: {e}")

    @staticmethod
    def _parse_embedding(raw_embedding: Any) -> np.ndarray:
        """Normalize DB embedding values to float32 arrays."""
        if isinstance(raw_embedding, np.ndarray):
            return raw_embedding.astype(np.float32)
        if hasattr(raw_embedding, "tolist"):
            try:
                return np.array(raw_embedding.tolist(), dtype=np.float32)
            except Exception:
                return np.array([], dtype=np.float32)
        if isinstance(raw_embedding, (list, tuple)):
            return np.array(raw_embedding, dtype=np.float32)
        if isinstance(raw_embedding, str):
            return np.fromstring(raw_embedding.strip("[]"), sep=",", dtype=np.float32)
        return np.array([], dtype=np.float32)

    def _resolve_edge_threshold(self, total_embeddings: int) -> float:
        """Select a practical threshold for fallback graph construction."""
        base = self._base_edge_similarity_threshold
        if not self._auto_tune_threshold:
            self._auto_tune_applied = False
            return base

        tuned = base
        # Large corpora often need lower thresholds to avoid sparse, unhelpful graphs.
        if total_embeddings >= 100_000:
            tuned = min(base, 0.74)
        elif total_embeddings >= 50_000:
            tuned = min(base, 0.76)
        elif total_embeddings >= 20_000:
            tuned = min(base, 0.78)
        elif total_embeddings >= 5_000:
            tuned = min(base, 0.80)
        elif total_embeddings >= 1_000:
            tuned = min(base, 0.82)

        tuned = max(self._min_edge_similarity_threshold, tuned)
        self._auto_tune_applied = abs(tuned - base) > 1e-9
        return tuned

    async def _build_networkx_graph(self) -> None:
        """Build NetworkX graph from database."""
        async with self._build_lock:
            if self._graph_built:
                return

            self._build_started_at = time.time()
            self._build_completed_at = None
            self._last_build_error = None
            logger.info("Building NetworkX graph from embeddings...")

            graph = nx.Graph()

            try:
                async with get_conn() as conn:
                    # Add file nodes
                    rows = await conn.fetch(
                        """
                        SELECT DISTINCT f.id, f.path, f.name, f.extension
                        FROM files f
                        INNER JOIN file_embeddings fe ON f.id = fe.file_id
                        WHERE COALESCE(fe.model, $2) = $2
                        LIMIT $1
                    """,
                        self._node_limit,
                        EMBED_MODEL,
                    )

                    for row in rows:
                        graph.add_node(
                            row["id"],
                            name=row["name"],
                            path=row["path"],
                            extension=row["extension"],
                        )

                    logger.info(f"Added {len(rows)} nodes to NetworkX graph")

                    # Add edges based on local similarity window.
                    total_embeddings = await conn.fetchval(
                        "SELECT COUNT(*) FROM file_embeddings WHERE COALESCE(model, $1) = $1",
                        EMBED_MODEL,
                    )
                    threshold = self._resolve_edge_threshold(total_embeddings or 0)
                    self._active_edge_similarity_threshold = threshold

                    rows = await conn.fetch(
                        """
                        SELECT f.id, fe.embedding
                        FROM files f
                        INNER JOIN file_embeddings fe ON f.id = fe.file_id
                        WHERE COALESCE(fe.model, $2) = $2
                        ORDER BY f.id
                        LIMIT $1
                    """,
                        self._embedding_limit,
                        EMBED_MODEL,
                    )

                    ids: List[int] = []
                    vectors: List[np.ndarray] = []
                    for row in rows:
                        emb = self._parse_embedding(row["embedding"])
                        if emb.size == 0:
                            continue
                        ids.append(row["id"])
                        vectors.append(emb)

                    edges_added = 0
                    if vectors:
                        matrix = np.vstack(vectors).astype(np.float32)
                        norms = np.linalg.norm(matrix, axis=1)
                        n_items = matrix.shape[0]
                        for i in range(n_items):
                            end = min(n_items, i + self._edge_window + 1)
                            if i + 1 >= end:
                                continue

                            candidate_slice = matrix[i + 1 : end]
                            denom = norms[i] * norms[i + 1 : end]
                            dot = candidate_slice @ matrix[i]

                            for offset, (score, denom_value) in enumerate(
                                zip(dot, denom), start=1
                            ):
                                if denom_value == 0.0:
                                    continue
                                similarity = float(score / denom_value)
                                if similarity >= threshold:
                                    graph.add_edge(
                                        ids[i],
                                        ids[i + offset],
                                        weight=similarity,
                                    )
                                    edges_added += 1

                    # If graph is still sparse, relax threshold one more step.
                    if (
                        vectors
                        and edges_added == 0
                        and threshold > self._min_edge_similarity_threshold
                    ):
                        relaxed_threshold = max(
                            self._min_edge_similarity_threshold,
                            threshold - 0.05,
                        )
                        if relaxed_threshold < threshold:
                            logger.info(
                                "Relaxing graph threshold from %.2f to %.2f due to sparse edges",
                                threshold,
                                relaxed_threshold,
                            )
                            self._active_edge_similarity_threshold = relaxed_threshold
                            threshold = relaxed_threshold
                            n_items = len(ids)
                            for i in range(n_items):
                                end = min(n_items, i + self._edge_window + 1)
                                if i + 1 >= end:
                                    continue

                                base_vec = vectors[i]
                                base_norm = np.linalg.norm(base_vec)
                                if base_norm == 0.0:
                                    continue

                                for j in range(i + 1, end):
                                    compare_vec = vectors[j]
                                    compare_norm = np.linalg.norm(compare_vec)
                                    if compare_norm == 0.0:
                                        continue

                                    similarity = float(
                                        (base_vec @ compare_vec)
                                        / (base_norm * compare_norm)
                                    )
                                    if similarity >= threshold:
                                        graph.add_edge(ids[i], ids[j], weight=similarity)
                                        edges_added += 1

                    logger.info(f"Added {edges_added} edges to NetworkX graph")

                self._graph = graph
                self._graph_built = True
                self._build_completed_at = time.time()
                elapsed = self._build_completed_at - self._build_started_at
                logger.info(
                    f"NetworkX graph ready: nodes={graph.number_of_nodes()}, "
                    f"edges={graph.number_of_edges()}, elapsed={elapsed:.2f}s"
                )
            except Exception as e:
                self._graph_built = False
                self._last_build_error = str(e)
                logger.error(f"Failed to build NetworkX graph: {e}")

    async def query_neighbors(
        self, file_id: int, depth: int = 1, min_similarity: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Query neighbors of a file in the graph.

        Args:
            file_id: Center file ID
            depth: Hop depth (1 or 2)
            min_similarity: Minimum edge weight

        Returns:
            List of neighbor file info with relationship data
        """
        if self._use_age:
            return await self._query_neighbors_age(file_id, depth, min_similarity)
        else:
            return await self._query_neighbors_networkx(file_id, depth, min_similarity)

    async def _query_neighbors_age(
        self, file_id: int, depth: int, min_similarity: float
    ) -> List[Dict[str, Any]]:
        """Query neighbors using AGE Cypher."""
        async with get_conn() as conn:
            await conn.execute("LOAD 'age';")
            await conn.execute("SET search_path = ag_catalog, public;")

            # Query 1-hop or 2-hop neighbors
            if depth == 1:
                query = """
                    SELECT * FROM cypher('storage_graph', $$
                        MATCH (f:File {file_id: %d})-[r]-(n:File)
                        WHERE r.weight >= %f
                        RETURN n.file_id as neighbor_id, n.name as name, 
                               n.path as path, r.weight as weight, 
                               type(r) as rel_type
                        LIMIT 20
                    $$) as (neighbor_id agtype, name agtype, path agtype, 
                           weight agtype, rel_type agtype)
                """ % (file_id, min_similarity)
            else:
                query = """
                    SELECT * FROM cypher('storage_graph', $$
                        MATCH (f:File {file_id: %d})-[r1]-(n1)-[r2]-(n2:File)
                        WHERE r1.weight >= %f AND r2.weight >= %f
                        RETURN n2.file_id as neighbor_id, n2.name as name,
                               n2.path as path, (r1.weight + r2.weight) / 2 as weight,
                               '2hop' as rel_type
                        LIMIT 20
                    $$) as (neighbor_id agtype, name agtype, path agtype,
                           weight agtype, rel_type agtype)
                """ % (file_id, min_similarity, min_similarity)

            try:
                rows = await conn.fetch(query)
                neighbors = []
                for row in rows:
                    neighbors.append(
                        {
                            "id": row["neighbor_id"],
                            "name": row["name"],
                            "path": row["path"],
                            "weight": float(row["weight"]) if row["weight"] else 0.0,
                            "relationship": row["rel_type"] or "related",
                        }
                    )
                return neighbors
            except Exception as e:
                logger.error(f"AGE query failed: {e}")
                return []

    async def _query_neighbors_networkx(
        self, file_id: int, depth: int, min_similarity: float
    ) -> List[Dict[str, Any]]:
        """Query neighbors using NetworkX."""
        await self._ensure_networkx_graph_ready(wait_timeout=self._query_wait_timeout)

        if self._graph is None or file_id not in self._graph:
            return []

        neighbors = []

        # 1-hop neighbors
        for neighbor_id in self._graph.neighbors(file_id):
            edge_data = self._graph.get_edge_data(file_id, neighbor_id)
            weight = edge_data.get("weight", 0) if edge_data else 0

            if weight >= min_similarity:
                node_data = self._graph.nodes[neighbor_id]
                neighbors.append(
                    {
                        "id": neighbor_id,
                        "name": node_data.get("name", ""),
                        "path": node_data.get("path", ""),
                        "weight": weight,
                        "relationship": "similar_to",
                    }
                )

        # 2-hop neighbors if requested
        if depth >= 2:
            seen = {file_id} | {n["id"] for n in neighbors}
            for n1 in list(neighbors):
                for n2_id in self._graph.neighbors(n1["id"]):
                    if n2_id not in seen:
                        edge_data = self._graph.get_edge_data(n1["id"], n2_id)
                        weight = edge_data.get("weight", 0) if edge_data else 0

                        if weight >= min_similarity:
                            node_data = self._graph.nodes[n2_id]
                            neighbors.append(
                                {
                                    "id": n2_id,
                                    "name": node_data.get("name", ""),
                                    "path": node_data.get("path", ""),
                                    "weight": (n1["weight"] + weight) / 2,
                                    "relationship": "2hop",
                                }
                            )
                            seen.add(n2_id)

        return neighbors[:20]

    async def get_pagerank(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get files ranked by PageRank.

        Args:
            limit: Number of top results

        Returns:
            List of files with PageRank scores
        """
        # AGE doesn't have built-in PageRank; use NetworkX graph.
        await self._ensure_networkx_graph_ready(wait_timeout=10.0)

        if self._graph is None or len(self._graph.nodes()) == 0:
            return []

        try:
            pagerank_scores = nx.pagerank(self._graph, weight="weight")
            sorted_scores = sorted(
                pagerank_scores.items(), key=lambda x: x[1], reverse=True
            )

            results = []
            for file_id, score in sorted_scores[:limit]:
                node_data = self._graph.nodes[file_id]
                results.append(
                    {
                        "id": file_id,
                        "name": node_data.get("name", ""),
                        "path": node_data.get("path", ""),
                        "extension": node_data.get("extension", ""),
                        "pagerank": score,
                    }
                )

            return results
        except Exception as e:
            logger.error(f"PageRank calculation failed: {e}")
            return []

    async def get_communities(self) -> List[Dict[str, Any]]:
        """Detect communities in the graph using Louvain algorithm.

        Returns:
            List of communities with member files
        """
        await self._ensure_networkx_graph_ready(wait_timeout=10.0)

        if self._graph is None or len(self._graph.nodes()) == 0:
            return []

        try:
            communities = nx.community.louvain_communities(
                self._graph, weight="weight", seed=42
            )

            results = []
            for i, community in enumerate(communities[:10]):  # Top 10 communities
                files = []
                for file_id in list(community)[:20]:  # Max 20 files per community
                    node_data = self._graph.nodes[file_id]
                    files.append(
                        {
                            "id": file_id,
                            "name": node_data.get("name", ""),
                            "path": node_data.get("path", ""),
                        }
                    )

                results.append(
                    {
                        "community_id": i,
                        "size": len(community),
                        "files": files,
                    }
                )

            return results
        except Exception as e:
            logger.error(f"Community detection failed: {e}")
            return []

    async def get_shortest_path(
        self, from_id: int, to_id: int
    ) -> Optional[Dict[str, Any]]:
        """Find shortest path between two files.

        Args:
            from_id: Source file ID
            to_id: Target file ID

        Returns:
            Path information or None if no path exists
        """
        await self._ensure_networkx_graph_ready(wait_timeout=10.0)

        if self._graph is None:
            return None

        if from_id not in self._graph or to_id not in self._graph:
            return None

        try:
            path = nx.shortest_path(
                self._graph, source=from_id, target=to_id, weight="weight"
            )

            # Build path details
            path_files = []
            for file_id in path:
                node_data = self._graph.nodes[file_id]
                path_files.append(
                    {
                        "id": file_id,
                        "name": node_data.get("name", ""),
                        "path": node_data.get("path", ""),
                    }
                )

            return {
                "from_id": from_id,
                "to_id": to_id,
                "path_length": len(path) - 1,
                "files": path_files,
            }
        except nx.NetworkXNoPath:
            return None
        except Exception as e:
            logger.error(f"Shortest path calculation failed: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """Return graph backend/build status metrics."""
        build_in_progress = self._build_task is not None and not self._build_task.done()
        elapsed_sec = None
        if self._build_started_at is not None and self._build_completed_at is not None:
            elapsed_sec = round(self._build_completed_at - self._build_started_at, 3)

        return {
            "backend": "AGE" if self._use_age else "NetworkX",
            "age_available": self._age_available,
            "graph_built": self._graph_built,
            "build_in_progress": build_in_progress,
            "last_build_error": self._last_build_error,
            "build_elapsed_seconds": elapsed_sec,
            "node_count": self._graph.number_of_nodes() if self._graph else 0,
            "edge_count": self._graph.number_of_edges() if self._graph else 0,
            "limits": {
                "node_limit": self._node_limit,
                "embedding_limit": self._embedding_limit,
                "edge_window": self._edge_window,
                "edge_similarity_threshold": self._active_edge_similarity_threshold,
                "base_edge_similarity_threshold": self._base_edge_similarity_threshold,
                "auto_tune_threshold": self._auto_tune_threshold,
                "auto_tune_applied": self._auto_tune_applied,
                "min_edge_similarity_threshold": self._min_edge_similarity_threshold,
            },
        }


# Global graph manager instance
_graph_manager: Optional[GraphManager] = None


async def init_graph_manager() -> GraphManager:
    """Initialize the global graph manager."""
    global _graph_manager
    _graph_manager = GraphManager()
    await _graph_manager.initialize()
    return _graph_manager


def get_graph_manager() -> Optional[GraphManager]:
    """Get the global graph manager instance."""
    return _graph_manager
