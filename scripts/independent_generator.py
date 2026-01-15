"""
独立的多轮对话生成脚本（不依赖其他模块）
"""

import json
import random
from datetime import datetime

# 测试数据（模拟从知识库）
MUSIC_DATA = [
    {"name": "青花瓷", "artist": "周杰伦", "era": "2000年代", "genre": "流行", "description": "周杰伦的中国风歌曲"},
    {"name": "甜蜜蜜", "artist": "邓丽君", "era": "70年代", "genre": "流行", "description": "邓丽君的经典歌曲"},
    {"name": "小城故事", "artist": "邓丽君", "era": "70年代", "genre": "流行", "description": "邓丽君的温馨歌曲"}
]

VIDEO_DATA = [
    {"name": "梦华录", "type": "古装剧", "year": "2022", "genre": "剧情", "description": "三个女人的奋斗故事"},
    {"name": "甄嬛传", "type": "古装剧", "year": "2011", "genre": "宫斗", "description": "甄嬛的后宫故事"},
    {"name": "琅琊榜", "type": "古装剧", "year": "2015", "genre": "权谋", "description": "梅长苏复仇的故事"}
]

POEM_DATA = [
    {"name": "静夜思", "author": "李白", "dynasty": "唐", "type": "poetry", "description": "唐代诗人李白的作品"},
    {"name": "春江花月夜", "author": "张若虚", "dynasty": "唐", "type": "poetry", "description": "唐诗人张若虚的作品"}
]


def generate_multiround_dialogue(count=50):
    """
    生成多轮对话数据
    """
    dialogues = []

    for i in range(1, count + 1):
        category = random.choice(["music", "video", "poem"])
        intent_type = random.choice(["play_all", "play_nth", "play_by_context", "play_referential"])

        # 选择类别对应的数据
        if category == "music":
            items = MUSIC_DATA
            scenario = "推荐音乐"
        elif category == "video":
            items = VIDEO_DATA
            scenario = "推荐视频"
        else:
            items = POEM_DATA
            scenario = "推荐诗词"

        # 随机难度
        difficulty = random.choice(["Easy", "Medium", "Hard"])

        # 随机轮数（2-5轮）
        total_rounds = random.choices([2, 2, 3, 4, 5], weights=[0.7, 0.2, 0.05, 0.05])[0]

        dialogue = {
            "id": f"md_{i:05d}",
            "metadata": {
                "category": category,
                "scenario": scenario,
                "difficulty": difficulty,
                "total_rounds": total_rounds,
                "playback_intent_type": intent_type,
                "generated_at": datetime.now().isoformat()
            },
            "dialogue": []
        }

        # 第一轮：推荐轮
        recommend_item = random.choice(items)
        if category == "music":
            q = f"可以分享一首{recommend_item['era']}的歌吗"
            a = f"《{recommend_item['name']}》，{recommend_item['description']}。希望你能喜欢。"
        elif category == "video":
            q = f"可以推荐一部{recommend_item['genre']}的剧吗？"
            a = f"《{recommend_item['name']}》，{recommend_item['description']}。希望能帮到你。"
        else:
            q = f"可以推荐一首{recommend_item['dynasty']}的诗吗？"
            a = f"《{recommend_item['name']}》，{recommend_item['description']}。希望这首诗能让你喜欢。"

        dialogue["dialogue"].append({
            "round": 1,
            "type": "recommendation",
            "q": q,
            "a": a,
            "extracted_items": [recommend_item]
        })

        # 中间轮（如果需要）
        for round_num in range(2, total_rounds):
            # 询问类型
            inquiry_type = random.choice(["detail_inquiry", "more_recommendations", "preference_clarify", "comparison_ask"])

            if inquiry_type == "detail_inquiry":
                if category == "music":
                    q = f"{recommend_item['name']}是哪个年代的歌？"
                    a = f"{recommend_item['name']}是{recommend_item['era']}的歌曲。"
                elif category == "video":
                    q = f"{recommend_item['name']}是哪个朝代的？"
                    a = f"{recommend_item['name']}是{recommend_item['year']}年的{recommend_item['type']}。"
                else:
                    q = f"{recommend_item['name']}是谁写的？"
                    a = f"{recommend_item['name']}是{recommend_item.get('author', '')}的作品。"

            elif inquiry_type == "more_recommendations":
                other_items = random.sample([item for item in items if item != recommend_item], 1)
                q = "还有别的推荐吗？"
                a = f"当然可以。《{other_items[0]['name']}》，{other_items[0].get('description', '')}。《{other_items[1]['name']}》，{other_items[1].get('description', '')}。"

            elif inquiry_type == "preference_clarify":
                if category == "music":
                    q = f"我想要轻松一点的"
                    a = f"《{recommend_item['name']}比较轻松。"
                elif category == "video":
                    q = "我想要搞笑一点的"
                    a = f"《{recommend_item['name']}比较搞笑。"
                else:
                    q = f"我想要温暖一点的"
                    a = f"《{recommend_item['name']}比较温暖。"

            elif inquiry_type == "comparison_ask":
                if len(items) > 1:
                    other_item = random.choice([item for item in items if item != recommend_item])
                    q = f"哪个评分更高？"
                    a = f"《{recommend_item['name']}和{other_item['name']}都很优秀。"
                else:
                    q = f"这个怎么样？"
                    a = f"《{recommend_item['name']}很不错。"

            dialogue["dialogue"].append({
                "round": round_num,
                "type": "inquiry",
                "q": q,
                "a": a,
                "inquiry_type": inquiry_type
            })

        # 最后一轮：播放轮
        target_item = recommend_item

        if intent_type == "play_all":
            q = "播放"
            a = f"播放《{target_item['name']}》"
        elif intent_type == "play_nth":
            if len(items) > 1:
                nth = random.randint(1, len(items))
                target_item = items[nth - 1]
            q = f"放第{nth}个吧"
            a = f"播放《{target_item['name']}》"
        elif intent_type == "play_by_context":
            if category == "music":
                q = f"播放{target_item['artist']}的{target_item['genre']}歌"
                a = f"播放{target_item['artist']}的{target_item['genre']}歌"
            elif category == "video":
                q = f"播放{target_item['type']}的剧"
                a = f"播放{target_item['type']}的剧"
            else:
                q = f"播放{target_item['name']}"
                a = f"播放《{target_item['name']}》"
        elif intent_type == "play_referential":
            q = "放前面那个吧"
            a = f"播放《{target_item['name']}》"
        elif intent_type == "play_complex":
            if category == "music":
                q = f"播放{target_item['artist']}和其他歌手合唱的歌"
                if len(items) > 1:
                    other_item = random.choice([item for item in items if item != target_item])
                    a = f"播放{target_item['artist']}和{other_item.get('artist', '')}合唱的歌"
            else:
                a = f"播放{target_item['name']}和{target_item['artist']}合唱的歌"
            elif category == "video":
                q = f"播放最经典的{target_item['type']}的剧"
                a = f"播放《甄嬛传》，这是最经典的宫斗剧。"
            else:
                q = f"播放{target_item['name']}最经典的作品"
                a = f"播放《{target_item['name']}》"

        dialogue["dialogue"].append({
            "round": total_rounds,
            "type": "playback",
            "q": q,
            "a": a,
            "playback_intent_type": intent_type,
            "target_item": target_item
        })

        dialogues.append(dialogue)

    return dialogues


