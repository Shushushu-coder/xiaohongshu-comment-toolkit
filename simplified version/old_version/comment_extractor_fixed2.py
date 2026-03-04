"""
小红书评论提取器 - 修复用户名版本
主要修复：
1. 修复用户名提取不准确的问题
2. 正确识别楼中楼回复中的回复者用户名
3. 改进用户名和内容的分离逻辑
4. 保持之前的展开功能
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


class CommentExtractorV4:
    """V4版本 - 修复用户名提取问题"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.data_dir = Path("data/comments")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def log(self, message, symbol="ℹ️"):
        """日志输出"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {symbol} {message}")
    
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
        """获取笔记基本信息"""
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
            info['note_id'] = self.extract_note_id(info['note_url'])
            
            # 获取标题
            title_selectors = [
                "#detail-title",
                "h1[class*='title']",
                "div[class*='note-title']",
                ".title",
                "h1"
            ]
            
            for selector in title_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    title = elem.text.strip()
                    if title and len(title) > 2:
                        info['note_title'] = title
                        break
                except:
                    continue
            
            # 获取作者
            author_selectors = [
                ".author-name",
                "a[class*='author']",
                "div[class*='user-name']",
                ".username"
            ]
            
            for selector in author_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    author = elem.text.strip()
                    if author and len(author) > 1:
                        info['author'] = author
                        break
                except:
                    continue
            
            self.log(f"笔记信息: ID={info['note_id']}, 标题={info['note_title'][:30]}...", "📌")
            
        except Exception as e:
            self.log(f"获取笔记信息部分失败: {e}", "⚠️")
        
        return info
    
    def smart_scroll_to_comments(self):
        """智能滚动到评论区"""
        self.log("定位评论区...", "📜")
        
        try:
            comment_area_selectors = [
                "#noteComment",
                "div[id*='comment']",
                ".comment-container",
                "div[class*='comment-area']",
            ]
            
            for selector in comment_area_selectors:
                try:
                    comment_area = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'start'});",
                        comment_area
                    )
                    time.sleep(random.uniform(1.5, 2.5))
                    self.log("已定位到评论区", "✅")
                    return True
                except:
                    continue
            
            self.log("使用备用滚动方案...", "🔍")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6);")
            time.sleep(random.uniform(1, 2))
            return True
            
        except Exception as e:
            self.log(f"定位评论区失败: {e}", "⚠️")
            return False
    
    def expand_all_comments(self):
        """展开所有折叠的评论内容"""
        self.log("开始展开所有折叠的评论...", "📖")
        
        expanded_count = 0
        max_attempts = 5
        
        for attempt in range(max_attempts):
            self.log(f"第 {attempt + 1} 轮展开检查...", "🔍")
            
            content_expanded = self.expand_comment_contents()
            reply_expanded = self.expand_sub_replies()
            more_loaded = self.click_load_more_comments()
            
            expanded_count += content_expanded + reply_expanded
            
            if content_expanded == 0 and reply_expanded == 0 and not more_loaded:
                self.log(f"所有内容已展开（共展开 {expanded_count} 次）", "✅")
                break
            
            time.sleep(random.uniform(1, 2))
        
        return expanded_count
    
    def expand_comment_contents(self):
        """展开评论内容本身"""
        expanded = 0
        
        expand_keywords = [
            '展开',
            '查看全部',
            '全文',
            '查看更多',
            '显示全部',
            'expand',
            'show more'
        ]
        
        try:
            for keyword in expand_keywords:
                try:
                    xpath_queries = [
                        f"//span[contains(text(), '{keyword}')]",
                        f"//div[contains(text(), '{keyword}')]",
                        f"//a[contains(text(), '{keyword}')]",
                        f"//button[contains(text(), '{keyword}')]",
                        f"//*[contains(@class, 'expand') and contains(text(), '{keyword}')]"
                    ]
                    
                    for xpath in xpath_queries:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        
                        for elem in elements:
                            try:
                                if elem.is_displayed() and elem.is_enabled():
                                    self.driver.execute_script(
                                        "arguments[0].scrollIntoView({block: 'center'});", 
                                        elem
                                    )
                                    time.sleep(0.3)
                                    
                                    try:
                                        elem.click()
                                    except:
                                        self.driver.execute_script("arguments[0].click();", elem)
                                    
                                    expanded += 1
                                    time.sleep(random.uniform(0.3, 0.6))
                                    
                            except Exception as e:
                                continue
                                
                except Exception as e:
                    continue
            
            if expanded > 0:
                self.log(f"展开了 {expanded} 个评论内容", "📖")
                
        except Exception as e:
            self.log(f"展开评论内容时出错: {e}", "⚠️")
        
        return expanded
    
    def expand_sub_replies(self):
        """展开楼中楼回复"""
        expanded = 0
        
        reply_keywords = [
            '条回复',
            '展开回复',
            'replies',
            '更多回复'
        ]
        
        try:
            for keyword in reply_keywords:
                try:
                    elements = self.driver.find_elements(
                        By.XPATH, 
                        f"//*[contains(text(), '{keyword}')]"
                    )
                    
                    for elem in elements:
                        try:
                            if elem.is_displayed() and elem.is_enabled():
                                self.driver.execute_script(
                                    "arguments[0].scrollIntoView({block: 'center'});", 
                                    elem
                                )
                                time.sleep(0.3)
                                
                                try:
                                    elem.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", elem)
                                
                                expanded += 1
                                time.sleep(random.uniform(0.5, 1))
                                
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    continue
            
            if expanded > 0:
                self.log(f"展开了 {expanded} 个楼中楼回复", "💬")
                
        except Exception as e:
            self.log(f"展开子回复时出错: {e}", "⚠️")
        
        return expanded
    
    def click_load_more_comments(self):
        """点击"加载更多评论"按钮"""
        load_more_texts = [
            '加载更多评论',
            '查看更多评论',
            '加载更多',
            '查看更多',
            '展开更多评论',
            'Load more',
            'Show more'
        ]
        
        try:
            for text in load_more_texts:
                try:
                    buttons = self.driver.find_elements(
                        By.XPATH, 
                        f"//*[contains(text(), '{text}')]"
                    )
                    
                    for button in buttons:
                        try:
                            if button.is_displayed() and button.is_enabled():
                                self.driver.execute_script(
                                    "arguments[0].scrollIntoView({block: 'center'});", 
                                    button
                                )
                                time.sleep(0.5)
                                
                                try:
                                    button.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", button)
                                
                                self.log(f"点击了「{text}」按钮", "🔄")
                                time.sleep(random.uniform(1.5, 2.5))
                                return True
                                
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            pass
        
        return False
    
    def load_all_comments_with_expansion(self, max_scrolls=20):
        """加载并展开所有评论"""
        self.log(f"开始加载和展开评论（最多滚动{max_scrolls}次）...", "🔄")
        
        last_height = 0
        scroll_count = 0
        no_change_count = 0
        
        while scroll_count < max_scrolls and no_change_count < 3:
            try:
                self.expand_all_comments()
                
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
                
                self.expand_all_comments()
                
                scroll_count += 1
                
                if current_height == last_height:
                    no_change_count += 1
                else:
                    no_change_count = 0
                    last_height = current_height
                
                if scroll_count % 3 == 0:
                    self.log(f"已滚动 {scroll_count} 次...", "🔄")
                
            except Exception as e:
                self.log(f"滚动时出错: {e}", "⚠️")
                break
        
        self.log(f"完成加载，共滚动 {scroll_count} 次", "✅")
        
        self.log("最后一次全面展开检查...", "🔍")
        self.expand_all_comments()
        
        self.smart_scroll_to_comments()
        return scroll_count
    
    def is_valid_comment_text(self, text):
        """验证是否是有效的评论内容"""
        if not text or len(text.strip()) < 2:
            return False
        
        exclude_patterns = [
            r'^(创作中心|业务合作|发现|发布|通知|我|全部|图文|视频|用户|筛选)$',
            r'^(关注|点赞|收藏|分享|评论|转发)$',
            r'沪ICP备',
            r'营业执照',
            r'公网安备',
            r'增值电信',
            r'行吟信息科技',
            r'小红书号',
            r'粉丝',
            r'笔记・\d+',
            r'^\d+$',
            r'^[\W_]+$',
            r'相关搜索',
            r'综合排序',
            r'最新',
            r'最热',
            r'^展开$',
            r'^查看全部$',
            r'^\d+条回复$',
        ]
        
        text_clean = text.strip()
        
        for pattern in exclude_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                return False
        
        chinese_count = len(re.findall(r'[\u4e00-\u9fff]', text_clean))
        english_count = len(re.findall(r'[a-zA-Z]', text_clean))
        
        if chinese_count >= 2 or english_count >= 4:
            return True
        
        return False
    
    def extract_username_from_element(self, elem):
        """
        从评论元素中提取用户名 - 改进版
        关键改进：正确处理楼中楼回复的用户名
        """
        username = "匿名用户"
        
        try:
            # 策略1: 尝试多种用户名选择器
            username_selectors = [
                "a[class*='user']",  # 用户链接
                "div[class*='nickname']",  # 昵称div
                "span[class*='nickname']",  # 昵称span
                "div[class*='user-name']",  # 用户名div
                ".username",  # 用户名类
                "a[class*='name']",  # 名字链接
            ]
            
            for selector in username_selectors:
                try:
                    user_elem = elem.find_element(By.CSS_SELECTOR, selector)
                    temp_username = user_elem.text.strip()
                    
                    # 过滤掉明显不是用户名的文本
                    if temp_username and len(temp_username) > 0 and len(temp_username) < 30:
                        # 排除常见的干扰文本
                        if not any(keyword in temp_username for keyword in [
                            '回复', '作者', '天前', '小时', '分钟', '刚刚', 
                            '点赞', '评论', '收藏', '关注'
                        ]):
                            username = temp_username
                            break
                except:
                    continue
            
            # 策略2: 如果上面的方法没找到，从完整文本中提取
            if username == "匿名用户":
                try:
                    # 获取评论元素的完整文本
                    full_text = elem.text.strip()
                    lines = full_text.split('\n')
                    
                    # 第一行通常是用户名
                    if lines and len(lines) > 0:
                        first_line = lines[0].strip()
                        
                        # 检查第一行是否看起来像用户名
                        if len(first_line) > 0 and len(first_line) < 30:
                            # 排除时间标记
                            if not re.match(r'^\d+[-/年月日时分秒: ]+', first_line):
                                # 排除"回复"字样
                                if '回复' not in first_line:
                                    username = first_line
                except:
                    pass
            
        except Exception as e:
            pass
        
        return username
    
    def extract_comment_content(self, elem, username):
        """
        从评论元素中提取评论内容 - 改进版
        关键改进：更好地分离用户名和内容
        """
        content = ""
        
        try:
            # 策略1: 尝试找到专门的内容元素
            content_selectors = [
                "div[class*='content']",
                "span[class*='content']",
                "p[class*='content']",
                ".comment-content",
                "div[class*='text']",
                "span[class*='text']"
            ]
            
            for selector in content_selectors:
                try:
                    content_elem = elem.find_element(By.CSS_SELECTOR, selector)
                    content = content_elem.text.strip()
                    if content and len(content) > 0:
                        break
                except:
                    continue
            
            # 策略2: 如果没找到内容元素，从完整文本中提取
            if not content:
                full_text = elem.text.strip()
                
                # 移除用户名
                if username in full_text:
                    content = full_text.replace(username, '', 1).strip()
                else:
                    content = full_text
                
                # 移除时间信息（通常在最后）
                lines = content.split('\n')
                filtered_lines = []
                
                for line in lines:
                    line = line.strip()
                    # 跳过空行
                    if not line:
                        continue
                    # 跳过纯数字或时间标记
                    if re.match(r'^[\d\-:年月日时分天前小刚来自 ]+$', line):
                        continue
                    # 跳过点赞、评论等互动信息
                    if re.match(r'^[\d点赞评论收藏 ]+$', line):
                        continue
                    filtered_lines.append(line)
                
                content = ' '.join(filtered_lines)
            
            # 清理内容
            content = content.strip()
            
            # 移除开头的"回复"标记（如果有）
            # 但保留"回复 XXX :"格式，因为这是有用信息
            
        except Exception as e:
            pass
        
        return content
    
    def extract_comments_v3(self):
        """
        提取评论 - V3改进版
        主要改进：更准确的用户名和内容提取
        """
        self.log("开始提取评论数据...", "📝")
        
        comments = []
        seen_contents = set()
        
        try:
            # 评论元素选择器
            comment_selectors = [
                "div[class*='comment-item']",
                "div[class*='commentItem']",
                ".comment-item",
                "div[class*='comment']",
            ]
            
            comment_elements = []
            for selector in comment_selectors:
                try:
                    elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elems:
                        comment_elements = elems
                        self.log(f"使用选择器: {selector}", "🎯")
                        break
                except:
                    continue
            
            if not comment_elements:
                self.log("未找到评论元素", "⚠️")
                return comments
            
            self.log(f"找到 {len(comment_elements)} 个评论元素", "🔍")
            
            for idx, elem in enumerate(comment_elements, 1):
                try:
                    # 提取用户名 - 使用改进的方法
                    username = self.extract_username_from_element(elem)
                    
                    # 提取评论内容 - 使用改进的方法
                    content = self.extract_comment_content(elem, username)
                    
                    # 提取时间
                    time_text = ""
                    time_selectors = [
                        "span[class*='time']",
                        "div[class*='time']",
                        ".date",
                        "span[class*='date']"
                    ]
                    
                    for selector in time_selectors:
                        try:
                            time_elem = elem.find_element(By.CSS_SELECTOR, selector)
                            time_text = time_elem.text.strip()
                            if time_text:
                                break
                        except:
                            continue
                    
                    # 如果没找到时间，尝试从文本中提取
                    if not time_text:
                        try:
                            full_text = elem.text
                            # 查找时间模式
                            time_patterns = [
                                r'\d+天前',
                                r'\d+小时前',
                                r'\d+分钟前',
                                r'刚刚',
                                r'\d{2}-\d{2}',
                                r'\d{4}-\d{2}-\d{2}',
                            ]
                            for pattern in time_patterns:
                                match = re.search(pattern, full_text)
                                if match:
                                    time_text = match.group(0)
                                    break
                        except:
                            pass
                    
                    # 提取点赞数
                    likes = 0
                    like_selectors = [
                        "span[class*='like']",
                        "div[class*='like']",
                        ".like-count"
                    ]
                    
                    for selector in like_selectors:
                        try:
                            like_elem = elem.find_element(By.CSS_SELECTOR, selector)
                            like_text = like_elem.text.strip()
                            numbers = re.findall(r'\d+', like_text)
                            if numbers:
                                likes = int(numbers[0])
                                break
                        except:
                            continue
                    
                    # 数据验证
                    if not self.is_valid_comment_text(content):
                        continue
                    
                    # 去重
                    content_key = f"{username}:{content[:50]}"
                    if content_key in seen_contents:
                        continue
                    seen_contents.add(content_key)
                    
                    # 构建评论对象
                    comment = {
                        'comment_id': f"comment_{idx}",
                        'username': username,
                        'content': content,
                        'time': time_text,
                        'likes': likes,
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    comments.append(comment)
                    
                    # 调试输出（可选）
                    if idx <= 5:  # 只输出前5条用于调试
                        self.log(f"样例 {idx}: {username} | {content[:30]}...", "🔍")
                    
                except Exception as e:
                    continue
            
            self.log(f"提取到 {len(comments)} 条有效评论", "✅")
            
        except Exception as e:
            self.log(f"提取评论时出错: {e}", "❌")
        
        return comments
    
    def save_comments(self, comments, note_info):
        """保存评论到文件"""
        if not comments:
            self.log("没有评论可保存", "⚠️")
            return None, None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        note_id = note_info.get('note_id', 'unknown')
        
        json_file = self.data_dir / f"comments_{note_id}_{timestamp}.json"
        csv_file = self.data_dir / f"comments_{note_id}_{timestamp}.csv"
        summary_file = self.data_dir / f"summary_{timestamp}.txt"
        
        try:
            # 保存JSON
            data = {
                'note_info': note_info,
                'comment_count': len(comments),
                'collected_at': datetime.now().isoformat(),
                'comments': comments
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.log(f"已保存JSON: {json_file.name}", "💾")
            
            # 保存CSV
            csv_headers = ['comment_id', 'note_id', 'note_title', 'username', 
                          'content', 'time', 'likes', 'content_length', 'collected_at']
            
            with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_headers)
                writer.writeheader()
                
                for comment in comments:
                    row = {
                        'comment_id': comment['comment_id'],
                        'note_id': note_id,
                        'note_title': note_info.get('note_title', ''),
                        'username': comment['username'],
                        'content': comment['content'],
                        'time': comment['time'],
                        'likes': comment['likes'],
                        'content_length': len(comment['content']),
                        'collected_at': comment['collected_at']
                    }
                    writer.writerow(row)
            
            self.log(f"已保存CSV: {csv_file.name}", "💾")
            
            # 保存摘要
            self.save_summary(comments, note_info, summary_file)
            
            return json_file, csv_file
            
        except Exception as e:
            self.log(f"保存文件失败: {e}", "❌")
            return None, None
    
    def save_summary(self, comments, note_info, summary_file):
        """生成并保存摘要报告"""
        try:
            total_comments = len(comments)
            total_likes = sum(c['likes'] for c in comments)
            avg_length = sum(len(c['content']) for c in comments) / total_comments if total_comments > 0 else 0
            
            short = len([c for c in comments if len(c['content']) < 20])
            medium = len([c for c in comments if 20 <= len(c['content']) <= 100])
            long = len([c for c in comments if len(c['content']) > 100])
            
            summary_content = f"""
