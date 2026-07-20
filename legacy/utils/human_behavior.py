"""
人类行为模拟工具 - 关键的反反爬组件
"""
import time
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import numpy as np
# 导入 undetected_chromedriver
import undetected_chromedriver as uc


class HumanBehavior:
    """模拟人类浏览行为"""
    
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        # --- 修复: 确保从正确的配置路径读取延迟 ---
        self.min_delay = config.get('scraper.delays.page_load.min', 3)
        self.max_delay = config.get('scraper.delays.page_load.max', 8)
    
    def random_delay(self, min_time=None, max_time=None):
        """随机延迟"""
        min_t = min_time or self.min_delay
        max_t = max_time or self.max_delay
        time.sleep(random.uniform(min_t, max_t))
    
    def human_like_mouse_move(self, element):
        """人类般的鼠标移动（贝塞尔曲线）"""
        action = ActionChains(self.driver)
        
        # 获取当前鼠标位置和目标位置
        try:
            target_x = element.location['x'] + random.randint(0, element.size['width'])
            target_y = element.location['y'] + random.randint(0, element.size['height'])
            
            # 生成贝塞尔曲线路径
            steps = random.randint(10, 20)
            for i in range(steps):
                # 添加随机偏移，模拟手抖
                x_offset = int(target_x * i / steps + random.randint(-5, 5))
                y_offset = int(target_y * i / steps + random.randint(-5, 5))
                
                # 检查偏移量是否合理
                move_x = max(0, x_offset // steps)
                move_y = max(0, y_offset // steps)

                action.move_by_offset(move_x, move_y)
                time.sleep(random.uniform(0.01, 0.05))
            
            action.perform()
        except Exception as e:
            # print(f"鼠标移动失败: {e}") # 调试时可以取消注释
            # 如果移动失败，直接点击
            pass
    
    def human_like_scroll(self, scroll_times=None):
        """人类般的滚动行为"""
        if scroll_times is None:
            scroll_times = random.randint(3, 8)
        
        for _ in range(scroll_times):
            # 随机滚动距离
            scroll_distance = random.randint(300, 800)
            
            # 使用JS滚动（比selenium的scroll更自然）
            self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
            
            # 随机停顿（模拟阅读）
            time.sleep(random.uniform(1, 3))
            
            # 有时候往回滚一点（模拟重新查看）
            if random.random() < 0.3:
                back_distance = random.randint(50, 200)
                self.driver.execute_script(f"window.scrollBy(0, -{back_distance});")
                time.sleep(random.uniform(0.5, 1.5))
    
    def scroll_to_element(self, element):
        """滚动到指定元素"""
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            element
        )
        time.sleep(random.uniform(0.5, 1.5))
    
    def human_like_typing(self, element, text):
        """人类般的输入（不同速度、偶尔删除重打）"""
        element.click()
        time.sleep(random.uniform(0.3, 0.8))
        
        for char in text:
            element.send_keys(char)
            
            # 随机打字速度
            time.sleep(random.uniform(0.05, 0.3))
            
            # 5%概率打错字然后删除
            if random.random() < 0.05:
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                element.send_keys(wrong_char)
                time.sleep(random.uniform(0.1, 0.3))
                element.send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.1, 0.2))
        
        time.sleep(random.uniform(0.5, 1.0))
    
    def simulate_reading(self, min_time=2, max_time=5):
        """模拟阅读页面"""
        read_time = random.uniform(min_time, max_time)
        
        # 在阅读过程中随机移动鼠标
        start_time = time.time()
        while time.time() - start_time < read_time:
            # 随机移动鼠标到页面某个位置
            x = random.randint(100, 1000)
            y = random.randint(100, 800)
            
            try:
                # 重置链
                ActionChains(self.driver).move_by_offset(x, y).perform()
            except:
                pass
            
            time.sleep(random.uniform(0.5, 1.5))
    
    def random_pause(self):
        """随机暂停（模拟思考、走神等）"""
        if random.random() < 0.1:  # 10%概率触发
            pause_time = random.uniform(5, 15)
            time.sleep(pause_time)
    
    def scroll_to_load_more(self, max_scrolls=10):
        """滚动到底部加载更多内容"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for i in range(max_scrolls):
            # 滚动到底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # 等待加载
            time.sleep(random.uniform(2, 4))
            
            # 检查是否加载了新内容
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break  # 没有新内容了
            
            last_height = new_height
            
            # 随机停顿
            if random.random() < 0.3:
                self.random_pause()


class AntiDetection:
    """反检测工具"""
    
    @staticmethod
    def get_random_user_agent():
        """获取随机User-Agent"""
        user_agents = [
            # Windows Chrome
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            # macOS Chrome
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Windows Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        ]
        return random.choice(user_agents)
    
    @staticmethod
    def get_chrome_options(config):
        """获取Chrome配置（反检测）"""
        # --- 修复 V1: 导入 undetected_chromedriver 的 Options ---
        # from selenium.webdriver.chrome.options import Options (这是错误的导入)
        options = uc.ChromeOptions()
        
        # 基础设置
        if config.get('scraper.browser.headless', False):
            options.add_argument('--headless=new')
        
        window_size = config.get('scraper.browser.window_size', '1920,1080')
        options.add_argument(f'--window-size={window_size}')
        
        # --- 修复 V2: 注释掉所有冲突的选项 ---
        # undetected_chromedriver 会自动处理这些, 手动添加会导致冲突
        # options.add_argument('--disable-blink-features=AutomationControlled')
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # options.add_experimental_option('useAutomationExtension', False)
        
        # 性能优化
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # 语言设置
        options.add_argument('--lang=zh-CN')
        options.add_experimental_option('prefs', {
            'intl.accept_languages': 'zh-CN,zh;q=0.9,en;q=0.8'
        })
        
        # 用户数据目录（保持登录状态）
        # --- 修复: 确保从正确的配置路径读取 ---
        user_data_dir = config.get('scraper.browser.user_data_dir')
        if user_data_dir:
            options.add_argument(f'--user-data-dir={user_data_dir}')
        
        return options