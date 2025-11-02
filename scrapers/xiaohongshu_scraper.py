"""
小红书爬虫核心类 - 远程调试模式版本
"""
# ====== 修改 1: 更新导入语句 ======
# 注释掉 undetected_chromedriver（不再需要）
# import undetected_chromedriver as uc

# 添加 Selenium 远程调试需要的导入
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
import json
from pathlib import Path
from datetime import datetime
import re


class XiaohongshuScraper:
    """小红书爬虫"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.driver = None
        self.human_behavior = None
        self.captcha_handler = None
        self.cookie_manager = None
        self.data_collected = []
    
    # ====== 修改 2: 新的 initialize 方法 ======
    def initialize(self):
        """初始化浏览器和工具类"""
        self.logger.info("初始化系统...")
        
        # 初始化浏览器（远程调试模式）
        if not self._init_driver():
            return False
        
        # 初始化工具类
        try:
            from utils.human_behavior import HumanBehavior
            from utils.captcha_handler import CaptchaHandler, CookieManager
            
            self.human_behavior = HumanBehavior(self.driver, self.config)
            self.captcha_handler = CaptchaHandler(self.driver, self.logger)
            self.cookie_manager = CookieManager(self.driver, self.logger)
            
            self.logger.info("✅ 系统初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"工具类初始化失败: {e}")
            return False
    
    # ====== 修改 3: 远程调试模式的 _init_driver 方法 ======
    def _init_driver(self):
        """使用远程调试模式连接Chrome"""
        try:
            self.logger.info("连接到远程调试 Chrome...")
            
            # 配置选项
            options = Options()
            
            # ⭐ 关键：连接到远程调试端口
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            
            # 反检测配置
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # 创建 driver
            self.driver = webdriver.Chrome(options=options)
            
            # 设置超时
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            # 执行反检测脚本
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en']
                    });
                '''
            })
            
            self.logger.info(f"✅ 成功连接! 当前URL: {self.driver.current_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 连接失败: {e}")
            self.logger.error("=" * 60)
            self.logger.error("请确保:")
            self.logger.error("1. 已经运行了 start_xiaohongshu_chrome.bat")
            self.logger.error("2. Chrome 调试模式正在运行（端口 9222）")
            self.logger.error("3. 没有其他程序占用 9222 端口")
            self.logger.error("=" * 60)
            
            # 提供诊断信息
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 9222))
            sock.close()
            
            if result != 0:
                self.logger.error("🔍 诊断: 端口 9222 未开放")
                self.logger.error("💡 解决: 双击运行 start_xiaohongshu_chrome.bat")
            else:
                self.logger.error("🔍 诊断: 端口已开放但无法连接")
                self.logger.error("💡 解决: 重启 Chrome 调试模式")
            
            return False
    
    # ====== 修改 4: 简化的 login 方法 ======
    def login(self, use_cookie=True):
        """登录小红书（远程调试模式简化版）"""
        self.logger.info("检查登录状态...")
        
        try:
            # 确保在小红书页面
            if "xiaohongshu.com" not in self.driver.current_url:
                self.driver.get("https://www.xiaohongshu.com")
                time.sleep(3)
            
            # 尝试使用 cookie 登录
            if use_cookie:
                accounts = self.config.get('accounts', [])
                if accounts and accounts[0].get('cookie_file'):
                    cookie_file = accounts[0]['cookie_file']
                    if Path(cookie_file).exists():
                        self.cookie_manager.load_cookies(cookie_file)
                        self.driver.refresh()
                        time.sleep(3)
                        
                        if self.cookie_manager.check_login_status():
                            self.logger.info("✅ Cookie登录成功")
                            return True
                        else:
                            self.logger.warning("Cookie已失效")
            
            # 检查是否已经登录（因为远程调试模式可能已经手动登录）
            try:
                # 尝试找到登录标识（用户头像等）
                self.driver.find_element(By.CSS_SELECTOR, "div.user-avatar, a.avatar")
                self.logger.info("✅ 检测到已登录状态")
                
                # 保存 cookie
                if self.config.get('accounts') and self.config['accounts'][0].get('cookie_file'):
                    self.cookie_manager.save_cookies(self.config['accounts'][0]['cookie_file'])
                
                return True
            except:
                pass
            
            # 需要手动登录
            self.logger.info("=" * 60)
            self.logger.info("⚠️  未检测到登录状态")
            self.logger.info("请在浏览器中手动登录小红书（扫码或短信）")
            self.logger.info("登录完成后，回到终端按 Enter 继续...")
            self.logger.info("=" * 60)
            
            input()  # 等待用户登录
            
            # 保存登录后的cookie
            if self.config.get('accounts') and self.config['accounts'][0].get('cookie_file'):
                self.cookie_manager.save_cookies(self.config['accounts'][0]['cookie_file'])
                self.logger.info("✅ 已保存登录状态")
            
            return True
            
        except Exception as e:
            self.logger.error(f"登录检查失败: {e}")
            return False
    
    def search_brand(self, keyword):
        """搜索品牌相关内容"""
        self.logger.info(f"搜索关键词: {keyword}")
        
        try:
            # 访问搜索页
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_notes"
            self.driver.get(search_url)
            self.human_behavior.random_delay(3, 5)
            
            # 检查验证码
            if self.captcha_handler.check_captcha():
                self.captcha_handler.handle_slider_captcha()
                self.captcha_handler.wait_for_captcha_disappear()
            
            # 模拟人类浏览
            self.human_behavior.human_like_scroll(scroll_times=3)
            
            return True
            
        except Exception as e:
            self.logger.error(f"搜索失败: {e}")
            return False
    
    def get_post_links(self, max_posts=50):
        """获取笔记链接"""
        self.logger.info(f"开始收集笔记链接（目标: {max_posts}条）...")
        
        post_links = set()
        scroll_attempts = 0
        max_scroll_attempts = 20
        
        while len(post_links) < max_posts and scroll_attempts < max_scroll_attempts:
            try:
                # 查找所有笔记卡片
                selectors = [
                    "//a[contains(@href, '/explore/')]",
                    "//section[@id='noteContainer']//a",
                    "//div[contains(@class, 'note-item')]//a"
                ]
                
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for elem in elements:
                            href = elem.get_attribute('href')
                            if href and '/explore/' in href:
                                post_links.add(href)
                    except:
                        continue
                
                self.logger.info(f"已收集 {len(post_links)} 条笔记链接")
                
                # 滚动加载更多
                self.human_behavior.scroll_to_load_more(max_scrolls=1)
                scroll_attempts += 1
                
                # 随机暂停
                if random.random() < 0.2:
                    self.human_behavior.random_pause()
                
            except Exception as e:
                self.logger.error(f"收集链接出错: {e}")
                scroll_attempts += 1
                time.sleep(2)
        
        self.logger.info(f"✅ 共收集到 {len(post_links)} 条笔记链接")
        return list(post_links)[:max_posts]
    
    # ====== 其他方法保持不变 ======
    # 你的原代码中的其他方法（get_comments, get_user_info等）保持不变
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                # 远程调试模式：不关闭浏览器，只断开连接
                self.logger.info("断开与浏览器的连接（浏览器将继续运行）")
                self.driver.quit()
            except:
                pass