#!/usr/bin/env python3
"""
Unit tests for Dependency Mapper
Level 1 Verification - Must pass before proceeding
"""

import pytest
import tempfile
import json
from pathlib import Path
from dependency_mapper import DependencyMapper, Dependency, generate_markdown_report


class TestRequirementsParsing:
    """Test requirements.txt parsing."""
    
    def test_parse_simple_requirements(self):
        """Test parsing simple requirements.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("""
fastapi==0.109.0
pydantic>=2.0.0
requests
# This is a comment

redis==4.5.0
""")
            
            mapper = DependencyMapper(root_dir=tmpdir)
            mapper._parse_requirements("TestProject", req_file)
            
            assert len(mapper.dependencies) == 4
            
            names = [d.name for d in mapper.dependencies]
            assert "fastapi" in names
            assert "pydantic" in names
            assert "requests" in names
            assert "redis" in names
    
    def test_parse_requirements_with_extras(self):
        """Test parsing requirements with extras."""
        with tempfile.TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("uvicorn[standard]==0.29.0\n")
            
            mapper = DependencyMapper(root_dir=tmpdir)
            mapper._parse_requirements("TestProject", req_file)
            
            assert len(mapper.dependencies) == 1
            assert mapper.dependencies[0].name == "uvicorn"
            assert mapper.dependencies[0].version == "0.29.0"
    
    def test_parse_requirements_skips_options(self):
        """Test that -r and -e options are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            req_file = Path(tmpdir) / "requirements.txt"
            req_file.write_text("""
-r other.txt
-e git+https://github.com/user/repo.git#egg=package
fastapi==0.109.0
""")
            
            mapper = DependencyMapper(root_dir=tmpdir)
            mapper._parse_requirements("TestProject", req_file)
            
            assert len(mapper.dependencies) == 1
            assert mapper.dependencies[0].name == "fastapi"


class TestPackageJsonParsing:
    """Test package.json parsing."""
    
    def test_parse_package_json(self):
        """Test parsing package.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_file = Path(tmpdir) / "package.json"
            pkg_file.write_text(json.dumps({
                "name": "test-project",
                "dependencies": {
                    "react": "^18.0.0",
                    "express": "~4.18.0"
                },
                "devDependencies": {
                    "typescript": "^5.0.0"
                }
            }))
            
            mapper = DependencyMapper(root_dir=tmpdir)
            mapper._parse_package_json("TestProject", pkg_file)
            
            assert len(mapper.dependencies) == 3
            
            names = [d.name for d in mapper.dependencies]
            assert "react" in names
            assert "express" in names
            assert "typescript" in names
            
            # Check sources
            dev_deps = [d for d in mapper.dependencies if "dev" in d.source]
            assert len(dev_deps) == 1
            assert dev_deps[0].name == "typescript"


class TestConflictDetection:
    """Test version conflict detection."""
    
    def test_find_simple_conflict(self):
        """Test detecting simple version conflicts."""
        mapper = DependencyMapper()
        mapper.dependencies = [
            Dependency("fastapi", "0.109.0", "requirements.txt", "proj1"),
            Dependency("fastapi", "0.110.0", "requirements.txt", "proj2"),
            Dependency("pydantic", "2.0.0", "requirements.txt", "proj1"),
            Dependency("pydantic", "2.0.0", "requirements.txt", "proj2")
        ]
        
        conflicts = mapper.find_conflicts()
        
        assert len(conflicts) == 1
        assert conflicts[0]["package"] == "fastapi"
        assert len(conflicts[0]["versions"]) == 2
        assert "0.109.0" in conflicts[0]["versions"]
        assert "0.110.0" in conflicts[0]["versions"]
    
    def test_no_conflict_for_same_version(self):
        """Test that same versions don't create conflicts."""
        mapper = DependencyMapper()
        mapper.dependencies = [
            Dependency("fastapi", "0.109.0", "requirements.txt", "proj1"),
            Dependency("fastapi", "0.109.0", "requirements.txt", "proj2"),
        ]
        
        conflicts = mapper.find_conflicts()
        
        assert len(conflicts) == 0
    
    def test_conflict_with_prefixes(self):
        """Test that ^, ~, >= are stripped for comparison."""
        mapper = DependencyMapper()
        mapper.dependencies = [
            Dependency("fastapi", "^0.109.0", "requirements.txt", "proj1"),
            Dependency("fastapi", "~0.110.0", "requirements.txt", "proj2"),
            Dependency("fastapi", ">=0.111.0", "package.json", "proj3"),
        ]
        
        conflicts = mapper.find_conflicts()
        
        assert len(conflicts) == 1
        assert "0.109.0" in conflicts[0]["versions"]
        assert "0.110.0" in conflicts[0]["versions"]
        assert "0.111.0" in conflicts[0]["versions"]


