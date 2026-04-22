/**
 * CyberArchitect Auth Integration (Refactored)
 * Uses the shared JWT validator.
 */

const path = require("path");
const JWTValidator = require("../integration/shared/jwt_validator");

// Configuration
const JWT_SECRET = process.env.AUTH_SECRET_KEY || process.env.JWT_SECRET_KEY || "";
const AUTH_ALGORITHM = "HS256";

// Initialize global validator
const validator = new JWTValidator(JWT_SECRET, AUTH_ALGORITHM);

module.exports = {
  validator,
  middleware: () => validator.middleware(),
  requireRoles: (roles) => validator.requireRoles(roles),
};
