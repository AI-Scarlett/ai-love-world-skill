#!/usr/bin/env python3
"""
AI Love World 持续测试服务
作为后台服务运行，持续测试所有功能
"""

import requests
import json
import time
import random
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/var/www/ailoveworld/logs/auto_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BASE_URL = "http://8.148.230.65"
API_URL = f"{BASE_URL}/api"

def test_endpoint(name, url, method="GET", data=None, headers=None):
    """测试单个接口"""
    try:
        start_time = time.time()
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.post(url, json=data, headers=headers, timeout=10)
        
        elapsed = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("success"):
                    logger.info(f"✅ {name} - {elapsed:.0f}ms")
                    return True
                else:
                    logger.error(f"❌ {name} - 业务错误: {result.get('error', 'Unknown')}")
                    return False
            except:
                logger.info(f"✅ {name} - {elapsed:.0f}ms")
                return True
        else:
            logger.error(f"❌ {name} - HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ {name} - {str(e)}")
        return False

def run_tests():
    """运行一轮测试"""
    tests = [
        ("首页", f"{BASE_URL}/"),
        ("社区帖子", f"{API_URL}/community/posts"),
        ("排行榜", f"{API_URL}/leaderboard/points?limit=10"),
        ("礼物商店", f"{API_URL}/gifts/store"),
        ("健康检查", f"{API_URL}/health"),
    ]
    
    passed = 0
    failed = 0
    
    for name, url in tests:
        if test_endpoint(name, url):
            passed += 1
        else:
            failed += 1
        time.sleep(0.5)
    
    logger.info(f"本轮测试完成: 通过 {passed}, 失败 {failed}")
    return failed == 0

def main():
    """主循环"""
    logger.info("=" * 60)
    logger.info("AI Love World 持续测试服务启动")
    logger.info("=" * 60)
    
    round_num = 0
    while True:
        round_num += 1
        logger.info(f"\n第 {round_num} 轮测试开始")
        
        success = run_tests()
        
        if success:
            sleep_time = random.randint(30, 60)
        else:
            sleep_time = 10  # 失败时快速重试
            logger.warning("本轮测试有失败项，10秒后重试")
        
        logger.info(f"等待 {sleep_time} 秒后进行下一轮...")
        time.sleep(sleep_time)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("测试服务已停止")
    except Exception as e:
        logger.error(f"测试服务异常: {e}")
