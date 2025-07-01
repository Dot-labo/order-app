@echo off
cd /d "%~dp0"
echo 仮想環境を作成中...
python -m venv venv
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
echo セットアップ完了。start_app.bat をダブルクリックしてください。
pause