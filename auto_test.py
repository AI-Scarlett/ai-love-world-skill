#!/usr/bin/env python3
"""
AI Love World 自动化测试脚本
模拟真人操作，持续测试所有功能
"""

import requests
import json
import time
import random
from datetime import datetime

# 配置
BASE_URL = "http://8.148.230.65"
API_URL = f"{BASE_URL}/api"
TEST_USER = {"username": "admin2", "password": "123456"}

# 测试结果
results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}

def log(msg, level="INFO"):
    """打印日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def test_api(endpoint, method="GET", data=None, headers=None):
    """测试API接口"""
    try:
        url = f"{API_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.post(url, json=data, headers=headers, timeout=10)
        
        results["total"] += 1
        if response.status_code == 200:
            results["passed"] += 1
            return True, response.json()
        else:
            results["failed"] += 1
            results["errors"].append(f"{endpoint}: HTTP {response.status_code}")
            return False, None
    except Exception as e:
        results["total"] += 1
        results["failed"] += 1
        results["errors"].append(f"{endpoint}: {str(e)}")
        return False, None

def test_homepage():
    """测试首页"""
    log("测试首页...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200 and "AI Love World" in response.text:
            log("✅ 首页正常", "PASS")
            return True
        else:
            log("❌ 首页异常", "FAIL")
            return False
    except Exception as e:
        log(f"❌ 首页错误: {e}", "FAIL")
        return False

def test_community():
    """测试社区"""
    log("测试社区...")
    success, data = test_api("/community/posts")
    if success and data.get("success"):
        posts = data.get("posts", [])
        log(f"✅ 社区正常，共 {len(posts)} 条帖子", "PASS")
        return True
    else:
        log("❌ 社区异常", "FAIL")
        return False

def test_leaderboard():
    """测试排行榜"""
    log("测试排行榜...")
    success, data = test_api("/leaderboard/points?limit=10")
    if success and data.get("success"):
        leaderboard = data.get("leaderboard", [])
        log(f"✅ 排行榜正常，共 {len(leaderboard)} 条数据", "PASS")
        return True
    else:
        log("❌ 排行榜异常", "FAIL")
        return False

def test_gifts():
    """测试礼物"""
    log("测试礼物...")
    success, data = test_api("/gifts/store")
    if success and data.get("success"):
        gifts = data.get("gifts", [])
        log(f"✅ 礼物正常，共 {len(gifts)} 个礼物", "PASS")
        return True
    else:
        log("❌ 礼物异常", "FAIL")
        return False

def test_login():
    """测试登录"""
    log("测试登录...")
    try:
        response = requests.post(
            f"{API_URL}/login",
            json=TEST_USER,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                log("✅ 登录正常", "PASS")
                return data.get("token")
        log("❌ 登录异常", "FAIL")
        return None
    except Exception as e:
        log(f"❌ 登录错误: {e}", "FAIL")
        return None

def test_wallet(token):
    """测试钱包"""
    log("测试钱包...")
    if not token:
        log("⚠️ 跳过钱包测试（未登录）", "SKIP")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    success, data = test_api("/wallet/1", headers=headers)
    if success:
        log("✅ 钱包正常", "PASS")
        return True
    else:
        log("❌ 钱包异常", "FAIL")
        return False

def test_post_create(token):
    """测试发帖"""
    log("测试发帖...")
    if not token:
        log("⚠️ 跳过发帖测试（未登录）", "SKIP")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "content": f"自动化测试帖子 {random.randint(1000, 9999)}",
        "images": []
    }
    success, result = test_api("/community/posts", method="POST", data=data, headers=headers)
    if success and result.get("success"):
        log("✅ 发帖正常", "PASS")
        return True
    else:
        log("❌ 发帖异常", "FAIL")
        return False

def run_all_tests():
    """运行所有测试"""
    log("=" * 50)
    log("开始自动化测试")
    log("=" * 50)
    
    # 重置结果
    results["total"] = 0
    results["passed"] = 0
    results["failed"] = 0
    results["errors"] = []
    
    # 测试不需要登录的功能
    test_homepage()
    test_community()
    test_leaderboard()
    test_gifts()
    
    # 登录并测试需要登录的功能
    token = test_login()
    if token:
        test_wallet(token)
        test_post_create(token)
    
    # 输出测试报告
    log("=" * 50)
    log("测试报告")
    log("=" * 50)
    log(f"总测试数: {results['total']}")
    log(f"通过: {results['passed']}")
    log(f"失败: {results['failed']}")
    
    if results["errors"]:
        log("\n错误详情:")
        for error in results["errors"]:
            log(f"  - {error}", "ERROR")
    
    return results["failed"] == 0

def main():
    """主函数"""
    log("AI Love World 自动化测试脚本启动")
    log("按 Ctrl+C 停止")
    
    test_count = 0
    while True:
        test_count += 1
        log(f"\n第 {test_count} 轮测试")
        run_all_tests()
        
        # 每10轮测试后暂停一下
        if test_count % 10 == 0:
            log("\n已完成 10 轮测试，暂停 30 秒...")
            time.sleep(30)
        else:
            # 每轮测试间隔随机 5-15 秒
            sleep_time = random.randint(5, 15)
            log(f"\n等待 {sleep_time} 秒后进行下一轮测试...")
            time.sleep(sleep_time)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n测试已停止")
        log(f"总测试轮数: {results['total']}")
