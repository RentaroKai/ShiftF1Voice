import json
import keyboard
import socket
import subprocess
import time
import sys
import os
import logging
from datetime import datetime

def setup_logging():
    """ログ設定の初期化"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'launcher_{datetime.now().strftime("%Y%m%d")}.log')
    
    logger = logging.getLogger('Launcher')
    logger.setLevel(logging.DEBUG)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def load_config():
    """設定ファイルの読み込み"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("config.jsonが見つかりません")
        return {
            "hotkey": "shift+f24",
            "launcher_enabled": True,
            "launcher_startup_delay": 1.0
        }
    except json.JSONDecodeError:
        logger.error("config.jsonの形式が不正です")
        return None

def try_start_app():
    """アプリケーションの起動を試みる"""
    logger.info("アプリケーション起動処理を開始")
    try:
        # 直接起動
        subprocess.Popen(["python", "voice_input_app.py"])
        logger.info("アプリケーションを起動しました")
        return True
    except Exception as e:
        logger.error(f"アプリケーションの起動に失敗しました: {str(e)}")
        return False

def setup_launcher_hotkey():
    """ランチャーのホットキーを設定"""
    try:
        hotkey = config.get('launcher_hotkey', config.get('hotkey', 'shift+f24'))
        logger.info(f"ホットキーを設定: {hotkey}")
        keyboard.add_hotkey(hotkey, try_start_app)
        return True
    except Exception as e:
        logger.error(f"ホットキーの設定に失敗しました: {str(e)}")
        return False

if __name__ == "__main__":
    logger = setup_logging()
    logger.info("ランチャーを起動します")
    
    # 設定の読み込み
    config = load_config()
    if config is None:
        logger.error("設定の読み込みに失敗しました。終了します")
        sys.exit(1)
    
    # ホットキーの設定
    if not setup_launcher_hotkey():
        logger.error("ホットキーの設定に失敗しました。終了します")
        sys.exit(1)
    
    logger.info("ランチャーの準備が完了しました。待機を開始します")
    print(f"ランチャーが起動しました。ホットキー: {config.get('launcher_hotkey', config.get('hotkey', 'shift+f24'))}")
    
    # メインループ
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        logger.info("ランチャーを終了します")
        print("ランチャーを終了します") 