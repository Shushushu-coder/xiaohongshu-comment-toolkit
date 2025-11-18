"""
小红书评论提取器 - 防重复版本
在原V6版本基础上增加去重功能

新增功能：
1. 自动记录已爬取的笔记ID
2. 批量处理时智能跳过已爬取的帖子
3. 提供强制重新爬取选项
4. 详细的爬取统计信息
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


class CrawlHistory:
    """爬取历史管理类"""
    
    def __init__(self, history_file="data/crawl_history.json"):
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history = self.load_history()
    
    def load_history(self):
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_history(self):
        """保存历史记录"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def is_crawled(self, note_id):
        """检查笔记是否已爬取"""
        return note_id in self.history
    
    def add_record(self, note_id, url, comment_count, timestamp=None):
        """添加爬取记录"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.history[note_id] = {
            'url': url,
            'comment_count': comment_count,
            'crawled_at': timestamp,
            'last_crawled': timestamp
        }
        self.save_history()
    
    def update_record(self, note_id, comment_count):
        """更新爬取记录（重新爬取时）"""
        if note_id in self.history:
            self.history[note_id]['comment_count'] = comment_count
            self.history[note_id]['last_crawled'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_history()
    
    def get_record(self, note_id):
        """获取爬取记录"""
        return self.history.get(note_id)
    
    def get_stats(self):
        """获取统计信息"""
        return {
            'total_crawled': len(self.history),
            'total_comments': sum(r.get('comment_count', 0) for r in self.history.values())
        }


class CommentExtractorNoDuplicate:
    """防重复版评论提取器"""
    
    def __init__(self, debug=False, force_recrawl=False):
        self.driver = None
        self.wait = None
        self.data_dir = Path("data/comments")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.debug = debug
        self.force_recrawl = force_recrawl  # 强制重新爬取
        self.history = CrawlHistory()  # 历史记录管理
    
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
            
            self.log("等待页面JavaScript渲染完成...", "⏳")
            time.sleep(3)
            
            try:
                self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            except:
                pass
            
            page_title = self.driver.title
            self.debug_log(f"页面标题: {page_title}")
            
            temp_title_from_page = None
            temp_author_from_page = None
            
            if ' - ' in page_title and page_title.endswith('小红书'):
                temp_title_from_page = page_title.rsplit(' - 小红书', 1)[0].strip()
                self.debug_log(f"从页面标题提取笔记标题: {temp_title_from_page[:50]}")
            elif ' - ' in page_title:
                parts = page_title.split(' - ')
                if len(parts) >= 1:
                    temp_title_from_page = parts[0].strip()
                    self.debug_log(f"从页面标题提取笔记标题: {temp_title_from_page[:50]}")
                
                if len(parts) >= 2 and parts[1].strip() != '小红书':
                    temp_author_from_page = parts[1].strip()
                    self.debug_log(f"从页面标题提取可能的作者: {temp_author_from_page}")
            
            try:
                page_source = self.driver.page_source
                
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
                
                if info['note_title'] == '未知标题' and temp_title_from_page:
                    info['note_title'] = temp_title_from_page
                    self.debug_log(f"使用页面标题作为笔记标题")
                
                author_patterns = [
                    r'"note":\s*{[^}]*"user":\s*{[^}]*"nickname":"([^"]+)"',
                    r'"noteData":\s*{[^}]*"user":\s*{[^}]*"nickname":"([^"]+)"',
                    r'"note":\s*{[^}]*"author":\s*{[^}]*"nickname":"([^"]+)"',
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
                
                if found_authors:
                    if len(found_authors) >= 2:
                        info['author'] = found_authors[1]
                        self.debug_log(f"使用第二个找到的作者（笔记作者）: {found_authors[1]}")
                    elif len(found_authors) == 1:
                        info['author'] = found_authors[0]
                        self.debug_log(f"只找到一个作者: {found_authors[0]}")
                    
            except Exception as e:
                self.debug_log(f"从页面源码提取失败: {e}")
            
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
            
        except Exception as e:
            self.log(f"获取笔记信息时出错: {e}", "⚠️")
        
        self.log(f"笔记ID: {info['note_id']}", "🆔")
        self.log(f"笔记标题: {info['note_title'][:50]}...", "📝")
        self.log(f"作者: {info['author']}", "👤")
        
        return info
    
    def smart_scroll_to_comments(self):
        """智能滚动到评论区"""
        self.log("滚动到评论区...", "📜")
        try:
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 800)")
                time.sleep(0.5)
        except:
            pass
    
    def load_all_comments_with_expansion(self, max_scrolls=20):
        """加载所有评论并展开"""
        self.log("开始加载评论...", "📥")
        scroll_count = 0
        last_height = 0
        no_change_count = 0
        
        while scroll_count < max_scrolls:
            try:
                expand_btns = self.driver.find_elements(By.CSS_SELECTOR, 
                    "div[class*='expand'], span[class*='expand'], button[class*='expand'], " +
                    "div[class*='unfold'], span[class*='unfold']")
                
                visible_expand_btns = [btn for btn in expand_btns 
                                      if btn.is_displayed() and btn.size['height'] > 0]
                
                if visible_expand_btns:
                    for btn in visible_expand_btns[:3]:
                        try:
                            if "展开" in btn.text or "更多" in btn.text:
                                btn.click()
                                time.sleep(0.3)
                        except:
                            pass
                
                current_height = self.driver.execute_script(
                    "return document.documentElement.scrollHeight")
                
                if current_height == last_height:
                    no_change_count += 1
                    if no_change_count >= 3:
                        self.log("评论已全部加载", "✅")
                        break
                else:
                    no_change_count = 0
                
                self.driver.execute_script("window.scrollBy(0, 800)")
                time.sleep(random.uniform(0.5, 1.0))
                
                last_height = current_height
                scroll_count += 1
                
            except Exception as e:
                self.debug_log(f"滚动过程出错: {e}")
                break
        
        self.log(f"完成 {scroll_count} 次滚动", "✅")
    
    def extract_comments_v6(self):
        """V6版评论提取方法"""
        self.log("开始提取评论（V6方法）...", "🔍")
        
        try:
            comment_elements = self.driver.find_elements(By.XPATH,
                "//div[contains(@class, 'comment-item') or contains(@class, 'note-comment-item')]")
            
            if not comment_elements:
                comment_elements = self.driver.find_elements(By.CSS_SELECTOR,
                    "div[class*='comment']")
            
            self.log(f"找到 {len(comment_elements)} 个评论容器", "📊")
            
            comments = []
            seen_ids = set()
            
            for idx, elem in enumerate(comment_elements, 1):
                try:
                    comment_data = self.extract_single_comment_v6(elem, idx)
                    
                    if comment_data and comment_data['comment_id']:
                        if comment_data['comment_id'] not in seen_ids:
                            comments.append(comment_data)
                            seen_ids.add(comment_data['comment_id'])
                            
                            if self.debug and idx <= 3:
                                self.debug_log(f"评论 {idx}: {comment_data['username']} - {comment_data['content'][:30]}...")
                
                except Exception as e:
                    self.debug_log(f"提取评论 {idx} 失败: {e}")
                    continue
            
            self.log(f"成功提取 {len(comments)} 条有效评论", "✅")
            return comments
            
        except Exception as e:
            self.log(f"评论提取失败: {e}", "❌")
            return []
    
    def extract_single_comment_v6(self, elem, idx):
        """V6版单条评论提取"""
        comment_id = f"comment_{idx}_{int(time.time())}"
        username = "未知用户"
        content = ""
        comment_time = ""
        likes = 0
        
        try:
            html = elem.get_attribute('outerHTML')
            
            username_patterns = [
                r'class="[^"]*user[^"]*name[^"]*">([^<]+)<',
                r'class="[^"]*author[^"]*">([^<]+)<',
                r'data-username="([^"]+)"',
            ]
            
            for pattern in username_patterns:
                match = re.search(pattern, html)
                if match:
                    temp_username = match.group(1).strip()
                    if temp_username and len(temp_username) > 0:
                        username = temp_username
                        break
            
            if username == "未知用户":
                try:
                    user_links = elem.find_elements(By.CSS_SELECTOR, "a")
                    for link in user_links:
                        href = link.get_attribute('href')
                        if href and '/user/profile/' in href:
                            username = link.text.strip()
                            if username:
                                break
                except:
                    pass
            
            try:
                content_elem = elem.find_element(By.CSS_SELECTOR,
                    "span[class*='content'], div[class*='content']")
                content = content_elem.text.strip()
            except:
                pass
            
            if not content:
                content_patterns = [
                    r'class="[^"]*content[^"]*">([^<]+)<',
                    r'class="[^"]*text[^"]*">([^<]+)<',
                ]
                for pattern in content_patterns:
                    match = re.search(pattern, html)
                    if match:
                        content = match.group(1).strip()
                        if content:
                            break
            
            try:
                time_elem = elem.find_element(By.CSS_SELECTOR,
                    "span[class*='time'], span[class*='date']")
                comment_time = time_elem.text.strip()
            except:
                pass
            
            try:
                like_elem = elem.find_element(By.CSS_SELECTOR,
                    "span[class*='like']")
                like_text = like_elem.text.strip()
                likes = int(''.join(filter(str.isdigit, like_text))) if like_text else 0
            except:
                pass
        
        except Exception as e:
            self.debug_log(f"提取评论详情失败: {e}")
        
        return {
            'comment_id': comment_id,
            'username': username,
            'content': content,
            'time': comment_time,
            'likes': likes,
            'content_length': len(content)
        }
    
    def save_comments(self, comments, note_info):
        """保存评论数据"""
        if not comments:
            return None, None
        
        note_id = note_info.get('note_id', 'unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        base_filename = f"comments_{note_id}_{timestamp}_v6_nodup"
        json_file = self.data_dir / f"{base_filename}.json"
        csv_file = self.data_dir / f"{base_filename}.csv"
        
        full_data = {
            'note_info': note_info,
            'comments': comments,
            'collected_at': datetime.now().isoformat(),
            'total_comments': len(comments)
        }
        
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)
            self.log(f"JSON已保存: {json_file.name}", "💾")
        except Exception as e:
            self.log(f"保存JSON失败: {e}", "❌")
            return None, None
        
        try:
            with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'comment_id', 'username', 'content', 'time', 'likes', 'content_length'
                ])
                writer.writeheader()
                writer.writerows(comments)
            self.log(f"CSV已保存: {csv_file.name}", "💾")
        except Exception as e:
            self.log(f"保存CSV失败: {e}", "❌")
        
        return json_file, csv_file
    
    def process_current_page(self, max_scrolls=20):
        """处理当前页面"""
        self.log("="*60, "")
        self.log("开始处理当前页面", "🚀")
        self.log("="*60, "")
        
        note_info = self.get_note_info()
        note_id = note_info.get('note_id')
        
        # 检查是否已爬取
        if note_id and not self.force_recrawl:
            if self.history.is_crawled(note_id):
                record = self.history.get_record(note_id)
                self.log(f"⚠️  该笔记已于 {record['crawled_at']} 爬取过", "⏭️")
                self.log(f"   之前爬取了 {record['comment_count']} 条评论", "📊")
                self.log("   跳过处理（使用 --force 参数可强制重新爬取）", "")
                return []
        
        self.log("等待页面加载完成...", "⏱️")
        time.sleep(random.uniform(2, 4))
        
        self.smart_scroll_to_comments()
        self.load_all_comments_with_expansion(max_scrolls=max_scrolls)
        comments = self.extract_comments_v6()
        
        if comments:
            json_file, csv_file = self.save_comments(comments, note_info)
            
            # 记录到历史
            if note_id:
                if self.history.is_crawled(note_id):
                    self.history.update_record(note_id, len(comments))
                    self.log(f"更新爬取记录: {note_id}", "🔄")
                else:
                    self.history.add_record(note_id, note_info['note_url'], len(comments))
                    self.log(f"新增爬取记录: {note_id}", "➕")
            
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
        """批量处理URL列表（带去重）"""
        self.log(f"开始批量处理 {len(urls)} 个笔记", "🚀")
        
        # 预先检查哪些已爬取
        url_status = []
        for url in urls:
            note_id = self.extract_note_id(url)
            is_crawled = self.history.is_crawled(note_id) if note_id else False
            url_status.append({
                'url': url,
                'note_id': note_id,
                'is_crawled': is_crawled
            })
        
        # 统计
        already_crawled = [s for s in url_status if s['is_crawled']]
        to_crawl = [s for s in url_status if not s['is_crawled']]
        
        self.log("="*60, "")
        self.log("📊 批量处理统计", "")
        self.log(f"总笔记数: {len(urls)}", "")
        self.log(f"已爬取: {len(already_crawled)} 个（将跳过）", "✅")
        self.log(f"待爬取: {len(to_crawl)} 个", "🆕")
        
        if already_crawled and not self.force_recrawl:
            self.log("\n已爬取的笔记:", "📋")
            for i, s in enumerate(already_crawled[:5], 1):
                record = self.history.get_record(s['note_id'])
                self.log(f"  {i}. {s['note_id']} (爬取于 {record['crawled_at']})", "")
            if len(already_crawled) > 5:
                self.log(f"  ... 还有 {len(already_crawled)-5} 个", "")
        
        self.log("="*60, "")
        
        if self.force_recrawl:
            self.log("⚠️  强制重新爬取模式：将重新爬取所有笔记", "🔄")
            urls_to_process = urls
        else:
            self.log(f"将只爬取 {len(to_crawl)} 个新笔记", "✅")
            urls_to_process = [s['url'] for s in to_crawl]
        
        if not urls_to_process:
            self.log("没有需要爬取的新笔记！", "✅")
            return []
        
        input(f"\n按回车开始爬取 {len(urls_to_process)} 个笔记...")
        
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
                    'note_id': self.extract_note_id(url),
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
                    'note_id': self.extract_note_id(url),
                    'comment_count': 0,
                    'success': False
                })
        
        self.print_batch_summary(results, len(already_crawled) if not self.force_recrawl else 0)
        return results
    
    def print_batch_summary(self, results, skipped_count=0):
        """打印批量处理总结"""
        total_processed = len(results)
        success = len([r for r in results if r['success']])
        total_comments = sum(r['comment_count'] for r in results)
        
        stats = self.history.get_stats()
        
        summary = f"""
