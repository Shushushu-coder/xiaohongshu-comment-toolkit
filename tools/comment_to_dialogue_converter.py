#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实用户评论 → 营销对话格式 转换脚本
功能：
1. 自动提取对话链
2. 智能品牌/产品替换
3. 用户名映射为a/b/c
4. 生成与营销对话相同格式的文本
5. 质量过滤
"""

import json
import re
from collections import defaultdict
from typing import List, Dict, Tuple, Optional


class CommentToDialogueConverter:
    """评论到对话的转换器"""
    
    def __init__(self):
        # 品牌/产品替换规则
        self.brand_mapping = {
            # 品牌名称 → B
            '谷雨': 'B',
            '肌肤未来': 'B1',
            '溪木源': 'B2',
            '溪': 'B2',
            '自然堂': 'B3',
            '佰草集': 'B4',
            '兰蔻': 'B5',
            '雅诗兰黛': 'B6',
            '欧莱雅': 'B7',
            '资生堂': 'B8',
            '珀莱雅': 'B9',
            '科颜氏': 'B10',
            '兰芝': 'B11',
            '悦诗风吟': 'B12',
            '妮维雅630': 'B13',
            'hbn': 'B14',
            'HBN': 'B15',
            'Hbn': 'B16', 
            'hfp': 'B16',
            'BB霜': 'B17',
            '谷屿': 'B',
            'lv': 'B18',
            '香奈儿': 'B19',
            '千人千面': 'B20',
            '稀物集': 'B21',
            '玉兰油': 'B22',
            '百雀羚': 'B23',
            '韩束': 'B24',




            # 可以添加更多品牌
        }
        
        self.product_mapping = {
            # 产品类型 → A
            '光感': 'A1',
            '雪肌': 'A2',
            '奶皮': 'A3',
            '美白奶罐': 'A4',
            '小奶罐': 'A4',            
            '雪绒花积雪草': 'A5',
            '仙人掌': 'A6',
            '淡斑瓶': 'A7',
            '抛光': 'A8',
            '高能': 'A9',
            '海藻珍珠粉': 'A10',
            '白千': 'A11',
            '山茶花': 'A12',
            '菌菇': 'A13',
            '层孔菌': 'A14',
            '红宝石': 'A15',
            '红蛮腰': 'A16',      
            '白蛮腰': 'A17',

            # 可以添加更多产品
        }
        
        self.platform_mapping = {
            # 平台 → D
            '小红书': 'D',
            '淘宝': 'D',
            '天猫': 'D',
            '京东': 'D',
            '抖音': 'D',
        }
        
        self.activity_mapping = {
            # 人名相关 → C
            '李佳琦': 'C',
            '张雨绮': 'C1',   
            '张新成': 'C2',
            '王安宇': 'C3',
            '鹿晗': 'C4',
            '杨紫': 'C5',

        }
        
        # 用户名映射字母表
        self.user_letters = 'abcdefghijklmnopqrstuvwxyz'
        
        # 质量过滤配置
        self.min_dialogue_turns = 2  # 最少对话轮数
        self.min_content_length = 5  # 最短内容长度
        self.max_content_length = 200  # 最长内容长度
        
    def extract_reply_info(self, content: str) -> Tuple[Optional[str], str]:
        """提取回复关系"""
        if content.startswith('回复 '):
            parts = content.split(' : ', 1)
            if len(parts) == 2:
                replied_to = parts[0].replace('回复 ', '').strip()
                actual_content = parts[1].strip()
                return replied_to, actual_content
        return None, content
    
    def build_dialogue_chains(self, topic_comments: List[Dict]) -> List[List[Dict]]:
        """从评论列表构建对话链"""
        dialogues = []
        used_indices = set()
        
        for i, comment in enumerate(topic_comments):
            if i in used_indices:
                continue
            
            replied_to, content = self.extract_reply_info(comment['content'])
            
            # 如果这是一个顶层评论（没有回复对象）
            if not replied_to:
                dialogue = [{
                    'user': comment['username'],
                    'content': content,
                    'likes': comment['likes']
                }]
                used_indices.add(i)
                
                # 查找所有回复这条评论的内容
                dialogue_users = {comment['username']}
                
                # 多次遍历以捕获嵌套回复
                changed = True
                while changed:
                    changed = False
                    for j in range(i + 1, len(topic_comments)):
                        if j in used_indices:
                            continue
                        
                        next_comment = topic_comments[j]
                        next_replied_to, next_content = self.extract_reply_info(next_comment['content'])
                        
                        # 如果回复的是当前对话中的某个用户
                        if next_replied_to in dialogue_users:
                            dialogue.append({
                                'user': next_comment['username'],
                                'content': next_content,
                                'likes': next_comment['likes'],
                                'reply_to': next_replied_to
                            })
                            dialogue_users.add(next_comment['username'])
                            used_indices.add(j)
                            changed = True
                
                if len(dialogue) >= self.min_dialogue_turns:
                    dialogues.append(dialogue)
        
        # 处理独立评论（可以配对成问答）
        standalone_comments = []
        for i, comment in enumerate(topic_comments):
            if i not in used_indices:
                replied_to, content = self.extract_reply_info(comment['content'])
                if not replied_to and len(content) >= self.min_content_length:
                    standalone_comments.append({
                        'user': comment['username'],
                        'content': content,
                        'likes': comment['likes']
                    })
        
        # 将高质量的独立评论配对成简单对话
        for comment in standalone_comments:
            # 生成一个询问来配对
            if any(keyword in comment['content'] for keyword in ['好用', '推荐', '白了', '效果']):
                dialogues.append([
                    {'user': 'inquirer', 'content': self._generate_inquiry(comment['content'])},
                    comment
                ])
        
        return dialogues
    
    def _generate_inquiry(self, content: str) -> str:
        """根据回答内容生成一个合适的询问"""
        if '好用' in content or '推荐' in content:
            return '这个好用吗？'
        elif '白了' in content or '美白' in content:
            return '真的能白吗？'
        elif '长痘' in content or '闭口' in content:
            return '会不会长痘啊？'
        elif '刺激' in content or '敏感' in content:
            return '敏感肌能用吗？'
        else:
            return '效果怎么样？'
    
    def replace_brands_products(self, content: str) -> str:
        """智能替换品牌、产品、平台、活动名称"""
        result = content
        
        # 替换品牌
        for brand, replacement in self.brand_mapping.items():
            result = result.replace(brand, replacement)
        
        # 替换产品（注意顺序，长的先替换）
        sorted_products = sorted(self.product_mapping.items(), key=lambda x: len(x[0]), reverse=True)
        for product, replacement in sorted_products:
            result = result.replace(product, replacement)
        
        # 替换平台
        for platform, replacement in self.platform_mapping.items():
            result = result.replace(platform, replacement)
        
        # 替换活动
        for activity, replacement in self.activity_mapping.items():
            result = result.replace(activity, replacement)
        
        # 处理一些常见的组合模式
        result = re.sub(r'B家的?A', 'B的A', result)
        result = re.sub(r'用B', '用B家', result)
        
        return result
    
    def map_users_to_letters(self, dialogue: List[Dict]) -> List[Dict]:
        """将用户名映射为字母标识"""
        user_mapping = {}
        letter_index = 0
        
        result = []
        for turn in dialogue:
            user = turn['user']
            if user not in user_mapping:
                if letter_index < len(self.user_letters):
                    user_mapping[user] = self.user_letters[letter_index]
                    letter_index += 1
                else:
                    user_mapping[user] = f"user{letter_index}"
                    letter_index += 1
            
            result.append({
                'user_letter': user_mapping[user],
                'content': turn['content'],
                'original_user': user
            })
        
        return result
    
    def filter_quality(self, dialogue: List[Dict]) -> bool:
        """质量过滤"""
        # 检查对话轮数
        if len(dialogue) < self.min_dialogue_turns:
            return False
        
        # 检查内容质量
        for turn in dialogue:
            content = turn['content']
            
            # 长度过滤
            if len(content) < self.min_content_length:
                return False
            if len(content) > self.max_content_length:
                # 太长的可以保留，但需要截断提示
                pass
            
            # 过滤无意义内容
            meaningless_patterns = [
                r'^[？?！!。\.]+$',  # 只有标点
                r'^哈+$',  # 只有"哈"
                r'^[emm]+$',  # 只有"emm"
            ]
            for pattern in meaningless_patterns:
                if re.match(pattern, content):
                    return False
        
        return True
    
    def format_as_marketing_dialogue(self, dialogue: List[Dict]) -> str:
        """格式化为营销对话格式"""
        lines = []
        for turn in dialogue:
            user_letter = turn['user_letter']
            content = turn['content']
            
            # 应用品牌/产品替换
            content = self.replace_brands_products(content)
            
            # 格式化
            line = f"{user_letter}：{content}"
            lines.append(line)
        
        return '\n'.join(lines)
    
    def convert_comments_to_dialogues(self, comments_data: Dict) -> List[str]:
        """转换整个评论数据集"""
        all_dialogues = []
        
        for topic_id, topic_comments in comments_data.items():
            print(f"\n处理话题: {topic_id} ({len(topic_comments)} 条评论)")
            
            # 构建对话链
            dialogues = self.build_dialogue_chains(topic_comments)
            print(f"  提取到 {len(dialogues)} 组对话")
            
            # 处理每组对话
            valid_count = 0
            for dialogue in dialogues:
                # 质量过滤
                if not self.filter_quality(dialogue):
                    continue
                
                # 用户名映射
                mapped_dialogue = self.map_users_to_letters(dialogue)
                
                # 格式化
                formatted = self.format_as_marketing_dialogue(mapped_dialogue)
                
                all_dialogues.append(formatted)
                valid_count += 1
            
            print(f"  通过质量过滤: {valid_count} 组")
        
        return all_dialogues
    
    def save_dialogues(self, dialogues: List[str], output_path: str):
        """保存对话到文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("真实评论转换的营销对话数据\n")
            f.write("=" * 50 + "\n\n")
            
            for i, dialogue in enumerate(dialogues, 1):
                f.write(dialogue)
                f.write("\n\n")  # 对话之间空一行
        
        print(f"\n✅ 已保存 {len(dialogues)} 组对话到: {output_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("真实评论 → 营销对话格式 转换器")
    print("=" * 60)
    
    # 读取评论数据
    input_file = '/mnt/user-data/uploads/comments.json'
    print(f"\n📖 读取评论数据: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        comments_data = json.load(f)
    
    total_comments = sum(len(comments) for comments in comments_data.values())
    print(f"   话题数: {len(comments_data)}")
    print(f"   总评论数: {total_comments}")
    
    # 创建转换器
    converter = CommentToDialogueConverter()
    
    # 转换
    print("\n🔄 开始转换...")
    dialogues = converter.convert_comments_to_dialogues(comments_data)
    
    # 保存结果
    output_file = '/home/claude/converted_dialogues.txt'
    converter.save_dialogues(dialogues, output_file)
    
    # 统计信息
    print("\n" + "=" * 60)
    print("📊 转换统计")
    print("=" * 60)
    print(f"输入评论数: {total_comments}")
    print(f"输出对话数: {len(dialogues)}")
    print(f"转换率: {len(dialogues)/total_comments*100:.1f}%")
    
    # 显示示例
    print("\n" + "=" * 60)
    print("📝 转换示例（前5组）")
    print("=" * 60)
    for i, dialogue in enumerate(dialogues[:5], 1):
        print(f"\n【示例 {i}】")
        print(dialogue)
    
    return output_file


if __name__ == '__main__':
    output_file = main()
    print(f"\n✨ 转换完成！输出文件: {output_file}")
