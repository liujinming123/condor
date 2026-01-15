"""
播放意图解析器
"""

import json
import asyncio
import traceback
from typing import List, Dict
import random
import logging

from ..llm.async_client import AsyncLLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOURCE_FILE = __file__


INTENT_DISTRIBUTION = {
    "play_all": 0.20,
    "play_nth": 0.30,
    "play_by_context": 0.20,
    "play_referential": 0.15,
    "play_complex": 0.15
}


class PlaybackIntentParser:
    """播放意图解析器"""

    def __init__(self, llm_client: AsyncLLMClient):
        """
        初始化播放意图解析器

        Args:
            llm_client: LLM客户端
        """
        self.llm_client = llm_client

    def sample_intent_type(self) -> str:
        """
        随机采样播放意图类型

        Returns:
            意图类型
        """
        return random.choices(
            list(INTENT_DISTRIBUTION.keys()),
            weights=list(INTENT_DISTRIBUTION.values())
        )[0]

    async def extract_items(self, recommendation_answer: str, previous_items: list = None) -> List[Dict]:
        """
        从推荐回答中提取可播放的内容项

        Args:
            recommendation_answer: 推荐回答
            previous_items: 前面的项

        Returns:
            可播放项列表
        """
        if previous_items:
            return previous_items

        prompt = f"""分析以下语音助手的推荐回答，提取可以被播放的内容项。

回答：{recommendation_answer}

请返回JSON格式（不要其他文字）：
{{
    "items": [
        {{"name": "内容名称", "index": 1}},
        {{"name": "内容名称", "index": 2}},
        {{"name": "内容名称", "index": 3}}
    ]
}}
"""

        try:
            response = await self.llm_client.call_llm(
                sys_query="你是数据提取专家，擅长从文本中提取结构化信息。",
                user_query=prompt,
                temperature=0.2,
                max_tokens=1000
            )

            if not response:
                logger.warning(f"[{SOURCE_FILE}:89] LLM响应为空")
                return self._fallback_extract(recommendation_answer)

            try:
                result = json.loads(response)
                items = result.get("items", [])
                return items
            except json.JSONDecodeError:
                logger.warning(f"[{SOURCE_FILE}:97] 解析LLM响应失败: {response[:100]}")
                return self._fallback_extract(recommendation_answer)

        except Exception as e:
            logger.error(f"[{SOURCE_FILE}:101] 提取播放项失败: {str(e)}\n{traceback.format_exc()}")
            return self._fallback_extract(recommendation_answer)

    def _fallback_extract(self, text: str) -> List[Dict]:
        """
        备用提取方法

        Args:
            text: 输入文本

        Returns:
            提取的项列表
        """
        items = []
        lines = text.split('\n')

        for i, line in enumerate(lines):
            if '《' in line and '》' in line:
                start = line.find('《') + 1
                end = line.find('》')
                if start < end:
                    name = line[start:end].strip()
                    if name:
                        items.append({
                            "name": name,
                            "index": len(items) + 1
                        })

        return items
