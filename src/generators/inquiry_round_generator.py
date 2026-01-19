"""
询问轮生成器
"""

import asyncio
import random
import traceback
from typing import Dict, List, Tuple
import logging

from ..llm.async_client import AsyncLLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOURCE_FILE = __file__


INQUIRY_PROMPTS = {
    "detail_inquiry": """生成语音助手对话的中间询问轮（询问细节）。

**对话历史：**
{dialogue_history}

**当前轮数：**{current_round}/{total_rounds}

**可播放的项：**
{items_list}

**要求：**
1. 用户问题要自然，询问具体细节
2. 助手回答要简明扼要
3. 回答可以补充新的推荐内容
4. 严格格式：q: [问题] answer: [回答]

**示例：**
前面推荐了5首歌
q: 第一首是谁唱的？
a: 《当我遇上你》是邓丽君的经典作品。

请生成中间询问轮：""",

    "more_recommendations": """生成语音助手对话的中间询问轮（更多推荐）。

**对话历史：**
{dialogue_history}

**当前轮数：**{current_round}/{total_rounds}

**要求：**
1. 用户问题："还有别的推荐吗？"或类似表达
2. 助手回答要推荐3-5个新的内容
3. 新推荐要不同于前面的推荐
4. 严格格式：q: [问题] answer: [回答]

**示例：**
q: 还有别的推荐吗？
a: 当然可以。《千里之外》，《青花瓷》，《稻香》，这些也都是很受欢迎的歌曲。

请生成中间询问轮：""",

    "filter_request": """生成语音助手对话的中间询问轮（筛选请求）。

**对话历史：**
{dialogue_history}

**当前轮数：**{current_round}/{total_rounds}

**可播放的项：**
{items_list}

**要求：**
1. 用户问题表达筛选条件（如"只要古装剧"、"只要80年代的"）
2. 助手回答要从前面的推荐中筛选
3. 如果没有匹配的，说明原因并提供新推荐
4. 严格格式：q: [问题] answer: [回答]

**示例：**
前面推荐了各种类型的歌
q: 只要80年代的
a: 好的，80年代的有《小城故事》、《甜蜜蜜》、《千千阙歌》...

请生成中间询问轮：""",

    "preference_clarify": """生成语音助手对话的中间询问轮（偏好明确）。

**对话历史：**
{dialogue_history}

**当前轮数：**{current_round}/{total_rounds}

**可播放的项：**
{items_list}

**要求：**
1. 用户问题表达偏好（如"我想要轻松一点的"、"要抒情一点的"）
2. 助手回答要根据偏好筛选或推荐
3. 严格格式：q: [问题] answer: [回答]

**示例：**
q: 我想要轻松一点的
a: 好的，这些歌曲中，《稻香》和《成都》比较轻松，您可以选择其中一首。

请生成中间询问轮：""",

    "comparison_ask": """生成语音助手对话的中间询问轮（对比询问）。

**对话历史：**
{dialogue_history}

**当前轮数：**{current_round}/{total_rounds}

**可播放的项：**
{items_list}

**要求：**
1. 用户问题要对比或询问（如"哪个评分最高？"、"哪个最火？"）
2. 助手回答要明确回答
3. 可以补充一些信息
4. 严格格式：q: [问题] answer: [回答]

**示例：**
q: 哪部评分最高？
a: 《琅琊榜》评分最高，达到了9.4分，是非常优秀的作品。

请生成中间询问轮："""
}


