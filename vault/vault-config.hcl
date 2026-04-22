# ReliantAI Platform - HashiCorp Vault Configuration
# Secrets management configuration

storage "file" {
  path = "/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = "false"
  tls_cert_file = "/vault/certs/cert.pem"
  tls_key_file  = "/vault/certs/key.pem"
}

# UI configuration
ui = true

# API configuration
api_addr = "https://vault.reliantai.io:8200"
cluster_addr = "https://vault.reliantai.io:8201"

# Default lease TTL
default_lease_ttl = "168h"

# Maximum lease TTL
max_lease_ttl = "720h"

# Plugin directory
plugin_directory = "/vault/plugins"

# Log level
log_level = "Info"

# Telemetry
telemetry {
  statsite_address = ""
  statsd_address   = ""
  disable_hostname = false
}
