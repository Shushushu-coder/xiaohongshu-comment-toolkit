@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 启动小红书爬虫 - Chrome 调试模式
echo ========================================
echo.
echo ⚠️  注意事项:
echo 1. 关闭所有现有的 Chrome 窗口!
echo 2. 不要关闭此窗口打开的 Chrome!
echo.
pause

:: 创建必要的目录
if not exist "D:\桌面\识别广告\xiaohongshu_scraper\data\chrome_profile" mkdir "D:\桌面\识别广告\xiaohongshu_scraper\data\chrome_profile"

echo.
echo 🔍 正在检查 Chrome 进程...
tasklist /FI "IMAGENAME eq chrome.exe" 2>NUL | find /I /N "chrome.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo ⚠️  检测到运行中的 Chrome 进程!
    echo 📌 建议: 先关闭所有 Chrome 窗口
    echo.
    choice /C YN /M "是否强制关闭所有 Chrome 进程? (Y=是, N=取消)"
    if errorlevel 2 goto :EOF
    echo 正在关闭 Chrome 进程...
    taskkill /F /IM chrome.exe /T >NUL 2>&1
    timeout /t 2 >NUL
)

echo.
echo 🌐 启动 Chrome 调试模式...
echo 📍 调试端口: 9222
echo 📂 配置目录: D:\桌面\识别广告\xiaohongshu_scraper\data\chrome_profile
echo.

:: 启动 Chrome 调试模式
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
    --remote-debugging-port=9222 ^
    --user-data-dir="D:\桌面\识别广告\xiaohongshu_scraper\data\chrome_profile" ^
    --disable-blink-features=AutomationControlled ^
    --disable-features=IsolateOrigins,site-per-process ^
    "https://www.xiaohongshu.com"

timeout /t 3 >NUL

echo.
echo ✅ Chrome 已启动!
echo.
echo 📋 下一步操作:
echo 1. 在打开的 Chrome 中手动登录小红书
echo 2. 登录完成后运行: python main.py
echo 3. 程序会自动连接到这个 Chrome 实例
echo.
echo ⚠️  重要: 程序运行期间不要关闭这个 Chrome 窗口!
echo.
pause