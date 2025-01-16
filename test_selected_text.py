from test import get_selected_text

def main():
    print("テキストを選択してから、Enterキーを押してください...")
    input()  # Enterキーの入力を待機
    
    try:
        selected_text = get_selected_text()
        print("選択されたテキスト:")
        print("-" * 40)
        print(selected_text)
        print("-" * 40)
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main() 