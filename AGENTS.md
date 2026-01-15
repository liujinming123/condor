# AGENTS.md - Voice Assistant Custom Condor

## Project Overview

This project generates multi-round (2-5 turns) voice assistant dialogue data for music, video, and poem/podcast recommendations using LLM-based generation with knowledge base support and validation.

## Build/Run Commands

### Setup Environment (Windows)
```bash
# Create conda environment
D:\Users\Jinming.Liu1\AppData\Local\anaconda3\Scripts\conda.exe create -n voice_assistant_condor python=3.10 -y
D:\Users\Jinming.Liu1\AppData\Local\anaconda3\Scripts\activate.bat voice_assistant_condor
pip install -r requirements.txt
```

### Load Media Knowledge Base
```bash
python scripts/load_media_data.py
```

### Generate Dialogue Data
```bash
python scripts/generate_dialogues.py
python scripts/test_generation.py
python scripts/test_small_generation.py
python scripts/simple_generate.py
```

### Run Tests
```bash
# Run specific test file
pytest scripts/test_generation.py -v

# Run single test function
pytest scripts/test_generation.py::test_generation -v

# Run with coverage
pytest --cov=src scripts/ -v
```

### Code Formatting
```bash
# Format code
black src/ scripts/

# Check formatting
black src/ scripts/ --check
```

## Code Style Guidelines

### Imports

**Order:** Standard Library → Third-Party → Local (relative)
```python
import asyncio
import json
import random
from datetime import datetime
from typing import Dict, List

import logging
import yaml

from src.llm.async_client import AsyncLLMClient
from .recommend_round_generator import RecommendRoundGenerator
```

**Rules:** Use absolute imports for src/, relative for same package, blank lines between groups, alphabetize.

### Formatting

- **Line Length:** 120 characters max
- **Quotes:** Double quotes unless single needed
- **Blank Lines:** 2 between classes, 1 between methods
- **Indentation:** 4 spaces (no tabs)

### Type Hints

Required for function signatures. Use concrete types when possible.
```python
async def generate_dialogue(
    self,
    category: str,
    scenario: str,
    difficulty: str,
    intent_type: str
) -> Dict[str, any]:
```

### Naming Conventions

| Pattern | Style | Example |
|---------|-------|---------|
| Classes | PascalCase | `MultiRoundDialogueGenerator` |
| Functions/Methods | snake_case | `generate_dialogue`, `_sample_round_count` |
| Constants | UPPER_SNAKE_CASE | `ROUND_DISTRIBUTION` |
| Variables | snake_case | `dialogue_count` |
| Private Methods | leading underscore | `_create_empty_dialogue` |

### Docstrings & Comments

- **Class:** Chinese description
- **Methods:** Chinese with English Args section
- **Inline:** Chinese for business logic, explain WHY not WHAT

```python
class MultiRoundDialogueGenerator:
    """多轮对话生成器（核心协调器）"""

def _sample_round_count(self) -> int:
    """
    随机采样对话轮数（2-5轮）

    Returns:
        轮数
    """
```

### Error Handling

```python
logger = logging.getLogger(__name__)

try:
    # operation
except Exception as e:
    logger.error(f"生成对话失败: {str(e)}")
    return fallback_value
```

**Rules:** Always log errors with descriptive messages, return sensible fallbacks, never expose API keys in logs.

### Async/Await

```python
async def call_llm(...) -> str:
    async with self.semaphore:
        await asyncio.sleep(request_interval)
        return await self._call_llm_internal(...)
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
├── scripts/            # Execution scripts
└── requirements.txt
```

### Configuration

- Use `yaml.safe_load()` for YAML files
- Access nested values: `config["generation"]["target_count"]`
- Never commit actual API keys

## Development Environment (Windows)

- **Python Path:** `D:\Users\Jinming.Liu1\AppData\Local\anaconda3`
- **Repo Root:** `D:\Geely work\code\git_program`
- **Terminal:** Use PowerShell for Windows commands
- **Switch Drives:** `d:` before file operations

## Critical Rules

1. **Encoding:** Add `# coding: utf-8` if file contains Chinese characters
2. **Syntax:** Ensure `( { [ "`'` all properly paired and nested
3. **Remote Services:** Test return format with demo code before full implementation
4. **Package Compatibility:** Fix by updating code or package version
5. **Error Handling:** Do NOT use try-except to suppress errors during development - expose and debug

**版本:** v1.1.0
**最后更新:** 2026-01-15
