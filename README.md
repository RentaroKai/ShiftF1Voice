# ShiftF1Voice

cursorとか使っているときにボイス入力がしたい！
けどwindowsにはいい感じのボイス入力がなかったので自力で作ってみた

## 使用方法

 C:\Users\<ユーザー名>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
にVoiceInputLauncher.exeへのショートカットを入れておくと1-1をスキップできる
動かないときは　pythonのパスがおかしいかもしれない


1. **起動手順（重要）**
   1. まず、ランチャーを起動します：
      ```
      VoiceInputLauncher.exe　または　ahk
      ```
   2. ランチャーが起動したら、以下のホットキーが使用可能になります：
   (キー割り当てはconfig.jsonで変更可能)
      - `Shift + F1`: 起動と録音開始/停止（録音中はボタンが「文字化」に変化。アプリが未起動の場合は起動になる）
      - `Shift + F2`: キャンセル
      - `Shift + F3`: AI加工（直前の文字起こし結果に音声で指示）
      - `Shift + F4`: 今選んでるウィンドウのテキスト消去

2. **注意事項**
   - 必ずランチャーを先に起動してください
   - ホットキーが効かない場合は、ランチャーが起動しているか確認してください


## 設定
- `config.json`でホットキーなどの設定をカスタマイズ可能
- バックアップは自動的に保存されます

## 機能
- ショートカットキーによる即時録音開始
- 音声認識による文字起こし
- バックアップ機能
- 後処理機能（OpenAI APIによる文章の編集）

## 主な機能

- **Shift-F1キーによる音声入力**: Shift-F1（カスタマイズ可能）を押して録音開始（ボタンが「文字化」に変化）、もう一度押して文字起こし
- **自動テキスト挿入**: 文字起こしされたテキストが現在アクティブなウィンドウに自動挿入
- **AIによる加工指示**: Shift+F3を押すことで、直前の文字起こし結果に対して音声で追加の指示や編集を依頼可能
- **キャンセル機能**: Shift-F2を押すことで、現在の操作をキャンセル
- **テキストバックアップ**: 変換されたテキストの自動バックアップ
- **エラーハンドリング**: 包括的なエラー処理とユーザーへのフィードバック
- **カスタマイズ設定**: 設定ファイルによる柔軟なカスタマイズ

## インストール手順（詳細）

## 事前準備
1. Pythonがインストールされていることを確認（コマンドプロンプトで`python --version`で確認）
2. 必要なライブラリをインストール：
   ```
   pip install -r requirements.txt
   ```

## 起動方法（2つの選択肢）

### 方法1: 実行ファイル（.exe）を使用する場合（推奨）
1. `VoiceInputLauncher.exe`を直接実行します
2. システムトレイにアイコンが表示されていれば起動成功です
3. Shift+F1（またはconfig.jsonで設定したキー）でアプリを起動できます

### 方法2: スタートアップに登録する場合
1. `VoiceInputLauncher.exe`のショートカットを作成
2. ショートカットを以下のフォルダに配置：
   `C:\Users\<ユーザー名>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`
3. PCを再起動すれば、自動的にアプリが起動します

## トラブルシューティング
- アプリが起動しない場合：
  - ログフォルダ内の`startup_debug.log`や`debug.log`を確認
  - config.jsonでホットキーが適切に設定されているか確認（一般的なキーボードでは`F24`などの特殊キーは使えません）
  - ホットキーを`shift+f1`など標準的なキーに変更することをお勧めします

## ファイル構成

- `voice_input_app.py`: メインアプリケーションのエントリーポイント
- `recorder.py`: 音声録音機能を提供
- `transcriber.py`: 音声をテキストに変換する機能を提供
- `utils.py`: ユーティリティ関数とエラーハンドリング
- `config.json`: ショートカットキーやバックアップ先などの設定

## 動作説明

1. **アプリケーションの起動**
   - `voice_input_app.py`を実行するか、実行ファイルを起動します
   - タスクトレイにアイコンが表示されます

2. **音声入力の使用**
   - Shift-F1キーを押してツール立ち上げ
   - Shift-F1キーを押して録音を開始します（ボタンが「文字化」に変化します）
   - 再度Shift-F1キーを押すと録音が停止し、テキストに変換されます
   - 変換されたテキストが自動的にアクティブなウィンドウに挿入されます

3. **追加機能の使用**
   - Shift-F3: 直前の文字起こし結果に対してAIに追加の指示を出せます
   - Shift-F2: 現在の操作をキャンセルします

## エラーハンドリング

- **API通信エラー**
  - 文字起こしの際にエラーが発生した場合、エラーメッセージを表示し、処理を中断します

- **バックアップエラー**
  - テキストの保存時にエラーが発生した場合、エラーメッセージを表示します

## セキュリティとプライバシー

- **APIキーの管理**
  - 環境変数`OPENAI_API_KEY`からAPIキーを取得します

- **音声データの扱い**
  - 処理後、音声ファイルは削除されます

## カスタマイズ

- **設定オプション**
  - `config.json`で以下の設定が可能です：
    - ショートカットキー
    - バックアップ保存先
    - バックアップ保持期間

## 注意点

- **プラットフォーム互換性**
  - 現在はWindows向けに最適化されています
