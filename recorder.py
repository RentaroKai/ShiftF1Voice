import sounddevice as sd
import wavio
import tempfile
import numpy as np
import logging
import time

class Recorder:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.samplerate = 16000
        self.channels = 1
        self.filename = None
        self.recording = []
        self.is_recording = False
        self.silence_threshold = 500  # Adjust this value based on testing
        self.silence_duration = 10  # seconds
        self.last_non_silence_time = None
        self.silence_callback = None

    def start_recording(self, silence_callback=None):
        self.logger.info("録音開始")
        self.recording = []
        self.is_recording = True
        self.silence_callback = silence_callback
        self.last_non_silence_time = time.time()

        def callback(indata, frames, time_info, status):
            if not self.is_recording:
                return
            amplitude = np.abs(indata).max()
            if amplitude > self.silence_threshold:
                self.last_non_silence_time = time.time()
            else:
                current_time = time.time()
                if current_time - self.last_non_silence_time > self.silence_duration:
                    self.logger.info("無音が10秒以上続いたため録音をキャンセルします")
                    self.stop_recording()
                    if self.silence_callback:
                        self.silence_callback()
                    return
            self.recording.append(indata.copy())

        try:
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                callback=callback,
                dtype=np.int16
            )
            self.stream.start()
        except Exception as e:
            self.logger.error(f"録音ストリーム開始中にエラー: {e}")
            self.is_recording = False
            if self.silence_callback:
                self.silence_callback()

    def stop_recording(self):
        self.logger.info("録音停止")
        if hasattr(self, 'stream'):
            self.is_recording = False
            self.stream.stop()
            self.stream.close()

            if self.recording:
                self.recording = np.concatenate(self.recording, axis=0)
                temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                wavio.write(temp_wav.name, self.recording, self.samplerate, sampwidth=2)
                self.filename = temp_wav.name

    def get_audio_file(self):
        return self.filename