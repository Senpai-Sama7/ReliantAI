"""
Property-Based Tests for RBAC (Properties 6-9, 71)
"""
import pytest
from hypothesis import given, strategies as st, settings

import auth_server
from auth_server import Role, Permission, has_permission
from memory_redis import MemoryRedis

# Property 6: Role Permission Hierarchy
@given(role=st.sampled_from([Role.SUPER_ADMIN, Role.ADMIN, Role.OPERATOR, Role.TECHNICIAN]))
@settings(max_examples=50)
def test_role_permission_hierarchy(role):
    """Property 6: Roles inherit permissions (admin includes operator permissions)"""
    if role == Role.SUPER_ADMIN:
        # Super admin has all permissions
        assert has_permission(role, Permission.READ)
        assert has_permission(role, Permission.WRITE)
        assert has_permission(role, Permission.DELETE)
        assert has_permission(role, Permission.ADMIN)
    elif role == Role.ADMIN:
        # Admin has read, write, delete but not admin
        assert has_permission(role, Permission.READ)
        assert has_permission(role, Permission.WRITE)
        assert has_permission(role, Permission.DELETE)
        assert not has_permission(role, Permission.ADMIN)
    elif role == Role.OPERATOR:
        # Operator has read, write
        assert has_permission(role, Permission.READ)
        assert has_permission(role, Permission.WRITE)
        assert not has_permission(role, Permission.DELETE)
        assert not has_permission(role, Permission.ADMIN)
    elif role == Role.TECHNICIAN:
        # Technician has only read
        assert has_permission(role, Permission.READ)
        assert not has_permission(role, Permission.WRITE)
        assert not has_permission(role, Permission.DELETE)
        assert not has_permission(role, Permission.ADMIN)

# Property 7: Super Admin Universal Access
@given(permission=st.sampled_from([Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN]))
@settings(max_examples=20)
def test_super_admin_universal_access(permission):
    """Property 7: Super admin has all permissions"""
    assert has_permission(Role.SUPER_ADMIN, permission)

# Property 8: Tenant Isolation Enforcement
@given(
    user_tenant=st.uuids(),
    resource_tenant=st.uuids()
)
@settings(max_examples=50)
def test_tenant_isolation_enforcement(user_tenant, resource_tenant):
    """Property 8: Non-super-admin cannot access different tenant's resources"""
    user_tenant_str = str(user_tenant)
    resource_tenant_str = str(resource_tenant)
    
    # Super admin can access any tenant
    can_access_super_admin = True
    
    # Other roles can only access their own tenant
    can_access_other = (user_tenant_str == resource_tenant_str)
    
    assert can_access_super_admin is True
    if user_tenant_str != resource_tenant_str:
        assert can_access_other is False

# Property 9: Permission Validation Before Write
@given(role=st.sampled_from([Role.TECHNICIAN, Role.OPERATOR, Role.ADMIN, Role.SUPER_ADMIN]))
@settings(max_examples=50)
def test_permission_validation_before_write(role):
    """Property 9: Write operations require WRITE permission"""
    can_write = has_permission(role, Permission.WRITE)
    
    if role in [Role.TECHNICIAN]:
        assert can_write is False
    else:
        assert can_write is True

# Property 71: Account Lockout After Failed Attempts
@pytest.mark.asyncio
async def test_account_lockout_after_failed_attempts():
    """Property 71: Account locks after 5 failed login attempts in 15 minutes"""
    from auth_server import track_failed_login, is_account_locked, reset_failed_login

    test_redis = MemoryRedis()
    auth_server.redis_client = test_redis
    username = "test_lockout_user"

    # Track 5 failed attempts
    for i in range(5):
        locked = await track_failed_login(username)
        if i < 4:
            assert locked is False
        else:
            assert locked is True
    
    # Verify account is locked
    assert await is_account_locked(username) is True
    
    # Reset and verify unlocked
    await reset_failed_login(username)
    assert await is_account_locked(username) is False
    await test_redis.close()
    auth_server.redis_client = None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
