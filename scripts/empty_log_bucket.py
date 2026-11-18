#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理日志桶脚本
对应实现: 日志桶清空脚本

功能: 清空 OBS 日志桶中的对象
"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def empty_obs_bucket(bucket_name, obs_client):
    """
    清空 OBS 桶中的所有对象

    Args:
        bucket_name: OBS 桶名称
        obs_client: OBS 客户端实例
    """
    print(f"正在清空桶: {bucket_name}")

    try:
        # 获取桶中所有对象
        response = obs_client.listObjects(bucket_name)

        if 'contents' in response:
            objects = response['contents']
            print(f"发现 {len(objects)} 个对象")

            # 删除所有对象
            for obj in objects:
                object_key = obj['key']
                print(f"删除: {object_key}")
                obs_client.deleteObject(bucket_name, object_key)

            print(f"桶 {bucket_name} 已清空")
        else:
            print(f"桶 {bucket_name} 为空")

    except Exception as e:
        print(f"清空桶失败: {str(e)}")
        raise


def main():
    if len(sys.argv) < 2:
        print("用法: python empty_log_bucket.py <bucket_name>")
        print("示例: python empty_log_bucket.py my-log-bucket")
        sys.exit(1)

    bucket_name = sys.argv[1]

    # 初始化 OBS 客户端
    try:
        from obs import ObsClient

        obs_client = ObsClient(
            access_key_id=os.environ.get('HW_ACCESS_KEY_ID', ''),
            secret_access_key=os.environ.get('HW_SECRET_ACCESS_KEY', ''),
            server='obs.cn-north-4.myhuaweicloud.com'
        )

        empty_obs_bucket(bucket_name, obs_client)

    except ImportError:
        print("错误: 请安装华为云 OBS SDK")
        print("安装: pip install esdk-obs-python")
        sys.exit(1)


if __name__ == '__main__':
    main()
