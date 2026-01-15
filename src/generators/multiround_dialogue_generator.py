"""
多轮对话生成器（核心协调器）
"""

import asyncio
import json
import random
import traceback
from datetime import datetime
from typing import Dict, List
import logging

from ..llm.async_client import AsyncLLMClient
from ..knowledge.knowledge_manager import MediaKnowledgeManager
from .recommend_round_generator import RecommendRoundGenerator
from .inquiry_round_generator import InquiryRoundGenerator
from .playback_intent_parser import PlaybackIntentParser
from .playback_round_generator import PlaybackRoundGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOURCE_FILE = __file__


ROUND_DISTRIBUTION = {
    2: 0.70,
    3: 0.20,
    4: 0.08,
    5: 0.02
}


class MultiRoundDialogueGenerator:
    """多轮对话生成器（核心协调器）"""

    def __init__(
        self,
        llm_client: AsyncLLMClient,
        knowledge_manager: MediaKnowledgeManager,
        scenarios_config: Dict,
        generation_config: Dict
    ):
        """
        初始化多轮对话生成器

        Args:
            llm_client: LLM客户端
            knowledge_manager: 知识库管理器
            scenarios_config: 场景配置
            generation_config: 生成配置
        """
        self.llm_client = llm_client
        self.knowledge_manager = knowledge_manager
        self.scenarios_config = scenarios_config
        self.generation_config = generation_config

        self.recommend_generator = RecommendRoundGenerator(llm_client)
        self.inquiry_generator = InquiryRoundGenerator(llm_client)
        self.playback_parser = PlaybackIntentParser(llm_client)
        self.playback_generator = PlaybackRoundGenerator(llm_client)

        self.dialogue_count = 0

    def _sample_round_count(self) -> int:
        """
        随机采样对话轮数（2-5轮）

        Returns:
            轮数
        """
        return random.choices(
            list(ROUND_DISTRIBUTION.keys()),
            weights=list(ROUND_DISTRIBUTION.values())
        )[0]

    def _map_category_to_knowledge(self, category: str) -> str:
        """
        将类别映射到知识库类别

        Args:
            category: 场景类别

        Returns:
            知识库类别
        """
        if "音乐" in category:
            return "music"
        elif "视频" in category:
            return "video"
        elif "诗词" in category or "播客" in category:
            return "poem"
        else:
            return "music"

    def _generate_id(self) -> str:
        """
        生成对话ID

        Returns:
            对话ID
        """
        self.dialogue_count += 1
        return f"md_{self.dialogue_count:06d}"

    def _random_combination(self):
        """
        随机选择类别、场景、难度、意图组合

        Returns:
            组合字典
        """
        category = random.choice(list(self.scenarios_config.get("scenarios", {}).keys()))

        category_config = self.scenarios_config["scenarios"][category]
        scenario_info = random.choice(category_config.get("categories", []))

        difficulties = scenario_info.get("difficulties", ["Easy"])
        difficulty = random.choice(difficulties)

        intents = scenario_info.get("intents", ["play_all"])
        intent_type = random.choice(intents)

        return {
            "category": category,
            "scenario": scenario_info.get("name", ""),
            "difficulty": difficulty,
            "intent_type": intent_type
        }

    async def generate_dialogue(
        self,
        category: str,
        scenario: str,
        difficulty: str,
        intent_type: str
    ) -> Dict:
        """
        生成一条完整的多轮对话（2-5轮）

        Args:
            category: 类别
            scenario: 场景
            difficulty: 难度
            intent_type: 播放意图类型

        Returns:
            对话数据
        """
        logger.info(f"生成对话: {category} - {scenario} - {difficulty} - {intent_type}")

        total_rounds = self._sample_round_count()
        logger.info(f"  总轮数: {total_rounds}")

        knowledge_category = self._map_category_to_knowledge(category)

        try:
            logger.info(f"  生成第一轮（推荐）...")
            first_round = await self.recommend_generator.generate(
                category=category,
                scenario=scenario,
                difficulty=difficulty,
                knowledge_manager=self.knowledge_manager,
                item_count=self.generation_config["generation"]["sampling"]["items_per_recommendation"]
            )

            if not first_round.get("q"):
                logger.warning(f"  第一轮生成失败，返回空对话")
                return self._create_empty_dialogue(category, scenario, difficulty, intent_type)

            items = await self.playback_parser.extract_items(
                first_round["a"]
            )

            dialogue_rounds = [first_round]

            if total_rounds > 2:
                logger.info(f"  生成中间轮（{total_rounds - 2}轮）...")
                for round_num in range(2, total_rounds):
                    inquiry_type = self.inquiry_generator.sample_inquiry_type()

                    inquiry_round, updated_items = await self.inquiry_generator.generate(
                        previous_rounds=dialogue_rounds,
                        items=items,
                        inquiry_type=inquiry_type,
                        current_round=round_num,
                        total_rounds=total_rounds,
                        knowledge_manager=self.knowledge_manager
                    )

                    dialogue_rounds.append(inquiry_round)
                    items = updated_items

                    await asyncio.sleep(0.3)

            logger.info(f"  生成最后一轮（播放）...")
            final_round = await self.playback_generator.generate(
                previous_rounds=dialogue_rounds,
                items=items,
                intent_type=intent_type,
                knowledge_manager=self.knowledge_manager
            )

            dialogue_rounds.append(final_round)

            return {
                "id": self._generate_id(),
                "metadata": {
                    "category": category,
                    "scenario": scenario,
                    "difficulty": difficulty,
                    "total_rounds": total_rounds,
                    "playback_intent_type": intent_type,
                    "generated_at": datetime.now().isoformat()
                },
                "dialogue": dialogue_rounds
            }

        except Exception as e:
            logger.error(f"[{SOURCE_FILE}:219] 生成对话失败: {str(e)}\n{traceback.format_exc()}")
            return self._create_empty_dialogue(category, scenario, difficulty, intent_type)

    def _create_empty_dialogue(
        self,
        category: str,
        scenario: str,
        difficulty: str,
        intent_type: str
    ) -> Dict:
        """
        创建空对话（用于失败时）

        Returns:
            空对话数据
        """
        return {
            "id": self._generate_id(),
            "metadata": {
                "category": category,
                "scenario": scenario,
                "difficulty": difficulty,
                "total_rounds": 2,
                "playback_intent_type": intent_type,
                "generated_at": datetime.now().isoformat(),
                "error": "generation_failed"
            },
            "dialogue": []
        }

    async def generate_batch(self, target_count: int):
        """
        批量生成对话，确保覆盖所有类别和意图类型

        Args:
            target_count: 目标数量

        Returns:
            对话列表
        """
        logger.info(f"开始批量生成，目标数量: {target_count}")
        all_dialogues = []

        scenarios = self.scenarios_config.get("scenarios", {})

        combinations = []

        for category, category_config in scenarios.items():
            for scenario_info in category_config.get("categories", []):
                for difficulty in scenario_info.get("difficulties", []):
                    for intent_type in scenario_info.get("intents", []):
                        combinations.append({
                            "category": category,
                            "scenario": scenario_info.get("name", ""),
                            "difficulty": difficulty,
                            "intent_type": intent_type
                        })

        max_per_combination = self.generation_config["generation"]["sampling"]["max_dialogues_per_combination"]

        for i, combination in enumerate(combinations):
            if i < max_per_combination:
                try:
                    dialogue = await self.generate_dialogue(
                        category=combination["category"],
                        scenario=combination["scenario"],
                        difficulty=combination["difficulty"],
                        intent_type=combination["intent_type"]
                    )
                    all_dialogues.append(dialogue)
                except Exception as e:
                    logger.error(f"[{SOURCE_FILE}:290] 生成对话失败: {str(e)}\n{traceback.format_exc()}")
                    continue

            if len(all_dialogues) >= target_count:
                logger.info(f"已达到目标数量: {len(all_dialogues)}")
                break

            await asyncio.sleep(0.5)

        while len(all_dialogues) < target_count:
            combination = self._random_combination()
            try:
                dialogue = await self.generate_dialogue(
                    category=combination["category"],
                    scenario=combination["scenario"],
                    difficulty=combination["difficulty"],
                    intent_type=combination["intent_type"]
                )
                all_dialogues.append(dialogue)
            except Exception as e:
                logger.error(f"[{SOURCE_FILE}:310] 生成对话失败: {str(e)}\n{traceback.format_exc()}")
                continue

            if len(all_dialogues) >= target_count:
                break

        logger.info(f"批量生成完成，共生成 {len(all_dialogues)} 条对话")
        return all_dialogues
