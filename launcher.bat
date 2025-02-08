@echo off
setlocal

REM 仮想環境の存在確認と有効化
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo 仮想環境が見つかりません。システムのPythonを使用します。
)

REM 必要なパッケージの確認
python -c "import keyboard" 2>nul
if errorlevel 1 (
    echo 必要なパッケージをインストールしています...
    pip install -r requirements.txt
)

REM launcherの起動
python launcher.py

endlocal 