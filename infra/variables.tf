# Variables for Serverless SaaS on 华为云

variable "region" {
  type        = string
  default     = "cn-north-4"
  description = "华为云区域"
}

variable "project_name" {
  type        = string
  default     = "saas-demo"
  description = "项目名称"
}

variable "vpc_id" {
  type        = string
  default     = ""
  description = "VPC ID (留空使用默认)"
}

variable "subnet_id" {
  type        = string
  default     = ""
  description = "子网 ID (留空使用默认)"
}

variable "db_password" {
  type        = string
  sensitive   = true
  default     = "Placeholder-Db-Pass-123!"
  description = "RDS 数据库管理员密码（生产环境请通过 tfvars 或命令行传入强密码）"
}
