# -*- coding: utf-8 -*-
"""
定时计量任务函数 - 按 60 分钟周期触发，收集并上报计量数据
对应实现: 定时计量汇总流程

华为云方案: 使用 FunctionGraph 定时触发器替代 EventBridge
"""

import json
import os
import pymysql
from datetime import datetime, timedelta
import urllib.request
import urllib.parse


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


def collect_metering_data():
    """
    收集所有活跃租户的计量数据
    对应实现: 从计量记录表查询数据
    """
    conn = get_db_connection()
    metering_data = []

    try:
        with conn.cursor() as cursor:
            # 查询所有活跃租户及其授权
            sql = """
                SELECT
                    t.tenant_id,
                    t.company_name,
                    e.product_code,
                    e.dimension,
                    e.quantity as entitled_quantity
                FROM tenants t
                LEFT JOIN entitlements e ON t.tenant_id = e.tenant_id AND e.status = 'active'
                WHERE t.status = 'active'
            """
            cursor.execute(sql)
            tenants = cursor.fetchall()

            # 查询当天的计量记录
            today = datetime.now().date()
            sql_metering = """
                SELECT tenant_id, product_code, dimension, SUM(quantity) as total_quantity
                FROM metering_records
                WHERE billing_period = %s
                GROUP BY tenant_id, product_code, dimension
            """
            cursor.execute(sql_metering, (today,))
            metering_records = cursor.fetchall()

            # 构建计量映射
            metering_map = {}
            for record in metering_records:
                key = (record['tenant_id'], record.get('product_code', 'default'), record.get('dimension', 'default'))
                metering_map[key] = record['total_quantity']

            # 构建计量数据
            for tenant in tenants:
                product_code = tenant.get('product_code', 'default')
                dimension = tenant.get('dimension', 'default')
                entitled_qty = tenant.get('entitled_quantity', 1)

                # 获取实际使用量
                key = (tenant['tenant_id'], product_code, dimension)
                actual_qty = metering_map.get(key, 0)

                metering_data.append({
                    'tenant_id': tenant['tenant_id'],
                    'company_name': tenant['company_name'],
                    'product_code': product_code,
                    'dimension': dimension,
                    'entitled_quantity': entitled_qty,
                    'actual_usage': actual_qty,
                    'timestamp': datetime.now().isoformat()
                })

            return metering_data

    finally:
        conn.close()


def report_metering_to_billing_system(metering_data):
    """
    向计量结算接口上报数据
    对应实现: 计量批量上报接口

    华为云方案: 这里可以对接结算系统或保存到数据库供后续汇总出账
    """
    print(f"上报计量数据: {len(metering_data)} 条记录")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 创建汇总表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metering_summary (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tenant_id VARCHAR(255) NOT NULL,
                    product_code VARCHAR(255),
                    dimension VARCHAR(255),
                    total_quantity INT,
                    billing_period DATE,
                    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_period (billing_period)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            today = datetime.now().date()

            for data in metering_data:
                sql = """
                    INSERT INTO metering_summary
                    (tenant_id, product_code, dimension, total_quantity, billing_period)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    data['tenant_id'],
                    data['product_code'],
                    data['dimension'],
                    data['actual_usage'],
                    today
                ))

            conn.commit()
            print(f"计量数据已汇总到数据库")

    finally:
        conn.close()

    return True


def handler(event, context):
    """
    定时计量任务入口
    华为云: 由 FunctionGraph 定时触发器按 60 分钟周期调用

    对应实现: 定时触发器调度
    """
    print(f"定时计量任务开始: {datetime.now().isoformat()}")
    print(f"触发事件: {json.dumps(event)}")

    try:
        # 1. 收集计量数据
        metering_data = collect_metering_data()
        print(f"收集到 {len(metering_data)} 条计量数据")

        # 2. 上报计量数据
        if metering_data:
            report_metering_to_billing_system(metering_data)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "records_processed": len(metering_data),
                "timestamp": datetime.now().isoformat()
            })
        }

    except Exception as e:
        print(f"定时计量任务失败: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        }
