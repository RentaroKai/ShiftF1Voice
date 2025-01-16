import logging
import sys
import os

# Common_OpenAIAPI のインポート
from Common_OpenAIAPI import generate_transcribe_from_audio

class TranscriptionError(Exception):
    """音声文字起こし処理中のエラーを表す例外クラス"""
    pass

class Transcriber:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.system_prompt = """プログラミング用語、技術用語、LLM関連の専門用語が頻出します。
これらの英語の技術用語は、日本語の文脈でも正確に認識して保持してください。頻発用語例：exe(エグゼ),仕様書"""

    def transcribe(self, audio_file):
        try:
            with open(audio_file, "rb") as file:
                transcript = generate_transcribe_from_audio(
                    file,
                    prompt=self.system_prompt
                )

            if transcript is None:
                raise TranscriptionError("文字起こし処理に失敗しました")

            self.logger.info("音声の文字起こしが完了しました")
            return transcript

        except FileNotFoundError:
            self.logger.error(f"ファイルが見つかりません: {audio_file}")
            raise TranscriptionError(f"音声ファイルが見つかりません: {audio_file}")

        except Exception as e:
            self.logger.error(f"予期せぬエラー: {str(e)}")
            raise TranscriptionError(f"予期せぬエラーが発生しました: {str(e)}")