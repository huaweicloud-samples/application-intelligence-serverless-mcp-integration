# -*- coding: utf-8 -*-
"""
授权检查函数 - 检查租户是否有权访问产品
对应实现: entitlement-sqs 流程
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


def check_entitlement(tenant_id, product_code):
    """
    检查租户授权状态
    对应实现: 产品授权查询接口
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT * FROM entitlements
                WHERE tenant_id = %s AND product_code = %s
                AND status = 'active'
                AND (expired_at IS NULL OR expired_at > NOW())
            """
            cursor.execute(sql, (tenant_id, product_code))
            return cursor.fetchone()
    finally:
        conn.close()


def handler(event, context):
    """
    处理授权检查请求

    请求参数 (JSON body):
    {
        "tenant_id": "租户ID",
        "product_code": "产品代码"
    }

    返回:
    {
        "entitled": true/false,
        "tenant_id": "租户ID",
        "product_code": "产品代码"
    }
    """
    print(f"收到授权检查请求: {json.dumps(event)}")

    try:
        # 解析请求参数
        if isinstance(event, dict) and 'body' in event:
            body = json.loads(event.get('body', '{}'))
        elif isinstance(event, dict):
            body = event
        else:
            body = json.loads(event)

        tenant_id = body.get('tenant_id')
        product_code = body.get('product_code', 'default-product')

        if not tenant_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "tenant_id is required"})
            }

        # 检查租户是否存在且活跃
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 检查租户状态
                sql = "SELECT status FROM tenants WHERE tenant_id = %s"
                cursor.execute(sql, (tenant_id,))
                tenant = cursor.fetchone()

                if not tenant or tenant.get('status') != 'active':
                    return {
                        "statusCode": 200,
                        "body": json.dumps({
                            "entitled": False,
                            "tenant_id": tenant_id,
                            "reason": "Tenant not found or inactive"
                        })
                    }

                # 检查授权
                entitlement = check_entitlement(tenant_id, product_code)

                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "entitled": entitlement is not None,
                        "tenant_id": tenant_id,
                        "product_code": product_code,
                        "entitlement": entitlement
                    })
                }
        finally:
            conn.close()

    except Exception as e:
        print(f"授权检查失败: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
