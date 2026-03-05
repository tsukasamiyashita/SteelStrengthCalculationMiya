import os
import sys
import pathlib
import subprocess
import multiprocessing
import streamlit.web.cli as stcli

PORT = 8501

def main():
    # exe化時のマルチプロセスを安全に行うための記述
    multiprocessing.freeze_support()
    
    # 1. コンソール非表示(--windowed)時のサイレントクラッシュ対策
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

    # 2. Streamlitの設定ファイル作成（エラー防止）
    streamlit_dir = pathlib.Path.home() / ".streamlit"
    streamlit_dir.mkdir(exist_ok=True)
    credentials_file = streamlit_dir / "credentials.toml"
    if not credentials_file.exists():
        credentials_file.write_text('[general]\nemail = ""\n')

    # 3. 前回ブラウザの「×」で閉じて残ってしまったプロセスを強制終了して綺麗にする
    try:
        output = subprocess.check_output("netstat -ano", shell=True).decode()
        for line in output.strip().split('\n'):
            # PORTを使用中で、かつLISTENING状態のものを探す
            if f":{PORT}" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                # 今動かそうとしている自分自身のプロセスでなければ強制終了
                if str(os.getpid()) != pid:
                    subprocess.call(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 4. exe化された環境での一時フォルダ（_MEIPASS）のパスを解決
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        os.chdir(sys._MEIPASS)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    # 実行するStreamlitアプリ（app.py）のフルパスを設定
    app_path = os.path.join(base_path, "app.py")
    
    # 5. Streamlitの起動コマンドを擬似的に設定
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        f"--server.port={PORT}",
        "--server.headless=false",
        "--browser.gatherUsageStats=false",
        "--server.address=127.0.0.1",
        "--global.developmentMode=false"
    ]
    
    # Streamlitサーバーを起動
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()