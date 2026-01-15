# Voice Assistant Custom Condor

基于Condor框架定制的语音助手多媒体技能多轮对话数据生成器。

## 项目简介

本项目实现了基于Condor理念的2-5轮语音助手对话数据生成，支持音乐、视频、诗词/播客等多种媒体类型的推荐和播放意图。

## 功能特点

1. **多轮对话生成**: 支持2-5轮对话，最后一轮继承上下文并表达播放意图
2. **知识库驱动**: 从CSV文件加载真实媒体数据
3. **播放意图多样性**: 支持5种播放意图类型
   - play_all: 直接播放全部
   - play_nth: 播放第N个
   - play_by_context: 基于上下文条件播放
   - play_referential: 模糊指代播放
   - play_complex: 多轮复杂播放
4. **中间询问轮**: 支持多种询问类型，可以生成新的推荐内容

## 项目结构

```
voice_assistant_custom_condor/
├── config/                    # 配置文件
├── src/                      # 源代码
│   ├── llm/                  # LLM客户端
│   ├── knowledge/              # 知识库管理
│   ├── generators/             # 对话生成器
│   ├── validators/             # 对话验证
│   └── utils/                 # 工具函数
├── scripts/                   # 执行脚本
├── data/                     # 数据输出
└── requirements.txt            # 依赖列表
```

## 快速开始

### 1. 创建Conda环境

```bash
D:\Users\Jinming.Liu1\AppData\Local\anaconda3\Scripts\conda.exe create -n voice_assistant_condor python=3.10 -y
D:\Users\Jinming.Liu1\AppData\Local\anaconda3\Scripts\activate.bat voice_assistant_condor
pip install -r requirements.txt
```

### 2. 加载媒体数据

```bash
python scripts/load_media_data.py
```

### 3. 生成对话数据

```bash
python scripts/generate_dialogues.py
```

生成的数据将保存在 `data/final/` 目录：
- `multiround_dialogues.jsonl`: JSONL格式的对话数据
- `generation_statistics.txt`: 生成统计报告

## 配置说明

### config/llm_config.yaml

LLM API配置：
- `base_url`: API地址
- `api_key`: API密钥
- `model`: 模型名称

### config/generation_config.yaml

生成参数配置：
- `target_count`: 目标生成数量（默认3000）
- `round_distribution`: 对话轮数分布
- `category_distribution`: 类别分布
- `sampling`: 采样参数

### config/multiround_scenarios.yaml

场景配置：定义各类别下的场景、难度和播放意图类型

## 输出数据格式

每条对话为JSON格式，包含：
- `id`: 对话ID
- `metadata`: 元数据（类别、场景、难度、轮数、播放意图类型）
- `dialogue`: 对话轮次列表

每轮对话包含：
- `q`: 用户问题
- `a`: 助手回答
- `round_type`: 轮次类型
- `playback_intent_type`: 播放意图类型（最后一轮）

## 示例对话

```
Q: 可以分享一部适合睡觉前看的电视剧吗
A: 《梦华录》，三个经历过各种困境的女人，携手勇闯汴京...希望这个电视剧能让你满意。

Q: 播放
A: 播放《梦华录》
```

## 数据分布目标

生成3000条对话的预期分布：
- 按轮数: 2轮70%, 3轮20%, 4轮8%, 5轮2%
- 按类别: 音乐40%, 视频40%, 诗词播客20%
- 按播放意图: play_all 20%, play_nth 30%, play_by_context 20%, play_referential 15%, play_complex 15%

## 技术特点

1. **异步并发控制**: 支持异步LLM调用，控制并发数
2. **错误重试**: 使用tenacity实现自动重试
3. **知识库采样**: 从真实媒体数据中随机采样
4. **质量保证**: 多层验证（格式验证、上下文一致性、播放意图准确性）
5. **统计分析**: 生成详细的统计报告

## 许可证

Apache-2.0
