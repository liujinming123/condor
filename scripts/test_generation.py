"""
测试脚本：小规模生成对话验证流程
"""

import asyncio
import sys
import os
import yaml
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_generation():
    print("=" * 60)
    print("Test: Dialogue Generation")
    print("=" * 60)
    print()

    try:
        print("1. Loading configuration...")
        with open("config/llm_config.yaml", 'r', encoding='utf-8') as f:
            llm_config = yaml.safe_load(f)
        with open("config/generation_config.yaml", 'r', encoding='utf-8') as f:
            gen_config = yaml.safe_load(f)
        gen_config["generation"]["target_count"] = 10
        print("   [OK] Loaded config")

        print("2. Loading knowledge base...")
        from src.knowledge.knowledge_manager import MediaKnowledgeManager
        knowledge_manager = MediaKnowledgeManager("config/media_knowledge.json")
        if not knowledge_manager.load_from_file():
            print("   [WARNING] Knowledge file not found")
            return
        print(f"   [OK] Music: {len(knowledge_manager.music_db)}")
        print(f"   [OK] Video: {len(knowledge_manager.video_db)}")
        print(f"   [OK] Poem: {len(knowledge_manager.poem_db)}")

        print("3. Testing recommendation round...")
        from src.llm.async_client import AsyncLLMClient
        from src.generators.recommend_round_generator import RecommendRoundGenerator

        llm_client = AsyncLLMClient(
            base_url=llm_config["llm_api"]["base_url"],
            api_key=llm_config["llm_api"]["api_key"],
            model=llm_config["llm_api"]["model"],
            max_concurrent=gen_config["generation"]["llm"]["max_concurrent"],
            request_interval=gen_config["generation"]["llm"]["request_interval"]
        )

        recommend_generator = RecommendRoundGenerator(llm_client)

        first_round = await recommend_generator.generate(
            category="music",
            scenario="by_artist",
            difficulty="Easy",
            knowledge_manager=knowledge_manager,
            item_count=3
        )

        if first_round.get("q") and first_round.get("a"):
            print("   [OK] First round generated")
            print(f"   Q: {first_round['q'][:100]}...")
            print(f"   A: {first_round['a'][:100]}...")
        else:
            print("   [FAIL] First round failed")
            print(f"   Q: {first_round.get('q', '')}")
            print(f"   A: {first_round.get('a', '')}")

        print("4. Testing playback intent parser...")
        from src.generators.playback_intent_parser import PlaybackIntentParser

        parser = PlaybackIntentParser(llm_client)
        items = await parser.extract_items(first_round["a"])

        print(f"   [OK] Extracted {len(items)} playable items")

        print("5. Testing playback round...")
        from src.generators.playback_round_generator import PlaybackRoundGenerator

        playback_generator = PlaybackRoundGenerator(llm_client)

        playback_round = await playback_generator.generate(
            previous_rounds=[first_round],
            items=items,
            intent_type="play_nth",
            knowledge_manager=knowledge_manager
        )

        if playback_round.get("q") and playback_round.get("a"):
            print("   [OK] Playback round generated")
            print(f"   Q: {playback_round['q']}")
            print(f"   A: {playback_round['a']}")
        else:
            print("   [FAIL] Playback round failed")

        print()
        print("=" * 60)
        print("Test Results Summary")
        print("=" * 60)
        print(f"Knowledge base: {len(knowledge_manager.music_db) + len(knowledge_manager.video_db) + len(knowledge_manager.poem_db)} items")
        print("All tests completed!")

        await llm_client.close()

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_generation())
