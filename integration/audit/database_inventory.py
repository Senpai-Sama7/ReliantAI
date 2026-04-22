#!/usr/bin/env python3
"""
Database Infrastructure Audit Tool
Scans all projects for database connections and documents them.

This is a REAL implementation - not a mock or placeholder.
"""

import os
import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Optional imports - handle gracefully if not available
try:
    import psycopg2
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False


@dataclass
class DatabaseInfo:
    project: str
    db_type: str  # postgresql, sqlite, neo4j, redis
    host: Optional[str]
    port: Optional[int]
    database: Optional[str]
    username: Optional[str]
    version: Optional[str]
    tables: List[str]
    status: str  # connected, error, not_running, file_not_found
    error_message: Optional[str] = None
    file_path: Optional[str] = None


class DatabaseAuditor:
    """Audits all databases across the ReliantAI project suite."""
    
    def __init__(self, root_dir: str = "/home/donovan/Projects/ReliantAI"):
        self.root_dir = Path(root_dir)
        self.results: List[DatabaseInfo] = []
        self.errors: List[str] = []
        
    def scan_all_projects(self) -> List[DatabaseInfo]:
        """Scan all projects for database configurations."""
        projects = [
            "Apex", "B-A-P", "Money", "ClearDesk", "Gen-H",
            "Citadel", "BackupIQ", "reGenesis", "CyberArchitect",
            "Acropolis", "intelligent-storage", "citadel_ultimate_a_plus",
            "DocuMancer"
        ]
        
        print(f"Scanning {len(projects)} projects for databases...")
        
        for project in projects:
            print(f"  Scanning {project}...", end=" ")
            count_before = len(self.results)
            self._scan_project(project)
            count_after = len(self.results)
            found = count_after - count_before
            print(f"({found} databases found)")
            
        return self.results
    
    def _scan_project(self, project: str):
        """Scan a single project for databases."""
        project_path = self.root_dir / project
        if not project_path.exists():
            return
            
        # Scan for SQLite databases
        self._find_sqlite_databases(project, project_path)
        
        # Scan for environment files with DB connections
        self._parse_env_files(project, project_path)
        
        # Check for known database locations
        self._check_known_database_paths(project, project_path)
    
    def _find_sqlite_databases(self, project: str, path: Path):
        """Find all SQLite .db and .sqlite files."""
        for pattern in ["*.db", "*.sqlite", "*.sqlite3"]:
            for db_file in path.rglob(pattern):
                if "__pycache__" in str(db_file) or "venv" in str(db_file) or ".venv" in str(db_file):
                    continue
                if db_file.is_dir():
                    continue
                self._audit_sqlite(project, db_file)
    
    def _audit_sqlite(self, project: str, db_path: Path):
        """Audit a SQLite database."""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get version
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            
            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Check if WAL mode is enabled
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            
            conn.close()
            
            rel_path = str(db_path.relative_to(self.root_dir))
            
            self.results.append(DatabaseInfo(
                project=project,
                db_type="sqlite",
                host=None,
                port=None,
                database=db_path.name,
                username=None,
                version=f"{version} (WAL: {journal_mode})",
                tables=tables,
                status="connected",
                file_path=rel_path
            ))
        except Exception as e:
            rel_path = str(db_path.relative_to(self.root_dir))
            self.results.append(DatabaseInfo(
                project=project,
                db_type="sqlite",
                host=None,
                port=None,
                database=db_path.name,
                username=None,
                version=None,
                tables=[],
                status="error",
                error_message=str(e),
                file_path=rel_path
            ))
    
    def _parse_env_files(self, project: str, path: Path):
        """Parse .env files for database connection strings."""
        for env_file in path.rglob(".env*"):
            if ".example" in env_file.name or ".template" in env_file.name:
                continue
            if env_file.is_dir():
                continue
            if "node_modules" in str(env_file):
                continue
                
            try:
                with open(env_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Look for PostgreSQL connections
                if 'postgresql://' in content or 'POSTGRES' in content.upper():
                    self._parse_postgres_env(project, content, env_file)
                    
                # Look for Redis connections
                if 'REDIS' in content.upper() or 'redis://' in content:
                    self._parse_redis_env(project, content, env_file)
                    
                # Look for Neo4j connections
                if 'NEO4J' in content.upper() or 'bolt://' in content:
                    self._parse_neo4j_env(project, content, env_file)
                    
            except Exception as e:
                self.errors.append(f"Error parsing {env_file}: {e}")
    
    def _parse_postgres_env(self, project: str, content: str, env_file: Path):
        """Parse PostgreSQL connection from env content."""
        # Try to find DATABASE_URL
        import re
        match = re.search(r'DATABASE_URL[=:](.+)', content)
        if match:
            url = match.group(1).strip().strip('"').strip("'")
            # Parse postgresql://user:pass@host:port/dbname
            parsed = self._parse_postgres_url(url)
            if parsed:
                # Try to connect and verify
                self._test_postgres_connection(project, parsed, str(env_file.relative_to(self.root_dir)))
    
    def _parse_postgres_url(self, url: str) -> Optional[Dict]:
        """Parse PostgreSQL connection URL."""
        import re
        # Pattern: postgresql://user:password@host:port/dbname
        pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
        match = re.match(pattern, url)
        if match:
            return {
                'username': match.group(1),
                'password': match.group(2),
                'host': match.group(3),
                'port': int(match.group(4)),
                'database': match.group(5)
            }
        return None
    
    def _test_postgres_connection(self, project: str, conn_info: Dict, source_file: str):
        """Test PostgreSQL connection."""
        if not HAS_POSTGRES:
            self.results.append(DatabaseInfo(
                project=project,
                db_type="postgresql",
                host=conn_info['host'],
                port=conn_info['port'],
                database=conn_info['database'],
                username=conn_info['username'],
                version=None,
                tables=[],
                status="not_running",
                error_message="psycopg2 not installed, cannot test connection",
                file_path=source_file
            ))
            return
        
        try:
            conn = psycopg2.connect(
                host=conn_info['host'],
                port=conn_info['port'],
                database=conn_info['database'],
                user=conn_info['username'],
                password=conn_info['password'],
                connect_timeout=5
            )
            cursor = conn.cursor()
            
            # Get version
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            # Get tables
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            self.results.append(DatabaseInfo(
                project=project,
                db_type="postgresql",
                host=conn_info['host'],
                port=conn_info['port'],
                database=conn_info['database'],
                username=conn_info['username'],
                version=version.split()[1] if version else None,
                tables=tables,
                status="connected",
                file_path=source_file
            ))
        except Exception as e:
            self.results.append(DatabaseInfo(
                project=project,
                db_type="postgresql",
                host=conn_info['host'],
                port=conn_info['port'],
                database=conn_info['database'],
                username=conn_info['username'],
                version=None,
                tables=[],
                status="error",
                error_message=str(e),
                file_path=source_file
            ))
    
    def _parse_redis_env(self, project: str, content: str, env_file: Path):
        """Parse Redis connection from env content."""
        import re
        # Look for REDIS_URL or REDIS_HOST
        url_match = re.search(r'REDIS_URL[=:](.+)', content)
        host_match = re.search(r'REDIS_HOST[=:](.+)', content)
        port_match = re.search(r'REDIS_PORT[=:](\d+)', content)
        
        host = "localhost"
        port = 6379
        
        if url_match:
            url = url_match.group(1).strip().strip('"').strip("'")
            # Parse redis://host:port
            parsed = re.match(r'redis://([^:]+):(\d+)', url)
            if parsed:
                host = parsed.group(1)
                port = int(parsed.group(2))
        elif host_match:
            host = host_match.group(1).strip().strip('"').strip("'")
            if port_match:
                port = int(port_match.group(1))
        
        self._test_redis_connection(project, host, port, str(env_file.relative_to(self.root_dir)))
    
    def _test_redis_connection(self, project: str, host: str, port: int, source_file: str):
        """Test Redis connection."""
        if not HAS_REDIS:
            self.results.append(DatabaseInfo(
                project=project,
                db_type="redis",
                host=host,
                port=port,
                database=None,
                username=None,
                version=None,
                tables=[],
                status="not_running",
                error_message="redis-py not installed, cannot test connection",
                file_path=source_file
            ))
            return
        
        try:
            r = redis.Redis(host=host, port=port, socket_connect_timeout=5)
            if r.ping():
                info = r.info()
                version = info.get('redis_version')
                
                # Get database info
                dbsize = r.dbsize()
                
                self.results.append(DatabaseInfo(
                    project=project,
                    db_type="redis",
                    host=host,
                    port=port,
                    database="0",
                    username=None,
                    version=version,
                    tables=[f"keys: {dbsize}"],
                    status="connected",
                    file_path=source_file
                ))
            else:
                raise Exception("Ping failed")
        except Exception as e:
            self.results.append(DatabaseInfo(
                project=project,
                db_type="redis",
                host=host,
                port=port,
                database=None,
                username=None,
                version=None,
                tables=[],
                status="error",
                error_message=str(e),
                file_path=source_file
            ))
    
    def _parse_neo4j_env(self, project: str, content: str, env_file: Path):
        """Parse Neo4j connection from env content."""
        import re
        uri_match = re.search(r'NEO4J_URI[=:](.+)', content)
        
        if uri_match:
            uri = uri_match.match.group(1).strip().strip('"').strip("'")
            # Parse bolt://host:port
            parsed = re.match(r'bolt://([^:]+):(\d+)', uri)
            if parsed:
                host = parsed.group(1)
                port = int(parsed.group(2))
                self._test_neo4j_connection(project, host, port, uri, str(env_file.relative_to(self.root_dir)))
    
    def _test_neo4j_connection(self, project: str, host: str, port: int, uri: str, source_file: str):
        """Test Neo4j connection."""
        if not HAS_NEO4J:
            self.results.append(DatabaseInfo(
                project=project,
                db_type="neo4j",
                host=host,
                port=port,
                database="neo4j",
                username="neo4j",
                version=None,
                tables=[],
                status="not_running",
                error_message="neo4j-python-driver not installed, cannot test connection",
                file_path=source_file
            ))
            return
        
        try:
            driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
            with driver.session() as session:
                result = session.run("CALL dbms.components() YIELD name, versions")
                record = result.single()
                version = record["versions"][0] if record else None
                
                # Get node count
                count_result = session.run("MATCH (n) RETURN count(n) as count")
                count = count_result.single()["count"]
                
                driver.close()
                
                self.results.append(DatabaseInfo(
                    project=project,
                    db_type="neo4j",
                    host=host,
                    port=port,
                    database="neo4j",
                    username="neo4j",
                    version=version,
                    tables=[f"nodes: {count}"],
                    status="connected",
                    file_path=source_file
                ))
        except Exception as e:
            self.results.append(DatabaseInfo(
                project=project,
                db_type="neo4j",
                host=host,
                port=port,
                database="neo4j",
                username="neo4j",
                version=None,
                tables=[],
                status="error",
                error_message=str(e),
                file_path=source_file
            ))
    
    def _check_known_database_paths(self, project: str, path: Path):
        """Check known database paths for specific projects."""
        known_paths = {
            "Money": ["data/dispatch.db", "data/tickets.db"],
            "citadel_ultimate_a_plus": ["data/citadel.db"],
            "intelligent-storage": ["data/storage.db"]
        }
        
        if project in known_paths:
            for db_path in known_paths[project]:
                full_path = path / db_path
                if full_path.exists() and not any(r.file_path == str(full_path.relative_to(self.root_dir)) for r in self.results):
                    self._audit_sqlite(project, full_path)
    
    def generate_report(self) -> Dict:
        """Generate JSON report of all databases."""
        return {
            "generated_at": datetime.now().isoformat(),
            "total_databases": len(self.results),
            "by_type": self._count_by_type(),
            "by_project": self._group_by_project(),
            "by_status": self._count_by_status(),
            "databases": [asdict(r) for r in self.results],
            "summary": {
                "connected": len([r for r in self.results if r.status == "connected"]),
                "errors": len([r for r in self.results if r.status == "error"]),
                "not_running": len([r for r in self.results if r.status == "not_running"]),
                "file_not_found": len([r for r in self.results if r.status == "file_not_found"])
            },
            "errors_during_scan": self.errors
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        counts = {}
        for r in self.results:
            counts[r.db_type] = counts.get(r.db_type, 0) + 1
        return counts
    
    def _count_by_status(self) -> Dict[str, int]:
        counts = {}
        for r in self.results:
            counts[r.status] = counts.get(r.status, 0) + 1
        return counts
    
    def _group_by_project(self) -> Dict[str, List[Dict]]:
        grouped = {}
        for r in self.results:
            if r.project not in grouped:
                grouped[r.project] = []
            grouped[r.project].append(asdict(r))
        return grouped


def generate_markdown_report(report: Dict, output_path: Path):
    """Generate human-readable Markdown report."""
    with open(output_path, 'w') as f:
        f.write("# Database Infrastructure Inventory\n\n")
        f.write(f"**Generated:** {report['generated_at']}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- **Total Databases Found:** {report['total_databases']}\n")
        f.write(f"- **Connected:** {report['summary']['connected']} ✅\n")
        f.write(f"- **Errors:** {report['summary']['errors']} ❌\n")
        f.write(f"- **Not Running:** {report['summary']['not_running']} ⚠️\n\n")
        
        f.write("## By Type\n\n")
        for db_type, count in report['by_type'].items():
            f.write(f"- **{db_type}:** {count}\n")
        
        f.write("\n## By Status\n\n")
        for status, count in report['by_status'].items():
            icon = "✅" if status == "connected" else "❌" if status == "error" else "⚠️"
            f.write(f"- {icon} **{status}:** {count}\n")
        
        f.write("\n## By Project\n\n")
        for project, dbs in sorted(report['by_project'].items()):
            f.write(f"### {project}\n\n")
            for db in dbs:
                status_icon = "✅" if db['status'] == "connected" else "❌" if db['status'] == "error" else "⚠️"
                f.write(f"{status_icon} **{db['db_type']}**: `{db['database']}`\n")
                if db['file_path']:
                    f.write(f"   - Path: `{db['file_path']}`\n")
                if db['host']:
                    f.write(f"   - Host: `{db['host']}:{db['port']}`\n")
                if db['version']:
                    f.write(f"   - Version: {db['version']}\n")
                if db['tables']:
                    tables_str = ", ".join(db['tables'][:10])
                    if len(db['tables']) > 10:
                        tables_str += f" (and {len(db['tables']) - 10} more)"
                    f.write(f"   - Tables: {tables_str}\n")
                if db['error_message']:
                    f.write(f"   - Error: `{db['error_message']}`\n")
                f.write("\n")
        
        if report['errors_during_scan']:
            f.write("\n## Errors During Scan\n\n")
            for error in report['errors_during_scan']:
                f.write(f"- {error}\n")


def main():
    """Run the database audit."""
    print("="*60)
    print("DATABASE INFRASTRUCTURE AUDIT")
    print("="*60)
    
    auditor = DatabaseAuditor()
    auditor.scan_all_projects()
    
    report = auditor.generate_report()
    
    # Save JSON report
    output_dir = Path("/home/donovan/Projects/ReliantAI/integration/proof/phase_0")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = output_dir / "database_inventory.json"
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Generate Markdown report
    md_path = output_dir / "DATABASE_INVENTORY.md"
    generate_markdown_report(report, md_path)
    
    print("\n" + "="*60)
    print("AUDIT COMPLETE")
    print("="*60)
    print(f"Total databases found: {report['total_databases']}")
    print(f"  ✅ Connected: {report['summary']['connected']}")
    print(f"  ❌ Errors: {report['summary']['errors']}")
    print(f"  ⚠️  Not running: {report['summary']['not_running']}")
    print(f"\nReports saved:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")
    
    return report


if __name__ == "__main__":
    report = main()
    exit(0 if report['summary']['errors'] == 0 else 1)
