import os
import sys
import streamlit.web.cli as stcli

def main():
    # 1. コンソール非表示(--windowed)時のサイレントクラッシュ対策
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

    # 2. exe化された環境での一時フォルダ（_MEIPASS）のパスを解決
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    # 実行するStreamlitアプリ（app.py）のフルパスを設定
    app_path = os.path.join(base_path, "app.py")
    
    # 3. Streamlitの起動コマンドを擬似的に設定
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.headless=false", # ブラウザを自動で開く
        "--server.port=8501",
        "--global.developmentMode=false"
    ]
    
    # Streamlitサーバーを起動
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()