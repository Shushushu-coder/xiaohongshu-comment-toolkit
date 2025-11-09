@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 小红书爬虫 - 改进启动流程
echo ========================================
echo.
echo 📋 新的启动流程（防风控）:
echo.
echo 第一步：启动Chrome并手动预热账号
echo ----------------------------------------
echo 1. 访问小红书首页
echo 2. 手动登录
echo 3. 随意浏览 5-10 分钟（重要！）
echo    - 刷首页
echo    - 点赞几个笔记
echo    - 看看评论
echo    - 关注1-2个人
echo 4. 手动搜索一次"谷雨"，浏览几个笔记
echo 5. 完成后回到这个窗口
echo.
echo 第二步：等待冷却
echo ----------------------------------------
echo 预热完成后，建议等待 10-30 分钟
echo 让账号"沉淀"，降低风控概率
echo.
echo 第三步：运行爬虫
echo ----------------------------------------
echo 等待时间到了之后，运行: python main_improved.py
echo.
pause

:: 检查并关闭现有Chrome
tasklist /FI "IMAGENAME eq chrome.exe" 2>NUL | find /I /N "chrome.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo 检测到Chrome进程，正在关闭...
    taskkill /F /IM chrome.exe /T >NUL 2>&1
    timeout /t 2 >NUL
)

:: 创建目录
if not exist "E:\xiaohongshu_scraper\data\chrome_profile" mkdir "E:\xiaohongshu_scraper\data\chrome_profile"

echo.
echo 🌐 启动 Chrome...
echo.

:: 启动Chrome（增加更多反检测参数）
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
    --remote-debugging-port=9222 ^
    --user-data-dir="E:\xiaohongshu_scraper\data\chrome_profile" ^
    --disable-blink-features=AutomationControlled ^
    --disable-features=IsolateOrigins,site-per-process ^
    --disable-web-security ^
    --disable-site-isolation-trials ^
    --disable-dev-shm-usage ^
    "https://www.xiaohongshu.com"

timeout /t 3 >NUL

echo.
echo ✅ Chrome 已启动！
echo.
echo ⚠️  现在请按照上面的步骤，花 10-15 分钟手动预热账号
echo.
echo 💡 预热技巧：
echo    - 不要太快，像正常用户一样慢慢浏览
echo    - 点赞、收藏几个笔记
echo    - 看看评论区，甚至发个表情评论
echo    - 这能让小红书认为你是"真人"
echo.
pause