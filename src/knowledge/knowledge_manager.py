"""
知识库管理器
"""

import json
import random
from typing import List, Dict, Optional
import logging

from .media_loader import MediaCSVLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MediaKnowledgeManager:
    """媒体知识库管理器"""

    def __init__(self, knowledge_file: str = "config/media_knowledge.json"):
        """
        初始化知识库

        Args:
            knowledge_file: 知识库文件路径
        """
        self.knowledge_file = knowledge_file
        self.music_db: List[Dict] = []
        self.video_db: List[Dict] = []
        self.poem_db: List[Dict] = []

    def load_from_file(self) -> bool:
        """
        从文件加载知识库

        Returns:
            是否加载成功
        """
        try:
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                knowledge = json.load(f)

            self.music_db = knowledge.get("music", [])
            self.video_db = knowledge.get("video", [])
            self.poem_db = knowledge.get("poem", [])

            logger.info(f"从文件加载知识库: 音乐{len(self.music_db)}, 视频{len(self.video_db)}, 诗词{len(self.poem_db)}")
            return True

        except FileNotFoundError:
            logger.warning(f"知识库文件 {self.knowledge_file} 不存在")
            return False
        except Exception as e:
            logger.error(f"加载知识库失败: {str(e)}")
            return False

    def load_from_csv(self, media_resource_path: str):
        """
        从CSV加载媒体数据

        Args:
            media_resource_path: 媒体资源目录路径
        """
        loader = MediaCSVLoader(media_resource_path)

        logger.info("加载音乐数据...")
        self.music_db = loader.load_music_samples(count=1000)

        logger.info("加载视频数据...")
        self.video_db = loader.load_tv_samples(count=500)

        logger.info("加载诗词数据...")
        self.poem_db = loader.load_poem_samples(count=200)

        self.save_to_file()

    def save_to_file(self):
        """保存知识库到文件"""
        knowledge = {
            "music": self.music_db,
            "video": self.video_db,
            "poem": self.poem_db,
            "statistics": {
                "music_count": len(self.music_db),
                "video_count": len(self.video_db),
                "poem_count": len(self.poem_db),
                "total_count": len(self.music_db) + len(self.video_db) + len(self.poem_db)
            }
        }

        with open(self.knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=2)

        logger.info(f"知识库已保存到 {self.knowledge_file}")

    def sample_items(
        self,
        category: str,
        count: int = 5,
        filter_condition: Optional[Dict] = None
    ) -> List[Dict]:
        """
        从指定类别采样内容

        Args:
            category: 类别
            count: 采样数量
            filter_condition: 过滤条件

        Returns:
            采样结果
        """
        if category == "music":
            pool = self.music_db
        elif category == "video":
            pool = self.video_db
        elif category == "poem":
            pool = self.poem_db
        else:
            return []

        if len(pool) == 0:
            return []

        # 应用过滤条件
        if filter_condition:
            if "exclude_names" in filter_condition:
                exclude_names = set(filter_condition["exclude_names"])
                pool = [item for item in pool if item.get("name") not in exclude_names]

        count = min(count, len(pool))

        if count == 0:
            return []

        return random.sample(pool, count)

    def get_knowledge_context(self, category: str, count: int = 3) -> str:
        """
        获取知识库上下文（用于prompt）

        Args:
            category: 类别
            count: 数量

        Returns:
            格式化的上下文字符串
        """
        samples = self.sample_items(category, count)

        if not samples:
            return ""

        context_lines = []
        for item in samples:
            if category == "music":
                context_lines.append(
                    f"- 歌曲: {item['name']}, 歌手: {item['artist']}, "
                    f"年代: {item.get('era', '')}, 描述: {item.get('description', '')}"
                )
            elif category == "video":
                context_lines.append(
                    f"- {item.get('name', '')} ({item.get('type', '')}): "
                    f"年份: {item.get('year', '')}, 描述: {item.get('description', '')}"
                )
            elif category == "poem":
                context_lines.append(
                    f"- {item.get('name', '')} ({item.get('type', '')}): "
                    f"朝代: {item.get('dynasty', '')}, 作者: {item.get('author', '')}, "
                    f"描述: {item.get('description', '')}"
                )

        return "\n".join(context_lines)
