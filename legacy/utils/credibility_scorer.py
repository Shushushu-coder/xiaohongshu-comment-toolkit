"""
用户可信度评分器 - 方法三的核心
"""
import numpy as np
from datetime import datetime, timedelta
import pandas as pd


class UserCredibilityScorer:
    """
    用户可信度评分器
    基于多维度特征评估用户是否为真实用户
    输出0-1分数，越高越可能是真实用户
    """
    
    def __init__(self, config):
        self.config = config
        self.rules = config.get('credibility_rules', {})
    
    def score_user(self, user_data):
        """
        评分主函数
        返回: (总分, 各维度得分详情)
        """
        scores = {}
        
        # 1. 账号年龄得分
        scores['account_age'] = self._score_account_age(user_data)
        
        # 2. 内容多样性得分
        scores['content_diversity'] = self._score_content_diversity(user_data)
        
        # 3. 互动比例得分
        scores['engagement_ratio'] = self._score_engagement_ratio(user_data)
        
        # 4. 发布模式得分
        scores['posting_pattern'] = self._score_posting_pattern(user_data)
        
        # 5. 粉丝质量得分
        scores['follower_quality'] = self._score_follower_quality(user_data)
        
        # 加权求和
        weights = {
            'account_age': self.rules.get('account_age', {}).get('weight', 0.2),
            'content_diversity': self.rules.get('content_diversity', {}).get('weight', 0.25),
            'engagement_ratio': self.rules.get('engagement_ratio', {}).get('weight', 0.15),
            'posting_pattern': self.rules.get('posting_pattern', {}).get('weight', 0.2),
            'follower_quality': self.rules.get('follower_quality', {}).get('weight', 0.2)
        }
        
        final_score = sum(scores[k] * weights[k] for k in scores)
        
        return final_score, scores
    
    def _score_account_age(self, user_data):
        """
        账号年龄得分
        注册时间越长，可信度越高
        """
        try:
            register_date = user_data.get('register_date')
            if not register_date:
                return 0.3  # 无数据时给予较低分
            
            # 计算账号天数
            if isinstance(register_date, str):
                register_date = datetime.strptime(register_date, '%Y-%m-%d')
            
            account_days = (datetime.now() - register_date).days
            
            # 归一化到0-1
            optimal_days = self.rules.get('account_age', {}).get('optimal_days', 730)
            score = min(account_days / optimal_days, 1.0)
            
            # 账号过新（<30天）给予惩罚
            if account_days < 30:
                score = score * 0.3
            
            return score
            
        except Exception as e:
            return 0.3
    
    def _score_content_diversity(self, user_data):
        """
        内容多样性得分
        发布内容涉及的类别越多，越可能是真实用户
        """
        try:
            # 从用户的笔记中统计类别
            post_categories = user_data.get('post_categories', [])
            unique_categories = len(set(post_categories))
            
            if unique_categories == 0:
                return 0.2
            
            optimal_categories = self.rules.get('content_diversity', {}).get('optimal_categories', 5)
            score = min(unique_categories / optimal_categories, 1.0)
            
            # 只发布单一类别内容的账号可疑
            if unique_categories == 1:
                score = score * 0.5
            
            return score
            
        except Exception as e:
            return 0.2
    
    def _score_engagement_ratio(self, user_data):
        """
        互动比例得分
        平均每条内容的互动数（点赞+评论）应该在合理范围内
        """
        try:
            total_likes = user_data.get('like_count', 0)
            note_count = user_data.get('note_count', 1)  # 避免除0
            
            if note_count == 0:
                return 0.2
            
            avg_engagement = total_likes / note_count
            
            # 正常用户的平均互动数通常在10-1000之间
            min_engagement = self.rules.get('engagement_ratio', {}).get('min_avg_engagement', 10)
            optimal_engagement = self.rules.get('engagement_ratio', {}).get('optimal_avg_engagement', 1000)
            
            score = self._normalize_value(avg_engagement, min_engagement, optimal_engagement)
            
            return score
            
        except Exception as e:
            return 0.2
    
    def _score_posting_pattern(self, user_data):
        """
        发布模式得分
        真实用户的发布时间应该有较大随机性
        机器人账号往往有规律的发布时间
        """
        try:
            post_times = user_data.get('post_times', [])
            
            if len(post_times) < 3:
                return 0.3
            
            # 计算发布时间间隔的标准差
            intervals = []
            for i in range(1, len(post_times)):
                if isinstance(post_times[i], str):
                    t1 = datetime.strptime(post_times[i], '%Y-%m-%d %H:%M:%S')
                    t0 = datetime.strptime(post_times[i-1], '%Y-%m-%d %H:%M:%S')
                else:
                    t1 = post_times[i]
                    t0 = post_times[i-1]
                
                interval = (t1 - t0).total_seconds() / 3600  # 转换为小时
                intervals.append(interval)
            
            # 计算标准差
            std_dev = np.std(intervals)
            
            # 标准差越大，说明发布时间越不规律，越像真人
            min_std = self.rules.get('posting_pattern', {}).get('min_std', 6)
            score = min(std_dev / (min_std * 2), 1.0)
            
            # 如果标准差过小（<1小时），说明发布过于规律
            if std_dev < 1:
                score = 0.1
            
            return score
            
        except Exception as e:
            return 0.3
    
    def _score_follower_quality(self, user_data):
        """
        粉丝质量得分
        通过粉丝数和获赞数的比例判断
        """
        try:
            follower_count = user_data.get('follower_count', 0)
            total_likes = user_data.get('like_count', 0)
            
            if follower_count == 0:
                # 粉丝为0但有内容，可能是新用户
                if user_data.get('note_count', 0) > 0:
                    return 0.5
                else:
                    return 0.1
            
            fan_like_ratio = total_likes / follower_count
            
            # 正常比例：0.5-10（每个粉丝贡献0.5-10个赞）
            min_ratio = self.rules.get('follower_quality', {}).get('min_fan_like_ratio', 0.5)
            max_ratio = self.rules.get('follower_quality', {}).get('max_fan_like_ratio', 10)
            
            score = self._normalize_value(fan_like_ratio, min_ratio, max_ratio)
            
            # 异常情况惩罚
            if fan_like_ratio < 0.1:  # 粉丝多但赞少（可能是僵尸粉）
                score = 0.2
            elif fan_like_ratio > 50:  # 赞远超粉丝（刷赞）
                score = 0.3
            
            return score
            
        except Exception as e:
            return 0.2
    
    def _normalize_value(self, value, low, high):
        """
        将值归一化到[0,1]
        - 小于low: 线性增长
        - 在low和high之间: 得分为1
        - 大于high: 线性下降
        """
        if value < low:
            return max(0, value / low)
        elif value > high:
            penalty = (value - high) / high
            return max(0, 1 - penalty)
        else:
            return 1.0
    
    def filter_users(self, users_df, threshold=0.6):
        """
        批量过滤用户
        
        参数:
            users_df: pandas DataFrame，包含用户数据
            threshold: 可信度阈值，默认0.6
        
        返回:
            filtered_df: 过滤后的DataFrame
            scores_df: 包含评分详情的DataFrame
        """
        scores_list = []
        
        for idx, user in users_df.iterrows():
            user_dict = user.to_dict()
            final_score, dimension_scores = self.score_user(user_dict)
            
            scores_list.append({
                'user_id': user.get('user_id', ''),
                'final_score': final_score,
                **dimension_scores
            })
        
        scores_df = pd.DataFrame(scores_list)
        
        # 合并原始数据和评分
        result_df = users_df.merge(scores_df, on='user_id', how='left')
        
        # 过滤
        filtered_df = result_df[result_df['final_score'] >= threshold]
        
        print(f"原始用户数: {len(users_df)}")
        print(f"过滤后用户数: {len(filtered_df)}")
        print(f"过滤比例: {len(filtered_df)/len(users_df)*100:.1f}%")
        
        return filtered_df, scores_df


