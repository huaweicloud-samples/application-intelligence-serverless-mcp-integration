# Testing Serverless SaaS on Huawei Cloud

本测试文档用于验证 **华为云 Serverless SaaS Integration** 是否正常工作。

## 前置条件

- [ ] 已完成 Terraform 部署
- [ ] 已配置 RDS MySQL 数据库
- [ ] 已配置 DMS RocketMQ
- [ ] 已配置 APIG API 网关
- [ ] 已获取 API 端点地址

## 测试步骤

### 1. 租户注册测试

```bash
# 注册新租户
curl -X POST https://<api-endpoint>/tenant/register \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant-001",
    "company_name": "测试公司",
    "contact_person": "张三",
    "contact_phone": "+86-13800138000",
    "contact_email": "test@example.com",
    "product_code": "default-product"
  }'
```

预期响应:
```json
{
  "message": "Registration successful",
  "tenant_id": "test-tenant-001",
  "company_name": "测试公司"
}
```

### 2. 租户查询测试

```bash
# 查询租户信息
curl -X GET "https://<api-endpoint>/tenant/resolve?tenant_id=test-tenant-001"
```

预期响应: 返回租户详细信息

### 3. 授权检查测试

```bash
# 检查租户授权
curl -X POST https://<api-endpoint>/entitlement/check \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant-001",
    "product_code": "default-product"
  }'
```

预期响应:
```json
{
  "entitled": true,
  "tenant_id": "test-tenant-001",
  "product_code": "default-product"
}
```

### 4. 授权授予测试

```bash
# 授予租户访问权限
curl -X POST https://<api-endpoint>/entitlement/grant \
  -H "Content-Type: application/json" \
  -d '{
    "action": "grant",
    "tenant_id": "test-tenant-001",
    "product_code": "default-product",
    "dimension": "admin_users",
    "quantity": 5
  }'
```

### 5. 授权撤销测试

```bash
# 撤销租户访问权限
curl -X POST https://<api-endpoint>/entitlement/revoke \
  -H "Content-Type: application/json" \
  -d '{
    "action": "revoke",
    "tenant_id": "test-tenant-001",
    "product_code": "default-product"
  }'
```

### 6. 计量测试

```bash
# 上报计量数据 (通过 RocketMQ)
# 消息格式:
{
  "tenant_id": "test-tenant-001",
  "product_code": "default-product",
  "dimension": "api_calls",
  "quantity": 1000,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 7. 定时计量任务测试

定时计量任务由 FunctionGraph 定时触发器按 60 分钟周期执行。可以在控制台查看执行日志确认任务正常运行。

## 数据库验证

```sql
-- 查看租户表
SELECT * FROM tenants;

-- 查看授权表
SELECT * FROM entitlements;

-- 查看计量记录表
SELECT * FROM metering_records;

-- 查看计量汇总表
SELECT * FROM metering_summary;
```

## 日志查询

查看 FunctionGraph 函数日志:

```bash
# 通过华为云控制台查看
# 或使用 CLI
oc function logs --name tenant-register --limit 100
```

## 常见问题

### Q: 注册失败
A: 检查数据库连接配置，确保 RDS MySQL 可访问

### Q: 授权检查失败
A: 检查 entitlements 表中是否有对应记录

### Q: 计量数据未上报
A: 检查 RocketMQ 队列是否正确配置，消息是否能正常消费