╔═══════════════════════════════════════════════════════════╗
║                   批量处理完成                              ║
╚═══════════════════════════════════════════════════════════╝

本次处理:
  处理笔记数: {total_processed}
  成功数量:   {success} / {total_processed} ({success/total_processed*100:.1f}% 如果 total_processed > 0 否则 0)
  失败数量:   {total_processed - success}
  获取评论:   {total_comments} 条
  跳过笔记:   {skipped_count} 个

历史统计:
  累计爬取笔记: {stats['total_crawled']} 个
  累计评论数:   {stats['total_comments']} 条

详细结果:
"""
        print(summary)
        
        for i, result in enumerate(results, 1):
            status = "✅" if result['success'] else "❌"
            note_id = result.get('note_id', 'unknown')[:10]
            print(f"{i}. {status} [{note_id}] {result['url'][:40]}... ({result['comment_count']} 条评论)")
        
        print("\n" + "="*60)
        print(f"💡 历史记录文件: data/crawl_history.json")
        print(f"📁 数据保存目录: data/comments/")
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.quit()


def main():
    """主函数"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║        小红书评论提取器 - 防重复版本                        ║
    ║        No Duplicate Crawling Version                    ║
    ║                                                          ║
    ║   🔥 新增特性:                                            ║
    ║   • 自动记录已爬取的笔记                                    ║
    ║   • 智能跳过已爬取内容                                      ║
    ║   • 详细的爬取统计                                         ║
    ║   • 支持强制重新爬取                                        ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    print("\n⚠️  使用前确认:")
    print("✓ 已运行 start_xiaohongshu_chrome.bat")
    print("✓ Chrome 已打开小红书")
    print("✓ 已登录账号")
    
    print("\n🔧 高级选项:")
    debug_choice = input("是否启用调试模式？(y/n，默认n): ").strip().lower()
    debug_mode = (debug_choice == 'y')
    
    force_choice = input("是否强制重新爬取已处理的笔记？(y/n，默认n): ").strip().lower()
    force_recrawl = (force_choice == 'y')
    
    if force_recrawl:
        print("⚠️  警告: 强制模式将重新爬取所有笔记，包括已处理的！")
    
    print("\n📋 选择模式:")
    print("1 - 提取当前打开的笔记评论（单个）")
    print("2 - 批量提取多个笔记评论（从 note_urls.txt）")
    print("3 - 批量提取（手动输入URL）")
    print("4 - 查看爬取历史统计")
    
    choice = input("\n请输入选择 (1/2/3/4): ").strip()
    
    if choice == "4":
        # 显示历史统计
        history = CrawlHistory()
        stats = history.get_stats()
        
        print(f"\n{'='*60}")
        print("📊 爬取历史统计")
        print(f"{'='*60}")
        print(f"累计爬取笔记: {stats['total_crawled']} 个")
        print(f"累计获取评论: {stats['total_comments']} 条")
        print(f"\n最近爬取的5个笔记:")
        
        sorted_history = sorted(
            history.history.items(),
            key=lambda x: x[1].get('last_crawled', ''),
            reverse=True
        )
        
        for i, (note_id, record) in enumerate(sorted_history[:5], 1):
            print(f"{i}. [{note_id[:10]}] {record['comment_count']} 条评论")
            print(f"   爬取时间: {record['last_crawled']}")
            print(f"   URL: {record['url'][:60]}...")
        
        print(f"\n{'='*60}")
        input("按回车返回...")
        return
    
    extractor = CommentExtractorNoDuplicate(debug=debug_mode, force_recrawl=force_recrawl)
    
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
    print("📊 爬取历史记录: data/crawl_history.json")
    print("💡 下次运行将自动跳过已爬取的笔记")
    input("\n按回车关闭...")
    extractor.close()


if __name__ == "__main__":
    main()