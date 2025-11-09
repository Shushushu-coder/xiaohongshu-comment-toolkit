#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书爬虫 - 远程调试模式测试工具
自动诊断连接问题并提供解决方案
"""

import sys
import socket
import time
import subprocess
import os

def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_step(step, text):
    """打印步骤"""
    print(f"\n[步骤 {step}] {text}")

def check_chrome_process():
    """检查 Chrome 进程"""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq chrome.exe"],
                capture_output=True,
                text=True
            )
            return "chrome.exe" in result.stdout.lower()
        else:
            result = subprocess.run(
                ["pgrep", "chrome"],
                capture_output=True
            )
            return result.returncode == 0
    except:
        return False

def check_debug_port():
    """检查调试端口是否开放"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 9222))
    sock.close()
    return result == 0

def test_selenium_connection():
    """测试 Selenium 连接"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        driver = webdriver.Chrome(options=options)
        
        info = {
            'url': driver.current_url,
            'title': driver.title,
            'success': True
        }
        
        # 不关闭 driver，保持连接
        return info
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    print_header("小红书爬虫 - 远程调试模式测试工具 v1.0")
    print("\n本工具将自动诊断远程调试连接问题")
    
    # 步骤 1: 检查 Chrome 进程
    print_step(1, "检查 Chrome 进程")
    has_chrome = check_chrome_process()
    
    if has_chrome:
        print("✅ 检测到 Chrome 进程运行中")
    else:
        print("⚠️  未检测到 Chrome 进程")
        print("\n💡 建议操作:")
        print("   1. 双击运行: start_xiaohongshu_chrome.bat")
        print("   2. 等待 Chrome 完全启动")
        print("   3. 重新运行本测试脚本")
        return
    
    # 步骤 2: 检查调试端口
    print_step(2, "检查调试端口 9222")
    port_open = check_debug_port()
    
    if port_open:
        print("✅ 端口 9222 已开放")
    else:
        print("❌ 端口 9222 未开放")
        print("\n💡 可能的原因:")
        print("   1. Chrome 未使用调试模式启动")
        print("   2. 端口号配置错误")
        print("\n🔧 解决方案:")
        print("   1. 关闭所有 Chrome 窗口")
        
        if sys.platform == "win32":
            print("      PowerShell: taskkill /F /IM chrome.exe /T")
        else:
            print("      Terminal: killall chrome")
        
        print("   2. 重新运行: start_xiaohongshu_chrome.bat")
        return
    
    # 步骤 3: 检查 Selenium 依赖
    print_step(3, "检查 Selenium 安装")
    try:
        import selenium
        print(f"✅ Selenium 已安装 (版本: {selenium.__version__})")
    except ImportError:
        print("❌ Selenium 未安装")
        print("\n🔧 解决方案:")
        print("   pip install selenium --break-system-packages")
        return
    
    # 步骤 4: 测试连接
    print_step(4, "测试 Selenium 远程调试连接")
    print("正在连接...")
    
    result = test_selenium_connection()
    
    if result['success']:
        print("\n🎉 连接成功!")
        print(f"   当前 URL: {result['url']}")
        print(f"   页面标题: {result['title']}")
        
        # 检查是否在小红书
        if 'xiaohongshu.com' in result['url']:
            print("\n✅ 已在小红书页面")
        else:
            print("\n💡 当前不在小红书页面")
            print("   程序会自动导航到小红书")
        
        print_header("✅ 所有检查通过!")
        print("\n🎯 现在可以运行主程序了:")
        print("   python main.py")
        print("\n💡 使用提示:")
        print("   - 保持 Chrome 窗口打开")
        print("   - 确保已在浏览器中登录小红书")
        print("   - 程序运行期间不要关闭 Chrome")
        
    else:
        print(f"\n❌ 连接失败: {result['error']}")
        print("\n🔍 诊断信息:")
        
        # 详细诊断
        if "No module named" in result['error']:
            print("   问题: 缺少 Python 包")
            print("   解决: pip install selenium --break-system-packages")
        
        elif "chrome not reachable" in result['error'].lower():
            print("   问题: Chrome 无法访问")
            print("   解决: 重启 Chrome 调试模式")
        
        elif "session not created" in result['error'].lower():
            print("   问题: 无法创建 Session")
            print("   解决: 确保 Chrome 是通过调试模式启动的")
            print("          不是普通双击打开的")
        
        else:
            print("   问题: 未知错误")
            print("   建议: 查看完整错误信息")
        
        print("\n🔧 通用解决步骤:")
        print("   1. 关闭所有 Chrome")
        if sys.platform == "win32":
            print("      taskkill /F /IM chrome.exe /T")
        print("   2. 重新运行 start_xiaohongshu_chrome.bat")
        print("   3. 等待 5 秒")
        print("   4. 再次运行本测试脚本")
    
    # 步骤 5: 文件检查（可选）
    print_step(5, "检查项目文件（可选）")
    
    files_to_check = [
        ("start_xiaohongshu_chrome.bat", "Chrome 启动脚本"),
        ("main.py", "主程序"),
        ("scrapers/xiaohongshu_scraper.py", "爬虫核心"),
        ("config/config.yaml", "配置文件"),
    ]
    
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            print(f"   ✅ {description}: {file_path}")
        else:
            print(f"   ⚠️  缺失: {description} ({file_path})")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

def test_quick():
    """快速测试模式（只检查连接）"""
    print("🚀 快速测试模式\n")
    
    # 检查端口
    if not check_debug_port():
        print("❌ 调试端口未开放")
        print("请先运行: start_xiaohongshu_chrome.bat")
        return False
    
    # 测试连接
    result = test_selenium_connection()
    if result['success']:
        print("✅ 连接成功!")
        print(f"URL: {result['url']}")
        return True
    else:
        print(f"❌ 连接失败: {result['error']}")
        return False

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        success = test_quick()
        sys.exit(0 if success else 1)
    else:
        main()
        input("\n按 Enter 退出...")