"""
Ultimate Intelligent Storage Nexus - Hybrid RAG with Knowledge Graph
Phase 4: GraphRAG + Vector Hybrid Architecture

Combines:
- Vector embeddings for semantic similarity
- Knowledge graph for relationship-aware reasoning
- Multi-hop traversal for complex queries
- Entity linking and resolution

Based on: Microsoft GraphRAG, Neo4j HybridRAG (2025)
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from collections import defaultdict
import networkx as nx
import re
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of relationships in the file knowledge graph"""

    IMPORTS = "imports"  # File imports another file
    DEPENDS_ON = "depends_on"  # File depends on another
    SIMILAR_TO = "similar_to"  # Semantically similar
    CONTAINS = "contains"  # Directory contains file
    REFERENCES = "references"  # References entity
    VERSION_OF = "version_of"  # Different version
    CO_OCCURS_WITH = "co_occurs_with"  # Often accessed together


class EntityType(Enum):
    """Types of entities extractable from files"""

    CLASS = "class"
    FUNCTION = "function"
    VARIABLE = "variable"
    MODULE = "module"
    API_ENDPOINT = "api_endpoint"
    DATABASE_TABLE = "database_table"
    CONFIG_KEY = "config_key"


@dataclass
class Entity:
    """Entity extracted from file"""

    name: str
    type: EntityType
    file_id: int
    line_number: Optional[int] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class Relationship:
    """Relationship between files or entities"""

    source: int  # File ID
    target: int  # File ID
    type: RelationshipType
    weight: float = 1.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class GraphNode:
    """Node in knowledge graph"""

    id: int
    type: str  # 'file', 'entity', 'concept'
    properties: Dict = field(default_factory=dict)