class InquiryRoundGenerator:
    """询问轮生成器"""

    def __init__(self, llm_client: AsyncLLMClient):
        """
        初始化询问轮生成器

        Args:
            llm_client: LLM客户端
        """
        self.llm_client = llm_client
        self.inquiry_types = list(INQUIRY_PROMPTS.keys())

    def sample_inquiry_type(self) -> str:
        """
        随机采样询问类型

        Returns:
            询问类型
        """
        return random.choice(self.inquiry_types)

    def _infer_category(self, items: List[Dict]) -> str:
        """
        从项列表推断类别

        Args:
            items: 项列表

        Returns:
            类别
        """
        if not items:
            return "music"

        first_item = items[0]
        if "artist" in first_item:
            return "music"
        elif "author" in first_item:
            return "poem"
        else:
            return "video"

    def _format_dialogue_history(self, rounds: List[Dict]) -> str:
        """
        格式化对话历史

        Args:
            rounds: 对话轮列表

        Returns:
            格式化字符串
        """
        lines = []
        for round in rounds:
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
                lines.append(f"{item['index']}. {name}（歌手：{item['artist']}）")
            elif "author" in item:
                lines.append(f"{item['index']}. {name}（作者：{item['author']}）")
            else:
                lines.append(f"{item['index']}. {name}")
        return "\n".join(lines)

    def _extract_new_items_from_answer(self, answer: str, existing_items: List[Dict]) -> List[Dict]:
        """
        从回答中提取新推荐内容

        Args:
            answer: 询问轮回答文本
            existing_items: 现有items

        Returns:
            更新后的items列表
        """
        new_items = []
        lines = answer.split('\n')

        for line in lines:
            if '《' in line and '》' in line:
                start = line.find('《') + 1
                end = line.find('》')
                if start < end:
                    name = line[start:end].strip()

                    author = ""
                    if '（' in line and '）' in line:
                        author_start = line.find('（') + 1
                        author_end = line.find('）')
                        if author_start < author_end:
                            author = line[author_start:author_end]
                            author = author.replace('歌手：', '').replace('作者：', '').strip()

                    exists = any(item.get("name") == name for item in existing_items)

                    if name and not exists:
                        new_items.append({
                            "name": name,
                            "index": len(existing_items) + len(new_items) + 1,
                            "artist": author
                        })

        all_items = existing_items + new_items
        return all_items

    async def generate(
        self,
        previous_rounds: List[Dict],
        items: List[Dict],
        inquiry_type: str,
        current_round: int,
        total_rounds: int,
        knowledge_manager
    ) -> Tuple[Dict, List[Dict]]:
        """
        生成询问轮对话

        Args:
            previous_rounds: 前面的轮次
            items: 可播放的项
            inquiry_type: 询问类型
            current_round: 当前轮数
            total_rounds: 总轮数
            knowledge_manager: 知识库管理器

        Returns:
            (对话数据, 更新后的项列表)
        """
        history_str = self._format_dialogue_history(previous_rounds)
        items_str = self._format_items(items)

        prompt = INQUIRY_PROMPTS[inquiry_type].format(
            dialogue_history=history_str,
            current_round=current_round,
            total_rounds=total_rounds,
            items_list=items_str
        )

        items = items.copy()

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.llm_client.call_llm(
                    sys_query="你是专业的语音助手，擅长生成自然的对话和推荐。",
                    user_query=prompt,
                    max_tokens=1500,
                    temperature=0.7
                )

                if not response:
                    if attempt < max_retries - 1:
                        logger.warning(f"[{SOURCE_FILE}:261] LLM响应为空，尝试重试 ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(1)
                        continue
                    logger.warning(f"[{SOURCE_FILE}:264] LLM响应为空，使用默认值")
                    return {
                        "q": "好的",
                        "a": "我帮您推荐一些内容。",
                        "round_type": "inquiry",
                        "inquiry_type": inquiry_type
                    }, items

                dialogue = self._parse_dialogue(response)
                dialogue["round_type"] = "inquiry"
                dialogue["inquiry_type"] = inquiry_type

                updated_items = self._extract_new_items_from_answer(dialogue.get("a", ""), items)

                return dialogue, updated_items

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"[{SOURCE_FILE}:280] 生成询问轮失败，尝试重试 ({attempt + 1}/{max_retries}): {str(e)}")
                    await asyncio.sleep(1)
                    continue
                logger.error(f"[{SOURCE_FILE}:283] 生成询问轮失败: {str(e)}\n{traceback.format_exc()}")
                return {
                    "q": "好的",
                    "a": "我帮您推荐一些内容。",
                    "round_type": "inquiry",
                    "inquiry_type": inquiry_type
                }, items

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
