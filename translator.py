import re
from langdetect import detect


from Common_OpenAIAPI import generate_chat_response

class Translator:
    def __init__(self):
        pass

    def detect_language(self, text: str) -> str:
        # 日本語文字（ひらがな、カタカナ、漢字）の検出
        if re.search(r'[ぁ-んァ-ン一-龥]', text):
            return 'ja'
        
        try:
            # langdetectを使用した言語検出
            return detect(text)
        except:
            # デフォルトは英語として扱う
            return 'en'

    def translate(self, text: str) -> str:
        if not text.strip():
            return ""

        source_lang = self.detect_language(text)
        
        if source_lang == 'ja':
            prompt = "以下の日本語を自然な英語に翻訳してください。なお、LLMやプログラム用語が多く含まれる可能性があります:\n" + text
        else:
            prompt = "以下の英語を自然な日本語に翻訳してください。なお、LLMやプログラム用語が多く含まれる可能性があります:\n" + text

        try:
            response = generate_chat_response(
                system_prompt="あなたは高性能な翻訳システムです。",
                user_message_content=prompt
            )
            return response.strip() if response else "翻訳エラー: レスポンスが空です"
        except Exception as e:
            return f"翻訳エラー: {str(e)}"