"""
小红书爬虫主程序
谷雨品牌评论收集 + 用户可信度评分
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_loader import config
from utils.logger import setup_logger
from scrapers.xiaohongshu_scraper import XiaohongshuScraper
from utils.credibility_scorer import UserCredibilityScorer, CommentFilter
import pandas as pd
from datetime import datetime
import json


class GuyuCommentCollector:
    """谷雨品牌评论收集器"""
    
    def __init__(self):
        
        logger_config_dict = config.get('logger', {})
        log_level_str = logger_config_dict.get('level', 'INFO') # 默认为 'INFO'
        self.logger = setup_logger(log_level_str)

        self.scraper = XiaohongshuScraper(config, self.logger)
        self.credibility_scorer = UserCredibilityScorer(config)
        self.comment_filter = CommentFilter(config)
        
        self.all_comments = []
        self.all_users = []
    
    def run(self):
        """主运行流程"""
        self.logger.info("=" * 60)
        self.logger.info("谷雨品牌评论收集系统启动")
        self.logger.info("=" * 60)
        
        try:
            # 1. 初始化浏览器
            if not self.scraper.initialize():
                self.logger.error("浏览器初始化失败，程序退出")
                return
            
            # 2. 登录
            if not self.scraper.login(use_cookie=True):
                self.logger.error("登录失败，程序退出")
                return
            
            # 3. 搜索谷雨相关内容
            keywords = config.get('search_keywords', ['谷雨'])
            for keyword in keywords:
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"开始搜索关键词: {keyword}")
                self.logger.info(f"{'='*60}\n")
                
                if not self.scraper.search_brand(keyword):
                    self.logger.warning(f"搜索 {keyword} 失败，跳过")
                    continue
                
                # 4. 获取笔记链接
                max_posts = config.get('scraper.max_posts_to_scrape', 50)
                post_links = self.scraper.get_post_links(max_posts=max_posts)
                
                if not post_links:
                    self.logger.warning(f"未找到 {keyword} 相关笔记")
                    continue
                
                # 5. 爬取每个笔记的评论
                for idx, post_url in enumerate(post_links, 1):
                    self.logger.info(f"\n处理笔记 {idx}/{len(post_links)}: {post_url}")
                    
                    comments = self.scraper.scrape_post_comments(post_url)
                    
                    if comments:
                        self.logger.info(f"收集到 {len(comments)} 条相关评论")
                        self.all_comments.extend(comments)
                        
                        # 收集用户信息
                        self._collect_user_info(comments)
                    
                    # 定期保存（防止意外中断导致数据丢失）
                    if idx % 10 == 0:
                        self._save_intermediate_data()
            
            # 6. 数据处理和过滤
            self._process_and_filter_data()
            
            # 7. 最终保存
            self._save_final_data()
            
            # 8. 生成报告
            self._generate_report()
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("数据收集完成！")
            self.logger.info("=" * 60)
            
        except KeyboardInterrupt:
            self.logger.warning("\n用户中断程序")
            self._save_intermediate_data()
        
        except Exception as e:
            self.logger.error(f"程序执行出错: {e}", exc_info=True)
            self._save_intermediate_data()
        
        finally:
            self.scraper.close()
    
    def _collect_user_info(self, comments):
        """收集评论用户的详细信息"""
        unique_users = set()
        for comment in comments:
            user_id = comment.get('user_id')
            if user_id and user_id not in unique_users:
                unique_users.add(user_id)
        
        self.logger.info(f"需要收集 {len(unique_users)} 个用户的详细信息")
        
        for user_id in unique_users:
            # 检查是否已经收集过
            if any(u['user_id'] == user_id for u in self.all_users):
                continue
            
            user_data = self.scraper.scrape_user_profile(user_id)
            if user_data:
                self.all_users.append(user_data)
    
    def _process_and_filter_data(self):
        """处理和过滤数据"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("开始数据处理和过滤")
        self.logger.info("=" * 60)
        
        if not self.all_comments:
            self.logger.warning("没有收集到评论数据")
            return
        
        # 转换为DataFrame
        comments_df = pd.DataFrame(self.all_comments)
        users_df = pd.DataFrame(self.all_users)
        
        self.logger.info(f"\n原始数据统计:")
        self.logger.info(f"  评论数: {len(comments_df)}")
        self.logger.info(f"  用户数: {len(users_df)}")
        
        # 评论质量过滤
        self.logger.info("\n执行评论质量过滤...")
        filtered_comments = self.comment_filter.filter_comments(comments_df)
        
        # 用户可信度评分
        self.logger.info("\n执行用户可信度评分...")
        if len(users_df) > 0:
            threshold = 0.6  # 可调整
            filtered_users, scores_df = self.credibility_scorer.filter_users(
                users_df, 
                threshold=threshold
            )
            
            # 只保留高可信度用户的评论
            high_quality_user_ids = set(filtered_users['user_id'].tolist())
            filtered_comments = filtered_comments[
                filtered_comments['user_id'].isin(high_quality_user_ids)
            ]
            
            self.logger.info(f"\n最终高质量数据:")
            self.logger.info(f"  评论数: {len(filtered_comments)}")
            self.logger.info(f"  用户数: {len(filtered_users)}")
            
            # 保存评分详情
            scores_df.to_csv(
                Path(config['storage']['output_dir']) / 'user_credibility_scores.csv',
                index=False,
                encoding='utf-8-sig'
            )
            
            # 更新数据
            self.filtered_comments = filtered_comments
            self.filtered_users = filtered_users
        else:
            self.logger.warning("没有用户数据，跳过可信度评分")
            self.filtered_comments = filtered_comments
            self.filtered_users = users_df
    
    def _save_intermediate_data(self):
        """保存中间数据（防止数据丢失）"""
        self.logger.info("保存中间数据...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = Path(config['storage']['backup_dir'])
        
        if self.all_comments:
            backup_file = backup_dir / f"comments_backup_{timestamp}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_comments, f, ensure_ascii=False, indent=2)
            self.logger.info(f"评论数据已备份: {backup_file}")
        
        if self.all_users:
            backup_file = backup_dir / f"users_backup_{timestamp}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_users, f, ensure_ascii=False, indent=2)
            self.logger.info(f"用户数据已备份: {backup_file}")
    
    def _save_final_data(self):
        """保存最终处理后的数据"""
        self.logger.info("\n保存最终数据...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(config['storage']['output_dir'])
        
        # 保存过滤后的评论
        if hasattr(self, 'filtered_comments') and len(self.filtered_comments) > 0:
            # CSV格式
            csv_file = output_dir / f"guyu_comments_filtered_{timestamp}.csv"
            self.filtered_comments.to_csv(csv_file, index=False, encoding='utf-8-sig')
            self.logger.info(f"✓ 评论数据(CSV): {csv_file}")
            
            # JSON格式
            json_file = output_dir / f"guyu_comments_filtered_{timestamp}.json"
            self.filtered_comments.to_json(
                json_file, 
                orient='records', 
                force_ascii=False, 
                indent=2
            )
            self.logger.info(f"✓ 评论数据(JSON): {json_file}")
        
        # 保存过滤后的用户
        if hasattr(self, 'filtered_users') and len(self.filtered_users) > 0:
            csv_file = output_dir / f"guyu_users_filtered_{timestamp}.csv"
            self.filtered_users.to_csv(csv_file, index=False, encoding='utf-8-sig')
            self.logger.info(f"✓ 用户数据(CSV): {csv_file}")
    
    def _generate_report(self):
        """生成数据收集报告"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("数据收集报告")
        self.logger.info("=" * 60)
        
        report = {
            'collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'target_brand': config['target_brand'],
            'raw_data': {
                'comments': len(self.all_comments),
                'users': len(self.all_users)
            },
            'filtered_data': {
                'comments': len(self.filtered_comments) if hasattr(self, 'filtered_comments') else 0,
                'users': len(self.filtered_users) if hasattr(self, 'filtered_users') else 0
            }
        }
        
        # 打印报告
        self.logger.info(f"\n目标品牌: {report['target_brand']}")
        self.logger.info(f"收集时间: {report['collection_time']}")
        self.logger.info(f"\n原始数据:")
        self.logger.info(f"  评论数: {report['raw_data']['comments']}")
        self.logger.info(f"  用户数: {report['raw_data']['users']}")
        self.logger.info(f"\n过滤后数据:")
        self.logger.info(f"  评论数: {report['filtered_data']['comments']}")
        self.logger.info(f"  用户数: {report['filtered_data']['users']}")
        
        if report['raw_data']['comments'] > 0:
            filter_rate = report['filtered_data']['comments'] / report['raw_data']['comments'] * 100
            self.logger.info(f"  保留率: {filter_rate:.1f}%")
        
        # 保存报告
        report_file = Path(config['storage']['output_dir']) / 'collection_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        self.logger.info(f"\n报告已保存: {report_file}")


def main():
    """程序入口"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║        小红书品牌评论收集系统 v1.0                       ║
    ║        Xiaohongshu Brand Comment Collector              ║
    ║                                                          ║
    ║        目标品牌: 谷雨 (GUYU)                            ║
    ║        功能: 评论收集 + 用户可信度评分                   ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    collector = GuyuCommentCollector()
    collector.run()


if __name__ == "__main__":
    main()