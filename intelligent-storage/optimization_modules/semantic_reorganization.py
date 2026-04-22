"""
Ultimate Intelligent Storage Nexus - Semantic File Reorganization
Human-Friendly, AI-Optimized Physical File Organization

This module reorganizes files on disk based on:
- Semantic similarity (AI embeddings)
- Knowledge graph relationships
- Human-readable folder naming
- Intuitive hierarchy for non-technical users

Features:
- Automatic folder creation with descriptive names
- Safe file moving with rollback capability
- Preview mode (dry-run)
- Relationship-aware grouping
- Conflict resolution
- Progress tracking
"""

import os
import shutil
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ReorganizationPlan:
    """Plan for reorganizing files"""

    source_path: str
    target_path: str
    folder_name: str
    category: str
    confidence: float
    reasoning: str
    related_files: List[int] = field(default_factory=list)


@dataclass
class FolderStructure:
    """Represents a folder in the reorganized structure"""

    name: str
    description: str
    files: List[int] = field(default_factory=list)
    subfolders: Dict[str, "FolderStructure"] = field(default_factory=dict)
    themes: List[str] = field(default_factory=list)
    confidence: float = 0.0


class HumanFriendlyNamer:
    """
    Generates human-readable folder names from AI-detected themes

    Converts technical concepts into intuitive folder names
    """

    # Theme mappings: technical to human-friendly
    THEME_MAPPINGS = {
        # Code domains
        "authentication": ["Login & Security", "User Access", "Account Management"],
        "database": ["Data Storage", "Database Files", "Information Records"],
        "api": ["Connections", "External Services", "APIs & Integrations"],
        "frontend": ["User Interface", "Website Design", "App Screens"],
        "backend": ["Server Logic", "Behind the Scenes", "System Core"],
        "config": ["Settings", "Configuration", "Preferences"],
        "test": ["Quality Checks", "Testing", "Validation"],
        "docs": ["Documentation", "Guides", "Instructions"],
        # Project types
        "web": ["Website Project", "Web Application", "Online Tools"],
        "mobile": ["Mobile App", "Phone Application", "Android/iOS"],
        "desktop": ["Computer Program", "Desktop App", "PC Software"],
        "script": ["Automation", "Helper Scripts", "Task Runners"],
        # Data types
        "image": ["Pictures", "Images", "Visual Content"],
        "video": ["Videos", "Movies", "Recordings"],
        "audio": ["Sounds", "Music", "Audio Files"],
        "document": ["Documents", "Papers", "Written Content"],
        "spreadsheet": ["Data Sheets", "Spreadsheets", "Tables"],
        # Time-based
        "recent": ["Recent Work", "Latest Files", "Current Projects"],
        "archive": ["Old Files", "Archive", "Past Work"],
        "backup": ["Backups", "Safety Copies", "File Recovery"],
        # Importance
        "important": ["Important", "Critical Files", "Must Keep"],
        "draft": ["Drafts", "Work in Progress", "Unfinished"],
        "template": ["Templates", "Starting Points", "Blueprints"],
    }

    @classmethod
    def generate_folder_name(
        cls, themes: List[str], file_types: List[str], confidence: float
    ) -> str:
        """Generate a human-friendly folder name"""
        # Find best matching human-friendly names
        friendly_names = []

        for theme in themes[:2]:  # Top 2 themes
            theme_lower = theme.lower()
            for key, names in cls.THEME_MAPPINGS.items():
                if key in theme_lower or theme_lower in key:
                    friendly_names.extend(names)
                    break

        # If no match, create descriptive name from file types
        if not friendly_names:
            if file_types:
                ext_names = [t.strip(".").upper() for t in file_types[:2]]
                friendly_names = [f"{' & '.join(ext_names)} Files"]
            else:
                friendly_names = ["Miscellaneous"]

        # Add visual indicators
        if "recent" in themes:
            folder_name = f"{friendly_names[0]} - Recent"
        elif "important" in themes:
            folder_name = f"⭐ {friendly_names[0]}"
        elif confidence > 0.9:
            folder_name = f"📂 {friendly_names[0]}"
        else:
            folder_name = friendly_names[0]

        # Clean up name
        folder_name = folder_name.replace("_", " ").title()

        return folder_name

    @classmethod
    def generate_description(
        cls, themes: List[str], file_count: int, sample_files: List[str]
    ) -> str:
        """Generate human-readable folder description"""
        theme_str = ", ".join(themes[:3])
        sample_str = ", ".join([Path(f).name for f in sample_files[:3]])

        descriptions = [
            f"Contains {file_count} files related to {theme_str}.",
            f"Includes: {sample_str}",
        ]

        if file_count > 50:
            descriptions.append("Large collection - consider sub-folders.")

        return " ".join(descriptions)


