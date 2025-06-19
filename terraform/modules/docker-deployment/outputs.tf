# ======================================================
# HIGHERSELF NETWORK SERVER - DOCKER DEPLOYMENT OUTPUTS
# Output values for Docker container orchestration
# ======================================================

# Environment information
output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

# Network information
output "network_name" {
  description = "Docker network name"
  value       = docker_network.higherself_network.name
}

output "network_id" {
  description = "Docker network ID"
  value       = docker_network.higherself_network.id
}

output "network_subnet" {
  description = "Docker network subnet"
  value       = var.network_subnet
}

# Volume information
output "volumes" {
  description = "Docker volumes created"
  value = {
    mongodb_data    = docker_volume.mongodb_data.name
    redis_data      = docker_volume.redis_data.name
    consul_data     = docker_volume.consul_data.name
    prometheus_data = docker_volume.prometheus_data.name
    grafana_data    = docker_volume.grafana_data.name
  }
}

# Container information
output "containers" {
  description = "Docker containers deployed"
  value = {
    higherself_server = {
      name   = docker_container.higherself_server.name
      id     = docker_container.higherself_server.id
      image  = docker_container.higherself_server.image
      ports  = docker_container.higherself_server.ports
      status = "running"
    }
    mongodb = var.mongodb_enabled ? {
      name   = docker_container.mongodb[0].name
      id     = docker_container.mongodb[0].id
      image  = docker_container.mongodb[0].image
      ports  = docker_container.mongodb[0].ports
      status = "running"
    } : null
    redis = var.redis_enabled ? {
      name   = docker_container.redis[0].name
      id     = docker_container.redis[0].id
      image  = docker_container.redis[0].image
      ports  = docker_container.redis[0].ports
      status = "running"
    } : null
    consul = var.consul_enabled ? {
      name   = docker_container.consul[0].name
      id     = docker_container.consul[0].id
      image  = docker_container.consul[0].image
      ports  = docker_container.consul[0].ports
      status = "running"
    } : null
  }
}

# Service endpoints
output "service_endpoints" {
  description = "Service endpoints for accessing the application"
  value = {
    application = {
      url         = "http://localhost:${var.container_port}"
      health_url  = "http://localhost:${var.container_port}/health"
      api_docs    = "http://localhost:${var.container_port}/docs"
    }
    mongodb = var.mongodb_enabled && var.environment == "development" ? {
      host = "localhost"
      port = 27017
      url  = "mongodb://localhost:27017"
    } : null
    redis = var.redis_enabled && var.environment == "development" ? {
      host = "localhost"
      port = 6379
      url  = "redis://localhost:6379"
    } : null
    consul = var.consul_enabled && var.environment == "development" ? {
      ui_url = "http://localhost:8500"
      api_url = "http://localhost:8500/v1"
    } : null
  }
}

# Configuration information
output "configuration" {
  description = "Deployment configuration summary"
  value = {
    environment           = var.environment
    multi_entity_mode    = var.multi_entity_mode
    primary_business_entity = var.primary_business_entity
    business_entities    = var.business_entities
    
    services_enabled = {
      mongodb    = var.mongodb_enabled
      redis      = var.redis_enabled
      consul     = var.consul_enabled
      prometheus = var.prometheus_enabled
      grafana    = var.grafana_enabled
    }
    
    resource_limits = var.resource_limits[var.environment]
    
    security = {
      secrets_backend = var.secrets_backend
      vault_enabled   = var.vault_enabled
      ssl_enabled     = var.enable_ssl
    }
  }
}

