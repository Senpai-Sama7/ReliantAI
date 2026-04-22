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

# Service configuration
SERVICES = {
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
    }
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
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    status = {
                        "status": "healthy",
                        "response_time": response.elapsed.total_seconds(),
                        "data": data
                    }
                except:
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
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_services": total_count,
                "healthy": healthy_count,
                "unhealthy": total_count - healthy_count,
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
        print(f"Timestamp: {report['timestamp']}")
        
        print("\n📋 Service Details:")
        print("-"*60)
        
        for name, result in report["services"].items():
            emoji = "✅" if result["status"] == "healthy" else "❌"
            print(f"  {emoji} {name:15} → {result['status']}")
            
            if "response_time" in result:
                print(f"     └─ Response time: {result['response_time']:.3f}s")
            
            if "error" in result:
                print(f"     └─ Error: {result['error']}")
        
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
    args = parser.parse_args()
    
    checker = HealthChecker(verbose=args.verbose)
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
