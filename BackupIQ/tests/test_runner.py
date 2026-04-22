#!/usr/bin/env python3
"""
Enterprise Test Runner
Comprehensive testing framework for FAANG-grade quality assurance
"""

import os
import sys
import json
import time
import subprocess
import pytest
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

# Test configuration
TEST_CONFIG = {
    "coverage_threshold": 95,
    "performance_threshold_seconds": 30,
    "memory_threshold_mb": 512,
    "max_test_duration_minutes": 15,
    "parallel_workers": 4
}

@dataclass
class TestResult:
    """Test result data structure"""
    category: str
    name: str
    status: str  # passed, failed, skipped
    duration: float
    details: Dict[str, Any]

@dataclass
class TestSummary:
    """Test summary data structure"""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration: float
    coverage_percent: float
    categories: Dict[str, int]

class EnterpriseTestRunner:
    """Enterprise-grade test runner with comprehensive reporting"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or TEST_CONFIG
        self.results: List[TestResult] = []
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup structured logger for test execution"""
        logger = logging.getLogger("test_runner")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def run_unit_tests(self) -> List[TestResult]:
        """Run unit tests with coverage"""
        self.logger.info("🧪 Running unit tests...")

        start_time = time.time()

        # Run pytest with coverage
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "--cov=src/",
            f"--cov-fail-under={self.config['coverage_threshold']}",
            "--cov-report=json",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--json-report",
            "--json-report-file=test-results/unit-results.json",
            f"-n={self.config['parallel_workers']}",
            "--tb=short",
            "-v"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            duration = time.time() - start_time

            # Parse results
            coverage_data = self._parse_coverage_report()
            test_data = self._parse_pytest_results("test-results/unit-results.json")

            test_result = TestResult(
                category="unit",
                name="unit_tests",
                status="passed" if result.returncode == 0 else "failed",
                duration=duration,
                details={
                    "coverage_percent": coverage_data.get("percent_covered", 0),
                    "tests_run": test_data.get("total", 0),
                    "tests_passed": test_data.get("passed", 0),
                    "tests_failed": test_data.get("failed", 0),
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            )

            self.results.append(test_result)
            self.logger.info(f"✅ Unit tests completed in {duration:.2f}s")
            return [test_result]

        except subprocess.TimeoutExpired:
            test_result = TestResult(
                category="unit",
                name="unit_tests",
                status="failed",
                duration=600,
                details={"error": "Test execution timeout"}
            )
            self.results.append(test_result)
            self.logger.error("❌ Unit tests timed out")
            return [test_result]

    def run_integration_tests(self) -> List[TestResult]:
        """Run integration tests"""
        self.logger.info("🔗 Running integration tests...")

        start_time = time.time()

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "--json-report",
            "--json-report-file=test-results/integration-results.json",
            "-v",
            "--tb=short"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            duration = time.time() - start_time

            test_data = self._parse_pytest_results("test-results/integration-results.json")

            test_result = TestResult(
                category="integration",
                name="integration_tests",
                status="passed" if result.returncode == 0 else "failed",
                duration=duration,
                details={
                    "tests_run": test_data.get("total", 0),
                    "tests_passed": test_data.get("passed", 0),
                    "tests_failed": test_data.get("failed", 0),
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            )

            self.results.append(test_result)
            self.logger.info(f"✅ Integration tests completed in {duration:.2f}s")
            return [test_result]

        except subprocess.TimeoutExpired:
            test_result = TestResult(
                category="integration",
                name="integration_tests",
                status="failed",
                duration=900,
                details={"error": "Test execution timeout"}
            )
            self.results.append(test_result)
            self.logger.error("❌ Integration tests timed out")
            return [test_result]

    def run_performance_tests(self) -> List[TestResult]:
        """Run performance benchmarks"""
        self.logger.info("⚡ Running performance tests...")

        start_time = time.time()

        cmd = [
            sys.executable, "-m", "pytest",
            "tests/performance/",
            "--benchmark-json=test-results/benchmark-results.json",
            "-v"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            duration = time.time() - start_time

            benchmark_data = self._parse_benchmark_results()

            test_result = TestResult(
                category="performance",
                name="performance_tests",
                status="passed" if result.returncode == 0 else "failed",
                duration=duration,
                details={
                    "benchmarks": benchmark_data,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            )

            self.results.append(test_result)
            self.logger.info(f"✅ Performance tests completed in {duration:.2f}s")
            return [test_result]

        except subprocess.TimeoutExpired:
            test_result = TestResult(
                category="performance",
                name="performance_tests",
                status="failed",
                duration=1800,
                details={"error": "Performance test timeout"}
            )
            self.results.append(test_result)
            self.logger.error("❌ Performance tests timed out")
            return [test_result]

    def run_security_tests(self) -> List[TestResult]:
        """Run security scans and tests"""
        self.logger.info("🛡️ Running security tests...")

        results = []

        # Bandit security scan
        bandit_result = self._run_bandit_scan()
        results.append(bandit_result)

        # Safety dependency scan
        safety_result = self._run_safety_scan()
        results.append(safety_result)

        # Secret detection
        secret_result = self._run_secret_detection()
        results.append(secret_result)

        self.results.extend(results)
        return results

    def _run_bandit_scan(self) -> TestResult:
        """Run Bandit security scanner"""
        start_time = time.time()

        cmd = [
            sys.executable, "-m", "bandit",
            "-r", "src/",
            "-f", "json",
            "-o", "test-results/bandit-results.json"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            duration = time.time() - start_time

            # Parse bandit results
            bandit_data = {}
            if os.path.exists("test-results/bandit-results.json"):
                with open("test-results/bandit-results.json", 'r') as f:
                    bandit_data = json.load(f)

            # Check for high/medium severity issues
            high_issues = [r for r in bandit_data.get("results", [])
                          if r.get("issue_severity") == "HIGH"]
            medium_issues = [r for r in bandit_data.get("results", [])
                           if r.get("issue_severity") == "MEDIUM"]

            status = "failed" if high_issues else "passed"

            return TestResult(
                category="security",
                name="bandit_scan",
                status=status,
                duration=duration,
                details={
                    "high_issues": len(high_issues),
                    "medium_issues": len(medium_issues),
                    "total_issues": len(bandit_data.get("results", [])),
                    "issues": bandit_data.get("results", [])
                }
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                category="security",
                name="bandit_scan",
                status="failed",
                duration=300,
                details={"error": "Bandit scan timeout"}
            )

    def _run_safety_scan(self) -> TestResult:
        """Run Safety dependency vulnerability scan"""
        start_time = time.time()

        cmd = [sys.executable, "-m", "safety", "check", "--json"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            duration = time.time() - start_time

            vulnerabilities = []
            if result.stdout:
                try:
                    vulnerabilities = json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass

            status = "failed" if vulnerabilities else "passed"

            return TestResult(
                category="security",
                name="safety_scan",
                status=status,
                duration=duration,
                details={
                    "vulnerabilities": len(vulnerabilities),
                    "details": vulnerabilities
                }
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                category="security",
                name="safety_scan",
                status="failed",
                duration=180,
                details={"error": "Safety scan timeout"}
            )

    def _run_secret_detection(self) -> TestResult:
        """Run secret detection scan"""
        start_time = time.time()

        # Simple regex-based secret detection
        secrets_found = []
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]

        for py_file in Path("src/").rglob("*.py"):
            try:
                content = py_file.read_text()
                for pattern in secret_patterns:
                    import re
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        secrets_found.append({
                            "file": str(py_file),
                            "pattern": pattern,
                            "matches": len(matches)
                        })
            except Exception:
                continue

        duration = time.time() - start_time
        status = "failed" if secrets_found else "passed"

        return TestResult(
            category="security",
            name="secret_detection",
            status=status,
            duration=duration,
            details={
                "secrets_found": len(secrets_found),
                "details": secrets_found
            }
        )

    def _parse_coverage_report(self) -> Dict[str, Any]:
        """Parse coverage report"""
        try:
            with open("coverage.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"percent_covered": 0}

    def _parse_pytest_results(self, filepath: str) -> Dict[str, Any]:
        """Parse pytest JSON results"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                summary = data.get("summary", {})
                return {
                    "total": summary.get("total", 0),
                    "passed": summary.get("passed", 0),
                    "failed": summary.get("failed", 0),
                    "skipped": summary.get("skipped", 0)
                }
        except FileNotFoundError:
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 0}

    def _parse_benchmark_results(self) -> Dict[str, Any]:
        """Parse benchmark results"""
        try:
            with open("test-results/benchmark-results.json", 'r') as f:
                data = json.load(f)
                benchmarks = data.get("benchmarks", [])
                return {
                    "count": len(benchmarks),
                    "benchmarks": benchmarks
                }
        except FileNotFoundError:
            return {"count": 0, "benchmarks": []}

    def generate_summary(self) -> TestSummary:
        """Generate comprehensive test summary"""
        total_tests = len(self.results)
        passed = len([r for r in self.results if r.status == "passed"])
        failed = len([r for r in self.results if r.status == "failed"])
        skipped = len([r for r in self.results if r.status == "skipped"])

        total_duration = sum(r.duration for r in self.results)

        # Get coverage from unit test results
        coverage = 0
        for result in self.results:
            if result.category == "unit":
                coverage = result.details.get("coverage_percent", 0)
                break

        # Count by category
        categories = {}
        for result in self.results:
            cat = result.category
            categories[cat] = categories.get(cat, 0) + 1

        return TestSummary(
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=total_duration,
            coverage_percent=coverage,
            categories=categories
        )

    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        summary = self.generate_summary()

        report = f"""
# 🧪 Enterprise Test Report

## 📊 Test Summary

- **Total Tests**: {summary.total_tests}
- **Passed**: {summary.passed} ✅
- **Failed**: {summary.failed} ❌
- **Skipped**: {summary.skipped} ⏭️
- **Duration**: {summary.duration:.2f}s
- **Coverage**: {summary.coverage_percent:.1f}%

## 📈 Quality Gates

{'✅ PASSED' if summary.coverage_percent >= self.config['coverage_threshold'] else '❌ FAILED'} - Coverage: {summary.coverage_percent:.1f}% (threshold: {self.config['coverage_threshold']}%)
{'✅ PASSED' if summary.failed == 0 else '❌ FAILED'} - Zero test failures
{'✅ PASSED' if summary.duration <= self.config['max_test_duration_minutes'] * 60 else '❌ FAILED'} - Duration: {summary.duration:.1f}s (threshold: {self.config['max_test_duration_minutes'] * 60}s)

## 📋 Test Categories

"""

        for category, count in summary.categories.items():
            report += f"- **{category.title()}**: {count} tests\n"

        report += "\n## 🔍 Detailed Results\n\n"

        for result in self.results:
            status_emoji = "✅" if result.status == "passed" else ("❌" if result.status == "failed" else "⏭️")
            report += f"### {status_emoji} {result.category.title()}: {result.name}\n"
            report += f"- **Status**: {result.status}\n"
            report += f"- **Duration**: {result.duration:.2f}s\n"

            # Add category-specific details
            if result.category == "unit":
                details = result.details
                report += f"- **Coverage**: {details.get('coverage_percent', 0):.1f}%\n"
                report += f"- **Tests Run**: {details.get('tests_run', 0)}\n"
            elif result.category == "security":
                details = result.details
                if result.name == "bandit_scan":
                    report += f"- **High Issues**: {details.get('high_issues', 0)}\n"
                    report += f"- **Medium Issues**: {details.get('medium_issues', 0)}\n"
                elif result.name == "safety_scan":
                    report += f"- **Vulnerabilities**: {details.get('vulnerabilities', 0)}\n"
                elif result.name == "secret_detection":
                    report += f"- **Secrets Found**: {details.get('secrets_found', 0)}\n"

            report += "\n"

        return report

    def run_all_tests(self) -> TestSummary:
        """Run complete test suite"""
        self.logger.info("🚀 Starting enterprise test suite...")

        # Create results directory
        os.makedirs("test-results", exist_ok=True)

        start_time = time.time()

        # Run all test categories
        self.run_unit_tests()
        self.run_integration_tests()
        self.run_performance_tests()
        self.run_security_tests()

        total_duration = time.time() - start_time

        # Generate and save report
        report = self.generate_report()
        with open("test-results/test-report.md", 'w') as f:
            f.write(report)

        summary = self.generate_summary()

        # Log final results
        if summary.failed == 0:
            self.logger.info(f"🎉 All tests passed! Duration: {total_duration:.2f}s")
        else:
            self.logger.error(f"❌ {summary.failed} tests failed. Duration: {total_duration:.2f}s")

        return summary

def main():
    """Main test runner entry point"""
    runner = EnterpriseTestRunner()
    summary = runner.run_all_tests()

    # Exit with non-zero code if tests failed
    sys.exit(0 if summary.failed == 0 else 1)

if __name__ == "__main__":
    main()