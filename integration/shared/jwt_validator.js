/**
 * Shared JWT Validator for Node.js services.
 * Consolidates authentication logic for CyberArchitect, reGenesis, and DocuMancer frontend.
 */

const jwt = require("jsonwebtoken");

class JWTValidator {
  /**
   * @param {string} secretKey - The secret key for verifying tokens.
   * @param {string} algorithm - The algorithm used for signing (default: HS256).
   */
  constructor(secretKey, algorithm = "HS256") {
    this.secretKey =
      secretKey || process.env.AUTH_SECRET_KEY || process.env.JWT_SECRET_KEY || "";
    this.algorithm = algorithm;
  }

  /**
   * Validates a JWT token and returns the decoded payload.
   * @param {string} token - The JWT token to validate.
   * @returns {Object|null} - The decoded payload or null if invalid.
   */
  validateToken(token) {
    if (!token) return null;
    if (!this.secretKey) {
      console.error("JWT Validation Error: JWT secret not configured");
      return null;
    }

    try {
      return jwt.verify(token, this.secretKey, {
        algorithms: [this.algorithm],
      });
    } catch (error) {
      console.error("JWT Validation Error:", error.message);
      return null;
    }
  }

  /**
   * Express/Connect middleware for authentication.
   */
  middleware() {
    return (req, res, next) => {
      const authHeader = req.headers.authorization;
      if (!authHeader) {
        return res.status(401).json({ error: "Missing authorization header" });
      }

      const parts = authHeader.split(" ");
      if (parts.length !== 2 || parts[0].toLowerCase() !== "bearer") {
        return res.status(401).json({ error: "Invalid authorization format" });
      }

      const token = parts[1];
      const decoded = this.validateToken(token);

      if (!decoded) {
        return res.status(401).json({ error: "Invalid or expired token" });
      }

      req.user = decoded;
      next();
    };
  }

  /**
   * Middleware factory for role-based access control.
   * @param {string[]} requiredRoles
   */
  requireRoles(requiredRoles) {
    return (req, res, next) => {
      if (!req.user) {
        return res.status(401).json({ error: "Authentication required" });
      }

      const userRoles = req.user.roles || [];
      const hasRole = requiredRoles.some((role) => userRoles.includes(role));

      if (!hasRole) {
        return res.status(403).json({ error: "Insufficient permissions" });
      }

      next();
    };
  }
}

module.exports = JWTValidator;
