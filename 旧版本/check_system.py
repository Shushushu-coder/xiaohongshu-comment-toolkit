"""
系统测试脚本
用于验证各个组件是否正常工作
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试模块导入"""
    print("测试1: 模块导入...")
    try:
        from utils.config_loader import config
        from utils.logger import setup_logger
        from utils.human_behavior import HumanBehavior, AntiDetection
        from utils.captcha_handler import CaptchaHandler, CookieManager
        from utils.credibility_scorer import UserCredibilityScorer, CommentFilter
        from scrapers.xiaohongshu_scraper import XiaohongshuScraper
        print("✓ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def test_config():
    """测试配置加载"""
    print("\n测试2: 配置加载...")
    try:
        from utils.config_loader import config
        target_brand = config.get('target_brand')
        print(f"✓ 配置加载成功，目标品牌: {target_brand}")
        return True
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return False

def test_logger():
    """测试日志系统"""
    print("\n测试3: 日志系统...")
    try:
        from utils.config_loader import config
        from utils.logger import setup_logger
        
        # --- 修复 V2 ---
        # 之前的错误 ('ConfigLoader' object has no attribute 'upper')
        # 和新的错误 ('dict' object has no attribute 'upper')
        # 强烈暗示 setup_logger 期望接收一个 *字符串* (可能是日志级别)
        # 并且它会对这个字符串调用 .upper()。
        # 
        # 让我们从配置中提取 'level' 字符串，并传递它。
        logger_config_dict = config.get('logger', {})
        log_level_str = logger_config_dict.get('level', 'INFO') # 默认为 'INFO'
        
        # 将日志级别字符串传递给 setup_logger
        logger = setup_logger(log_level_str) 
        # --- 修复结束 ---

        logger.info("测试日志信息")
        print("✓ 日志系统正常")
        return True
    except Exception as e:
        print(f"✗ 日志系统失败: {e}")
        return False

def test_credibility_scorer():
    """测试可信度评分器"""
    print("\n测试4: 可信度评分器...")
    try:
        from utils.config_loader import config
        from utils.credibility_scorer import UserCredibilityScorer
        
        scorer = UserCredibilityScorer(config)
        
        # 测试用户数据
        test_user = {
            'user_id': 'test_123',
            'register_date': '2022-01-01',
            'post_categories': ['美妆', '旅行', '美食'],
            'like_count': 3000,
            'note_count': 30,
            'follower_count': 300,
            'post_times': [
                '2024-01-01 10:00:00',
                '2024-01-03 14:00:00',
                '2024-01-05 09:00:00'
            ]
        }
        
        final_score, dimension_scores = scorer.score_user(test_user)
        
        print(f"  最终得分: {final_score:.3f}")
        print(f"  各维度得分:")
        for dim, score in dimension_scores.items():
            print(f"    {dim}: {score:.3f}")
        
        print("✓ 可信度评分器正常")
        return True
    except Exception as e:
        print(f"✗ 可信度评分器失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chrome_driver():
    """测试Chrome驱动"""
    print("\n测试5: Chrome驱动...")
    try:
        import undetected_chromedriver as uc
        from utils.config_loader import config
        from utils.human_behavior import AntiDetection
        
        options = AntiDetection.get_chrome_options(config)
        options.add_argument('--headless=new')  # 无头模式测试
        
        driver = uc.Chrome(options=options)
        driver.get("https://www.baidu.com")
        title = driver.title
        driver.quit()
        
        print(f"✓ Chrome驱动正常 (测试页面: {title})")
        return True
    except Exception as e:
        print(f"✗ Chrome驱动失败: {e}")
        print("  提示: 请确保已安装Chrome浏览器")
        return False

def test_directory_structure():
    """测试目录结构"""
    print("\n测试6: 目录结构...")
    try:
        required_dirs = [
            'data/output',
            'data/backup',
            'data/cookies',
            'logs'
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                print(f"  创建目录: {dir_path}")
        
        print("✓ 目录结构正常")
        return True
    except Exception as e:
        print(f"✗ 目录结构检查失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("小红书爬虫系统 - 组件测试")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config,
        test_logger,
        test_credibility_scorer,
        test_directory_structure,
        # test_chrome_driver,  # 可选，需要时间
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"测试出错: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n✓ 所有测试通过！系统可以正常运行")
        print("\n运行爬虫: python main.py")
    else:
        print("\n✗ 部分测试失败，请检查错误信息")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)