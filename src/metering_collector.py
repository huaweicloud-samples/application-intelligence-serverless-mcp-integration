# -*- coding: utf-8 -*-
"""
计量收集器函数 - 从 RocketMQ 队列接收计量记录
对应实现: metering 队列消费流程
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


def save_metering_record(tenant_id, product_code, dimension, quantity, timestamp):
    """保存计量记录到数据库"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 创建计量记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metering_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tenant_id VARCHAR(255) NOT NULL,
                    product_code VARCHAR(255) NOT NULL,
                    dimension VARCHAR(255) DEFAULT 'default',
                    quantity INT NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    billing_period DATE,
                    INDEX idx_tenant_period (tenant_id, billing_period)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # 获取当前计量周期 (按小时)
            billing_period = datetime.now().date()

            # 插入计量记录
            sql = """
                INSERT INTO metering_records (tenant_id, product_code, dimension, quantity, billing_period)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (tenant_id, product_code, dimension, quantity, billing_period))
            conn.commit()

            print(f"计量记录已保存: tenant={tenant_id}, dim={dimension}, qty={quantity}")
            return True
    finally:
        conn.close()


def handler(event, context):
    """
    处理 RocketMQ 消息中的计量请求
    对应实现: 消息队列消费

    消息格式 (JSON):
    {
        "tenant_id": "租户ID",
        "product_code": "产品代码",
        "dimension": "计量维度",
        "quantity": 数量,
        "timestamp": "时间戳"
    }
    """
    print(f"收到计量请求: {json.dumps(event)}")

    try:
        # 解析消息 - RocketMQ 可能通过不同方式传递消息
        if isinstance(event, dict):
            # 检查消息体
            messages = event.get('messages', [])
            if messages:
                # RocketMQ 消息格式
                msg_body = json.loads(messages[0].get('body', '{}'))
            elif 'body' in event:
                msg_body = json.loads(event.get('body', '{}'))
            else:
                msg_body = event
        else:
            msg_body = json.loads(event)

        tenant_id = msg_body.get('tenant_id')
        product_code = msg_body.get('product_code', 'default-product')
        dimension = msg_body.get('dimension', 'default')
        quantity = msg_body.get('quantity', 1)
        timestamp = msg_body.get('timestamp', datetime.now().isoformat())

        if not tenant_id:
            print("缺少 tenant_id，跳过处理")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "tenant_id is required"})
            }

        # 保存计量记录
        save_metering_record(tenant_id, product_code, dimension, quantity, timestamp)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "metering_recorded": True,
                "tenant_id": tenant_id
            })
        }

    except Exception as e:
        print(f"计量处理失败: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