╔═══════════════════════════════════════════════════════════╗
║                   数据收集摘要报告                          ║
╚═══════════════════════════════════════════════════════════╝

📌 笔记信息
----------------------------------------------------------
笔记ID:     {note_info.get('note_id', 'N/A')}
笔记标题:   {note_info.get('note_title', 'N/A')}
作者:       {note_info.get('author', 'N/A')}
URL:        {note_info.get('note_url', 'N/A')}

💬 评论统计
----------------------------------------------------------
总评论数:   {total_comments} 条
平均长度:   {avg_length:.1f} 字符
总点赞数:   {total_likes}

📊 内容长度分布
----------------------------------------------------------
短评论 (<20字):      {short} 条 ({short/total_comments*100:.1f}%)
中等评论 (20-100字): {medium} 条 ({medium/total_comments*100:.1f}%)
长评论 (>100字):     {long} 条 ({long/total_comments*100:.1f}%)

⏰ 收集时间
----------------------------------------------------------
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

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
        self.log("开始处理当前页面", "🚀")
        self.log("="*60, "")
        
        note_info = self.get_note_info()
        
        self.log("等待页面加载完成...", "⏱️")
        time.sleep(random.uniform(2, 4))
        
        self.smart_scroll_to_comments()
        
        self.load_all_comments_with_expansion(max_scrolls=max_scrolls)
        
        # 使用V3版本的提取方法
        comments = self.extract_comments_v3()
        
        if comments:
            json_file, csv_file = self.save_comments(comments, note_info)
            
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
        """批量处理URL列表"""
        self.log(f"开始批量处理 {len(urls)} 个笔记", "🚀")
        
        results = []
        
        for i, url in enumerate(urls, 1):
            self.log(f"\n{'='*60}")
            self.log(f"处理笔记 {i}/{len(urls)}", "📝")
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
                
                if i < len(urls):
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
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.quit()


