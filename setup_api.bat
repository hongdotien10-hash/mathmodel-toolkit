@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ================================================
echo   MathModel Toolkit - API Key Setup
echo ================================================
echo.
echo This toolkit uses AI (DeepSeek V4 Pro) to:
echo   - Analyze problems intelligently
echo   - Select the best models
echo   - Write paper sections with real data
echo   - Clean data based on real-world context
echo.
echo Without API key, it still works using local rules.
echo With API key, paper quality improves significantly.
echo API cost: Free version ~0.5-1 RMB, Pro version ~3-5 RMB.
echo.

:: Check if .env already exists
if exist ".env" (
    echo [INFO] .env file already exists.
    echo.
    type .env
    echo.
    set /p overwrite="Overwrite? (y/n, default n): "
    if /i not "%overwrite%"=="y" goto :end
)

echo.
echo Select your API provider:
echo   [1] DeepSeek V4 Pro (Recommended - cheapest, best for Chinese)
echo   [2] OpenAI (GPT-4o)
echo   [3] Zhipu GLM
echo   [4] Tongyi Qianwen
echo   [5] Kimi (Moonshot)
echo   [6] I already have a key, just enter it
echo.
set /p choice="Enter 1-6 (default 1): "
if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo.
    echo === DeepSeek V4 Pro ===
    echo Get your key at: https://platform.deepseek.com
    echo 1. Register/Login at platform.deepseek.com
    echo 2. Go to API Keys page
    echo 3. Click "Create new API key"
    echo 4. Copy the key (starts with sk-)
    echo.
    set /p apikey="Paste your DeepSeek API key: "
    echo DEEPSEEK_API_KEY=%apikey%> .env
    echo # DeepSeek V4 Pro>> .env
    goto :done
)

if "%choice%"=="2" (
    echo.
    echo === OpenAI ===
    echo Get your key at: https://platform.openai.com/api-keys
    echo.
    set /p apikey="Paste your OpenAI API key (sk-...): "
    echo OPENAI_API_KEY=%apikey%> .env
    echo LLM_PROVIDER=openai>> .env
    echo LLM_MODEL=gpt-4o>> .env
    goto :done
)

if "%choice%"=="3" (
    echo.
    echo === Zhipu GLM ===
    echo Get your key at: https://open.bigmodel.cn
    echo.
    set /p apikey="Paste your Zhipu API key: "
    echo ZHIPU_API_KEY=%apikey%> .env
    echo LLM_PROVIDER=zhipu>> .env
    goto :done
)

if "%choice%"=="4" (
    echo.
    echo === Tongyi Qianwen ===
    echo Get your key at: https://dashscope.console.aliyun.com
    echo.
    set /p apikey="Paste your DashScope API key: "
    echo DASHSCOPE_API_KEY=%apikey%> .env
    echo LLM_PROVIDER=qwen>> .env
    goto :done
)

if "%choice%"=="5" (
    echo.
    echo === Kimi (Moonshot) ===
    echo Get your key at: https://platform.moonshot.cn
    echo.
    set /p apikey="Paste your Kimi API key: "
    echo MOONSHOT_API_KEY=%apikey%> .env
    echo LLM_PROVIDER=moonshot>> .env
    goto :done
)

if "%choice%"=="6" (
    echo.
    echo === Custom Key ===
    set /p apikey="Paste your API key: "
    echo DEEPSEEK_API_KEY=%apikey%> .env
    goto :done
)

:done
echo.
echo ================================================
echo   API Key saved to .env file!
echo ================================================
echo.
echo The .env file is gitignored and will NOT be
echo uploaded to GitHub. Your key is safe.
echo.
echo You can now run run.bat to start the toolkit.
echo.

:end
pause
