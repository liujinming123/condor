"""
改进的多轮对话生成脚本 - 带详细日志和错误处理
"""

import asyncio
import sys
import os
import yaml
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    print("=" * 60)
    print("[TARGET] Enhanced Dialogue Generator")
    print("=" * 60)
    print()
    print(f"Starting time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Step 1: 加载配置
        print("1. Loading configuration...")
        with open("config/llm_config.yaml", 'r', encoding='utf-8') as f:
            llm_config = yaml.safe_load(f)
        with open("config/multiround_scenarios.yaml", 'r', encoding='utf-8') as f:
            scenarios_config = yaml.safe_load(f)
        with open("config/generation_config.yaml", 'r', encoding='utf-8') as f:
            gen_config = yaml.safe_load(f)

        target_count = gen_config["generation"]["target_count"]
        print(f"   Target: {target_count} dialogues")
        print("   [OK] Configuration loaded")

        # Step 2: 验证知识库
        print("2. Checking knowledge base...")
        kb_path = Path("config/media_knowledge.json")

        if not kb_path.exists():
            print("   [ERROR] Knowledge base file not found!")
            print("   Please run: python scripts/load_media_data.py")
            return

        with open(kb_path, 'r', encoding='utf-8') as f:
            kb_data = json.load(f)
            music_count = len(kb_data.get("music", []))
            video_count = len(kb_data.get("video", []))
            poem_count = len(kb_data.get("poem", []))

        if music_count == 0 and video_count == 0 and poem_count == 0:
            print("   [ERROR] Knowledge base is empty!")
            return

        print(f"   [OK] Knowledge base: Music={music_count}, Video={video_count}, Poem={poem_count}")

        # Step 3: 导入模块
        print("3. Importing modules...")
        try:
            from src.llm.async_client import AsyncLLMClient
            from src.knowledge.knowledge_manager import MediaKnowledgeManager
            from src.generators.multiround_dialogue_generator import MultiRoundDialogueGenerator
            from src.validators.multiround_validator import MultiRoundValidator
            from src.utils.formatter import export_to_jsonl, export_statistics
            from src.utils.quality_checker import QualityChecker

            print("   [OK] All modules imported")

        except ImportError as e:
            print(f"   [ERROR] Import failed: {e}")
            return

        # Step 4: 初始化组件
        print("4. Initializing components...")
        try:
            llm_client = AsyncLLMClient(
                base_url=llm_config["llm_api"]["base_url"],
                api_key=llm_config["llm_api"]["api_key"],
                model=llm_config["llm_api"]["model"],
                max_concurrent=2,
                request_interval=1.0,
                # timeout=60.0
            )

            knowledge_manager = MediaKnowledgeManager("config/media_knowledge.json")
            knowledge_manager.load_from_file()

            generator = MultiRoundDialogueGenerator(
                llm_client=llm_client,
                knowledge_manager=knowledge_manager,
                scenarios_config=scenarios_config,
                generation_config=gen_config
            )

            print("   [OK] Components initialized")

        except Exception as e:
            print(f"   [ERROR] Initialization failed: {e}")
            return

        # Step 5: 生成对话
        print("5. Generating dialogues...")
        output_dir = Path("data/final")
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_count = 0
        total_count = target_count

        batch_size = 10
        batches = (total_count + batch_size - 1) // batch_size

        for batch_num in range(1, batches + 1):
            print(f"\n   Batch {batch_num}/{batches}")
            start_count = generated_count
            end_count = min(start_count + batch_size, total_count)

            try:
                batch_dialogues = await generator.generate_batch(end_count - start_count)
                generated_count = len(batch_dialogues)

                print(f"   Generated {len(batch_dialogues)} dialogues in this batch")

                # 保存中间结果
                if batch_dialogues:
                    batch_file = output_dir / f"batch_{batch_num}_temp.json"
                    with open(batch_file, 'w', encoding='utf-8') as f:
                        json.dump(batch_dialogues, f, ensure_ascii=False, indent=2)
                    print(f"   Saved intermediate: {batch_file}")

                generated_count = len(batch_dialogues)

                if generated_count >= total_count:
                    print(f"\n   Reached target count: {total_count}")
                    break

            except Exception as e:
                print(f"   [ERROR] Batch {batch_num} failed: {e}")
                import traceback
                traceback.print_exc()

                # 如果出错，尝试使用已保存的数据
                break

        if generated_count == 0:
            print("\n   [ERROR] No dialogues were generated!")
            return

        # Step 6: 验证数据
        print("\n6. Validating dialogues...")
        validator = MultiRoundValidator()

        valid_dialogues = []
        invalid_count = 0

        for i, dialogue in enumerate(batch_dialogues):
            report = validator.validate_dialogue(dialogue)
            dialogue["validation_report"] = report

            if report["valid"]:
                valid_dialogues.append(dialogue)
            else:
                invalid_count += 1
                if invalid_count <= 5:
                    q = dialogue.get("dialogue", [{}])[-1].get("q", "")[:100]
                    a = dialogue.get("dialogue", [{}])[-1].get("a", "")[:100]
                    print(f"   Invalid dialogue {i+1}:")
                    print(f"     Q: {q}")
                    print(f"     A: {a}")
                    print(f"     Error: {report.get('errors', [])}")
                else:
                    break

        print(f"   [OK] Validated: {len(valid_dialogues)}/{len(batch_dialogues)} valid dialogues")

        if len(valid_dialogues) == 0:
            print("\n   [ERROR] No valid dialogues!")
            return

        # Step 7: 质量检查
        print("\n7. Quality check...")
        quality_checker = QualityChecker()

        quality_report = quality_checker.check_batch_quality(valid_dialogues)
        filtered_dialogues = quality_checker.filter_by_quality(valid_dialogues, min_score=3.0)

        print(f"   Quality report:")
        print(f"     Average score: {quality_report['average_score']:.2f}")
        print(f"     Min score: {quality_report['min_score']:.2f}")
        print(f"   Max score: {quality_report['max_score']:.2f}")
        print(f"   Filtered: {len(filtered_dialogues)}/{len(valid_dialogues)}")

        # Step 8: 保存结果
        print("\n8. Saving results...")

        final_file = output_dir / "multiround_dialogues.jsonl"

        export_to_jsonl(filtered_dialogues, str(final_file))
        print(f"   [OK] Saved to {final_file}")

        stats_file = output_dir / "generation_statistics.txt"
        export_statistics(filtered_dialogues, str(stats_file))
        print(f"   [OK] Statistics saved to {stats_file}")

        # 打印最终统计
        print()
        print("=" * 60)
        print("📊 Generation Summary")
        print("=" * 60)
        print(f"Total dialogues: {len(filtered_dialogues)}")
        print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Output directory: {output_dir}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