def save_dialogues(dialogues, output_file="data/final/multiround_dialogues.jsonl"):
    """
    保存对话数据到JSONL文件
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for dialogue in dialogues:
            json_line = json.dumps(dialogue, ensure_ascii=False)
            f.write(json_line + '\n')

    print(f"Saved {len(dialogues)} dialogues to {output_file}")


def generate_statistics(dialogues):
    """
    生成统计信息
    """
    total = len(dialogues)
    round_dist = {}
    category_dist = {}
    difficulty_dist = = intent_dist = {}

    for dialogue in dialogues:
        metadata = dialogue.get("metadata", {})
        total_rounds = metadata.get("total_rounds", 2)

        round_dist[total_rounds] = round_dist.get(total_rounds, 0) + 1
        category = metadata.get("category", "unknown")
        category_dist[category] = category_dist.get(category, 0) + 1

        difficulty = metadata.get("difficulty", "unknown")
        difficulty_dist[difficulty] = difficulty_dist.get(difficulty, 0) + 1

        intent_type = metadata.get("playback_intent_type", "unknown")
        intent_dist[intent_type] = intent_dist.get(intent_type, 0) + 1

    stats = {
        "total": total,
        "valid": total,
        "avg_rounds": total_rounds / total if total > 0 else 0,
        "round_distribution": round_dist,
        "category_distribution": category_dist,
        "difficulty_distribution": difficulty_dist,
        "intent_distribution": intent_dist
    }

    return stats


def main():
    """
    主函数
    """
    import sys
    import os

    print("=" * 60)
    print("Independent Dialogue Generator")
    print("=" * 60)
    print()

    target_count = 50

    try:
        print(f"Generating {target_count} dialogues...")
        dialogues = generate_multiround_dialogue(target_count)

        print(f"Generated {len(dialogues)} dialogues")

        output_file = "data/final/independent_dialogues.jsonl"
        save_dialogues(dialogues, output_file)

        stats = generate_statistics(dialogues)

        print()
        print("=" * 60)
        print("Generation Summary")
        print("=" * 60)
        print(f"Total dialogues: {stats['total']}")
        print(f"Average rounds: {stats['avg_rounds']:.2f}")
        print()
        print("By rounds:")
        for round_count, count in sorted(stats['round_distribution'].items()):
            print(f"  - {round_count} rounds: {count} ({count/stats['total']*100:.1f}%)")
        print()
        print("By category:")
        for category, count in sorted(stats['category_distribution'].items()):
            print(f"  - {category}: {count} ({count/stats['total']*100:.1f}%)")
        print()
        print("By intent:")
        for intent, count in sorted(stats['intent_distribution'].items()):
            print(f"  - {intent}: {count} ({count/stats['total']*100:.1f}%)")
        print()
        print("=" * 60)
        print(f"Output: {output_file}")
        print("=" * 60)

        sys.exit(0)

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()