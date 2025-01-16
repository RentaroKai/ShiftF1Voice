import sys
import os
import tkinter as tk
from tkinter import messagebox
from recorder import Recorder
from transcriber import Transcriber
from translator import Translator
import utils
import threading
import json
import keyboard  # 新しくインポート
import logging
from datetime import datetime
import time
import psutil  # 新しくインポート
import socket
from contextlib import contextmanager

from Common_OpenAIAPI import generate_chat_response
# TrayIcon クラスをインポート
from tray_icon import TrayIcon

def prevent_multiple_instances():
    """Prevent multiple instances of the application from running"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Try to bind to a local port
        sock.bind(('localhost', 47200))  # You can change this port number
    except socket.error:
        # Port is already in use, which means another instance is running
        print("Another instance is already running")
        sys.exit(0)
    return sock

class VoiceInputApp:
    def __init__(self):
        # まずログ設定を初期化
        self.setup_logging()
        
        # 多重起動チェック
        if self.is_already_running():
            self.logger.info("既存のアプリケーションを終了します")
            self.terminate_existing_instance()
            time.sleep(1)  # 既存プロセスの終了を待つ

        # config.jsonのパスを取得
        if getattr(sys, 'frozen', False):
            # exe実行時のパス
            config_path = os.path.join(sys._MEIPASS, 'config.json')
        else:
            # 通常実行時のパス
            config_path = 'config.json'

        # 設定ファイルの読み込み
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # 設定ファイルが見つからない場合はデフォルト値を設定
            self.config = {
                'hotkey': 'shift+f1',
                'cancel_hotkey': 'shift+f2',
                'post_process_hotkey': 'shift+f3',
                'window_position': {'x': 100, 'y': 100}
            }
            # 設定ファイルを作成
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)

        self.hotkey = self.config.get('hotkey', 'shift+f1')
        self.cancel_hotkey = self.config.get('cancel_hotkey', 'shift+f2')
        self.translate_hotkey = 'shift+f21'
        # ウィンドウ位置の設定を読み込み
        self.window_position = self.config.get('window_position', {'x': 100, 'y': 100})

        self.recorder = Recorder()
        self.transcriber = Transcriber()
        self.openai_api = generate_chat_response
        self.translator = Translator()
        self.is_recording = False
        self.post_process_hotkey = self.config.get('post_process_hotkey', 'shift+f3')
        self.is_post_processing = False
        self.setup_gui()
        self.setup_hotkey()
        # self.root.after(100, self.setup_tray)  # のセットアップをコメントアウト
        self.logger.info("アプリケーションを初期化しました")

        # 処理中断フラグを追加
        self.is_processing = False
        self.should_cancel = False

    def setup_logging(self):
        # ログディレクトリの作成
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)

        # ログファイル名に日付を含める
        log_file = os.path.join(log_dir, f'voice_input_{datetime.now().strftime("%Y%m%d")}.log')

        # ログの設定
        self.logger = logging.getLogger('VoiceInputApp')
        self.logger.setLevel(logging.DEBUG)

        # ファインドラの設定
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Voice Input")
        # ウィンドウを少し大きくして新しいボタンを収容
        self.root.geometry(f"150x90+{self.window_position['x']}+{self.window_position['y']}")
        # 常に最前面に表示
        self.root.attributes('-topmost', True)
        # 背景色を設定（デフォルト状態: 薄い青）
        self.root.configure(bg='#e6f3ff')

        # ステータスラベルとボタンを1行に配置
        frame = tk.Frame(self.root, bg='#e6f3ff')
        frame.pack(expand=True, fill='both', padx=5, pady=5)

        self.status_label = tk.Label(frame, text="待機中", bg='#e6f3ff')
        self.status_label.pack(side='left', padx=5)

        # ボタンを配置するフレームを追加
        button_frame = tk.Frame(frame, bg='#e6f3ff')
        button_frame.pack(side='right', padx=5)

        self.cancel_button = tk.Button(button_frame, text="×", width=2, command=self.cancel_recording)
        self.cancel_button.pack(side='right', padx=2)

        self.start_button = tk.Button(button_frame, text="録音", width=6, command=self.toggle_recording)
        self.start_button.pack(side='right', padx=2)

        self.chat_button = tk.Button(button_frame, text="Chat", width=6, command=self.start_post_processing)
        self.chat_button.pack(side='right', padx=2)

        # バックアップファイルを開くボタンを追加
        self.open_backup_button = tk.Button(button_frame, text="履歴", width=6, command=self.open_latest_backup)
        self.open_backup_button.pack(side='right', padx=2)

        # ウィンドウが移動された時のイベントをバインド
        self.root.bind('<Configure>', self.on_window_move)

    def setup_hotkey(self):
        try:
            # 完全なクリーンアップを実行
            keyboard.unhook_all()
            # 少し待機して、システムのホットキー状態をリセット
            time.sleep(0.1)

            # 録音開始/停止のホットキー
            keyboard.on_press_key(self.hotkey.split('+')[1], self.handle_hotkey)
            # キャンセル用のホットキー
            keyboard.on_press_key(self.cancel_hotkey.split('+')[1], self.handle_cancel_hotkey)
            # 後処理用のホットキー
            keyboard.on_press_key(self.post_process_hotkey.split('+')[1], self.handle_post_process_hotkey)
            # 翻訳用のホットキー
            keyboard.on_press_key('f21', self.handle_translate_hotkey)

            self.logger.info(f"ホットキー '{self.hotkey}' と '{self.cancel_hotkey}' と '{self.post_process_hotkey}' と '{self.translate_hotkey}' を設定しました")
        except Exception as e:
            self.logger.error(f"ホットキー設定中にエラー: {str(e)}")
            messagebox.showerror("エラー", f"ホットキー設定エラー：\n{e}")

    def handle_hotkey(self, event):
        try:
            # Shiftキーが押されているかチェック
            if keyboard.is_pressed('shift'):
                self.logger.debug("Shift+F1 が押されました")
                if self.is_recording:
                    self.stop_recording()
                else:
                    self.start_recording()
        except Exception as e:
            self.logger.error(f"ホットキー処理中にエラー: {str(e)}")

    def handle_cancel_hotkey(self, event):
        try:
            # Shiftキーが押されているかチェック
            if keyboard.is_pressed('shift'):
                self.logger.debug("Shift+F23 が押されました")
                if self.is_recording:
                    self.cancel_recording()
                elif self.is_processing:
                    self.cancel_processing()
                elif self.is_post_processing:
                    self.cancel_post_processing()
        except Exception as e:
            self.logger.error(f"キャンセルホットキー処理中にエラー: {str(e)}")

    def handle_post_process_hotkey(self, event):
        try:
            if keyboard.is_pressed('shift'):
                self.logger.debug("Shift+F3 が押されました")
                if self.is_post_processing:
                    # 処理中なら録音を停止してOpenAIに送信
                    self.stop_post_processing()
                else:
                    # 処理中でなければ開始
                    self.start_post_processing()
        except Exception as e:
            self.logger.error(f"後処理ホットキー処理中にエラー: {str(e)}")

    def handle_translate_hotkey(self, event):
        try:
            if keyboard.is_pressed('shift'):
                self.logger.debug("Shift+F21 が押されました")
                self.translate_selected_text()
        except Exception as e:
            self.logger.error(f"翻訳ホットキー処理中にエラー: {str(e)}")

    def translate_selected_text(self):
        try:
            # 選択中のテキストを取得
            selected_text = utils.get_selected_text()
            print ("選択テキストは", selected_text)
            if not selected_text:
                self.logger.warning("テキストが選択されていません")
                messagebox.showwarning("警告", "テキストが選択されていません")
                return

            # UIを翻訳中の状態に更新
            self.status_label.config(text="翻訳中")
            self.root.configure(bg='#90EE90')  # 薄い緑色
            self.status_label.configure(bg='#90EE90')

            # 翻訳を実行
            translated_text = self.translator.translate(selected_text)
            if translated_text:
                # 翻訳結果で選択テキストを置換
                utils.replace_selected_text(translated_text)
                self.logger.info("翻訳が完了しました")
            else:
                self.logger.warning("翻訳結果が空です")
                messagebox.showwarning("警告", "翻訳に失敗しました")

        except Exception as e:
            self.logger.error(f"翻訳処理中にエラー: {str(e)}")
            messagebox.showerror("エラー", f"翻訳処理中にエラーが発生しました：\n{e}")
        finally:
            # UIを待機中の状態に戻す
            self.status_label.config(text="待機中")
            self.root.configure(bg='#e6f3ff')  # デフォルトの薄い青色
            self.status_label.configure(bg='#e6f3ff')

    def toggle_recording(self, event=None):
        self.logger.info(f"ホットキーが押されました。現在の状態: recording={self.is_recording}")
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.logger.info("録音開始処理を実行します")
        if not utils.is_input_field_active():
            self.logger.warning("入力欄が選択されていません")
            messagebox.showerror("エラー", "入力欄が選択されていません。")
            return
        self.is_recording = True
        self.status_label.config(text="録音中")
        self.root.configure(bg='#ff9999')
        self.status_label.configure(bg='#ff9999')
        self.start_button.configure(text="停止")
        self.logger.info("録音スレッドを開始します")
        threading.Thread(target=self.recorder.start_recording, args=(self.on_silence_detected,)).start()

    def on_silence_detected(self):
        """無音が検出されたときに呼び出されるコールバック"""
        self.logger.info("無音検出による録音キャンセルを処理します")
        self.is_recording = False
        # Use the after method to safely update the UI from the main thread
        self.root.after(0, self.update_ui_after_silence)

    def update_ui_after_silence(self):
        self.status_label.config(text="無音検出によって停止")
        self.root.configure(bg='#e6f3ff')
        self.status_label.configure(bg='#e6f3ff')
        self.start_button.configure(text="録音")
        messagebox.showinfo("情報", "無音が10秒以上続いたため録音をキャンセルしました。")

    def stop_recording(self):
        self.logger.info("録音停止処理を実行します")
        self.is_recording = False
        self.status_label.config(text="処理中")
        self.root.configure(bg='#ffb366')
        self.status_label.configure(bg='#ffb366')
        self.recorder.stop_recording()
        self.logger.info("音声処理スレッドを開始します")
        threading.Thread(target=self.process_audio).start()

    def process_audio(self):
        self.logger.info("音声処理を開始します")
        try:
            self.is_processing = True
            self.should_cancel = False
            audio_file = self.recorder.get_audio_file()
            self.logger.debug(f"音声ファイル: {audio_file}")

            # 中断チェック
            if self.should_cancel:
                self.logger.info("処理がキャンセルされました")
                self.status_label.config(text="キャンセルされました")
                self.root.configure(bg='#e6f3ff')
                self.status_label.configure(bg='#e6f3ff')
                self.start_button.configure(text="録音")
                return

            text = self.transcriber.transcribe(audio_file)
            self.logger.debug(f"文字起こし結果: {text}")

            # 中断チェック
            if self.should_cancel:
                self.logger.info("処理がキャンセルされました")
                self.status_label.config(text="キャンセルされました")
                self.root.configure(bg='#e6f3ff')
                self.status_label.configure(bg='#e6f3ff')
                self.start_button.configure(text="録音")
                return

            utils.insert_text_to_active_field(text)
            utils.save_backup(text)
            self.status_label.config(text="待機中")
            self.root.configure(bg='#e6f3ff')
            self.status_label.configure(bg='#e6f3ff')
            self.start_button.configure(text="録音")
            self.logger.info("音声処理が完了しました")
        except Exception as e:
            self.logger.error(f"処理中にエラーが発生しました: {str(e)}", exc_info=True)
            messagebox.showerror("エラー", f"処理中にエラーが発生しました：\n{e}")
            self.status_label.config(text="エラー")
        finally:
            self.is_processing = False
            self.should_cancel = False
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file)
                self.logger.debug("一時音声ファイルを削除しました")

    def cancel_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.recorder.stop_recording()
            self.status_label.config(text="待機中")
            # 背景を薄い青に戻す
            self.root.configure(bg='#e6f3ff')
            self.status_label.configure(bg='#e6f3ff')
            self.start_button.configure(text="録音")
            # 録音ファルを削除
            audio_file = self.recorder.get_audio_file()
            if audio_file is not None and os.path.exists(audio_file):
                os.remove(audio_file)
                self.logger.debug(f"キャンセされた録音ファイルを削除しました: {audio_file}")

    def on_window_move(self, event):
        # ウィンドウの移動が完了しときの処理
        if event.widget == self.root:
            # 新しい位置を取得
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            # 位置が変更された場合のみ保存
            if x != self.window_position['x'] or y != self.window_position['y']:
                self.window_position = {'x': x, 'y': y}
                # 設定をファイルに保存
                self.config['window_position'] = self.window_position
                with open('config.json', 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=4)
                self.logger.debug(f"ウィンドウ位置を保存しました: x={x}, y={y}")

    def check_hotkey_status(self):
        """ホットキーの状態をチェックして表示する"""
        self.logger.info("ホットキーの状態をチェック")
        try:
            # 現在の設定を再確認
            keyboard.unhook_all()
            time.sleep(0.1)
            keyboard.on_press_key(self.hotkey.split('+')[1], self.handle_hotkey)

            # 現在の状態を表示
            status_msg = (
                f"ホットキー '{self.hotkey}' を再設定しました\n"
                f"���在の録音状態: {'録音中' if self.is_recording else '待機中'}"
            )
            messagebox.showinfo("キー状態", status_msg)
            self.logger.info(status_msg)
        except Exception as e:
            error_msg = f"ホットキーエラー: {str(e)}"
            messagebox.showerror("キー状態", error_msg)
            self.logger.error(error_msg)

    def setup_tray(self):
        """トレイアイコンをセットアップ"""
        try:
            # アイコンファイルの絶対パスを取得
            icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'icon.png'))
            self.logger.info(f"アイコンの絶対パス: {icon_path}")
            self.logger.info(f"カレントディレクトリ: {os.getcwd()}")
            self.logger.info(f"アイコンファイルの存在: {os.path.exists(icon_path)}")
            
            self.tray = TrayIcon(self)
            self.tray.setup_tray()
            self.root.deiconify()
            self.root.lift()
        except Exception as e:
            self.logger.error(f"トレイアイコンのセットアップ中にエラー: {str(e)}")

    def start_post_processing(self):
        """テキスト後処理を開始"""
        self.logger.info("テキスト後処理を開始します")
        if not self.is_post_processing:
            self.is_post_processing = True
            self.status_label.config(text="音声指示待ち")
            self.root.configure(bg='#b3e6ff')
            self.status_label.configure(bg='#b3e6ff')
            threading.Thread(target=self.record_post_process_instruction).start()

    def record_post_process_instruction(self):
        """後処理のめの音声指示を録音"""
        try:
            self.recorder.start_recording(self.on_post_process_silence_detected)
        except Exception as e:
            self.logger.error(f"後処理指示の録音中にエラー: {str(e)}")
            self.reset_post_process_state()

    def on_post_process_silence_detected(self):
        """後処理指示の録音が完了したときの処理"""
        self.logger.info("後処理指示の録音が完了しました")
        self.root.after(0, self.process_post_process_instruction)

    def process_post_process_instruction(self):
        """録音した指示を処理してテキストを更新"""
        audio_file = None
        try:
            self.is_processing = True
            self.should_cancel = False
            # 最新のバックアップファイルを取得
            backup_dir = self.config.get('backup_directory', './backups')
            files = [f for f in os.listdir(backup_dir) if f.endswith('_transcription.txt')]
            if not files:
                raise FileNotFoundError("バックアップファイルが見つかりません")

            latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(backup_dir, x)))
            file_path = os.path.join(backup_dir, latest_file)

            # 中断チェック
            if self.should_cancel:
                self.logger.info("処理がキャンセルされました")
                self.status_label.config(text="キャンセルされました")
                self.root.configure(bg='#e6f3ff')
                self.status_label.configure(bg='#e6f3ff')
                return

            # 元のテキストを読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                original_text = f.read()

            # 音声指示をテキストに変換
            audio_file = self.recorder.get_audio_file()
            instruction = self.transcriber.transcribe(audio_file)

            # 中断チェック
            if self.should_cancel:
                self.logger.info("処理がキャンセルされました")
                self.status_label.config(text="キャンセルされました")
                self.root.configure(bg='#e6f3ff')
                self.status_label.configure(bg='#e6f3ff')
                return

            # OpenAI APIで処理
            from Common_OpenAIAPI import generate_chat_response

            prompt = f"以下のテキストを、次の指示に従って編集してください:\n\n指示: {instruction}\n\nテキスト:\n{original_text}"
            processed_text = generate_chat_response("", prompt)

            # 中断チェック
            if self.should_cancel:
                self.logger.info("処理がキャンセルされました")
                self.status_label.config(text="キャンセルされました")
                self.root.configure(bg='#e6f3ff')
                self.status_label.configure(bg='#e6f3ff')
                return

            if processed_text:
                utils.insert_text_to_active_field(processed_text)
                utils.save_backup(processed_text)
                self.logger.info("テキスト後処理が完了しました")
                self.status_label.config(text="待機中")
                self.root.configure(bg='#e6f3ff')
                self.status_label.configure(bg='#e6f3ff')

        except Exception as e:
            self.logger.error(f"後処理中にエラー: {str(e)}")
            messagebox.showerror("エラー", f"後処理中にエラーが発生しました：\n{e}")
        finally:
            self.is_processing = False
            self.should_cancel = False
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file)
            self.reset_post_process_state()

    def reset_post_process_state(self):
        """後処理の状態をリセット"""
        self.is_post_processing = False
        self.status_label.config(text="待機中")
        self.root.configure(bg='#e6f3ff')
        self.status_label.configure(bg='#e6f3ff')

    def cancel_post_processing(self):
        """後処理をキャンセル"""
        self.logger.info("後処理をキャンセルします")
        if self.is_post_processing:
            self.is_post_processing = False
            self.recorder.stop_recording()
            audio_file = self.recorder.get_audio_file()
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file)
            self.status_label.config(text="キャンセルされました")
            self.root.configure(bg='#e6f3ff')
            self.status_label.configure(bg='#e6f3ff')
            self.logger.info("後処理をキャンセルしました")

    def stop_post_processing(self):
        """後処理の録音を停止してOpenAIに送信"""
        self.logger.info("後処理の録音を停止します")
        self.recorder.stop_recording()
        self.status_label.config(text="処理中")
        self.root.configure(bg='#ffb366')
        self.status_label.configure(bg='#ffb366')
        # 音声処理を別スレッドで開始
        threading.Thread(target=self.process_post_process_instruction).start()

    def run(self):
        try:
            # アプリケーション起動時に古いバックアップを削除
            deleted_count = utils.cleanup_old_backups()
            if deleted_count > 0:
                self.logger.info(f"{deleted_count}個の古いバックアップファイルを削除しました")

            # ウィンドウを閉じるボタンの動作を変更
            # self.root.protocol("WM_DELETE_WINDOW", lambda: self.root.withdraw())  # コメントアウト
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"アプリケーション実行中にエラーが発生: {str(e)}", exc_info=True)
        finally:
            # アプリケーション終了時にホットキーを解除
            try:
                keyboard.remove_hotkey(self.hotkey)
                self.logger.info("ホットキーを解除しました")
            except:
                pass
            keyboard.unhook_all()
            self.logger.info("全てのホットキーフックを解除しました")

    def is_already_running(self):
        """既に同じアプリケーションが起動しているかチェック"""
        current_process = psutil.Process()
        current_pid = current_process.pid
        terminated_pid = None
        
        # プロセス名でフィルタリングして、pythonプロセスのみを取得
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                # 自分自身のプロセスはスキップ
                if proc.pid == current_pid:
                    continue
                
                # pythonプロセスのみをチェック
                if 'python' not in proc.name().lower():
                    continue
                
                # cmdlineの取得は、pythonプロセスの場合のみ行う
                cmdline = proc.cmdline()
                if len(cmdline) >= 2 and 'voice_input_app.py' in cmdline[-1]:
                    terminated_pid = proc.pid
                    proc.terminate()
                    break  # 見つかったら即座にループを抜ける
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if terminated_pid:
            # 0.3秒待機して、プロセスが確実に終了したか確認
            time.sleep(0.3)
            try:
                # プロセスが存在するかチェック
                psutil.Process(terminated_pid)
                # まだ存在する場合は強制終了
                psutil.Process(terminated_pid).kill()
                time.sleep(0.1)  # 強制終了後の短い待機
            except psutil.NoSuchProcess:
                pass  # プロセスが既に終了している場合は何もしない
            return True
        
        return False

    def terminate_existing_instance(self):
        """既存のアプリケーションインスタンスを終了"""
        terminated_pid = None
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                # pythonプロセスのみをチェック
                if 'python' not in proc.name().lower():
                    continue
                    
                cmdline = proc.cmdline()
                if len(cmdline) >= 2 and 'voice_input_app.py' in cmdline[-1]:
                    terminated_pid = proc.pid
                    proc.terminate()
                    break  # 見つかったら即座にループを抜ける
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if terminated_pid:
            # 0.3秒待機して、プロセスが確実に終了したか確認
            time.sleep(0.3)
            try:
                # プロセスが存在するかチェック
                psutil.Process(terminated_pid)
                # まだ存在する場合は強制終了
                psutil.Process(terminated_pid).kill()
                time.sleep(0.1)  # 強制終了後の短い待機
            except psutil.NoSuchProcess:
                pass  # プロセスが既に終了している場合は何もしない

    def cancel_processing(self):
        """OpenAI APIへの送信処理をキャンセル"""
        self.logger.info("処理をキャンセルします")
        self.should_cancel = True
        self.status_label.config(text="キャンセル中...")

    def open_latest_backup(self):
        """最新のバックアップファイルを開く"""
        try:
            # バックアップフォルダのパスを取得
            backup_dir = 'backups'
            if not os.path.exists(backup_dir):
                self.logger.warning("バックアップフォルダが存在しません")
                messagebox.showwarning("警告", "バックアップフォルダが存在しません")
                return

            # バックアップフォルダ内のファイルを取得し、最新のものを探す
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('_transcription.txt')]
            if not backup_files:
                self.logger.warning("バックアップファイルが存在しません")
                messagebox.showwarning("警告", "バックアップファイルが存在しません")
                return

            # ファイル名でソートして最新のものを取得
            latest_file = max(backup_files)
            latest_file_path = os.path.join(backup_dir, latest_file)

            # デフォルトのテキストエディタでファイルを開く
            os.startfile(latest_file_path)
            self.logger.info(f"最新のバックアップファイルを開きました: {latest_file}")

        except Exception as e:
            self.logger.error(f"バックアップファイルを開く際にエラーが発生しました: {str(e)}")
            messagebox.showerror("エラー", f"バックアップファイルを開く際にエラーが発生しました：\n{e}")

if __name__ == "__main__":
    socket_instance = prevent_multiple_instances()
    app = VoiceInputApp()
    app.run()