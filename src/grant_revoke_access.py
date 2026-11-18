# -*- coding: utf-8 -*-
"""
授权管理函数 - 授予或撤销租户对产品的访问权限
对应实现: 产品授权授予/撤销流程
"""

import json
import os
import pymysql
from datetime import datetime, timedelta


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


def handler(event, context):
    """
    处理授权管理请求

    请求参数 (JSON body):
    {
        "action": "grant" | "revoke",
        "tenant_id": "租户ID",
        "product_code": "产品代码",
        "dimension": "计量维度 (如 admin_users, api_calls)",
        "quantity": 数量 (仅 grant 时需要),
        "expired_at": "过期时间 (ISO格式, 可选)"
    }

    返回:
    {
        "success": true/false,
        "action": "grant" | "revoke",
        "tenant_id": "租户ID"
    }
    """
    print(f"收到授权管理请求: {json.dumps(event)}")

    try:
        # 解析请求参数
        if isinstance(event, dict) and 'body' in event:
            body = json.loads(event.get('body', '{}'))
        elif isinstance(event, dict):
            body = event
        else:
            body = json.loads(event)

        action = body.get('action', 'grant').lower()
        tenant_id = body.get('tenant_id')
        product_code = body.get('product_code', 'default-product')
        dimension = body.get('dimension', 'default')
        quantity = body.get('quantity', 1)
        expired_at = body.get('expired_at')

        if not tenant_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "tenant_id is required"})
            }

        if action not in ['grant', 'revoke']:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "action must be 'grant' or 'revoke'"})
            }

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 创建授权表（如果不存在）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS entitlements (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        tenant_id VARCHAR(255) NOT NULL,
                        product_code VARCHAR(255) NOT NULL,
                        dimension VARCHAR(255) DEFAULT 'default',
                        quantity INT DEFAULT 1,
                        status VARCHAR(50) DEFAULT 'active',
                        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expired_at DATETIME,
                        INDEX idx_tenant_product (tenant_id, product_code),
                        UNIQUE KEY uk_tenant_product_dim (tenant_id, product_code, dimension)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)

                if action == 'grant':
                    # 解析过期时间
                    expired_at_val = None
                    if expired_at:
                        expired_at_val = datetime.fromisoformat(expired_at.replace('Z', '+00:00'))

                    # 插入或更新授权记录
                    sql = """
                        INSERT INTO entitlements (tenant_id, product_code, dimension, quantity, status, expired_at)
                        VALUES (%s, %s, %s, %s, 'active', %s)
                        ON DUPLICATE KEY UPDATE
                            quantity = VALUES(quantity),
                            status = 'active',
                            expired_at = VALUES(expired_at),
                            granted_at = NOW()
                    """
                    cursor.execute(sql, (tenant_id, product_code, dimension, quantity, expired_at_val))
                    conn.commit()

                    # 更新租户状态为活跃
                    cursor.execute(
                        "UPDATE tenants SET status = 'active' WHERE tenant_id = %s",
                        (tenant_id,)
                    )
                    conn.commit()

                    print(f"授权成功: tenant_id={tenant_id}, product={product_code}, quantity={quantity}")

                else:  # revoke
                    # 撤销授权
                    sql = """
                        UPDATE entitlements
                        SET status = 'revoked'
                        WHERE tenant_id = %s AND product_code = %s
                    """
                    cursor.execute(sql, (tenant_id, product_code))
                    conn.commit()

                    # 更新租户状态为停用
                    cursor.execute(
                        "UPDATE tenants SET status = 'suspended' WHERE tenant_id = %s",
                        (tenant_id,)
                    )
                    conn.commit()

                    print(f"撤销授权成功: tenant_id={tenant_id}, product={product_code}")

                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "success": True,
                        "action": action,
                        "tenant_id": tenant_id,
                        "product_code": product_code
                    })
                }
        finally:
            conn.close()

    except Exception as e:
        print(f"授权管理失败: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
