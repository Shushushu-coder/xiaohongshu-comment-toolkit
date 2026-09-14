@echo off
setlocal
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
set "USER_DATA_DIR=%~dp0data\chrome_profile"
set "DEBUG_PORT=9222"
set "XIAOHONGSHU_URL=https://www.xiaohongshu.com"
set "CHROME_EXE="

call :probe_devtools
if not errorlevel 1 goto devtools_ready

call :probe_port
if not errorlevel 1 goto port_conflict

call :find_chrome
if errorlevel 1 goto chrome_not_found

if exist "%USER_DATA_DIR%" goto launch_chrome

mkdir "%USER_DATA_DIR%" >nul 2>&1
if errorlevel 1 goto profile_error

:launch_chrome
start "" "%CHROME_EXE%" ^
  --remote-debugging-port=%DEBUG_PORT% ^
  --user-data-dir="%USER_DATA_DIR%" ^
  "%XIAOHONGSHU_URL%"

if errorlevel 1 goto launch_error

echo.
echo Chrome 调试实例的启动命令已执行。
echo 用户数据目录：BAT 所在目录下的 data\chrome_profile
echo 调试端口：9222
echo.
echo 首次使用时，请在打开的 Chrome 窗口中登录小红书。
echo.
echo 然后在仓库根目录运行：
echo python scraper.py
exit /b 0

:devtools_ready
echo.
echo [信息] 已检测到有效的 Chrome DevTools 服务，端口：9222
echo [信息] 无需重复启动 Chrome。
echo.
echo 请在仓库根目录运行：
echo python scraper.py
exit /b 0

:port_conflict
echo [错误] 端口 9222 已被其他服务监听，但没有检测到有效的 Chrome DevTools 服务。
echo 请手动检查占用该端口的服务，然后重新运行本脚本。
echo 本脚本不会自动结束任何进程。
exit /b 1

:chrome_not_found
echo [错误] 未在常见的系统级或用户级 Chrome 安装位置找到 chrome.exe。
echo 请安装 Chrome 或手动检查安装位置。
exit /b 1

:profile_error
echo [错误] 无法创建 BAT 所在目录下的 data\chrome_profile。
exit /b 1

:launch_error
echo [错误] Chrome 启动命令执行失败。
exit /b 1

:probe_devtools
powershell.exe -NoProfile -Command "try { $uri = 'http://127.0.0.1:' + $env:DEBUG_PORT + '/json/version'; $r = Invoke-RestMethod -Uri $uri -TimeoutSec 2 -ErrorAction Stop; $browser = [string]$r.Browser; $ws = [string]$r.webSocketDebuggerUrl; $ok = -not [string]::IsNullOrWhiteSpace($browser) -and -not [string]::IsNullOrWhiteSpace($ws) -and ($ws.StartsWith('ws://') -or $ws.StartsWith('wss://')) -and $ws.Contains('/devtools/browser/'); if ($ok) { exit 0 }; exit 1 } catch { exit 1 }" >nul 2>&1
exit /b %errorlevel%

:probe_port
powershell.exe -NoProfile -Command "$p = [int]$env:DEBUG_PORT; $found = $false; foreach ($endpoint in [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()) { if ($endpoint.Port -eq $p) { $found = $true; break } }; if ($found) { exit 0 }; exit 1" >nul 2>&1
exit /b %errorlevel%

:find_chrome
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" goto use_program_files
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" goto use_program_files_x86
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" goto use_local_app_data
exit /b 1

:use_program_files
set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
exit /b 0

:use_program_files_x86
set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
exit /b 0

:use_local_app_data
set "CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"
exit /b 0
