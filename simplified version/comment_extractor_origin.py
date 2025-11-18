"""
小红书评论提取器 - 优化版
主要改进：
1. 更精准的评论元素定位
2. 更好的数据结构和字段
3. 更清晰的输出格式
4. 增强的数据清洗和验证
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


class CommentExtractorOptimized:
    """优化版评论提取器"""
    
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
            # 匹配类似 /explore/xxxxx 的ID
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
            # 提取笔记ID
            info['note_id'] = self.extract_note_id(info['note_url'])
            
            # 获取标题 - 多种选择器
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
                    if title and len(title) > 2:  # 至少3个字符
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
            # 小红书评论区的精确选择器
            comment_area_selectors = [
                "#noteComment",  # 评论区ID
                "div[id*='comment']",
                ".comment-container",
                "div[class*='comment-area']",
            ]
            
            for selector in comment_area_selectors:
                try:
                    comment_area = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    
                    # 平滑滚动到评论区
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'start'});",
                        comment_area
                    )
                    time.sleep(random.uniform(1.5, 2.5))
                    self.log("已定位到评论区", "✅")
                    return True
                except:
                    continue
            
            # 如果找不到评论区，滚动到页面60%的位置
            self.log("使用备用滚动方案...", "🔍")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6);")
            time.sleep(random.uniform(1, 2))
            return True
            
        except Exception as e:
            self.log(f"定位评论区失败: {e}", "⚠️")
            return False
    
    def load_all_comments(self, max_scrolls=20):
        """加载所有评论 - 使用滚动和点击加载更多"""
        self.log(f"开始加载评论（最多滚动{max_scrolls}次）...", "🔄")
        
        last_height = 0
        scroll_count = 0
        no_change_count = 0
        
        while scroll_count < max_scrolls and no_change_count < 3:
            try:
                # 获取当前页面高度
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # 滚动到底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1.5, 2.5))
                
                # 尝试点击"加载更多"按钮
                self.try_click_load_more()
                
                scroll_count += 1
                
                # 检查页面是否还在增长
                if current_height == last_height:
                    no_change_count += 1
                else:
                    no_change_count = 0
                    last_height = current_height
                
                if scroll_count % 5 == 0:
                    self.log(f"已滚动 {scroll_count} 次...", "🔄")
                
            except Exception as e:
                self.log(f"滚动时出错: {e}", "⚠️")
                break
        
        self.log(f"完成加载，共滚动 {scroll_count} 次", "✅")
        
        # 最后滚动回评论区开头
        self.smart_scroll_to_comments()
        return scroll_count
    
    def try_click_load_more(self):
        """尝试点击"加载更多"按钮"""
        load_more_texts = ['加载更多', '查看更多', '展开更多', 'Load more']
        
        try:
            for text in load_more_texts:
                buttons = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        button.click()
                        time.sleep(random.uniform(1, 2))
                        return True
        except:
            pass
        
        return False
    
    def is_valid_comment_text(self, text):
        """验证是否是有效的评论内容"""
        if not text or len(text.strip()) < 2:
            return False
        
        # 排除页面元素关键词（更严格）
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
            r'^\d+$',  # 纯数字
            r'^[\W_]+$',  # 只有符号
            r'相关搜索',
            r'综合排序',
            r'最新',
            r'最热',
        ]
        
        text_clean = text.strip()
        
        for pattern in exclude_patterns:
            if re.search(pattern, text_clean):
                return False
        
        # 检查是否包含实际文字内容
        chinese_count = len(re.findall(r'[\u4e00-\u9fff]', text_clean))
        english_count = len(re.findall(r'[a-zA-Z]', text_clean))
        
        # 至少要有2个中文字符或4个英文字符
        if chinese_count >= 2 or english_count >= 4:
            return True
        
        return False
    
    def extract_comments_v2(self):
        """优化的评论提取方法 - 更精准"""
        self.log("开始提取评论...", "📝")
        
        comments = []
        seen_contents = set()
        
        try:
            # 小红书评论的精确选择器（根据实际页面结构）
            comment_selectors = [
                # 评论列表项
                "div.comment-item",
                "li.comment",
                "div[class*='CommentItem']",
                # 评论容器内的项目
                "#noteComment .comment",
                ".comment-list .item",
            ]
            
            comment_elements = []
            used_selector = None
            
            # 尝试所有选择器
            for selector in comment_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and len(elements) > 5:  # 至少要找到5条评论才算有效
                        comment_elements = elements
                        used_selector = selector
                        self.log(f"使用选择器: {selector}, 找到 {len(elements)} 个评论元素", "🔍")
                        break
                except:
                    continue
            
            if not comment_elements:
                self.log("未找到标准评论元素，尝试备用方案...", "⚠️")
                return self.extract_comments_fallback()
            
            # 解析每个评论
            for idx, elem in enumerate(comment_elements, 1):
                try:
                    comment_data = self.parse_comment_element(elem, idx)
                    
                    if comment_data and comment_data['content']:
                        content = comment_data['content']
                        
                        # 去重和验证
                        if content not in seen_contents and self.is_valid_comment_text(content):
                            comments.append(comment_data)
                            seen_contents.add(content)
                
                except Exception as e:
                    continue
            
            self.log(f"成功提取 {len(comments)} 条有效评论", "✅")
            
        except Exception as e:
            self.log(f"提取评论出错: {e}", "❌")
        
        return comments
    
    def parse_comment_element(self, elem, index):
        """解析单个评论元素"""
        try:
            # 提取评论内容
            content_selectors = [
                ".content",
                ".comment-content",
                ".text",
                "div[class*='content']",
                "p"
            ]
            
            content = ""
            for selector in content_selectors:
                try:
                    content_elem = elem.find_element(By.CSS_SELECTOR, selector)
                    content = content_elem.text.strip()
                    if content:
                        break
                except:
                    continue
            
            # 如果上述方法都失败，用元素的text
            if not content:
                content = elem.text.strip()
            
            # 提取用户名
            username_selectors = [
                ".username",
                ".nickname",
                ".user-name",
                "a[class*='user']",
                ".author"
            ]
            
            username = "匿名用户"
            for selector in username_selectors:
                try:
                    user_elem = elem.find_element(By.CSS_SELECTOR, selector)
                    username = user_elem.text.strip()
                    if username:
                        break
                except:
                    continue
            
            # 提取时间
            time_selectors = [
                ".time",
                ".date",
                "span[class*='time']",
                ".publish-time"
            ]
            
            comment_time = ""
            for selector in time_selectors:
                try:
                    time_elem = elem.find_element(By.CSS_SELECTOR, selector)
                    comment_time = time_elem.text.strip()
                    if comment_time:
                        break
                except:
                    continue
            
            # 提取点赞数
            likes = 0
            like_selectors = [
                ".like-count",
                "span[class*='like']",
                ".count"
            ]
            
            for selector in like_selectors:
                try:
                    like_elem = elem.find_element(By.CSS_SELECTOR, selector)
                    like_text = like_elem.text.strip()
                    # 尝试提取数字
                    like_match = re.search(r'\d+', like_text)
                    if like_match:
                        likes = int(like_match.group())
                        break
                except:
                    continue
            
            return {
                'comment_id': f"comment_{index}",
                'username': username,
                'content': content,
                'time': comment_time,
                'likes': likes,
                'collected_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return None
    
    def extract_comments_fallback(self):
        """备用评论提取方法 - 当标准方法失败时使用"""
        self.log("使用备用提取方案...", "🔄")
        
        comments = []
        seen_contents = set()
        
        try:
            # 查找所有可能包含文本的div和span
            text_elements = self.driver.find_elements(By.CSS_SELECTOR, "div, span, p")
            
            for elem in text_elements:
                try:
                    text = elem.text.strip()
                    
                    # 基本验证
                    if not text or len(text) < 5:
                        continue
                    
                    # 去重
                    if text in seen_contents:
                        continue
                    
                    # 严格验证
                    if self.is_valid_comment_text(text):
                        # 检查是否看起来像评论（包含中文句子）
                        if re.search(r'[\u4e00-\u9fff，。！？、：；""''（）【】]', text):
                            comment_data = {
                                'comment_id': f"comment_{len(comments)+1}",
                                'username': '匿名用户',
                                'content': text,
                                'time': '',
                                'likes': 0,
                                'collected_at': datetime.now().isoformat()
                            }
                            
                            comments.append(comment_data)
                            seen_contents.add(text)
                            
                            # 限制最多提取的评论数（避免误提取）
                            if len(comments) >= 100:
                                break
                
                except:
                    continue
            
            self.log(f"备用方案提取到 {len(comments)} 条评论", "✅")
            
        except Exception as e:
            self.log(f"备用提取也失败: {e}", "❌")
        
        return comments
    
    def save_comments(self, comments, note_info):
        """保存评论（优化的格式）"""
        if not comments:
            self.log("没有评论需要保存", "⚠️")
            return None, None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        note_id = note_info.get('note_id', 'unknown')
        
        # JSON文件
        json_filename = self.data_dir / f"comments_{note_id}_{timestamp}.json"
        
        # 完整数据结构
        full_data = {
            'note_info': note_info,
            'comment_count': len(comments),
            'collected_at': datetime.now().isoformat(),
            'comments': comments
        }
        
        try:
            # 保存JSON
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)
            
            self.log(f"JSON已保存: {json_filename.name}", "💾")
            
            # 保存CSV
            csv_filename = self.data_dir / f"comments_{note_id}_{timestamp}.csv"
            self.save_as_csv_optimized(comments, note_info, csv_filename)
            
            # 保存统计报告
            self.save_summary(note_info, comments, timestamp)
            
            return json_filename, csv_filename
            
        except Exception as e:
            self.log(f"保存失败: {e}", "❌")
            return None, None
    
    def save_as_csv_optimized(self, comments, note_info, filename):
        """优化的CSV保存 - 更好的格式和字段"""
        try:
            # CSV字段
            fieldnames = [
                'comment_id',
                'note_id',
                'note_title',
                'username',
                'content',
                'time',
                'likes',
                'content_length',
                'collected_at'
            ]
            
            with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for comment in comments:
                    row = {
                        'comment_id': comment.get('comment_id', ''),
                        'note_id': note_info.get('note_id', ''),
                        'note_title': note_info.get('note_title', ''),
                        'username': comment.get('username', ''),
                        'content': comment.get('content', ''),
                        'time': comment.get('time', ''),
                        'likes': comment.get('likes', 0),
                        'content_length': len(comment.get('content', '')),
                        'collected_at': comment.get('collected_at', '')
                    }
                    writer.writerow(row)
            
            self.log(f"CSV已保存: {filename.name}", "💾")
            
        except Exception as e:
            self.log(f"CSV保存失败: {e}", "⚠️")
    
    def save_summary(self, note_info, comments, timestamp):
        """保存数据统计摘要"""
        try:
            summary_file = self.data_dir / f"summary_{timestamp}.txt"
            
            # 计算统计信息
            total_comments = len(comments)
            avg_length = sum(len(c['content']) for c in comments) / total_comments if total_comments > 0 else 0
            total_likes = sum(c.get('likes', 0) for c in comments)
            
            # 内容长度分布
            short = len([c for c in comments if len(c['content']) < 20])
            medium = len([c for c in comments if 20 <= len(c['content']) < 100])
            long = len([c for c in comments if len(c['content']) >= 100])
            
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
            
            # 同时打印到控制台
            print(summary_content)
            
        except Exception as e:
            self.log(f"保存摘要失败: {e}", "⚠️")
    
    def process_current_page(self, max_scrolls=20):
        """处理当前页面 - 主流程"""
        self.log("="*60, "")
        self.log("开始处理当前页面", "🚀")
        self.log("="*60, "")
        
        # 1. 获取笔记信息
        note_info = self.get_note_info()
        
        # 2. 等待页面稳定
        self.log("等待页面加载完成...", "⏱️")
        time.sleep(random.uniform(2, 4))
        
        # 3. 滚动到评论区
        self.smart_scroll_to_comments()
        
        # 4. 加载所有评论
        self.load_all_comments(max_scrolls=max_scrolls)
        
        # 5. 提取评论
        comments = self.extract_comments_v2()
        
        # 6. 保存评论
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
                # 访问页面
                self.log(f"访问URL...", "🌐")
                self.driver.get(url)
                
                # 等待页面加载
                wait_time = random.uniform(4, 7)
                self.log(f"等待页面加载 {wait_time:.1f} 秒...", "⏱️")
                time.sleep(wait_time)
                
                # 处理当前页面
                comments = self.process_current_page(max_scrolls=20)
                
                results.append({
                    'url': url,
                    'comment_count': len(comments),
                    'success': len(comments) > 0
                })
                
                # 笔记间延迟（重要！）
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
        
        # 打印批量处理总结
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
        """关闭连接（不关闭Chrome）"""
        if self.driver:
            self.driver.quit()


def main():
    """主函数"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║        小红书评论提取器 - 优化版 v2.0                    ║
    ║        Optimized Comment Extractor                      ║
    ║                                                          ║
    ║   ✨ 主要改进:                                            ║
    ║   • 更精准的评论识别                                      ║
    ║   • 更好的数据结构                                        ║
    ║   • 自动生成统计报告                                      ║
    ║   • 改进的CSV格式                                        ║
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
    
    # 创建提取器
    extractor = CommentExtractorOptimized()
    
    # 连接Chrome
    if not extractor.connect_to_chrome():
        input("\n❌ 连接失败，按回车退出...")
        return
    
    if choice == "1":
        # 模式1: 单个页面
        print("\n✓ 请确保Chrome当前已打开一个小红书笔记页面")
        input("准备好后按回车开始提取...")
        
        extractor.process_current_page(max_scrolls=20)
        
    elif choice == "2":
        # 模式2: 从文件读取URL
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
        # 模式3: 手动输入URL
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