class TestSharedDependencies:
    """Test shared dependency detection."""
    
    def test_find_shared_dependencies(self):
        """Test finding dependencies used by multiple projects."""
        mapper = DependencyMapper()
        mapper.dependencies = [
            Dependency("fastapi", "0.109.0", "requirements.txt", "proj1"),
            Dependency("fastapi", "0.109.0", "requirements.txt", "proj2"),
            Dependency("fastapi", "0.109.0", "requirements.txt", "proj3"),
            Dependency("unique", "1.0.0", "requirements.txt", "proj1"),
        ]
        
        shared = mapper.find_shared_dependencies()
        
        assert "fastapi" in shared
        assert shared["fastapi"]["count"] == 3
        assert "unique" not in shared  # Only used by one project


class TestReportGeneration:
    """Test report generation."""
    
    def test_json_report_structure(self):
        """Test JSON report has correct structure."""
        mapper = DependencyMapper(root_dir="/tmp")
        mapper.dependencies = [
            Dependency("fastapi", "0.109.0", "requirements.txt", "proj1"),
            Dependency("pydantic", "2.0.0", "requirements.txt", "proj1"),
            Dependency("fastapi", "0.110.0", "requirements.txt", "proj2"),
        ]
        
        report = mapper.generate_report()
        
        assert "generated_at" in report
        assert report["total_dependencies"] == 3
        assert report["unique_packages"] == 2  # fastapi, pydantic
        assert report["conflict_count"] == 1  # fastapi has 2 versions
        assert report["shared_count"] == 1  # fastapi is shared
        assert len(report["conflicts"]) == 1
        assert len(report["shared_dependencies"]) == 1
    
    def test_markdown_report_generation(self):
        """Test Markdown report generation."""
        report = {
            "generated_at": "2026-03-04T12:00:00",
            "total_dependencies": 10,
            "unique_packages": 5,
            "conflict_count": 1,
            "shared_count": 2,
            "by_source": {"requirements.txt": 8, "package.json": 2},
            "conflicts": [
                {
                    "package": "fastapi",
                    "versions": ["0.109.0", "0.110.0"],
                    "used_by": [
                        {"project": "proj1", "version": "0.109.0", "source": "requirements.txt"},
                        {"project": "proj2", "version": "0.110.0", "source": "requirements.txt"}
                    ]
                }
            ],
            "shared_dependencies": {
                "fastapi": {"count": 2, "projects": ["proj1", "proj2"], "versions": ["0.109.0", "0.110.0"], "sources": ["requirements.txt"]}
            },
            "by_project": {
                "proj1": [{"name": "fastapi", "version": "0.109.0", "source": "requirements.txt", "project": "proj1"}]
            },
            "errors": []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test_report.md"
            generate_markdown_report(report, md_path)
            
            content = md_path.read_text()
            
            assert "# Service Dependency Map" in content
            assert "fastapi" in content
            assert "0.109.0" in content
            assert "0.110.0" in content
            assert "Version Conflicts" in content


class TestRealProjectValidation:
    """
    Validation tests against the actual ReliantAI project.
    """
    
    def test_maps_real_dependencies(self):
        """Verify real dependencies are mapped."""
        mapper = DependencyMapper(root_dir="/home/donovan/Projects/ReliantAI")
        mapper.map_all()
        
        # Should find many dependencies
        assert len(mapper.dependencies) > 100
        
        # Should find common packages
        names = [d.name for d in mapper.dependencies]
        assert "fastapi" in names or any("fast" in n for n in names)
    
    def test_finds_conflicts_in_real_project(self):
        """Verify conflicts are found in real project."""
        mapper = DependencyMapper(root_dir="/home/donovan/Projects/ReliantAI")
        mapper.map_all()
        
        conflicts = mapper.find_conflicts()
        
        # Should find some conflicts (multiple projects use same packages)
        assert len(conflicts) > 0
    
    def test_reports_saved_to_proof_directory(self):
        """Verify reports are saved to the proof directory."""
        # Run the mapper
        report = main()
        
        # Verify files exist
        json_path = Path("/home/donovan/Projects/ReliantAI/integration/proof/phase_0/dependency_map.json")
        md_path = Path("/home/donovan/Projects/ReliantAI/integration/proof/phase_0/DEPENDENCY_MAP.md")
        
        assert json_path.exists(), "JSON report not saved"
        assert md_path.exists(), "Markdown report not saved"
        
        # Verify JSON is valid
        with open(json_path) as f:
            data = json.load(f)
            assert "total_dependencies" in data
            assert data["total_dependencies"] > 0


def main():
    """Run the mapper and return report."""
    mapper = DependencyMapper()
    mapper.map_all()
    return mapper.generate_report()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
