# Serverless SaaS on 华为云

[English](./README.md)

[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![华为云](https://img.shields.io/badge/Cloud-华为云-blue.svg)](https://www.huaweicloud.com/)

## 简介

基于华为云的 Serverless 多租户 SaaS 架构，实现租户注册、订阅管理、计量结算功能。采用 FunctionGraph + APIG + RDS MySQL + OBS 构建无服务器应用。

## 目录

- [架构图](#架构图)
- [方案亮点](#方案亮点)
- [涉及云服务与费用](#涉及云服务与费用)
- [前置条件](#前置条件)
- [快速开始](#快速开始)
- [使用方法](#使用方法)
- [清理资源](#清理资源)
- [详细说明](#详细说明)
- [FAQ](#faq)
- [许可证](#许可证)
- [联系方式](#联系方式)

## 架构图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  用户/租户  │────▶│    APIG     │────▶│ FunctionGraph │
│             │     │             │     │   Functions   │
└─────────────┘     └─────────────┘     └───────┬───────┘
                                                │
                    ┌─────────────┐              │
                    │    OBS      │◀─────────────┤
                    │  (存储)     │              │
                    └─────────────┘              │
                                                ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    SMN      │◀────│  DMS       │◀────│  RDS MySQL   │
│  (消息通知) │     │  RocketMQ  │     │  (租户数据)  │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 方案亮点

- **全 Serverless 架构**：无需管理服务器，按需付费
- **多租户支持**：基于租户隔离的数据模型
- **事件驱动**：RocketMQ 实现异步消息处理
- **定时计量**：FunctionGraph 定时触发器实现按小时计量

## 涉及云服务

| 云服务 | 结算方式 |
|--------|----------|
| APIG | 按调用量结算 |
| FunctionGraph | 按调用量结算 |
| RDS MySQL | 包年包月 |
| OBS | 按存储量结算 |
| DMS RocketMQ | 包年包月 |

## 前置条件

1. 华为云账号已开通以下服务：
   - FunctionGraph
   - APIG
   - OBS
   - RDS MySQL
   - DMS
   - VPC
2. 安装 Terraform >= 1.0
3. 安装华为云 CLI (`oc`)

## 快速开始

```bash
# 1. 克隆项目
git clone <this-repo>
cd huaweicloud/application-intelligence-serverless-mcp-integration

# 2. 初始化 Terraform
cd infra
terraform init

# 3. 预览部署
terraform plan

# 4. 执行部署
terraform apply
```

## 使用方法

### 租户注册

```bash
curl -X POST https://<api-endpoint>/tenant/register \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "tenant-001", "email": "user@example.com"}'
```

### 查询租户

```bash
curl -X GET https://<api-endpoint>/tenant/resolve?tenant_id=tenant-001
```

### 检查授权

```bash
curl -X POST https://<api-endpoint>/entitlement/check \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "tenant-001", "product_id": "prod-001"}'
```

## 清理资源

```bash
terraform destroy
```

**注意**：清理前请确认已备份重要数据。

## 详细说明

### 核心组件

1. **APIG**：统一 API 网关，处理所有外部请求
2. **FunctionGraph**：
   - `tenant-register`：处理租户注册
   - `tenant-resolve`：查询租户信息
   - `entitlement-check`：检查租户授权
   - `metering-scheduler`：定时触发计量任务
   - `metering-collector`：收集计量数据
3. **RDS MySQL**：存储租户和授权数据
4. **OBS**：存储租户上传的文件
5. **DMS RocketMQ**：异步消息队列
6. **SMN**：发送告警通知

### 环境变量

| 变量名 | 说明 |
|--------|------|
| DB_ENDPOINT | RDS MySQL 连接地址 |
| OBS_BUCKET | OBS 存储桶名称 |
| ROCKETMQ_ENDPOINT | RocketMQ 连接地址 |

## FAQ

### Q: 如何修改租户数据模型？
A: 修改 `main.tf` 中 RDS MySQL 实例配置，或在代码层实现数据模型抽象。

### Q: 支持哪些计量结算模式？
A: 当前实现基于小时粒度计量，可扩展为按用量结算。

### Q: 如何监控函数调用？
A: 通过 FunctionGraph 控制台查看调用日志和监控指标。

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 维护者：华为云架构团队
- 邮箱：cloud-architecture@huawei.com

---
*基于 Serverless 多租户 SaaS 架构最佳实践*
