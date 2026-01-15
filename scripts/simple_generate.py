"""
简化的多轮对话生成脚本（避免中文编码问题）
"""

import asyncio
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def generate_dialogues():
    print("=" * 60)
    print("Simple Dialogue Generator")
    print("=" * 60)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 简化的测试数据（模拟50条）
        test_data = []

        categories = ["music", "video", "poem"]

        for i in range(50):
            category = categories[i % 3]
            
            if category == "music":
                items = [
                    {"name": "青花瓷", "artist": "周杰伦", "era": "2000年代", "genre": "流行", "description": "周杰伦的中国风歌曲"},
                    {"name": "甜蜜蜜", "artist": "邓丽君", "era": "70年代", "genre": "流行", "description": "邓丽君的经典歌曲"},
                    {"name": "小城故事", "artist": "邓丽君", "era": "70年代", "genre": "流行", "description": "邓丽君的温馨歌曲"}
                ]
                scenario = "推荐音乐"
            elif category == "video":
                items = [
                    {"name": "梦华录", "type": "古装剧", "year": "2022", "genre": "剧情", "description": "三个女人的奋斗故事"},
                    {"name": "甄嬛传", "type": "古装剧", "year": "2011", "genre": "宫斗", "description": "甄嬛的后宫故事"}
                ]
                scenario = "推荐视频"
            else:
                items = [
                    {"name": "静夜思", "author": "李白", "dynasty": "唐", "type": "poetry", "description": "唐代诗人李白的作品"},
                    {"name": "春江花月夜", "author": "张若虚", "dynasty": "唐", "type": "poetry", "description": "唐代诗人张若虚的作品"}
                ]
                scenario = "推荐诗词"

            intents = ["play_all", "play_nth", "play_by_context"]

            for j, intent_type in enumerate(intents):
                if j >= 3:
                    break

                # 第一轮：推荐
                dialogue = {
                    "id": f"md_{i+1:05d}",
                    "metadata": {
                        "category": category,
                        "scenario": scenario,
                        "total_rounds": 2,
                        "playback_intent_type": intent_type,
                        "generated_at": datetime.now().isoformat()
                    },
                    "dialogue": []
                }

                # 第一轮：推荐
                item_list_str = ", ".join([f"{item['name']}({item.get('type', '')})" for item in items[:3]])
                if category == "music":
                    q = f"可以推荐几首好听的{scenario}吗？"
                elif category == "video":
                    q = f"可以推荐一部好看的{scenario}吗？"
                else:
                    q = f"可以推荐一首{scenario}吗？"

                a = f"{item_list_str}。这些都是很棒的作品，希望你能喜欢！"

                dialogue["dialogue"].append({
                    "round": 1,
                    "type": "recommendation",
                    "q": q,
                    "a": a,
                    "extracted_items": items[:3]
                })

                # 第二轮：播放
                if intent_type == "play_all":
                    q = "播放"
                    target = items[0]
                    a = f"播放《{target['name']}》"
                elif intent_type == "play_nth":
                    nth = random.randint(1, len(items))
                    target = items[nth-1]
                    q = f"放第{nth}个吧"
                    a = f"播放《{target['name']}》"
                elif intent_type == "play_by_context":
                    target = items[0]
                    q = f"播放{target['name']}的{items[0].get('type', '')}"
                    a = f"播放《{target['name']}》"
                else:
                    q = "播放" 
                    target = items[0]
                    a = f"播放《{target['name']}》"

                dialogue["dialogue"].append({
                    "round": 2,
                    "type": "playback",
                    "q": q,
                    "a": a,
                    "playback_intent_type": intent_type
                })

                test_data.append(dialogue)

                # 每10条保存一次
                if (i+1) % 10 == 0:
                    print(f"Generated {len(test_data)} dialogues so far...")

        # 保存数据
        output_dir = Path("data/final")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "simple_dialogues.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

        print()
        print("=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"Total dialogues: {len(test_data)}")
        print(f"Output file: {output_file}")
        print()
        print("=" * 60)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        return test_data

    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    dialogues = asyncio.run(generate_dialogues())
    print(f"Successfully generated {len(dialogues)} dialogues")