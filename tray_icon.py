import threading
import pystray
from PIL import Image
import os

class TrayIcon:
    def __init__(self, app):
        self.app = app
        # アイコンのパスを絶対パスで取得
        self.icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'icon.png'))

    def setup_tray(self):
        try:
            # アイコンの存在確認とログ出力
            self.app.logger.info(f"TrayIcon: アイコンパス: {self.icon_path}")
            self.app.logger.info(f"TrayIcon: アイコンファイルの存在: {os.path.exists(self.icon_path)}")
            
            # アイコンの読み込み
            image = Image.open(self.icon_path)
            icon = pystray.Icon(
                "name",
                image,
                "Voice Input",
                menu=self.create_menu()
            )
            threading.Thread(target=icon.run, daemon=True).start()
            
        except Exception as e:
            self.app.logger.error(f"TrayIcon: アイコンの設定中にエラー: {str(e)}")

    def create_menu(self):
        menu = pystray.Menu(
            pystray.MenuItem("表示/非表示", self.toggle_window),
            pystray.MenuItem("終了", self.quit_app)
        )
        return menu

    def toggle_window(self, icon, item):
        if self.app.root.winfo_viewable():
            self.app.root.withdraw()  # ウィンドウを非表示
        else:
            self.app.root.deiconify()  # ウィンドウを表示
            self.app.root.lift()  # 最前面に表示

    def quit_app(self, icon, item):
        icon.stop()
        self.app.root.quit()