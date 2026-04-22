#!/usr/bin/env python3
"""
Unit tests for API Discovery Tool
Level 1 Verification - Must pass before proceeding
"""

import pytest
import tempfile
import json
import ast
from pathlib import Path
import yaml
from api_discovery import APIDiscoverer, APIEndpoint, generate_markdown_api_report


class TestPythonParsing:
    """Test Python file parsing for FastAPI/Flask endpoints."""
    
    def test_fastapi_get_endpoint(self):
        """Test parsing FastAPI GET endpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test Python file with FastAPI endpoint
            py_file = Path(tmpdir) / "test_app.py"
            py_file.write_text('''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    return {"users": []}
''')
            
            discoverer = APIDiscoverer(root_dir=tmpdir)
            discoverer._scan_python_file("TestProject", py_file)
            
            assert len(discoverer.endpoints) == 1
            endpoint = discoverer.endpoints[0]
            assert endpoint.method == "GET"
            assert endpoint.path == "/users"
            assert endpoint.function_name == "get_users"
            assert endpoint.source_framework == "fastapi"
    
    def test_fastapi_post_endpoint_with_params(self):
        """Test parsing FastAPI POST endpoint with parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test_app.py"
            py_file.write_text('''
from fastapi import FastAPI

app = FastAPI()

@app.post("/users")
def create_user(name: str, email: str):
    return {"id": 1}
''')
            
            discoverer = APIDiscoverer(root_dir=tmpdir)
            discoverer._scan_python_file("TestProject", py_file)
            
            assert len(discoverer.endpoints) == 1
            endpoint = discoverer.endpoints[0]
            assert endpoint.method == "POST"
            assert endpoint.path == "/users"
            assert len(endpoint.parameters) == 2
            assert endpoint.parameters[0]["name"] == "name"
            assert endpoint.parameters[1]["name"] == "email"
    
    def test_flask_route_endpoint(self):
        """Test parsing Flask route endpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test_app.py"
            py_file.write_text('''
from flask import Flask

app = Flask(__name__)

@app.route("/items", methods=["GET"])
def get_items():
    return {"items": []}
''')
            
            discoverer = APIDiscoverer(root_dir=tmpdir)
            discoverer._scan_python_file("TestProject", py_file)
            
            assert len(discoverer.endpoints) == 1
            endpoint = discoverer.endpoints[0]
            assert endpoint.method == "GET"
            assert endpoint.path == "/items"
            assert endpoint.source_framework == "flask"
    
    def test_multiple_endpoints_in_file(self):
        """Test parsing multiple endpoints in one file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test_app.py"
            py_file.write_text('''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    pass

@app.post("/users")
def create_user():
    pass

@app.get("/items")
def get_items():
    pass
''')
            
            discoverer = APIDiscoverer(root_dir=tmpdir)
            discoverer._scan_python_file("TestProject", py_file)
            
            assert len(discoverer.endpoints) == 3
            methods = [ep.method for ep in discoverer.endpoints]
            assert "GET" in methods
            assert "POST" in methods
    
    def test_endpoint_with_path_parameters(self):
        """Test parsing endpoint with path parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test_app.py"
            py_file.write_text('''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"id": user_id}
''')
            
            discoverer = APIDiscoverer(root_dir=tmpdir)
            discoverer._scan_python_file("TestProject", py_file)
            
            assert len(discoverer.endpoints) == 1
            endpoint = discoverer.endpoints[0]
            assert endpoint.path == "/users/{user_id}"
            assert len(endpoint.parameters) >= 1


class TestJSParsing:
    """Test JavaScript/TypeScript file parsing for Express endpoints."""
    
    def test_express_get_endpoint(self):
        """Test parsing Express GET endpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            js_file = Path(tmpdir) / "server.js"
            js_file.write_text('''
const express = require('express');
const app = express();

app.get('/api/users', (req, res) => {
    res.json({ users: [] });
});
''')
            
            discoverer = APIDiscoverer(root_dir=tmpdir)
            discoverer._scan_js_file("TestProject", js_file)
            
            assert len(discoverer.endpoints) == 1
            endpoint = discoverer.endpoints[0]
            assert endpoint.method == "GET"
            assert endpoint.path == "/api/users"
            assert endpoint.source_framework == "express"
    
    def test_express_post_endpoint(self):
        """Test parsing Express POST endpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            js_file = Path(tmpdir) / "routes.js"
            js_file.write_text('''
const router = require('express').Router();

router.post('/create', async (req, res) => {
    const result = await createItem(req.body);
    res.json(result);
});
''')
            
            discoverer = APIDiscoverer(root_dir=tmpdir)
            discoverer._scan_js_file("TestProject", js_file)
            
            assert len(discoverer.endpoints) == 1
            endpoint = discoverer.endpoints[0]
            assert endpoint.method == "POST"
            assert endpoint.path == "/create"
    
    def test_express_multiple_methods(self):
        """Test parsing multiple Express methods."""
        with tempfile.TemporaryDirectory() as tmpdir:
            js_file = Path(tmpdir) / "api.js"
            js_file.write_text('''
app.get('/items', handler);
app.post('/items', handler);
app.put('/items/:id', handler);
app.delete('/items/:id', handler);
''')
            
            discoverer = APIDiscoverer(root_dir=tmpdir)
            discoverer._scan_js_file("TestProject", js_file)
            
            assert len(discoverer.endpoints) == 4
            methods = [ep.method for ep in discoverer.endpoints]
            assert set(methods) == {"GET", "POST", "PUT", "DELETE"}


class TestReportGeneration:
    """Test report generation."""
    
    def test_json_report_structure(self):
        """Test JSON report has correct structure."""
        discoverer = APIDiscoverer(root_dir="/tmp")
        discoverer.endpoints = [
            APIEndpoint("p1", "f1.py", "GET", "/users", "get_users", 1, source_framework="fastapi"),
            APIEndpoint("p1", "f1.py", "POST", "/users", "create_user", 5, source_framework="fastapi"),
            APIEndpoint("p2", "f2.js", "GET", "/items", "get_items", 1, source_framework="express")
        ]
        
        report = discoverer.generate_report()
        
        assert "generated_at" in report
        assert report["total_endpoints"] == 3
        assert report["by_method"]["GET"] == 2
        assert report["by_method"]["POST"] == 1
        assert report["by_framework"]["fastapi"] == 2
        assert report["by_framework"]["express"] == 1
        assert len(report["by_project"]["p1"]) == 2
        assert len(report["by_project"]["p2"]) == 1
    
    def test_openapi_spec_generation(self):
        """Test OpenAPI spec generation."""
        discoverer = APIDiscoverer(root_dir="/tmp")
        discoverer.endpoints = [
            APIEndpoint("p1", "f1.py", "GET", "/users", "get_users", 1, 
                       parameters=[{"name": "page", "in": "query", "required": False, "type": "integer"}]),
            APIEndpoint("p1", "f1.py", "POST", "/users", "create_user", 5, auth_required=True)
        ]
        
        spec = discoverer.generate_openapi_spec()
        
        assert spec["openapi"] == "3.0.0"
        assert "info" in spec
        assert "paths" in spec
        assert "/users" in spec["paths"]
        assert "get" in spec["paths"]["/users"]
        assert "post" in spec["paths"]["/users"]
        assert spec["paths"]["/users"]["post"]["security"] == [{"bearerAuth": []}]
    
    def test_markdown_report_generation(self):
        """Test Markdown report generation."""
        report = {
            "generated_at": "2026-03-04T12:00:00",
            "total_endpoints": 2,
            "by_method": {"GET": 1, "POST": 1},
            "by_framework": {"fastapi": 2},
            "test_summary": {"tested": 0, "accessible": 0, "not_tested": 2},
            "by_project": {
                "TestProject": [
                    {
                        "project": "TestProject",
                        "file": "app.py",
                        "method": "GET",
                        "path": "/users",
                        "function_name": "get_users",
                        "line_number": 5,
                        "auth_required": False,
                        "parameters": [],
                        "source_framework": "fastapi",
                        "status": "discovered",
                        "test_result": None
                    }
                ]
            },
            "endpoints": [],
            "errors": []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test_report.md"
            generate_markdown_api_report(report, md_path)
            
            content = md_path.read_text()
            
            assert "# API Endpoint Inventory" in content
            assert "TestProject" in content
            assert "GET" in content
            assert "/users" in content
            assert "fastapi" in content


class TestRealProjectValidation:
    """
    Validation tests against the actual ReliantAI project.
    These tests verify the discovery works on the real codebase.
    """
    
    def test_discovers_money_endpoints(self):
        """Verify Money endpoints are discovered."""
        discoverer = APIDiscoverer(root_dir="/home/donovan/Projects/ReliantAI")
        discoverer._scan_project("Money")
        
        money_endpoints = [e for e in discoverer.endpoints if e.project == "Money"]
        
        # Money should have multiple endpoints
        assert len(money_endpoints) >= 5
        
        # Should have GET endpoints
        get_endpoints = [e for e in money_endpoints if e.method == "GET"]
        assert len(get_endpoints) > 0
        
        # Should have POST endpoints
        post_endpoints = [e for e in money_endpoints if e.method == "POST"]
        assert len(post_endpoints) > 0
    
    def test_discovers_citadel_endpoints(self):
        """Verify Citadel endpoints are discovered."""
        discoverer = APIDiscoverer(root_dir="/home/donovan/Projects/ReliantAI")
        discoverer._scan_project("Citadel")
        
        citadel_endpoints = [e for e in discoverer.endpoints if e.project == "Citadel"]
        
        # Citadel should have many endpoints
        assert len(citadel_endpoints) >= 10
    
    def test_discovers_gen_h_endpoints(self):
        """Verify Gen-H has Express endpoints."""
        discoverer = APIDiscoverer(root_dir="/home/donovan/Projects/ReliantAI")
        discoverer._scan_project("Gen-H")
        
        gen_h_endpoints = [e for e in discoverer.endpoints if e.project == "Gen-H"]
        
        # Should find Express endpoints
        express_endpoints = [e for e in gen_h_endpoints if e.source_framework == "express"]
        assert len(express_endpoints) > 0
    
    def test_reports_saved_to_proof_directory(self):
        """Verify reports are saved to the proof directory."""
        # Run the discovery
        report = main()
        
        # Verify files exist
        json_path = Path("/home/donovan/Projects/ReliantAI/integration/proof/phase_0/api_inventory.json")
        yaml_path = Path("/home/donovan/Projects/ReliantAI/integration/proof/phase_0/api_inventory.yaml")
        md_path = Path("/home/donovan/Projects/ReliantAI/integration/proof/phase_0/API_INVENTORY.md")
        
        assert json_path.exists(), "JSON report not saved"
        assert yaml_path.exists(), "YAML report not saved"
        assert md_path.exists(), "Markdown report not saved"
        
        # Verify JSON is valid
        with open(json_path) as f:
            data = json.load(f)
            assert "total_endpoints" in data
            assert data["total_endpoints"] > 0
        
        # Verify YAML is valid OpenAPI
        with open(yaml_path) as f:
            spec = yaml.safe_load(f)
            assert spec.get("openapi") == "3.0.0"
            assert "paths" in spec


def main():
    """Run the discovery and return report."""
    discoverer = APIDiscoverer()
    discoverer.discover_all()
    return discoverer.generate_report()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
