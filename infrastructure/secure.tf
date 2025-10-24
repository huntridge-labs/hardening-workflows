# Secure Terraform configuration following best practices
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Secure backend configuration
  backend "s3" {
    # Backend configuration should be provided via backend config file
    # No hardcoded values here
  }
}

# Configure the AWS Provider with secure settings
provider "aws" {
  region = var.aws_region

  # Enforce secure communication
  skip_credentials_validation = false
  skip_metadata_api_check     = false
  skip_region_validation      = false

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
      Owner       = var.owner
    }
  }
}

# Secondary provider for replication region
provider "aws" {
  alias  = "replica"
  region = var.replica_region

  # Enforce secure communication
  skip_credentials_validation = false
  skip_metadata_api_check     = false
  skip_region_validation      = false

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
      Owner       = var.owner
    }
  }
}

# Variables
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
  validation {
    condition = can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", var.aws_region))
    error_message = "AWS region must be a valid region format."
  }
}

variable "replica_region" {
  description = "AWS region for S3 bucket replication"
  type        = string
  default     = "us-east-1"
  validation {
    condition = can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", var.replica_region))
    error_message = "Replica region must be a valid region format."
  }
}

variable "environment" {
  description = "Environment name"
  type        = string
  validation {
    condition = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  validation {
    condition = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "owner" {
  description = "Owner of the resources"
  type        = string
}

# KMS key for S3 bucket encryption
resource "aws_kms_key" "s3_bucket_key" {
  description             = "KMS key for S3 bucket encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-s3-key"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "s3_bucket_key_alias" {
  name          = "alias/${var.project_name}-${var.environment}-s3-key"
  target_key_id = aws_kms_key.s3_bucket_key.key_id
}

# KMS key for replica bucket encryption
resource "aws_kms_key" "s3_replica_bucket_key" {
  provider                = aws.replica
  description             = "KMS key for S3 replica bucket encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-s3-replica-key"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "s3_replica_bucket_key_alias" {
  provider      = aws.replica
  name          = "alias/${var.project_name}-${var.environment}-s3-replica-key"
  target_key_id = aws_kms_key.s3_replica_bucket_key.key_id
}

# IAM role for S3 replication
resource "aws_iam_role" "s3_replication_role" {
  name = "${var.project_name}-${var.environment}-s3-replication-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-s3-replication-role"
    Environment = var.environment
  }
}

# IAM policy for S3 replication
resource "aws_iam_role_policy" "s3_replication_policy" {
  name = "${var.project_name}-${var.environment}-s3-replication-policy"
  role = aws_iam_role.s3_replication_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          aws_s3_bucket.secure_bucket.arn
        ]
      },
      {
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Effect = "Allow"
        Resource = [
          "${aws_s3_bucket.secure_bucket.arn}/*"
        ]
      },
      {
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ]
        Effect = "Allow"
        Resource = [
          "${aws_s3_bucket.replica_bucket.arn}/*"
        ]
      },
      {
        Action = [
          "kms:Decrypt"
        ]
        Effect = "Allow"
        Resource = [
          aws_kms_key.s3_bucket_key.arn
        ]
        Condition = {
          StringLike = {
            "kms:ViaService" = "s3.${var.aws_region}.amazonaws.com"
          }
        }
      },
      {
        Action = [
          "kms:Encrypt"
        ]
        Effect = "Allow"
        Resource = [
          aws_kms_key.s3_replica_bucket_key.arn
        ]
        Condition = {
          StringLike = {
            "kms:ViaService" = "s3.${var.replica_region}.amazonaws.com"
          }
        }
      }
    ]
  })
}

# Replica S3 bucket in different region
resource "aws_s3_bucket" "replica_bucket" {
  provider = aws.replica
  bucket   = "${var.project_name}-${var.environment}-secure-bucket-replica"

  tags = {
    Name        = "Secure Application Bucket Replica"
    Environment = var.environment
  }
}

# Enable versioning for replica bucket (required for replication)
resource "aws_s3_bucket_versioning" "replica_bucket_versioning" {
  provider = aws.replica
  bucket   = aws_s3_bucket.replica_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Encrypt replica bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "replica_bucket_encryption" {
  provider = aws.replica
  bucket   = aws_s3_bucket.replica_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3_replica_bucket_key.arn
    }
    bucket_key_enabled = true
  }
}

