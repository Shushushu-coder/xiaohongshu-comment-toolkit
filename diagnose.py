"""
小红书访问诊断工具
用于快速检测账号和笔记访问状态
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from datetime import datetime

def test_access():
    """测试笔记访问状态"""
    print("=" * 70)
    print("🔍 小红书访问诊断工具")
    print("=" * 70)
    print()
    
    try:
        # 连接到调试 Chrome
        print("1️⃣ 连接远程调试 Chrome...")
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=options)
        print("   ✅ 连接成功")
        print()
        
        # 检查当前页面
        current_url = driver.current_url
        print(f"2️⃣ 当前页面: {current_url}")
        
        # 检查登录状态
        if "xiaohongshu.com" in current_url:
            print("   ✅ 在小红书页面")
            
            # 简单检查登录状态
            page_source = driver.page_source
            if "登录" in page_source and "个人主页" not in page_source:
                print("   ⚠️ 可能未登录，请先手动登录")
                driver.quit()
                return
            else:
                print("   ✅ 已登录")
        else:
            print("   ⚠️ 不在小红书页面")
        
        print()
        
        # 测试笔记列表
        print("3️⃣ 开始测试笔记访问...")
        print()
        
        test_urls = [
            "https://www.xiaohongshu.com/explore/688e39230000000025013980",
            "https://www.xiaohongshu.com/explore/681dc903000000002301395",
            "https://www.xiaohongshu.com/explore/67cfad4d000000000302aea",
        ]
        
        results = []
        for i, url in enumerate(test_urls, 1):
            print(f"   测试 {i}/3: {url}")
            
            try:
                driver.get(url)
                time.sleep(5)  # 等待页面加载
                
                # 检查页面内容
                page_source = driver.page_source
                
                if "暂时无法浏览" in page_source or "无法查看" in page_source:
                    print(f"      ❌ 无法访问 - 显示限制页面")
                    results.append(False)
                elif "评论" in page_source or "点赞" in page_source:
                    print(f"      ✅ 可以访问 - 页面正常")
                    results.append(True)
                else:
                    print(f"      ⚠️ 未知状态 - 页面异常")
                    results.append(False)
                
                # 等待一段时间模拟人类浏览
                time.sleep(5)
                
            except Exception as e:
                print(f"      ❌ 访问失败: {e}")
                results.append(False)
        
        print()
        driver.quit()
        
        # 生成诊断报告
        print("=" * 70)
        print("📊 诊断报告")
        print("=" * 70)
        print()
        
        success_count = sum(results)
        total_count = len(results)
        success_rate = success_count / total_count * 100
        
        print(f"访问成功率: {success_count}/{total_count} ({success_rate:.0f}%)")
        print()
        
        # 给出建议
        if success_rate == 0:
            print("🔴 严重问题 - 所有笔记均无法访问")
            print()
            print("可能原因:")
            print("  1. 账号被严重限制或封禁")
            print("  2. IP地址被封禁")
            print()
            print("建议方案:")
            print("  ✅ 方案1: 更换账号")
            print("  ✅ 方案2: 更换IP地址（重启路由器）")
            print("  ✅ 方案3: 等待 24-48 小时后再试")
            print("  ✅ 方案4: 使用手机热点测试")
            
        elif success_rate < 50:
            print("🟡 中度问题 - 部分笔记无法访问")
            print()
            print("可能原因:")
            print("  1. 触发了小红书的风控系统")
            print("  2. 访问频率过高")
            print()
            print("建议方案:")
            print("  ✅ 方案1: 停止爬取 2-4 小时")
            print("  ✅ 方案2: 大幅降低访问频率")
            print("  ✅ 方案3: 使用慢速模式配置")
            print("  ✅ 方案4: 每次只爬 3-5 个笔记")
            
        elif success_rate < 100:
            print("🟢 轻微问题 - 大部分笔记可以访问")
            print()
            print("可能原因:")
            print("  1. 部分笔记本身不可访问")
            print("  2. 轻度触发风控")
            print()
            print("建议方案:")
            print("  ✅ 方案1: 稍微降低访问频率")
            print("  ✅ 方案2: 增加笔记间的等待时间")
            print("  ✅ 方案3: 继续观察，谨慎使用")
            
        else:
            print("🟢 访问正常 - 可以继续使用")
            print()
            print("建议:")
            print("  ✅ 保持当前的访问频率")
            print("  ✅ 继续使用慢速模式")
            print("  ✅ 定期（每小时）检查状态")
        
        print()
        print("=" * 70)
        print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        print()
        print("请确认:")
        print("  1. 已经运行了 start_xiaohongshu_chrome.bat")
        print("  2. Chrome 调试模式正在运行")
        print("  3. 已在浏览器中登录小红书")

if __name__ == "__main__":
    print()
    print("⚠️  请确保:")
    print("   1. 已运行 start_xiaohongshu_chrome.bat")
    print("   2. 已在浏览器中登录小红书")
    print()
    input("按 Enter 开始诊断...")
    print()
    
    test_access()