#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
营销对话数据分类器
功能：将营销对话数据.docx按对话特征分为两类
1. 多人对话型 - 类似真实评论中的对话提取器输出
2. 单人长叙述型 - 类似真实评论中的长评论提取器输出

与真实评论提取器的区别：
- 真实评论提取器：从原始评论中提取和转换
- 本分类器：对已格式化的营销对话进行分类和优化
"""

from docx import Document
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MarketingDialogueClassifier:
    """营销对话分类器"""
    
    def __init__(self):
        # 统计
        self.stats = {
            'total_paragraphs': 0,
            'dialogue_paragraphs': 0,
            'narrative_paragraphs': 0,
            'empty_paragraphs': 0,
            'multi_turn_dialogues': 0,
            'long_narratives': 0,
            'avg_dialogue_turns': 0,
            'avg_narrative_length': 0,
        }
        
        # 分类结果
        self.multi_turn_dialogues = []  # 多人对话
        self.long_narratives = []  # 单人长叙述
        
    def read_docx(self, filepath: str) -> List[str]:
        """
        读取docx文件
        重要：保留空行作为对话组的分隔符
        """
        doc = Document(filepath)
        paragraphs = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            # 保留所有段落，包括空行
            paragraphs.append(text)
        
        return paragraphs
    
    def is_dialogue_line(self, text: str) -> Tuple[bool, str, str]:
        """
        判断是否为对话行
        返回: (是否对话, 说话人, 内容)
        """
        # 匹配格式: a：内容 or a: 内容
        match = re.match(r'^([a-z]|回[a-z])\s*[：:]\s*(.+)$', text, re.IGNORECASE)
        if match:
            speaker = match.group(1).strip()
            content = match.group(2).strip()
            return True, speaker, content
        
        # 匹配格式: a（回主楼）：内容
        match = re.match(r'^([a-z])\s*[（(]回.+?[）)]\s*[：:]\s*(.+)$', text, re.IGNORECASE)
        if match:
            speaker = match.group(1).strip()
            content = match.group(2).strip()
            return True, speaker, content
        
        return False, '', text
    
    def extract_dialogue_groups(self, paragraphs: List[str]) -> List[List[Dict]]:
        """
        提取对话组
        重要修改：空行是对话组的天然分隔符，不应跨空行合并对话
        每个空行分隔的内容都是一个独立的对话组
        """
        dialogue_groups = []
        current_group = []
        
        for para in paragraphs:
            # 空段落作为分隔符 - 保存当前组并开始新组
            if not para.strip():
                if current_group:
                    dialogue_groups.append(current_group)
                    current_group = []
                continue
            
            is_dialogue, speaker, content = self.is_dialogue_line(para)
            
            if is_dialogue:
                current_group.append({
                    'speaker': speaker,
                    'content': content,
                    'original': para
                })
            else:
                # 如果遇到非对话行，保存当前组
                if current_group:
                    dialogue_groups.append(current_group)
                    current_group = []
                
                # 检查是否为叙述性内容（非标题）
                if len(para) >= 20 and not any(x in para for x in ['营销对话', '指代', '对话式']):
                    # 单独作为一个叙述组
                    dialogue_groups.append([{
                        'speaker': 'narrative',
                        'content': para,
                        'original': para
                    }])
        
        # 保存最后一组
        if current_group:
            dialogue_groups.append(current_group)
        
        return dialogue_groups
    
    def classify_dialogue_group(self, group: List[Dict]) -> str:
        """
        分类对话组
        返回: 'multi_turn' (多轮对话) 或 'long_narrative' (长叙述)
        """
        # 如果只有一个说话人
        if len(group) == 1:
            content = group[0]['content']
            speaker = group[0]['speaker']
            
            # 如果是叙述类型或内容很长
            if speaker == 'narrative' or len(content) >= 50:
                return 'long_narrative'
            else:
                return 'short_single'  # 短单句，可能要过滤
        
        # 统计不同说话人数量
        speakers = set(item['speaker'] for item in group)
        
        # 如果有2个或以上说话人，是多轮对话
        if len(speakers) >= 2:
            return 'multi_turn'
        
        # 如果只有1个说话人但有多条发言
        elif len(group) >= 2:
            total_length = sum(len(item['content']) for item in group)
            # 如果总长度够长，算作长叙述
            if total_length >= 50:
                return 'long_narrative'
            else:
                return 'multi_turn'  # 算作自问自答式对话
        
        return 'short_single'
    
    def format_multi_turn(self, group: List[Dict]) -> str:
        """格式化多轮对话"""
        lines = []
        for item in group:
            speaker = item['speaker']
            content = item['content']
            lines.append(f"{speaker}：{content}")
        return '\n'.join(lines)
    
    def format_long_narrative(self, group: List[Dict]) -> Dict:
        """格式化长叙述"""
        if len(group) == 1:
            return {
                'content': group[0]['content'],
                'length': len(group[0]['content']),
                'type': 'single_narrative'
            }
        else:
            # 多条连续发言合并
            combined = '，'.join([item['content'] for item in group])
            return {
                'content': combined,
                'length': len(combined),
                'type': 'multi_statement'
            }
    
    def analyze_dialogue_quality(self, dialogue: str) -> Dict:
        """分析对话质量"""
        lines = dialogue.split('\n')
        
        # 统计轮数
        turns = len(lines)
        
        # 统计说话人数
        speakers = set()
        for line in lines:
            if '：' in line or ':' in line:
                speaker = line.split('：')[0] if '：' in line else line.split(':')[0]
                speakers.add(speaker.strip())
        
        # 统计总字数
        total_chars = sum(len(line) for line in lines)
        
        # 评估互动性
        interaction_score = min(len(speakers) * 20, 60)  # 说话人越多，互动性越强
        
        # 评估长度得分
        length_score = min(turns * 10, 40)  # 轮数越多，得分越高
        
        # 总分
        quality_score = interaction_score + length_score
        
        return {
            'turns': turns,
            'speakers': len(speakers),
            'total_chars': total_chars,
            'quality_score': quality_score,
            'interaction_level': 'high' if len(speakers) >= 3 else 'medium' if len(speakers) == 2 else 'low'
        }
    
    def analyze_narrative_quality(self, narrative: Dict) -> Dict:
        """分析叙述质量"""
        content = narrative['content']
        length = narrative['length']
        
        # 信息密度检测
        info_keywords = ['用', '效果', '感觉', '推荐', '适合', '不错', '好用', '白', '补水']
        info_count = sum(1 for kw in info_keywords if kw in content)
        
        # 长度得分
        if length >= 100:
            length_score = 50
        elif length >= 70:
            length_score = 40
        elif length >= 50:
            length_score = 30
        else:
            length_score = 20
        
        # 信息密度得分
        info_score = min(info_count * 10, 50)
        
        # 总分
        quality_score = length_score + info_score
        
        return {
            'length': length,
            'info_density': info_count,
            'quality_score': quality_score,
            'quality_tier': 'high' if quality_score >= 70 else 'medium' if quality_score >= 50 else 'low'
        }
    
    def classify_all(self, paragraphs: List[str]):
        """分类所有内容"""
        # 提取对话组
        dialogue_groups = self.extract_dialogue_groups(paragraphs)
        
        print(f"\n提取到 {len(dialogue_groups)} 个对话组")
        
        # 分类每个组
        for group in dialogue_groups:
            classification = self.classify_dialogue_group(group)
            
            if classification == 'multi_turn':
                formatted = self.format_multi_turn(group)
                quality = self.analyze_dialogue_quality(formatted)
                
                self.multi_turn_dialogues.append({
                    'dialogue': formatted,
                    'quality': quality
                })
                
            elif classification == 'long_narrative':
                formatted = self.format_long_narrative(group)
                quality = self.analyze_narrative_quality(formatted)
                
                self.long_narratives.append({
                    'narrative': formatted,
                    'quality': quality
                })
        
        # 更新统计
        self.stats['multi_turn_dialogues'] = len(self.multi_turn_dialogues)
        self.stats['long_narratives'] = len(self.long_narratives)
        
        if self.multi_turn_dialogues:
            avg_turns = sum(d['quality']['turns'] for d in self.multi_turn_dialogues) / len(self.multi_turn_dialogues)
            self.stats['avg_dialogue_turns'] = round(avg_turns, 1)
        
        if self.long_narratives:
            avg_length = sum(n['narrative']['length'] for n in self.long_narratives) / len(self.long_narratives)
            self.stats['avg_narrative_length'] = round(avg_length, 1)
    
    def save_dialogues(self, filepath: str):
        """保存多轮对话"""
        # 按质量分数排序
        sorted_dialogues = sorted(
            self.multi_turn_dialogues,
            key=lambda x: x['quality']['quality_score'],
            reverse=True
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("营销对话数据 - 多轮对话分类\n")
            f.write("=" * 70 + "\n\n")
            f.write("说明：提取多人互动的对话，类似真实评论的对话提取器输出\n")
            f.write(f"总数：{len(sorted_dialogues)} 组\n\n")
            f.write("=" * 70 + "\n\n")
            
            for i, item in enumerate(sorted_dialogues, 1):
                dialogue = item['dialogue']
                quality = item['quality']
                
                f.write(f"【对话 {i}】\n")
                f.write(f"质量分数: {quality['quality_score']}/100\n")
                f.write(f"对话轮数: {quality['turns']}轮\n")
                f.write(f"参与人数: {quality['speakers']}人\n")
                f.write(f"互动水平: {quality['interaction_level']}\n")
                f.write(f"\n{dialogue}\n\n")
                f.write("-" * 70 + "\n\n")
        
        print(f"✅ 已保存 {len(sorted_dialogues)} 组多轮对话到: {filepath}")
    
    def save_narratives(self, filepath: str, top_n: int = None):
        """保存长叙述"""
        # 按质量分数排序
        sorted_narratives = sorted(
            self.long_narratives,
            key=lambda x: x['quality']['quality_score'],
            reverse=True
        )
        
        if top_n:
            sorted_narratives = sorted_narratives[:top_n]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("营销对话数据 - 长叙述分类\n")
            f.write("=" * 70 + "\n\n")
            f.write("说明：提取单人深度叙述，类似真实评论的长评论提取器输出\n")
            f.write(f"总数：{len(sorted_narratives)} 条\n\n")
            f.write("=" * 70 + "\n\n")
            
            for i, item in enumerate(sorted_narratives, 1):
                narrative = item['narrative']
                quality = item['quality']
                
                f.write(f"【叙述 {i}】\n")
                f.write(f"质量分数: {quality['quality_score']}/100\n")
                f.write(f"内容长度: {quality['length']}字\n")
                f.write(f"信息密度: {quality['info_density']}\n")
                f.write(f"质量等级: {quality['quality_tier']}\n")
                f.write(f"\n{narrative['content']}\n\n")
                f.write("-" * 70 + "\n\n")
        
        print(f"✅ 已保存 {len(sorted_narratives)} 条长叙述到: {filepath}")
    
    def generate_report(self) -> str:
        """生成分类报告"""
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append("营销对话数据分类报告")
        lines.append("=" * 70)
        
        lines.append("\n【基本统计】")
        lines.append(f"  总对话组: {self.stats['multi_turn_dialogues'] + self.stats['long_narratives']}")
        lines.append(f"  多轮对话: {self.stats['multi_turn_dialogues']} 组")
        lines.append(f"  长叙述: {self.stats['long_narratives']} 条")
        
        lines.append("\n【多轮对话特征】")
        if self.multi_turn_dialogues:
            lines.append(f"  平均轮数: {self.stats['avg_dialogue_turns']}轮")
            
            # 统计互动水平分布
            interaction_dist = defaultdict(int)
            for d in self.multi_turn_dialogues:
                interaction_dist[d['quality']['interaction_level']] += 1
            
            lines.append(f"  互动水平分布:")
            for level in ['high', 'medium', 'low']:
                if level in interaction_dist:
                    count = interaction_dist[level]
                    pct = count / len(self.multi_turn_dialogues) * 100
                    lines.append(f"    {level}: {count} ({pct:.1f}%)")
        
        lines.append("\n【长叙述特征】")
        if self.long_narratives:
            lines.append(f"  平均长度: {self.stats['avg_narrative_length']}字")
            
            # 统计质量分布
            quality_dist = defaultdict(int)
            for n in self.long_narratives:
                quality_dist[n['quality']['quality_tier']] += 1
            
            lines.append(f"  质量分布:")
            for tier in ['high', 'medium', 'low']:
                if tier in quality_dist:
                    count = quality_dist[tier]
                    pct = count / len(self.long_narratives) * 100
                    lines.append(f"    {tier}: {count} ({pct:.1f}%)")
        
        lines.append("\n" + "=" * 70)
        
        return '\n'.join(lines)


def main():
    """主函数"""
    print("=" * 70)
    print("营销对话数据分类器")
    print("功能：将营销对话按特征分为多轮对话和长叙述两类")
    print("=" * 70)
    
    # 读取文件
    marketing_dir = PROJECT_ROOT / "data" / "marketing"
    input_file = marketing_dir / "营销对话数据.docx"
    print(f"\n读取文件: {input_file}")
    
    classifier = MarketingDialogueClassifier()
    paragraphs = classifier.read_docx(str(input_file))
    
    print(f"总段落数: {len(paragraphs)}")
    
    # 分类
    print("\n开始分类...")
    classifier.classify_all(paragraphs)
    
    # 保存结果
    print("\n保存结果...")
    marketing_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存多轮对话
    dialogue_file = marketing_dir / "marketing_dialogues.txt"
    classifier.save_dialogues(dialogue_file)
    
    # 保存所有长叙述
    narrative_file_full = marketing_dir / "marketing_narratives_full.txt"
    classifier.save_narratives(narrative_file_full)
    
    # 保存TOP50长叙述
    narrative_file_top = marketing_dir / "marketing_narratives_top50.txt"
    classifier.save_narratives(narrative_file_top, top_n=50)
    
    # 生成报告
    report = classifier.generate_report()
    print(report)
    
    with open(marketing_dir / "marketing_classification_report.txt", 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 显示示例
    print("\n" + "=" * 70)
    print("示例数据")
    print("=" * 70)
    
    print("\n【多轮对话示例】")
    for i, item in enumerate(classifier.multi_turn_dialogues[:3], 1):
        print(f"\n示例 {i} (质量分: {item['quality']['quality_score']})")
        print(item['dialogue'])
    
    print("\n【长叙述示例】")
    for i, item in enumerate(classifier.long_narratives[:3], 1):
        print(f"\n示例 {i} (质量分: {item['quality']['quality_score']})")
        print(item['narrative']['content'][:100] + "...")
    
    return dialogue_file, narrative_file_full


if __name__ == '__main__':
    main()