def main():
    """主函数"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║        小红书评论提取器 - V4 修复用户名版本               ║
    ║        Username Fix Version                             ║
    ║                                                          ║
    ║   ✨ V4 主要修复:                                         ║
    ║   • 修复用户名提取不准确问题                               ║
    ║   • 正确识别楼中楼回复的用户名                             ║
    ║   • 改进内容和用户名的分离逻辑                             ║
    ║   • 保持所有展开功能                                       ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    print("\n⚠️  使用前确认:")
    print("✓ 已运行 start_xiaohongshu_chrome.bat")
    print("✓ Chrome 已打开小红书")
    print("✓ 已登录账号")
    
    print("\n📋 选择模式:")
    print("1 - 提取当前打开的笔记评论（单个）")
    print("2 - 批量提取多个笔记评论（从 note_urls.txt）")
    print("3 - 批量提取（手动输入URL）")
    
    choice = input("\n请输入选择 (1/2/3): ").strip()
    
    extractor = CommentExtractorV4()
    
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
            input("按回车开始批量处理...")
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
            input("按回车开始处理...")
            extractor.batch_process_from_urls(urls)
        else:
            print("\n❌ 未输入有效URL")
    
    else:
        print("\n❌ 无效选择")
    
    print("\n\n✅ 所有数据已保存在 data/comments/ 目录")
    print("📊 包含: JSON文件、CSV文件、统计报告")
    input("\n按回车关闭...")
    extractor.close()


if __name__ == "__main__":
    main()