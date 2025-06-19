# ======================================================
# HIGHERSELF NETWORK SERVER - DOCKER DEPLOYMENT MODULE
# Terraform configuration for Docker container orchestration
# ======================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

# Local variables
locals {
  environment = var.environment
  project_name = var.project_name
  
  # Resource naming
  name_prefix = "${var.project_name}-${var.environment}"
  
  # Environment-specific configuration
  env_config = var.environment_config[var.environment]
  
  # Resource limits based on environment
  resource_limits = var.resource_limits[var.environment]
  
  # Common labels
  common_labels = merge(var.common_tags, {
    "com.higherself.environment" = var.environment
    "com.higherself.project" = var.project_name
    "com.higherself.managed-by" = "terraform"
  })
}

# Docker network for the application
resource "docker_network" "higherself_network" {
  name = "${local.name_prefix}-network"
  
  driver = "bridge"
  
  ipam_config {
    subnet = var.network_subnet
  }
  
  labels = local.common_labels
}

# Docker volumes for persistent data
resource "docker_volume" "mongodb_data" {
  name = "${local.name_prefix}-mongodb-data"
  
  labels = merge(local.common_labels, {
    "com.higherself.service" = "mongodb"
    "com.higherself.volume-type" = "data"
  })
}

resource "docker_volume" "redis_data" {
  name = "${local.name_prefix}-redis-data"
  
  labels = merge(local.common_labels, {
    "com.higherself.service" = "redis"
    "com.higherself.volume-type" = "data"
  })
}

resource "docker_volume" "consul_data" {
  name = "${local.name_prefix}-consul-data"
  
  labels = merge(local.common_labels, {
    "com.higherself.service" = "consul"
    "com.higherself.volume-type" = "data"
  })
}

resource "docker_volume" "prometheus_data" {
  name = "${local.name_prefix}-prometheus-data"
  
  labels = merge(local.common_labels, {
    "com.higherself.service" = "prometheus"
    "com.higherself.volume-type" = "data"
  })
}

resource "docker_volume" "grafana_data" {
  name = "${local.name_prefix}-grafana-data"
  
  labels = merge(local.common_labels, {
    "com.higherself.service" = "grafana"
    "com.higherself.volume-type" = "data"
  })
}

# MongoDB container
resource "docker_container" "mongodb" {
  count = var.mongodb_enabled ? 1 : 0
  
  name  = "${local.name_prefix}-mongodb"
  image = "mongo:6.0"
  
  restart = "unless-stopped"
  
  ports {
    internal = 27017
    external = var.environment == "development" ? 27017 : null
  }
  
  env = [
    "MONGO_INITDB_ROOT_USERNAME=${var.mongodb_root_username}",
    "MONGO_INITDB_ROOT_PASSWORD=${var.mongodb_root_password}",
    "MONGO_INITDB_DATABASE=${var.mongodb_database}",
    "MONGO_APP_USER=${var.mongodb_username}",
    "MONGO_APP_PASSWORD=${var.mongodb_password}"
  ]
  
  volumes {
    volume_name    = docker_volume.mongodb_data.name
    container_path = "/data/db"
  }
  
  volumes {
    host_path      = "${path.cwd}/logs/${var.environment}/mongodb"
    container_path = "/var/log/mongodb"
  }
  
  command = [
    "--auth",
    "--bind_ip_all",
    "--logpath", "/var/log/mongodb/mongod.log",
    "--logappend",
    "--wiredTigerCacheSizeGB", var.mongodb_cache_size
  ]
  
  healthcheck {
    test = ["CMD", "mongosh", "--eval", "db.runCommand('ping').ok"]
    interval = "30s"
    timeout = "10s"
    retries = 5
    start_period = "40s"
  }
  
  networks_advanced {
    name = docker_network.higherself_network.name
  }
  
  labels = merge(local.common_labels, {
    "com.higherself.service" = "mongodb"
    "com.higherself.service-type" = "database"
  })
}

# Redis container
resource "docker_container" "redis" {
  count = var.redis_enabled ? 1 : 0
  
  name  = "${local.name_prefix}-redis"
  image = "redis:7.2-alpine"
  
  restart = "unless-stopped"
  
  ports {
    internal = 6379
    external = var.environment == "development" ? 6379 : null
  }
  
  volumes {
    volume_name    = docker_volume.redis_data.name
    container_path = "/data"
  }
  
  volumes {
    host_path      = "${path.cwd}/logs/${var.environment}/redis"
    container_path = "/var/log/redis"
  }
  
  command = var.redis_password != "" ? [
    "redis-server",
    "--requirepass", var.redis_password,
    "--appendonly", "yes"
  ] : [
    "redis-server",
    "--appendonly", "yes"
  ]
  
  healthcheck {
    test = ["CMD", "redis-cli", "ping"]
    interval = "30s"
    timeout = "5s"
    retries = 5
    start_period = "10s"
  }
  
  networks_advanced {
    name = docker_network.higherself_network.name
  }
  
  labels = merge(local.common_labels, {
    "com.higherself.service" = "redis"
    "com.higherself.service-type" = "cache"
  })
}

