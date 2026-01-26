# =============================================================================
# ElastiCache Redis Module
# =============================================================================

variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_group_name" {
  type = string
}

variable "allowed_security_groups" {
  type = list(string)
}

variable "node_type" {
  type = string
}

variable "num_cache_nodes" {
  type = number
}

locals {
  identifier = "${var.project_name}-${var.environment}"
}

# -----------------------------------------------------------------------------
# Security Group
# -----------------------------------------------------------------------------

resource "aws_security_group" "redis" {
  name        = "${local.identifier}-redis-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = var.allowed_security_groups
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.identifier}-redis-sg"
  }
}

# -----------------------------------------------------------------------------
# Random Auth Token
# -----------------------------------------------------------------------------

resource "random_password" "redis_auth" {
  length  = 32
  special = false
}

# -----------------------------------------------------------------------------
# Parameter Group
# -----------------------------------------------------------------------------

resource "aws_elasticache_parameter_group" "main" {
  name   = "${local.identifier}-redis7-params"
  family = "redis7"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  tags = {
    Name = "${local.identifier}-redis7-params"
  }
}

# -----------------------------------------------------------------------------
# ElastiCache Replication Group (Cluster Mode)
# -----------------------------------------------------------------------------

resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = local.identifier
  description                = "Redis cluster for ${local.identifier}"

  engine               = "redis"
  engine_version       = "7.0"
  node_type            = var.node_type
  port                 = 6379
  parameter_group_name = aws_elasticache_parameter_group.main.name

  num_cache_clusters = var.num_cache_nodes

  subnet_group_name  = var.subnet_group_name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_auth.result

  automatic_failover_enabled = true
  multi_az_enabled          = true

  snapshot_retention_limit = 5
  snapshot_window          = "03:00-05:00"
  maintenance_window       = "Mon:05:00-Mon:06:00"

  tags = {
    Name = local.identifier
  }
}

# -----------------------------------------------------------------------------
# Store auth token in Secrets Manager
# -----------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "redis_auth" {
  name = "${var.project_name}/${var.environment}/redis"

  tags = {
    Name = "${local.identifier}-redis-auth"
  }
}

resource "aws_secretsmanager_secret_version" "redis_auth" {
  secret_id = aws_secretsmanager_secret.redis_auth.id
  secret_string = jsonencode({
    endpoint   = aws_elasticache_replication_group.main.configuration_endpoint_address
    port       = aws_elasticache_replication_group.main.port
    auth_token = random_password.redis_auth.result
  })
}

# Outputs are in outputs.tf
