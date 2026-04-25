/**
 * reGenesis Auth Integration.
 * Uses the shared JWT validator from an ESM package context.
 */

import { createRequire } from "module";

const require = createRequire(import.meta.url);
const JWTValidator = require("../integration/shared/jwt_validator");

const JWT_SECRET = process.env.AUTH_SECRET_KEY || process.env.JWT_SECRET_KEY;
const AUTH_ALGORITHM = "HS256";

const validator = new JWTValidator(JWT_SECRET, AUTH_ALGORITHM);

export { validator };
export const middleware = () => validator.middleware();
export const requireRoles = (roles) => validator.requireRoles(roles);
export default {
  validator,
  middleware,
  requireRoles,
};
