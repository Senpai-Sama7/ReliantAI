# Kong Gateway Configuration Analysis

**Date:** 2026-04-18  
**Status:** In Progress

## Current Configuration Summary

### Services Configured: 15

| Service | JWT Plugin | JWT Config | Rate Limit | Correlation ID | Prometheus | Health Route |
|---------|------------|------------|------------|---------------|------------|--------------|
| event-bus | ✅ | anonymous: anonymous-consumer | ✅ 2000/min (redis) | ✅ | ✅ | ✅ |
| auth-service | ✅ | secret_is_base64: false | ✅ 100/min | ❌ | ✅ | ❌ |
| apex-core | ✅ | secret_is_base64: false | ✅ 1000/min (local) | ✅ | ✅ | ❌ |
| citadel | ✅ | (none) | ✅ 1000/min | ✅ | ✅ | ❌ |
| acropolis | ✅ | (none) | ✅ 1000/min | ✅ | ✅ | ❌ |
| b-a-p | ✅ | (none) | ✅ 1000/min | ✅ | ✅ | ❌ |
| money | ✅ | (none) | ✅ 1000/min | ✅ | ✅ | ❌ |
| gen-h | ✅ | (none) | ✅ 1000/min | ✅ | ✅ | ❌ |
| cleardesk | ✅ | (none) | ✅ 1000/min | ✅ | ✅ | ❌ |
| backupiq | ✅ | (none) | ✅ 1000/min | ✅ | ✅ | ❌ |
| intelligent-storage | ✅ | (none) | ✅ 1000/min | ✅ | ✅ | ❌ |
| citadel-ultimate | ✅ | (none) | ✅ 1000/min | ✅ | ✅ | ❌ |
| documancer | ✅ | (none) | ✅ 1000/min | ✅ | ✅ | ❌ |
| regenesis | ✅ | (none) | ✅ 1000/min | ✅ | ✅ | ❌ |
| cyberarchitect | ✅ | (none) | ✅ 1000/min | ✅ | ✅ | ❌ |
| nexus-runtime | ✅ | (none) | ❌ | ❌ | ❌ | ❌ |
| apex-mcp | ✅ | secret_is_base64: false | ✅ 1000/min | ✅ | ✅ | ❌ |
| skill-service | ✅ | secret_is_base64: false | ✅ 500/min | ✅ | ✅ | ❌ |

## Issues Identified

### 1. JWT Plugin Configuration Inconsistency
**Severity:** HIGH  
**Issue:** 13 services have JWT plugin without explicit configuration  
**Impact:** JWT plugin may use default settings which may not match security requirements  
**Recommendation:** Add consistent JWT configuration to all services

### 2. Missing Health Check Routes
**Severity:** HIGH  
**Issue:** 16 services lack dedicated health check routes  
**Impact:** Health checks must go through main routes, requiring JWT authentication  
**Recommendation:** Add `/health` route to all services with JWT bypass via anonymous consumer

### 3. Missing Correlation ID on auth-service
**Severity:** MEDIUM  
**Issue:** auth-service doesn't have correlation-id plugin (relies on global)  
**Impact:** Auth service requests may not have correlation ID in some scenarios  
**Recommendation:** Add explicit correlation-id plugin to auth-service

### 4. Missing Prometheus on nexus-runtime
**Severity:** MEDIUM  
**Issue:** nexus-runtime has no Prometheus plugin  
**Impact:** No metrics collection for nexus-runtime  
**Recommendation:** Add Prometheus plugin

### 5. Missing Correlation ID on nexus-runtime
**Severity:** MEDIUM  
**Issue:** nexus-runtime has no correlation-id plugin  
**Impact:** No distributed tracing for nexus-runtime  
**Recommendation:** Add correlation-id plugin

### 6. Rate Limiting Policy Inconsistency
**Severity:** LOW  
**Issue:** Mix of local and redis rate limiting policies  
**Impact:** Local policies don't scale across Kong instances  
**Recommendation:** Standardize on redis policy for production

### 7. Missing Anonymous Consumer
**Severity:** HIGH  
**Issue:** anonymous-consumer referenced in event-bus JWT config but not defined in YAML  
**Impact:** Health check bypass won't work  
**Recommendation:** Add consumers section with anonymous-consumer definition

## Remediation Plan

### Priority 1: Critical Security Issues
1. Add consumers section with anonymous-consumer
2. Add health check routes to all services
3. Standardize JWT plugin configuration across all services

### Priority 2: Observability Gaps
4. Add Prometheus plugin to nexus-runtime
5. Add correlation-id plugin to nexus-runtime and auth-service

### Priority 3: Consistency Improvements
6. Standardize rate limiting policy to redis
7. Add file-log configuration to all services for debugging

## Proposed Standard Configuration

### JWT Plugin (All Services)
```yaml
- name: jwt
  config:
    secret_is_base64: false
    uri_param_names: []
    claims_to_verify:
      - exp
```

### Health Check Route (All Services)
```yaml
- name: {service}-health
  paths:
    - /{service}/health
  methods:
    - GET
  strip_path: true
  plugins:
    - name: jwt
      config:
        anonymous: anonymous-consumer
```

### Consumers Section
```yaml
consumers:
  - username: anonymous-consumer
    custom_id: anonymous-health-check
```
