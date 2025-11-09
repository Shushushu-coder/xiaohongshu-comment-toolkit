"""
小红书互动数据诊断工具
用于诊断点赞数、收藏数、评论数的提取
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import re

def diagnose_interactions():
    """诊断当前页面的互动数据"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║         小红书互动数据诊断工具                             ║
    ║     用于查找点赞、收藏、评论数的HTML元素                    ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        # 连接到Chrome
        print("\n[1/5] 连接到Chrome...")
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=options)
        print("✅ 连接成功")
        
        # 获取页面信息
        print("\n[2/5] 获取页面基本信息...")
        url = driver.current_url
        print(f"URL: {url}")
        
        # 等待页面加载
        print("\n[3/5] 等待页面加载...")
        time.sleep(3)
        
        # 分析页面源码
        print("\n[4/5] 分析页面源码中的互动数据...")
        page_source = driver.page_source
        
        # 查找点赞数相关的模式
        print("\n  💖 查找点赞数...")
        likes_patterns = [
            (r'"likedCount":\s*(\d+)', 'JSON中的likedCount'),
            (r'"liked_count":\s*(\d+)', 'JSON中的liked_count'),
            (r'"likes":\s*(\d+)', 'JSON中的likes'),
            (r'点赞\s*(\d+)', '文本"点赞"+数字'),
            (r'"interactInfo":\s*{[^}]*"likedCount":\s*["\']?(\d+)', 'interactInfo.likedCount'),
        ]
        
        found_likes = []
        for pattern, desc in likes_patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                for match in matches[:5]:
                    try:
                        num = int(match)
                        if num > 0:
                            found_likes.append((desc, num))
                            print(f"    ✅ [{desc}]: {num}")
                    except:
                        pass
        
        # 查找收藏数相关的模式
        print("\n  ⭐ 查找收藏数...")
        collects_patterns = [
            (r'"collectedCount":\s*(\d+)', 'JSON中的collectedCount'),
            (r'"collected_count":\s*(\d+)', 'JSON中的collected_count'),
            (r'"collects":\s*(\d+)', 'JSON中的collects'),
            (r'收藏\s*(\d+)', '文本"收藏"+数字'),
            (r'"interactInfo":\s*{[^}]*"collectedCount":\s*["\']?(\d+)', 'interactInfo.collectedCount'),
        ]
        
        found_collects = []
        for pattern, desc in collects_patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                for match in matches[:5]:
                    try:
                        num = int(match)
                        if num > 0:
                            found_collects.append((desc, num))
                            print(f"    ✅ [{desc}]: {num}")
                    except:
                        pass
        
        # 查找评论数相关的模式
        print("\n  💬 查找评论数...")
        comments_patterns = [
            (r'"commentCount":\s*(\d+)', 'JSON中的commentCount'),
            (r'"comment_count":\s*(\d+)', 'JSON中的comment_count'),
            (r'"comments":\s*(\d+)', 'JSON中的comments'),
            (r'评论\s*(\d+)', '文本"评论"+数字'),
            (r'"interactInfo":\s*{[^}]*"commentCount":\s*["\']?(\d+)', 'interactInfo.commentCount'),
        ]
        
        found_comments = []
        for pattern, desc in comments_patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                for match in matches[:5]:
                    try:
                        num = int(match)
                        if num > 0:
                            found_comments.append((desc, num))
                            print(f"    ✅ [{desc}]: {num}")
                    except:
                        pass
        
        # 尝试通过CSS选择器查找
        print("\n[5/5] 尝试CSS选择器...")
        
        # 查找包含数字的互动元素
        print("\n  🔍 查找互动栏元素...")
        interaction_selectors = [
            "div[class*='interact']",
            "div[class*='engagement']",
            "div[class*='toolbar']",
            "div[class*='action']",
            "[class*='like']",
            "[class*='collect']",
            "[class*='comment']",
        ]
        
        for selector in interaction_selectors:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, selector)
                if elems:
                    for elem in elems[:3]:
                        text = elem.text.strip()
                        # 查找文本中的数字
                        numbers = re.findall(r'\d+', text)
                        if numbers and text:
                            print(f"    ✅ [{selector}]: {text[:100]}")
            except:
                pass
        
        # 输出总结
        print("\n" + "="*60)
        print("诊断总结")
        print("="*60)
        
        if found_likes:
            print(f"\n✅ 找到 {len(found_likes)} 个可能的点赞数:")
            for desc, num in found_likes[:5]:
                print(f"  • [{desc}]: {num}")
            # 去重并选择最合理的
            unique_likes = list(set([num for _, num in found_likes]))
            print(f"\n💡 去重后的点赞数: {unique_likes}")
            if unique_likes:
                print(f"💡 建议使用: {max(unique_likes)}")
        else:
            print("\n❌ 未找到点赞数")
        
        if found_collects:
            print(f"\n✅ 找到 {len(found_collects)} 个可能的收藏数:")
            for desc, num in found_collects[:5]:
                print(f"  • [{desc}]: {num}")
            unique_collects = list(set([num for _, num in found_collects]))
            print(f"\n💡 去重后的收藏数: {unique_collects}")
            if unique_collects:
                print(f"💡 建议使用: {max(unique_collects)}")
        else:
            print("\n❌ 未找到收藏数")
        
        if found_comments:
            print(f"\n✅ 找到 {len(found_comments)} 个可能的评论数:")
            for desc, num in found_comments[:5]:
                print(f"  • [{desc}]: {num}")
            unique_comments = list(set([num for _, num in found_comments]))
            print(f"\n💡 去重后的评论数: {unique_comments}")
            if unique_comments:
                print(f"💡 建议使用: {max(unique_comments)}")
        else:
            print("\n❌ 未找到评论数")
        
        # 查找完整的interactInfo JSON对象
        print("\n" + "="*60)
        print("查找完整的interactInfo对象")
        print("="*60)
        interact_info_pattern = r'"interactInfo":\s*({[^}]+})'
        interact_matches = re.findall(interact_info_pattern, page_source)
        if interact_matches:
            print("\n✅ 找到interactInfo对象:")
            for i, match in enumerate(interact_matches[:3], 1):
                print(f"\n对象 {i}:")
                print(match[:500])
        
        # 保存诊断报告
        report_file = "interaction_diagnosis.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"URL: {url}\n\n")
            f.write("="*60 + "\n")
            f.write("找到的点赞数:\n")
            f.write("="*60 + "\n")
            for desc, num in found_likes:
                f.write(f"[{desc}]: {num}\n")
            f.write("\n" + "="*60 + "\n")
            f.write("找到的收藏数:\n")
            f.write("="*60 + "\n")
            for desc, num in found_collects:
                f.write(f"[{desc}]: {num}\n")
            f.write("\n" + "="*60 + "\n")
            f.write("找到的评论数:\n")
            f.write("="*60 + "\n")
            for desc, num in found_comments:
                f.write(f"[{desc}]: {num}\n")
        
        print(f"\n📄 完整诊断报告已保存到: {report_file}")
        
    except Exception as e:
        print(f"\n❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键关闭...")

if __name__ == "__main__":
    diagnose_interactions()
    