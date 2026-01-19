"""
播放轮生成器
"""

import json
import asyncio
import random
import re
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
3. JSON格式：{{"作者": [...], "作品": "...", "作品类型": "音乐/视频/诗词/播客"}}
4. 作者字段为数组，如果只有一个作者也用数组格式
5. **重要：作者和作品必须来自之前对话中推荐的内容**

**示例：**
q: 播放
a: {{"作者": ["邓丽君"], "作品": "甜蜜蜜", "作品类型": "音乐"}}

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
3. JSON格式：{{"作者": [...], "作品": "...", "作品类型": "音乐/视频/诗词/播客"}}
4. 作者字段为数组，如果只有一个作者也用数组格式
5. **重要：作者和作品必须来自之前对话中推荐的内容**

**示例：**
q: 放第二个吧直接放
a: {{"作者": ["张学友"], "作品": "吻别", "作品类型": "音乐"}}

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
3. JSON格式：{{"作者": [...], "作品": "...", "作品类型": "音乐/视频/诗词/播客"}}
4. 作者字段为数组，如果只有一个作者也用数组格式
5. **重要：作者和作品必须来自之前对话中推荐的内容，且符合指定条件**

**示例：**
q: 播放周杰伦的歌
a: {{"作者": ["周杰伦"], "作品": "青花瓷", "作品类型": "音乐"}}

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
3. JSON格式：{{"作者": [...], "作品": "...", "作品类型": "音乐/视频/诗词/播客"}}
4. 作者字段为数组，如果只有一个作者也用数组格式
5. **重要：作者和作品必须来自之前对话中推荐的内容**

**示例：**
q: 放前面那个
a: {{"作者": ["邓丽君"], "作品": "小城故事", "作品类型": "音乐"}}

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
3. JSON格式：{{"作者": [...], "作品": "...", "作品类型": "音乐/视频/诗词/播客"}}
4. 作者字段为数组，如果只有一个作者也用数组格式
5. **重要：作者和作品必须来自之前对话中推荐的内容，且符合复杂条件**

