@echo off
REM PF2 Translation Tools - Build Script
REM Creates a minimal-size executable

echo ========================================
echo PF2 翻译工具 - 打包脚本
echo ========================================
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安装 PyInstaller...
    pip install pyinstaller
)

REM Download UPX for compression (optional but recommended)
if not exist "upx" (
    echo.
    echo [提示] 建议下载 UPX 以进一步压缩 exe 文件
    echo 下载地址: https://github.com/upx/upx/releases
    echo 将 upx.exe 放入项目目录的 upx 文件夹中
    echo.
)

echo.
echo 开始打包...
echo.

REM Run PyInstaller with spec file
if exist "build.spec" (
    pyinstaller --clean build.spec
) else (
    REM Fallback: single-file build without spec
    pyinstaller --onefile --noconsole --name "PF2翻译工具" ^
        --add-data "nltk_data;nltk_data" ^
        --exclude-module matplotlib ^
        --exclude-module scipy ^
        --exclude-module PIL ^
        --exclude-module unittest ^
        main.py
)

echo.
echo ========================================
if exist "dist\PF2翻译工具.exe" (
    echo 打包完成！
    echo 输出文件: dist\PF2翻译工具.exe
    for %%A in ("dist\PF2翻译工具.exe") do echo 文件大小: %%~zA bytes
) else (
    echo 打包失败，请检查错误信息
)
echo ========================================
pause