# Block public access for replica bucket
resource "aws_s3_bucket_public_access_block" "replica_bucket_pab" {
  provider = aws.replica
  bucket   = aws_s3_bucket.replica_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Secure S3 bucket configuration
resource "aws_s3_bucket" "secure_bucket" {
  bucket = "${var.project_name}-${var.environment}-secure-bucket"

  tags = {
    Name        = "Secure Application Bucket"
    Environment = var.environment
  }
}

# Enable versioning
resource "aws_s3_bucket_versioning" "secure_bucket_versioning" {
  bucket = aws_s3_bucket.secure_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "secure_bucket_encryption" {
  bucket = aws_s3_bucket.secure_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3_bucket_key.arn
    }
    bucket_key_enabled = true
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "secure_bucket_pab" {
  bucket = aws_s3_bucket.secure_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable cross-region replication
resource "aws_s3_bucket_replication_configuration" "secure_bucket_replication" {
  depends_on = [aws_s3_bucket_versioning.secure_bucket_versioning]

  role   = aws_iam_role.s3_replication_role.arn
  bucket = aws_s3_bucket.secure_bucket.id

  rule {
    id     = "replicate-all"
    status = "Enabled"

    filter {}

    destination {
      bucket        = aws_s3_bucket.replica_bucket.arn
      storage_class = "STANDARD"

      encryption_configuration {
        replica_kms_key_id = aws_kms_key.s3_replica_bucket_key.arn
      }
    }

    delete_marker_replication {
      status = "Enabled"
    }
  }
}

# S3 bucket for access logs
resource "aws_s3_bucket" "logs_bucket" {
  bucket = "${var.project_name}-${var.environment}-logs-bucket"

  tags = {
    Name        = "Access Logs Bucket"
    Environment = var.environment
  }
}

# Enable versioning for logs bucket
resource "aws_s3_bucket_versioning" "logs_bucket_versioning" {
  bucket = aws_s3_bucket.logs_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Encrypt logs bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "logs_bucket_encryption" {
  bucket = aws_s3_bucket.logs_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3_bucket_key.arn
    }
    bucket_key_enabled = true
  }
}

# Block public access for logs bucket
resource "aws_s3_bucket_public_access_block" "logs_bucket_pab" {
  bucket = aws_s3_bucket.logs_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable logging for secure bucket
resource "aws_s3_bucket_logging" "secure_bucket_logging" {
  bucket = aws_s3_bucket.secure_bucket.id

  target_bucket = aws_s3_bucket.logs_bucket.id
  target_prefix = "s3-access-logs/"
}

# Secure VPC configuration
resource "aws_vpc" "secure_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc"
  }
}

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  name              = "/aws/vpc/${var.project_name}-${var.environment}-flow-logs"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.s3_bucket_key.arn

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpc-flow-logs"
    Environment = var.environment
  }
}

# IAM role for VPC Flow Logs
resource "aws_iam_role" "vpc_flow_logs_role" {
  name = "${var.project_name}-${var.environment}-vpc-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpc-flow-logs-role"
    Environment = var.environment
  }
}

# IAM policy for VPC Flow Logs
resource "aws_iam_role_policy" "vpc_flow_logs_policy" {
  name = "${var.project_name}-${var.environment}-vpc-flow-logs-policy"
  role = aws_iam_role.vpc_flow_logs_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect = "Allow"
        Resource = "*"
      }
    ]
  })
}

# Enable VPC Flow Logs
resource "aws_flow_log" "vpc_flow_logs" {
  iam_role_arn    = aws_iam_role.vpc_flow_logs_role.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_logs.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.secure_vpc.id

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpc-flow-logs"
    Environment = var.environment
  }
}

# Private subnets only
resource "aws_subnet" "private_subnet" {
  count = 2

  vpc_id            = aws_vpc.secure_vpc.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.project_name}-${var.environment}-private-subnet-${count.index + 1}"
    Type = "private"
  }
}

# Security group with minimal permissions
resource "aws_security_group" "secure_sg" {
  name_prefix = "${var.project_name}-${var.environment}-"
  description = "Secure security group with restricted HTTPS access within VPC only"
  vpc_id      = aws_vpc.secure_vpc.id

  # Only necessary ingress rules
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
    description = "HTTPS from VPC"
  }

  # Restricted egress - only within VPC
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
    description = "HTTPS outbound within VPC only"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-sg"
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

# Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.secure_vpc.id
}

output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.secure_bucket.id
}

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.secure_sg.id
}
