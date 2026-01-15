"""
小规模生成测试脚本（避免控制台编码问题）
"""

import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_small_generation():
    """测试生成10条对话"""

    print("=" * 60)
    print("Testing Dialogue Generation (10 samples)")
    print("=" * 60)
    print()

    try:
        import yaml
        with open("config/llm_config.yaml", 'r', encoding='utf-8') as f:
            llm_config = yaml.safe_load(f)
        with open("config/generation_config.yaml", 'r', encoding='utf-8') as f:
            gen_config = yaml.safe_load(f)

        gen_config["generation"]["target_count"] = 10

        from src.llm.async_client import AsyncLLMClient
        from src.knowledge.knowledge_manager import MediaKnowledgeManager
        from src.generators.multiround_dialogue_generator import MultiRoundDialogueGenerator

        print("Initializing components...")

        llm_client = AsyncLLMClient(
            base_url=llm_config["llm_api"]["base_url"],
            api_key=llm_config["llm_api"]["api_key"],
            model=llm_config["llm_api"]["model"],
            max_concurrent=2,
            request_interval=1.0
        )

        knowledge_manager = MediaKnowledgeManager("config/media_knowledge.json")
        knowledge_manager.load_from_file()

        scenarios_config = {
            "scenarios": {
                "music": {
                    "categories": [
                        {
                            "name": "by_artist",
                            "difficulties": ["Easy", "Medium"],
                            "intents": ["play_all", "play_nth"]
                        }
                    ]
                }
            }
        }

        generator = MultiRoundDialogueGenerator(
            llm_client=llm_client,
            knowledge_manager=knowledge_manager,
            scenarios_config=scenarios_config,
            generation_config=gen_config
        )

        print("Starting generation of 10 dialogues...")

        dialogues = await generator.generate_batch(10)

        print(f"Generated {len(dialogues)} dialogues")

        output_path = Path("data/final/test_dialogues.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dialogues, f, ensure_ascii=False, indent=2)

        print(f"Saved to {output_path}")

        for i, dialogue in enumerate(dialogues[:5]):
            rounds = dialogue.get("dialogue", [])
            print(f"\n--- Dialogue {i+1} ---")
            for r in rounds:
                q = r.get("q", "")[:80] if r.get("q") else ""
                a = r.get("a", "")[:100] if r.get("a") else ""
                print(f"Q: {q}")
                print(f"A: {a}")

        await llm_client.close()

        print()
        print("=" * 60)
        print("Test Complete!")
        print("=" * 60)

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_small_generation())
