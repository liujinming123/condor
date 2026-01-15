"""
异步LLM客户端
"""

import asyncio
from typing import List, Dict, Any
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncLLMClient:
    """异步LLM客户端，支持并发控制"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        max_concurrent: int = 5,
        request_interval: float = 0.5
    ):
        """
        初始化LLM客户端

        Args:
            base_url: LLM API地址
            api_key: API密钥
            model: 模型名称
            max_concurrent: 最大并发请求数
            request_interval: 请求间隔（秒）
        """
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.request_interval = request_interval
        self.max_concurrent = max_concurrent

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _call_llm_internal(
        self,
        sys_query: str,
        user_query: str,
        max_tokens: int = 2000,
        temperature: float = 0.5
    ) -> str:
        """
        内部LLM调用方法

        Args:
            sys_query: 系统提示词
            user_query: 用户查询
            max_tokens: 最大token数
            temperature: 温度参数

        Returns:
            LLM响应内容
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": sys_query},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False,
                extra_body={
                    "top_k": 20,
                    "chat_template_kwargs": {"enable_thinking": True}
                }
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}")
            raise

    async def call_llm(
        self,
        sys_query: str,
        user_query: str,
        max_tokens: int = 2000,
        temperature: float = 0.5
    ) -> str:
        """
        调用LLM（带并发控制）

        Args:
            sys_query: 系统提示词
            user_query: 用户查询
            max_tokens: 最大token数
            temperature: 温度参数

        Returns:
            LLM响应内容
        """
        async with self.semaphore:
            await asyncio.sleep(self.request_interval)
            return await self._call_llm_internal(
                sys_query, user_query, max_tokens, temperature
            )

    async def batch_generate(
        self,
        tasks: List[Dict[str, str]],
        show_progress: bool = True
    ) -> List[str]:
        """
        批量生成

        Args:
            tasks: 任务列表，每个任务包含sys和user字段
            show_progress: 是否显示进度

        Returns:
            生成结果列表
        """
        from tqdm import tqdm

        results = []
        total_tasks = len(tasks)

        if show_progress:
            pbar = tqdm(total=total_tasks, desc="生成进度")

        for task in tasks:
            try:
                result = await self.call_llm(
                    task["sys"],
                    task["user"]
                )
                results.append(result)
            except Exception as e:
                logger.error(f"生成失败: {str(e)}")
                results.append("")

            if show_progress:
                pbar.update(1)

        if show_progress:
            pbar.close()

        return results

    async def close(self):
        """关闭客户端"""
        await self.client.close()
