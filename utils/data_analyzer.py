"""
数据分析工具
用于分析收集到的评论数据
"""
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import jieba
import jieba.analyse
from wordcloud import WordCloud


class DataAnalyzer:
    """数据分析器"""
    
    def __init__(self, comments_file, users_file=None):
        """
        初始化
        
        参数:
            comments_file: 评论数据文件路径
            users_file: 用户数据文件路径（可选）
        """
        self.comments_df = pd.read_csv(comments_file)
        self.users_df = pd.read_csv(users_file) if users_file else None
        
        print(f"已加载评论数据: {len(self.comments_df)} 条")
        if self.users_df is not None:
            print(f"已加载用户数据: {len(self.users_df)} 个")
    
    def basic_statistics(self):
        """基础统计分析"""
        print("\n" + "=" * 60)
        print("基础统计信息")
        print("=" * 60)
        
        # 评论统计
        print("\n【评论统计】")
        print(f"总评论数: {len(self.comments_df)}")
        print(f"平均评论长度: {self.comments_df['content'].str.len().mean():.1f} 字")
        print(f"最长评论: {self.comments_df['content'].str.len().max()} 字")
        print(f"最短评论: {self.comments_df['content'].str.len().min()} 字")
        
        if 'like_count' in self.comments_df.columns:
            print(f"\n平均点赞数: {self.comments_df['like_count'].mean():.1f}")
            print(f"点赞中位数: {self.comments_df['like_count'].median():.1f}")
            print(f"最高点赞: {self.comments_df['like_count'].max()}")
        
        # 用户统计
        if self.users_df is not None:
            print("\n【用户统计】")
            print(f"总用户数: {len(self.users_df)}")
            if 'follower_count' in self.users_df.columns:
                print(f"平均粉丝数: {self.users_df['follower_count'].mean():.1f}")
                print(f"平均获赞数: {self.users_df['like_count'].mean():.1f}")
            
            if 'final_score' in self.users_df.columns:
                print(f"\n平均可信度得分: {self.users_df['final_score'].mean():.3f}")
                print(f"可信度得分中位数: {self.users_df['final_score'].median():.3f}")
    
    def sentiment_analysis(self):
        """情感分析（简单版）"""
        print("\n" + "=" * 60)
        print("情感分析")
        print("=" * 60)
        
        # 定义情感词典（简化版）
        positive_words = [
            '好用', '喜欢', '推荐', '满意', '棒', '赞', '不错', '完美', 
            '惊喜', '温和', '好闻', '舒服', '有效', '值得', '爱了'
        ]
        negative_words = [
            '不好', '失望', '差', '坑', '假', '骗', '后悔', '难用',
            '过敏', '刺激', '油腻', '不值', '退货'
        ]
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for comment in self.comments_df['content']:
            pos_score = sum(1 for word in positive_words if word in comment)
            neg_score = sum(1 for word in negative_words if word in comment)
            
            if pos_score > neg_score:
                positive_count += 1
            elif neg_score > pos_score:
                negative_count += 1
            else:
                neutral_count += 1
        
        total = len(self.comments_df)
        print(f"正面评论: {positive_count} ({positive_count/total*100:.1f}%)")
        print(f"负面评论: {negative_count} ({negative_count/total*100:.1f}%)")
        print(f"中性评论: {neutral_count} ({neutral_count/total*100:.1f}%)")
    
    def keyword_extraction(self, top_n=20):
        """关键词提取"""
        print("\n" + "=" * 60)
        print(f"高频关键词 (Top {top_n})")
        print("=" * 60)
        
        # 合并所有评论
        all_text = ' '.join(self.comments_df['content'].tolist())
        
        # 使用TF-IDF提取关键词
        keywords = jieba.analyse.extract_tags(all_text, topK=top_n, withWeight=True)
        
        for idx, (word, weight) in enumerate(keywords, 1):
            print(f"{idx:2d}. {word:10s} (权重: {weight:.4f})")
        
        return keywords
    
    def generate_wordcloud(self, output_file='wordcloud.png'):
        """生成词云"""
        print(f"\n生成词云图: {output_file}")
        
        # 合并所有评论
        all_text = ' '.join(self.comments_df['content'].tolist())
        
        # 分词
        words = jieba.cut(all_text)
        
        # 过滤停用词
        stopwords = set(['的', '了', '是', '我', '你', '也', '有', '在', '就', '都', '不', '和'])
        filtered_words = [word for word in words if len(word) > 1 and word not in stopwords]
        text = ' '.join(filtered_words)
        
        # 生成词云
        wc = WordCloud(
            font_path='simhei.ttf',  # 需要中文字体
            width=1200,
            height=800,
            background_color='white',
            max_words=100
        )
        
        try:
            wc.generate(text)
            wc.to_file(output_file)
            print(f"✓ 词云已保存")
        except Exception as e:
            print(f"✗ 词云生成失败: {e}")
            print("  提示: 需要安装中文字体")
    
    def credibility_distribution(self):
        """可信度得分分布"""
        if self.users_df is None or 'final_score' not in self.users_df.columns:
            print("没有可信度评分数据")
            return
        
        print("\n" + "=" * 60)
        print("用户可信度分布")
        print("=" * 60)
        
        scores = self.users_df['final_score']
        
        print(f"平均分: {scores.mean():.3f}")
        print(f"中位数: {scores.median():.3f}")
        print(f"标准差: {scores.std():.3f}")
        print(f"\n得分区间分布:")
        print(f"  0.0-0.2: {(scores < 0.2).sum()} 人 ({(scores < 0.2).sum()/len(scores)*100:.1f}%)")
        print(f"  0.2-0.4: {((scores >= 0.2) & (scores < 0.4)).sum()} 人")
        print(f"  0.4-0.6: {((scores >= 0.4) & (scores < 0.6)).sum()} 人")
        print(f"  0.6-0.8: {((scores >= 0.6) & (scores < 0.8)).sum()} 人")
        print(f"  0.8-1.0: {(scores >= 0.8).sum()} 人")
    
    def export_report(self, output_file='analysis_report.txt'):
        """导出分析报告"""
        import sys
        from io import StringIO
        
        # 重定向输出
        old_stdout = sys.stdout
        sys.stdout = report_output = StringIO()
        
        # 执行所有分析
        self.basic_statistics()
        self.sentiment_analysis()
        self.keyword_extraction()
        self.credibility_distribution()
        
        # 恢复输出
        sys.stdout = old_stdout
        
        # 保存报告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_output.getvalue())
        
        print(f"\n分析报告已保存: {output_file}")


# 使用示例
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python data_analyzer.py <评论文件.csv> [用户文件.csv]")
        sys.exit(1)
    
    comments_file = sys.argv[1]
    users_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    analyzer = DataAnalyzer(comments_file, users_file)
    
    # 执行分析
    analyzer.basic_statistics()
    analyzer.sentiment_analysis()
    analyzer.keyword_extraction()
    analyzer.credibility_distribution()
    
    # 导出报告
    analyzer.export_report()
    
    # 生成词云（可选）
    # analyzer.generate_wordcloud()