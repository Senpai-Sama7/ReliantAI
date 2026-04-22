FROM hashicorp/vault:1.15

# Copy configuration
COPY vault-config.hcl /vault/config/vault-config.hcl

# Copy SSL certificates
COPY ../nginx/ssl/cert.pem /vault/certs/cert.pem
COPY ../nginx/ssl/key.pem /vault/certs/key.pem

# Set environment variables
ENV VAULT_ADDR=https://localhost:8200
ENV VAULT_API_ADDR=https://localhost:8200

# Expose ports
EXPOSE 8200 8201

# Volume for persistent data
VOLUME ["/vault/data"]

# Start vault
CMD ["vault", "server", "-config=/vault/config/vault-config.hcl"]
