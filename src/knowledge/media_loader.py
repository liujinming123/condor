"""
媒体CSV数据加载器
"""

import csv
import json
import random
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MediaCSVLoader:
    """媒体CSV数据加载器"""

    def __init__(self, media_resource_path: str):
        """
        初始化加载器

        Args:
            media_resource_path: 媒体资源目录路径
        """
        self.media_resource_path = media_resource_path
        self.music_csv = f"{media_resource_path}/_hot_resource_of_music_comment_v7.csv"
        self.tv_csv = f"{media_resource_path}/_hot_resource_of_television_show_v6.csv"
        self.poem_csv = f"{media_resource_path}/_hot_resource_of_poem_v3.csv"

    def _infer_era(self, singer: str) -> str:
        """
        根据歌手推断年代

        Args:
            singer: 歌手名

        Returns:
            年代字符串
        """
        classic_singers = ["邓丽君", "张学友", "王菲", "刘德华", "张国荣",
                           "梅艳芳", "陈慧娴", "谭咏麟", "成龙", "周华健"]
        if any(s in singer for s in classic_singers):
            return "70-90年代"

        modern_singers = ["周杰伦", "陈奕迅", "林俊杰", "梁静茹", "孙燕姿",
                         "五月天", "薛之谦", "毛不易", "周深", "邓紫棋"]
        if any(s in singer for s in modern_singers):
            return "2000-2010年代"

        return "当代"

    def _extract_year(self, publish_time: str) -> str:
        """
        从发布时间提取年份

        Args:
            publish_time: 发布时间字符串

        Returns:
            年份字符串
        """
        if not publish_time:
            return "未知"

        import re
        match = re.search(r'\d{4}', publish_time)
        if match:
            return match.group()

        return "未知"

    def load_music_samples(self, count: int = 1000) -> List[Dict]:
        """
        加载音乐样本数据

        Args:
            count: 采样数量

        Returns:
            音乐列表
        """
        samples = []
        try:
            with open(self.music_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if len(samples) >= count:
                        break

                    song_name = row.get("song", "")
                    singer_name = row.get("singer", "")

                    if song_name and singer_name:
                        song = {
                            "name": song_name,
                            "artist": singer_name,
                            "album": row.get("album", ""),
                            "genre": row.get("genre", "流行"),
                            "era": self._infer_era(singer_name),
                            "description": f"{singer_name}的经典歌曲"
                        }
                        samples.append(song)

            logger.info(f"成功加载 {len(samples)} 条音乐数据")
            return samples

        except FileNotFoundError:
            logger.error(f"音乐CSV文件未找到: {self.music_csv}")
            return []
        except Exception as e:
            logger.error(f"加载音乐数据失败: {str(e)}")
            return []

    def load_tv_samples(self, count: int = 500) -> List[Dict]:
        """
        加载视频样本数据

        Args:
            count: 采样数量

        Returns:
            视频列表
        """
        samples = []
        try:
            with open(self.tv_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if len(samples) >= count:
                        break

                    title = row.get("title", "")
                    if title:
                        video = {
                            "name": title,
                            "type": row.get("genre", ""),
                            "year": self._extract_year(row.get("publishTime", "")),
                            "genre": row.get("genre", ""),
                            "area": row.get("area", ""),
                            "language": row.get("language", ""),
                            "description": f"{row.get('genre', '')}类型的节目"
                        }
                        samples.append(video)

            logger.info(f"成功加载 {len(samples)} 条视频数据")
            return samples

        except FileNotFoundError:
            logger.error(f"视频CSV文件未找到: {self.tv_csv}")
            return []
        except Exception as e:
            logger.error(f"加载视频数据失败: {str(e)}")
            return []

    def load_poem_samples(self, count: int = 200) -> List[Dict]:
        """
        加载诗词/播客样本数据

        Args:
            count: 采样数量

        Returns:
            诗词列表
        """
        samples = []
        try:
            with open(self.poem_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if len(samples) >= count:
                        break

                    poem_name = row.get("poem", "")
                    poet_name = row.get("poet", "")

                    if poem_name and poet_name:
                        poem = {
                            "name": poem_name,
                            "author": poet_name,
                            "dynasty": row.get("dynasty", ""),
                            "type": "poetry",
                            "description": f"{row.get('dynasty', '')}代诗人{poet_name}的作品"
                        }
                        samples.append(poem)

            logger.info(f"成功加载 {len(samples)} 条诗词数据")
            return samples

        except FileNotFoundError:
            logger.error(f"诗词CSV文件未找到: {self.poem_csv}")
            return []
        except Exception as e:
            logger.error(f"加载诗词数据失败: {str(e)}")
            return []
