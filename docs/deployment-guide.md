# 部署指南

## 前置条件

1. 华为云账号
2. Terraform >= 1.0
3. 华为云 CLI (oc)

## 部署步骤

### 1. 环境准备

```bash
# 安装 Terraform
brew install terraform

# 安装华为云 CLI
curl -sSL https://support.huaweicloud.com/devg-cli/cli-bucket-inst.html | bash
```

### 2. 配置认证

```bash
# 配置华为云访问凭证
oc config set --global auth <access_key> <secret_key>
```

### 3. 初始化

```bash
cd infra
terraform init
```

### 4. 配置变量

创建 `terraform.tfvars`：

```hcl
region      = "cn-north-4"
project_name = "saas-demo"
vpc_id      = ""  # 留空使用默认 VPC
subnet_id   = ""  # 留空使用默认子网
```

### 5. 部署

```bash
# 预览
terraform plan

# 部署
terraform apply
```

### 6. 验证

```bash
# 查看输出
terraform output

# 测试 API
curl https://<api-endpoint>/tenant/register
```

## 资源清单

部署将创建以下资源：

| 资源类型 | 数量 |
|----------|------|
| FunctionGraph 函数 | 6 |
| APIG API | 3 |
| RDS MySQL 实例 | 1 |
| OBS Bucket | 2 |
| DMS RocketMQ | 1 |
| SMN Topic | 1 |
| 安全组 | 1 |

## 清理

```bash
terraform destroy
```
