"""
质量检查器
"""

from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QualityChecker:
    """质量检查器"""

    def __init__(self):
        """初始化质量检查器"""
        pass

    def check_dialogue_quality(self, dialogue: Dict) -> Dict:
        """
        检查单条对话的质量

        Args:
            dialogue: 对话数据

        Returns:
            质量报告
        """
        report = {
            "score": 5.0,
            "issues": []
        }

        rounds = dialogue.get("dialogue", [])

        if not rounds:
            report["score"] = 0.0
            report["issues"].append("对话为空")
            return report

        for i, round in enumerate(rounds):
            q = round.get("q", "")
            a = round.get("a", "")

            if not q:
                report["score"] -= 2.0
                report["issues"].append(f"第{i+1}轮缺少问题")
            if not a:
                report["score"] -= 2.0
                report["issues"].append(f"第{i+1}轮缺少回答")

            if q and len(q) < 2:
                report["score"] -= 0.5
                report["issues"].append(f"第{i+1}轮问题过短")

            if a and len(a) < 10:
                report["score"] -= 0.5
                report["issues"].append(f"第{i+1}轮回答过短")

            if not ("q:" in q or not q):
                report["score"] -= 0.5
                report["issues"].append(f"第{i+1}轮问题格式不正确")

        report["score"] = max(0.0, report["score"])
        return report

    def check_batch_quality(self, dialogues: List[Dict]) -> Dict:
        """
        批量检查对话质量

        Args:
            dialogues: 对话列表

        Returns:
            批量质量报告
        """
        total = len(dialogues)
        scores = []

        for dialogue in dialogues:
            report = self.check_dialogue_quality(dialogue)
            scores.append(report["score"])

        if scores:
            average_score = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)

            return {
                "total": total,
                "average_score": average_score,
                "min_score": min_score,
                "max_score": max_score,
                "dialogue_scores": scores
            }
        else:
            return {
                "total": total,
                "average_score": 0.0,
                "min_score": 0.0,
                "max_score": 0.0,
                "dialogue_scores": []
            }

    def filter_by_quality(self, dialogues: List[Dict], min_score: float = 3.0) -> List[Dict]:
        """
        按质量分数过滤对话

        Args:
            dialogues: 对话列表
            min_score: 最低质量分数

        Returns:
            过滤后的对话列表
        """
        filtered = []
        for dialogue in dialogues:
            report = self.check_dialogue_quality(dialogue)
            if report["score"] >= min_score:
                dialogue["quality_score"] = report["score"]
                filtered.append(dialogue)
            else:
                dialogue["quality_score"] = report["score"]
                dialogue["filtered"] = False

        logger.info(f"质量过滤: {len(filtered)}/{len(dialogues)} 条通过（最低分: {min_score})")
        return filtered
