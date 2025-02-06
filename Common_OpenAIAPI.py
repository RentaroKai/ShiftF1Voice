import openai
import os
import base64
import requests
from typing import List, Dict, Any
from pydantic import BaseModel
import time

DEFAULT_CHAT_MODEL = "gpt-4o"
DEFAULT_VISION_MODEL = "gpt-4o"
DEFAULT_AUDIO_MODEL = "whisper-1"
DEFAULT_4oAUDIO_MODEL = "gpt-4o-audio-preview"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = ""

DEFAULT_IMAGE_MODEL = "dall-e-3"
DEFAULT_IMAGE_SIZE = "1024x1024"
DEFAULT_IMAGE_QUALITY = "hd"
DEFAULT_IMAGE_STYLE = "vivid"
DEFAULT_IMAGE_FOLDER = os.path.join(os.path.expanduser("~"), "Documents")

DEFAULT_REALTIME_MODEL = "gpt-4o-realtime-preview"
DEFAULT_VOICE = "alloy"

api_key = os.getenv("OPENAI_API_KEY")

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

def generate_transcribe_from_audio(audio_file, model=DEFAULT_AUDIO_MODEL, language="ja", prompt=""):
    client = get_client()
    try:
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

def generate_image(prompt, model=DEFAULT_IMAGE_MODEL, n=1, size=DEFAULT_IMAGE_SIZE, response_format="b64_json", quality=DEFAULT_IMAGE_QUALITY, style=DEFAULT_IMAGE_STYLE, folder_path=DEFAULT_IMAGE_FOLDER, file_name_prefix="generated_image"):
    import time
    client = get_client()
    try:
        response = client.images.generate(
            model=model,
            prompt=prompt,
            n=n,
            size=size,
            response_format=response_format,
            quality=quality,
            style=style
        )
        for i, d in enumerate(response.data):
            file_path = os.path.join(folder_path, f"{file_name_prefix}_{int(time.time())}_{i}.png")
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(d.b64_json))
    except Exception as e:
        print(f"Error during image generation: {e}")
        return None

def generate_audio_response(prompt, voice="alloy", format="wav", model=DEFAULT_4oAUDIO_MODEL):
    client = get_client()
    try:
        print(f"\n=== Audio Response API Call ===")
        print(f"Model: {model}")
        print(f"Voice: {voice}")
        print(f"Format: {format}")
        print(f"Prompt: {prompt}")

        completion = client.chat.completions.create(
            model=model,
            modalities=["text", "audio"],
            audio={"voice": voice, "format": format},
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        print("\n=== API Response ===")
        print(f"Response status: Success")
        print(f"Response type: {type(completion)}")
        print(f"Response details: {completion}")

        audio_data = base64.b64decode(completion.choices[0].message.audio.data)
        return audio_data
    except Exception as e:
        print("\n=== API Error ===")
        print(f"Error during audio generation: {e}")
        return None

async def generate_realtime_audio(
    text,
    voice=DEFAULT_VOICE,
    temperature=DEFAULT_TEMPERATURE,
    model=DEFAULT_REALTIME_MODEL,
    output_dir="audio_responses",
    custom_filename=None,
    instructions=None
):
    import websockets
    import json
    from datetime import datetime
    from pydub import AudioSegment
    import io
    import base64

    print(f"\n=== Realtime Audio API Call ===")
    print(f"Model: {model}")
    print(f"Voice: {voice}")
    print(f"Temperature: {temperature}")
    print(f"Text: {text}")
    print(f"Instructions: {instructions}")

    client = get_client()
    api_key = client.api_key

    uri = f"wss://api.openai.com/v1/realtime?model={model}"

    try:
        async with websockets.connect(uri, extra_headers={
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Beta": "realtime=v1"
        }) as websocket:
            session_update = {
                "type": "session.update",
                "session": {
                    "voice": voice,
                    "temperature": temperature
                }
            }

            if instructions:
                session_update["session"]["instructions"] = instructions

            print("\n=== WebSocket Messages ===")
            print(f"Sending session update: {json.dumps(session_update, indent=2)}")
            await websocket.send(json.dumps(session_update))

            message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": text}
                    ]
                }
            }
            print(f"Sending message: {json.dumps(message, indent=2)}")
            await websocket.send(json.dumps(message))

            print("Sending response create request")
            await websocket.send(json.dumps({"type": "response.create"}))

            audio_data = bytearray()
            event_count = 0
            async for message in websocket:
                event = json.loads(message)
                event_count += 1
                if event['type'] == 'response.audio.delta':
                    audio_data.extend(base64.b64decode(event['delta']))
                elif event['type'] == 'response.audio.done':
                    break
                elif 'error' in event:
                    print(f"\nError event received: {event}")

                if event_count <= 5:
                    print(f"\nReceived event: {event['type']}")

            print(f"\nTotal events received: {event_count}")

            if not audio_data:
                return None

            os.makedirs(output_dir, exist_ok=True)

            if custom_filename:
                filename = f"{custom_filename}.mp3"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"response_audio_{timestamp}.mp3"

            filepath = os.path.join(output_dir, filename)

            audio = AudioSegment.from_raw(
                io.BytesIO(audio_data),
                sample_width=2,
                frame_rate=24000,
                channels=1
            )
            audio.export(filepath, format="mp3")

            return filepath

    except Exception as e:
        print(f"\n=== WebSocket Error ===")
        print(f"Error during realtime audio generation: {e}")
        return None