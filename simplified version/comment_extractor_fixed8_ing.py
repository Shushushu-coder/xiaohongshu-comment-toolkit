"""
小红书评论提取器 - V5 强化版本
彻底解决用户名提取问题

核心策略改变：
1. 放弃CSS选择器,改用XPath精确定位
2. 使用HTML结构层级关系判断用户名位置
3. 增强调试输出，显示HTML结构
4. 采用"排除法"：排除content区域的用户名

新增功能：
5. 爬取历史存储，避免重复爬取相同链接
"""
import time
import random
import json
import csv
import re
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains


class CommentExtractorV6:
    """V6简化版 - 彻底解决用户名提取 + 简化CSV输出 + 爬取历史记录"""
    
    def __init__(self, debug=False):
        self.driver = None
        self.wait = None
        self.data_dir = Path("data/comments")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.debug = debug  # 调试模式
        
        # 新增：爬取历史记录文件
        self.history_file = Path("data/crawl_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.crawl_history = self.load_history()
    
    def load_history(self):
        """加载爬取历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.log(f"加载历史记录失败: {e}", "⚠️")
                return {}
        return {}
    
    def save_history(self):
        """保存爬取历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.crawl_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存历史记录失败: {e}", "⚠️")
    
    def is_url_crawled(self, url):
        """检查URL是否已经爬取过"""
        return url in self.crawl_history
    
    def add_to_history(self, url, note_id, comment_count):
        """将URL添加到历史记录"""
        self.crawl_history[url] = {
            'note_id': note_id,
            'crawled_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'comment_count': comment_count
        }
        self.save_history()
    
    def get_history_info(self, url):
        """获取URL的历史爬取信息"""
        return self.crawl_history.get(url, None)
    
    def log(self, message, symbol="ℹ️"):
        """日志输出"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {symbol} {message}")
    
    def debug_log(self, message):
        """调试日志"""
        if self.debug:
            print(f"[DEBUG] {message}")
    
    def connect_to_chrome(self):
        """连接到已打开的Chrome"""
        self.log("连接到Chrome调试端口...", "🔗")
        
        try:
            options = webdriver.ChromeOptions()
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)
            
            self.log("连接成功！", "✅")
            return True
            
        except Exception as e:
            self.log(f"连接失败: {e}", "❌")
            self.log("请确保已运行 start_xiaohongshu_chrome.bat", "💡")
            return False
    
    def extract_note_id(self, url):
        """从URL中提取笔记ID"""
        try:
            match = re.search(r'/explore/([a-zA-Z0-9]+)', url)
            if match:
                return match.group(1)
            return None
        except:
            return None
    
    def get_note_info(self):
        """获取笔记基本信息 - V6.3增强版"""
        info = {
            'note_id': None,
            'note_title': '未知标题',
            'note_url': self.driver.current_url,
            'author': '未知作者',
            'publish_time': '',
            'likes': 0,
            'collects': 0
        }
        
        try:
            # 提取笔记ID
            info['note_id'] = self.extract_note_id(info['note_url'])
            
            # 额外等待，确保页面完全加载
            self.log("等待页面JavaScript渲染完成...", "⏳")
            time.sleep(3)
            
            # 等待页面加载完成
            try:
                self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            except:
                pass
            
            # 先从页面title提取（最可靠的备选方案）
            page_title = self.driver.title
            self.debug_log(f"页面标题: {page_title}")
            
            # 策略1: 从页面标题提取（备选方案，先保存）
            temp_title_from_page = None
            temp_author_from_page = None
            
            # 页面标题格式通常是: "笔记标题 - 小红书"
            if ' - ' in page_title and page_title.endswith('小红书'):
                # 去掉末尾的" - 小红书"
                temp_title_from_page = page_title.rsplit(' - 小红书', 1)[0].strip()
                self.debug_log(f"从页面标题提取笔记标题: {temp_title_from_page[:50]}")
            elif ' - ' in page_title:
                parts = page_title.split(' - ')
                # 第一部分是标题
                if len(parts) >= 1:
                    temp_title_from_page = parts[0].strip()
                    self.debug_log(f"从页面标题提取笔记标题: {temp_title_from_page[:50]}")
                
                # 如果有第二部分且不是"小红书"，可能是作者（但通常不准确）
                if len(parts) >= 2 and parts[1].strip() != '小红书':
                    temp_author_from_page = parts[1].strip()
                    self.debug_log(f"从页面标题提取可能的作者: {temp_author_from_page}")
            
            # 策略2: 从页面源码中查找JSON（最可靠的作者来源）
            try:
                page_source = self.driver.page_source
                
                # 尝试从页面源码中提取标题
                title_patterns = [
                    r'"noteTitle":"([^"]+)"',
                    r'"title":"([^"]+)"',
                    r'data-title="([^"]+)"',
                    r'"note":\s*{[^}]*"title":"([^"]+)"',
                ]
                
                for pattern in title_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        title = match.group(1).strip()
                        if title and len(title) > 2 and '小红书' not in title:
                            info['note_title'] = title
                            self.debug_log(f"从页面源码JSON提取标题: {title[:50]}")
                            break
                
                # 如果JSON中没找到标题，使用页面title提取的
                if info['note_title'] == '未知标题' and temp_title_from_page:
                    info['note_title'] = temp_title_from_page
                    self.debug_log(f"使用页面标题作为笔记标题")
                
                # 尝试从页面源码中提取作者（更精确的模式）
                # 小红书的JSON结构中，笔记作者通常在 note.user.nickname 或 note.author.nickname
                author_patterns = [
                    # 优先匹配note对象中的user.nickname（这是笔记作者）
                    r'"note":\s*{[^}]*"user":\s*{[^}]*"nickname":"([^"]+)"',
                    r'"noteData":\s*{[^}]*"user":\s*{[^}]*"nickname":"([^"]+)"',
                    # 匹配note对象中的author.nickname
                    r'"note":\s*{[^}]*"author":\s*{[^}]*"nickname":"([^"]+)"',
                    # 通用的nickname（可能匹配到当前登录用户）
                    r'"nickname":"([^"]+)"',
                ]
                
                found_authors = []
                for pattern in author_patterns:
                    matches = re.findall(pattern, page_source)
                    if matches:
                        for match in matches:
                            author = match.strip()
                            if author and len(author) > 0 and author not in found_authors:
                                found_authors.append(author)
                                self.debug_log(f"找到可能的作者: {author}")
                
                # 使用找到的作者（优先使用第二个，因为第一个通常是当前登录用户）
                if found_authors:
                    # 如果找到多个作者，优先使用第二个（通常是笔记作者）
                    # 第一个nickname通常是当前登录用户
                    if len(found_authors) >= 2:
                        info['author'] = found_authors[1]
                        self.debug_log(f"使用第二个找到的作者（笔记作者）: {found_authors[1]}")
                        self.debug_log(f"第一个作者（可能是登录用户）: {found_authors[0]}")
                    elif len(found_authors) == 1:
                        # 只有一个作者时使用它
                        info['author'] = found_authors[0]
                        self.debug_log(f"只找到一个作者: {found_authors[0]}")
                    
                    # 如果找到多于2个，显示其他可能的作者
                    if len(found_authors) > 2:
                        self.debug_log(f"其他可能的作者: {', '.join(found_authors[2:])}")
                
            except Exception as e:
                self.debug_log(f"从页面源码提取失败: {e}")
            
            # 策略3: 尝试CSS选择器提取标题
            if info['note_title'] == '未知标题':
                title_selectors = [
                    "#detail-title",
                    "h1[class*='title']",
                    "div[class*='note-title']",
                    "span[class*='title']",
                    ".title",
                    "h1",
                ]
                
                for selector in title_selectors:
                    try:
                        elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        title = elem.text.strip()
                        if title and len(title) > 2 and len(title) < 200:
                            info['note_title'] = title
                            self.debug_log(f"通过CSS选择器找到标题({selector}): {title[:50]}")
                            break
                    except:
                        continue
            
            # 策略4: 尝试CSS选择器提取作者
            if info['author'] == '未知作者':
                author_selectors = [
                    "a.author-name",
                    ".author-name",
                    "a[class*='author']",
                    "div[class*='user-name']",
                    "span[class*='user-name']",
                ]
                
                for selector in author_selectors:
                    try:
                        elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        author = elem.text.strip()
                        if author and len(author) > 0 and len(author) < 50:
                            info['author'] = author
                            self.debug_log(f"通过CSS选择器找到作者({selector}): {author}")
                            break
                    except:
                        continue
            
            self.log(f"笔记信息提取完成", "📝")
            self.log(f"  ├─ ID: {info['note_id'] or '未知'}", "")
            self.log(f"  ├─ 标题: {info['note_title'][:30]}...", "")
            self.log(f"  └─ 作者: {info['author']}", "")
            
        except Exception as e:
            self.log(f"获取笔记信息失败: {e}", "⚠️")
        
        return info
    
    def smart_scroll_to_comments(self):
        """智能定位并滚动到评论区"""
        self.log("正在定位评论区...", "🔍")
        
        try:
            comment_selectors = [
                "#noteContainer",
                "div[class*='comment']",
                ".comment-container",
                "[id*='comment']",
            ]
            
            for selector in comment_selectors:
                try:
                    comment_section = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    self.driver.execute_script("""
                        arguments[0].scrollIntoView({
                            behavior: 'smooth',
                            block: 'center'
                        });
                    """, comment_section)
                    
                    time.sleep(2)
                    self.log("已定位到评论区", "✅")
                    return True
                    
                except NoSuchElementException:
                    continue
            
            self.log("未找到评论区元素，尝试向下滚动...", "⚠️")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(2)
            
        except Exception as e:
            self.log(f"滚动到评论区失败: {e}", "⚠️")
    
    def load_all_comments_with_expansion(self, max_scrolls=20):
        """加载所有评论（包括展开'查看全部'）- 简化版"""
        self.log(f"开始加载评论（最多滚动{max_scrolls}次）...", "📜")
        
        scroll_count = 0
        no_change_count = 0
        last_comment_count = 0
        
        while scroll_count < max_scrolls:
            try:
                # 1. 查找并点击所有"查看全部 X 条回复"按钮
                try:
                    expand_buttons = self.driver.find_elements(
                        By.XPATH, 
                        "//span[contains(text(), '查看全部') and contains(text(), '回复')]"
                    )
                    
                    if expand_buttons:
                        for btn in expand_buttons[:3]:  # 每次只点击前3个
                            try:
                                self.driver.execute_script("arguments[0].click();", btn)
                                time.sleep(random.uniform(0.5, 1))
                            except:
                                pass
                        self.debug_log(f"点击了 {min(len(expand_buttons), 3)} 个展开按钮")
                except:
                    pass
                
                # 2. 滚动页面
                self.driver.execute_script("""
                    window.scrollBy({
                        top: 800,
                        behavior: 'smooth'
                    });
                """)
                
                scroll_count += 1
                time.sleep(random.uniform(1.5, 2.5))
                
                # 3. 检查是否有新评论加载
                try:
                    all_comments = self.driver.find_elements(By.CSS_SELECTOR, "[class*='comment']")
                    current_count = len(all_comments)
                    
                    if current_count == last_comment_count:
                        no_change_count += 1
                        if no_change_count >= 3:
                            self.log(f"评论加载完成（连续{no_change_count}次无变化）", "✅")
                            break
                    else:
                        no_change_count = 0
                        self.log(f"  ├─ 第{scroll_count}次滚动：发现 {current_count} 个评论元素", "")
                    
                    last_comment_count = current_count
                    
                except:
                    pass
                
                # 4. 检查是否到达页面底部
                at_bottom = self.driver.execute_script("""
                    return (window.innerHeight + window.pageYOffset) >= document.body.scrollHeight - 100;
                """)
                
                if at_bottom and scroll_count > 5:
                    self.log("已到达页面底部", "✅")
                    break
                    
            except Exception as e:
                self.debug_log(f"滚动异常: {e}")
                break
        
        self.log(f"评论加载完成（共滚动{scroll_count}次）", "✅")
    
    def extract_comments_v6(self):
        """V6 简化版评论提取 - 继承V5的用户名提取逻辑"""
        self.log("开始提取评论（V6方法）...", "🔄")
        
        try:
            time.sleep(2)
            
            # 使用XPath查找所有评论项（小红书的评论通常在特定div中）
            comment_items = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'comment-item') or contains(@class, 'note-item')]"
            )
            
            if not comment_items:
                # 备选方案：查找所有可能的评论容器
                comment_items = self.driver.find_elements(
                    By.XPATH,
                    "//div[.//span[contains(text(), '点赞')] or .//span[contains(@class, 'like')]]"
                )
            
            self.log(f"找到 {len(comment_items)} 个评论容器", "📊")
            
            if not comment_items:
                self.log("未找到任何评论", "⚠️")
                return []
            
            comments = []
            processed_ids = set()
            
            for idx, item in enumerate(comment_items, 1):
                try:
                    comment_data = self._extract_single_comment_v6(item, idx)
                    
                    if comment_data and comment_data['comment_id'] not in processed_ids:
                        comments.append(comment_data)
                        processed_ids.add(comment_data['comment_id'])
                        
                        # 实时显示进度
                        if len(comments) % 10 == 0:
                            self.log(f"  ├─ 已提取 {len(comments)} 条评论...", "")
                    
                except Exception as e:
                    self.debug_log(f"提取第 {idx} 条评论失败: {e}")
                    continue
            
            self.log(f"评论提取完成！共 {len(comments)} 条有效评论", "✅")
            return comments
            
        except Exception as e:
            self.log(f"评论提取失败: {e}", "❌")
            return []
    
    def _extract_single_comment_v6(self, item, idx):
        """提取单条评论 - V6简化版（继承V5用户名提取逻辑）"""
        try:
            # 获取评论的HTML结构用于调试
            item_html = item.get_attribute('outerHTML')[:500]
            self.debug_log(f"\n{'='*60}")
            self.debug_log(f"处理第 {idx} 条评论")
            self.debug_log(f"HTML片段: {item_html}")
            
            # ==================== 用户名提取 ====================
            # V5核心策略：使用XPath层级结构 + 排除法
            username = None
            
            # 策略1: 查找头像旁边的用户名（最可靠）
            try:
                # 查找头像元素
                avatar = item.find_element(By.XPATH, ".//img[contains(@class, 'avatar') or contains(@src, 'avatar')]")
                
                # 从头像的父级或同级查找用户名
                username_candidates = [
                    # 头像的下一个兄弟元素中的文本
                    ".//img[contains(@class, 'avatar')]/following-sibling::*//span[not(contains(text(), '点赞')) and not(contains(text(), '回复'))]",
                    # 头像父元素的兄弟元素
                    ".//img[contains(@class, 'avatar')]/../following-sibling::*//span[1]",
                    # 头像所在div的父级的子元素
                    ".//img[contains(@class, 'avatar')]/../..//span[not(ancestor::*[contains(@class, 'content')])]",
                ]
                
                for xpath in username_candidates:
                    try:
                        name_elem = item.find_element(By.XPATH, xpath)
                        name = name_elem.text.strip()
                        if name and len(name) > 0 and len(name) < 30:
                            # 排除一些明显不是用户名的文本
                            exclude_keywords = ['点赞', '回复', '删除', '举报', '查看', '条回复', '刚刚', '分钟前', '小时前', '天前']
                            if not any(keyword in name for keyword in exclude_keywords):
                                username = name
                                self.debug_log(f"✓ 通过头像定位找到用户名: {username}")
                                break
                    except:
                        continue
            except:
                self.debug_log("未找到头像元素")
            
            # 策略2: 使用XPath排除content区域（V5核心策略）
            if not username:
                try:
                    # 查找所有span，但排除content类内的span
                    name_spans = item.find_elements(
                        By.XPATH,
                        ".//span[not(ancestor::*[contains(@class, 'content')]) and not(contains(@class, 'content'))]"
                    )
                    
                    for span in name_spans[:5]:  # 只检查前5个
                        text = span.text.strip()
                        if text and len(text) > 0 and len(text) < 30:
                            # 排除明显不是用户名的
                            exclude_keywords = ['点赞', '回复', '删除', '举报', '查看', '条回复', '刚刚', '分钟前', '小时前', '天前', '：']
                            if not any(keyword in text for keyword in exclude_keywords):
                                username = text
                                self.debug_log(f"✓ 通过排除法找到用户名: {username}")
                                break
                except Exception as e:
                    self.debug_log(f"排除法失败: {e}")
            
            # 策略3: 查找class包含'name'或'user'的元素
            if not username:
                try:
                    name_selectors = [
                        ".//span[contains(@class, 'name')]",
                        ".//div[contains(@class, 'user')]//span",
                        ".//a[contains(@class, 'name')]",
                    ]
                    
                    for selector in name_selectors:
                        try:
                            name_elem = item.find_element(By.XPATH, selector)
                            name = name_elem.text.strip()
                            if name and len(name) > 0 and len(name) < 30:
                                username = name
                                self.debug_log(f"✓ 通过class查找找到用户名: {username}")
                                break
                        except:
                            continue
                except:
                    pass
            
            # 策略4: 最后的备选方案 - 找第一个短文本span
            if not username:
                try:
                    all_spans = item.find_elements(By.TAG_NAME, "span")
                    for span in all_spans[:10]:
                        text = span.text.strip()
                        if text and 1 <= len(text) <= 20:
                            exclude_keywords = ['点赞', '回复', '删除', '举报', '查看', '条回复', '刚刚', '分钟前', '小时前', '天前']
                            if not any(keyword in text for keyword in exclude_keywords):
                                username = text
                                self.debug_log(f"✓ 通过备选方案找到用户名: {username}")
                                break
                except:
                    pass
            
            if not username:
                username = f"用户_{idx}"
                self.debug_log(f"⚠ 未能提取用户名，使用默认: {username}")
            
            # ==================== 评论内容提取 ====================
            content = None
            try:
                # 查找包含content类的元素
                content_elem = item.find_element(By.XPATH, ".//*[contains(@class, 'content')]")
                content = content_elem.text.strip()
                
                # 清理内容：移除"查看全部回复"等文本
                if content:
                    content = re.sub(r'查看全部\s*\d+\s*条回复', '', content)
                    content = re.sub(r'点赞\s*\d*', '', content)
                    content = content.strip()
                
                self.debug_log(f"✓ 内容: {content[:50]}...")
            except:
                self.debug_log("未找到content元素")
            
            if not content:
                # 备选：获取item中所有文本，排除用户名
                content = item.text.strip()
                if username and username in content:
                    content = content.replace(username, '', 1).strip()
            
            # ==================== 时间提取 ====================
            comment_time = ""
            try:
                time_patterns = [
                    ".//span[contains(text(), '分钟前')]",
                    ".//span[contains(text(), '小时前')]",
                    ".//span[contains(text(), '天前')]",
                    ".//span[contains(text(), '刚刚')]",
                    ".//span[contains(@class, 'time')]",
                ]
                
                for pattern in time_patterns:
                    try:
                        time_elem = item.find_element(By.XPATH, pattern)
                        comment_time = time_elem.text.strip()
                        if comment_time:
                            break
                    except:
                        continue
            except:
                pass
            
            # ==================== 点赞数提取 ====================
            likes = 0
            try:
                like_elem = item.find_element(By.XPATH, ".//span[contains(text(), '点赞')]")
                like_text = like_elem.text.strip()
                
                # 提取数字
                match = re.search(r'(\d+)', like_text)
                if match:
                    likes = int(match.group(1))
            except:
                pass
            
            # ==================== 生成评论ID ====================
            comment_id = f"{idx}_{hash(f'{username}_{content}') % 100000}"
            
            comment_data = {
                'comment_id': comment_id,
                'username': username,
                'content': content or "",
                'time': comment_time,
                'likes': likes,
                'content_length': len(content) if content else 0
            }
            
            self.debug_log(f"✓ 成功提取: {username} - {content[:30]}...")
            return comment_data
            
        except Exception as e:
            self.debug_log(f"提取单条评论失败: {e}")
            return None
    
    def save_comments(self, comments, note_info):
        """保存评论 - V6简化CSV版"""
        if not comments:
            return None, None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            note_id = note_info.get('note_id', 'unknown')
            
            # JSON文件（保留完整信息）
            json_filename = f"comments_{note_id}_{timestamp}_v6.json"
            json_file = self.data_dir / json_filename
            
            json_data = {
                'note_info': note_info,
                'comments': comments,
                'total_comments': len(comments),
                'collected_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            self.log(f"JSON文件已保存: {json_filename}", "💾")
            
            # CSV文件（简化版 - 只包含核心字段）
            csv_filename = f"comments_{note_id}_{timestamp}_v6.csv"
            csv_file = self.data_dir / csv_filename
            
            # V6: 简化的CSV字段
            csv_fields = ['comment_id', 'username', 'content', 'time', 'likes', 'content_length']
            
            with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_fields)
                writer.writeheader()
                
                for comment in comments:
                    # 只写入简化字段
                    row = {field: comment.get(field, '') for field in csv_fields}
                    writer.writerow(row)
            
            self.log(f"CSV文件已保存: {csv_filename}", "💾")
            
            # 生成统计摘要
            self.save_summary(comments, note_info, timestamp)
            
            return json_file, csv_file
            
        except Exception as e:
            self.log(f"保存评论失败: {e}", "❌")
            return None, None
    
    def save_summary(self, comments, note_info, timestamp):
        """保存统计摘要"""
        try:
            note_id = note_info.get('note_id', 'unknown')
            summary_file = self.data_dir / f"summary_{note_id}_{timestamp}_v6.txt"
            
            # 计算统计信息
            total_likes = sum(c.get('likes', 0) for c in comments)
            avg_length = sum(c.get('content_length', 0) for c in comments) / len(comments) if comments else 0
            
            # 按点赞数排序获取热门评论
            top_comments = sorted(comments, key=lambda x: x.get('likes', 0), reverse=True)[:5]
            
            summary_content = f"""
╔═══════════════════════════════════════════════════════════╗
║              小红书评论提取统计报告 (V6)                    ║
╚═══════════════════════════════════════════════════════════╝

【笔记信息】
笔记ID:     {note_info.get('note_id', '未知')}
笔记标题:   {note_info.get('note_title', '未知')}
笔记作者:   {note_info.get('author', '未知')}
笔记链接:   {note_info.get('note_url', '未知')}

【统计概览】
提取时间:   {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
评论总数:   {len(comments)} 条
总点赞数:   {total_likes}
平均长度:   {avg_length:.1f} 字

【热门评论 TOP 5】
"""
            
            for i, comment in enumerate(top_comments, 1):
                summary_content += f"""
{i}. {comment.get('username', '未知用户')} ({comment.get('likes', 0)} 赞)
   {comment.get('content', '')[:100]}...
"""
            
            summary_content += """
═══════════════════════════════════════════════════════════
"""
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            
            print(summary_content)
            
        except Exception as e:
            self.log(f"保存摘要失败: {e}", "⚠️")
    
    def process_current_page(self, max_scrolls=20):
        """处理当前页面"""
        self.log("="*60, "")
        self.log("开始处理当前页面（V6简化版）", "🚀")
        self.log("="*60, "")
        
        note_info = self.get_note_info()
        current_url = self.driver.current_url
        
        # 检查是否已爬取过
        if self.is_url_crawled(current_url):
            history_info = self.get_history_info(current_url)
            self.log("⚠️  该URL已在爬取历史中！", "🔍")
            self.log(f"  ├─ 上次爬取时间: {history_info['crawled_at']}", "")
            self.log(f"  ├─ 评论数量: {history_info['comment_count']} 条", "")
            self.log(f"  └─ 笔记ID: {history_info['note_id']}", "")
            
            choice = input("\n是否重新爬取？(y/n，默认n): ").strip().lower()
            if choice != 'y':
                self.log("已跳过该URL", "⏭️")
                return []
        
        self.log("等待页面加载完成...", "⏱️")
        time.sleep(random.uniform(2, 4))
        
        self.smart_scroll_to_comments()
        
        self.load_all_comments_with_expansion(max_scrolls=max_scrolls)
        
        # 使用V6版本的提取方法
        comments = self.extract_comments_v6()
        
        if comments:
            json_file, csv_file = self.save_comments(comments, note_info)
            
            # 添加到爬取历史
            self.add_to_history(current_url, note_info.get('note_id', 'unknown'), len(comments))
            self.log(f"已添加到爬取历史", "💾")
            
            if json_file and csv_file:
                self.log("="*60, "")
                self.log("处理完成！", "🎉")
                self.log(f"评论数量: {len(comments)} 条", "💬")
                self.log(f"JSON文件: {json_file.name}", "📄")
                self.log(f"CSV文件: {csv_file.name}", "📄")
                self.log("="*60, "")
            
            return comments
        else:
            self.log("未提取到有效评论", "⚠️")
            return []
    
    def batch_process_from_urls(self, urls):
        """批量处理URL列表（带历史记录检查）"""
        self.log(f"开始批量处理 {len(urls)} 个笔记", "🚀")
        
        # 检查历史记录
        urls_to_process = []
        skipped_urls = []
        
        for url in urls:
            if self.is_url_crawled(url):
                history_info = self.get_history_info(url)
                self.log(f"\n⚠️  已爬取过: {url[:50]}...", "🔍")
                self.log(f"  ├─ 爬取时间: {history_info['crawled_at']}", "")
                self.log(f"  └─ 评论数: {history_info['comment_count']} 条", "")
                skipped_urls.append(url)
            else:
                urls_to_process.append(url)
        
        if skipped_urls:
            self.log(f"\n发现 {len(skipped_urls)} 个已爬取的URL", "📊")
            choice = input("是否重新爬取这些URL？(y/n，默认n): ").strip().lower()
            if choice == 'y':
                urls_to_process.extend(skipped_urls)
                self.log("将重新爬取所有URL", "✅")
            else:
                self.log(f"已跳过 {len(skipped_urls)} 个URL，仅处理新URL", "⏭️")
        
        if not urls_to_process:
            self.log("没有需要处理的新URL", "ℹ️")
            return []
        
        self.log(f"\n实际处理 {len(urls_to_process)} 个URL", "📝")
        input("按回车开始处理...")
        
        results = []
        
        for i, url in enumerate(urls_to_process, 1):
            self.log(f"\n{'='*60}")
            self.log(f"处理笔记 {i}/{len(urls_to_process)}", "📝")
            self.log(f"{'='*60}")
            
            try:
                self.log(f"访问URL...", "🌐")
                self.driver.get(url)
                
                wait_time = random.uniform(4, 7)
                self.log(f"等待页面加载 {wait_time:.1f} 秒...", "⏱️")
                time.sleep(wait_time)
                
                comments = self.process_current_page(max_scrolls=20)
                
                results.append({
                    'url': url,
                    'comment_count': len(comments),
                    'success': len(comments) > 0
                })
                
                if i < len(urls_to_process):
                    delay = random.randint(30, 60)
                    self.log(f"等待 {delay} 秒后处理下一个笔记...", "⏸️")
                    time.sleep(delay)
                
            except Exception as e:
                self.log(f"处理失败: {e}", "❌")
                results.append({
                    'url': url,
                    'comment_count': 0,
                    'success': False
                })
        
        self.print_batch_summary(results)
        return results
    
    def print_batch_summary(self, results):
        """打印批量处理总结"""
        total = len(results)
        success = len([r for r in results if r['success']])
        total_comments = sum(r['comment_count'] for r in results)
        
        summary = f"""
╔═══════════════════════════════════════════════════════════╗
║                   批量处理完成                              ║
╚═══════════════════════════════════════════════════════════╝

处理笔记数: {total}
成功数量:   {success} / {total} ({success/total*100:.1f}%)
失败数量:   {total - success}
总评论数:   {total_comments} 条

详细结果:
"""
        print(summary)
        
        for i, result in enumerate(results, 1):
            status = "✅" if result['success'] else "❌"
            print(f"{i}. {status} {result['url'][:50]}... ({result['comment_count']} 条评论)")
        
        print("\n" + "="*60)
    
    def show_history_stats(self):
        """显示爬取历史统计"""
        if not self.crawl_history:
            self.log("暂无爬取历史", "ℹ️")
            return
        
        total_urls = len(self.crawl_history)
        total_comments = sum(info['comment_count'] for info in self.crawl_history.values())
        
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                  爬取历史统计                               ║
╚═══════════════════════════════════════════════════════════╝

已爬取URL数: {total_urls}
总评论数:    {total_comments} 条
历史文件:    {self.history_file}

最近爬取记录:
""")
        
        # 按时间排序，显示最近10条
        sorted_history = sorted(
            self.crawl_history.items(),
            key=lambda x: x[1]['crawled_at'],
            reverse=True
        )[:10]
        
        for url, info in sorted_history:
            print(f"  • {url[:60]}...")
            print(f"    时间: {info['crawled_at']} | 评论: {info['comment_count']}条 | ID: {info['note_id']}")
        
        print("\n" + "="*60)
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.quit()


def main():
    """主函数"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║        小红书评论提取器 - V6 简化版本                      ║
    ║        Simplified CSV Output Version                    ║
    ║                                                          ║
    ║   🔥 V6 核心特性:                                         ║
    ║   • 彻底解决用户名提取问题（继承V5）                        ║
    ║   • 简化CSV输出格式                                        ║
    ║   • 删除冗余字段（note_id, note_title, collected_at）    ║
    ║   • 保留核心字段便于分析                                    ║
    ║   • JSON文件保留完整信息                                   ║
    ║   🆕 爬取历史记录，避免重复爬取                             ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    print("\n⚠️  使用前确认:")
    print("✓ 已运行 start_xiaohongshu_chrome.bat")
    print("✓ Chrome 已打开小红书")
    print("✓ 已登录账号")
    
    print("\n🔧 调试模式:")
    debug_choice = input("是否启用调试模式？(y/n，默认n): ").strip().lower()
    debug_mode = (debug_choice == 'y')
    
    print("\n📋 选择模式:")
    print("1 - 提取当前打开的笔记评论（单个）")
    print("2 - 批量提取多个笔记评论（从 note_urls.txt）")
    print("3 - 批量提取（手动输入URL）")
    print("4 - 查看爬取历史")
    
    choice = input("\n请输入选择 (1/2/3/4): ").strip()
    
    extractor = CommentExtractorV6(debug=debug_mode)
    
    if choice == "4":
        # 查看历史记录
        extractor.show_history_stats()
        input("\n按回车退出...")
        return
    
    if not extractor.connect_to_chrome():
        input("\n❌ 连接失败，按回车退出...")
        return
    
    if choice == "1":
        print("\n✓ 请确保Chrome当前已打开一个小红书笔记页面")
        input("准备好后按回车开始提取...")
        
        extractor.process_current_page(max_scrolls=20)
        
    elif choice == "2":
        url_file = Path("note_urls.txt")
        
        if not url_file.exists():
            print(f"\n❌ 未找到文件: {url_file}")
            print("请创建 note_urls.txt 文件，每行一个URL")
            input("按回车退出...")
            return
        
        with open(url_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and line.strip().startswith('http')]
        
        if urls:
            print(f"\n✓ 从文件读取到 {len(urls)} 个URL")
            extractor.batch_process_from_urls(urls)
        else:
            print("\n❌ 文件中没有有效的URL")
    
    elif choice == "3":
        print("\n请输入笔记URL（每行一个，输入空行结束）:")
        print("示例: https://www.xiaohongshu.com/explore/xxxxx")
        print()
        
        urls = []
        while True:
            url = input().strip()
            if not url:
                break
            if url.startswith('http'):
                urls.append(url)
                print(f"  ✓ 已添加第 {len(urls)} 个URL")
            else:
                print(f"  ⚠️  无效URL，已跳过")
        
        if urls:
            print(f"\n✓ 共 {len(urls)} 个笔记")
            extractor.batch_process_from_urls(urls)
        else:
            print("\n❌ 未输入有效URL")
    
    else:
        print("\n❌ 无效选择")
    
    print("\n\n✅ 所有数据已保存在 data/comments/ 目录")
    print("📊 包含: JSON文件（完整信息）、CSV文件（简化版）、统计报告")
    print("💡 V6版本特点:")
    print("   - CSV仅包含: comment_id, username, content, time, likes, content_length")
    print("   - JSON保留完整信息（含note_id, note_title等）")
    print("   - 文件名包含 _v6 标记")
    print("   🆕 - 爬取历史记录保存在 data/crawl_history.json")
    input("\n按回车关闭...")
    extractor.close()


if __name__ == "__main__":
    main()