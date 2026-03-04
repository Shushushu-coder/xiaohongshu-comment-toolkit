"""
小红书评论数据整合工具（简化版）
功能：
1. 整合多个帖子的评论数据
2. 输出三个JSON文件：评论、标题、元数据
"""

import json
import re
from pathlib import Path
from datetime import datetime


class DataAggregator:
    """数据整合器"""
    
    def __init__(self, raw_data_dir="data/comments"):
        self.raw_dir = Path(raw_data_dir)
        self.output_dir = Path("data/aggregated")
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.posts_data = []
        self.all_comments = []
        
        print(f"📂 原始数据目录: {self.raw_dir.absolute()}")
        print(f"📂 输出数据目录: {self.output_dir.absolute()}")
    
    def scan_raw_data(self):
        """扫描原始数据文件"""
        print("\n🔍 扫描原始数据文件...")
        
        json_files = list(self.raw_dir.glob("comments_*.json"))
        
        if not json_files:
            print(f"❌ 未找到JSON文件在 {self.raw_dir.absolute()}")
            return []
        
        print(f"✅ 找到 {len(json_files)} 个数据文件")
        
        for f in json_files[:5]:
            print(f"   - {f.name}")
        if len(json_files) > 5:
            print(f"   ... 还有 {len(json_files) - 5} 个文件")
        
        return json_files
    
    def load_data(self):
        """加载所有原始数据"""
        print("\n📥 加载数据...")
        
        json_files = self.scan_raw_data()
        
        if not json_files:
            return False
        
        loaded_count = 0
        failed_count = 0
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 提取帖子信息
                note_info = data.get('note_info', {})
                comments = data.get('comments', [])
                
                post_data = {
                    'post_id': note_info.get('note_id', f'unknown_{loaded_count}'),
                    'title': note_info.get('note_title', '未知标题'),
                    'author': note_info.get('author', '未知作者'),
                    'url': note_info.get('note_url', ''),
                    'comment_count': len(comments),
                    'collected_at': data.get('collected_at', ''),
                    'source_file': json_file.name,
                    'comments': comments  # 保留原始评论数据
                }
                
                self.posts_data.append(post_data)
                self.all_comments.extend(comments)
                
                loaded_count += 1
                
            except Exception as e:
                print(f"⚠️ 加载失败: {json_file.name} - {e}")
                failed_count += 1
        
        print(f"\n✅ 成功加载: {loaded_count} 个文件")
        if failed_count > 0:
            print(f"⚠️ 失败: {failed_count} 个文件")
        
        print(f"📊 总计: {len(self.posts_data)} 个帖子, {len(self.all_comments)} 条评论")
        
        return True
    
    def save_comments_json(self):
        """保存评论JSON文件 - 按帖子ID分组"""
        print("\n💾 [1/3] 保存评论数据...")
        
        comments_data = {}
        
        for post in self.posts_data:
            post_id = post['post_id']
            
            # 整理评论数据，保留对话结构
            comments_list = []
            for comment in post['comments']:
                content = comment.get('content', '')
                
                # 计算评论长度，忽略 {回复【用户ID】：} 格式
                # 使用正则表达式移除回复前缀
                cleaned_content = re.sub(r'回复.*?[：:]', '', content).strip()
                comment_length = len(cleaned_content)
                
                comment_item = {
                    'comment_id': comment.get('comment_id', ''),
                    'username': comment.get('username', ''),
                    'content': content,
                    'length': comment_length,
                    'likes': comment.get('likes', 0),
                }
                
                # 如果有回复/对话，也包含进来
                if 'replies' in comment and comment['replies']:
                    comment_item['replies'] = comment['replies']
                elif 'sub_comments' in comment and comment['sub_comments']:
                    comment_item['replies'] = comment['sub_comments']
                
                comments_list.append(comment_item)
            
            comments_data[post_id] = comments_list
        
        # 保存文件
        output_file = self.output_dir / "comments.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comments_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已保存: {output_file.name}")
        print(f"   包含 {len(comments_data)} 个帖子的评论数据")
        
        return output_file
    
    def save_titles_json(self):
        """保存标题JSON文件"""
        print("\n💾 [2/3] 保存标题数据...")
        
        titles_data = {}
        
        for post in self.posts_data:
            titles_data[post['post_id']] = post['title']
        
        # 保存文件
        output_file = self.output_dir / "titles.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(titles_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已保存: {output_file.name}")
        print(f"   包含 {len(titles_data)} 个帖子标题")
        
        return output_file
    
    def save_metadata_json(self):
        """保存元数据JSON文件"""
        print("\n💾 [3/3] 保存元数据...")
        
        # 统计信息
        total_likes = sum(c.get('likes', 0) for c in self.all_comments)
        avg_comment_length = (
            sum(len(c.get('content', '')) for c in self.all_comments) / len(self.all_comments) 
            if self.all_comments else 0
        )
        
        # 构建元数据
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'statistics': {
                'total_posts': len(self.posts_data),
                'total_comments': len(self.all_comments),
                'total_likes': total_likes,
                'avg_comment_length': round(avg_comment_length, 2)
            },
            'posts': []
        }
        
        # 添加每个帖子的元数据
        for post in self.posts_data:
            post_comments = post['comments']
            post_likes = sum(c.get('likes', 0) for c in post_comments)
            
            post_meta = {
                'post_id': post['post_id'],
                'title': post['title'],
                'author': post['author'],
                'url': post['url'],
                'comment_count': len(post_comments),
                'total_likes': post_likes,
                'collected_at': post['collected_at'],
                'source_file': post['source_file']
            }
            
            metadata['posts'].append(post_meta)
        
        # 按评论数排序
        metadata['posts'].sort(key=lambda x: x['comment_count'], reverse=True)
        
        # 保存文件
        output_file = self.output_dir / "metadata.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已保存: {output_file.name}")
        print(f"   包含统计信息和 {len(metadata['posts'])} 个帖子的元数据")
        
        return output_file
    
    def print_summary(self):
        """打印摘要信息"""
        print("\n" + "="*60)
        print("📊 数据整合摘要")
        print("="*60)
        
        total_likes = sum(c.get('likes', 0) for c in self.all_comments)
        avg_comment_length = (
            sum(len(c.get('content', '')) for c in self.all_comments) / len(self.all_comments) 
            if self.all_comments else 0
        )
        
        print(f"\n基本统计:")
        print(f"  • 总帖子数:     {len(self.posts_data)} 个")
        print(f"  • 总评论数:     {len(self.all_comments)} 条")
        print(f"  • 总点赞数:     {total_likes}")
        print(f"  • 平均评论长度: {avg_comment_length:.1f} 字符")
        
        print(f"\n生成文件:")
        print(f"  • {self.output_dir}/comments.json   - 评论数据（按帖子ID分组）")
        print(f"  • {self.output_dir}/titles.json     - 标题数据（post_id: 标题）")
        print(f"  • {self.output_dir}/metadata.json   - 元数据（统计信息）")
        
        print("\n评论最多的帖子 (Top 5):")
        sorted_posts = sorted(self.posts_data, key=lambda x: x['comment_count'], reverse=True)
        for i, post in enumerate(sorted_posts[:5], 1):
            print(f"  {i}. {post['title'][:40]:<40} | {post['comment_count']:4d}条")
        
        print("\n" + "="*60)
    
    def aggregate_all(self):
        """执行完整的数据整合流程"""
        print("\n" + "="*60)
        print("开始数据整合")
        print("="*60)
        
        # 加载数据
        if not self.load_data():
            print("\n❌ 没有数据可整合")
            return False
        
        # 保存三个JSON文件
        self.save_comments_json()
        self.save_titles_json()
        self.save_metadata_json()
        
        # 打印摘要
        self.print_summary()
        
        print("\n✅ 数据整合完成！")
        print(f"📂 输出目录: {self.output_dir.absolute()}")
        
        return True


def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        小红书评论数据整合工具（简化版）                    ║
║        Data Aggregator for Xiaohongshu Comments         ║
║                                                          ║
║   输出文件:                                               ║
║   • comments.json  - 评论数据（含对话）                   ║
║   • titles.json    - 标题数据                            ║
║   • metadata.json  - 元数据（统计信息）                   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # 获取原始数据目录
    default_dir = "data/comments"
    print(f"\n请输入原始数据目录 (默认: {default_dir})")
    raw_dir = input("路径: ").strip() or default_dir
    
    # 创建整合器
    aggregator = DataAggregator(raw_dir)
    
    # 执行整合
    success = aggregator.aggregate_all()
    
    if success:
        print("\n💡 使用建议:")
        print("  • comments.json - 用于分析评论内容和对话")
        print("  • titles.json   - 快速查找帖子标题")
        print("  • metadata.json - 查看统计信息和帖子概览")
    
    input("\n按回车退出...")


if __name__ == "__main__":

        
    main()