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
        """使用远程调试模式连接Chrome - 最简化版本（兼容所有版本）"""
        try:
            self.logger.info("连接到远程调试 Chrome...")
            
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            
            # 只使用最基本的远程调试配置（兼容所有 ChromeDriver 版本）
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            
            # 创建驱动（不添加任何额外选项，避免兼容性问题）
            self.driver = webdriver.Chrome(options=options)
            
            # 设置超时
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            self.logger.info(f"✅ 连接成功: {self.driver.current_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 连接失败: {e}")
            self.logger.error("=" * 60)
            self.logger.error("请确保:")
            self.logger.error("1. 已经运行了 start_xiaohongshu_chrome.bat")
            self.logger.error("2. Chrome 调试模式正在运行（端口 9222）")
            self.logger.error("3. 没有其他程序占用 9222 端口")
            self.logger.error("4. 已删除旧的 ChromeDriver")
            self.logger.error("=" * 60)
            
            # 诊断
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 9222))
            sock.close()
            
            if result == 0:
                self.logger.error("🔍 诊断: 端口已开放但无法连接")
                self.logger.error("💡 最可能的原因: 系统中存在旧版本 ChromeDriver 干扰")
                self.logger.error("💡 解决方案:")
                self.logger.error("   以管理员身份运行 PowerShell:")
                self.logger.error("   Remove-Item 'C:\\Program Files\\Python310\\chromedriver.exe' -Force")
            else:
                self.logger.error("🔍 诊断: 端口未开放")
                self.logger.error("💡 解决: 运行 start_xiaohongshu_chrome.bat")
            
            return False

    
    # ====== 修改 4: 简化的 login 方法 ======
    def login(self, use_cookie=True):
        """登录小红书 - 简化版（假设已在浏览器中手动登录）"""
        self.logger.info("检查登录状态...")
        
        try:
            # 确保在小红书页面
            if "xiaohongshu.com" not in self.driver.current_url:
                self.driver.get("https://www.xiaohongshu.com")
                time.sleep(3)
            
            # 简单询问用户是否已登录
            self.logger.info("=" * 60)
            self.logger.info("请确认:")
            self.logger.info("1. 浏览器中是否已经登录小红书？")
            self.logger.info("2. 能看到个人头像吗？")
            self.logger.info("")
            self.logger.info("如果已登录，直接按 Enter 继续")
            self.logger.info("如果未登录，请先登录再按 Enter")
            self.logger.info("=" * 60)
            
            input()  # 等待用户确认
            
            self.logger.info("✅ 继续执行...")
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
    def scrape_post_comments(self, post_url):
        """爬取单个笔记的评论 - 增强版"""
        self.logger.info(f"访问笔记: {post_url}")
        
        try:
            # ===== 添加：随机决定是否访问 =====
            if random.random() < 0.3:  # 30% 概率跳过
                self.logger.info("随机跳过此笔记（模拟真实浏览）")
                return []
            
            # 访问笔记
            self.driver.get(post_url)
            
            # ===== 修改：增加初始等待 =====
            self.human_behavior.random_delay(5, 10)  # 从 (3, 5) 改为 (5, 10)
            
            # ===== 添加：模拟阅读笔记内容 =====
            self.logger.info("模拟阅读笔记内容...")
            time.sleep(random.randint(5, 15))  # 停留5-15秒
            
            # ===== 添加：随机滚动查看图片 =====
            if random.random() < 0.5:  # 50% 概率滚动
                self.logger.info("随机滚动查看...")
                self.human_behavior.human_like_scroll(scroll_times=random.randint(1, 3))
            
            # 检查验证码
            if self.captcha_handler.check_captcha():
                self.captcha_handler.handle_slider_captcha()
                self.captcha_handler.wait_for_captcha_disappear()
            
            # ===== 添加：随机决定是否查看评论 =====
            if random.random() < 0.7:  # 70% 概率查看评论
                # 滚动加载评论
                self.human_behavior.human_like_scroll(scroll_times=3)
                
                # 提取评论
                comments = self._extract_comments()
                
                # 过滤出包含目标品牌的评论
                target_brand = self.config.get('target_brand', '谷雨')
                filtered_comments = []
                
                for comment in comments:
                    content = comment.get('content', '')
                    if target_brand in content:
                        filtered_comments.append(comment)
                
                if filtered_comments:
                    self.logger.info(f"✅ 找到 {len(filtered_comments)} 条相关评论")
                else:
                    self.logger.info("未找到相关评论")
                
                return filtered_comments
            else:
                self.logger.info("随机选择不查看评论（模拟真实浏览）")
                return []
            
        except Exception as e:
            self.logger.error(f"爬取评论失败: {e}")
            return []


    def _extract_comments(self):
        """提取页面中的评论"""
        comments = []
        
        try:
            # 等待评论区加载
            time.sleep(2)
            
            # 尝试多个可能的选择器
            comment_selectors = [
                "//div[contains(@class, 'comment-item')]",
                "//div[contains(@class, 'note-comment')]",
                "//div[@class='comments-container']//div[contains(@class, 'item')]"
            ]
            
            comment_elements = []
            for selector in comment_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        comment_elements = elements
                        break
                except:
                    continue
            
            if not comment_elements:
                self.logger.warning("未找到评论元素")
                return comments
            
            for elem in comment_elements:
                try:
                    comment_data = {
                        'content': '',
                        'user_name': '',
                        'user_id': '',
                        'comment_time': '',
                        'like_count': 0,
                        'post_url': self.driver.current_url
                    }
                    
                    # 提取评论内容
                    try:
                        content_elem = elem.find_element(By.XPATH, ".//div[contains(@class, 'content')] | .//span[contains(@class, 'content')]")
                        comment_data['content'] = content_elem.text.strip()
                    except:
                        try:
                            comment_data['content'] = elem.text.strip()
                        except:
                            pass
                    
                    # 提取用户名
                    try:
                        user_elem = elem.find_element(By.XPATH, ".//a[contains(@class, 'user')] | .//span[contains(@class, 'user')]")
                        comment_data['user_name'] = user_elem.text.strip()
                        
                        # 尝试获取用户ID
                        user_link = user_elem.get_attribute('href')
                        if user_link and '/user/profile/' in user_link:
                            comment_data['user_id'] = user_link.split('/user/profile/')[-1].split('?')[0]
                    except:
                        pass
                    
                    # 提取点赞数
                    try:
                        like_elem = elem.find_element(By.XPATH, ".//span[contains(@class, 'like')] | .//span[contains(@class, 'count')]")
                        like_text = like_elem.text.strip()
                        comment_data['like_count'] = self._parse_count(like_text)
                    except:
                        pass
                    
                    # 提取时间
                    try:
                        time_elem = elem.find_element(By.XPATH, ".//span[contains(@class, 'time')] | .//span[contains(@class, 'date')]")
                        comment_data['comment_time'] = time_elem.text.strip()
                    except:
                        pass
                    
                    if comment_data['content']:
                        comments.append(comment_data)
                    
                except Exception as e:
                    self.logger.debug(f"解析单条评论失败: {e}")
                    continue
            
            self.logger.info(f"提取到 {len(comments)} 条评论")
            return comments
            
        except Exception as e:
            self.logger.error(f"提取评论失败: {e}")
            return comments


    def scrape_user_profile(self, user_id):
        """爬取用户主页信息"""
        self.logger.info(f"访问用户主页: {user_id}")
        
        try:
            # 访问用户主页
            user_url = f"https://www.xiaohongshu.com/user/profile/{user_id}"
            self.driver.get(user_url)
            self.human_behavior.random_delay(2, 4)
            
            # 检查验证码
            if self.captcha_handler.check_captcha():
                self.captcha_handler.handle_slider_captcha()
                self.captcha_handler.wait_for_captcha_disappear()
            
            user_data = {
                'user_id': user_id,
                'user_name': '',
                'follower_count': 0,
                'following_count': 0,
                'note_count': 0,
                'like_count': 0,
                'collect_count': 0,
                'created_at': '',
                'notes': []
            }
            
            # 提取用户信息
            try:
                # 用户名
                name_elem = self.driver.find_element(By.XPATH, "//div[contains(@class, 'user-name')] | //span[contains(@class, 'username')]")
                user_data['user_name'] = name_elem.text.strip()
            except:
                pass
            
            # 粉丝数
            try:
                follower_elem = self.driver.find_element(By.XPATH, "//div[contains(@class, 'follower')] | //span[contains(text(), '粉丝')]/..")
                user_data['follower_count'] = self._parse_count(follower_elem.text)
            except:
                pass
            
            # 关注数
            try:
                following_elem = self.driver.find_element(By.XPATH, "//div[contains(@class, 'following')] | //span[contains(text(), '关注')]/..")
                user_data['following_count'] = self._parse_count(following_elem.text)
            except:
                pass
            
            # 笔记数
            try:
                note_elem = self.driver.find_element(By.XPATH, "//div[contains(@class, 'note-count')] | //span[contains(text(), '笔记')]/..")
                user_data['note_count'] = self._parse_count(note_elem.text)
            except:
                pass
            
            # 获赞数
            try:
                like_elem = self.driver.find_element(By.XPATH, "//div[contains(@class, 'like-count')] | //span[contains(text(), '获赞')]/..")
                user_data['like_count'] = self._parse_count(like_elem.text)
            except:
                pass
            
            self.logger.info(f"✅ 用户信息: {user_data['user_name']}, 粉丝: {user_data['follower_count']}, 笔记: {user_data['note_count']}")
            
            return user_data
            
        except Exception as e:
            self.logger.error(f"爬取用户信息失败: {e}")
            return None


    def _parse_count(self, text):
        """解析数量文本（如 1.2万 -> 12000）"""
        if not text:
            return 0
        
        try:
            # 移除非数字字符（保留数字和小数点）
            import re
            text = text.strip()
            
            # 匹配数字和单位
            match = re.search(r'([\d.]+)\s*([万千百wWkK]?)', text)
            if not match:
                return 0
            
            number = float(match.group(1))
            unit = match.group(2).lower()
            
            # 转换单位
            multiplier = 1
            if unit in ['万', 'w']:
                multiplier = 10000
            elif unit in ['千', 'k']:
                multiplier = 1000
            elif unit in ['百']:
                multiplier = 100
            
            return int(number * multiplier)
            
        except:
            return 0
  



    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                # 远程调试模式：不关闭浏览器，只断开连接
                self.logger.info("断开与浏览器的连接（浏览器将继续运行）")
                self.driver.quit()
            except:
                pass