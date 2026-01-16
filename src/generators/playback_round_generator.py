"""
播放轮生成器
"""

import asyncio
import random
import traceback
from typing import Dict, List
import logging

from ..llm.async_client import AsyncLLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOURCE_FILE = __file__


PLAYBACK_PROMPTS = {
    "play_all": """基于前面对话，生成最后一轮播放对话。

**前面对话：**
{dialogue_history}

**可播放的项：**
{items_list}

**播放意图：**直接播放全部推荐内容

**要求：**
1. 用户问题简洁："播放"、"放吧"、"来吧"等
2. 助手回答：播放第一个推荐内容
3. 严格格式：q: [问题] answer: [回答]

**示例：**
q: 播放
answer: 播放《梦华录》

请生成最后一轮：""",

    "play_nth": """基于前面对话，生成最后一轮播放对话。

**前面对话：**
{dialogue_history}

**可播放的项：**
{items_list}

**播放意图：**播放第{nth}个

**要求：**
1. 用户问题要多样："放第二个"/"播放第三首"/"我想听第一个"/"第几首"等
2. 助手回答：播放对应序号的内容
3. 严格格式：q: [问题] answer: [回答]

**示例：**
意图：播放第2个
q: 放第二个吧直接放
answer: 播放《唱不完的故事》

请生成最后一轮：""",

    "play_by_context": """基于前面对话，生成最后一轮播放对话。

**前面对话：**
{dialogue_history}

**可播放的项：**
{items_list}

**播放意图：**基于上下文条件播放
**条件：**{condition}

**要求：**
1. 用户问题要明确表达条件
2. 助手回答要准确匹配上下文中的内容
3. 如果条件涉及多个匹配项，选择最合适的
4. 严格格式：q: [问题] answer: [回答]

**示例：**
上下文：列举了多个歌手
意图：播放特定歌手的歌
q: 播放周杰伦的第一个人合唱的歌
answer: 播放周杰伦和蔡依林合唱的歌

请生成最后一轮：""",

    "play_referential": """基于前面对话，生成最后一轮播放对话。

**前面对话：**
{dialogue_history}

**可播放的项：**
{items_list}

**播放意图：**模糊指代播放
**指代词：**{referential}

**要求：**
1. 用户问题简洁："放前面那个"/"播放这个"/"就它了"等
2. 助手回答：播放第一个推荐内容
3. 严格格式：q: [问题] answer: [回答]

**示例：**
q: 放前面那个
answer: 播放《梦华录》

请生成最后一轮：""",

    "play_complex": """基于前面对话，生成最后一轮播放对话。

**前面对话：**
{dialogue_history}

**可播放的项：**
{items_list}

**播放意图：**多轮复杂播放
**复杂条件：**{complex_condition}

**要求：**
1. 用户问题明确表达复杂条件
2. 助手回答要准确匹配上下文和条件
3. 可能需要结合多个轮的信息
4. 严格格式：q: [问题] answer: [回答]

**示例：**
q: 播放周杰伦和蔡依林合唱的歌
answer: 播放周杰伦和蔡依林合唱的歌

请生成最后一轮："""
}


class PlaybackRoundGenerator:
    """播放轮生成器"""

    def __init__(self, llm_client: AsyncLLMClient):
        """
        初始化播放轮生成器

        Args:
            llm_client: LLM客户端
        """
        self.llm_client = llm_client

    def _format_dialogue_history(self, rounds: List[Dict]) -> str:
        """
        格式化对话历史

        Args:
            rounds: 对话轮列表

        Returns:
            格式化字符串
        """
        lines = []
        for round in rounds[-3:]:
            q = round.get("q", "")
            a = round.get("a", "")
            if q:
                lines.append(f"Q: {q}")
            if a:
                lines.append(f"A: {a}")
        return "\n".join(lines)

    def _format_items(self, items: List[Dict]) -> str:
        """
        格式化项列表

        Args:
            items: 项列表

        Returns:
            格式化字符串
        """
        lines = []
        for item in items[:5]:
            name = item.get("name", "")
            if "artist" in item:
                lines.append(f"{item['index']}. {name}（{item['artist']}）")
            elif "author" in item:
                lines.append(f"{item['index']}. {name}（{item['author']}）")
            else:
                lines.append(f"{item['index']}. {name}")
        return "\n".join(lines)

    def _generate_context_condition(self, items: List[Dict]) -> str:
        """
        生成上下文条件

        Args:
            items: 项列表

        Returns:
            条件字符串
        """
        if not items or not items[0]:
            return "推荐的内容"

        conditions = []

        first_item = items[0] or {}
        if first_item.get("artist"):
            singers = list(set(item.get("artist", "") or "" for item in items))
            if len(singers) > 1:
                conditions.append(f"歌手{singers[0]}和{singers[1]}合唱的")
            else:
                conditions.append(f"{singers[0]}的")
        elif first_item.get("author"):
            authors = list(set(item.get("author", "") or "" for item in items))
            if len(authors) > 1:
                conditions.append(f"{authors[0]}代诗人{authors[1]}的作品")
            else:
                conditions.append(f"{authors[0]}的诗")

        return conditions[0] if conditions else "推荐的内容"

    async def generate(
        self,
        previous_rounds: List[Dict],
        items: List[Dict],
        intent_type: str,
        knowledge_manager
    ) -> Dict:
        """
        生成播放轮对话

        Args:
            previous_rounds: 前面的轮次
            items: 可播放的项
            intent_type: 播放意图类型
            knowledge_manager: 知识库管理器

        Returns:
            对话数据
        """
        history_str = self._format_dialogue_history(previous_rounds)
        items_str = self._format_items(items)

        prompt = PLAYBACK_PROMPTS[intent_type]

        if intent_type == "play_nth":
            nth = random.randint(1, len(items)) if items else 1
            prompt = prompt.format(
                dialogue_history=history_str,
                items_list=items_str,
                nth=nth
            )
        elif intent_type == "play_by_context":
            condition = self._generate_context_condition(items)
            prompt = prompt.format(
                dialogue_history=history_str,
                items_list=items_str,
                condition=condition
            )
        elif intent_type == "play_referential":
            referential = random.choice(["前面那个", "这个", "前面第一个"])
            prompt = prompt.format(
                dialogue_history=history_str,
                items_list=items_str,
                referential=referential
            )
        elif intent_type == "play_complex":
            complex_condition = self._generate_context_condition(items)
            prompt = prompt.format(
                dialogue_history=history_str,
                items_list=items_str,
                complex_condition=complex_condition
            )
        else:
            prompt = prompt.format(
                dialogue_history=history_str,
                items_list=items_str
            )

        try:
            response = await self.llm_client.call_llm(
                sys_query="你是专业的语音助手，擅长理解播放意图并生成简洁的播放回复。",
                user_query=prompt,
                max_tokens=500,
                temperature=0.5
            )

            if not response:
                logger.warning(f"[{SOURCE_FILE}:285] LLM响应为空")
                return {
                    "q": "播放",
                    "a": "",
                    "round_type": "playback",
                    "playback_intent_type": intent_type
                }

            dialogue = self._parse_dialogue(response)
            dialogue["round_type"] = "playback"
            dialogue["playback_intent_type"] = intent_type

            return dialogue

        except Exception as e:
            logger.error(f"[{SOURCE_FILE}:303] 生成播放轮失败: {str(e)}\n{traceback.format_exc()}")
            return {
                "q": "",
                "a": "",
                "round_type": "playback",
                "playback_intent_type": intent_type
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