# Business entity configuration
output "business_entity_config" {
  description = "Business entity configuration"
  value = {
    multi_entity_mode       = var.multi_entity_mode
    primary_business_entity = var.primary_business_entity
    enabled_entities        = var.business_entities
    
    entity_details = {
      the_7_space = {
        enabled = contains(var.business_entities, "the_7_space")
        contact_count = 191
        primary_workflows = ["gallery_management", "artist_engagement", "event_coordination"]
      }
      am_consulting = {
        enabled = contains(var.business_entities, "am_consulting")
        contact_count = 1300
        primary_workflows = ["client_management", "project_tracking", "business_automation"]
      }
      higherself_core = {
        enabled = contains(var.business_entities, "higherself_core")
        contact_count = 1300
        primary_workflows = ["community_management", "content_curation", "member_engagement"]
      }
    }
  }
}

# Deployment files
output "generated_files" {
  description = "Generated deployment files"
  value = {
    docker_compose_file = local_file.docker_compose_generated.filename
    deployment_info     = local_file.deployment_info.filename
  }
}

# Health check information
output "health_checks" {
  description = "Health check endpoints and configuration"
  value = {
    application = {
      endpoint = "http://localhost:${var.container_port}/health"
      interval = "30s"
      timeout  = "30s"
      retries  = 5
    }
    mongodb = var.mongodb_enabled ? {
      command  = "mongosh --eval 'db.runCommand(\"ping\").ok'"
      interval = "30s"
      timeout  = "10s"
      retries  = 5
    } : null
    redis = var.redis_enabled ? {
      command  = "redis-cli ping"
      interval = "30s"
      timeout  = "5s"
      retries  = 5
    } : null
    consul = var.consul_enabled ? {
      command  = "consul members"
      interval = "30s"
      timeout  = "10s"
      retries  = 5
    } : null
  }
}

# Management commands
output "management_commands" {
  description = "Useful management commands for the deployment"
  value = {
    docker_compose = {
      start   = "docker-compose up -d"
      stop    = "docker-compose down"
      logs    = "docker-compose logs -f"
      status  = "docker-compose ps"
      restart = "docker-compose restart"
    }
    
    health_checks = {
      application = "curl -f http://localhost:${var.container_port}/health"
      mongodb     = var.mongodb_enabled ? "docker exec ${docker_container.higherself_server.name} mongosh --eval 'db.runCommand(\"ping\")'" : null
      redis       = var.redis_enabled ? "docker exec ${docker_container.higherself_server.name} redis-cli ping" : null
    }
    
    logs = {
      application = "docker logs ${docker_container.higherself_server.name}"
      mongodb     = var.mongodb_enabled ? "docker logs ${docker_container.mongodb[0].name}" : null
      redis       = var.redis_enabled ? "docker logs ${docker_container.redis[0].name}" : null
      consul      = var.consul_enabled ? "docker logs ${docker_container.consul[0].name}" : null
    }
  }
}

# Deployment summary
output "deployment_summary" {
  description = "Summary of the deployment"
  value = {
    environment     = var.environment
    project_name    = var.project_name
    deployment_time = timestamp()
    
    containers_deployed = length([
      docker_container.higherself_server.name,
      var.mongodb_enabled ? docker_container.mongodb[0].name : null,
      var.redis_enabled ? docker_container.redis[0].name : null,
      var.consul_enabled ? docker_container.consul[0].name : null
    ]) - length([for x in [
      var.mongodb_enabled ? null : "mongodb",
      var.redis_enabled ? null : "redis", 
      var.consul_enabled ? null : "consul"
    ] : x if x != null])
    
    volumes_created = length([
      docker_volume.mongodb_data.name,
      docker_volume.redis_data.name,
      docker_volume.consul_data.name,
      docker_volume.prometheus_data.name,
      docker_volume.grafana_data.name
    ])
    
    network_created = docker_network.higherself_network.name
    
    next_steps = [
      "Check application health: curl http://localhost:${var.container_port}/health",
      "View application logs: docker logs ${docker_container.higherself_server.name}",
      "Access API documentation: http://localhost:${var.container_port}/docs",
      var.consul_enabled && var.environment == "development" ? "Access Consul UI: http://localhost:8500" : null
    ]
  }
}
