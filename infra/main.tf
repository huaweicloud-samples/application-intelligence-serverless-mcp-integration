# Terraform IaC for Serverless SaaS on 华为云

terraform {
  required_version = ">= 1.0"
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "1.96.1"
    }
  }
}

provider "huaweicloud" {
  region = var.region
}

# ==================== VPC & Network ====================

data "huaweicloud_vpc" "default" {
  id = var.vpc_id != "" ? var.vpc_id : "vpc-default"
}

data "huaweicloud_vpc_subnet" "default" {
  id = var.subnet_id != "" ? var.subnet_id : "subnet-default"
}

# ==================== Security Group ====================

resource "huaweicloud_networking_secgroup" "saas_sg" {
  name        = "saas-sg-${var.project_name}"
  description = "Security group for SaaS application"
}

resource "huaweicloud_networking_secgroup_rule" "allow_https" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = huaweicloud_networking_secgroup.saas_sg.id
}

resource "huaweicloud_networking_secgroup_rule" "allow_http" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = huaweicloud_networking_secgroup.saas_sg.id
}

resource "huaweicloud_networking_secgroup_rule" "allow_mysql" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 3306
  port_range_max    = 3306
  remote_ip_prefix  = "10.0.0.0/8"
  security_group_id = huaweicloud_networking_secgroup.saas_sg.id
}

# ==================== OBS Bucket ====================

resource "huaweicloud_obs_bucket" "assets" {
  bucket        = "${var.project_name}-assets-${var.region}"
  acl           = "private"
  storage_class = "STANDARD"
}

# ==================== RDS for PostgreSQL ====================

resource "huaweicloud_rds_instance" "tenants" {
  name              = "tenants-db"
  flavor            = "rds.pg.s3.medium.ha"
  availability_zone = ["cn-north-4a"]
  security_group_id = huaweicloud_networking_secgroup.saas_sg.id
  subnet_id         = data.huaweicloud_vpc_subnet.default.id
  vpc_id            = data.huaweicloud_vpc.default.id

  db {
    type     = "PostgreSQL"
    version  = "14"
    password = var.db_password
  }

  volume {
    type = "CLOUDSSD"
    size = 20
  }
}

# ==================== DMS RocketMQ ====================

resource "huaweicloud_dms_rocketmq_instance" "main" {
  name               = "saas-rocketmq"
  engine_version     = "4.9"
  flavor_id          = "rocketmq.small.io"
  availability_zones = ["cn-north-4a"]
  storage_space      = 100
  storage_spec_code  = "dms.rocketmq.professional"
  vpc_id             = data.huaweicloud_vpc.default.id
  subnet_id          = data.huaweicloud_vpc_subnet.default.id
  security_group_id  = huaweicloud_networking_secgroup.saas_sg.id
}

resource "huaweicloud_dms_rocketmq_topic" "metering" {
  instance_id = huaweicloud_dms_rocketmq_instance.main.id
  name        = "metering-topic"
  queue_num   = 8
}

# ==================== FunctionGraph Functions ====================

resource "huaweicloud_fgs_function" "tenant_register" {
  name        = "tenant-register"
  runtime     = "Python3.9"
  handler     = "index.handler"
  memory_size = 128
  timeout     = 30

  code_type = "inline"
  func_code = <<-EOF
# -*- coding: utf-8 -*-
import json
def handler(event, context):
    return {"statusCode": 200, "body": json.dumps({"message": "tenant registered"})}
EOF

  user_data = jsonencode({
    DB_HOST    = huaweicloud_rds_instance.tenants.private_ips[0]
    DB_PORT    = "3306"
    DB_NAME    = "tenants"
    DB_USER    = "root"
    OBS_BUCKET = huaweicloud_obs_bucket.assets.bucket
  })

  vpc_id     = data.huaweicloud_vpc.default.id
  network_id = data.huaweicloud_vpc_subnet.default.id
}

resource "huaweicloud_fgs_function" "tenant_resolve" {
  name        = "tenant-resolve"
  runtime     = "Python3.9"
  handler     = "index.handler"
  memory_size = 128
  timeout     = 30

  code_type = "inline"
  func_code = <<-EOF
# -*- coding: utf-8 -*-
import json
def handler(event, context):
    return {"statusCode": 200, "body": json.dumps({"tenant_id": "default"})}
EOF

  user_data = jsonencode({
    DB_HOST = huaweicloud_rds_instance.tenants.private_ips[0]
    DB_PORT = "3306"
  })

  vpc_id     = data.huaweicloud_vpc.default.id
  network_id = data.huaweicloud_vpc_subnet.default.id
}

resource "huaweicloud_fgs_function" "entitlement_check" {
  name        = "entitlement-check"
  runtime     = "Python3.9"
  handler     = "index.handler"
  memory_size = 128
  timeout     = 30

  code_type = "inline"
  func_code = <<-EOF
# -*- coding: utf-8 -*-
import json
def handler(event, context):
    return {"statusCode": 200, "body": json.dumps({"entitled": true})}
EOF

  user_data = jsonencode({
    DB_HOST = huaweicloud_rds_instance.tenants.private_ips[0]
  })

  vpc_id     = data.huaweicloud_vpc.default.id
  network_id = data.huaweicloud_vpc_subnet.default.id
}

# ==================== APIG API Gateway ====================

resource "huaweicloud_apig_instance" "main" {
  name              = "saas-api"
  edition           = "BASIC"
  vpc_id            = data.huaweicloud_vpc.default.id
  subnet_id         = data.huaweicloud_vpc_subnet.default.id
  security_group_id = huaweicloud_networking_secgroup.saas_sg.id
  description       = "SaaS API Gateway"
}

resource "huaweicloud_apig_group" "saas" {
  instance_id = huaweicloud_apig_instance.main.id
  name        = "saas-group"
}

# ==================== Outputs ====================

output "api_endpoint" {
  value = huaweicloud_apig_instance.main.id
}

output "obs_assets_bucket" {
  value = huaweicloud_obs_bucket.assets.bucket
}

output "rds_endpoint" {
  value = huaweicloud_rds_instance.tenants.private_ips[0]
}

output "rocketmq_endpoint" {
  value = huaweicloud_dms_rocketmq_instance.main.broker_address
}
