"""
验证码处理工具
"""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import io


class CaptchaHandler:
    """验证码处理器"""
    
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger
    
    def check_captcha(self, timeout=3):
        """检测是否出现验证码"""
        try:
            # 小红书常见的验证码元素
            captcha_selectors = [
                "//div[contains(@class, 'verify')]",
                "//div[contains(@class, 'captcha')]",
                "//div[contains(text(), '验证')]",
                "//iframe[contains(@src, 'captcha')]"
            ]
            
            for selector in captcha_selectors:
                try:
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if element:
                        self.logger.warning("检测到验证码!")
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            return False
    
    def handle_slider_captcha(self):
        """
        处理滑动验证码
        注意：小红书的滑动验证码非常智能，纯自动化很难通过
        这里提供半自动方案：检测到验证码后暂停，等待人工滑动
        """
        self.logger.warning("检测到滑动验证码，请手动完成验证...")
        
        # 方案1：暂停等待人工操作（推荐）
        input("请在浏览器中手动完成滑动验证，完成后按Enter继续...")
        
        # 方案2：尝试自动滑动（成功率低，仅供参考）
        # self._auto_slide_captcha()
        
        time.sleep(2)
        return True
    
    def _auto_slide_captcha(self):
        """
        自动滑动验证码（参考实现，实际效果有限）
        小红书的验证码会检测鼠标轨迹的真实性，纯线性移动会被识别
        """
        try:
            # 查找滑块元素
            slider = self.driver.find_element(By.CLASS_NAME, "slide-button")
            
            # 获取需要滑动的距离（需要通过图像识别缺口位置）
            distance = self._get_slide_distance()
            
            # 生成人类般的滑动轨迹
            tracks = self._generate_human_slide_track(distance)
            
            # 按住滑块
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(self.driver).click_and_hold(slider).perform()
            
            # 按轨迹移动
            for track in tracks:
                ActionChains(self.driver).move_by_offset(track, 0).perform()
                time.sleep(random.uniform(0.001, 0.003))
            
            # 释放滑块
            time.sleep(random.uniform(0.5, 1.0))
            ActionChains(self.driver).release().perform()
            
            time.sleep(2)
            
        except Exception as e:
            self.logger.error(f"自动滑动失败: {e}")
            return False
    
    def _get_slide_distance(self):
        """
        获取滑动距离（需要图像识别）
        这里返回一个估计值，实际项目中需要用CV算法识别缺口
        """
        # 截图
        screenshot = self.driver.get_screenshot_as_png()
        
        # TODO: 使用opencv识别缺口位置
        # 这里简化处理，返回固定值
        return random.randint(200, 250)
    
    def _generate_human_slide_track(self, distance):
        """
        生成人类般的滑动轨迹
        使用加速度模型：先加速、后减速，加入随机抖动
        """
        tracks = []
        current = 0
        mid = distance * 0.8  # 80%的位置开始减速
        
        t = 0.2
        v = 0
        
        while current < distance:
            if current < mid:
                # 加速阶段
                a = random.uniform(2, 5)
            else:
                # 减速阶段
                a = -random.uniform(3, 5)
            
            v0 = v
            v = v0 + a * t
            move = v0 * t + 0.5 * a * t * t
            current += move
            
            # 加入随机抖动
            move += random.uniform(-1, 1)
            tracks.append(round(move))
        
        return tracks
    
    def wait_for_captcha_disappear(self, timeout=30):
        """等待验证码消失"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.check_captcha(timeout=1):
                self.logger.info("验证码已通过")
                return True
            time.sleep(1)
        
        self.logger.error("验证码处理超时")
        return False


class CookieManager:
    """Cookie管理器"""
    
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger
    
    def save_cookies(self, filepath):
        """保存cookies"""
        import json
        from pathlib import Path
        
        cookies = self.driver.get_cookies()
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Cookies已保存到: {filepath}")
    
    def load_cookies(self, filepath):
        """加载cookies"""
        import json
        from pathlib import Path
        
        if not Path(filepath).exists():
            self.logger.warning(f"Cookie文件不存在: {filepath}")
            return False
        
        with open(filepath, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        for cookie in cookies:
            # 删除一些可能导致问题的字段
            if 'expiry' in cookie:
                del cookie['expiry']
            try:
                self.driver.add_cookie(cookie)
            except Exception as e:
                self.logger.debug(f"添加cookie失败: {e}")
        
        self.logger.info(f"Cookies已加载: {filepath}")
        return True
    
    def check_login_status(self):
        """检查登录状态"""
        try:
            # 检查是否有登录相关的cookie
            cookies = self.driver.get_cookies()
            cookie_names = [c['name'] for c in cookies]
            
            # 小红书的关键cookie（根据实际情况调整）
            required_cookies = ['web_session', 'xsecappid']  # 示例
            
            for required in required_cookies:
                if required not in cookie_names:
                    return False
            
            # 尝试访问需要登录的页面
            self.driver.get("https://www.xiaohongshu.com/user/profile")
            time.sleep(2)
            
            # 检查是否跳转到登录页
            if "login" in self.driver.current_url:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"检查登录状态失败: {e}")
            return False