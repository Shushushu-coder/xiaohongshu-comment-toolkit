#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长结构评论提取器
功能定位：与对话提取器形成互补
- 对话提取器：提取多人交互的对话链（a/b/c格式）
- 长评论提取器：提取单人深度长评论（段落式结构）

核心功能：
1. 识别和提取高质量长评论
2. 自动分段和结构化（观点、体验、建议等）
3. 提取关键信息点（效果、成分、价格、使用感受等）
4. 智能摘要和标签生成
5. 品牌/产品替换
6. 质量评分和排序
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class CommentAnalysis:
    """评论分析结果"""
    original_text: str
    cleaned_text: str
    length: int
    likes: int
    username: str
    
    # 结构化信息
    segments: List[Dict] = field(default_factory=list)  # 分段
    key_points: List[str] = field(default_factory=list)  # 关键信息点
    
    # 自动识别的内容类型
    has_product_review: bool = False  # 产品评价
    has_usage_experience: bool = False  # 使用体验
    has_comparison: bool = False  # 对比评测
    has_recommendation: bool = False  # 推荐建议
    has_warning: bool = False  # 警告/避坑
    
    # 情感和质量
    sentiment: str = 'neutral'  # positive/negative/neutral/mixed
    quality_score: float = 0.0  # 0-100分
    
    # 标签
    tags: List[str] = field(default_factory=list)
    
    # 替换后的文本
    formatted_text: str = ''


