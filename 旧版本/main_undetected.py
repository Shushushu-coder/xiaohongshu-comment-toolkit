"""
小红书爬虫 - Undetected ChromeDriver版本
这是反检测效果最好的方案！

安装：pip install undetected-chromedriver
"""
import undetected_chromedriver as uc
import random
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class StealthXiaohongshuScraper:
    """使用Undetected ChromeDriver的隐形爬虫"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
    
    def initialize_stealth_browser(self):
        """初始化隐形浏览器"""
        print("🎭 启动隐形浏览器...")
        
        options = uc.ChromeOptions()
        
        # 使用已有的用户配置（保持登录状态）
        profile_path = r"D:\桌面\识别广告\xiaohongshu_scraper\data\chrome_profile"
        options.add_argument(f'--user-data-dir={profile_path}')
        
        # 额外配置
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-first-run')
        options.add_argument('--no-service-autorun')
        options.add_argument('--password-store=basic')
        
        # 设置窗口大小
        options.add_argument('--window-size=1920,1080')
        
        # 禁用一些可能暴露自动化的功能
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            # 使用undetected-chromedriver（会自动处理很多反检测）
            self.driver = uc.Chrome(
                options=options,
                version_main=None,  # 自动检测Chrome版本
                use_subprocess=True
            )
            
            self.wait = WebDriverWait(self.driver, 20)
            
            print("✅ 隐形浏览器已启动")
            return True
            
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            print("\n💡 解决方法：")
            print("1. 确保已安装：pip install undetected-chromedriver")
            print("2. 关闭所有Chrome窗口")
            print("3. 重新运行脚本")
            return False
    
    def human_like_scroll(self, times=5):
        """超级拟人的滚动"""
        print(f"📜 执行 {times} 次拟人滚动...")
        
        for i in range(times):
            # 随机滚动模式
            scroll_type = random.choice(['smooth', 'sudden', 'back'])
            
            if scroll_type == 'smooth':
                # 平滑滚动
                distance = random.randint(300, 800)
                self.driver.execute_script(f"""
                    window.scrollBy({{
                        top: {distance},
                        left: 0,
                        behavior: 'smooth'
                    }});
                """)
                time.sleep(random.uniform(1, 2.5))
                
            elif scroll_type == 'sudden':
                # 突然滚动（模拟快速滑动）
                distance = random.randint(500, 1000)
                self.driver.execute_script(f"window.scrollBy(0, {distance});")
                time.sleep(random.uniform(0.3, 0.8))
                
            else:  # back
                # 回滚（模拟看漏了内容）
                distance = random.randint(-300, -100)
                self.driver.execute_script(f"window.scrollBy(0, {distance});")
                time.sleep(random.uniform(0.5, 1.2))
            
            # 随机停顿
            if random.random() > 0.6:
                pause = random.uniform(1, 3)
                time.sleep(pause)
    
    def visit_xiaohongshu(self):
        """访问小红书并预热"""
        print("\n🌐 访问小红书...")
        
        try:
            self.driver.get("https://www.xiaohongshu.com")
            time.sleep(random.uniform(4, 7))
            
            print("✅ 页面已加载")
            
            # 检查是否需要登录
            if "登录" in self.driver.page_source or "login" in self.driver.current_url:
                print("\n⚠️  需要登录！")
                print("请在浏览器中手动登录小红书")
                input("登录完成后按回车继续...")
            
            return True
            
        except Exception as e:
            print(f"❌ 访问失败: {e}")
            return False
    
    def pre_search_warmup(self, duration=60):
        """搜索前的账号预热"""
        print(f"\n🔥 账号预热 {duration} 秒...")
        print("模拟真实用户浏览行为...")
        
        start_time = time.time()
        action_count = 0
        
        while time.time() - start_time < duration:
            # 随机动作
            actions = ['scroll', 'pause', 'back_scroll', 'quick_scroll']
            action = random.choice(actions)
            
            if action == 'scroll':
                self.human_like_scroll(random.randint(2, 4))
                action_count += 1
                
            elif action == 'pause':
                # 停顿观看
                pause_time = random.uniform(3, 8)
                print(f"  👀 停顿 {pause_time:.1f}秒...")
                time.sleep(pause_time)
                action_count += 1
                
            elif action == 'back_scroll':
                # 向上滚动
                self.driver.execute_script(f"window.scrollBy(0, -{random.randint(200, 500)});")
                time.sleep(random.uniform(1, 2))
                
            else:  # quick_scroll
                # 快速浏览
                for _ in range(random.randint(2, 4)):
                    self.driver.execute_script(f"window.scrollBy(0, {random.randint(400, 700)});")
                    time.sleep(random.uniform(0.3, 0.7))
                action_count += 1
            
            # 小延迟
            time.sleep(random.uniform(0.5, 1.5))
        
        print(f"✅ 预热完成！执行了 {action_count} 个动作")
    
    def smart_search(self, keyword="谷雨"):
        """智能搜索"""
        print(f"\n🔍 搜索: {keyword}")
        
        try:
            # 找搜索框
            search_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='搜索']"))
            )
            
            # 点击搜索框
            time.sleep(random.uniform(0.5, 1))
            search_box.click()
            time.sleep(random.uniform(0.3, 0.7))
            
            # 模拟打字
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.15, 0.35))
            
            # 思考
            time.sleep(random.uniform(0.8, 1.5))
            
            # 提交搜索
            from selenium.webdriver.common.keys import Keys
            search_box.send_keys(Keys.RETURN)
            
            # 等待结果
            time.sleep(random.uniform(4, 7))
            
            # 检测风控
            page_text = self.driver.page_source
            if any(keyword in page_text for keyword in [
                '无法访问', '扫描', '手机', '验证'
            ]):
                print("❌ 检测到风控！")
                
                # 保存截图和HTML
                self.driver.save_screenshot("blocked_screenshot.png")
                with open("blocked_page.html", "w", encoding="utf-8") as f:
                    f.write(page_text)
                
                print("📸 已保存: blocked_screenshot.png")
                print("📄 已保存: blocked_page.html")
                
                return False
            
            print("✅ 搜索成功！")
            return True
            
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return False
    
    def test_run(self):
        """测试运行"""
        print("\n" + "="*60)
        print("🧪 测试运行 - Undetected ChromeDriver")
        print("="*60)
        
        # 1. 启动浏览器
        if not self.initialize_stealth_browser():
            return
        
        # 2. 访问小红书
        if not self.visit_xiaohongshu():
            return
        
        # 3. 预热账号
        self.pre_search_warmup(duration=random.randint(40, 70))
        
        # 4. 搜索
        if self.smart_search("谷雨"):
            print("\n🎉 成功！未被风控")
            print("\n下一步可以:")
            print("1. 继续爬取笔记")
            print("2. 或者先关闭，过几个小时再来")
        else:
            print("\n😢 还是被风控了...")
            print("\n建议:")
            print("1. 手动在这个浏览器中随便浏览30分钟")
            print("2. 明天再来试试")
            print("3. 或者换个账号/IP")
        
        input("\n按回车关闭...")
        self.close()
    
    def close(self):
        """关闭"""
        if self.driver:
            self.driver.quit()


def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     小红书爬虫 - Undetected版 v3.0                       ║
    ║     最强反检测方案                                       ║
    ║                                                          ║
    ║     技术特点:                                            ║
    ║     🎭 Undetected-ChromeDriver                           ║
    ║     🤖 超拟人行为模拟                                    ║
    ║     🔐 保持登录状态                                      ║
    ║     ⏱️  智能预热机制                                     ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    print("\n📦 前置要求:")
    print("pip install undetected-chromedriver")
    print("\n⚠️  首次使用建议:")
    print("1. 先手动登录小红书并随便浏览30分钟")
    print("2. 第二天再运行此脚本")
    print("3. 效果会更好")
    
    input("\n按回车开始...")
    
    scraper = StealthXiaohongshuScraper()
    scraper.test_run()


if __name__ == "__main__":
    main()