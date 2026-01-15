"""
多轮对话验证器
"""

import re
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiRoundValidator:
    """多轮对话验证器"""

    def __init__(self):
        """初始化验证器"""
        self.playback_keywords = [
            "播放", "放", "来", "听", "看",
            "第一个", "第二个", "第三个", "第几个",
            "那首", "那个", "这部", "这"
        ]

    def validate_dialogue(self, dialogue: Dict) -> Dict:
        """
        验证单条多轮对话的质量

        Args:
            dialogue: 对话数据

        Returns:
            验证报告
        """
        report = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        rounds = dialogue.get("dialogue", [])

        if not rounds:
            report["valid"] = False
            report["errors"].append("对话为空")
            return report

        report["rounds_count"] = len(rounds)

        for i, round in enumerate(rounds):
            if not round.get("q"):
                report["errors"].append(f"第{i+1}轮缺少问题")
            if not round.get("a"):
                report["errors"].append(f"第{i+1}轮缺少回答")

        if len(rounds) < 2:
            report["valid"] = False
            report["errors"].append(f"对话轮数不足：{len(rounds)}轮，至少需要2轮")
        elif len(rounds) > 5:
            report["warnings"].append(f"对话轮数过多：{len(rounds)}轮，建议控制在2-5轮")

        if rounds and rounds[0].get("round_type") != "recommendation":
            report["warnings"].append("第一轮不是推荐类型")

        last_round = rounds[-1]
        if last_round.get("round_type") != "playback":
            report["errors"].append("最后一轮不是播放意图")
            report["valid"] = False

        if not self._is_playback_intent(last_round.get("q", "")):
            report["warnings"].append("最后一轮用户问题可能不是明确的播放意图")

        if not self._check_context_consistency(rounds):
            report["warnings"].append("对话上下文可能不一致")

        if not self._verify_playback_accuracy(last_round, rounds[:-1]):
            report["warnings"].append("最后一轮播放意图可能不准确")

        return report

    def _is_playback_intent(self, question: str) -> bool:
        """
        检查是否是播放意图

        Args:
            question: 用户问题

        Returns:
            是否是播放意图
        """
        if not question:
            return False

        question_lower = question.lower()
        return any(kw in question_lower for kw in self.playback_keywords)

    def _check_context_consistency(self, rounds: List[Dict]) -> bool:
        """
        检查上下文一致性

        Args:
            rounds: 对话轮列表

        Returns:
            是否一致
        """
        if len(rounds) < 2:
            return True

        last_round = rounds[-1]
        previous_rounds = rounds[:-1]

        last_q = last_round.get("q", "")

        if not last_q:
            return True

        for prev_round in previous_rounds:
            prev_q = prev_round.get("q", "")
            if prev_q in last_q:
                return True

        if self._contains_referential_words(last_q):
            return True

        return True

    def _contains_referential_words(self, text: str) -> bool:
        """
        检查是否包含指代词

        Args:
            text: 输入文本

        Returns:
            是否包含指代词
        """
        referential_words = ["那个", "这个", "这", "那首", "那部", "前面"]
        text_lower = text.lower()
        return any(rw in text_lower for rw in referential_words)

    def _verify_playback_accuracy(self, last_round: Dict, previous_rounds: List[Dict]) -> bool:
        """
        验证播放意图的准确性

        Args:
            last_round: 最后一轮
            previous_rounds: 前面的轮次

        Returns:
            是否准确
        """
        last_q = last_round.get("q", "")
        last_a = last_round.get("a", "")

        if not last_q or not last_a:
            return True

        if "播放" in last_a:
            content_name = self._extract_content_name(last_a)
            if content_name and len(previous_rounds) > 0:
                return True

        return True

    def _extract_content_name(self, text: str) -> str:
        """
        从文本中提取内容名称

        Args:
            text: 输入文本

        Returns:
            内容名称
        """
        match = re.search(r'《([^》]+)', text)
        if match:
            return match.group(1)
        return ""

    def validate_batch(self, dialogues: List[Dict]) -> Dict:
        """
        批量验证对话

        Args:
            dialogues: 对话列表

        Returns:
            批量验证报告
        """
        total = len(dialogues)
        valid_count = 0
        invalid_count = 0
        error_summary = {}

        for dialogue in dialogues:
            report = self.validate_dialogue(dialogue)
            if report["valid"]:
                valid_count += 1
            else:
                invalid_count += 1

            for error in report["errors"]:
                error_summary[error] = error_summary.get(error, 0) + 1

        return {
            "total": total,
            "valid": valid_count,
            "invalid": invalid_count,
            "valid_rate": valid_count / total if total > 0 else 0,
            "error_summary": error_summary
        }
