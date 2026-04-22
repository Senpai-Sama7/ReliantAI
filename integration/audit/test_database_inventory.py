#!/usr/bin/env python3
"""
Unit tests for Database Inventory Tool
Level 1 Verification - Must pass before proceeding
"""

import pytest
import tempfile
import sqlite3
import json
from pathlib import Path
from database_inventory import DatabaseAuditor, DatabaseInfo, generate_markdown_report


class TestSQLiteAudit:
    """Test SQLite database auditing."""
    
    def test_sqlite_database_found_and_audited(self):
        """Test that SQLite databases are found and properly audited."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test database
            db_path = Path(tmpdir) / "test.db"
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Create test tables
            cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
            cursor.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER)")
            cursor.execute("INSERT INTO users VALUES (1, 'Alice')")
            conn.commit()
            conn.close()
            
            # Create a mock project structure
            project_dir = Path(tmpdir) / "TestProject"
            project_dir.mkdir()
            
            # Move the database into the project
            db_in_project = project_dir / "app.db"
            db_path.rename(db_in_project)
            
            # Audit the project
            auditor = DatabaseAuditor(root_dir=tmpdir)
            auditor._find_sqlite_databases("TestProject", project_dir)
            
            # Verify results
            assert len(auditor.results) == 1
            db_info = auditor.results[0]
            
            assert db_info.project == "TestProject"
            assert db_info.db_type == "sqlite"
            assert db_info.database == "app.db"
            assert db_info.status == "connected"
            assert "users" in db_info.tables
            assert "orders" in db_info.tables
            assert "sqlite_sequence" in db_info.tables
            assert db_info.version is not None
    
    def test_corrupt_sqlite_handled(self):
        """Test that corrupt SQLite files are handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a corrupt "database" file
            project_dir = Path(tmpdir) / "BadProject"
            project_dir.mkdir()
            
            db_path = project_dir / "corrupt.db"
            db_path.write_text("This is not a valid SQLite database")
            
            # Audit should not crash
            auditor = DatabaseAuditor(root_dir=tmpdir)
            auditor._audit_sqlite("BadProject", db_path)
            
            assert len(auditor.results) == 1
            assert auditor.results[0].status == "error"
            assert auditor.results[0].error_message is not None


class TestReportGeneration:
    """Test report generation."""
    
    def test_json_report_structure(self):
        """Test JSON report has correct structure."""
        auditor = DatabaseAuditor(root_dir="/tmp")
        auditor.results = [
            DatabaseInfo("test1", "sqlite", None, None, "test.db", None, "3.39", ["t1"], "connected"),
            DatabaseInfo("test2", "postgresql", "localhost", 5432, "testdb", "user", "14", ["t1", "t2"], "connected"),
            DatabaseInfo("test3", "redis", "localhost", 6379, "0", None, "7.0", ["keys: 5"], "error", "Connection refused")
        ]
        
        report = auditor.generate_report()
        
        # Verify structure
        assert "generated_at" in report
        assert report["total_databases"] == 3
        assert report["by_type"]["sqlite"] == 1
        assert report["by_type"]["postgresql"] == 1
        assert report["by_type"]["redis"] == 1
        assert report["summary"]["connected"] == 2
        assert report["summary"]["errors"] == 1
        assert len(report["databases"]) == 3
    
    def test_markdown_report_generation(self):
        """Test Markdown report is generated correctly."""
        report = {
            "generated_at": "2026-03-04T12:00:00",
            "total_databases": 2,
            "by_type": {"sqlite": 1, "postgresql": 1},
            "by_status": {"connected": 2},
            "by_project": {
                "TestProject": [
                    {
                        "project": "TestProject",
                        "db_type": "sqlite",
                        "database": "app.db",
                        "status": "connected",
                        "version": "3.39",
                        "tables": ["users", "orders"],
                        "file_path": "TestProject/app.db",
                        "host": None,
                        "port": None,
                        "error_message": None
                    }
                ]
            },
            "summary": {"connected": 2, "errors": 0, "not_running": 0, "file_not_found": 0},
            "errors_during_scan": []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test_report.md"
            generate_markdown_report(report, md_path)
            
            content = md_path.read_text()
            
            assert "# Database Infrastructure Inventory" in content
            assert "TestProject" in content
            assert "sqlite" in content
            assert "app.db" in content
            assert "users" in content
            assert "orders" in content


class TestProjectScanning:
    """Test full project scanning."""
    
    def test_empty_project(self):
        """Test scanning project with no databases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "EmptyProject"
            project_dir.mkdir()
            
            auditor = DatabaseAuditor(root_dir=tmpdir)
            auditor._scan_project("EmptyProject")
            
            assert len(auditor.results) == 0
    
    def test_multiple_databases_in_project(self):
        """Test project with multiple databases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "MultiDbProject"
            project_dir.mkdir()
            
            # Create multiple SQLite databases
            for i in range(3):
                db_path = project_dir / f"db{i}.sqlite"
                conn = sqlite3.connect(str(db_path))
                conn.execute(f"CREATE TABLE table{i} (id INTEGER)")
                conn.close()
            
            auditor = DatabaseAuditor(root_dir=tmpdir)
            auditor._scan_project("MultiDbProject")
            
            assert len(auditor.results) == 3
            assert all(r.status == "connected" for r in auditor.results)


class TestRealProjectValidation:
    """
    Validation tests against the actual ReliantAI project.
    These tests verify the audit works on the real codebase.
    """
    
    def test_audit_finds_money_database(self):
        """Verify Money dispatch.db is found."""
        auditor = DatabaseAuditor(root_dir="/home/donovan/Projects/ReliantAI")
        auditor._scan_project("Money")
        
        money_dbs = [r for r in auditor.results if r.project == "Money"]
        
        # Should find at least the dispatch.db
        assert len(money_dbs) >= 1
        
        dispatch_db = next((r for r in money_dbs if r.database == "dispatch.db"), None)
        assert dispatch_db is not None, "dispatch.db not found"
        assert dispatch_db.status == "connected"
        assert "dispatches" in dispatch_db.tables
    
    def test_audit_finds_citadel_ultimate_db(self):
        """Verify citadel_ultimate_a_plus lead_queue.db is found."""
        auditor = DatabaseAuditor(root_dir="/home/donovan/Projects/ReliantAI")
        auditor._scan_project("citadel_ultimate_a_plus")
        
        citadel_dbs = [r for r in auditor.results if r.project == "citadel_ultimate_a_plus"]
        
        assert len(citadel_dbs) >= 1
        
        lead_db = next((r for r in citadel_dbs if r.database == "lead_queue.db"), None)
        assert lead_db is not None, "lead_queue.db not found"
        assert lead_db.status == "connected"
    
    def test_report_saved_to_proof_directory(self):
        """Verify reports are saved to the proof directory."""
        import os
        
        # Run the audit
        report = main()
        
        # Verify files exist
        json_path = Path("/home/donovan/Projects/ReliantAI/integration/proof/phase_0/database_inventory.json")
        md_path = Path("/home/donovan/Projects/ReliantAI/integration/proof/phase_0/DATABASE_INVENTORY.md")
        
        assert json_path.exists(), "JSON report not saved"
        assert md_path.exists(), "Markdown report not saved"
        
        # Verify JSON is valid
        with open(json_path) as f:
            data = json.load(f)
            assert "total_databases" in data
            assert data["total_databases"] > 0


def main():
    """Run the audit and return report."""
    auditor = DatabaseAuditor()
    auditor.scan_all_projects()
    return auditor.generate_report()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
