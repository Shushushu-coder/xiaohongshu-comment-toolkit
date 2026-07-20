#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话生成任务数据准备工具
功能：将对话数据转换为适合训练对话生成模型的格式
支持多种格式：单轮预测、多轮上下文、instruction格式
"""

import json
from pathlib import Path
from typing import List, Dict
import random


class DialogueGenerationDataPrep:
    """对话生成数据准备器"""
    
    def __init__(self, context_window=3):
        """
        Args:
            context_window: 对话上下文窗口大小(前N轮)
        """
        self.context_window = context_window
        self.train_examples = []
        self.val_examples = []
        self.test_examples = []
    
    def prepare_single_turn_prediction(self, data: List[Dict]) -> List[Dict]:
        """
        单轮预测格式
        输入: 前N轮对话
        输出: 下一轮回复
        """
        examples = []
        
        for item in data:
            if item['type'] != 'dialogue':
                continue
            
            turns = item['content']['turns']
            if len(turns) < 2:  # 至少需要2轮
                continue
            
            # 对每个可预测的轮次创建一个训练样本
            for i in range(1, len(turns)):
                # 获取上下文(前N轮)
                start_idx = max(0, i - self.context_window)
                context = turns[start_idx:i]
                target = turns[i]
                
                example = {
                    'id': f"{item['id']}_turn_{i}",
                    'context': [
                        {'speaker': t['speaker'], 'text': t['text']}
                        for t in context
                    ],
                    'target': {
                        'speaker': target['speaker'],
                        'text': target['text']
                    },
                    'metadata': {
                        'source': item['source'],
                        'turn_index': i,
                        'total_turns': len(turns)
                    }
                }
                examples.append(example)
        
        return examples
    
    def prepare_instruction_format(self, data: List[Dict]) -> List[Dict]:
        """
        Instruction格式 (适用于Instruct模型)
        包含instruction、input、output
        """
        examples = []
        
        for item in data:
            if item['type'] != 'dialogue':
                continue
            
            turns = item['content']['turns']
            if len(turns) < 2:
                continue
            
            for i in range(1, len(turns)):
                start_idx = max(0, i - self.context_window)
                context = turns[start_idx:i]
                target = turns[i]
                
                # 构建上下文文本
                context_text = '\n'.join([
                    f"{t['speaker']}：{t['text']}"
                    for t in context
                ])
                
                example = {
                    'instruction': '你是一个护肤品评论社区的对话助手。请根据前面的对话历史，生成下一轮自然的回复。',
                    'input': f"对话历史：\n{context_text}\n\n请生成{target['speaker']}的回复：",
                    'output': target['text'],
                    'metadata': {
                        'id': f"{item['id']}_turn_{i}",
                        'source': item['source'],
                        'turn_index': i
                    }
                }
                examples.append(example)
        
        return examples
    
    def prepare_chat_format(self, data: List[Dict]) -> List[Dict]:
        """
        Chat格式 (适用于ChatGPT风格模型)
        包含messages列表
        """
        examples = []
        
        for item in data:
            if item['type'] != 'dialogue':
                continue
            
            turns = item['content']['turns']
            if len(turns) < 2:
                continue
            
            for i in range(1, len(turns)):
                start_idx = max(0, i - self.context_window)
                context = turns[start_idx:i]
                target = turns[i]
                
                # 构建messages
                messages = [
                    {
                        'role': 'system',
                        'content': '你是一个护肤品评论社区的对话助手，请提供自然、真实、有用的回复。'
                    }
                ]
                
                # 添加对话历史
                for t in context:
                    role = 'user' if t['speaker'] == context[0]['speaker'] else 'assistant'
                    messages.append({
                        'role': role,
                        'content': t['text']
                    })
                
                example = {
                    'messages': messages,
                    'target_message': {
                        'role': 'assistant',
                        'content': target['text']
                    },
                    'metadata': {
                        'id': f"{item['id']}_turn_{i}",
                        'source': item['source']
                    }
                }
                examples.append(example)
        
        return examples
    
    def split_dataset(self, examples: List[Dict], 
                     train_ratio=0.8, val_ratio=0.1, test_ratio=0.1,
                     seed=42):
        """分割数据集"""
        random.seed(seed)
        shuffled = examples.copy()
        random.shuffle(shuffled)
        
        total = len(shuffled)
        train_size = int(total * train_ratio)
        val_size = int(total * val_ratio)
        
        self.train_examples = shuffled[:train_size]
        self.val_examples = shuffled[train_size:train_size + val_size]
        self.test_examples = shuffled[train_size + val_size:]
        
        print(f"\n数据集分割:")
        print(f"  训练集: {len(self.train_examples)} 条 ({train_ratio*100:.0f}%)")
        print(f"  验证集: {len(self.val_examples)} 条 ({val_ratio*100:.0f}%)")
        print(f"  测试集: {len(self.test_examples)} 条 ({test_ratio*100:.0f}%)")
    
    def save_dataset(self, output_dir: str, format_type: str):
        """保存数据集"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 保存训练集
        with open(output_path / 'train.jsonl', 'w', encoding='utf-8') as f:
            for example in self.train_examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        # 保存验证集
        with open(output_path / 'val.jsonl', 'w', encoding='utf-8') as f:
            for example in self.val_examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        # 保存测试集
        with open(output_path / 'test.jsonl', 'w', encoding='utf-8') as f:
            for example in self.test_examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        # 保存配置
        config = {
            'format_type': format_type,
            'context_window': self.context_window,
            'train_size': len(self.train_examples),
            'val_size': len(self.val_examples),
            'test_size': len(self.test_examples)
        }
        
        with open(output_path / 'config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 数据集已保存到: {output_dir}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='对话生成任务数据准备')
    parser.add_argument('--input', type=str, required=True,
                       help='输入文件 (JSONL格式)')
    parser.add_argument('--output', type=str, required=True,
                       help='输出目录')
    parser.add_argument('--format', type=str, 
                       choices=['single_turn', 'instruction', 'chat'],
                       default='single_turn',
                       help='数据格式类型')
    parser.add_argument('--context-window', type=int, default=3,
                       help='对话上下文窗口大小')
    parser.add_argument('--seed', type=int, default=42,
                       help='随机种子')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("对话生成任务数据准备")
    print("=" * 70)
    print(f"\n输入文件: {args.input}")
    print(f"输出目录: {args.output}")
    print(f"数据格式: {args.format}")
    print(f"上下文窗口: {args.context_window} 轮")
    
    # 读取数据
    print("\n读取数据...")
    data = []
    with open(args.input, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    
    print(f"读取了 {len(data)} 条数据")
    
    # 准备数据
    prep = DialogueGenerationDataPrep(context_window=args.context_window)
    
    print(f"\n准备 {args.format} 格式数据...")
    
    if args.format == 'single_turn':
        examples = prep.prepare_single_turn_prediction(data)
    elif args.format == 'instruction':
        examples = prep.prepare_instruction_format(data)
    elif args.format == 'chat':
        examples = prep.prepare_chat_format(data)
    
    print(f"生成了 {len(examples)} 个训练样本")
    
    # 分割数据集
    prep.split_dataset(examples, seed=args.seed)
    
    # 保存数据集
    prep.save_dataset(args.output, args.format)
    
    # 显示示例
    print("\n" + "=" * 70)
    print("数据示例 (前3个训练样本)")
    print("=" * 70)
    
    for i, example in enumerate(prep.train_examples[:3], 1):
        print(f"\n【示例 {i}】")
        print(json.dumps(example, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ 完成!")
    print("=" * 70)


if __name__ == '__main__':
    main()