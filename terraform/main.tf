# HigherSelf Network Server - Main Terraform Configuration
# Enterprise-grade Infrastructure as Code with Gruntwork integration
# This file is now managed by Terragrunt - see terragrunt.hcl for configuration

terraform {
  required_version = ">= 1.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
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

  # Backend configuration is now managed by Terragrunt
  # See terragrunt.hcl for remote state configuration
}

# Local variables for configuration
locals {
  project_name = "higherself-network-server"
  environment  = var.environment
  
  common_tags = {
    Project     = local.project_name
    Environment = local.environment
    ManagedBy   = "terraform"
    Owner       = "HigherSelf-Network"
    Purpose     = "enterprise-automation-platform"
  }

  # Service configuration
  services = {
    windsurf_agent = {
      image = "thehigherselfnetworkserver"
      port  = 8000
      replicas = var.environment == "production" ? 3 : 1
    }
    mongodb = {
      image = "mongo:6.0"
      port  = 27017
      storage = var.environment == "production" ? "100Gi" : "10Gi"
    }
    redis = {
      image = "redis:7.0-alpine"
      port  = 6379
      storage = var.environment == "production" ? "20Gi" : "5Gi"
    }
    nginx = {
      image = "nginx:alpine"
      ports = [80, 443]
    }
    prometheus = {
      image = "prom/prometheus:latest"
      port  = 9090
      storage = var.environment == "production" ? "50Gi" : "10Gi"
    }
    grafana = {
      image = "grafana/grafana:latest"
      port  = 3000
    }
    consul = {
      image = "hashicorp/consul:1.15"
      port  = 8500
    }
  }
}

# Docker provider configuration
provider "docker" {
  host = var.docker_host
}

# AWS provider configuration (for cloud resources)
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = local.common_tags
  }
}

# Docker network for HigherSelf services
resource "docker_network" "higherself_network" {
  name   = "${local.project_name}-${local.environment}"
  driver = "bridge"
  
  labels {
    label = "project"
    value = local.project_name
  }
  
  labels {
    label = "environment"
    value = local.environment
  }
}

# Docker volumes for persistent data
resource "docker_volume" "mongodb_data" {
  name = "${local.project_name}-mongodb-data-${local.environment}"
  
  labels {
    label = "service"
    value = "mongodb"
  }
  
  labels {
    label = "environment"
    value = local.environment
  }
}

resource "docker_volume" "redis_data" {
  name = "${local.project_name}-redis-data-${local.environment}"
  
  labels {
    label = "service"
    value = "redis"
  }
  
  labels {
    label = "environment"
    value = local.environment
  }
}

resource "docker_volume" "consul_data" {
  name = "${local.project_name}-consul-data-${local.environment}"
  
  labels {
    label = "service"
    value = "consul"
  }
  
  labels {
    label = "environment"
    value = local.environment
  }
}

resource "docker_volume" "prometheus_data" {
  name = "${local.project_name}-prometheus-data-${local.environment}"
  
  labels {
    label = "service"
    value = "prometheus"
  }
  
  labels {
    label = "environment"
    value = local.environment
  }
}

resource "docker_volume" "grafana_data" {
  name = "${local.project_name}-grafana-data-${local.environment}"
  
  labels {
    label = "service"
    value = "grafana"
  }
  
  labels {
    label = "environment"
    value = local.environment
  }
}

# Application logs volume
resource "docker_volume" "app_logs" {
  name = "${local.project_name}-logs-${local.environment}"
  
  labels {
    label = "type"
    value = "logs"
  }
  
  labels {
    label = "environment"
    value = local.environment
  }
}

# Application data volume
resource "docker_volume" "app_data" {
  name = "${local.project_name}-data-${local.environment}"
  
  labels {
    label = "type"
    value = "data"
  }
  
  labels {
    label = "environment"
    value = local.environment
  }
}
