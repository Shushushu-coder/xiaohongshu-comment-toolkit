"""
配置加载器模块
支持YAML配置文件加载、环境变量覆盖、点号路径访问
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器类"""
    
    _instance = None
    _config: Dict[str, Any] = {}
    _config_file: Optional[Path] = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置加载器"""
        if not self._config:
            self.load_config()
    
    def load_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
            
        Returns:
            配置字典
        """
        if config_file is None:
            # 尝试多个可能的配置文件位置
            possible_paths = [
                Path(__file__).parent.parent / "config" / "config.yaml",
                Path(__file__).parent.parent / "config.yaml",
                Path.cwd() / "config" / "config.yaml",
                Path.cwd() / "config.yaml",
            ]
            
            for path in possible_paths:
                if path.exists():
                    config_file = str(path)
                    break
            
            if config_file is None:
                logger.warning("未找到配置文件，使用默认配置")
                self._config = self._get_default_config()
                return self._config
        
        self._config_file = Path(config_file)
        
        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
            logger.info(f"成功加载配置文件: {self._config_file}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._config = self._get_default_config()
        
        # 应用环境变量覆盖
        self._apply_env_overrides()
        
        return self._config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'scraper': {
                'brand_name': '谷雨',
                'target_keywords': ['谷雨', '护肤', '国货'],
                'max_notes': 50,
                'max_comments_per_note': 100,
                'scroll_pause_time': 2.0,
                'request_delay': (3, 8),
            },
            'browser': {
                'headless': False,
                'disable_images': False,
                'window_size': [1920, 1080],
            },
            'credibility': {
                'min_score': 0.6,
                'weights': {
                    'account_age': 0.20,
                    'content_diversity': 0.25,
                    'engagement_ratio': 0.15,
                    'posting_pattern': 0.20,
                    'follower_quality': 0.20,
                }
            },
            'logging': {
                'level': 'INFO',
                'format': '{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}',
                'rotation': '100 MB',
                'retention': '30 days',
            }
        }
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖配置"""
        # 支持通过环境变量覆盖配置
        # 格式: XIAOHONGSHU_SCRAPER_MAX_NOTES=100
        prefix = "XIAOHONGSHU_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower().replace('_', '.')
                self.set(config_key, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        使用点号路径获取配置值
        
        Args:
            key: 配置键，支持点号路径，如 'scraper.brand_name'
            default: 默认值
            
        Returns:
            配置值
            
        Example:
            >>> config.get('scraper.brand_name')
            '谷雨'
            >>> config.get('scraper.max_notes', 50)
            50
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        使用点号路径设置配置值
        
        Args:
            key: 配置键，支持点号路径
            value: 配置值
            
        Example:
            >>> config.set('scraper.max_notes', 100)
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def reload(self):
        """重新加载配置文件"""
        if self._config_file:
            self.load_config(str(self._config_file))
    
    def save(self, output_file: Optional[str] = None):
        """
        保存配置到文件
        
        Args:
            output_file: 输出文件路径，如果为None则保存到原文件
        """
        if output_file is None:
            output_file = self._config_file
        
        if output_file is None:
            raise ValueError("没有指定输出文件")
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"配置已保存到: {output_path}")


# 全局单例实例
_global_config = ConfigLoader()


def get_config() -> ConfigLoader:
    """获取全局配置实例"""
    return _global_config


# 导出全局config对象，用于向后兼容
config = _global_config


# 便捷函数
def get(key: str, default: Any = None) -> Any:
    """便捷函数：获取配置值"""
    return _global_config.get(key, default)


def set(key: str, value: Any):
    """便捷函数：设置配置值"""
    _global_config.set(key, value)


def reload():
    """便捷函数：重新加载配置"""
    _global_config.reload()


if __name__ == "__main__":
    # 测试代码
    config = get_config()
    print("配置测试:")
    print(f"品牌名称: {config.get('scraper.brand_name')}")
    print(f"最大笔记数: {config.get('scraper.max_notes')}")
    print(f"最小可信度分数: {config.get('credibility.min_score')}")