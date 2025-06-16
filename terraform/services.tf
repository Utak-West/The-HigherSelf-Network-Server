# HigherSelf Network Server - Service Definitions
# Enterprise-grade Docker service configurations

# MongoDB Database Service
resource "docker_container" "mongodb" {
  name  = "${local.project_name}-mongodb-${local.environment}"
  image = local.services.mongodb.image
  
  restart = "unless-stopped"
  
  ports {
    internal = local.services.mongodb.port
    external = local.services.mongodb.port
  }
  
  volumes {
    volume_name    = docker_volume.mongodb_data.name
    container_path = "/data/db"
  }
  
  volumes {
    host_path      = abspath("./deployment/mongodb")
    container_path = "/docker-entrypoint-initdb.d"
    read_only      = true
  }
  
  volumes {
    volume_name    = docker_volume.app_logs.name
    container_path = "/var/log/mongodb"
  }
  
  env = [
    "MONGO_INITDB_ROOT_USERNAME=${var.mongodb_root_user}",
    "MONGO_INITDB_ROOT_PASSWORD=${var.mongodb_root_password}",
    "MONGO_INITDB_DATABASE=${var.mongodb_database}",
    "MONGO_APP_USER=${var.mongodb_app_user}",
    "MONGO_APP_PASSWORD=${var.mongodb_app_password}"
  ]
  
  command = [
    "--auth",
    "--bind_ip_all",
    "--logpath", "/var/log/mongodb/mongod.log",
    "--logappend",
    "--wiredTigerCacheSizeGB", "1"
  ]
  
  networks_advanced {
    name = docker_network.higherself_network.name
  }
  
  labels {
    label = "service"
    value = "mongodb"
  }
  
  labels {
    label = "environment"
    value = local.environment
  }
  
  labels {
    label = "prometheus.scrape"
    value = "true"
  }
  
  labels {
    label = "prometheus.port"
    value = "27017"
  }
  
  healthcheck {
    test = [
      "CMD-SHELL",
      "echo 'try { db.runCommand(\"ping\").ok ? 0 : 2 } catch(err) { print(\"MongoDB health check failed: \" + err); 2 }' | mongosh localhost:27017/${var.mongodb_database} --quiet"
    ]
    interval     = "30s"
    timeout      = "10s"
    retries      = 5
    start_period = "40s"
  }
}

# Redis Cache Service
resource "docker_container" "redis" {
  name  = "${local.project_name}-redis-${local.environment}"
  image = local.services.redis.image
  
  restart = "unless-stopped"
  
  ports {
    internal = local.services.redis.port
    external = local.services.redis.port
  }
  
  volumes {
    volume_name    = docker_volume.redis_data.name
    container_path = "/data"
  }
  
  volumes {
    host_path      = abspath("./deployment/redis/redis.conf")
    container_path = "/usr/local/etc/redis/redis.conf"
    read_only      = true
  }
  
  command = ["redis-server", "/usr/local/etc/redis/redis.conf"]
  
  networks_advanced {
    name = docker_network.higherself_network.name
  }
  
  labels {
    label = "service"
    value = "redis"
  }
  
  labels {
    label = "environment"
    value = local.environment
  }
  
  labels {
    label = "prometheus.scrape"
    value = "true"
  }
  
  labels {
    label = "prometheus.port"
    value = "6379"
  }
  
  healthcheck {
    test         = ["CMD", "redis-cli", "ping"]
    interval     = "30s"
    timeout      = "5s"
    retries      = 5
    start_period = "10s"
  }
}

# Consul Service Discovery
resource "docker_container" "consul" {
  name  = "${local.project_name}-consul-${local.environment}"
  image = local.services.consul.image
  
  restart = "unless-stopped"
  
  ports {
    internal = local.services.consul.port
    external = local.services.consul.port
  }
  
  volumes {
    volume_name    = docker_volume.consul_data.name
    container_path = "/consul/data"
  }
  
  env = [
    "CONSUL_BIND_INTERFACE=eth0"
  ]
  
  command = [
    "agent",
    "-server",
    "-ui",
    "-client=0.0.0.0",
    "-bootstrap-expect=1",
    "-data-dir=/consul/data"
  ]
  
  networks_advanced {
    name = docker_network.higherself_network.name
  }
  
  labels {
    label = "service"
    value = "consul"
  }
  
  labels {
    label = "environment"
    value = local.environment
  }
  
  healthcheck {
    test         = ["CMD", "consul", "members"]
    interval     = "30s"
    timeout      = "10s"
    retries      = 5
    start_period = "10s"
  }
}

# Prometheus Monitoring (conditional)
resource "docker_container" "prometheus" {
  count = var.enable_monitoring ? 1 : 0
  
  name  = "${local.project_name}-prometheus-${local.environment}"
  image = local.services.prometheus.image
  
  restart = "unless-stopped"
  
  ports {
    internal = local.services.prometheus.port
    external = local.services.prometheus.port
  }
  
  volumes {
    host_path      = abspath("./deployment/prometheus")
    container_path = "/etc/prometheus"
    read_only      = true
  }
  
  volumes {
    volume_name    = docker_volume.prometheus_data.name
    container_path = "/prometheus"
  }
  
  command = [
    "--config.file=/etc/prometheus/prometheus.yml",
    "--storage.tsdb.path=/prometheus",
    "--web.console.libraries=/etc/prometheus/console_libraries",
    "--web.console.templates=/etc/prometheus/consoles",
    "--web.enable-lifecycle"
  ]
  
  networks_advanced {
    name = docker_network.higherself_network.name
  }
  
  labels {
    label = "service"
    value = "prometheus"
  }
  
  labels {
    label = "environment"
    value = local.environment
  }
  
  depends_on = [
    docker_container.mongodb,
    docker_container.redis,
    docker_container.consul
  ]
}

# Grafana Dashboard (conditional)
resource "docker_container" "grafana" {
  count = var.enable_monitoring ? 1 : 0
  
  name  = "${local.project_name}-grafana-${local.environment}"
  image = local.services.grafana.image
  
  restart = "unless-stopped"
  
  ports {
    internal = local.services.grafana.port
    external = local.services.grafana.port
  }
  
  volumes {
    host_path      = abspath("./deployment/grafana/provisioning")
    container_path = "/etc/grafana/provisioning"
    read_only      = true
  }
  
  volumes {
    volume_name    = docker_volume.grafana_data.name
    container_path = "/var/lib/grafana"
  }
  
  env = [
    "GF_SECURITY_ADMIN_PASSWORD=${var.grafana_admin_password}",
    "GF_SERVER_ROOT_URL=%(protocol)s://%(domain)s:%(http_port)s/grafana/",
    "GF_SERVER_SERVE_FROM_SUB_PATH=true"
  ]
  
  networks_advanced {
    name = docker_network.higherself_network.name
  }
  
  labels {
    label = "service"
    value = "grafana"
  }
  
  labels {
    label = "environment"
    value = local.environment
  }
  
  depends_on = [
    docker_container.prometheus
  ]
}
