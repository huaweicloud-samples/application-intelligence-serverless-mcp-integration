# -*- coding: utf-8 -*-
"""
重定向函数 - 处理 SaaS 产品页面的重定向
对应实现: 产品页重定向流程
"""

import json
import os
import urllib.parse


def handler(event, context):
    """
    处理重定向请求

    请求参数 (query string):
    - product_code: 产品代码
    - redirect_uri: 重定向目标URL (可选)
    - tenant_id: 租户ID (可选，用于多租户场景)

    返回: 302 重定向响应
    """
    print(f"收到重定向请求: {json.dumps(event)}")

    try:
        # 解析请求参数
        if isinstance(event, dict):
            params = event.get('queryStringParameters', {}) or {}

            # 从 query string 获取参数
            product_code = params.get('product_code')
            redirect_uri = params.get('redirect_uri')
            tenant_id = params.get('tenant_id')

            # 如果没有 query string，尝试从 path 获取
            if not product_code:
                path = event.get('path', '/')
                if '/' in path:
                    parts = path.split('/')
                    product_code = parts[-1] if parts[-1] else parts[-2]
        else:
            product_code = None
            redirect_uri = None
            tenant_id = None

        # 确定重定向目标
        frontend_url = os.environ.get('FRONTEND_URL', 'https://your-saas-app.example.com')

        if redirect_uri:
            # 使用提供的重定向URI
            target_url = f"{frontend_url}?redirect={urllib.parse.quote(redirect_uri)}"
        elif tenant_id:
            # 重定向到特定租户的 SaaS 应用
            target_url = f"{frontend_url}/app/{tenant_id}"
        elif product_code:
            # 重定向到产品页面
            target_url = f"{frontend_url}/product/{product_code}"
        else:
            # 默认重定向到首页
            target_url = frontend_url

        print(f"重定向到: {target_url}")

        # 返回 302 重定向响应
        return {
            "statusCode": 302,
            "headers": {
                "Location": target_url,
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            },
            "body": ""
        }

    except Exception as e:
        print(f"重定向处理失败: {str(e)}")

        # 失败时重定向到错误页面或首页
        return {
            "statusCode": 302,
            "headers": {
                "Location": os.environ.get('FRONTEND_URL', 'https://your-saas-app.example.com'),
            },
            "body": ""
        }
