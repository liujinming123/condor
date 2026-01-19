"""
LLM调用重试辅助工具
"""

import asyncio
import logging
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)


async def call_with_retry(
    func: Callable,
    max_retries: int = 3,
    retry_interval: float = 1.0,
    func_name: str = "function"
) -> Optional[Any]:
    """
    带重试的函数调用

    Args:
        func: 要调用的异步函数
        max_retries: 最大重试次数
        retry_interval: 重试间隔（秒）
        func_name: 函数名称（用于日志）

    Returns:
        函数返回值，失败多次后返回None
    """
    for attempt in range(max_retries):
        try:
            result = await func()
            if result is not None:
                return result
            
            if attempt < max_retries - 1:
                logger.warning(f"{func_name} 返回空值，尝试重试 ({attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_interval)
                continue
            
            logger.warning(f"{func_name} 返回空值，已达最大重试次数")
            return None
            
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"{func_name} 调用失败，尝试重试 ({attempt + 1}/{max_retries}): {str(e)}")
                await asyncio.sleep(retry_interval)
                continue
            logger.error(f"{func_name} 调用失败: {str(e)}")
            raise
    
    return None