# Consul container
resource "docker_container" "consul" {
  count = var.consul_enabled ? 1 : 0
  
  name  = "${local.name_prefix}-consul"
  image = "hashicorp/consul:1.16"
  
  restart = "unless-stopped"
  
  ports {
    internal = 8500
    external = var.environment == "development" ? 8500 : null
  }
  
  volumes {
    volume_name    = docker_volume.consul_data.name
    container_path = "/consul/data"
  }
  
  volumes {
    host_path      = "${path.cwd}/logs/${var.environment}/consul"
    container_path = "/consul/logs"
  }
  
  command = [
    "agent",
    "-server",
    "-ui",
    "-client=0.0.0.0",
    "-bootstrap-expect=1",
    "-data-dir=/consul/data",
    "-log-file=/consul/logs/consul.log"
  ]
  
  env = [
    "CONSUL_BIND_INTERFACE=eth0",
    "CONSUL_CLIENT_INTERFACE=eth0"
  ]
  
  healthcheck {
    test = ["CMD", "consul", "members"]
    interval = "30s"
    timeout = "10s"
    retries = 5
    start_period = "20s"
  }
  
  networks_advanced {
    name = docker_network.higherself_network.name
  }
  
  labels = merge(local.common_labels, {
    "com.higherself.service" = "consul"
    "com.higherself.service-type" = "discovery"
  })
}

# Main application container
resource "docker_container" "higherself_server" {
  name  = "${local.name_prefix}-server"
  image = "${var.docker_registry}/${var.docker_image_name}:${var.docker_image_tag}"
  
  restart = "unless-stopped"
  
  ports {
    internal = var.container_port
    external = var.container_port
  }
  
  env = concat([
    "RUNNING_IN_CONTAINER=true",
    "PYTHONUNBUFFERED=1",
    "ENVIRONMENT=${var.environment}",
    "DEBUG=${local.env_config.debug_enabled}",
    "LOG_LEVEL=${var.log_level}",
    "MULTI_ENTITY_MODE=${var.multi_entity_mode}",
    "PRIMARY_BUSINESS_ENTITY=${var.primary_business_entity}",
    "MONGODB_URI=mongodb://${var.mongodb_username}:${var.mongodb_password}@${local.name_prefix}-mongodb:27017/${var.mongodb_database}",
    "REDIS_URI=redis://:${var.redis_password}@${local.name_prefix}-redis:6379/0",
    "CONSUL_HTTP_ADDR=${local.name_prefix}-consul:8500"
  ], var.additional_env_vars)
  
  volumes {
    host_path      = "${path.cwd}/logs/${var.environment}"
    container_path = "/app/logs"
  }
  
  volumes {
    host_path      = "${path.cwd}/data/${var.environment}"
    container_path = "/app/data"
  }
  
  volumes {
    host_path      = "${path.cwd}/config"
    container_path = "/app/config"
    read_only      = true
  }
  
  healthcheck {
    test = ["CMD", "curl", "-f", "http://localhost:${var.container_port}/health"]
    interval = "30s"
    timeout = "30s"
    retries = 5
    start_period = "60s"
  }
  
  networks_advanced {
    name = docker_network.higherself_network.name
  }
  
  labels = merge(local.common_labels, {
    "com.higherself.service" = "api"
    "com.higherself.service-type" = "application"
  })
  
  depends_on = [
    docker_container.mongodb,
    docker_container.redis,
    docker_container.consul
  ]
}

# Generate Docker Compose file for manual deployment
resource "local_file" "docker_compose_generated" {
  filename = "${path.cwd}/docker-compose.${var.environment}.generated.yml"
  
  content = templatefile("${path.module}/templates/docker-compose.yml.tpl", {
    environment = var.environment
    project_name = var.project_name
    name_prefix = local.name_prefix
    
    # Service configuration
    mongodb_enabled = var.mongodb_enabled
    redis_enabled = var.redis_enabled
    consul_enabled = var.consul_enabled
    prometheus_enabled = var.prometheus_enabled
    grafana_enabled = var.grafana_enabled
    
    # Image configuration
    docker_registry = var.docker_registry
    docker_image_name = var.docker_image_name
    docker_image_tag = var.docker_image_tag
    
    # Database configuration
    mongodb_username = var.mongodb_username
    mongodb_password = var.mongodb_password
    mongodb_database = var.mongodb_database
    redis_password = var.redis_password
    
    # Resource configuration
    resource_limits = local.resource_limits
    
    # Network configuration
    network_subnet = var.network_subnet
    
    # Business entity configuration
    multi_entity_mode = var.multi_entity_mode
    primary_business_entity = var.primary_business_entity
    business_entities = var.business_entities
  })
}

# Output deployment information
resource "local_file" "deployment_info" {
  filename = "${path.cwd}/deployment-info-${var.environment}.json"
  
  content = jsonencode({
    environment = var.environment
    project_name = var.project_name
    deployment_time = timestamp()
    
    services = {
      higherself_server = {
        name = docker_container.higherself_server.name
        image = docker_container.higherself_server.image
        ports = docker_container.higherself_server.ports
      }
      mongodb = var.mongodb_enabled ? {
        name = docker_container.mongodb[0].name
        image = docker_container.mongodb[0].image
        ports = docker_container.mongodb[0].ports
      } : null
      redis = var.redis_enabled ? {
        name = docker_container.redis[0].name
        image = docker_container.redis[0].image
        ports = docker_container.redis[0].ports
      } : null
      consul = var.consul_enabled ? {
        name = docker_container.consul[0].name
        image = docker_container.consul[0].image
        ports = docker_container.consul[0].ports
      } : null
    }
    
    volumes = {
      mongodb_data = docker_volume.mongodb_data.name
      redis_data = docker_volume.redis_data.name
      consul_data = docker_volume.consul_data.name
      prometheus_data = docker_volume.prometheus_data.name
      grafana_data = docker_volume.grafana_data.name
    }
    
    network = {
      name = docker_network.higherself_network.name
      subnet = var.network_subnet
    }
  })
}
