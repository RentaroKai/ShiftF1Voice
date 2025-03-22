import openai
import os
import base64
import requests
from typing import List, Dict, Any
from pydantic import BaseModel
import time
import json

DEFAULT_CHAT_MODEL = "gpt-4o"
DEFAULT_VISION_MODEL = "gpt-4o"
DEFAULT_AUDIO_MODEL = "whisper-1"
DEFAULT_4oAUDIO_MODEL = "gpt-4o-audio-preview"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = ""


DEFAULT_IMAGE_FOLDER = os.path.join(os.path.expanduser("~"), "Documents")



api_key = os.getenv("OPENAI_API_KEY")

def get_transcriber_model():
    """
    設定ファイルからtranscriber_modelを読み込む
    設定ファイルがない場合やモデル設定がnullの場合はデフォルト値を使用
    """
    config_path = 'config.json'
    print(f"[LOG] 設定ファイルの読み込みを試行: {config_path}")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            print(f"[LOG] 設定ファイル読み込み成功: {config}")
            if 'audio' in config and 'transcriber_model' in config['audio'] and config['audio']['transcriber_model']:
                model = config['audio']['transcriber_model']
                print(f"[LOG] 設定ファイルからモデルを取得: {model}")
                return model
            else:
                print(f"[LOG] 設定ファイルにモデル設定がないかnullのため、デフォルト値を使用: {DEFAULT_AUDIO_MODEL}")
    except FileNotFoundError:
        print(f"[LOG] 設定ファイルが見つかりません: {config_path}")
    except json.JSONDecodeError:
        print(f"[LOG] 設定ファイルのJSONが不正です: {config_path}")
    except KeyError as e:
        print(f"[LOG] 設定ファイルに必要なキーがありません: {e}")
    except Exception as e:
        print(f"[LOG] 予期せぬエラーが発生しました: {e}")
    print(f"[LOG] デフォルトモデルを使用: {DEFAULT_AUDIO_MODEL}")
    return DEFAULT_AUDIO_MODEL

def get_client():    
    if 'SSL_CERT_FILE' in os.environ:
        del os.environ['SSL_CERT_FILE']
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key is not set in environment variables.")
    openai.api_key = api_key
    return openai.OpenAI()

def generate_chat_response(system_prompt, user_message_content, max_tokens=DEFAULT_MAX_TOKENS, temperature=DEFAULT_TEMPERATURE, model_name=DEFAULT_CHAT_MODEL, retries=3):
    client = get_client()
    for attempt in range(retries):
        try:
            params = {
                "model": model_name,
                "temperature": temperature,
                "messages": []
            }

            if system_prompt:
                params["messages"].append({"role": "system", "content": system_prompt})

            params["messages"].append({"role": "user", "content": user_message_content})

            if isinstance(max_tokens, int) and max_tokens > 0:
                params["max_tokens"] = max_tokens

            response = client.chat.completions.create(**params)
            print(response)
            return response.choices[0].message.content

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                print("Retrying...")
                time.sleep(10)
            else:
                print("All attempts failed.")
                return None

class ResponseStep(BaseModel):
    steps: List[str]
    answers: List[str]

def generate_chat_responseStruct(messages: List[Dict[str, Any]], response_format: BaseModel, model: str = DEFAULT_CHAT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
    client = get_client()
    response = client.beta.chat.completions.parse(
        model=model,
        temperature=temperature,
        messages=messages,
        response_format=response_format,
    )
    return response

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_vision_ai_api(image_path, prompt_text, model=DEFAULT_VISION_MODEL):
    import certifi
    client = get_client()
    base64_image = encode_image(image_path)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        verify=certifi.where()
    )
    return response.json()

def generate_transcribe_from_audio(audio_file, model=None, language="ja", prompt=""):
    client = get_client()
    try:
        # モデルが指定されていない場合は設定から読み込む
        if model is None:
            model = get_transcriber_model()
        
        transcript = client.audio.transcriptions.create(
            file=audio_file,
            model=model,
            response_format="json",
            language=language,
            prompt=prompt,
        )
        return transcript.text
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None
