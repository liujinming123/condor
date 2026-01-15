"""
数据格式化器
"""

import json
from pathlib import Path
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def export_to_jsonl(dialogues: List[Dict], output_file: str):
    """
    导出为JSONL格式

    Args:
        dialogues: 对话列表
        output_file: 输出文件路径
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for dialogue in dialogues:
            json_line = json.dumps(dialogue, ensure_ascii=False)
            f.write(json_line + '\n')

    logger.info(f"成功导出 {len(dialogues)} 条对话到 {output_file}")


def export_to_json(dialogues: List[Dict], output_file: str):
    """
    导出为JSON格式

    Args:
        dialogues: 对话列表
        output_file: 输出文件路径
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dialogues, f, ensure_ascii=False, indent=2)

    logger.info(f"成功导出 {len(dialogues)} 条对话到 {output_file}")


def export_statistics(dialogues: List[Dict], output_file: str):
    """
    导出统计报告

    Args:
        dialogues: 对话列表
        output_file: 输出文件路径
    """
    stats = generate_statistics(dialogues)

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("多轮对话数据生成统计报告\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"总对话数: {stats['total']}\n")
        f.write(f"有效对话数: {stats['valid']}\n")
        f.write(f"无效对话数: {stats['invalid']}\n")
        f.write(f"平均轮数: {stats['avg_rounds']:.2f}\n\n")

        f.write("按轮数分布：\n")
        for round_count, count in stats['round_distribution'].items():
            f.write(f"  - {round_count}轮: {count} 条 ({count/stats['total']*100:.1f}%)\n")

        f.write("\n按类别分布：\n")
        for category, count in stats['category_distribution'].items():
            f.write(f"  - {category}: {count} 条 ({count/stats['total']*100:.1f}%)\n")

        f.write("\n按难度分布：\n")
        for difficulty, count in stats['difficulty_distribution'].items():
            f.write(f"  - {difficulty}: {count} 条 ({count/stats['total']*100:.1f}%)\n")

        f.write("\n按播放意图分布：\n")
        for intent, count in stats['intent_distribution'].items():
            f.write(f"  - {intent}: {count} 条 ({count/stats['total']*100:.1f}%)\n")

        f.write("\n" + "=" * 60 + "\n")

    logger.info(f"成功导出统计报告到 {output_file}")


def generate_statistics(dialogues: List[Dict]) -> Dict:
    """
    生成统计信息

    Args:
        dialogues: 对话列表

    Returns:
        统计字典
    """
    total = len(dialogues)

    round_distribution = {}
    category_distribution = {}
    difficulty_distribution = {}
    intent_distribution = {}
    total_rounds = 0

    for dialogue in dialogues:
        metadata = dialogue.get("metadata", {})
        rounds = dialogue.get("dialogue", [])

        round_count = len(rounds)
        total_rounds += round_count

        round_distribution[round_count] = round_distribution.get(round_count, 0) + 1

        category = metadata.get("category", "未知")
        category_distribution[category] = category_distribution.get(category, 0) + 1

        difficulty = metadata.get("difficulty", "未知")
        difficulty_distribution[difficulty] = difficulty_distribution.get(difficulty, 0) + 1

        intent_type = metadata.get("playback_intent_type", "未知")
        intent_distribution[intent_type] = intent_distribution.get(intent_type, 0) + 1

    return {
        "total": total,
        "valid": total,
        "invalid": 0,
        "avg_rounds": total_rounds / total if total > 0 else 0,
        "round_distribution": round_distribution,
        "category_distribution": category_distribution,
        "difficulty_distribution": difficulty_distribution,
        "intent_distribution": intent_distribution
    }
