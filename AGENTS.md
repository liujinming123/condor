# AGENTS.md - Voice Assistant Custom Condor

## Project Overview

Multi-round dialogue generator for voice assistant data (music/video/poem/podcast).

## Build/Run Commands

### Setup Environment
```bash
# Linux/macOS
conda create -n ljm_condor python=3.10 -y
conda activate ljm_condor
pip install -r requirements.txt

# Windows
D:\Users\Jinming.Liu1\AppData\Local\anaconda3\Scripts\conda.exe create -n voice_assistant_condor python=3.10 -y
D:\Users\Jinming.Liu1\AppData\Local\anaconda3\Scripts\activate.bat voice_assistant_condor
pip install -r requirements.txt
```

### Load Media Knowledge Base & Generate Dialogues
```bash
python scripts/load_media_data.py
python scripts/generate_dialogues.py
```

### Run Tests
```bash
pytest scripts/test_generation.py -v                          # All tests
pytest scripts/test_generation.py::test_generation -v         # Single test
pytest --cov=src scripts/ -v                                   # With coverage
```

### Code Formatting
```bash
black src/ scripts/ --check    # Check
black src/ scripts/             # Format
```

## Code Style Guidelines

### Imports (3 groups, alphabetized)
```python
import asyncio
from typing import Dict

import yaml

from src.llm import AsyncLLMClient
from .local_module import ClassName
```

### Formatting
- Line length: 120 chars
- Quotes: double quotes unless single needed
- Indentation: 4 spaces

### Type Hints (required for functions)
```python
async def generate(self, category: str) -> Dict[str, any]:
```

### Naming Conventions
| Type | Style | Example |
|------|-------|---------|
| Classes | PascalCase | `MultiRoundDialogueGenerator` |
| Functions/Methods | snake_case | `generate_dialogue` |
| Constants | UPPER_SNAKE_CASE | `ROUND_DISTRIBUTION` |
| Variables | snake_case | `dialogue_count` |
| Private | leading underscore | `_sample_round_count` |

### Docstrings & Comments
- Class: Chinese description
- Methods: Chinese with English Args
- Inline: Chinese, explain WHY not WHAT

```python
class Generator:
    """对话生成器"""

def _method(self) -> str:
    """
    处理数据

    Args:
        data: 输入数据
    Returns:
        处理结果
    """
```

### Error Handling
```python
logger = logging.getLogger(__name__)

try:
    result = operation()
except Exception as e:
    logger.error(f"操作失败: {str(e)}")
    return fallback_value
```
- Always log errors with descriptive messages
- Return sensible fallbacks
- **NEVER suppress errors during development - expose and debug**

### LLM Retry Pattern
```python
max_retries = 3
for attempt in range(max_retries):
    response = await llm_client.call_llm(...)
    
    if not response:
        if attempt < max_retries - 1:
            await asyncio.sleep(1)
            continue
        # Use fallback/default after max retries
    ...
```
- Max retries: 3
- Retry interval: 1 second
- Use fallback/default after max retries

### Async/Await
```python
async def call_llm() -> str:
    async with self.semaphore:
        await asyncio.sleep(interval)
        return await self._call_internal()
```

### Project Structure
```
voice_assistant_custom_condor/
├── config/              # YAML configs
├── src/
│   ├── llm/            # AsyncLLMClient
│   ├── knowledge/      # MediaKnowledgeManager
│   ├── generators/     # Dialogue generators
│   ├── validators/     # Quality validation
│   └── utils/          # Utilities
│       └── retry_helper.py   # LLM retry utility
├── scripts/            # Execution scripts
└── requirements.txt
```

### Configuration
- Use `yaml.safe_load()` for YAML
- Access nested: `config["generation"]["target_count"]`
- **Never commit actual API keys**

## Critical Rules
1. **Encoding:** Add `# coding: utf-8` for files with Chinese characters
2. **Syntax:** Verify `( { [ "`'` are properly paired and nested
3. **Remote Services:** Test return format with demo code before full implementation
4. **Package Compatibility:** Update code or package version to fix compatibility
5. **Error Handling:** During development, DO NOT use try-except to suppress errors

**Version:** v1.2.1
**Last Updated:** 2026-01-19
