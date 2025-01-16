import pyperclip
import pyautogui
import datetime
import os
import json
import time
from text_selection_utils import get_selected_text

def is_input_field_active():
    # アクティブなウィンドウやフィールドをチェックするロジックを実装
    # 簡易的にTrueを返す
    return True

def insert_text_to_active_field(text):
    # openAIが間違えていれてくる文章を削除
    text = text.replace("ご視聴ありがとうございました", "")
    text = text.replace("次の動画でお会いしましょう", "")
    text = text.replace("本日はご覧いただきありがとうございます", "")
    # 末尾の空白を削除
    text = text.strip()

    pyperclip.copy(text)
    pyautogui.hotkey('ctrl', 'v')  # Windowsの場合。macOSは('command', 'v')

def save_backup(text):
    # 設定ファイルからバックアップ先を取得
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    backup_dir = config.get('backup_directory', './backups')
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_transcription.txt"
    backup_path = os.path.join(backup_dir, filename)
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(text)

def cleanup_old_backups():
    """
    1日より古いバックアップファイルを削除します
    """
    try:
        # 設定ファイルからバックアップディレクトリを取得
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        backup_dir = config.get('backup_directory', './backups')
        days_to_keep = 1  # 保持期間を1日に固定

        if not os.path.exists(backup_dir):
            return 0

        current_time = datetime.datetime.now()
        deleted_count = 0

        # バックアップファイルの削除
        for filename in os.listdir(backup_dir):
            if not filename.endswith('_transcription.txt'):
                continue

            file_path = os.path.join(backup_dir, filename)
            file_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
            age = current_time - file_time

            if age.days >= days_to_keep:
                os.remove(file_path)
                deleted_count += 1

        # ログファイルの削除
        log_dir = 'logs'
        if os.path.exists(log_dir):
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(log_dir, filename)
                    file_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                    age = current_time - file_time

                    if age.days >= days_to_keep:
                        os.remove(file_path)
                        deleted_count += 1

        return deleted_count
    except Exception as e:
        print(f"ファイルの削除中にエラーが発生しました: {str(e)}")
        return 0

def replace_selected_text(text):
    # 新しいテキストをクリップボードにコピー
    pyperclip.copy(text)
    # Ctrl+Vでペースト
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.1)  # 操作の安定性のために少し待機