**示例：**
q: 播放周杰伦和蔡依林合唱的歌
a: {{"作者": ["周杰伦", "蔡依林"], "作品": "布拉格广场", "作品类型": "音乐"}}

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
                if isinstance(a, dict):
                    lines.append(f"A: {json.dumps(a, ensure_ascii=False)}")
                else:
                    lines.append(f"A: {a}")
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
            name = item.get("name", "")
            author = item.get("artist") or item.get("author", "")
            item_type = self._infer_type(item)

            simplified_items.append({
                "name": name,
                "author": author,
                "type": item_type
            })

        return json.dumps(simplified_items, ensure_ascii=False)

    def _infer_type(self, item: Dict) -> str:
        """
        根据item字段推断作品类型

        Args:
            item: 项数据

        Returns:
            作品类型
        """
        if item.get("artist"):
            return "音乐"
        elif item.get("author"):
            return "诗词"
        else:
            return "视频"

    def _normalize_text(self, text: str) -> str:
        """
        标准化文本用于模糊匹配

        Args:
            text: 输入文本

        Returns:
            标准化后的文本
        """
        return re.sub(r'[《》""''""'']', '', text.lower())

    def _fuzzy_match(self, target: str, source: str) -> bool:
        """
        模糊匹配：检查target是否在source中

        Args:
            target: 目标文本
            source: 源文本

        Returns:
            是否匹配
        """
        target_norm = self._normalize_text(target)
        source_norm = self._normalize_text(source)

        if target_norm in source_norm:
            return True

        target_chars = set(target_norm)
        source_chars = set(source_norm)

        if len(target_chars) > 0 and len(target_chars - source_chars) == 0:
            if len(target_norm) >= 2:
                return True

        return False

    def _validate_playback_content(
        self,
        playback_a: Dict,
        previous_rounds: List[Dict]
    ) -> tuple:
        """
        验证播放内容是否在之前的对话中出现过

        Args:
            playback_a: 播放轮的JSON回答
            previous_rounds: 之前的对话轮次

        Returns:
            (是否通过, 缺失的作者列表, 缺失的作品列表)
        """
        authors = playback_a.get("作者", [])
        work = playback_a.get("作品", "")

        previous_text = ""
        for round in previous_rounds:
            q = round.get("q", "")
            a = round.get("a", "")
            if isinstance(a, dict):
                previous_text += q + " " + json.dumps(a, ensure_ascii=False) + " "
            else:
                previous_text += q + " " + a + " "

        missing_authors = []
        for author in authors:
            found = False
            for round in previous_rounds:
                a = round.get("a", "")
                if isinstance(a, dict):
                    a_text = json.dumps(a, ensure_ascii=False)
                else:
                    a_text = a
                if self._fuzzy_match(author, a_text):
                    found = True
                    break
            if not found:
                missing_authors.append(author)

        missing_work = ""
        if work:
            found = False
            for round in previous_rounds:
                a = round.get("a", "")
                if isinstance(a, dict):
                    a_text = json.dumps(a, ensure_ascii=False)
                else:
                    a_text = a
                if self._fuzzy_match(work, a_text):
                    found = True
                    break
            if not found:
                missing_work = work

        is_valid = len(missing_authors) == 0 and missing_work == ""
        return is_valid, missing_authors, missing_work

    def _generate_retry_prompt(
        self,
        original_prompt: str,
        missing_authors: List[str],
        missing_work: str,
        previous_rounds: List[Dict]
    ) -> str:
        """
        生成重试提示，包含详细的错误信息

        Args:
            original_prompt: 原始提示
            missing_authors: 缺失的作者列表
            missing_work: 缺失的作品
            previous_rounds: 之前的对话轮次

        Returns:
            重试提示
        """
        history_str = self._format_dialogue_history(previous_rounds)

        retry_warning = []
        if missing_authors:
            retry_warning.append(f"以下作者未在之前对话中出现: {', '.join(missing_authors)}")
        if missing_work:
            retry_warning.append(f"以下作品未在之前对话中出现: {missing_work}")

        warning_text = "\n".join(retry_warning)

        retry_prompt = f"""{original_prompt}

**重要警告（请仔细阅读）：**
{warning_text}

**之前对话内容：**
{history_str}

**请重新生成，确保：**
1. 作者和作品必须完全来自之前对话中推荐的内容
2. 不要编造或 hallucination
3. 如果之前推荐的内容不符合条件，请选择其他符合条件的内容

请重新生成："""

        return retry_prompt

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
                    dialogue["a"] = {"作者": [], "作品": "", "作品类型": ""}

        return dialogue

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

        extra_params = {}
        if intent_type == "play_nth":
            nth = random.randint(1, len(items)) if items else 1
            extra_params["nth"] = nth
        elif intent_type == "play_by_context":
            extra_params["condition"] = self._generate_context_condition(items)
        elif intent_type == "play_referential":
            extra_params["referential"] = random.choice(["前面那个", "这个", "前面第一个"])
        elif intent_type == "play_complex":
            extra_params["complex_condition"] = self._generate_context_condition(items)

        prompt = prompt.format(
            dialogue_history=history_str,
            items_json=items_json,
            **extra_params
        )

        max_retries = 3
        last_response = None

        for attempt in range(max_retries):
            try:
                response = await self.llm_client.call_llm(
                    sys_query="你是专业的语音助手，擅长理解播放意图并生成符合要求JSON格式的播放回复。",
                    user_query=prompt,
                    max_tokens=500,
                    temperature=0.5
                )

                if not response:
                    if attempt < max_retries - 1:
                        logger.warning(f"[{SOURCE_FILE}:319] LLM响应为空，尝试重试 ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(1)
                        prompt = self._generate_retry_prompt(
                            PLAYBACK_PROMPTS[intent_type].format(
                                dialogue_history=history_str,
                                items_json=items_json,
                                **extra_params
                            ),
                            ["LLM无响应"],
                            "",
                            previous_rounds
                        )
                        continue
                    logger.warning(f"[{SOURCE_FILE}:328] LLM响应为空，使用默认值")
                    return {
                        "q": "播放",
                        "a": {"作者": [], "作品": "", "作品类型": ""},
                        "round_type": "playback",
                        "playback_intent_type": intent_type
                    }

                dialogue = self._parse_dialogue(response)

                if dialogue["a"] and isinstance(dialogue["a"], dict):
                    is_valid, missing_authors, missing_work = self._validate_playback_content(
                        dialogue["a"], previous_rounds
                    )

                    if not is_valid:
                        if attempt < max_retries - 1:
                            logger.warning(f"[{SOURCE_FILE}:347] 播放内容未验证通过，尝试重试 ({attempt + 1}/{max_retries})")
                            logger.warning(f"  缺失作者: {missing_authors}, 缺失作品: {missing_work}")
                            await asyncio.sleep(1)
                            prompt = self._generate_retry_prompt(
                                PLAYBACK_PROMPTS[intent_type].format(
                                    dialogue_history=history_str,
                                    items_json=items_json,
                                    **extra_params
                                ),
                                missing_authors,
                                missing_work,
                                previous_rounds
                            )
                            continue
                        logger.warning(f"[{SOURCE_FILE}:361] 验证失败，使用默认值")
                    else:
                        dialogue["round_type"] = "playback"
                        dialogue["playback_intent_type"] = intent_type
                        return dialogue
                else:
                    if attempt < max_retries - 1:
                        logger.warning(f"[{SOURCE_FILE}:369] JSON解析失败，尝试重试 ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(1)
                        prompt = self._generate_retry_prompt(
                            PLAYBACK_PROMPTS[intent_type].format(
                                dialogue_history=history_str,
                                items_json=items_json,
                                **extra_params
                            ),
                            ["JSON格式错误"],
                            "",
                            previous_rounds
                        )
                        continue
                    logger.warning(f"[{SOURCE_FILE}:379] JSON解析失败，使用默认值")

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"[{SOURCE_FILE}:384] 生成播放轮失败，尝试重试 ({attempt + 1}/{max_retries}): {str(e)}")
                    await asyncio.sleep(1)
                    continue
                logger.error(f"[{SOURCE_FILE}:387] 生成播放轮失败: {str(e)}\n{traceback.format_exc()}")
                return {
                    "q": "播放",
                    "a": {"作者": [], "作品": "", "作品类型": ""},
                    "round_type": "playback",
                    "playback_intent_type": intent_type
                }

        return {
            "q": "播放",
            "a": {"作者": [], "作品": "", "作品类型": ""},
            "round_type": "playback",
            "playback_intent_type": intent_type
        }

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
