#!/usr/bin/env python3
"""
Semantic File Analyzer
Enterprise-grade semantic analysis for intelligent file classification
"""

import logging
import mimetypes
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class SemanticAnalysisResult:
    """Results of semantic analysis"""
    file_path: str
    file_type: str
    semantic_category: str
    importance_score: float
    tags: List[str] = field(default_factory=list)
    language: Optional[str] = None
    framework: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "file_path": self.file_path,
            "file_type": self.file_type,
            "semantic_category": self.semantic_category,
            "importance_score": self.importance_score,
            "tags": self.tags,
            "language": self.language,
            "framework": self.framework,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


class EnterpriseSemanticAnalyzer:
    """
    Enterprise semantic analyzer for intelligent file classification

    Features:
    - File type detection
    - Content-based classification
    - Programming language detection
    - Framework identification
    - Importance scoring
    - Semantic tagging
    """

    def __init__(self):
        """Initialize semantic analyzer"""
        self.extension_map = self._build_extension_map()
        self.framework_patterns = self._build_framework_patterns()

    def _build_extension_map(self) -> Dict[str, Dict[str, Any]]:
        """Build extension to category mapping"""
        return {
            # Programming Languages
            '.py': {'category': 'code', 'language': 'python', 'importance': 0.8},
            '.js': {'category': 'code', 'language': 'javascript', 'importance': 0.8},
            '.ts': {'category': 'code', 'language': 'typescript', 'importance': 0.8},
            '.java': {'category': 'code', 'language': 'java', 'importance': 0.8},
            '.cpp': {'category': 'code', 'language': 'cpp', 'importance': 0.8},
            '.c': {'category': 'code', 'language': 'c', 'importance': 0.8},
            '.go': {'category': 'code', 'language': 'go', 'importance': 0.8},
            '.rs': {'category': 'code', 'language': 'rust', 'importance': 0.8},
            '.rb': {'category': 'code', 'language': 'ruby', 'importance': 0.7},
            '.php': {'category': 'code', 'language': 'php', 'importance': 0.7},
            '.swift': {'category': 'code', 'language': 'swift', 'importance': 0.8},
            '.kt': {'category': 'code', 'language': 'kotlin', 'importance': 0.8},

            # Web Technologies
            '.html': {'category': 'web', 'language': 'html', 'importance': 0.6},
            '.css': {'category': 'web', 'language': 'css', 'importance': 0.6},
            '.scss': {'category': 'web', 'language': 'scss', 'importance': 0.6},
            '.jsx': {'category': 'web', 'language': 'react', 'importance': 0.8},
            '.tsx': {'category': 'web', 'language': 'react-typescript', 'importance': 0.8},
            '.vue': {'category': 'web', 'language': 'vue', 'importance': 0.8},

            # Documents
            '.pdf': {'category': 'document', 'language': None, 'importance': 0.7},
            '.doc': {'category': 'document', 'language': None, 'importance': 0.6},
            '.docx': {'category': 'document', 'language': None, 'importance': 0.6},
            '.txt': {'category': 'document', 'language': None, 'importance': 0.5},
            '.md': {'category': 'document', 'language': 'markdown', 'importance': 0.7},

            # Configuration
            '.json': {'category': 'config', 'language': 'json', 'importance': 0.7},
            '.yaml': {'category': 'config', 'language': 'yaml', 'importance': 0.7},
            '.yml': {'category': 'config', 'language': 'yaml', 'importance': 0.7},
            '.toml': {'category': 'config', 'language': 'toml', 'importance': 0.7},
            '.ini': {'category': 'config', 'language': 'ini', 'importance': 0.6},
            '.env': {'category': 'config', 'language': None, 'importance': 0.9},

            # Media
            '.jpg': {'category': 'image', 'language': None, 'importance': 0.4},
            '.jpeg': {'category': 'image', 'language': None, 'importance': 0.4},
            '.png': {'category': 'image', 'language': None, 'importance': 0.4},
            '.gif': {'category': 'image', 'language': None, 'importance': 0.3},
            '.svg': {'category': 'image', 'language': 'svg', 'importance': 0.6},

            # Database
            '.sql': {'category': 'database', 'language': 'sql', 'importance': 0.8},
            '.db': {'category': 'database', 'language': None, 'importance': 0.8},
            '.sqlite': {'category': 'database', 'language': None, 'importance': 0.8},
        }

    def _build_framework_patterns(self) -> Dict[str, List[str]]:
        """Build framework detection patterns"""
        return {
            'react': ['jsx', 'tsx', 'package.json'],
            'vue': ['.vue', 'vue.config'],
            'angular': ['angular.json', 'ng'],
            'django': ['manage.py', 'settings.py', 'wsgi.py'],
            'flask': ['app.py', 'flask'],
            'fastapi': ['main.py', 'fastapi'],
            'spring': ['pom.xml', 'application.properties'],
            'docker': ['Dockerfile', 'docker-compose'],
            'kubernetes': ['.yaml', 'deployment', 'service'],
        }

    async def analyze_file(self, file_path: str) -> SemanticAnalysisResult:
        """
        Analyze a single file

        Args:
            file_path: Path to file

        Returns:
            SemanticAnalysisResult with analysis results
        """
        path = Path(file_path)

        # Basic file info
        extension = path.suffix.lower()
        file_info = self.extension_map.get(extension, {
            'category': 'unknown',
            'language': None,
            'importance': 0.5
        })

        # Initialize result
        result = SemanticAnalysisResult(
            file_path=str(path),
            file_type=extension,
            semantic_category=file_info['category'],
            importance_score=file_info['importance'],
            language=file_info.get('language'),
            tags=[file_info['category']]
        )

        # Add filename-based tags
        filename = path.name.lower()
        if 'test' in filename:
            result.tags.append('test')
            result.importance_score *= 0.8
        if 'config' in filename or 'settings' in filename:
            result.tags.append('configuration')
            result.importance_score *= 1.2
        if filename in ['readme.md', 'license', 'contributing.md']:
            result.tags.append('documentation')
            result.importance_score *= 1.3

        # Detect framework if code file
        if result.semantic_category == 'code':
            framework = self._detect_framework(path)
            if framework:
                result.framework = framework
                result.tags.append(f'framework:{framework}')

        # Calculate final importance (cap at 1.0)
        result.importance_score = min(result.importance_score, 1.0)

        logger.debug(
            f"Analyzed {file_path}: {result.semantic_category} "
            f"(importance: {result.importance_score:.2f})"
        )

        return result

    def _detect_framework(self, file_path: Path) -> Optional[str]:
        """Detect framework from file path and content"""
        path_str = str(file_path).lower()

        for framework, patterns in self.framework_patterns.items():
            if any(pattern in path_str for pattern in patterns):
                return framework

        return None

    async def analyze_batch(self, file_paths: List[str]) -> List[SemanticAnalysisResult]:
        """
        Analyze multiple files

        Args:
            file_paths: List of file paths

        Returns:
            List of SemanticAnalysisResult
        """
        results = []
        for file_path in file_paths:
            try:
                result = await self.analyze_file(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {str(e)}")

        return results

    def get_category_statistics(
        self,
        results: List[SemanticAnalysisResult]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate statistics by category

        Args:
            results: List of analysis results

        Returns:
            Dictionary of statistics by category
        """
        stats: Dict[str, Dict[str, Any]] = {}

        for result in results:
            category = result.semantic_category

            if category not in stats:
                stats[category] = {
                    'count': 0,
                    'avg_importance': 0.0,
                    'languages': set(),
                    'frameworks': set()
                }

            stats[category]['count'] += 1
            stats[category]['avg_importance'] += result.importance_score

            if result.language:
                stats[category]['languages'].add(result.language)
            if result.framework:
                stats[category]['frameworks'].add(result.framework)

        # Calculate averages and convert sets to lists
        for category, data in stats.items():
            if data['count'] > 0:
                data['avg_importance'] /= data['count']
            data['languages'] = list(data['languages'])
            data['frameworks'] = list(data['frameworks'])

        return stats
