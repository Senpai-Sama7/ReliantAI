"""
JSON Schema Validation for HVAC Dispatch
Validates request/response payloads against defined schemas.

Based on Citadel's schema gate pattern - every input is validated
before processing, every output is validated before sending.
"""

from __future__ import annotations

import json
import jsonschema
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from config import setup_logging

logger = setup_logging("schema_validation")

# Schema directory
SCHEMA_DIR = Path(__file__).parent / "schemas"


@dataclass
class ValidationResult:
    """Result of schema validation"""
    valid: bool
    errors: List[str]
    data: Optional[Dict[str, Any]] = None


class SchemaValidator:
    """
    Validates payloads against JSON schemas.
    
    Schemas are loaded from the schemas/ directory and cached.
    """
    
    def __init__(self):
        self._schemas: Dict[str, Dict] = {}
        self._validators: Dict[str, jsonschema.Draft7Validator] = {}
        self._load_schemas()
    
    def _load_schemas(self) -> None:
        """Load all schemas from schemas/ directory"""
        if not SCHEMA_DIR.exists():
            logger.warning(f"Schema directory not found: {SCHEMA_DIR}")
            return
        
        for schema_file in SCHEMA_DIR.glob("*.json"):
            try:
                schema = json.loads(schema_file.read_text())
                name = schema_file.stem
                self._schemas[name] = schema
                self._validators[name] = jsonschema.Draft7Validator(schema)
                logger.info(f"Loaded schema: {name}")
            except Exception as e:
                logger.error(f"Failed to load schema {schema_file}: {e}")
    
    def validate(
        self,
        schema_name: str,
        data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate data against a schema.
        
        Args:
            schema_name: Name of the schema (e.g., 'dispatch_request')
            data: Dictionary to validate
            
        Returns:
            ValidationResult with valid=True/False and error details
        """
        if schema_name not in self._validators:
            logger.error(f"Schema not found: {schema_name}")
            return ValidationResult(
                valid=False,
                errors=[f"Schema not found: {schema_name}"],
                data=data
            )
        
        validator = self._validators[schema_name]
        errors = list(validator.iter_errors(data))
        
        if errors:
            error_messages = []
            for error in errors:
                path = ".".join(str(p) for p in error.path) if error.path else "root"
                error_messages.append(f"{path}: {error.message}")
            
            logger.warning(f"Validation failed for {schema_name}: {error_messages}")
            return ValidationResult(
                valid=False,
                errors=error_messages,
                data=data
            )
        
        logger.debug(f"Validation passed for {schema_name}")
        return ValidationResult(valid=True, errors=[], data=data)
    
    def validate_or_raise(
        self,
        schema_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate and return data, or raise ValidationError.
        
        Raises:
            ValidationError: If validation fails
        """
        result = self.validate(schema_name, data)
        if not result.valid:
            raise ValidationError(f"Validation failed: {result.errors}")
        return result.data
    
    def get_schema(self, schema_name: str) -> Optional[Dict]:
        """Get a loaded schema by name"""
        return self._schemas.get(schema_name)
    
    def list_schemas(self) -> List[str]:
        """List all loaded schema names"""
        return list(self._schemas.keys())


class ValidationError(Exception):
    """Raised when schema validation fails"""
    pass


# Global validator instance
_validator: Optional[SchemaValidator] = None


def get_validator() -> SchemaValidator:
    """Get or create global schema validator"""
    global _validator
    if _validator is None:
        _validator = SchemaValidator()
    return _validator


# Convenience functions
def validate_dispatch_request(data: Dict[str, Any]) -> ValidationResult:
    """Validate dispatch request payload"""
    return get_validator().validate("dispatch_request", data)


def validate_or_raise(schema_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and return data, or raise ValidationError"""
    return get_validator().validate_or_raise(schema_name, data)


def is_valid_phone(phone: str) -> bool:
    """Quick phone number validation (E.164 format)"""
    import re
    return bool(re.match(r'^\+1[0-9]{10}$', phone))


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input (truncate, strip)"""
    if not isinstance(value, str):
        return str(value)[:max_length]
    return value.strip()[:max_length]
