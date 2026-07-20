#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志系统模块
提供彩色日志输出、文件记录、错误追踪等功能
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }
    
    def format(self, record):
        """格式化日志记录"""
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # 调用父类方法
        return super().format(record)


class Logger:
    """日志管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化日志系统"""
        if self._initialized:
            return
            
        self.logger = logging.getLogger('ReviewCrawler')
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加handler
        if self.logger.handlers:
            return
        
        # 创建日志目录
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        
        # 设置日志文件路径
        timestamp = datetime.now().strftime('%Y%m%d')
        self.log_file = self.log_dir / f'crawler_{timestamp}.log'
        self.error_log_file = self.log_dir / f'error_{timestamp}.log'
        
        # 控制台处理器（彩色输出）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # 文件处理器（所有日志）
        file_handler = logging.FileHandler(
            self.log_file, 
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # 错误文件处理器（仅错误日志）
        error_handler = logging.FileHandler(
            self.error_log_file,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # 添加处理器
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        
        self._initialized = True
        
    def debug(self, message: str):
        """调试信息"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """一般信息"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """警告信息"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """错误信息"""
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False):
        """严重错误"""
        self.logger.critical(message, exc_info=exc_info)
    
    def exception(self, message: str):
        """异常信息（自动包含堆栈）"""
        self.logger.exception(message)


# 全局日志实例
_logger_instance: Optional[Logger] = None


def get_logger() -> Logger:
    """
    获取全局日志实例
    
    Returns:
        Logger: 日志管理器实例
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance


def setup_logger(log_level: str = 'INFO', log_dir: str = 'logs') -> Logger:
    """
    设置日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志目录路径
    
    Returns:
        Logger: 配置好的日志实例
    """
    logger = get_logger()
    
    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.logger.setLevel(level)
    
    # 更新日志目录
    logger.log_dir = Path(log_dir)
    logger.log_dir.mkdir(exist_ok=True)
    
    return logger


# 便捷函数
def debug(message: str):
    """记录调试信息"""
    get_logger().debug(message)


def info(message: str):
    """记录一般信息"""
    get_logger().info(message)


def warning(message: str):
    """记录警告信息"""
    get_logger().warning(message)


def error(message: str, exc_info: bool = False):
    """记录错误信息"""
    get_logger().error(message, exc_info=exc_info)


def critical(message: str, exc_info: bool = False):
    """记录严重错误"""
    get_logger().critical(message, exc_info=exc_info)


def exception(message: str):
    """记录异常信息（自动包含堆栈）"""
    get_logger().exception(message)


if __name__ == '__main__':
    # 测试日志系统
    logger = get_logger()
    
    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    logger.critical("这是一条严重错误信息")
    
    # 测试异常记录
    try:
        1 / 0
    except Exception as e:
        logger.exception("捕获到异常")
    
    print(f"\n日志文件保存在: {logger.log_file}")
    print(f"错误日志保存在: {logger.error_log_file}")