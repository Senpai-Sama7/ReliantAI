FROM hashicorp/vault:1.15

# Install curl for Docker health probes (AGENTS.md invariant)
RUN apk add --no-cache curl

# Copy configuration
COPY vault-config.hcl /vault/config/vault-config.hcl

# Set environment variables
ENV VAULT_ADDR=https://localhost:8200
ENV VAULT_API_ADDR=https://localhost:8200

# Expose ports
EXPOSE 8200 8201

# Volume for persistent data
VOLUME ["/vault/data"]

# Start vault
CMD ["vault", "server", "-config=/vault/config/vault-config.hcl"]
