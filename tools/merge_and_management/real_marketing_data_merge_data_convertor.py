#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据转换工具
功能：将原始文本数据转换为统一的JSONL格式，便于模型训练
"""

import json
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from collections import defaultdict
import random

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class DataConverter:
    """数据转换器"""
    
    def __init__(self, seed=42):
        self.seed = seed
        random.seed(seed)
        
        # 统计信息
        self.stats = defaultdict(int)
        
    def parse_real_dialogue(self, filepath: str) -> List[Dict]:
        """解析真实评论对话数据"""
        print(f"\n📄 解析: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        dialogues = []
        
        # 按对话分组
        dialogue_blocks = re.split(r'【对话 \d+】', content)
        
        for i, block in enumerate(dialogue_blocks[1:], 1):  # 跳过第一个空块
            block = block.strip()
            if not block:
                continue
            
            # 提取对话轮次
            turns = []
            for line in block.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # 匹配对话格式 a：xxx 或 b：xxx
                match = re.match(r'^([a-z]+)\s*[：:]\s*(.+)$', line, re.IGNORECASE)
                if match:
                    speaker = match.group(1).strip()
                    text = match.group(2).strip()
                    turns.append({
                        'speaker': speaker,
                        'text': text
                    })
            
            if turns:
                # 统计参与人数
                speakers = set(turn['speaker'] for turn in turns)
                
                dialogue = {
                    'id': f'real_dialogue_{i:03d}',
                    'type': 'dialogue',
                    'source': 'real_comment',
                    'content': {
                        'turns': turns
                    },
                    'metadata': {
                        'turn_count': len(turns),
                        'participant_count': len(speakers),
                        'total_length': sum(len(t['text']) for t in turns)
                    }
                }
                dialogues.append(dialogue)
                self.stats['real_dialogue_count'] += 1
        
        print(f"✅ 解析完成: {len(dialogues)} 组对话")
        return dialogues
    
    def parse_marketing_dialogue(self, filepath: str) -> List[Dict]:
        """解析营销对话数据"""
        print(f"\n📄 解析: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        dialogues = []
        
        # 按对话分组
        dialogue_blocks = re.split(r'【对话 \d+】', content)
        
        for i, block in enumerate(dialogue_blocks[1:], 1):
            block = block.strip()
            if not block:
                continue
            
            # 提取元数据
            quality_match = re.search(r'质量分数:\s*(\d+)/100', block)
            turns_match = re.search(r'对话轮数:\s*(\d+)轮', block)
            participants_match = re.search(r'参与人数:\s*(\d+)人', block)
            interaction_match = re.search(r'互动水平:\s*(\w+)', block)
            
            # 提取对话内容
            content_start = block.find('\n\n') + 2
            dialogue_text = block[content_start:].split('---')[0].strip()
            
            # 解析对话轮次
            turns = []
            for line in dialogue_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                match = re.match(r'^([a-zA-Z]+)\s*[：:]\s*(.+)$', line)
                if match:
                    speaker = match.group(1).strip()
                    text = match.group(2).strip()
                    turns.append({
                        'speaker': speaker,
                        'text': text
                    })
            
            if turns:
                dialogue = {
                    'id': f'marketing_dialogue_{i:03d}',
                    'type': 'dialogue',
                    'source': 'marketing_content',
                    'content': {
                        'turns': turns
                    },
                    'metadata': {
                        'quality_score': int(quality_match.group(1)) if quality_match else None,
                        'turn_count': int(turns_match.group(1)) if turns_match else len(turns),
                        'participant_count': int(participants_match.group(1)) if participants_match else None,
                        'interaction_level': interaction_match.group(1) if interaction_match else None,
                        'total_length': sum(len(t['text']) for t in turns)
                    }
                }
                dialogues.append(dialogue)
                self.stats['marketing_dialogue_count'] += 1
        
        print(f"✅ 解析完成: {len(dialogues)} 组对话")
        return dialogues
    
    def parse_real_narrative(self, filepath: str) -> List[Dict]:
        """解析真实评论长叙述数据"""
        print(f"\n📄 解析: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        narratives = []
        
        # 按评论分组
        narrative_blocks = re.split(r'【评论 \d+】', content)
        
        for i, block in enumerate(narrative_blocks[1:], 1):
            block = block.strip()
            if not block:
                continue
            
            # 提取元数据
            quality_match = re.search(r'质量分数:\s*([\d.]+)/100', block)
            likes_match = re.search(r'点赞数:\s*(\d+)', block)
            length_match = re.search(r'长度:\s*(\d+)字', block)
            sentiment_match = re.search(r'情感:\s*(\w+)', block)
            tags_match = re.search(r'标签:\s*(.+)', block)
            key_info_match = re.search(r'关键信息:\s*(.+)', block)
            
            # 提取原文
            original_match = re.search(r'【原文】\n(.+?)(?:\n\n【|$)', block, re.DOTALL)
            replaced_match = re.search(r'【品牌替换后】\n(.+?)(?:\n\n|$)', block, re.DOTALL)
            
            original_text = original_match.group(1).strip() if original_match else ""
            replaced_text = replaced_match.group(1).strip() if replaced_match else original_text
            
            if original_text:
                # 解析标签
                tags = []
                if tags_match:
                    tags = [t.strip() for t in tags_match.group(1).split(',')]
                
                # 解析关键信息
                key_info = []
                if key_info_match:
                    key_info = [k.strip() for k in key_info_match.group(1).split('|')]
                
                narrative = {
                    'id': f'real_narrative_{i:03d}',
                    'type': 'narrative',
                    'source': 'real_comment',
                    'content': {
                        'original': original_text,
                        'brand_replaced': replaced_text
                    },
                    'metadata': {
                        'quality_score': float(quality_match.group(1)) if quality_match else None,
                        'likes': int(likes_match.group(1)) if likes_match else 0,
                        'length': int(length_match.group(1)) if length_match else len(original_text),
                        'sentiment': sentiment_match.group(1) if sentiment_match else None,
                        'tags': tags,
                        'key_info': key_info
                    }
                }
                narratives.append(narrative)
                self.stats['real_narrative_count'] += 1
        
        print(f"✅ 解析完成: {len(narratives)} 条长叙述")
        return narratives
    
    def parse_marketing_narrative(self, filepath: str) -> List[Dict]:
        """解析营销长叙述数据"""
        print(f"\n📄 解析: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        narratives = []
        
        # 按叙述分组
        narrative_blocks = re.split(r'【叙述 \d+】', content)
        
        for i, block in enumerate(narrative_blocks[1:], 1):
            block = block.strip()
            if not block:
                continue
            
            # 提取元数据
            quality_match = re.search(r'质量分数:\s*(\d+)/100', block)
            length_match = re.search(r'内容长度:\s*(\d+)字', block)
            density_match = re.search(r'信息密度:\s*(\d+)', block)
            tier_match = re.search(r'质量等级:\s*(\w+)', block)
            
            # 提取内容 (在最后一个分隔线后)
            content_parts = block.split('\n\n')
            text = ""
            for part in content_parts:
                if not any(x in part for x in ['质量分数', '内容长度', '信息密度', '质量等级', '---']):
                    text = part.strip()
                    break
            
            if text:
                narrative = {
                    'id': f'marketing_narrative_{i:03d}',
                    'type': 'narrative',
                    'source': 'marketing_content',
                    'content': {
                        'text': text
                    },
                    'metadata': {
                        'quality_score': int(quality_match.group(1)) if quality_match else None,
                        'length': int(length_match.group(1)) if length_match else len(text),
                        'info_density': int(density_match.group(1)) if density_match else None,
                        'quality_tier': tier_match.group(1) if tier_match else None
                    }
                }
                narratives.append(narrative)
                self.stats['marketing_narrative_count'] += 1
        
        print(f"✅ 解析完成: {len(narratives)} 条长叙述")
        return narratives
    
    def convert_all(self, input_dir: str, output_dir: str):
        """转换所有数据"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print("=" * 70)
        print("数据转换工具")
        print("=" * 70)
        
        all_data = []
        
        # 解析真实评论对话
        real_dialogue_file = input_path / 'real_dialogues.txt'
        if real_dialogue_file.exists():
            all_data.extend(self.parse_real_dialogue(str(real_dialogue_file)))
        
        # 解析营销对话
        marketing_dialogue_file = input_path / 'marketing_dialogues.txt'
        if marketing_dialogue_file.exists():
            all_data.extend(self.parse_marketing_dialogue(str(marketing_dialogue_file)))
        
        # 解析真实评论长叙述
        real_narrative_file = input_path / 'real_narratives_full.txt'
        if real_narrative_file.exists():
            all_data.extend(self.parse_real_narrative(str(real_narrative_file)))
        
        # 解析营销长叙述
        marketing_narrative_file = input_path / 'marketing_narratives_full.txt'
        if marketing_narrative_file.exists():
            all_data.extend(self.parse_marketing_narrative(str(marketing_narrative_file)))
        
        print("\n" + "=" * 70)
        print(f"✅ 总计解析: {len(all_data)} 条数据")
        print("=" * 70)
        
        # 保存统一格式数据
        unified_file = output_path / 'unified_all.jsonl'
        with open(unified_file, 'w', encoding='utf-8') as f:
            for item in all_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"\n💾 已保存统一格式数据: {unified_file}")
        
        # 按类型分割
        self.split_by_type(all_data, output_path)
        
        # 按来源分割
        self.split_by_source(all_data, output_path)
        
        # 按质量分割
        self.split_by_quality(all_data, output_path)
        
        # 数据集分割 (train/val/test)
        self.split_dataset(all_data, output_path)
        
        # 生成统计报告
        self.generate_report(all_data, output_path)
        
        return all_data
    
    def split_by_type(self, data: List[Dict], output_path: Path):
        """按类型分割"""
        type_dir = output_path / 'by_type'
        type_dir.mkdir(exist_ok=True)
        
        dialogues = [d for d in data if d['type'] == 'dialogue']
        narratives = [d for d in data if d['type'] == 'narrative']
        
        with open(type_dir / 'dialogues.jsonl', 'w', encoding='utf-8') as f:
            for item in dialogues:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        with open(type_dir / 'narratives.jsonl', 'w', encoding='utf-8') as f:
            for item in narratives:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"\n📁 按类型分割:")
        print(f"   对话: {len(dialogues)} 条 → {type_dir / 'dialogues.jsonl'}")
        print(f"   叙述: {len(narratives)} 条 → {type_dir / 'narratives.jsonl'}")
    
    def split_by_source(self, data: List[Dict], output_path: Path):
        """按来源分割"""
        source_dir = output_path / 'by_source'
        source_dir.mkdir(exist_ok=True)
        
        real = [d for d in data if d['source'] == 'real_comment']
        marketing = [d for d in data if d['source'] == 'marketing_content']
        
        with open(source_dir / 'real.jsonl', 'w', encoding='utf-8') as f:
            for item in real:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        with open(source_dir / 'marketing.jsonl', 'w', encoding='utf-8') as f:
            for item in marketing:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"\n📁 按来源分割:")
        print(f"   真实评论: {len(real)} 条 → {source_dir / 'real.jsonl'}")
        print(f"   营销内容: {len(marketing)} 条 → {source_dir / 'marketing.jsonl'}")
    
    def split_by_quality(self, data: List[Dict], output_path: Path):
        """按质量分割"""
        quality_dir = output_path / 'by_quality'
        quality_dir.mkdir(exist_ok=True)
        
        high = []
        medium = []
        low = []
        
        for item in data:
            score = item['metadata'].get('quality_score')
            if score is None:
                continue
            
            if score >= 70:
                high.append(item)
            elif score >= 40:
                medium.append(item)
            else:
                low.append(item)
        
        with open(quality_dir / 'high.jsonl', 'w', encoding='utf-8') as f:
            for item in high:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        with open(quality_dir / 'medium.jsonl', 'w', encoding='utf-8') as f:
            for item in medium:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        with open(quality_dir / 'low.jsonl', 'w', encoding='utf-8') as f:
            for item in low:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"\n📁 按质量分割:")
        print(f"   高质量 (≥70): {len(high)} 条 → {quality_dir / 'high.jsonl'}")
        print(f"   中质量 (40-69): {len(medium)} 条 → {quality_dir / 'medium.jsonl'}")
        print(f"   低质量 (<40): {len(low)} 条 → {quality_dir / 'low.jsonl'}")
    
    def split_dataset(self, data: List[Dict], output_path: Path, 
                     train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
        """分割为训练/验证/测试集"""
        dataset_dir = output_path / 'dataset'
        dataset_dir.mkdir(exist_ok=True)
        
        # 随机打乱
        data_shuffled = data.copy()
        random.shuffle(data_shuffled)
        
        total = len(data_shuffled)
        train_size = int(total * train_ratio)
        val_size = int(total * val_ratio)
        
        train_data = data_shuffled[:train_size]
        val_data = data_shuffled[train_size:train_size + val_size]
        test_data = data_shuffled[train_size + val_size:]
        
        # 保存
        with open(dataset_dir / 'train.jsonl', 'w', encoding='utf-8') as f:
            for item in train_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        with open(dataset_dir / 'val.jsonl', 'w', encoding='utf-8') as f:
            for item in val_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        with open(dataset_dir / 'test.jsonl', 'w', encoding='utf-8') as f:
            for item in test_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"\n📁 数据集分割 ({train_ratio*100:.0f}%/{val_ratio*100:.0f}%/{test_ratio*100:.0f}%):")
        print(f"   训练集: {len(train_data)} 条 → {dataset_dir / 'train.jsonl'}")
        print(f"   验证集: {len(val_data)} 条 → {dataset_dir / 'val.jsonl'}")
        print(f"   测试集: {len(test_data)} 条 → {dataset_dir / 'test.jsonl'}")
    
    def generate_report(self, data: List[Dict], output_path: Path):
        """生成统计报告"""
        report = {
            'total_count': len(data),
            'by_type': defaultdict(int),
            'by_source': defaultdict(int),
            'by_quality': {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0},
            'dialogue_stats': {
                'total': 0,
                'avg_turns': 0,
                'avg_participants': 0
            },
            'narrative_stats': {
                'total': 0,
                'avg_length': 0
            }
        }
        
        for item in data:
            report['by_type'][item['type']] += 1
            report['by_source'][item['source']] += 1
            
            score = item['metadata'].get('quality_score')
            if score is None:
                report['by_quality']['unknown'] += 1
            elif score >= 70:
                report['by_quality']['high'] += 1
            elif score >= 40:
                report['by_quality']['medium'] += 1
            else:
                report['by_quality']['low'] += 1
            
            if item['type'] == 'dialogue':
                report['dialogue_stats']['total'] += 1
                turn_count = item['metadata'].get('turn_count', 0)
                if turn_count:
                    report['dialogue_stats']['avg_turns'] += turn_count
                participant_count = item['metadata'].get('participant_count', 0)
                if participant_count:
                    report['dialogue_stats']['avg_participants'] += participant_count
            
            elif item['type'] == 'narrative':
                report['narrative_stats']['total'] += 1
                length = item['metadata'].get('length', 0)
                if length:
                    report['narrative_stats']['avg_length'] += length
        
        # 计算平均值
        if report['dialogue_stats']['total'] > 0:
            report['dialogue_stats']['avg_turns'] /= report['dialogue_stats']['total']
            report['dialogue_stats']['avg_participants'] /= report['dialogue_stats']['total']
        
        if report['narrative_stats']['total'] > 0:
            report['narrative_stats']['avg_length'] /= report['narrative_stats']['total']
        
        # 保存报告
        report_file = output_path / 'statistics.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 打印报告
        print("\n" + "=" * 70)
        print("数据统计报告")
        print("=" * 70)
        print(f"\n总数据量: {report['total_count']} 条")
        print(f"\n按类型:")
        for type_name, count in report['by_type'].items():
            print(f"  {type_name}: {count} 条 ({count/report['total_count']*100:.1f}%)")
        
        print(f"\n按来源:")
        for source_name, count in report['by_source'].items():
            print(f"  {source_name}: {count} 条 ({count/report['total_count']*100:.1f}%)")
        
        print(f"\n按质量:")
        for quality, count in report['by_quality'].items():
            print(f"  {quality}: {count} 条")
        
        print(f"\n对话数据统计:")
        print(f"  平均轮数: {report['dialogue_stats']['avg_turns']:.1f}")
        print(f"  平均参与人数: {report['dialogue_stats']['avg_participants']:.1f}")
        
        print(f"\n长叙述统计:")
        print(f"  平均长度: {report['narrative_stats']['avg_length']:.1f}字")
        
        print(f"\n📊 统计报告已保存: {report_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据转换工具')
    parser.add_argument('--input', type=str, default=str(PROJECT_ROOT / "data" / "all_data_20251121"),
                       help='输入目录 (包含原始txt文件)')
    parser.add_argument('--output', type=str, default=str(PROJECT_ROOT / "data" / "all_data_20251121" / "converted_data"),
                       help='输出目录')
    parser.add_argument('--seed', type=int, default=42,
                       help='随机种子')
    
    args = parser.parse_args()
    
    converter = DataConverter(seed=args.seed)
    converter.convert_all(args.input, args.output)
    
    print("\n" + "=" * 70)
    print("✅ 数据转换完成!")
    print("=" * 70)
    print(f"\n输出目录: {args.output}")
    print("\n目录结构:")
    print("  unified_all.jsonl       - 统一格式的全部数据")
    print("  by_type/                - 按类型分类 (对话/叙述)")
    print("  by_source/              - 按来源分类 (真实/营销)")
    print("  by_quality/             - 按质量分类 (高/中/低)")
    print("  dataset/                - 训练集分割 (train/val/test)")
    print("  statistics.json         - 统计报告")
    print("\n下一步:")
    print("  1. 查看 statistics.json 了解数据分布")
    print("  2. 使用 dataset/ 中的数据进行训练")
    print("  3. 根据需要使用 by_type/by_source/by_quality 筛选数据")


if __name__ == '__main__':
    main()