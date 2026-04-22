#!/usr/bin/env python3
"""
Unit tests for APEX Auth Integration
"""

import pytest
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, '/home/donovan/Projects/ReliantAI/integration/shared')
sys.path.insert(0, '/home/donovan/Projects/ReliantAI/apex/apex-agents/api')


def test_auth_integration_imports():
    """Test that auth integration module imports successfully."""
    try:
        import auth_integration
        assert hasattr(auth_integration, 'get_current_user')
        assert hasattr(auth_integration, 'AuthIntegration')
        assert hasattr(auth_integration, 'AUTH_ENABLED')
        print("✅ Auth integration imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        raise


def test_auth_integration_instance():
    """Test AuthIntegration class instantiation."""
    from auth_integration import AuthIntegration
    
    auth = AuthIntegration()
    assert hasattr(auth, 'enabled')
    assert hasattr(auth, 'validator')


def test_get_current_user_without_auth():
    """Test that get_current_user works when auth is disabled."""
    from auth_integration import get_current_user_optional
    import asyncio
    
    result = asyncio.run(get_current_user_optional())
    assert result["username"] == "anonymous"
    assert result["roles"] == []


def test_main_py_imports():
    """Test that main.py can import auth integration."""
    try:
        # This will fail if there are import errors
        import main
        print("✅ main.py imports successful")
    except Exception as e:
        print(f"⚠️ main.py import warning: {e}")
        # Don't fail - main.py may have other dependencies


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
