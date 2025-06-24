import logging
import sys
import os
import json


class SystemMessageFilter(logging.Filter):
    """专门过滤冗长的系统配置消息的日志过滤器"""
    
    def filter(self, record):
        """过滤日志记录"""
        try:
            # 只过滤DEBUG级别的特定冗长系统消息
            if record.levelno == logging.DEBUG:
                message = record.getMessage()
                
                # 过滤包含大量系统配置信息的DEBUG日志
                if any(keyword in message for keyword in [
                    'type="dynacfg"',
                    'type="functionmsg"'
                ]) and len(message) > 500:  # 只过滤超长的系统消息
                    return False
                
                # 过滤包含大量XML配置的消息
                if ('<?xml version="1.0"?>' in message and 
                    any(xml_tag in message for xml_tag in ['<dynacfg>', '<functionmsg>']) and 
                    len(message) > 500):
                    return False
            
            return True
            
        except Exception as e:
            # 如果过滤器出错，不阻止日志输出
            return True


def _reset_logger(log):
    for handler in log.handlers:
        handler.close()
        log.removeHandler(handler)
        del handler
    log.handlers.clear()
    log.propagate = False
    
    # 创建系统消息过滤器
    system_filter = SystemMessageFilter()
    
    console_handle = logging.StreamHandler(sys.stdout)
    console_handle.setFormatter(
        logging.Formatter(
            "[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    console_handle.addFilter(system_filter)  # 添加过滤器
    
    file_handle = logging.FileHandler("run.log", encoding="utf-8")
    file_handle.setFormatter(
        logging.Formatter(
            "[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    file_handle.addFilter(system_filter)  # 添加过滤器
    
    log.addHandler(file_handle)
    log.addHandler(console_handle)


def _get_logger():
    log = logging.getLogger("log")
    _reset_logger(log)
    
    # 默认日志级别
    log_level = logging.INFO
    
    # 尝试从配置文件读取日志级别
    try:
        # 读取配置文件
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                level_str = config.get("log_level", "INFO")
                
                # 将字符串日志级别转换为logging模块常量
                if level_str == "DEBUG":
                    log_level = logging.DEBUG
                elif level_str == "INFO":
                    log_level = logging.INFO
                elif level_str == "WARNING":
                    log_level = logging.WARNING
                elif level_str == "ERROR":
                    log_level = logging.ERROR
                elif level_str == "CRITICAL":
                    log_level = logging.CRITICAL
                
                print(f"设置日志级别为: {level_str}")
    except Exception as e:
        print(f"读取日志配置错误，使用默认INFO级别: {e}")
    
    log.setLevel(log_level)
    return log


# 日志句柄
logger = _get_logger()


# 允许动态设置日志级别的函数
def set_logger_level(level_str):
    """
    动态设置日志级别
    :param level_str: 日志级别字符串 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO, 
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    if level_str in level_map:
        logger.setLevel(level_map[level_str])
        logger.info(f"日志级别已设置为: {level_str}")
    else:
        logger.warning(f"无效的日志级别: {level_str}，可用值: {', '.join(level_map.keys())}")