class SemanticReorganizer:
    """
    Reorganizes files based on semantic similarity and knowledge graph

    Creates human-friendly folder structure while maintaining AI optimization
    """

    def __init__(
        self,
        storage_manager,
        knowledge_graph,
        quantizer,
        base_path: str = "/mnt/external/organized",
    ):
        self.storage = storage_manager
        self.kg = knowledge_graph
        self.quantizer = quantizer
        self.base_path = Path(base_path)

        # Reorganization state
        self.reorganization_log: List[Dict] = []
        self.rollback_stack: List[Tuple[str, str]] = []

        logger.info(f"SemanticReorganizer initialized")
        logger.info(f"  Base path: {self.base_path}")

    def analyze_files(self, file_ids: List[int]) -> Dict[int, Dict]:
        """Analyze files for reorganization"""
        logger.info(f"Analyzing {len(file_ids)} files for reorganization...")

        analysis = {}

        for fid in file_ids:
            result = self.storage.retrieve(fid)
            if not result:
                continue

            metadata = self.storage.cold_index.get(fid, {}).get("metadata", {})
            entities = self.kg.file_entities.get(fid, [])
            entity_names = [e.name for e in entities]

            themes = self._detect_themes(fid, metadata, entity_names)
            neighbors = self.kg.find_related_files(fid, max_hops=1)

            analysis[fid] = {
                "id": fid,
                "current_path": metadata.get("path", "unknown"),
                "name": metadata.get("name", "unknown"),
                "extension": metadata.get("extension", ""),
                "themes": themes,
                "entities": entity_names,
                "neighbors": [n[0] for n in neighbors],
                "embedding": result.get("float32"),
                "size": metadata.get("size", 0),
            }

        return analysis

    def _detect_themes(
        self, file_id: int, metadata: Dict, entities: List[str]
    ) -> List[str]:
        """Detect themes from file metadata and entities"""
        themes = set()

        ext = metadata.get("extension", "").lower()
        if ext in [".py", ".js", ".ts", ".java"]:
            themes.add("code")
        elif ext in [".md", ".txt", ".doc"]:
            themes.add("document")
        elif ext in [".png", ".jpg", ".gif"]:
            themes.add("image")
        elif ext in [".mp4", ".avi", ".mov"]:
            themes.add("video")

        for entity in entities:
            entity_lower = entity.lower()
            if any(word in entity_lower for word in ["auth", "login", "password"]):
                themes.add("authentication")
            if any(word in entity_lower for word in ["db", "database", "sql"]):
                themes.add("database")
            if any(word in entity_lower for word in ["api", "endpoint", "route"]):
                themes.add("api")
            if any(word in entity_lower for word in ["test", "spec", "mock"]):
                themes.add("test")

        name = metadata.get("name", "").lower()
        if any(word in name for word in ["test", "spec"]):
            themes.add("test")
        if any(word in name for word in ["config", "setting"]):
            themes.add("config")

        return list(themes)

    def cluster_files(
        self, analysis: Dict[int, Dict], n_clusters: Optional[int] = None
    ) -> Dict[int, int]:
        """
        Cluster files based on semantic similarity

        Returns: file_id -> cluster_id mapping
        """
        logger.info("Clustering files by semantic similarity...")

        file_ids = list(analysis.keys())

        if len(file_ids) < 10:
            logger.warning("Too few files for clustering")
            return {fid: 0 for fid in file_ids}

        # Build embedding matrix
        embeddings = []
        valid_ids = []

        for fid in file_ids:
            emb = analysis[fid].get("embedding")
            if emb is not None:
                embeddings.append(emb)
                valid_ids.append(fid)

        if len(embeddings) < 5:
            logger.warning("Too few embeddings for clustering")
            return {fid: 0 for fid in file_ids}

        embeddings = np.array(embeddings)

        # Determine number of clusters
        if n_clusters is None:
            n_clusters = max(2, min(len(embeddings) // 20, 50))

        logger.info(f"  Clustering {len(embeddings)} files into {n_clusters} groups...")

        # Agglomerative clustering (hierarchical)
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters, metric="cosine", linkage="average"
        )

        labels = clustering.fit_predict(embeddings)

        # Map back to file IDs
        return {fid: int(label) for fid, label in zip(valid_ids, labels)}

    def create_folder_structure(
        self, analysis: Dict[int, Dict], clusters: Dict[int, int]
    ) -> Dict[int, FolderStructure]:
        """
        Create human-friendly folder structure from clusters

        Returns: cluster_id -> FolderStructure
        """
        logger.info("Creating human-friendly folder structure...")

        folders: Dict[int, FolderStructure] = {}

        # Group files by cluster
        cluster_files: Dict[int, List[int]] = defaultdict(list)
        for fid, cid in clusters.items():
            cluster_files[cid].append(fid)

        for cid, files in cluster_files.items():
            if not files:
                continue

            # Analyze cluster themes
            all_themes = []
            all_extensions = []

            for fid in files:
                all_themes.extend(analysis[fid].get("themes", []))
                ext = analysis[fid].get("extension", "")
                if ext:
                    all_extensions.append(ext)

            # Get most common themes
            theme_counts = {}
            for theme in all_themes:
                theme_counts[theme] = theme_counts.get(theme, 0) + 1
            top_themes = sorted(
                theme_counts.keys(), key=lambda t: theme_counts[t], reverse=True
            )[:3]

            # Get most common extensions
            ext_counts = {}
            for ext in all_extensions:
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
            top_extensions = sorted(
                ext_counts.keys(), key=lambda e: ext_counts[e], reverse=True
            )[:2]

            # Calculate confidence
            if files:
                confidence = sum(
                    analysis[f]["embedding"] is not None for f in files
                ) / len(files)
            else:
                confidence = 0.0

            # Generate folder name
            folder_name = HumanFriendlyNamer.generate_folder_name(
                top_themes, top_extensions, confidence
            )

            # Generate description
            sample_files = [analysis[f]["current_path"] for f in files[:3]]
            description = HumanFriendlyNamer.generate_description(
                top_themes, len(files), sample_files
            )

            folders[cid] = FolderStructure(
                name=folder_name,
                description=description,
                files=files,
                themes=top_themes,
                confidence=confidence,
            )

        logger.info(f"  Created {len(folders)} folders")
        return folders

    def generate_reorganization_plan(
        self, file_ids: List[int], dry_run: bool = True
    ) -> List[ReorganizationPlan]:
        """
        Generate complete reorganization plan

        Args:
            file_ids: Files to reorganize
            dry_run: If True, don't actually move files

        Returns:
            List of reorganization plans
        """
        logger.info("=" * 70)
        logger.info("GENERATING REORGANIZATION PLAN")
        logger.info("=" * 70)

        # Step 1: Analyze files
        analysis = self.analyze_files(file_ids)

        # Step 2: Cluster files
        clusters = self.cluster_files(analysis)

        # Step 3: Create folder structure
        folders = self.create_folder_structure(analysis, clusters)

        # Step 4: Generate plans
        plans = []

        for cid, folder in folders.items():
            # Create folder path
            folder_path = self.base_path / self._sanitize_filename(folder.name)

            for fid in folder.files:
                source_path = analysis[fid]["current_path"]
                filename = analysis[fid]["name"]

                # Check for naming conflicts
                target_path = self._resolve_conflict(folder_path, filename)

                # Create plan
                plan = ReorganizationPlan(
                    source_path=source_path,
                    target_path=str(target_path),
                    folder_name=folder.name,
                    category=folder.themes[0] if folder.themes else "misc",
                    confidence=folder.confidence,
                    reasoning=folder.description,
                    related_files=[f for f in folder.files if f != fid],
                )

                plans.append(plan)

        # Sort by confidence (highest first)
        plans.sort(key=lambda p: p.confidence, reverse=True)

        logger.info(f"\nGenerated {len(plans)} reorganization plans")
        logger.info(f"  Organized into {len(folders)} folders")
        logger.info(
            f"  Average confidence: {np.mean([p.confidence for p in plans]):.2f}"
        )

        return plans

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize folder name for filesystem"""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "-")

        # Limit length
        if len(name) > 100:
            name = name[:97] + "..."

        return name.strip()

    def _resolve_conflict(self, folder_path: Path, filename: str) -> Path:
        """Resolve naming conflicts"""
        target = folder_path / filename

        if not target.exists():
            return target

        # Add number suffix
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        counter = 1

        while target.exists():
            new_name = f"{stem}_{counter}{suffix}"
            target = folder_path / new_name
            counter += 1

        return target

    def execute_reorganization(
        self, plans: List[ReorganizationPlan], dry_run: bool = True
    ) -> Dict:
        """
        Execute reorganization plan

        Args:
            plans: List of reorganization plans
            dry_run: If True, simulate without moving files

        Returns:
            Execution results
        """
        logger.info("=" * 70)
        if dry_run:
            logger.info("DRY RUN - Simulating reorganization")
        else:
            logger.info("EXECUTING REORGANIZATION")
        logger.info("=" * 70)

        results = {
            "moved": 0,
            "skipped": 0,
            "errors": 0,
            "folders_created": set(),
            "log": [],
        }

        for i, plan in enumerate(plans):
            if i % 100 == 0:
                logger.info(f"  Progress: {i}/{len(plans)} files processed")

            try:
                source = Path(plan.source_path)
                target = Path(plan.target_path)

                # Check if source exists
                if not source.exists():
                    logger.warning(f"  Source not found: {source}")
                    results["skipped"] += 1
                    continue

                # Create folder
                folder = target.parent
                if not dry_run:
                    folder.mkdir(parents=True, exist_ok=True)
                results["folders_created"].add(str(folder))

                # Move file
                if not dry_run:
                    shutil.move(str(source), str(target))

                    # Update database
                    self._update_file_path(plan)

                    # Add to rollback stack
                    self.rollback_stack.append((str(target), str(source)))

                results["moved"] += 1
                results["log"].append(
                    {
                        "action": "move",
                        "source": str(source),
                        "target": str(target),
                        "folder": plan.folder_name,
                        "confidence": plan.confidence,
                    }
                )

            except Exception as e:
                logger.error(f"  Error moving {plan.source_path}: {e}")
                results["errors"] += 1
                results["log"].append(
                    {"action": "error", "source": plan.source_path, "error": str(e)}
                )

        logger.info(f"\nReorganization complete!")
        logger.info(f"  Files moved: {results['moved']}")
        logger.info(f"  Folders created: {len(results['folders_created'])}")
        logger.info(f"  Skipped: {results['skipped']}")
        logger.info(f"  Errors: {results['errors']}")

        return results

    def _update_file_path(self, plan: ReorganizationPlan):
        """Update file path in database after move"""
        # This would update the database record
        # Implementation depends on your database schema
        pass

    def rollback(self) -> Dict:
        """
        Rollback all moves from last reorganization

        Returns:
            Rollback results
        """
        logger.info("=" * 70)
        logger.info("ROLLING BACK REORGANIZATION")
        logger.info("=" * 70)

        results = {"restored": 0, "errors": 0}

        # Process in reverse order
        for target, source in reversed(self.rollback_stack):
            try:
                if Path(target).exists():
                    shutil.move(target, source)
                    results["restored"] += 1
            except Exception as e:
                logger.error(f"  Error restoring {target}: {e}")
                results["errors"] += 1

        # Clear rollback stack
        self.rollback_stack = []

        logger.info(f"\nRollback complete!")
        logger.info(f"  Files restored: {results['restored']}")
        logger.info(f"  Errors: {results['errors']}")

        return results

    def preview_reorganization(self, plans: List[ReorganizationPlan]) -> str:
        """Generate human-readable preview of reorganization"""
        lines = []
        lines.append("=" * 70)
        lines.append("REORGANIZATION PREVIEW")
        lines.append("=" * 70)
        lines.append("")

        # Group by folder
        folders: Dict[str, List[ReorganizationPlan]] = defaultdict(list)
        for plan in plans:
            folders[plan.folder_name].append(plan)

        for folder_name, folder_plans in sorted(folders.items()):
            if not folder_plans:
                continue

            lines.append(f"📁 {folder_name}")
            lines.append(f"   {folder_plans[0].reasoning}")
            lines.append(f"   Files: {len(folder_plans)}")
            lines.append(
                f"   Confidence: {np.mean([p.confidence for p in folder_plans]):.1%}"
            )
            lines.append("")

            # Show sample files
            for plan in folder_plans[:5]:
                filename = Path(plan.source_path).name
                lines.append(f"     • {filename}")

            if len(folder_plans) > 5:
                lines.append(f"     ... and {len(folder_plans) - 5} more")

            lines.append("")

        lines.append("=" * 70)
        lines.append(f"Total: {len(plans)} files in {len(folders)} folders")
        lines.append("=" * 70)

        return "\n".join(lines)


class IntelligentFileManager:
    """
    High-level interface for intelligent file management

    Combines semantic reorganization with the existing storage system
    """

    def __init__(self, storage_manager, knowledge_graph, quantizer):
        self.reorganizer = SemanticReorganizer(
            storage_manager, knowledge_graph, quantizer
        )
        self.storage = storage_manager
        self.kg = knowledge_graph

    def organize_by_semantics(
        self, file_ids: Optional[List[int]] = None, dry_run: bool = True
    ) -> Dict:
        """
        Organize files by semantic meaning

        Args:
            file_ids: Specific files to organize (None = all files)
            dry_run: Preview changes without executing

        Returns:
            Reorganization results
        """
        if file_ids is None:
            # Get all file IDs from storage
            file_ids = list(self.storage.cold_index.keys())

        logger.info(f"Organizing {len(file_ids)} files by semantic meaning...")

        # Generate plan
        plans = self.reorganizer.generate_reorganization_plan(file_ids, dry_run)

        # Show preview
        preview = self.reorganizer.preview_reorganization(plans)
        print(preview)

        if dry_run:
            logger.info("\nThis was a dry run. No files were moved.")
            logger.info("To execute, call organize_by_semantics(dry_run=False)")
            return {"status": "preview", "plans": plans}

        # Execute reorganization
        results = self.reorganizer.execute_reorganization(plans, dry_run=False)

        return {"status": "executed", "results": results, "plans": plans}

    def create_project_structure(self, project_name: str, file_ids: List[int]) -> str:
        """
        Create organized project structure from scattered files

        Args:
            project_name: Name for the new organized project
            file_ids: Files to include

        Returns:
            Path to organized project
        """
        # Set project-specific base path
        project_path = f"/mnt/external/organized_projects/{project_name}"
        self.reorganizer.base_path = Path(project_path)

        # Organize files
        result = self.organize_by_semantics(file_ids, dry_run=False)

        # Create README
        readme_path = Path(project_path) / "README.txt"
        with open(readme_path, "w") as f:
            f.write(f"Project: {project_name}\n")
            f.write(f"Files: {len(file_ids)}\n")
            f.write(f"Organized by: AI Semantic Analysis\n")
            f.write(f"Date: {datetime.now().isoformat()}\n")
            f.write("\nThis folder structure was automatically generated\n")
            f.write("based on file content and semantic relationships.\n")

        return project_path


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("SEMANTIC FILE REORGANIZATION MODULE")
    logger.info("Human-Friendly, AI-Optimized Physical Organization")
    logger.info("=" * 70)

    # Demo the human-friendly naming
    logger.info("\nDemo: Human-Friendly Folder Naming")

    test_cases = [
        (["authentication", "web"], [".py", ".js"], 0.95),
        (["database", "api"], [".sql", ".py"], 0.88),
        (["image", "recent"], [".png", ".jpg"], 0.92),
        (["document"], [".md", ".txt"], 0.75),
        ([], [".rs", ".toml"], 0.65),
    ]

    for themes, exts, conf in test_cases:
        name = HumanFriendlyNamer.generate_folder_name(themes, exts, conf)
        desc = HumanFriendlyNamer.generate_description(
            themes, 25, [f"file{i}.ext" for i in range(3)]
        )
        logger.info(f"\n  Themes: {themes}")
        logger.info(f"  Extensions: {exts}")
        logger.info(f"  Generated: {name}")
        logger.info(f"  Description: {desc[:80]}...")

    logger.info("\n" + "=" * 70)
    logger.info("Module ready for integration!")
    logger.info("=" * 70)