class KnowledgeGraph:
    """
    Knowledge graph for file relationships and entities

    Built on NetworkX for flexibility, can be backed by Neo4j for production
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.entity_index: Dict[str, List[int]] = defaultdict(
            list
        )  # entity name -> file ids
        self.file_entities: Dict[int, List[Entity]] = defaultdict(list)

    def add_file_node(self, file_id: int, metadata: Dict):
        """Add file as graph node"""
        self.graph.add_node(file_id, type="file", **metadata)

    def add_relationship(self, rel: Relationship):
        """Add relationship between files"""
        self.graph.add_edge(
            rel.source,
            rel.target,
            relationship_type=rel.type.value,
            weight=rel.weight,
            **rel.metadata,
        )

    def add_entity(self, file_id: int, entity: Entity):
        """Add entity extracted from file"""
        self.file_entities[file_id].append(entity)
        self.entity_index[entity.name].append(file_id)

        # Add entity as separate node
        entity_node_id = f"entity:{entity.name}:{file_id}"
        self.graph.add_node(
            entity_node_id,
            type="entity",
            entity_type=entity.type.value,
            file_id=file_id,
            line_number=entity.line_number,
            **entity.metadata,
        )

        # Link file to entity
        self.graph.add_edge(
            file_id, entity_node_id, relationship_type="contains_entity"
        )

    def extract_code_entities(self, file_id: int, content: str, language: str):
        """Extract entities from code content"""
        entities = []

        if language in ["python", "py"]:
            entities = self._extract_python_entities(file_id, content)
        elif language in ["javascript", "js", "typescript", "ts"]:
            entities = self._extract_js_entities(file_id, content)

        for entity in entities:
            self.add_entity(file_id, entity)

        return entities

    def _extract_python_entities(self, file_id: int, content: str) -> List[Entity]:
        """Extract Python classes, functions, imports"""
        entities = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Class definitions
            class_match = re.match(r"^class\s+(\w+)", line)
            if class_match:
                entities.append(
                    Entity(
                        name=class_match.group(1),
                        type=EntityType.CLASS,
                        file_id=file_id,
                        line_number=i,
                    )
                )

            # Function definitions
            func_match = re.match(r"^def\s+(\w+)", line)
            if func_match:
                entities.append(
                    Entity(
                        name=func_match.group(1),
                        type=EntityType.FUNCTION,
                        file_id=file_id,
                        line_number=i,
                    )
                )

            # Import statements
            import_match = re.match(r"^(?:from|import)\s+([\w.]+)", line)
            if import_match:
                entities.append(
                    Entity(
                        name=import_match.group(1),
                        type=EntityType.MODULE,
                        file_id=file_id,
                        line_number=i,
                    )
                )

        return entities

    def _extract_js_entities(self, file_id: int, content: str) -> List[Entity]:
        """Extract JavaScript/TypeScript entities"""
        entities = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Function definitions (various patterns)
            func_match = re.match(
                r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\([^)]*\)\s*=>))",
                line,
            )
            if func_match:
                name = func_match.group(1) or func_match.group(2)
                if name:
                    entities.append(
                        Entity(
                            name=name,
                            type=EntityType.FUNCTION,
                            file_id=file_id,
                            line_number=i,
                        )
                    )

            # Class definitions
            class_match = re.match(r"class\s+(\w+)", line)
            if class_match:
                entities.append(
                    Entity(
                        name=class_match.group(1),
                        type=EntityType.CLASS,
                        file_id=file_id,
                        line_number=i,
                    )
                )

        return entities

    def find_related_files(
        self, file_id: int, max_hops: int = 2
    ) -> List[Tuple[int, int, float]]:
        """
        Find files related to given file via graph traversal

        Returns: List of (file_id, num_hops, combined_weight)
        """
        if file_id not in self.graph:
            return []

        related = []
        seen = {file_id}

        # BFS traversal
        queue = [(file_id, 0, 1.0)]  # (node, hops, weight)

        while queue:
            current, hops, weight = queue.pop(0)

            if hops >= max_hops:
                continue

            for neighbor in self.graph.neighbors(current):
                if neighbor not in seen:
                    seen.add(neighbor)
                    edge_data = self.graph[current][neighbor]
                    edge_weight = edge_data.get("weight", 1.0)
                    new_weight = (
                        weight * edge_weight * (0.5**hops)
                    )  # Decay with distance

                    if isinstance(neighbor, int):  # Only file nodes
                        related.append((neighbor, hops + 1, new_weight))

                    queue.append((neighbor, hops + 1, new_weight))

        return related

    def find_by_entity(self, entity_name: str) -> List[int]:
        """Find files containing named entity"""
        return self.entity_index.get(entity_name, [])

    def get_centrality_scores(self) -> Dict[int, float]:
        """Get PageRank centrality scores for files"""
        if len(self.graph) == 0:
            return {}

        try:
            centrality = nx.pagerank(self.graph)
            # Filter only file nodes (int IDs)
            return {
                node: score
                for node, score in centrality.items()
                if isinstance(node, int)
            }
        except:
            return {}

    def detect_communities(self) -> Dict[int, int]:
        """Detect file communities using Louvain algorithm"""
        if len(self.graph) == 0:
            return {}

        try:
            import community as community_louvain

            partition = community_louvain.best_partition(self.graph.to_undirected())
            return {
                node: comm for node, comm in partition.items() if isinstance(node, int)
            }
        except ImportError:
            logger.warning("python-louvain not installed, skipping community detection")
            return {}


class HybridRAGRetriever:
    """
    Hybrid RAG combining vector search with knowledge graph traversal

    Query Processing:
    1. Parse query for entities and intent
    2. Vector search for semantic similarity
    3. Graph traversal for relationship context
    4. Combine results with weighted fusion
    5. Rerank based on graph centrality and relevance
    """

    def __init__(self, knowledge_graph: KnowledgeGraph, vector_search_fn=None):
        self.kg = knowledge_graph
        self.vector_search = vector_search_fn
        self.query_expander = QueryExpander()

    def retrieve(
        self,
        query: str,
        query_embedding: np.ndarray,
        top_k: int = 10,
        use_graph: bool = True,
    ) -> List[Dict]:
        """
        Hybrid retrieval pipeline

        Returns enriched results with graph context
        """
        results = []

        # Step 1: Extract entities from query
        query_entities = self._extract_query_entities(query)
        logger.debug(f"Query entities: {query_entities}")

        # Step 2: Vector search (semantic similarity)
        vector_results = []
        if self.vector_search:
            vector_results = self.vector_search(query_embedding, k=top_k * 2)

        # Step 3: Graph-based retrieval
        graph_results = []
        if use_graph:
            # Find files by entity match
            for entity in query_entities:
                files_with_entity = self.kg.find_by_entity(entity)
                for file_id in files_with_entity:
                    graph_results.append(
                        {
                            "id": file_id,
                            "source": "entity_match",
                            "entity": entity,
                            "score": 0.9,  # High confidence for exact entity match
                        }
                    )

            # Multi-hop traversal from vector results
            for file_id, vec_score in vector_results:
                related = self.kg.find_related_files(file_id, max_hops=2)
                for related_id, hops, graph_weight in related:
                    graph_results.append(
                        {
                            "id": related_id,
                            "source": f"graph_hop_{hops}",
                            "related_to": file_id,
                            "score": vec_score * graph_weight,
                        }
                    )

        # Step 4: Result fusion
        fused_results = self._fuse_results(vector_results, graph_results, top_k)

        # Step 5: Enrich with graph context
        for result in fused_results:
            file_id = result["id"]

            # Add related files
            result["related_files"] = self.kg.find_related_files(file_id, max_hops=1)

            # Add entities
            result["entities"] = [
                {"name": e.name, "type": e.type.value}
                for e in self.kg.file_entities.get(file_id, [])
            ][:5]  # Top 5 entities

            # Add explanation
            result["explanation"] = self._generate_explanation(result, query_entities)

        return fused_results

    def _extract_query_entities(self, query: str) -> List[str]:
        """Extract potential entity names from query"""
        # Simple extraction: look for capitalized words and code-like terms
        entities = []

        # Capitalized CamelCase words (likely class names)
        camel_case = re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b", query)
        entities.extend(camel_case)

        # snake_case words (likely function/variable names)
        snake_case = re.findall(r"\b[a-z]+_[a-z_]+\b", query)
        entities.extend(snake_case)

        # Quoted strings
        quoted = re.findall(r'["\']([^"\']+)["\']', query)
        entities.extend(quoted)

        return list(set(entities))

    def _fuse_results(
        self,
        vector_results: List[Tuple[int, float]],
        graph_results: List[Dict],
        top_k: int,
    ) -> List[Dict]:
        """Fuse vector and graph results with Reciprocal Rank Fusion"""

        # Create score dictionaries
        vector_scores = {id: score for id, score in vector_results}
        graph_scores = {}

        for gr in graph_results:
            fid = gr["id"]
            if fid in graph_scores:
                graph_scores[fid] = max(graph_scores[fid], gr["score"])
            else:
                graph_scores[fid] = gr["score"]

        # Reciprocal Rank Fusion
        k = 60  # RRF constant
        all_ids = set(vector_scores.keys()) | set(graph_scores.keys())

        fused_scores = {}
        for fid in all_ids:
            score = 0

            # Vector rank contribution
            if fid in vector_scores:
                vector_rank = (
                    sorted(
                        vector_scores.keys(),
                        key=lambda x: vector_scores[x],
                        reverse=True,
                    ).index(fid)
                    + 1
                )
                score += 1.0 / (k + vector_rank)

            # Graph rank contribution
            if fid in graph_scores:
                graph_rank = (
                    sorted(
                        graph_scores.keys(), key=lambda x: graph_scores[x], reverse=True
                    ).index(fid)
                    + 1
                )
                score += 1.0 / (k + graph_rank)

            fused_scores[fid] = score

        # Sort by fused score
        sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

        # Return enriched results
        return [
            {
                "id": fid,
                "fused_score": score,
                "vector_score": vector_scores.get(fid),
                "graph_score": graph_scores.get(fid),
            }
            for fid, score in sorted_results[:top_k]
        ]

    def _generate_explanation(self, result: Dict, query_entities: List[str]) -> str:
        """Generate human-readable explanation for result"""
        explanations = []

        if result.get("vector_score"):
            explanations.append(f"Semantic similarity: {result['vector_score']:.2f}")

        if result.get("graph_score"):
            explanations.append(f"Relationship score: {result['graph_score']:.2f}")

        matching_entities = [
            e["name"] for e in result.get("entities", []) if e["name"] in query_entities
        ]
        if matching_entities:
            explanations.append(f"Contains entities: {', '.join(matching_entities)}")

        return "; ".join(explanations) if explanations else "Direct match"


class QueryExpander:
    """
    Expands queries for better retrieval

    Techniques:
    - Synonym expansion
    - Code pattern expansion
    - Semantic query variants
    """

    def __init__(self):
        self.code_patterns = {
            "database": ["db", "sql", "postgres", "mysql", "mongodb"],
            "authentication": ["auth", "login", "oauth", "jwt", "session"],
            "api": ["endpoint", "route", "controller", "handler"],
            "test": ["spec", "unittest", "pytest", "jest"],
        }

    def expand(self, query: str) -> List[str]:
        """Expand query into multiple variants"""
        expansions = [query]

        # Add code pattern variants
        for concept, synonyms in self.code_patterns.items():
            if concept in query.lower():
                for syn in synonyms:
                    expansions.append(query.lower().replace(concept, syn))

        # Add semantic variants
        expansions.append(f"how to {query}")
        expansions.append(f"{query} example")
        expansions.append(f"{query} implementation")

        return list(set(expansions))


class GraphRAGPipeline:
    """
    Complete GraphRAG pipeline for complex queries

    Supports:
    - Multi-hop reasoning
    - Entity linking
    - Community-aware retrieval
    """

    def __init__(
        self, knowledge_graph: KnowledgeGraph, hybrid_retriever: HybridRAGRetriever
    ):
        self.kg = knowledge_graph
        self.retriever = hybrid_retriever

    def answer_complex_query(self, query: str, query_embedding: np.ndarray) -> Dict:
        """
        Answer complex multi-part queries using GraphRAG

        Example: "Find authentication code similar to the User class"

        Steps:
        1. Decompose query into sub-queries
        2. Execute each sub-query
        3. Traverse graph to connect results
        4. Synthesize final answer
        """

        # Step 1: Parse query structure
        sub_queries = self._decompose_query(query)

        # Step 2: Execute sub-queries
        sub_results = []
        for sq in sub_queries:
            results = self.retriever.retrieve(
                sq["text"],
                query_embedding,  # Simplified: use same embedding
                top_k=5,
            )
            sub_results.append({"intent": sq["intent"], "results": results})

        # Step 3: Find connections between sub-results
        connections = self._find_connections(sub_results)

        # Step 4: Synthesize answer
        answer = self._synthesize_answer(query, sub_results, connections)

        return {
            "query": query,
            "sub_queries": sub_results,
            "connections": connections,
            "answer": answer,
            "sources": self._collect_sources(sub_results),
        }

    def _decompose_query(self, query: str) -> List[Dict]:
        """Decompose complex query into sub-queries"""
        sub_queries = []

        # Simple decomposition: look for "like X" patterns
        similar_match = re.search(
            r"similar to (.+?)(?:$|(?:that|which|with))", query.lower()
        )
        if similar_match:
            sub_queries.append({"text": similar_match.group(1), "intent": "reference"})
            sub_queries.append(
                {"text": query.replace(similar_match.group(0), ""), "intent": "search"}
            )
        else:
            sub_queries.append({"text": query, "intent": "search"})

        return sub_queries

    def _find_connections(self, sub_results: List[Dict]) -> List[Dict]:
        """Find graph connections between sub-query results"""
        connections = []

        if len(sub_results) < 2:
            return connections

        # Find shortest paths between results of different sub-queries
        results_a = [r["id"] for r in sub_results[0]["results"]]
        results_b = [r["id"] for r in sub_results[1]["results"]]

        for id_a in results_a[:3]:  # Check top 3 from each
            for id_b in results_b[:3]:
                try:
                    path = nx.shortest_path(self.kg.graph.to_undirected(), id_a, id_b)
                    if len(path) > 1:
                        connections.append(
                            {
                                "from": id_a,
                                "to": id_b,
                                "path": path,
                                "path_length": len(path),
                            }
                        )
                except nx.NetworkXNoPath:
                    continue

        return connections

    def _synthesize_answer(
        self, query: str, sub_results: List[Dict], connections: List[Dict]
    ) -> str:
        """Generate natural language answer"""
        if not sub_results:
            return "No relevant files found."

        # Get primary results
        primary = sub_results[0]["results"][:3]

        answer_parts = []
        answer_parts.append(f"Found {len(primary)} relevant files:")

        for i, result in enumerate(primary, 1):
            answer_parts.append(
                f"{i}. File ID {result['id']} (score: {result['fused_score']:.2f})"
            )
            if result.get("explanation"):
                answer_parts.append(f"   - {result['explanation']}")

        if connections:
            answer_parts.append(
                f"\nFound {len(connections)} relationship paths between concepts."
            )

        return "\n".join(answer_parts)

    def _collect_sources(self, sub_results: List[Dict]) -> List[int]:
        """Collect all source file IDs"""
        sources = set()
        for sr in sub_results:
            for result in sr["results"]:
                sources.add(result["id"])
        return list(sources)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("HYBRID RAG WITH KNOWLEDGE GRAPH")
    logger.info("Phase 4: GraphRAG + Vector Hybrid Architecture")
    logger.info("=" * 60)

    # Create knowledge graph
    kg = KnowledgeGraph()

    # Add sample files and relationships
    logger.info("\nBuilding sample knowledge graph...")

    # Add files
    for i in range(10):
        kg.add_file_node(
            i, {"name": f"file_{i}.py", "language": "python", "size": 1000 + i * 100}
        )

    # Add relationships
    relationships = [
        Relationship(0, 1, RelationshipType.IMPORTS, weight=0.9),
        Relationship(1, 2, RelationshipType.DEPENDS_ON, weight=0.8),
        Relationship(0, 3, RelationshipType.SIMILAR_TO, weight=0.7),
        Relationship(3, 4, RelationshipType.IMPORTS, weight=0.9),
        Relationship(5, 0, RelationshipType.REFERENCES, weight=0.6),
    ]

    for rel in relationships:
        kg.add_relationship(rel)

    # Extract entities from sample code
    sample_code = """
