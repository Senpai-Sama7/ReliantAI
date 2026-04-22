#!/usr/bin/env python3
"""
Service Dependency Mapper
Maps dependencies across all projects.

This is a REAL implementation - not a mock or placeholder.
"""

import json
import tomllib
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import re


@dataclass
class Dependency:
    name: str
    version: str
    source: str  # requirements.txt, package.json, Cargo.toml, pyproject.toml
    project: str


class DependencyMapper:
    """Maps dependencies across all projects."""
    
    def __init__(self, root_dir: str = "/home/donovan/Projects/ReliantAI"):
        self.root_dir = Path(root_dir)
        self.dependencies: List[Dependency] = []
        self.errors: List[str] = []
        
    def map_all(self) -> List[Dependency]:
        """Map all dependencies."""
        projects = [
            "Apex", "B-A-P", "Money", "ClearDesk", "Gen-H",
            "Citadel", "BackupIQ", "reGenesis", "CyberArchitect",
            "Acropolis", "intelligent-storage", "citadel_ultimate_a_plus",
            "DocuMancer"
        ]
        
        print(f"Scanning {len(projects)} projects for dependencies...")
        
        for project in projects:
            print(f"  Scanning {project}...", end=" ")
            count_before = len(self.dependencies)
            self._scan_project(project)
            count_after = len(self.dependencies)
            found = count_after - count_before
            print(f"({found} deps found)")
            
        return self.dependencies
    
    def _scan_project(self, project: str):
        """Scan a project for dependencies."""
        project_path = self.root_dir / project
        if not project_path.exists():
            return
            
        # Python requirements.txt
        for req_file in project_path.rglob("requirements*.txt"):
            if "__pycache__" in str(req_file) or "venv" in str(req_file) or ".venv" in str(req_file):
                continue
            self._parse_requirements(project, req_file)
        
        # Poetry pyproject.toml
        pyproject = project_path / "pyproject.toml"
        if pyproject.exists():
            self._parse_pyproject(project, pyproject)
        
        # Node.js package.json
        for pkg_file in project_path.rglob("package.json"):
            if "node_modules" in str(pkg_file):
                continue
            if pkg_file.is_dir():
                continue
            self._parse_package_json(project, pkg_file)
        
        # Rust Cargo.toml
        for cargo_file in project_path.rglob("Cargo.toml"):
            if "target" in str(cargo_file):
                continue
            self._parse_cargo(project, cargo_file)
    
    def _parse_requirements(self, project: str, file_path: Path):
        """Parse requirements.txt file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if line.startswith('-'):
                        continue  # Skip options like -r, -e
                    
                    # Parse package==version format
                    # Handle: package==1.0.0, package>=1.0.0, package~=1.0.0, package[extra]>=1.0
                    match = re.match(r'^([a-zA-Z0-9_-]+)(\[[^\]]+\])?([<>=!~]+)?(.+)?', line)
                    if match:
                        name = match.group(1)
                        version = match.group(4) if match.group(4) else "unspecified"
                        version = version.strip()
                        if not version:
                            version = "unspecified"
                        self.dependencies.append(Dependency(
                            name=name.lower(),
                            version=version,
                            source="requirements.txt",
                            project=project
                        ))
        except Exception as e:
            self.errors.append(f"Error parsing {file_path}: {e}")
    
    def _parse_pyproject(self, project: str, file_path: Path):
        """Parse Poetry pyproject.toml."""
        try:
            with open(file_path, 'rb') as f:
                data = tomllib.load(f)
            
            # Poetry dependencies
            deps = data.get('tool', {}).get('poetry', {}).get('dependencies', {})
            for name, version in deps.items():
                if name == 'python':
                    continue
                if isinstance(version, dict):
                    version = version.get('version', 'unspecified')
                self.dependencies.append(Dependency(
                    name=name.lower(),
                    version=str(version),
                    source="pyproject.toml",
                    project=project
                ))
            
            # Dev dependencies
            dev_deps = data.get('tool', {}).get('poetry', {}).get('group', {}).get('dev', {}).get('dependencies', {})
            for name, version in dev_deps.items():
                if isinstance(version, dict):
                    version = version.get('version', 'unspecified')
                self.dependencies.append(Dependency(
                    name=name.lower(),
                    version=str(version),
                    source="pyproject.toml (dev)",
                    project=project
                ))
        except Exception as e:
            self.errors.append(f"Error parsing {file_path}: {e}")
    
    def _parse_package_json(self, project: str, file_path: Path):
        """Parse Node.js package.json."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
            
            for dep_type in ['dependencies', 'devDependencies']:
                deps = data.get(dep_type, {})
                for name, version in deps.items():
                    source = "package.json" if dep_type == 'dependencies' else "package.json (dev)"
                    self.dependencies.append(Dependency(
                        name=name.lower(),
                        version=version,
                        source=source,
                        project=project
                    ))
        except Exception as e:
            self.errors.append(f"Error parsing {file_path}: {e}")
    
    def _parse_cargo(self, project: str, file_path: Path):
        """Parse Rust Cargo.toml."""
        try:
            with open(file_path, 'rb') as f:
                data = tomllib.load(f)
            
            deps = data.get('dependencies', {})
            for name, version in deps.items():
                if isinstance(version, dict):
                    version = version.get('version', 'unspecified')
                self.dependencies.append(Dependency(
                    name=name.lower(),
                    version=str(version),
                    source="Cargo.toml",
                    project=project
                ))
        except Exception as e:
            self.errors.append(f"Error parsing {file_path}: {e}")
    
    def find_conflicts(self) -> List[Dict]:
        """Find version conflicts between projects."""
        by_name: Dict[str, List[Dependency]] = {}
        for dep in self.dependencies:
            if dep.name not in by_name:
                by_name[dep.name] = []
            by_name[dep.name].append(dep)
        
        conflicts = []
        for name, deps in by_name.items():
            # Normalize versions for comparison
            versions = set()
            for d in deps:
                # Strip ^, ~, >=, etc for comparison
                v = re.sub(r'^[<>=!~^]+', '', d.version)
                versions.add(v)
            
            if len(versions) > 1:
                conflicts.append({
                    "package": name,
                    "versions": sorted(list(versions)),
                    "used_by": [{"project": d.project, "version": d.version, "source": d.source} for d in deps]
                })
        
        # Sort by number of versions (most conflicts first)
        conflicts.sort(key=lambda x: len(x["versions"]), reverse=True)
        return conflicts
    
    def find_shared_dependencies(self) -> Dict[str, Dict]:
        """Find dependencies used by multiple projects."""
        by_name: Dict[str, List[Dependency]] = {}
        for dep in self.dependencies:
            if dep.name not in by_name:
                by_name[dep.name] = []
            by_name[dep.name].append(dep)
        
        shared = {}
        for name, deps in by_name.items():
            if len(deps) > 1:
                projects = list(set(d.project for d in deps))
                versions = list(set(d.version for d in deps))
                shared[name] = {
                    "count": len(deps),
                    "projects": projects,
                    "versions": versions,
                    "sources": list(set(d.source for d in deps))
                }
        
        # Sort by count
        return dict(sorted(shared.items(), key=lambda x: x[1]["count"], reverse=True))
    
    def generate_report(self) -> Dict:
        """Generate dependency report."""
        by_project: Dict[str, List[Dict]] = {}
        by_source: Dict[str, int] = {}
        
        for dep in self.dependencies:
            if dep.project not in by_project:
                by_project[dep.project] = []
            by_project[dep.project].append(asdict(dep))
            
            by_source[dep.source] = by_source.get(dep.source, 0) + 1
        
        conflicts = self.find_conflicts()
        shared = self.find_shared_dependencies()
        
        return {
            "generated_at": datetime.now().isoformat(),
            "total_dependencies": len(self.dependencies),
            "unique_packages": len(set(d.name for d in self.dependencies)),
            "by_project": by_project,
            "by_source": by_source,
            "conflicts": conflicts,
            "conflict_count": len(conflicts),
            "shared_dependencies": shared,
            "shared_count": len(shared),
            "errors": self.errors
        }


