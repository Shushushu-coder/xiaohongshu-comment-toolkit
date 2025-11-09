"""
数据处理示例脚本
用于分析优化版提取器产生的CSV数据
"""
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import re
from pathlib import Path

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class CommentAnalyzer:
    """评论数据分析器"""
    
    def __init__(self, csv_file):
        """初始化"""
        self.csv_file = csv_file
        self.df = None
        self.load_data()
    
    def load_data(self):
        """加载数据"""
        try:
            self.df = pd.read_csv(self.csv_file, encoding='utf-8-sig')
            print(f"✅ 成功加载数据: {len(self.df)} 条评论")
            print(f"📊 数据列: {list(self.df.columns)}")
        except Exception as e:
            print(f"❌ 加载失败: {e}")
    
    def basic_stats(self):
        """基础统计"""
        print("\n" + "="*60)
        print("📊 基础统计信息")
        print("="*60)
        
        print(f"\n总评论数: {len(self.df)}")
        print(f"笔记标题: {self.df['note_title'].iloc[0]}")
        print(f"笔记ID: {self.df['note_id'].iloc[0]}")
        
        print(f"\n评论长度统计:")
        print(self.df['content_length'].describe())
        
        print(f"\n点赞数统计:")
        print(self.df['likes'].describe())
        
        # 用户统计
        unique_users = self.df['username'].nunique()
        print(f"\n独立用户数: {unique_users}")
        
        # 时间统计
        time_available = self.df['time'].notna().sum()
        print(f"包含时间信息的评论: {time_available} ({time_available/len(self.df)*100:.1f}%)")
    
    def length_distribution(self):
        """评论长度分布"""
        print("\n" + "="*60)
        print("📏 评论长度分布")
        print("="*60)
        
        short = len(self.df[self.df['content_length'] < 20])
        medium = len(self.df[(self.df['content_length'] >= 20) & (self.df['content_length'] < 100)])
        long = len(self.df[self.df['content_length'] >= 100])
        
        total = len(self.df)
        print(f"\n短评论 (<20字): {short} ({short/total*100:.1f}%)")
        print(f"中等评论 (20-100字): {medium} ({medium/total*100:.1f}%)")
        print(f"长评论 (>100字): {long} ({long/total*100:.1f}%)")
        
        # 可视化
        try:
            plt.figure(figsize=(10, 6))
            plt.hist(self.df['content_length'], bins=30, edgecolor='black')
            plt.xlabel('评论长度（字符数）')
            plt.ylabel('数量')
            plt.title('评论长度分布')
            plt.grid(True, alpha=0.3)
            
            output_dir = Path('data/analysis')
            output_dir.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_dir / 'length_distribution.png', dpi=300, bbox_inches='tight')
            print(f"\n✅ 图表已保存: data/analysis/length_distribution.png")
            plt.close()
        except Exception as e:
            print(f"⚠️ 图表生成失败: {e}")
    
    def top_users(self, n=10):
        """最活跃用户"""
        print("\n" + "="*60)
        print(f"👤 最活跃用户 (Top {n})")
        print("="*60)
        
        user_counts = self.df['username'].value_counts().head(n)
        
        for rank, (user, count) in enumerate(user_counts.items(), 1):
            print(f"{rank}. {user}: {count} 条评论")
    
    def top_liked_comments(self, n=10):
        """最受欢迎评论"""
        print("\n" + "="*60)
        print(f"❤️ 最受欢迎评论 (Top {n})")
        print("="*60)
        
        top_comments = self.df.nlargest(n, 'likes')
        
        for rank, (idx, row) in enumerate(top_comments.iterrows(), 1):
            content = row['content'][:50] + '...' if len(row['content']) > 50 else row['content']
            print(f"\n{rank}. 👤 {row['username']}")
            print(f"   ❤️ {row['likes']} 赞")
            print(f"   💬 {content}")
    
    def keyword_analysis(self, top_n=20):
        """关键词分析（简单版）"""
        print("\n" + "="*60)
        print(f"🔍 关键词分析 (Top {top_n})")
        print("="*60)
        
        # 合并所有评论
        all_text = ' '.join(self.df['content'].astype(str))
        
        # 提取常见词汇（这里使用简单的分词，实际应用建议使用jieba）
        # 简单按空格和标点分割
        words = re.findall(r'[\u4e00-\u9fff]+', all_text)
        
        # 过滤停用词
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', 
                     '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', 
                     '会', '着', '没有', '看', '好', '自己', '这'}
        
        words = [w for w in words if len(w) >= 2 and w not in stopwords]
        
        # 统计词频
        word_counts = Counter(words)
        
        print("\n高频词汇:")
        for rank, (word, count) in enumerate(word_counts.most_common(top_n), 1):
            print(f"{rank:2d}. {word:6s} - {count:3d}次")
        
        # 可视化
        try:
            top_words = word_counts.most_common(15)
            words_list, counts = zip(*top_words)
            
            plt.figure(figsize=(12, 6))
            plt.barh(range(len(words_list)), counts)
            plt.yticks(range(len(words_list)), words_list)
            plt.xlabel('出现次数')
            plt.title('高频词汇分布')
            plt.gca().invert_yaxis()
            
            output_dir = Path('data/analysis')
            plt.savefig(output_dir / 'keyword_frequency.png', dpi=300, bbox_inches='tight')
            print(f"\n✅ 词频图已保存: data/analysis/keyword_frequency.png")
            plt.close()
        except Exception as e:
            print(f"⚠️ 词频图生成失败: {e}")
    
    def sentiment_simple(self):
        """简单情感分析"""
        print("\n" + "="*60)
        print("😊 简单情感分析")
        print("="*60)
        
        # 定义情感词典（简化版）
        positive_words = ['好', '棒', '喜欢', '推荐', '不错', '赞', '优秀', '满意', 
                          '惊喜', '值得', '有效', '完美', '爱了']
        negative_words = ['差', '不好', '失望', '垃圾', '难用', '后悔', '坑', 
                          '烂', '无语', '浪费', '不推荐']
        
        def analyze_sentiment(text):
            text = str(text)
            pos_count = sum(1 for word in positive_words if word in text)
            neg_count = sum(1 for word in negative_words if word in text)
            
            if pos_count > neg_count:
                return 'positive'
            elif neg_count > pos_count:
                return 'negative'
            else:
                return 'neutral'
        
        self.df['sentiment'] = self.df['content'].apply(analyze_sentiment)
        
        sentiment_counts = self.df['sentiment'].value_counts()
        
        print("\n情感分布:")
        for sentiment, count in sentiment_counts.items():
            emoji = {'positive': '😊', 'negative': '😞', 'neutral': '😐'}[sentiment]
            label = {'positive': '积极', 'negative': '消极', 'neutral': '中性'}[sentiment]
            print(f"{emoji} {label}: {count} ({count/len(self.df)*100:.1f}%)")
        
        # 可视化
        try:
            plt.figure(figsize=(8, 6))
            colors = {'positive': '#90EE90', 'negative': '#FFB6C1', 'neutral': '#D3D3D3'}
            sentiment_counts.plot(kind='bar', color=[colors.get(x, 'gray') for x in sentiment_counts.index])
            plt.xlabel('情感类型')
            plt.ylabel('数量')
            plt.title('评论情感分布')
            plt.xticks(rotation=0)
            
            output_dir = Path('data/analysis')
            plt.savefig(output_dir / 'sentiment_distribution.png', dpi=300, bbox_inches='tight')
            print(f"\n✅ 情感分布图已保存: data/analysis/sentiment_distribution.png")
            plt.close()
        except Exception as e:
            print(f"⚠️ 情感图生成失败: {e}")
    
    def export_cleaned_data(self):
        """导出清洗后的数据"""
        print("\n" + "="*60)
        print("💾 导出清洗后数据")
        print("="*60)
        
        # 进一步过滤（可选）
        cleaned = self.df[self.df['content_length'] > 5].copy()
        
        output_dir = Path('data/analysis')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f'cleaned_{Path(self.csv_file).name}'
        cleaned.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ 已导出 {len(cleaned)} 条数据到: {output_file}")
    
    def generate_report(self):
        """生成完整报告"""
        print("\n" + "="*60)
        print("📄 生成完整分析报告")
        print("="*60)
        
        report_content = f"""
╔═══════════════════════════════════════════════════════════╗
║                   数据分析报告                              ║
╚═══════════════════════════════════════════════════════════╝

📌 数据来源
----------------------------------------------------------
文件名: {self.csv_file}
笔记标题: {self.df['note_title'].iloc[0]}
笔记ID: {self.df['note_id'].iloc[0]}

📊 基础统计
----------------------------------------------------------
总评论数: {len(self.df)}
独立用户: {self.df['username'].nunique()}
平均长度: {self.df['content_length'].mean():.1f} 字符
平均点赞: {self.df['likes'].mean():.1f}

📏 长度分布
----------------------------------------------------------
短评论 (<20字): {len(self.df[self.df['content_length'] < 20])} ({len(self.df[self.df['content_length'] < 20])/len(self.df)*100:.1f}%)
中等评论 (20-100字): {len(self.df[(self.df['content_length'] >= 20) & (self.df['content_length'] < 100)])} ({len(self.df[(self.df['content_length'] >= 20) & (self.df['content_length'] < 100)])/len(self.df)*100:.1f}%)
长评论 (>100字): {len(self.df[self.df['content_length'] >= 100])} ({len(self.df[self.df['content_length'] >= 100])/len(self.df)*100:.1f}%)

❤️ 互动统计
----------------------------------------------------------
最高点赞数: {self.df['likes'].max()}
最低点赞数: {self.df['likes'].min()}
点赞总数: {self.df['likes'].sum()}

⏰ 生成时间
----------------------------------------------------------
{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

═══════════════════════════════════════════════════════════
"""
        
        output_dir = Path('data/analysis')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = output_dir / 'analysis_report.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(report_content)
        print(f"\n✅ 报告已保存: {report_file}")
    
    def run_full_analysis(self):
        """运行完整分析"""
        print("\n" + "="*60)
        print("🚀 开始完整数据分析")
        print("="*60)
        
        self.basic_stats()
        self.length_distribution()
        self.top_users()
        self.top_liked_comments()
        self.keyword_analysis()
        self.sentiment_simple()
        self.export_cleaned_data()
        self.generate_report()
        
        print("\n" + "="*60)
        print("✅ 分析完成！所有结果保存在 data/analysis/ 目录")
        print("="*60)


