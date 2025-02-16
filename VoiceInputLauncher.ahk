#Requires AutoHotkey v2.0  ; AHK v2を使用
#SingleInstance Force    ; 多重起動防止

; グローバル変数
global configFile := "config.json"  ; カレントディレクトリのconfig.jsonを使用
global pythonScript := "voice_input_app.py"  ; カレントディレクトリのPythonスクリプトを使用
global iconFile := "icon.ico"  ; カレントディレクトリのアイコンを使用
global pythonProcess := 0  ; Pythonプロセスの管理用
global isRunning := false  ; 実行状態の管理
global isProcessingHotkey := false  ; ホットキー処理中フラグ
global config := Map()  ; 設定を保持するグローバル変数
global isDebug := false  ; デバッグモードをfalseに変更

; デバッグ用の時間計測関数
GetTime() {
    return DllCall("GetTickCount64")
}

LogTime(message, startTime) {
    current := GetTime()
    elapsed := current - startTime
    FileAppend Format("{1}: {2}ms`n", message, elapsed), "startup_debug.log", "UTF-8"
    return current
}

; デバッグ用：起動時間計測の開始
startTime := GetTime()
currentTime := startTime
FileAppend Format("アプリケーション起動開始: {1}`n", A_Now), "startup_debug.log", "UTF-8"

; 必須ファイルの存在チェック
currentTime := LogTime("ファイルチェック開始", startTime)
if (!FileExist(configFile)) {
    MsgBox("必要な設定ファイルが見つかりません: " configFile)
    ExitApp()
}

if (!FileExist(pythonScript)) {
    MsgBox("必要なPythonスクリプトが見つかりません: " pythonScript)
    ExitApp()
}
currentTime := LogTime("ファイルチェック完了", startTime)

; 設定の読み込み
currentTime := LogTime("設定読み込み開始", startTime)
LoadConfig()
currentTime := LogTime("設定読み込み完了", startTime)

; システムトレイの設定
currentTime := LogTime("トレイメニュー初期化開始", startTime)
InitializeTrayMenu()
currentTime := LogTime("トレイメニュー初期化完了", startTime)

; システムトレイの初期化関数
InitializeTrayMenu() {
    if FileExist(iconFile) {
        TraySetIcon(iconFile)
    }
    A_TrayMenu.Delete()
    A_TrayMenu.Add("音声入力ツール 起動/停止", MenuToggleVoiceInput)
    A_TrayMenu.Add()
    A_TrayMenu.Add("終了", ExitHandler)
}

; 設定ファイルを読み込む関数
LoadConfig() {
    try {
        configStartTime := GetTime()
        currentTime := configStartTime
        LogTime("LoadConfig開始", configStartTime)
        
        if (isDebug) {
            FileAppend "設定ファイル読み込み開始`n", "startup_debug.log", "UTF-8"
        }
        
        ; ファイル読み込みを一度だけ実行
        fileContent := FileRead(configFile)
        currentTime := LogTime("ファイル読み込み完了", configStartTime)
        
        ; JSONの解析を一括で実行
        currentTime := LogTime("JSON解析開始", configStartTime)
        
        ; 全てのホットキーを一度に検索
        pattern := '"(hotkey|cancel_hotkey|post_process_hotkey|clear_hotkey)"\s*:\s*"shift\+f(\d+)"'
        pos := 1
        while (RegExMatch(fileContent, pattern, &match, pos)) {
            key := match[1]
            value := "+" . "F" . match[2]
            config[key] := value
            pos := match.Pos + match.Len
        }
        
        currentTime := LogTime("JSON解析完了", configStartTime)
        
        ; ホットキーの設定を一括で実行
        currentTime := LogTime("ホットキー設定開始", configStartTime)
        SetupHotkeys(config)
        currentTime := LogTime("ホットキー設定完了", configStartTime)
        
        if (isDebug) {
            LogTime("LoadConfig完了", configStartTime)
        }
    }
    catch Error as err {
        FileAppend Format("LoadConfigでエラー発生: {1}`n", err.Message), "startup_debug.log", "UTF-8"
        ExitApp()
    }
}

; ホットキーを設定する関数
SetupHotkeys(config) {
    try {
        ; ホットキーと対応する関数のマッピング
        hotkeyMap := Map(
            "hotkey", HandleMainHotkey,
            "cancel_hotkey", CancelVoiceInput,
            "post_process_hotkey", PostProcessVoiceInput,
            "clear_hotkey", ClearText
        )
        
        ; 一括でホットキーを設定
        for key, func in hotkeyMap {
            if (config.Has(key) && config[key]) {
                Hotkey config[key], func
            }
        }
    }
    catch Error as err {
        FileAppend Format("ホットキー設定エラー: {1}`n", err.Message), "startup_debug.log", "UTF-8"
    }
}

