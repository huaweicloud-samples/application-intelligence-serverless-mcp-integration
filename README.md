# Serverless SaaS on Huawei Cloud

[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Huawei Cloud](https://img.shields.io/badge/Cloud-华为云-blue.svg)](https://www.huaweicloud.com/)

## Introduction

Huawei Cloud-based Serverless Multi-Tenant SaaS Architecture, implementing tenant registration, subscription management, and metering/settlement functions. Built with FunctionGraph + APIG + RDS MySQL + OBS for serverless applications.

## Table of Contents

- [Architecture](#architecture)
- [Key Features](#key-features)
- [Cloud Services](#cloud-services)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Cleanup](#cleanup)
- [Detailed Documentation](#detailed-documentation)
- [FAQ](#faq)
- [License](#license)
- [Contact](#contact)

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  User/Tenant │────▶│    APIG     │────▶│ FunctionGraph │
│             │     │             │     │   Functions   │
└─────────────┘     └─────────────┘     └───────┬───────┘
                                                │
                    ┌─────────────┐              │
                    │    OBS      │◀─────────────┤
                    │  (Storage)  │              │
                    └─────────────┘              │
                                                ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    SMN      │◀────│  DMS       │◀────│  RDS MySQL   │
│  (Notifications)│     │  RocketMQ  │     │  (Tenant Data)│
└─────────────┘     └─────────────┘     └─────────────┘
```

## Key Features

- **Full Serverless Architecture**: No server management, pay-as-you-go
- **Multi-Tenant Support**: Tenant isolation data model
- **Event-Driven**: RocketMQ for async message processing
- **Scheduled Metering**: FunctionGraph timer triggers metering on a 60-minute cycle

## Cloud Services

| Service | Settlement |
|---------|------------|
| APIG | Per request volume |
| FunctionGraph | Per invocation volume |
| RDS MySQL | Monthly subscription |
| OBS | Per storage volume |
| DMS RocketMQ | Monthly subscription |

## Prerequisites

1. Huawei Cloud account with the following services enabled:
   - FunctionGraph
   - APIG
   - OBS
   - RDS MySQL
   - DMS
   - VPC
2. Terraform >= 1.0 installed
3. Huawei Cloud CLI (`oc`) installed

## Quick Start

```bash
# 1. Clone the project
git clone <this-repo>
cd huaweicloud/application-intelligence-serverless-mcp-integration

# 2. Initialize Terraform
cd infra
terraform init

# 3. Preview deployment
terraform plan

# 4. Deploy
terraform apply
```

## Usage

### Tenant Registration

```bash
curl -X POST https://<api-endpoint>/tenant/register \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "tenant-001", "email": "user@example.com"}'
```

### Query Tenant

```bash
curl -X GET https://<api-endpoint>/tenant/resolve?tenant_id=tenant-001
```

### Check Entitlement

```bash
curl -X POST https://<api-endpoint>/entitlement/check \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "tenant-001", "product_id": "prod-001"}'
```

## Cleanup

```bash
terraform destroy
```

**Note**: Please backup important data before cleanup.

## Detailed Documentation

### Core Components

1. **APIG**: Unified API gateway for all external requests
2. **FunctionGraph**:
   - `tenant-register`: Handle tenant registration
   - `tenant-resolve`: Query tenant information
   - `entitlement-check`: Check tenant authorization
   - `metering-scheduler`: Scheduled metering trigger
   - `metering-collector`: Collect metering data
3. **RDS MySQL**: Store tenant and entitlement data
4. **OBS**: Store tenant-uploaded files
5. **DMS RocketMQ**: Async message queue
6. **SMN**: Send alert notifications

### Environment Variables

| Variable | Description |
|----------|-------------|
| DB_ENDPOINT | RDS MySQL connection address |
| OBS_BUCKET | OBS bucket name |
| ROCKETMQ_ENDPOINT | RocketMQ connection address |

## FAQ

### Q: How to modify tenant data model?
A: Modify RDS MySQL instance configuration in `main.tf`, or implement data model abstraction in code layer.

### Q: What metering/settlement models are supported?
A: The current implementation meters usage on a per-hour cycle, expandable to usage-based settlement.

### Q: How to monitor function calls?
A: View call logs and metrics via FunctionGraph console.

## License

MIT License - See [LICENSE](LICENSE) file

## Contact

- Maintainer: Huawei Cloud Architecture Team
- Email: cloud-architecture@huaweicloud.com

---

*Based on Serverless Multi-Tenant SaaS Architecture Best Practices*

---

[中文版](./README.cn.md)
