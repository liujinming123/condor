"""
推荐轮生成器
"""

import json
import asyncio
from typing import Dict
import logging

from ..llm.async_client import AsyncLLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


RECOMMEND_PROMPT = """你是一个专业的语音助手对话数据生成专家。

任务：生成语音助手对话的第一轮（推荐轮）。

**类别：**{category}
**场景：**{scenario}
**难度：**{difficulty}

**要求：**
1. 用户问题要自然，符合真实语音场景
2. 助手回答要详细友好，推荐{item_count}个具体内容
3. 每个推荐包含：名称 + 简要描述（50-100字）
4. 如果可能，包含更多元信息（歌手/年代/类型/评分等）
5. 回答结尾要礼貌（如"希望你能喜欢"、"希望这些能帮到你"）
6. 严格格式：q: [问题] answer: [回答]

**知识库参考内容（请从中选择真实内容）：**
{knowledge_samples}

**示例：**
q: 可以分享一部适合睡觉前看的电视剧吗
answer: 《梦华录》，三个经历过各种困境的女人，携手勇闯汴京，并最终姐妹齐心，通过自己的努力将永安楼变成汴京最大酒楼的故事。希望这个电视剧能让你满意。

请生成一条第一轮对话："""


class RecommendRoundGenerator:
    """推荐轮生成器"""

    def __init__(self, llm_client: AsyncLLMClient):
        """
        初始化推荐轮生成器

        Args:
            llm_client: LLM客户端
        """
        self.llm_client = llm_client

    def _map_category_to_knowledge(self, category: str) -> str:
        """
        将类别映射到知识库类别

        Args:
            category: 场景类别

        Returns:
            知识库类别
        """
        if "音乐" in category:
            return "music"
        elif "视频" in category:
            return "video"
        elif "诗词" in category or "播客" in category:
            return "poem"
        else:
            return "music"

    def _format_samples(self, samples: list) -> str:
        """
        格式化样本数据

        Args:
            samples: 样本列表

        Returns:
            格式化字符串
        """
        if not samples:
            return ""

        lines = []
        for item in samples[:5]:
            name = item.get("name", "")
            if not name:
                continue

            if "artist" in item:
                lines.append(f"- {name}（歌手：{item['artist']}）")
            elif "author" in item:
                lines.append(f"- {name}（作者：{item['author']}）")
            else:
                lines.append(f"- {name}")

        return "\n".join(lines)

    async def generate(
        self,
        category: str,
        scenario: str,
        difficulty: str,
        knowledge_manager,
        item_count: int = 5
    ) -> Dict:
        """
        生成推荐轮对话

        Args:
            category: 类别
            scenario: 场景
            difficulty: 难度
            knowledge_manager: 知识库管理器
            item_count: 推荐数量

        Returns:
            对话数据
        """
        knowledge_category = self._map_category_to_knowledge(category)
        knowledge_samples = knowledge_manager.get_knowledge_context(
            knowledge_category, count=item_count
        )

        prompt = RECOMMEND_PROMPT.format(
            category=category,
            scenario=scenario,
            difficulty=difficulty,
            item_count=item_count,
            knowledge_samples=knowledge_samples
        )

        try:
            response = await self.llm_client.call_llm(
                sys_query="你是一个专业的语音助手对话数据生成专家，擅长生成自然、友好、准确的对话数据。",
                user_query=prompt,
                max_tokens=2000,
                temperature=0.7
            )

            dialogue = self._parse_dialogue(response)

            dialogue["round_type"] = "recommendation"
            dialogue["extracted_items"] = knowledge_samples[:item_count]

            return dialogue

        except Exception as e:
            logger.error(f"生成推荐轮失败: {str(e)}")
            return {
                "q": "",
                "a": "",
                "round_type": "recommendation",
                "extracted_items": []
            }

    def _parse_dialogue(self, response: str) -> Dict:
        """
        解析LLM返回的对话

        Args:
            response: LLM响应

        Returns:
            解析后的对话
        """
        dialogue = {"q": "", "a": ""}

        if "q:" in response and "answer:" in response:
            parts = response.split("answer:")
            if len(parts) == 2:
                question_part = parts[0]
                answer_part = parts[1]

                q_start = question_part.find("q:")
                if q_start != -1:
                    dialogue["q"] = question_part[q_start + 2:].strip()

                dialogue["a"] = answer_part.strip()
        elif "q:" in response:
            q_start = response.find("q:")
            q_end = response.find("\n", q_start)
            if q_end == -1:
                q_end = len(response)
            dialogue["q"] = response[q_start + 2:q_end].strip()
        else:
            dialogue["q"] = response.strip()
            dialogue["a"] = ""

        return dialogue
