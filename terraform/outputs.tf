# HigherSelf Network Server - Terraform Outputs
# Enterprise-grade infrastructure outputs for monitoring and integration

output "project_info" {
  description = "Project information and metadata"
  value = {
    name        = local.project_name
    environment = local.environment
    tags        = local.common_tags
  }
}

output "network_info" {
  description = "Docker network information"
  value = {
    network_id   = docker_network.higherself_network.id
    network_name = docker_network.higherself_network.name
    driver       = docker_network.higherself_network.driver
  }
}

output "volume_info" {
  description = "Docker volume information"
  value = {
    mongodb_volume = {
      id   = docker_volume.mongodb_data.id
      name = docker_volume.mongodb_data.name
    }
    redis_volume = {
      id   = docker_volume.redis_data.id
      name = docker_volume.redis_data.name
    }
    consul_volume = {
      id   = docker_volume.consul_data.id
      name = docker_volume.consul_data.name
    }
    prometheus_volume = {
      id   = docker_volume.prometheus_data.id
      name = docker_volume.prometheus_data.name
    }
    grafana_volume = {
      id   = docker_volume.grafana_data.id
      name = docker_volume.grafana_data.name
    }
    logs_volume = {
      id   = docker_volume.app_logs.id
      name = docker_volume.app_logs.name
    }
    data_volume = {
      id   = docker_volume.app_data.id
      name = docker_volume.app_data.name
    }
  }
}

output "service_endpoints" {
  description = "Service endpoint information"
  value = {
    windsurf_agent = {
      port = local.services.windsurf_agent.port
      url  = "http://localhost:${local.services.windsurf_agent.port}"
    }
    mongodb = {
      port = local.services.mongodb.port
      url  = "mongodb://localhost:${local.services.mongodb.port}/${var.mongodb_database}"
    }
    redis = {
      port = local.services.redis.port
      url  = "redis://localhost:${local.services.redis.port}/0"
    }
    nginx = {
      http_port  = 80
      https_port = 443
      http_url   = "http://localhost"
      https_url  = "https://localhost"
    }
    prometheus = {
      port = local.services.prometheus.port
      url  = "http://localhost:${local.services.prometheus.port}"
    }
    grafana = {
      port = local.services.grafana.port
      url  = "http://localhost:${local.services.grafana.port}"
    }
    consul = {
      port = local.services.consul.port
      url  = "http://localhost:${local.services.consul.port}"
    }
  }
}

output "resource_configuration" {
  description = "Resource configuration for current environment"
  value = var.resource_limits[var.environment]
}

output "deployment_commands" {
  description = "Useful deployment commands"
  value = {
    terraform_init    = "terraform init"
    terraform_plan    = "terraform plan -var-file=\"environments/${var.environment}.tfvars\""
    terraform_apply   = "terraform apply -var-file=\"environments/${var.environment}.tfvars\""
    terraform_destroy = "terraform destroy -var-file=\"environments/${var.environment}.tfvars\""
    docker_compose    = "docker-compose -f docker-compose.yml up -d"
    health_check      = "curl -f http://localhost:8000/health"
  }
}

output "monitoring_urls" {
  description = "Monitoring and observability URLs"
  value = var.enable_monitoring ? {
    prometheus = "http://localhost:9090"
    grafana    = "http://localhost:3000"
    consul     = "http://localhost:8500"
    health     = "http://localhost:8000/health"
    metrics    = "http://localhost:8000/metrics"
  } : {}
}

output "security_info" {
  description = "Security configuration information"
  value = {
    ssl_enabled    = var.enable_ssl
    allowed_ips    = var.allowed_ips
    backup_enabled = var.backup_retention_days > 0
  }
  sensitive = false
}

output "integration_status" {
  description = "Integration service status"
  value = {
    notion_configured     = var.notion_token != ""
    openai_configured     = var.openai_api_key != ""
    huggingface_configured = var.huggingface_token != ""
    cloud_deployment      = var.enable_cloud_deployment
    cloud_provider        = var.cloud_provider
  }
  sensitive = false
}

output "scaling_configuration" {
  description = "Auto-scaling configuration"
  value = var.enable_autoscaling ? {
    enabled       = true
    min_replicas  = var.min_replicas
    max_replicas  = var.max_replicas
    cpu_threshold = var.cpu_threshold
  } : {
    enabled = false
  }
}

output "backup_configuration" {
  description = "Backup and disaster recovery configuration"
  value = {
    retention_days = var.backup_retention_days
    schedule       = var.backup_schedule
    enabled        = var.backup_retention_days > 0
  }
}

output "terraform_workspace" {
  description = "Current Terraform workspace information"
  value = {
    workspace   = terraform.workspace
    environment = var.environment
    state_path  = "terraform.tfstate"
  }
}

output "quick_start_guide" {
  description = "Quick start commands for HigherSelf Network Server"
  value = {
    step_1 = "terraform init"
    step_2 = "terraform plan -var-file=\"environments/${var.environment}.tfvars\""
    step_3 = "terraform apply -var-file=\"environments/${var.environment}.tfvars\""
    step_4 = "docker-compose up -d"
    step_5 = "curl http://localhost:8000/health"
    
    monitoring = var.enable_monitoring ? {
      prometheus = "Open http://localhost:9090 for metrics"
      grafana    = "Open http://localhost:3000 for dashboards (admin/admin)"
      consul     = "Open http://localhost:8500 for service discovery"
    } : "Monitoring disabled"
    
    logs = "docker-compose logs -f windsurf-agent"
    stop = "docker-compose down"
  }
}
