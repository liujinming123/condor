"""
加载媒体数据脚本（简化版）
"""

import sys
import os
import csv
import json
import random
from pathlib import Path


MEDIA_RESOURCE_PATH = r"D:\Geely work\code\git_program\ailab-nlu-media\rule_engine\media_resource"
OUTPUT_FILE = "config/media_knowledge.json"


def load_music_sample(count=100):
    """加载音乐样本"""
    csv_file = f"{MEDIA_RESOURCE_PATH}/_hot_resource_of_music_comment_v7.csv"
    samples = []

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= count:
                    break

                song_name = row.get("song", "")
                singer_name = row.get("singer", "")

                if song_name and singer_name:
                    samples.append({
                        "name": song_name,
                        "artist": singer_name,
                        "album": row.get("album", ""),
                        "genre": row.get("genre", "pop"),
                        "era": "modern",
                        "description": f"{singer_name}'s song"
                    })
    except Exception as e:
        print(f"Error loading music: {e}")

    return samples


def load_tv_sample(count=50):
    """加载视频样本"""
    csv_file = f"{MEDIA_RESOURCE_PATH}/_hot_resource_of_television_show_v6.csv"
    samples = []

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= count:
                    break

                title = row.get("title", "")
                if title:
                    year = row.get("publishTime", "")[:4] if row.get("publishTime", "") else "2023"

                    samples.append({
                        "name": title,
                        "type": row.get("genre", ""),
                        "year": year,
                        "genre": row.get("genre", ""),
                        "area": row.get("area", ""),
                        "description": f"{row.get('genre', '')} show"
                    })
    except Exception as e:
        print(f"Error loading TV: {e}")

    return samples


def load_poem_sample(count=30):
    """加载诗词样本"""
    csv_file = f"{MEDIA_RESOURCE_PATH}/_hot_resource_of_poem_v3.csv"
    samples = []

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= count:
                    break

                poem_name = row.get("poem", "")
                poet_name = row.get("poet", "")
                dynasty = row.get("dynasty", "")

                if poem_name:
                    samples.append({
                        "name": poem_name,
                        "author": poet_name,
                        "dynasty": dynasty,
                        "type": "poetry",
                        "description": f"{dynasty} poem by {poet_name}"
                    })
    except Exception as e:
        print(f"Error loading poem: {e}")

    return samples


def main():
    print("=" * 60)
    print("Media Data Loader")
    print("=" * 60)
    print()

    print("1. Loading music data...")
    music_samples = load_music_sample(count=100)
    print(f"   [OK] Music: {len(music_samples)} items")

    print()
    print("2. Loading video data...")
    tv_samples = load_tv_sample(count=50)
    print(f"   [OK] Video: {len(tv_samples)} items")

    print()
    print("3. Loading poem data...")
    poem_samples = load_poem_sample(count=30)
    print(f"   [OK] Poem: {len(poem_samples)} items")

    print()
    print("4. Saving knowledge base...")

    knowledge = {
        "music": music_samples,
        "video": tv_samples,
        "poem": poem_samples,
        "statistics": {
            "music_count": len(music_samples),
            "video_count": len(tv_samples),
            "poem_count": len(poem_samples),
            "total_count": len(music_samples) + len(tv_samples) + len(poem_samples)
        }
    }

    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)

    print(f"   [OK] Knowledge base saved to {OUTPUT_FILE}")
    print()
    print("=" * 60)
    print("Loading Complete!")
    print(f"Total: {knowledge['statistics']['total_count']} items")
    print("=" * 60)


if __name__ == "__main__":
    main()
