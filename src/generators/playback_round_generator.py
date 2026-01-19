"""
播放轮生成器
"""

import json
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

**可播放的项（JSON格式）：**
{items_json}

**播放意图：**直接播放全部推荐内容

**要求：**
1. 用户问题简洁："播放"、"放吧"、"来吧"等
2. 助手回答必须是JSON格式，不要其他文字
3. JSON格式：{"作者": [...], "作品": "...", "作品类型": "音乐/视频/诗词/播客"}
4. 作者字段为数组，如果只有一个作者也用数组格式

**示例：**
q: 播放
a: {"作者": ["邓丽君"], "作品": "甜蜜蜜", "作品类型": "音乐"}

请生成最后一轮：""",

    "play_nth": """基于前面对话，生成最后一轮播放对话。

**前面对话：**
{dialogue_history}

**可播放的项（JSON格式）：**
{items_json}

**播放意图：**播放第{nth}个

**要求：**
1. 用户问题要多样："放第二个"/"播放第三首"/"我想听第一个"/"第几首"等
2. 助手回答必须是JSON格式，不要其他文字
3. JSON格式：{"作者": [...], "作品": "...", "作品类型": "音乐/视频/诗词/播客"}

**示例：**
意图：播放第2个
q: 放第二个吧直接放
a: {"作者": ["张学友"], "作品": "吻别", "作品类型": "音乐"}

请生成最后一轮：""",

    "play_by_context": """基于前面对话，生成最后一轮播放对话。

**前面对话：**
{dialogue_history}

**可播放的项（JSON格式）：**
{items_json}

**播放意图：**基于上下文条件播放
**条件：**{condition}

**要求：**
1. 用户问题要明确表达条件
2. 助手回答必须是JSON格式，不要其他文字
3. JSON格式：{"作者": [...], "作品": "...", "作品类型": "音乐/视频/诗词/播客"}

**示例：**
q: 播放周杰伦的歌
a: {"作者": ["周杰伦"], "作品": "青花瓷", "作品类型": "音乐"}

请生成最后一轮：""",

    "play_referential": """基于前面对话，生成最后一轮播放对话。

**前面对话：**
{dialogue_history}

**可播放的项（JSON格式）：**
{items_json}

**播放意图：**模糊指代播放
**指代词：**{referential}

**要求：**
1. 用户问题简洁："放前面那个"/"播放这个"/"就它了"等
2. 助手回答必须是JSON格式，不要其他文字
3. JSON格式：{"作者": [...], "作品": "...", "作品类型": "音乐/视频/诗词/播客"}

**示例：**
q: 放前面那个
a: {"作者": ["邓丽君"], "作品": "小城故事", "作品类型": "音乐"}

请生成最后一轮：""",

    "play_complex": """基于前面对话，生成最后一轮播放对话。

**前面对话：**
{dialogue_history}

**可播放的项（JSON格式）：**
{items_json}

**播放意图：**多轮复杂播放
**复杂条件：**{complex_condition}

**要求：**
1. 用户问题明确表达复杂条件
2. 助手回答必须是JSON格式，不要其他文字
3. JSON格式：{"作者": [...], "作品": "...", "作品类型": "音乐/视频/诗词/播客"}

**示例：**
q: 播放周杰伦和蔡依林合唱的歌
a: {"作者": ["周杰伦", "蔡依林"], "作品": "布拉格广场", "作品类型": "音乐"}

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

    def _format_items_json(self, items: List[Dict]) -> str:
        """
        将items格式化为JSON字符串供LLM参考

        Args:
            items: 项列表

        Returns:
            JSON格式字符串
        """
        if not items:
            return "[]"

        simplified_items = []
        for item in items[:5]:
            simplified_items.append({
                "name": item.get("name", ""),
                "author": item.get("artist") or item.get("author", ""),
                "type": self._infer_type(item)
            })

        return json.dumps(simplified_items, ensure_ascii=False)

    def _infer_type(self, item: Dict) -> str:
        """
        根据item字段推断作品类型

        Args:
            item: 项数据

        Returns:
            作品类型：音乐/视频/诗词/播客
        """
        if item.get("artist"):
            return "音乐"
        elif item.get("author"):
            return "诗词"
        else:
            return "视频"

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
        items_json = self._format_items_json(items)

        prompt = PLAYBACK_PROMPTS[intent_type]

        if intent_type == "play_nth":
            nth = random.randint(1, len(items)) if items else 1
            prompt = prompt.format(
                dialogue_history=history_str,
                items_json=items_json,
                nth=nth
            )
        elif intent_type == "play_by_context":
            condition = self._generate_context_condition(items)
            prompt = prompt.format(
                dialogue_history=history_str,
                items_json=items_json,
                condition=condition
            )
        elif intent_type == "play_referential":
            referential = random.choice(["前面那个", "这个", "前面第一个"])
            prompt = prompt.format(
                dialogue_history=history_str,
                items_json=items_json,
                referential=referential
            )
        elif intent_type == "play_complex":
            complex_condition = self._generate_context_condition(items)
            prompt = prompt.format(
                dialogue_history=history_str,
                items_json=items_json,
                complex_condition=complex_condition
            )
        else:
            prompt = prompt.format(
                dialogue_history=history_str,
                items_json=items_json
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
        dialogue = {"q": "", "a": {}}

        if "q:" in response and "a:" in response:
            parts = response.split("a:")
            if len(parts) == 2:
                question_part = parts[0]
                answer_part = parts[1]

                q_start = question_part.find("q:")
                if q_start != -1:
                    dialogue["q"] = question_part[q_start + 2:].strip()

                try:
                    dialogue["a"] = json.loads(answer_part.strip())
                except json.JSONDecodeError:
                    logger.warning(f"[{SOURCE_FILE}:375] 解析JSON失败: {answer_part[:100]}")
                    dialogue["a"] = {"作者": [], "作品": "", "作品类型": ""}
        elif "q:" in response:
            q_start = response.find("q:")
            q_end = response.find("\n", q_start)
            if q_end == -1:
                q_end = len(response)
            dialogue["q"] = response[q_start + 2:q_end].strip()
            dialogue["a"] = {"作者": [], "作品": "", "作品类型": ""}
        else:
            dialogue["q"] = response.strip()
            dialogue["a"] = {"作者": [], "作品": "", "作品类型": ""}

        return dialogue
