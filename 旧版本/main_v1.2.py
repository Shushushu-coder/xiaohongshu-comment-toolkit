"""
小红书爬虫 - 改进版（增强反检测）
核心改进：
1. 先访问首页，模拟真实用户
2. 增加随机浏览行为
3. 在搜索前进行预热
"""
import random
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import json


class ImprovedXiaohongshuScraper:
    """改进的小红书爬虫 - 强化反检测"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
    
    def connect_to_chrome(self):
        """连接到远程调试Chrome"""
        print("🔗 连接到Chrome调试端口...")
        
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        # 额外的反检测设置
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 20)
            
            # 注入反检测脚本
            self.inject_stealth_js()
            
            print("✅ 成功连接到Chrome")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def inject_stealth_js(self):
        """注入反检测JavaScript"""
        print("💉 注入反检测脚本...")
        
        stealth_js = """
        // 覆盖 navigator.webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // 覆盖 chrome 属性
        window.chrome = {
            runtime: {}
        };
        
        // 覆盖 permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Telegram.prototype.PermissionStatus.prototype.granted }) :
            originalQuery(parameters)
        );
        
        // 添加插件伪装
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // 添加语言伪装
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en']
        });
        """
        
        try:
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': stealth_js
            })
            print("✅ 反检测脚本已注入")
        except Exception as e:
            print(f"⚠️  脚本注入失败（但可能不影响）: {e}")
    
    def simulate_human_scroll(self, times=3):
        """模拟人类滚动行为"""
        for _ in range(times):
            # 随机滚动距离
            scroll_distance = random.randint(300, 800)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
            time.sleep(random.uniform(0.5, 1.5))
        
        # 随机上滚一点
        if random.random() > 0.5:
            self.driver.execute_script(f"window.scrollBy(0, -{random.randint(100, 300)});")
            time.sleep(random.uniform(0.3, 0.8))
    
    def simulate_mouse_movement(self):
        """模拟鼠标移动"""
        try:
            actions = ActionChains(self.driver)
            # 移动到随机位置
            x_offset = random.randint(-100, 100)
            y_offset = random.randint(-100, 100)
            actions.move_by_offset(x_offset, y_offset).perform()
            time.sleep(random.uniform(0.1, 0.3))
        except:
            pass
    
    def warm_up_homepage(self, duration=30):
        """首页预热 - 关键步骤！"""
        print("\n" + "="*60)
        print("🔥 第一步：首页预热（模拟真实用户）")
        print("="*60)
        
        try:
            # 确保在首页
            if "xiaohongshu.com" not in self.driver.current_url:
                print("📍 访问小红书首页...")
                self.driver.get("https://www.xiaohongshu.com")
                time.sleep(random.uniform(3, 5))
            
            print(f"⏱️  预热 {duration} 秒，模拟浏览行为...")
            
            start_time = time.time()
            actions_count = 0
            
            while time.time() - start_time < duration:
                # 随机选择一个动作
                action = random.choice([
                    'scroll',
                    'mouse_move', 
                    'wait',
                    'small_scroll'
                ])
                
                if action == 'scroll':
                    print(f"  [{actions_count+1}] 📜 随机滚动...")
                    self.simulate_human_scroll(random.randint(2, 4))
                    actions_count += 1
                
                elif action == 'mouse_move':
                    print(f"  [{actions_count+1}] 🖱️  移动鼠标...")
                    self.simulate_mouse_movement()
                    actions_count += 1
                
                elif action == 'small_scroll':
                    # 小幅度滚动
                    scroll = random.randint(50, 200)
                    self.driver.execute_script(f"window.scrollBy(0, {scroll});")
                    time.sleep(random.uniform(0.2, 0.5))
                
                else:  # wait
                    # 静止观察
                    wait_time = random.uniform(2, 5)
                    print(f"  [{actions_count+1}] 👀 停留 {wait_time:.1f} 秒...")
                    time.sleep(wait_time)
                    actions_count += 1
                
                # 小延迟
                time.sleep(random.uniform(0.5, 2))
            
            print(f"✅ 预热完成！共执行 {actions_count} 个模拟动作")
            print(f"⏸️  等待 5 秒让页面稳定...")
            time.sleep(5)
            
        except Exception as e:
            print(f"⚠️  预热过程出现问题（继续运行）: {e}")
    
    def search_with_preparation(self, keyword="谷雨"):
        """带准备的搜索 - 模拟真实用户"""
        print("\n" + "="*60)
        print(f"🔍 第二步：搜索 '{keyword}'")
        print("="*60)
        
        try:
            # 1. 先缓慢移动到搜索框
            print("1️⃣ 定位搜索框...")
            search_selectors = [
                "input[placeholder*='搜索']",
                "input[type='search']",
                ".search-input",
                "#search-input"
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if search_box:
                        break
                except:
                    continue
            
            if not search_box:
                print("❌ 找不到搜索框")
                return False
            
            # 2. 移动鼠标到搜索框（模拟真实操作）
            print("2️⃣ 移动鼠标到搜索框...")
            actions = ActionChains(self.driver)
            actions.move_to_element(search_box).perform()
            time.sleep(random.uniform(0.5, 1))
            
            # 3. 点击搜索框
            print("3️⃣ 点击搜索框...")
            search_box.click()
            time.sleep(random.uniform(0.3, 0.8))
            
            # 4. 逐字输入（模拟打字）
            print(f"4️⃣ 输入关键词: {keyword}")
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))  # 打字间隔
            
            # 5. 停顿（模拟思考）
            think_time = random.uniform(0.5, 1.5)
            print(f"5️⃣ 停顿 {think_time:.1f} 秒（模拟思考）...")
            time.sleep(think_time)
            
            # 6. 按回车或点击搜索按钮
            print("6️⃣ 执行搜索...")
            from selenium.webdriver.common.keys import Keys
            search_box.send_keys(Keys.RETURN)
            
            # 7. 等待搜索结果加载
            wait_time = random.uniform(3, 6)
            print(f"7️⃣ 等待搜索结果 {wait_time:.1f} 秒...")
            time.sleep(wait_time)
            
            # 8. 检查是否被风控
            page_text = self.driver.page_source.lower()
            if any(keyword in page_text for keyword in [
                '无法访问', '扫描', '验证', '异常', '频繁'
            ]):
                print("❌ 检测到风控提示！")
                print("\n当前页面状态：")
                print(f"URL: {self.driver.current_url}")
                # 截图
                self.driver.save_screenshot("error_screenshot.png")
                print("📸 已保存截图: error_screenshot.png")
                return False
            
            print("✅ 搜索成功！")
            return True
            
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return False
    
    def run_safe_scraping(self):
        """安全的爬取流程"""
        print("\n" + "="*60)
        print("🚀 开始安全爬取流程")
        print("="*60)
        
        # 步骤0: 连接Chrome
        if not self.connect_to_chrome():
            return
        
        # 步骤1: 首页预热（30-60秒）
        warm_up_time = random.randint(30, 60)
        self.warm_up_homepage(duration=warm_up_time)
        
        # 步骤2: 搜索
        if not self.search_with_preparation("谷雨"):
            print("\n⚠️  搜索失败，建议：")
            print("1. 手动在Chrome中完成一次搜索")
            print("2. 等待10-30分钟")
            print("3. 重新运行脚本")
            return
        
        # 步骤3: 浏览搜索结果
        print("\n3️⃣ 浏览搜索结果...")
        self.simulate_human_scroll(random.randint(3, 6))
        time.sleep(random.uniform(3, 6))
        
        print("\n✅ 安全爬取流程完成！")
        print("\n💡 下一步：")
        print("- 如果没有被风控，可以继续爬取笔记")
        print("- 如果还是被风控，说明需要更长的账号养护期")
        
    def close(self):
        """关闭（但不关闭Chrome）"""
        print("\n⚠️  保持Chrome打开，只断开连接...")
        if self.driver:
            self.driver.quit()


def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     小红书爬虫 - 改进版 v2.0                             ║
    ║     Enhanced Anti-Detection Mode                         ║
    ║                                                          ║
    ║     核心改进:                                            ║
    ║     ✅ 首页预热 - 模拟真实用户                          ║
    ║     ✅ 渐进式搜索 - 逐字输入                            ║
    ║     ✅ 随机行为 - 滚动、停顿、鼠标移动                  ║
    ║     ✅ 反检测JS - 伪装浏览器特征                        ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    print("\n⚠️  使用前确认：")
    print("1. 已运行 start_xiaohongshu_chrome.bat")
    print("2. Chrome已打开并已登录小红书")
    print("3. 如果之前被风控，已等待至少2小时")
    input("\n按回车键继续...")
    
    scraper = ImprovedXiaohongshuScraper()
    scraper.run_safe_scraping()
    
    input("\n按回车键关闭...")
    scraper.close()


if __name__ == "__main__":
    main()