; メインホットキーのハンドラー
HandleMainHotkey(*) {
    global isProcessingHotkey, config, isRunning
    FileAppend "HandleMainHotkey が呼び出されました`n", "debug.log"
    
    if (isProcessingHotkey) {
        FileAppend "既に処理中のため、無視します`n", "debug.log"
        return  ; 処理中なら何もしない
    }
    
    FileAppend "現在の状態: isRunning = " isRunning "`n", "debug.log"
    
    isProcessingHotkey := true
    if (!isRunning) {
        FileAppend "StartVoiceInput を呼び出します`n", "debug.log"
        StartVoiceInput()
    } else {
        FileAppend "アプリケーション実行中のホットキー処理`n", "debug.log"
        
        try {
            mainHotkey := config["hotkey"]
            FileAppend "ホットキー設定: " mainHotkey "`n", "debug.log"
            
            ; ホットキーを一時的に無効化
            Hotkey mainHotkey, "Off"
            
            ; キーを送信せずに、Python側にメッセージを送る方法を検討
            ; 現在は一時的に無効化のみ行う
            
            ; 100ミリ秒後にホットキーを再有効化
            SetTimer () => Hotkey(mainHotkey, "On"), -100
            FileAppend "ホットキーの再有効化をスケジュール`n", "debug.log"
        }
        catch Error as err {
            FileAppend "エラーが発生しました: " err.Message "`n", "debug.log"
        }
    }
    Sleep 50  ; 処理完了まで待機時間を短縮
    isProcessingHotkey := false
    FileAppend "HandleMainHotkey の処理が完了しました`n", "debug.log"
}

; 音声入力の開始
StartVoiceInput() {
    global pythonProcess, isRunning, pythonScript
    try {
        runCmd := "python `"" pythonScript "`""
        Run runCmd,, "Hide", &processId
        if (processId) {
            pythonProcess := processId
            isRunning := true
            UpdateTrayIcon(true)
            SetTimer CheckProcessInactive, 0
            SetTimer CheckProcess, 1000
        }
    }
    catch Error as err {
        FileAppend Format("StartVoiceInputでエラー発生: {1}`n", err.Message), "startup_debug.log", "UTF-8"
    }
}

; 音声入力の停止
StopVoiceInput() {
    global pythonProcess, isRunning
    try {
        if (pythonProcess) {
            ProcessClose(pythonProcess)
            pythonProcess := 0
            isRunning := false
            UpdateTrayIcon(false)
            SetTimer CheckProcess, 0
        }
    }
    catch Error as err {
    }
}

; プロセスの状態を監視
CheckProcess() {
    global pythonProcess, isRunning
    if (!ProcessExist(pythonProcess)) {
        pythonProcess := 0
        isRunning := false
        UpdateTrayIcon(false)
        SetTimer CheckProcess, 0
        SetTimer CheckProcessInactive, 20000
    }
}

; 非アクティブ時のプロセス監視（低頻度）
CheckProcessInactive() {
    global pythonProcess, isRunning
    if (ProcessExist(pythonProcess)) {
        isRunning := true
        UpdateTrayIcon(true)
        SetTimer CheckProcessInactive, 0  ; 低頻度チェックを停止
        SetTimer CheckProcess, 1000  ; 通常の監視を開始
    }
}

; プロセス状態の確認（デバッグ用）
CheckProcessStatus(*) {
    global pythonProcess, isRunning, isDebug
    if (isRunning) {
        MsgBox("プロセス実行中`nPID: " pythonProcess)
    } else {
        MsgBox("プロセス停止中")
    }
}

; トレイアイコンの更新
UpdateTrayIcon(running) {
    global iconFile
    if (running) {
        TraySetIcon(iconFile)  ; アクティブ時のアイコン
        A_TrayMenu.Rename("音声入力ツール 起動/停止", "音声入力ツール 停止")
    } else {
        TraySetIcon(iconFile)  ; 非アクティブ時のアイコン
        A_TrayMenu.Rename("音声入力ツール 停止", "音声入力ツール 起動/停止")
    }
}

; 音声入力のキャンセル
CancelVoiceInput(*) {
    if (isRunning) {
        ; TODO: キャンセル処理を実装
        ; MsgBox("音声入力のキャンセル")
    }
}

; 後処理の開始
PostProcessVoiceInput(*) {
    if (isRunning) {
        ; TODO: 後処理の実装
        ; MsgBox("後処理の開始")
    }
}

; テキストのクリア
ClearText(*) {
    if (isRunning) {
        ; TODO: テキストクリア処理の実装
        ; MsgBox("テキストのクリア")
    }
}

; アプリケーション終了時の処理
ExitHandler(*) {
    if (isRunning) {
        if (isDebug) {
            ; MsgBox("終了処理を開始します`nプロセスID: " pythonProcess)
        }
        StopVoiceInput()
    }
    ExitApp()
}

; メニューからの音声入力切り替え
MenuToggleVoiceInput(*) {
    if (!isRunning) {
        StartVoiceInput()
    } else {
        StopVoiceInput()
    }
} 