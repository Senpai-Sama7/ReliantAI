#!/usr/bin/env python3
"""
ReliantAI Platform Health Check
Verifies all services are running and healthy
"""

import sys
import json
import argparse
from typing import Dict, List, Any
from datetime import datetime

try:
    import requests
except ImportError:
    print("Error: requests package not installed. Run: pip install requests")
    sys.exit(1)

# Service configuration — ALL 20+ platform services
SERVICES = {
    # Core critical services
    "money": {
        "url": "http://localhost:8000",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": True
    },
    "complianceone": {
        "url": "http://localhost:8001",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": True
    },
    "finops360": {
        "url": "http://localhost:8002",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": True
    },
    "integration": {
        "url": "http://localhost:8080",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    "orchestrator": {
        "url": "http://localhost:9000",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": True
    },
    "nginx": {
        "url": "http://localhost:80",
        "health_endpoint": "/nginx-health",
        "api_key": None,
        "critical": False
    },
    # Infrastructure
    "vault": {
        "url": "http://localhost:8200",
        "health_endpoint": "/v1/sys/health?standbyok=true",
        "api_key": None,
        "critical": False
    },
    # Analytics & AI
    "bap": {
        "url": "http://localhost:8108",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    "apex-agents": {
        "url": "http://localhost:8109",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    "apex-ui": {
        "url": "http://localhost:8112",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    "apex-mcp": {
        "url": "http://localhost:4000",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    "acropolis": {
        "url": "http://localhost:8110",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    # Operations Intelligence
    "ops-intelligence-backend": {
        "url": "http://localhost:8095",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    "ops-intelligence-frontend": {
        "url": "http://localhost:5174",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    # Security & Observability
    "citadel": {
        "url": "http://localhost:8100",
        "health_endpoint": "/api/health",
        "api_key": None,
        "critical": False
    },
    "citadel-ultimate-a-plus": {
        "url": "http://localhost:8111",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    # Frontends
    "cleardesk": {
        "url": "http://localhost:8101",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    "gen-h": {
        "url": "http://localhost:8102",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    "regenesis": {
        "url": "http://localhost:8107",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    # Specialized Services
    "documancer": {
        "url": "http://localhost:8103",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    "backupiq": {
        "url": "http://localhost:8104",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    "cyberarchitect": {
        "url": "http://localhost:8105",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
    "sovieren-ai": {
        "url": "http://localhost:8106",
        "health_endpoint": "/health",
        "api_key": None,
        "critical": False
    },
}

class HealthChecker:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {}
        self.errors = []
    
    def check_service(self, name: str, config: Dict) -> Dict[str, Any]:
        """Check health of a single service"""
        url = f"{config['url']}{config['health_endpoint']}"
        
        try:
            response = requests.get(url, timeout=10)
            
            # Vault /sys/health returns 200 or 429 (standby) as healthy
            is_healthy = response.status_code in (200, 204, 429)
            
            if is_healthy:
                try:
                    data = response.json()
                    status = {
                        "status": "healthy",
                        "response_time": response.elapsed.total_seconds(),
                        "data": data
                    }
                except Exception:
                    status = {
                        "status": "healthy",
                        "response_time": response.elapsed.total_seconds()
                    }
            else:
                status = {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "response_time": response.elapsed.total_seconds()
                }
                if config.get("critical"):
                    self.errors.append(f"{name}: HTTP {response.status_code}")
                    
        except requests.exceptions.ConnectionError:
            status = {"status": "unreachable", "error": "Connection refused"}
            if config.get("critical"):
                self.errors.append(f"{name}: Connection refused")
                
        except requests.exceptions.Timeout:
            status = {"status": "timeout", "error": "Request timed out"}
            if config.get("critical"):
                self.errors.append(f"{name}: Timeout")
                
        except Exception as e:
            status = {"status": "error", "error": str(e)}
            if config.get("critical"):
                self.errors.append(f"{name}: {str(e)}")
        
        return status
    
    def check_all(self) -> Dict[str, Any]:
        """Check all services"""
        print("🔍 Checking ReliantAI Platform Health...\n")
        
        for name, config in SERVICES.items():
            if self.verbose:
                print(f"  Checking {name}...", end=" ")
            
            result = self.check_service(name, config)
            self.results[name] = result
            
            if self.verbose:
                status_emoji = "✅" if result["status"] == "healthy" else "❌"
                print(f"{status_emoji} {result['status']}")
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate health report"""
        healthy_count = sum(1 for r in self.results.values() if r["status"] == "healthy")
        total_count = len(self.results)
        critical_services = [n for n, c in SERVICES.items() if c.get("critical")]
        critical_healthy = sum(1 for n in critical_services if self.results.get(n, {}).get("status") == "healthy")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_services": total_count,
                "healthy": healthy_count,
                "unhealthy": total_count - healthy_count,
                "critical_total": len(critical_services),
                "critical_healthy": critical_healthy,
                "status": "healthy" if healthy_count == total_count else "degraded" if healthy_count > 0 else "critical"
            },
            "services": self.results
        }
        
        if self.errors:
            report["errors"] = self.errors
        
        return report
    
    def print_report(self, report: Dict):
        """Print formatted report"""
        print("\n" + "="*60)
        print("📊 RELIANTAI PLATFORM HEALTH REPORT")
        print("="*60)
        
        summary = report["summary"]
        status_emoji = "✅" if summary["status"] == "healthy" else "⚠️" if summary["status"] == "degraded" else "❌"
        
        print(f"\nStatus: {status_emoji} {summary['status'].upper()}")
        print(f"Services: {summary['healthy']}/{summary['total_services']} healthy")
        print(f"Critical: {summary['critical_healthy']}/{summary['critical_total']} healthy")
        print(f"Timestamp: {report['timestamp']}")
        
        print("\n📋 Service Details:")
        print("-"*60)
        
        # Group by status for readability
        healthy = [(n, r) for n, r in report["services"].items() if r["status"] == "healthy"]
        unhealthy = [(n, r) for n, r in report["services"].items() if r["status"] != "healthy"]
        
        if healthy:
            print("\n  ✅ Healthy Services:")
            for name, result in healthy:
                print(f"     {name:25} → {result['status']} ({result.get('response_time', 0):.3f}s)")
        
        if unhealthy:
            print("\n  ❌ Unhealthy Services:")
            for name, result in unhealthy:
                print(f"     {name:25} → {result['status']}")
                if "error" in result:
                    print(f"        └─ Error: {result['error']}")
        
        if report.get("errors"):
            print("\n❌ Critical Errors:")
            print("-"*60)
            for error in report["errors"]:
                print(f"  • {error}")
        
        print("\n" + "="*60)
        
        return summary["status"] == "healthy"

def main():
    parser = argparse.ArgumentParser(description="ReliantAI Platform Health Check")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-j", "--json", action="store_true", help="Output as JSON")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode (exit code only)")
    parser.add_argument("--critical-only", action="store_true", help="Check only critical services")
    args = parser.parse_args()
    
    checker = HealthChecker(verbose=args.verbose)
    
    # Filter to critical only if requested
    if args.critical_only:
        global SERVICES
        SERVICES = {k: v for k, v in SERVICES.items() if v.get("critical")}
    
    report = checker.check_all()
    
    if args.json:
        print(json.dumps(report, indent=2))
        sys.exit(0 if report["summary"]["status"] == "healthy" else 1)
    
    if not args.quiet:
        is_healthy = checker.print_report(report)
    else:
        is_healthy = report["summary"]["status"] == "healthy"
    
    sys.exit(0 if is_healthy else 1)

if __name__ == "__main__":
    main()