class LongCommentExtractor:
    """长结构评论提取器"""
    
    def __init__(self, min_length=50, mode='quality'):
        """
        Args:
            min_length: 最短长度阈值（字符数）
            mode: 'quality'(质量优先) / 'quantity'(数量优先) / 'comprehensive'(全面)
        """
        self.min_length = min_length
        self.mode = mode
        
        # 品牌/产品映射（与对话提取器保持一致）
        self.brand_mapping = {
            '雪绒花积雪草': 'A1',
            '美白奶罐': 'A2',
            '谷雨': 'B',
            '谷屿': 'B',
            '小奶罐': 'A2',
            '奶罐': 'A2',
            '光感水': 'A3',
            '光感': 'A3',
            '溪木源': 'B2',
            '珀莱雅': 'B9',
            '薇诺娜': 'B24',
            '谢馥春': 'B25',
            '仙人掌': 'A6',
            '雪肌': 'A4',
            '次抛': 'A18',
            '奶片面膜': 'A20',
            '玫瑰水': 'A21',
            '源力面霜': 'A19',
            '兰蔻': 'B5',
            '雅诗兰黛': 'B6',
            '欧莱雅': 'B7',
            '资生堂': 'B8',
            '科颜氏': 'B10',
            '兰芝': 'B11',
            '小红书': 'D',
            '淘宝': 'D',
            '天猫': 'D',
            '京东': 'D',
            '抖音': 'D',
            '拼多多': 'D',
        }
        
        # 按长度排序
        self.brand_mapping = dict(sorted(
            self.brand_mapping.items(),
            key=lambda x: len(x[0]),
            reverse=True
        ))
        
        # 内容类型识别关键词
        self.content_patterns = {
            'product_review': [
                '用了', '试了', '买了', '入手', '效果', '质地', '味道', '包装',
                '成分', '配方', '功效', '适合', '不适合'
            ],
            'usage_experience': [
                '第一次', '刚开始', '用了.*天', '用了.*周', '用了.*月', '用完',
                '早上', '晚上', '白天', '每天', '坚持', '使用方法', '用法'
            ],
            'comparison': [
                '相比', '对比', '比.*好', '比.*差', '和.*一起', '换成', '之前用',
                '更', '没有.*好', '不如', 'vs', 'PK'
            ],
            'recommendation': [
                '推荐', '建议', '可以试试', '值得', '适合.*皮', '如果.*的话',
                '我觉得', '个人认为', '强烈推荐', '不推荐'
            ],
            'warning': [
                '注意', '小心', '千万', '不要', '避免', '慎用', '踩雷', '后悔',
                '翻车', '不建议', '警告', '容易.*长痘', '会.*过敏'
            ]
        }
        
        # 情感关键词
        self.positive_keywords = [
            '好用', '推荐', '白了', '效果好', '不错', '满意', '喜欢', '爱了',
            '变白', '提亮', '清爽', '温和', '舒服', '吸收快', '性价比高',
            '值得', '回购', '无限回购'
        ]
        
        self.negative_keywords = [
            '长痘', '过敏', '闷痘', '闭口', '粉刺', '刺激', '不好用', '难用',
            '后悔', '退了', '拉', '黏腻', '油腻', '假滑', '搓泥', '不吸收',
            '鸡肋', '踩雷', '翻车', '智商税'
        ]
        
        # 关键信息提取模式
        self.info_patterns = {
            'skin_type': r'(油皮|干皮|混油|混干|敏感肌|痘痘肌|中性皮)',
            'duration': r'用了?([一二三四五六七八九十\d]+)(天|周|个?月|年)',
            'price': r'(\d+).*?元|价格.*?(\d+)',
            'effect': r'(美白|提亮|补水|保湿|控油|祛痘|抗老|紧致|淡斑)',
            'texture': r'(清爽|黏腻|油腻|厚重|轻薄|水润|滋润)',
            'season': r'(春天|夏天|秋天|冬天|春季|夏季|秋季|冬季)',
        }
        
        # 统计
        self.stats = {
            'total_comments': 0,
            'long_comments': 0,
            'by_quality_tier': defaultdict(int),
            'by_content_type': defaultdict(int),
            'by_sentiment': defaultdict(int),
        }
    
    def clean_content(self, content: str) -> str:
        """清洗文本"""
        # 移除emoji
        content = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+', '', content)
        # 移除小红书表情
        content = re.sub(r'\[.*?R\]', '', content)
        content = re.sub(r'\[.*?\]', '', content)
        # 统一标点和空格
        content = re.sub(r'\s+', ' ', content).strip()
        return content
    
    def replace_brands(self, content: str) -> str:
        """替换品牌/产品"""
        result = content
        for original, replacement in self.brand_mapping.items():
            result = result.replace(original, replacement)
        return result
    
    def segment_comment(self, text: str) -> List[Dict]:
        """
        智能分段：将长评论分成逻辑段落
        """
        segments = []
        
        # 按句号、问号、感叹号分句
        sentences = re.split(r'[。！？\n]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return segments
        
        # 分段策略：根据语义相关性分组
        current_segment = {
            'type': 'intro',  # intro/experience/effect/comparison/conclusion
            'content': [],
            'key_info': []
        }
        
        segment_markers = {
            'experience': ['用了', '开始', '刚', '第一次', '试了'],
            'effect': ['效果', '感觉', '变化', '白了', '改善'],
            'comparison': ['相比', '对比', '和', '比'],
            'recommendation': ['推荐', '建议', '可以', '适合'],
            'conclusion': ['总的来说', '总之', '整体', '综合']
        }
        
        for sentence in sentences:
            # 判断句子类型
            segment_type = 'general'
            for stype, markers in segment_markers.items():
                if any(marker in sentence for marker in markers):
                    segment_type = stype
                    break
            
            # 如果类型变化，创建新段落
            if segment_type != 'general' and current_segment['content'] and segment_type != current_segment['type']:
                if current_segment['content']:
                    current_segment['content'] = '，'.join(current_segment['content'])
                    segments.append(current_segment)
                current_segment = {
                    'type': segment_type,
                    'content': [],
                    'key_info': []
                }
            
            current_segment['content'].append(sentence)
            current_segment['type'] = segment_type if segment_type != 'general' else current_segment['type']
        
        # 添加最后一个段落
        if current_segment['content']:
            current_segment['content'] = '，'.join(current_segment['content'])
            segments.append(current_segment)
        
        return segments
    
    def extract_key_points(self, text: str) -> List[str]:
        """
        提取关键信息点
        """
        key_points = []
        
        # 提取结构化信息
        for info_type, pattern in self.info_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                if info_type == 'skin_type':
                    key_points.append(f"肤质：{matches[0]}")
                elif info_type == 'duration':
                    key_points.append(f"使用时长：{matches[0][0]}{matches[0][1]}")
                elif info_type == 'price':
                    price = matches[0][0] if matches[0][0] else matches[0][1]
                    key_points.append(f"价格：{price}元")
                elif info_type == 'effect':
                    key_points.append(f"功效：{'/'.join(set(matches))}")
                elif info_type == 'texture':
                    key_points.append(f"质地：{matches[0]}")
                elif info_type == 'season':
                    key_points.append(f"季节：{matches[0]}")
        
        # 提取产品提及
        products_mentioned = []
        for brand in self.brand_mapping.keys():
            if brand in text and len(brand) > 1:  # 避免单字误匹配
                products_mentioned.append(brand)
        
        if products_mentioned:
            key_points.append(f"产品：{'/'.join(set(products_mentioned[:3]))}")  # 最多3个
        
        return key_points
    
    def identify_content_types(self, text: str) -> Dict[str, bool]:
        """
        识别评论包含的内容类型
        """
        types = {}
        
        for content_type, keywords in self.content_patterns.items():
            has_type = False
            for keyword in keywords:
                if re.search(keyword, text):
                    has_type = True
                    break
            types[content_type] = has_type
        
        return types
    
    def analyze_sentiment(self, text: str) -> str:
        """
        情感分析
        """
        pos_count = sum(1 for kw in self.positive_keywords if kw in text)
        neg_count = sum(1 for kw in self.negative_keywords if kw in text)
        
        if pos_count > 0 and neg_count > 0:
            # 既有正面又有负面
            if abs(pos_count - neg_count) <= 1:
                return 'mixed'  # 混合评价
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        return 'neutral'
    
    def calculate_quality_score(self, comment: Dict, analysis: CommentAnalysis) -> float:
        """
        计算评论质量分数（0-100）
        
        评分维度：
        1. 长度分 (0-20分)
        2. 点赞数分 (0-20分)
        3. 信息丰富度分 (0-25分)
        4. 结构完整度分 (0-20分)
        5. 独特性分 (0-15分)
        """
        score = 0.0
        
        # 1. 长度分（50-200字为最佳）
        length = analysis.length
        if length >= 200:
            score += 20
        elif length >= 150:
            score += 18
        elif length >= 100:
            score += 15
        elif length >= 50:
            score += 10
        
        # 2. 点赞数分（考虑受欢迎程度）
        likes = analysis.likes
        if likes >= 100:
            score += 20
        elif likes >= 50:
            score += 18
        elif likes >= 20:
            score += 15
        elif likes >= 10:
            score += 12
        elif likes >= 5:
            score += 8
        elif likes >= 1:
            score += 5
        
        # 3. 信息丰富度分（关键信息点越多越好）
        key_points_count = len(analysis.key_points)
        if key_points_count >= 5:
            score += 25
        elif key_points_count >= 4:
            score += 20
        elif key_points_count >= 3:
            score += 15
        elif key_points_count >= 2:
            score += 10
        elif key_points_count >= 1:
            score += 5
        
        # 4. 结构完整度分（包含多种内容类型）
        content_type_count = sum([
            analysis.has_product_review,
            analysis.has_usage_experience,
            analysis.has_comparison,
            analysis.has_recommendation,
            analysis.has_warning
        ])
        if content_type_count >= 4:
            score += 20
        elif content_type_count >= 3:
            score += 15
        elif content_type_count >= 2:
            score += 10
        elif content_type_count >= 1:
            score += 5
        
        # 5. 独特性分（有对比、建议等深度内容）
        if analysis.has_comparison:
            score += 5
        if analysis.has_recommendation:
            score += 5
        if len(analysis.segments) >= 3:  # 有明确分段
            score += 5
        
        return min(score, 100.0)
    
    def generate_tags(self, analysis: CommentAnalysis) -> List[str]:
        """
        生成标签
        """
        tags = []
        
        # 情感标签
        if analysis.sentiment == 'positive':
            tags.append('好评')
        elif analysis.sentiment == 'negative':
            tags.append('差评')
        elif analysis.sentiment == 'mixed':
            tags.append('中性评价')
        
        # 质量标签
        if analysis.quality_score >= 80:
            tags.append('高质量')
        elif analysis.quality_score >= 60:
            tags.append('中等质量')
        
        # 内容类型标签
        if analysis.has_product_review:
            tags.append('产品评测')
        if analysis.has_usage_experience:
            tags.append('使用体验')
        if analysis.has_comparison:
            tags.append('对比测评')
        if analysis.has_recommendation:
            tags.append('购买建议')
        if analysis.has_warning:
            tags.append('避坑指南')
        
        # 长度标签
        if analysis.length >= 200:
            tags.append('长评')
        elif analysis.length >= 100:
            tags.append('中评')
        
        # 受欢迎度标签
        if analysis.likes >= 50:
            tags.append('高赞')
        elif analysis.likes >= 10:
            tags.append('热门')
        
        return tags
    
    def analyze_comment(self, comment: Dict) -> Optional[CommentAnalysis]:
        """
        分析单条评论
        """
        # 清洗文本
        original_text = comment['content']
        cleaned_text = self.clean_content(original_text)
        
        # 长度过滤
        if len(cleaned_text) < self.min_length:
            return None
        
        # 创建分析对象
        analysis = CommentAnalysis(
            original_text=original_text,
            cleaned_text=cleaned_text,
            length=len(cleaned_text),
            likes=comment.get('likes', 0),
            username=comment.get('username', 'anonymous')
        )
        
        # 分段
        analysis.segments = self.segment_comment(cleaned_text)
        
        # 提取关键信息
        analysis.key_points = self.extract_key_points(cleaned_text)
        
        # 识别内容类型
        content_types = self.identify_content_types(cleaned_text)
        analysis.has_product_review = content_types['product_review']
        analysis.has_usage_experience = content_types['usage_experience']
        analysis.has_comparison = content_types['comparison']
        analysis.has_recommendation = content_types['recommendation']
        analysis.has_warning = content_types['warning']
        
        # 情感分析
        analysis.sentiment = self.analyze_sentiment(cleaned_text)
        
        # 质量评分
        analysis.quality_score = self.calculate_quality_score(comment, analysis)
        
        # 生成标签
        analysis.tags = self.generate_tags(analysis)
        
        # 品牌替换后的文本
        analysis.formatted_text = self.replace_brands(cleaned_text)
        
        return analysis
    
    def extract_from_data(self, comments_data: Dict) -> List[CommentAnalysis]:
        """
        从评论数据中提取长评论
        """
        all_analyses = []
        
        for topic_id, comments in comments_data.items():
            print(f"\n处理话题: {topic_id} ({len(comments)} 条评论)")
            
            self.stats['total_comments'] += len(comments)
            
            topic_analyses = []
            for comment in comments:
                analysis = self.analyze_comment(comment)
                if analysis:
                    topic_analyses.append(analysis)
            
            print(f"  提取长评论: {len(topic_analyses)} 条")
            all_analyses.extend(topic_analyses)
            self.stats['long_comments'] += len(topic_analyses)
        
        # 排序：按质量分数降序
        all_analyses.sort(key=lambda x: x.quality_score, reverse=True)
        
        # 统计
        for analysis in all_analyses:
            # 质量分级
            if analysis.quality_score >= 80:
                self.stats['by_quality_tier']['高质量(80+)'] += 1
            elif analysis.quality_score >= 60:
                self.stats['by_quality_tier']['中等质量(60-79)'] += 1
            else:
                self.stats['by_quality_tier']['一般质量(60-)'] += 1
            
            # 情感分布
            self.stats['by_sentiment'][analysis.sentiment] += 1
            
            # 内容类型
            if analysis.has_product_review:
                self.stats['by_content_type']['产品评测'] += 1
            if analysis.has_usage_experience:
                self.stats['by_content_type']['使用体验'] += 1
            if analysis.has_comparison:
                self.stats['by_content_type']['对比测评'] += 1
            if analysis.has_recommendation:
                self.stats['by_content_type']['购买建议'] += 1
            if analysis.has_warning:
                self.stats['by_content_type']['避坑指南'] += 1
        
        return all_analyses
    
    def format_output(self, analyses: List[CommentAnalysis], top_n: int = None) -> str:
        """
        格式化输出
        """
        if top_n:
            analyses = analyses[:top_n]
        
        lines = []
        lines.append("=" * 70)
        lines.append("长结构评论提取结果")
        lines.append("=" * 70)
        lines.append("")
        
        for i, analysis in enumerate(analyses, 1):
            lines.append(f"【评论 {i}】")
            lines.append(f"质量分数: {analysis.quality_score:.1f}/100")
            lines.append(f"点赞数: {analysis.likes}")
            lines.append(f"长度: {analysis.length}字")
            lines.append(f"情感: {analysis.sentiment}")
            lines.append(f"标签: {', '.join(analysis.tags)}")
            
            if analysis.key_points:
                lines.append(f"关键信息: {' | '.join(analysis.key_points)}")
            
            lines.append("")
            lines.append("【原文】")
            lines.append(analysis.cleaned_text)
            lines.append("")
            lines.append("【品牌替换后】")
            lines.append(analysis.formatted_text)
            
            if analysis.segments and len(analysis.segments) > 1:
                lines.append("")
                lines.append("【结构分析】")
                for j, segment in enumerate(analysis.segments, 1):
                    lines.append(f"  段落{j} ({segment['type']}): {segment['content'][:50]}...")
            
            lines.append("")
            lines.append("-" * 70)
            lines.append("")
        
        return '\n'.join(lines)
    
    def generate_report(self) -> str:
        """
        生成统计报告
        """
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append("长评论提取报告")
        lines.append("=" * 70)
        
        lines.append(f"\n【基本统计】")
        lines.append(f"  总评论数: {self.stats['total_comments']}")
        lines.append(f"  长评论数: {self.stats['long_comments']}")
        if self.stats['total_comments'] > 0:
            lines.append(f"  提取率: {self.stats['long_comments']/self.stats['total_comments']*100:.1f}%")
        
        lines.append(f"\n【质量分布】")
        for tier, count in sorted(self.stats['by_quality_tier'].items(), reverse=True):
            pct = count / max(self.stats['long_comments'], 1) * 100
            lines.append(f"  {tier}: {count} ({pct:.1f}%)")
        
        lines.append(f"\n【情感分布】")
        for sentiment, count in sorted(self.stats['by_sentiment'].items(), key=lambda x: x[1], reverse=True):
            pct = count / max(self.stats['long_comments'], 1) * 100
            lines.append(f"  {sentiment}: {count} ({pct:.1f}%)")
        
        lines.append(f"\n【内容类型】(一条评论可能包含多种类型)")
        for ctype, count in sorted(self.stats['by_content_type'].items(), key=lambda x: x[1], reverse=True):
            pct = count / max(self.stats['long_comments'], 1) * 100
            lines.append(f"  {ctype}: {count} ({pct:.1f}%)")
        
        lines.append("\n" + "=" * 70)
        
        return '\n'.join(lines)


def main():
    """主函数"""
    print("=" * 70)
    print("长结构评论提取器")
    print("与对话提取器形成互补：专注于单人深度长评论")
    print("=" * 70)
    
    # 读取数据
    input_file = PROJECT_ROOT / "data" / "comments" / "comments.json"
    print(f"\n读取: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_comments = sum(len(comments) for comments in data.values())
    print(f"话题数: {len(data)}")
    print(f"评论数: {total_comments}")
    
    # 创建提取器
    print("\n选择模式: quality (质量优先，最短50字)")
    extractor = LongCommentExtractor(min_length=50, mode='quality')
    
    # 提取
    print("\n开始提取...")
    analyses = extractor.extract_from_data(data)
    
    # 保存完整结果
    output_dir = PROJECT_ROOT / "data" / "comment_to_single"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "long_comments_full.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(extractor.format_output(analyses))
    
    print(f"\n✅ 已保存 {len(analyses)} 条长评论到: {output_file}")
    
    # 保存TOP评论
    top_file = output_dir / "long_comments_top50.txt"
    with open(top_file, 'w', encoding='utf-8') as f:
        f.write(extractor.format_output(analyses, top_n=50))
    
    print(f"✅ 已保存TOP50高质量评论到: {top_file}")
    
    # 生成报告
    report = extractor.generate_report()
    print(report)
    
    with open(output_dir / "long_comments_report.txt", 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 显示TOP5示例
    print("\n" + "=" * 70)
    print("TOP5高质量评论示例")
    print("=" * 70)
    
    for i, analysis in enumerate(analyses[:5], 1):
        print(f"\n【示例 {i}】质量分: {analysis.quality_score:.1f} | 点赞: {analysis.likes} | {analysis.length}字")
        print(f"标签: {', '.join(analysis.tags)}")
        print(f"内容: {analysis.cleaned_text[:100]}...")
        print(f"替换: {analysis.formatted_text[:100]}...")
    
    return output_file


if __name__ == '__main__':
    main()