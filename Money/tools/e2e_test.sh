#!/usr/bin/env bash
# E2E smoke test for Houston HVAC AI Dispatch
# Requires: real .env with all API keys configured
# Usage: bash tools/e2e_test.sh
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
PASS=0; FAIL=0; BASE="http://127.0.0.1:8000"

check() {
    local desc="$1" cmd="$2" expect="$3"
    result=$(eval "$cmd" 2>/dev/null) || true
    if echo "$result" | grep -q "$expect"; then
        echo -e "  ${GREEN}✓${NC} $desc"
        ((PASS++))
    else
        echo -e "  ${RED}✗${NC} $desc (expected: $expect)"
        ((FAIL++))
    fi
}

echo -e "${YELLOW}═══ Houston HVAC AI Dispatch — E2E Test ═══${NC}"
echo ""

# 0. Check .env exists
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: .env file not found. Copy .env.example and fill in credentials.${NC}"
    exit 1
fi

# 1. Run unit tests
echo -e "${YELLOW}[1/4] Unit Tests${NC}"
if python3 -m pytest tests/ -q --tb=line 2>&1 | tail -1 | grep -q "passed"; then
    echo -e "  ${GREEN}✓${NC} All pytest tests passed"
    ((PASS++))
else
    echo -e "  ${RED}✗${NC} Some pytest tests failed"
    ((FAIL++))
fi

# 2. Run legacy scenarios
echo -e "${YELLOW}[2/4] Legacy Scenarios${NC}"
if python3 tools/test_suite.py 2>&1 | tail -1 | grep -q "11/11"; then
    echo -e "  ${GREEN}✓${NC} All 11 legacy scenarios passed"
    ((PASS++))
else
    echo -e "  ${RED}✗${NC} Legacy scenarios failed"
    ((FAIL++))
fi

# 3. API key from env
API_KEY=$(grep DISPATCH_API_KEY .env | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
if [ -z "$API_KEY" ]; then
    echo -e "${RED}ERROR: DISPATCH_API_KEY not set in .env${NC}"
    exit 1
fi

# 4. Server health (assumes server is running)
echo -e "${YELLOW}[3/4] API Endpoints${NC}"
check "GET /health returns ok" \
    "curl -s $BASE/health" '"status"'

check "GET /health shows DB connected" \
    "curl -s $BASE/health" '"database":"connected"'

check "GET /admin without key returns 401" \
    "curl -s -o /dev/null -w '%{http_code}' $BASE/admin" "401"

check "GET /admin with key returns 200" \
    "curl -s -o /dev/null -w '%{http_code}' -H 'x-api-key: $API_KEY' $BASE/admin" "200"

check "POST /dispatch without key returns 401" \
    "curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/dispatch -H 'content-type: application/json' -d '{\"customer_message\":\"test\"}'" "401"

check "POST /dispatch with key returns 200" \
    "curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/dispatch -H 'content-type: application/json' -H 'x-api-key: $API_KEY' -d '{\"customer_message\":\"AC not cooling\"}'" "200"

check "GET /dispatches returns list" \
    "curl -s -H 'x-api-key: $API_KEY' $BASE/dispatches" '"dispatches"'

# 5. Log file check
echo -e "${YELLOW}[4/4] System Checks${NC}"
if [ -f hvac_dispatch.log ]; then
    echo -e "  ${GREEN}✓${NC} hvac_dispatch.log exists"
    ((PASS++))
else
    echo -e "  ${RED}✗${NC} hvac_dispatch.log not found"
    ((FAIL++))
fi

# Summary
echo ""
echo -e "${YELLOW}═══ Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC} ═══"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
