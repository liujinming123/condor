@echo off
echo ================================================================
echo Voice Assistant Custom Condor - 快速启动脚本
echo ================================================================
echo.

echo [1] 创建Conda环境...
D:\Users\Jinming.Liu1\AppData\Local\anaconda3\Scripts\conda.exe create -n voice_assistant_condor python=3.10 -y

echo.
echo [2] 激活环境并安装依赖...
call D:\Users\Jinming.Liu1\AppData\Local\anaconda3\Scripts\activate.bat voice_assistant_condor
pip install -r requirements.txt

echo.
echo [3] 加载媒体数据...
python scripts/load_media_data.py

echo.
echo [4] 生成对话数据...
python scripts/generate_dialogues.py

echo.
echo ================================================================
echo 完成！
echo ================================================================
echo.
echo 生成的数据位于: data/final/
echo   - multiround_dialogues.jsonl
echo   - generation_statistics.txt
echo.
echo ================================================================
