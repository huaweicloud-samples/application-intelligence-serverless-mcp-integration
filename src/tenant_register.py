# -*- coding: utf-8 -*-
"""
租户注册函数 - 注册新租户到 SaaS 系统
对应实现: 新订阅者注册流程
"""

import json
import os
import pymysql
from datetime import datetime


def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=int(os.environ.get('DB_PORT', 3306)),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'saas_tenants'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def send_notification_email(contact_email):
    """
    发送欢迎邮件
    对应实现: 邮件通知服务
    华为云对应: 华为云邮箱推送或消息通知服务
    """
    # 这里可以集成华为云的邮件服务
    # 例如：@hicloud.com 企业邮箱或第三方 SMTP 服务
    print(f"[通知] 发送欢迎邮件到: {contact_email}")
    return True


def handler(event, context):
    """
    处理租户注册请求

    请求参数 (JSON body):
    {
        "tenant_id": "租户ID",
        "company_name": "公司名称",
        "contact_person": "联系人",
        "contact_phone": "联系电话",
        "contact_email": "联系邮箱",
        "product_code": "产品代码"
    }

    返回:
    {
        "statusCode": 200,
        "body": "成功消息"
    }
    """
    print(f"收到注册请求: {json.dumps(event)}")

    try:
        # 解析请求参数
        if isinstance(event, dict) and 'body' in event:
            body = json.loads(event.get('body', '{}'))
        else:
            body = event if isinstance(event, dict) else json.loads(event)

        tenant_id = body.get('tenant_id')
        company_name = body.get('company_name')
        contact_person = body.get('contact_person')
        contact_phone = body.get('contact_phone')
        contact_email = body.get('contact_email')
        product_code = body.get('product_code', 'default-product')

        # 参数验证
        if not all([tenant_id, company_name, contact_person, contact_phone, contact_email]):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Missing required fields"
                })
            }

        # 保存到数据库
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 创建租户表（如果不存在）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tenants (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        tenant_id VARCHAR(255) UNIQUE NOT NULL,
                        company_name VARCHAR(255),
                        contact_person VARCHAR(255),
                        contact_phone VARCHAR(50),
                        contact_email VARCHAR(255),
                        product_code VARCHAR(255),
                        status VARCHAR(50) DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_tenant_id (tenant_id),
                        INDEX idx_email (contact_email)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)

                # 插入或更新租户记录
                sql = """
                    INSERT INTO tenants (tenant_id, company_name, contact_person, contact_phone, contact_email, product_code, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'active')
                    ON DUPLICATE KEY UPDATE
                        company_name = VALUES(company_name),
                        contact_person = VALUES(contact_person),
                        contact_phone = VALUES(contact_phone),
                        contact_email = VALUES(contact_email),
                        product_code = VALUES(product_code),
                        status = 'active',
                        updated_at = NOW()
                """
                cursor.execute(sql, (tenant_id, company_name, contact_person, contact_phone, contact_email, product_code))
                conn.commit()

                print(f"租户 {tenant_id} 注册成功")

        finally:
            conn.close()

        # 发送欢迎通知
        send_notification_email(contact_email)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Registration successful",
                "tenant_id": tenant_id,
                "company_name": company_name
            })
        }

    except Exception as e:
        print(f"注册失败: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }
