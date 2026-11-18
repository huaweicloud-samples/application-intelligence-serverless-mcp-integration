# 架构说明

## 整体架构

本项目实现基于华为云的 Serverless 多租户 SaaS 架构，主要包含以下核心模块：

## 1. 租户管理模块

- **tenant-register**：租户注册 API
- **tenant-resolve**：租户信息查询 API
- 数据存储：RDS MySQL (DynamoDB 兼容模式)

## 2. 授权管理模块

- **entitlement-check**：检查租户产品授权
- **entitlement-sync**：同步授权变更事件（通过 RocketMQ）
- 事件驱动架构：基于 DMS RocketMQ

## 3. 计量结算模块

- **metering-scheduler**：定时触发器（按 60 分钟周期执行）
- **metering-collector**：收集租户用量数据
- 存储：OBS (对象存储)

## 4. API 网关

- 统一入口：华为云 APIG
- 认证：支持 API Key / JWT
- 限流：可配置 QPS 限制

## 5. 消息通知

- SMN 主题：发送告警和通知
- RocketMQ：异步消息处理

## 技术栈

| 组件 | 华为云服务 |
|------|-----------|
| 计算 | FunctionGraph |
| API | APIG |
| 数据库 | RDS MySQL |
| 存储 | OBS |
| 消息队列 | DMS RocketMQ |
| 通知 | SMN |
| 日志 | LTS |