class User:
    def authenticate(self):
        pass

def login_user():
    user = User()
    user.authenticate()
    """

    kg.extract_code_entities(0, sample_code, "python")

    logger.info(
        f"Graph stats: {len(kg.graph)} nodes, {kg.graph.number_of_edges()} edges"
    )

    # Test graph traversal
    logger.info("\nTesting graph traversal...")
    related = kg.find_related_files(0, max_hops=2)
    logger.info(f"Files related to file 0: {related}")

    # Test entity lookup
    logger.info("\nTesting entity lookup...")
    files_with_user = kg.find_by_entity("User")
    logger.info(f"Files containing 'User' entity: {files_with_user}")

    # Create hybrid retriever (without vector search for demo)
    retriever = HybridRAGRetriever(kg, vector_search_fn=None)

    # Mock vector search function
    def mock_vector_search(embedding, k=10):
        return [(i, 0.9 - i * 0.05) for i in range(min(k, 10))]

    retriever.vector_search = mock_vector_search

    # Test hybrid retrieval
    logger.info("\nTesting hybrid retrieval...")
    query = "Find authentication code"
    query_embedding = np.random.randn(768).astype(np.float32)

    results = retriever.retrieve(query, query_embedding, top_k=5)

    logger.info(f"Query: {query}")
    logger.info(f"Top results:")
    for r in results:
        logger.info(f"  File {r['id']}: score={r['fused_score']:.3f}")
        logger.info(f"    Explanation: {r['explanation']}")
        if r["entities"]:
            logger.info(f"    Entities: {[e['name'] for e in r['entities']]}")

    # Test GraphRAG pipeline
    logger.info("\nTesting GraphRAG pipeline...")
    pipeline = GraphRAGPipeline(kg, retriever)

    complex_query = "Find authentication code similar to User class"
    answer = pipeline.answer_complex_query(complex_query, query_embedding)

    logger.info(f"Complex query: {complex_query}")
    logger.info(f"Answer:\n{answer['answer']}")

    logger.info("\n" + "=" * 60)
    logger.info("Phase 4 Complete: Hybrid RAG Implemented")
    logger.info("Combining vector similarity with graph relationships")
    logger.info("=" * 60)