class CommentFilter:
    """评论质量过滤器"""
    
    def __init__(self, config):
        self.config = config
        self.quality_filters = config.get('quality_filters', {})
    
    def filter_comments(self, comments_df):
        """
        过滤评论
        
        参数:
            comments_df: pandas DataFrame
        
        返回:
            filtered_df: 过滤后的DataFrame
        """
        df = comments_df.copy()
        original_count = len(df)
        
        # 1. 长度过滤
        min_length = self.quality_filters.get('min_comment_length', 5)
        max_length = self.quality_filters.get('max_comment_length', 1000)
        df = df[df['content'].str.len().between(min_length, max_length)]
        
        # 2. 排除明显的营销话术
        exclude_patterns = self.quality_filters.get('exclude_patterns', [])
        for pattern in exclude_patterns:
            df = df[~df['content'].str.contains(pattern, na=False)]
        
        # 3. 去除重复评论（可能是复制粘贴的水军）
        df = df.drop_duplicates(subset=['content'], keep='first')
        
        # 4. 去除全是表情/符号的评论
        df = df[df['content'].str.replace(r'[^\w\s]', '', regex=True).str.len() > 3]
        
        filtered_count = len(df)
        print(f"评论过滤: {original_count} -> {filtered_count} ({filtered_count/original_count*100:.1f}%)")
        
        return df


# 使用示例
if __name__ == "__main__":
    # 示例用户数据
    sample_user = {
        'user_id': '123456',
        'register_date': '2022-01-01',
        'post_categories': ['美妆', '旅行', '美食', '穿搭'],
        'like_count': 5000,
        'note_count': 50,
        'follower_count': 500,
        'post_times': [
            '2024-01-01 10:30:00',
            '2024-01-03 14:20:00',
            '2024-01-05 09:15:00',
            '2024-01-08 20:40:00'
        ]
    }
    
    from utils.config_loader import config
    scorer = UserCredibilityScorer(config)
    
    final_score, dimension_scores = scorer.score_user(sample_user)
    
    print("=" * 50)
    print("用户可信度评分结果")
    print("=" * 50)
    print(f"最终得分: {final_score:.3f}")
    print("\n各维度得分:")
    for dim, score in dimension_scores.items():
        print(f"  {dim}: {score:.3f}")