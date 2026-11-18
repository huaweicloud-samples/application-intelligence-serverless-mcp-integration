# -*- coding: utf-8 -*-
"""
租户解析函数 - 根据租户ID查询租户信息
"""

import json
import os
import pymysql


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
    处理租户查询请求

    请求参数:
    - tenant_id: 租户ID (query string 或 body)

    返回: 租户信息
    """
    print(f"收到查询请求: {json.dumps(event)}")

    try:
        # 解析请求参数
        if isinstance(event, dict):
            if 'queryStringParameters' in event:
                params = event.get('queryStringParameters', {})
                tenant_id = params.get('tenant_id')
            elif 'body' in event:
                body = json.loads(event.get('body', '{}'))
                tenant_id = body.get('tenant_id')
            else:
                tenant_id = event.get('tenant_id')
        else:
            tenant_id = event

        if not tenant_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "tenant_id is required"})
            }

        # 查询数据库
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM tenants WHERE tenant_id = %s"
                cursor.execute(sql, (tenant_id,))
                result = cursor.fetchone()

                if result:
                    # 移除敏感信息
                    result.pop('id', None)
                    return {
                        "statusCode": 200,
                        "body": json.dumps(result)
                    }
                else:
                    return {
                        "statusCode": 404,
                        "body": json.dumps({"error": "Tenant not found"})
                    }
        finally:
            conn.close()

    except Exception as e:
        print(f"查询失败: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