def main():
    """主函数"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║           评论数据分析工具                                ║
    ║           Comment Data Analyzer                         ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # 查找最新的CSV文件
    data_dir = Path('data/comments')
    
    if not data_dir.exists():
        print("❌ 未找到 data/comments 目录")
        print("请先运行 comment_extractor_optimized.py 采集数据")
        input("\n按回车退出...")
        return
    
    csv_files = list(data_dir.glob('comments_*.csv'))
    
    if not csv_files:
        print("❌ 未找到CSV文件")
        print("请先运行 comment_extractor_optimized.py 采集数据")
        input("\n按回车退出...")
        return
    
    # 按修改时间排序，取最新的
    csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print("\n📁 找到以下CSV文件:")
    for i, file in enumerate(csv_files[:5], 1):  # 只显示最新的5个
        print(f"{i}. {file.name}")
    
    choice = input("\n请选择要分析的文件（输入数字，直接回车选择最新的）: ").strip()
    
    if not choice:
        selected_file = csv_files[0]
    else:
        try:
            idx = int(choice) - 1
            selected_file = csv_files[idx]
        except:
            print("❌ 无效选择，使用最新文件")
            selected_file = csv_files[0]
    
    print(f"\n✓ 选择文件: {selected_file.name}")
    
    # 创建分析器并运行
    analyzer = CommentAnalyzer(selected_file)
    analyzer.run_full_analysis()
    
    input("\n✅ 按回车退出...")


if __name__ == "__main__":
    main()