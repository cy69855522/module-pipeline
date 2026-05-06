import importlib
import math
import os
import random
import time
from functools import wraps
from glob import glob
from typing import Any, Dict, List, Type

import pandas as pd
from dotenv import load_dotenv

from .progress_logger import ProgressLogger

DATASET_DIR = 'dataset'
API_KEY_PATH = 'api_key.env'
STYLE_BOLD_START = '\033[1m'
STYLE_BOLD_END = '\033[0m'
MILLISECONDS_IN_SECOND = 1000

# Time Interval to Seconds Mapping
TIME_INTERVAL_IN_SECONDS: Dict[str, int] = {
    '1s': 1,
    '15s': 15,
    '30s': 30,
    '1m': 60,
    '3m': 180,
    '5m': 300,
    '15m': 900,
    '30m': 1800,
    '1H': 3600,
    '2H': 7200,
    '4H': 14400,
    '6H': 21600,
    '8H': 28800,
    '12H': 43200,
    '1D': 86400,
    '3D': 259200,
    '1W': 604800,
    '1M': 2592000,  # Approximate: 30 days
}


def get_root() -> str:
    """
    获取项目根目录的绝对路径。
    默认为当前工作目录，子项目可以通过设置环境变量或传递参数来覆盖。

    Returns:
        str: 项目根目录路径。
    """
    return os.getcwd()


def get_dataset_root(root: str | None = None) -> str:
    """
    获取数据集根目录的绝对路径。

    Args:
        root: 项目根目录，默认为 get_root()。

    Returns:
        str: 数据集根目录路径。
    """
    if root is None:
        root = get_root()
    return os.path.join(root, DATASET_DIR)


def get_pu_file_name(pu_name: str) -> str:
    """
    根据 PU (Processing Unit) 名称获取对应的文件名。
    实际上是调用 get_module_file_name。

    Args:
        pu_name (str): PU 名称，通常是大驼峰命名。

    Returns:
        str: 转换后的下划线命名文件名。
    """
    return get_module_file_name(pu_name)


def get_module_file_name(module_name: str) -> str:
    """
    将大驼峰命名的模块名转换为下划线命名。
    例如: 'SmartMoneyTracking' -> 'smart_money_tracking'

    Args:
        module_name (str): 模块名称。

    Returns:
        str: 下划线命名的字符串。
    """
    words = []
    for char in module_name:
        if char.isupper():
            words.append(char.lower())
        else:
            words[-1] += char
    return '_'.join(words)


def get_file_name_by_class_name(class_name: str) -> str:
    """
    将类名转换为文件名（下划线命名）。
    与 get_module_file_name 逻辑相同。

    Args:
        class_name (str): 类名。

    Returns:
        str: 文件名。
    """
    words = []
    for char in class_name:
        if char.isupper():
            words.append(char.lower())
        else:
            words[-1] += char
    return '_'.join(words)


def get_class_by_name(class_name: str, root: str = 'pu') -> Type:
    """
    根据类名动态加载并返回对应的类对象。
    会自动在指定 root 目录下搜索匹配的文件。

    Args:
        class_name (str): 要加载的类名。
        root (str): 搜索的根目录，默认为 'pu'。

    Returns:
        Type: 加载的类对象。

    Raises:
        AssertionError: 如果找不到对应的文件或找到多个匹配文件。
    """
    class_file_name = get_file_name_by_class_name(class_name)
    pattern = f'{root}/**/{class_file_name}.py'
    class_package = glob(pattern, recursive=True)
    assert class_package, f'Cannot find class by pattern {pattern}'
    assert len(
        class_package) == 1, f'Find conflict class names from pattern {pattern}:\n{class_package}'
    class_package = class_package[0].replace('.py', '').replace(os.sep, '.')
    class_package = importlib.import_module(class_package)
    pu_class = getattr(class_package, class_name)
    return pu_class


def get_str_list(content: str, sep: str = ',') -> List[str]:
    """
    将分隔符分隔的字符串转换为列表，并过滤空字符串。

    Args:
        content (str): 输入字符串。
        sep (str): 分隔符，默认为逗号。

    Returns:
        List[str]: 字符串列表。
    """
    return [s for s in content.split(sep) if s] if content else []


def get_terminal_column_size() -> int:
    """
    获取当前终端的列宽。
    如果获取失败，默认返回 100。

    Returns:
        int: 终端列宽。
    """
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 100


def get_datetime_str(datetime: pd.Timestamp) -> str:
    """
    将 pandas Timestamp 对象格式化为字符串。
    格式: 'YYYY-MM-DD HH:MM:SS Z'

    Args:
        datetime (pd.Timestamp): 时间戳对象。

    Returns:
        str: 格式化后的时间字符串。
    """
    return datetime.strftime('%Y-%m-%d %H:%M:%S %Z')


def pad_last_line_bread(csv_path: str):
    """
    确保 CSV 文件最后以换行符结尾。
    如果文件非空且最后没有换行符，则追加一个换行符。

    Args:
        csv_path (str): CSV 文件路径。
    """
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        with open(csv_path, 'rb+') as f:
            f.seek(-1, os.SEEK_END)
            if f.read(1) != b'\n':
                f.write(b'\n')


def exponential_backoff(max_retries: int = 10, initial_delay: float = 1, max_delay: float = 300):
    """
    指数退避装饰器。
    用于在函数执行失败时进行重试，等待时间指数增加，并包含随机抖动。

    Args:
        max_retries (int): 最大重试次数。
        initial_delay (float): 初始延迟(秒)。
        max_delay (float): 最大延迟时间(秒)。

    Returns:
        Callable: 装饰后的函数。
    """

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e  # 最后一次重试后仍失败则抛出异常

                    # 计算带抖动的延迟时间
                    jitter = random.uniform(0, delay * 0.1)  # 添加10%的随机抖动
                    sleep_time = min(delay + jitter, max_delay)

                    print(
                        f"尝试 {attempt + 1}/{max_retries} 失败，等待 {sleep_time:.2f} 秒后重试... 错误: {str(e)}"
                    )
                    time.sleep(sleep_time)

                    # 指数增加延迟
                    delay *= 2

        return wrapper

    return decorator


class ExponentialBackoffRetry:
    """
    指数退避重试类。
    用作对象来管理重试状态，而不是装饰器。
    """

    def __init__(self, max_retries: int = 10, initial_delay: float = 1):
        """
        初始化重试对象。

        Args:
            max_retries (int): 最大重试次数。
            initial_delay (float): 初始延迟(秒)。
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.reset()

    def __call__(self) -> bool:
        """
        执行一次等待。
        如果超过最大重试次数，返回 False。
        否则等待相应的时间后返回 True。

        Returns:
            bool: 是否应该继续重试。
        """
        self.num_retries += 1
        if self.num_retries > self.max_retries:
            return False
        jitter = random.uniform(0, self.delay * 0.1)  # 添加10%的随机抖动
        sleep_time = self.delay + jitter
        for _ in ProgressLogger(range(math.ceil(sleep_time)), desc='Retrying'):
            time.sleep(1)
        self.delay *= 3
        return True

    def reset(self):
        """重置重试计数器和延迟时间。"""
        self.delay = self.initial_delay
        self.num_retries = 0


def load_environment_variable(api_key_path: str | None = None):
    """
    加载环境变量文件。

    Args:
        api_key_path: 环境变量文件路径，默认为 API_KEY_PATH ('api_key.env')。
    """
    load_dotenv(api_key_path or API_KEY_PATH)