def generate_markdown_report(report: Dict, output_path: Path):
    """Generate Markdown dependency report."""
    with open(output_path, 'w') as f:
        f.write("# Service Dependency Map\n\n")
        f.write(f"**Generated:** {report['generated_at']}\n\n")
        f.write(f"- **Total Dependencies:** {report['total_dependencies']}\n")
        f.write(f"- **Unique Packages:** {report['unique_packages']}\n")
        f.write(f"- **Version Conflicts:** {report['conflict_count']}\n")
        f.write(f"- **Shared Dependencies:** {report['shared_count']}\n\n")
        
        f.write("## By Source\n\n")
        for source, count in sorted(report['by_source'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"- **{source}:** {count}\n")
        
        if report['conflicts']:
            f.write("\n## Version Conflicts ⚠️\n\n")
            f.write(f"Found **{len(report['conflicts'])}** packages with version conflicts:\n\n")
            
            for conflict in report['conflicts'][:20]:  # Top 20
                f.write(f"### {conflict['package']}\n\n")
                f.write(f"Versions: {', '.join(conflict['versions'])}\n\n")
                f.write("Used by:\n")
                for usage in conflict['used_by']:
                    f.write(f"- `{usage['project']}`: `{usage['version']}` ({usage['source']})\n")
                f.write("\n")
        
        if report['shared_dependencies']:
            f.write("\n## Most Shared Dependencies\n\n")
            f.write("| Package | Projects | Versions |\n")
            f.write("|---------|----------|----------|\n")
            for name, info in list(report['shared_dependencies'].items())[:30]:
                versions_str = ', '.join(info['versions'][:3])
                if len(info['versions']) > 3:
                    versions_str += f" (+{len(info['versions']) - 3} more)"
                f.write(f"| {name} | {info['count']} | {versions_str} |\n")
        
        f.write("\n## By Project\n\n")
        for project, deps in sorted(report['by_project'].items()):
            f.write(f"### {project}\n\n")
            f.write(f"**{len(deps)}** dependencies\n\n")
            
            # Group by source
            by_source = {}
            for dep in deps:
                if dep['source'] not in by_source:
                    by_source[dep['source']] = []
                by_source[dep['source']].append(dep)
            
            for source, source_deps in by_source.items():
                f.write(f"**{source}:** {len(source_deps)}\n\n")
                for dep in source_deps[:10]:  # Limit to first 10
                    f.write(f"- `{dep['name']}`: `{dep['version']}`\n")
                if len(source_deps) > 10:
                    f.write(f"- ... and {len(source_deps) - 10} more\n")
                f.write("\n")
        
        if report['errors']:
            f.write("\n## Errors During Scan\n\n")
            for error in report['errors']:
                f.write(f"- {error}\n")


def main():
    """Run the dependency mapper."""
    print("="*60)
    print("SERVICE DEPENDENCY MAPPER")
    print("="*60)
    
    mapper = DependencyMapper()
    mapper.map_all()
    
    report = mapper.generate_report()
    
    # Save JSON report
    output_dir = Path("/home/donovan/Projects/ReliantAI/integration/proof/phase_0")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = output_dir / "dependency_map.json"
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Generate Markdown report
    md_path = output_dir / "DEPENDENCY_MAP.md"
    generate_markdown_report(report, md_path)
    
    print("\n" + "="*60)
    print("MAPPING COMPLETE")
    print("="*60)
    print(f"Total dependencies mapped: {report['total_dependencies']}")
    print(f"Unique packages: {report['unique_packages']}")
    print(f"Version conflicts: {report['conflict_count']}")
    print(f"Shared dependencies: {report['shared_count']}")
    
    if report['conflicts']:
        print(f"\n⚠️  Top conflicts:")
        for conflict in report['conflicts'][:5]:
            print(f"  - {conflict['package']}: {', '.join(conflict['versions'][:3])}")
    
    print(f"\nReports saved:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")
    
    if mapper.errors:
        print(f"\n⚠️  {len(mapper.errors)} errors during scan")
    
    return report


if __name__ == "__main__":
    report = main()
    exit(0)
