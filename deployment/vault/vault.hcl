# HashiCorp Vault Configuration for HigherSelf Network Server
# Enterprise-grade secrets management configuration

# Storage backend configuration
storage "file" {
  path = "/vault/data"
}

# Listener configuration
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1  # Disable for development, enable for production
  
  # For production, enable TLS:
  # tls_disable = 0
  # tls_cert_file = "/vault/config/vault.crt"
  # tls_key_file = "/vault/config/vault.key"
}

# API address
api_addr = "http://0.0.0.0:8200"

# Cluster address (for HA deployments)
cluster_addr = "http://0.0.0.0:8201"

# UI configuration
ui = true

# Logging
log_level = "INFO"
log_format = "json"

# Disable mlock for development (enable for production)
disable_mlock = true

# Plugin directory
plugin_directory = "/vault/plugins"

# Default lease TTL and max lease TTL
default_lease_ttl = "768h"  # 32 days
max_lease_ttl = "8760h"     # 365 days

# Entropy configuration for better randomness
entropy "seal" {
  mode = "augmentation"
}

# Telemetry configuration
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
  enable_hostname_label = false
  
  # Metrics prefixes
  metrics_prefix = "higherself_vault"
}

# Seal configuration (for production)
# seal "awskms" {
#   region     = "us-east-1"
#   kms_key_id = "alias/higherself-vault-seal"
# }

# High Availability configuration (for production)
# ha_storage "consul" {
#   address = "consul:8500"
#   path    = "vault/"
#   
#   service = "vault"
#   service_tags = "higherself,secrets"
#   
#   check_timeout = "5s"
#   max_parallel = "128"
# }
