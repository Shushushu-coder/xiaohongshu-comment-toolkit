#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实用户评论 → 营销对话格式 转换脚本 (实用增强版)
针对性解决核心问题:
1. 对话提取率低 - 采用多策略提取
2. 独立评论浪费 - 智能配对算法
3. 品牌替换问题 - 清洗+智能替换
"""

import json
import re
from collections import defaultdict
from typing import List, Dict, Tuple, Optional, Set
from difflib import SequenceMatcher


class EnhancedCommentConverter:
    """增强版评论转换器"""
    
    def __init__(self, mode='balanced'):
        """
        mode: 'strict' (严格) / 'balanced' (平衡) / 'loose' (宽松)
        """
        self.mode = mode
        
        # 品牌/产品映射 (按长度降序)
        self.brand_mapping = {
            '雪绒花积雪草': 'A1',
            '美白奶罐': 'A2',
            '谷雨': 'B',
            '谷屿': 'B',
            '小奶罐': 'A2',
            '光感水': 'A3',
            '光感': 'A3',
            '溪木源': 'B2',
            '珀莱雅': 'B9',
            '薇诺娜': 'B24',
            '谢馥春': 'B25',
            '小红书': 'D',
            '淘宝': 'D',
            '天猫': 'D',
            '京东': 'D',
            '抖音': 'D',
            '拼多多': 'D',
            '仙人掌': 'A6',
            '雪肌': 'A4',
            '次抛': 'A18',
            '奶片面膜': 'A20',
            '玫瑰水': 'A21',
            '源力面霜': 'A19',
        }
        
        # 按长度排序
        self.brand_mapping = dict(sorted(
            self.brand_mapping.items(),
            key=lambda x: len(x[0]),
            reverse=True
        ))
        
        # 情感关键词
        self.positive_kw = ['好用', '推荐', '白了', '效果好', '不错', '满意', '喜欢', '变白', '提亮', '清爽']
        self.negative_kw = ['长痘', '过敏', '闷痘', '闭口', '粉刺', '刺激', '不好用', '难用', '后悔', '退了', '拉', '黏腻']
        
        # 统计
        self.stats = {
            'strategy_explicit': 0,  # 明确回复链
            'strategy_keyword': 0,   # 关键词聚类
            'strategy_qa_pair': 0,   # 问答配对
            'filtered': 0,
            'positive': 0,
            'negative': 0,
            'neutral': 0,
        }
        
        # 设置阈值
        self.set_thresholds(mode)
    
    def set_thresholds(self, mode):
        """根据模式设置阈值"""
        thresholds = {
            'strict': {
                'min_turns': 3,
                'min_length': 5,
                'min_likes_for_qa': 5,
                'similarity': 0.90,
            },
            'balanced': {
                'min_turns': 2,
                'min_length': 3,
                'min_likes_for_qa': 1,
                'similarity': 0.85,
            },
            'loose': {
                'min_turns': 2,
                'min_length': 2,
                'min_likes_for_qa': 0,
                'similarity': 0.80,
            }
        }
        
        config = thresholds.get(mode, thresholds['balanced'])
        self.min_turns = config['min_turns']
        self.min_length = config['min_length']
        self.min_likes_for_qa = config['min_likes_for_qa']
        self.similarity_threshold = config['similarity']
    
    def clean_content(self, content: str) -> str:
        """清洗内容"""
        # 移除emoji
        content = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+', '', content)
        # 移除小红书表情
        content = re.sub(r'\[.*?R\]', '', content)
        content = re.sub(r'\[.*?\]', '', content)
        # 统一空格
        content = re.sub(r'\s+', ' ', content).strip()
        return content
    
    def extract_reply(self, content: str) -> Tuple[Optional[str], str]:
        """提取回复关系"""
        content = self.clean_content(content)
        match = re.match(r'^回复\s+(.+?)\s*[:：]\s*(.+)$', content)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return None, content
    
    def replace_brands(self, content: str) -> str:
        """替换品牌/产品"""
        result = content
        for original, replacement in self.brand_mapping.items():
            result = result.replace(original, replacement)
        return result
    
    def analyze_sentiment(self, text: str) -> str:
        """分析情感"""
        pos_count = sum(1 for kw in self.positive_kw if kw in text)
        neg_count = sum(1 for kw in self.negative_kw if kw in text)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        return 'neutral'
    
    def is_similar(self, text1: str, text2: str) -> bool:
        """判断文本相似度"""
        return SequenceMatcher(None, text1, text2).ratio() > self.similarity_threshold
    
    def is_valid_dialogue(self, dialogue: List[Dict], existing: List[str]) -> bool:
        """验证对话有效性"""
        # 检查轮数
        if len(dialogue) < self.min_turns:
            return False
        
        # 检查每轮内容
        for turn in dialogue:
            content = turn['content']
            if len(content) < self.min_length:
                return False
            
            # 过滤无意义内容
            if re.match(r'^[？?！!。\.，,]+$', content):
                return False
            if content in ['一样', '我也是', '同', '蹲', '哈哈', 'emm']:
                return False
        
        # 检查重复
        dialogue_text = ' '.join([t['content'] for t in dialogue])
        for exist_text in existing:
            if self.is_similar(dialogue_text, exist_text):
                return False
        
        return True
    
    # ========== 策略1: 提取明确的回复链 ==========
    def extract_explicit_chains(self, comments: List[Dict]) -> List[List[Dict]]:
        """提取明确的回复链"""
        comment_map = {}
        for i, comment in enumerate(comments):
            replied_to, content = self.extract_reply(comment['content'])
            comment_map[i] = {
                'index': i,
                'user': comment['username'],
                'content': content,
                'likes': comment['likes'],
                'replied_to': replied_to
            }
        
        dialogues = []
        used = set()
        
        # 找根评论
        roots = [i for i, c in comment_map.items() if c['replied_to'] is None]
        
        for root_idx in roots:
            if root_idx in used:
                continue
            
            # BFS构建对话树
            dialogue = []
            queue = [root_idx]
            dialogue_users = set()
            
            while queue:
                idx = queue.pop(0)
                if idx in used:
                    continue
                
                curr = comment_map[idx]
                dialogue.append({
                    'user': curr['user'],
                    'content': curr['content'],
                    'likes': curr['likes']
                })
                
                dialogue_users.add(curr['user'])
                used.add(idx)
                
                # 找回复当前对话中用户的评论
                for check_idx in range(idx + 1, len(comments)):
                    if check_idx not in used:
                        check = comment_map[check_idx]
                        if check['replied_to'] in dialogue_users:
                            queue.append(check_idx)
            
            if len(dialogue) >= 2:
                dialogues.append(dialogue)
        
        return dialogues
    
    # ========== 策略2: 关键词聚类 ==========
    def cluster_by_keywords(self, comments: List[Dict]) -> List[List[Dict]]:
        """通过关键词聚类评论"""
        # 定义关键词组
        keyword_groups = [
            ['长痘', '闭口', '痘痘'],
            ['美白', '白了', '变白', '提亮'],
            ['过敏', '敏感', '刺激', '泛红'],
            ['搓泥', '成膜'],
            ['清爽', '黏腻', '油腻'],
            ['价格', '多少钱', '便宜', '贵'],
            ['好用', '效果', '推荐'],
        ]
        
        dialogues = []
        
        for keywords in keyword_groups:
            # 找包含这些关键词的评论
            related_comments = []
            for comment in comments:
                content = self.clean_content(comment['content'])
                if any(kw in content for kw in keywords):
                    related_comments.append({
                        'user': comment['username'],
                        'content': content,
                        'likes': comment['likes']
                    })
            
            # 如果找到2条以上,组成对话
            if len(related_comments) >= 2:
                # 取前3-4条最相关的
                related_comments = sorted(related_comments, key=lambda x: x['likes'], reverse=True)[:4]
                if len(related_comments) >= 2:
                    dialogues.append(related_comments[:3])  # 最多3轮
        
        return dialogues
    
    # ========== 策略3: 问答配对 ==========
    def create_qa_pairs(self, comments: List[Dict]) -> List[List[Dict]]:
        """为高质量评论生成问答对"""
        qa_pairs = []
        
        # 问题模板
        question_templates = {
            ('好用', '推荐', '不错'): '这个产品好用吗?',
            ('白了', '美白', '变白', '提亮'): '真的能美白吗?',
            ('长痘', '闭口', '痘痘'): '会不会长痘?',
            ('过敏', '敏感', '刺激'): '敏感肌可以用吗?',
            ('清爽', '黏腻'): '质地怎么样?',
            ('搓泥'): '会搓泥吗?',
            ('价格', '多少钱'): '价格怎么样?',
            ('吸收', '渗透'): '吸收快吗?',
        }
        
        for comment in comments:
            content = self.clean_content(comment['content'])
            
            # 跳过太短或点赞太少的
            if len(content) < self.min_length:
                continue
            if comment['likes'] < self.min_likes_for_qa:
                continue
            
            # 匹配问题模板
            question = None
            for keywords, q in question_templates.items():
                if any(kw in content for kw in keywords):
                    question = q
                    break
            
            if question:
                qa_pairs.append([
                    {'user': 'inquirer', 'content': question, 'likes': 0},
                    {'user': comment['username'], 'content': content, 'likes': comment['likes']}
                ])
        
        return qa_pairs
    
    def convert_topic(self, comments: List[Dict]) -> List[List[Dict]]:
        """转换单个话题的评论"""
        all_dialogues = []
        
        # 策略1: 明确回复链
        explicit_chains = self.extract_explicit_chains(comments)
        self.stats['strategy_explicit'] += len(explicit_chains)
        all_dialogues.extend(explicit_chains)
        
        # 策略2: 关键词聚类
        if self.mode in ['balanced', 'loose']:
            keyword_clusters = self.cluster_by_keywords(comments)
            self.stats['strategy_keyword'] += len(keyword_clusters)
            all_dialogues.extend(keyword_clusters)
        
        # 策略3: 问答配对
        qa_pairs = self.create_qa_pairs(comments)
        self.stats['strategy_qa_pair'] += len(qa_pairs)
        all_dialogues.extend(qa_pairs)
        
        return all_dialogues
    
    def format_dialogue(self, dialogue: List[Dict]) -> str:
        """格式化对话"""
        # 用户名映射
        user_map = {}
        letters = 'abcdefghijklmnopqrstuvwxyz'
        
        lines = []
        for turn in dialogue:
            user = turn['user']
            if user not in user_map:
                user_map[user] = letters[len(user_map)] if len(user_map) < 26 else f"user{len(user_map)}"
            
            content = self.replace_brands(turn['content'])
            lines.append(f"{user_map[user]}：{content}")
        
        return '\n'.join(lines)
    
    def convert_all(self, comments_data: Dict) -> List[str]:
        """转换所有评论"""
        all_dialogues = []
        existing_texts = []
        
        for topic_id, comments in comments_data.items():
            print(f"\n处理话题: {topic_id} ({len(comments)} 条评论)")
            
            # 转换该话题
            topic_dialogues = self.convert_topic(comments)
            print(f"  提取到 {len(topic_dialogues)} 组候选对话")
            
            # 过滤和格式化
            valid_count = 0
            for dialogue in topic_dialogues:
                if self.is_valid_dialogue(dialogue, existing_texts):
                    formatted = self.format_dialogue(dialogue)
                    all_dialogues.append(formatted)
                    
                    # 记录用于去重
                    dialogue_text = ' '.join([t['content'] for t in dialogue])
                    existing_texts.append(dialogue_text)
                    
                    # 统计情感
                    sentiment = self.analyze_sentiment(dialogue_text)
                    self.stats[sentiment] += 1
                    
                    valid_count += 1
                else:
                    self.stats['filtered'] += 1
            
            print(f"  通过过滤: {valid_count} 组")
        
        return all_dialogues
    
    def generate_report(self, total_comments: int, dialogues: List[str]) -> str:
        """生成报告"""
        report = []
        report.append("\n" + "=" * 60)
        report.append("转换报告")
        report.append("=" * 60)
        
        report.append(f"\n【基本统计】")
        report.append(f"  输入评论数: {total_comments}")
        report.append(f"  输出对话数: {len(dialogues)}")
        if total_comments > 0:
            report.append(f"  转换率: {len(dialogues)/total_comments*100:.1f}%")
        
        report.append(f"\n【提取策略】")
        report.append(f"  明确回复链: {self.stats['strategy_explicit']}")
        report.append(f"  关键词聚类: {self.stats['strategy_keyword']}")
        report.append(f"  问答配对: {self.stats['strategy_qa_pair']}")
        report.append(f"  总候选数: {sum([self.stats['strategy_explicit'], self.stats['strategy_keyword'], self.stats['strategy_qa_pair']])}")
        report.append(f"  过滤数: {self.stats['filtered']}")
        
        report.append(f"\n【情感分布】")
        total = max(len(dialogues), 1)
        report.append(f"  正面: {self.stats['positive']} ({self.stats['positive']/total*100:.1f}%)")
        report.append(f"  负面: {self.stats['negative']} ({self.stats['negative']/total*100:.1f}%)")
        report.append(f"  中性: {self.stats['neutral']} ({self.stats['neutral']/total*100:.1f}%)")
        
        report.append("\n" + "=" * 60)
        return '\n'.join(report)


def main():
    """主函数"""
    print("=" * 60)
    print("评论转对话转换器 - 实用增强版")
    print("=" * 60)
    
    # 读取数据
    input_file = r'data\comments\comments.json'
    print(f"\n读取: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_comments = sum(len(comments) for comments in data.values())
    print(f"话题数: {len(data)}")
    print(f"评论数: {total_comments}")
    
    # 创建转换器 - 可选择模式
    print("\n选择模式: balanced (平衡)")
    converter = EnhancedCommentConverter(mode='balanced')
    
    # 转换
    print("\n开始转换...")
    dialogues = converter.convert_all(data)
    
    # 保存
    output_file = r'data\comment_to_dialogue\dialogues_enhanced.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("评论转对话 - 增强版输出\n")
        f.write("=" * 50 + "\n\n")
        for i, dialogue in enumerate(dialogues, 1):
            f.write(f"【对话 {i}】\n{dialogue}\n\n")
    
    print(f"\n✅ 已保存 {len(dialogues)} 组对话到: {output_file}")
    
    # 报告
    report = converter.generate_report(total_comments, dialogues)
    print(report)
    
    with open(r'data\comment_to_dialogue\report_enhanced.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 示例
    print("\n" + "=" * 60)
    print("示例对话(前5组)")
    print("=" * 60)
    for i, dialogue in enumerate(dialogues[:5], 1):
        print(f"\n【示例 {i}】\n{dialogue}")
    
    return output_file


if __name__ == '__main__':
    main()