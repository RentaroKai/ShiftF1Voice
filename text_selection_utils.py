import time
import pyperclip
import keyboard
import pyautogui

# 選択したテキストを取得する関数
def get_selected_text():
    print("get_selected_textが正しく呼ばれました")
    
    # 現在のクリップボードの内容を保存
    previous_clipboard = pyperclip.paste()
    
    try:
        # Ctrl+Cを送信して選択テキストをコピー
        keyboard.send('ctrl+c')
        time.sleep(0.1)  # 短い待機時間から始める
        
        # クリップボードから新しい選択テキストを取得
        selected_text = pyperclip.paste()
        
        # テキストが選択されていない場合は待機時間を増やして再試行
        attempt = 1
        while not selected_text and attempt < 3:
            time.sleep(0.2 * attempt)  # 待機時間を徐々に増やす
            selected_text = pyperclip.paste()
            attempt += 1
            print(f"試行 {attempt}: テキスト取得を再試行中...")
        
        # 最終的にテキストが取得できなかった場合
        if not selected_text:
            print("テキストが選択されていません。元のクリップボードの内容を使用します。")
            selected_text = previous_clipboard
        
        print("選択されたテキストは", selected_text)
        return selected_text
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return previous_clipboard

def clear_text():
    """
    現在フォーカスされているテキスト入力欄の内容を全て消去します。
    Ctrl+Aで全選択し、Deleteキーで削除します。
    """
    # 全選択（Ctrl+A）
    keyboard.press('ctrl')
    keyboard.press('a')
    time.sleep(0.1)
    keyboard.release('a')
    keyboard.release('ctrl')
    
    # 削除
    keyboard.press_and_release('delete')
    
    return True