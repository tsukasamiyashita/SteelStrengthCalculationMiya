import os
import sys
import math
import subprocess
import pathlib
import multiprocessing

# バージョン情報
APP_VERSION = "v1.1.0"
PORT = 8501  # Streamlitが使用するポート番号

# ==========================================
# 【重要】起動・プロセス管理 (ブラウザの×ボタン対策)
# ==========================================
# Streamlitが裏で実行中かどうかのフラグを確認します
if __name__ == "__main__" and os.environ.get("STREAMLIT_APP_RUNNING") != "1":
    # exe化時のマルチプロセス（子プロセス生成）を安全に行うための記述
    multiprocessing.freeze_support()
    
    # Streamlitの設定ファイル作成（エラー防止）
    streamlit_dir = pathlib.Path.home() / ".streamlit"
    streamlit_dir.mkdir(exist_ok=True)
    credentials_file = streamlit_dir / "credentials.toml"
    if not credentials_file.exists():
        credentials_file.write_text('[general]\nemail = ""\n')

    # ▼ 前回のゾンビプロセス（閉じ残し）をキルする処理 ▼
    try:
        # Windowsのコマンドを使い、指定ポートを使用中のプロセスを探す
        output = subprocess.check_output(f"netstat -ano | findstr :{PORT}", shell=True).decode()
        for line in output.strip().split('\n'):
            if "LISTENING" in line:
                pid = line.strip().split()[-1]
                # 自分自身でなければ、古いプロセスを強制終了してポートを解放する
                if str(os.getpid()) != pid:
                    subprocess.call(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass  # プロセスが見つからない場合はそのまま進む

    # このプロセスがStreamlitを起動する親になるためのフラグを設定
    os.environ["STREAMLIT_APP_RUNNING"] = "1"

    # ▼ Streamlitの起動処理 ▼
    import streamlit.web.cli as stcli
    if getattr(sys, 'frozen', False):
        # exeとして実行された場合
        os.chdir(sys._MEIPASS)
        sys.argv = [
            "streamlit", "run", "app.py",
            f"--server.port={PORT}",
            "--server.headless=false",
            "--browser.gatherUsageStats=false",
            "--server.address=127.0.0.1",
            "--global.developmentMode=false"
        ]
    else:
        # Pythonスクリプトとして実行された場合
        sys.argv = [
            "streamlit", "run", "app.py",
            f"--server.port={PORT}",
            "--server.headless=false",
            "--server.address=127.0.0.1"
        ]
    
    sys.exit(stcli.main())

# ==========================================
# ここから下は Streamlit の UI・メインロジック
# ==========================================
import streamlit as st

def get_readme_text():
    """readme.mdを読み込む関数"""
    try:
        if getattr(sys, 'frozen', False):
            readme_path = os.path.join(sys._MEIPASS, "readme.md")
        else:
            readme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "readme.md")
            
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return "readme.md が見つかりません。コンパイル時に含まれているか確認してください。"
    except Exception as e:
        return f"読み込みエラー: {e}"

# ==========================================
# データベース・物性値定義
# ==========================================
# 【1. 鋼材】
MATERIAL_PROPS = {
    "E": 205000,    # 縦弾性係数 (N/mm2)
    "Yield": 235,   # 降伏点 (N/mm2)
    "Tensile": 400, # 引張強さ (N/mm2)
    "Density": 7.85 # 密度 (g/cm3)
}

STEEL_DB = {
    "H鋼": {
        "100 x 50 x 5 x 7": {"H": 100, "B": 50, "t1": 5, "t2": 7},
        "100 x 100 x 6 x 8": {"H": 100, "B": 100, "t1": 6, "t2": 8},
        "125 x 60 x 6 x 8": {"H": 125, "B": 60, "t1": 6, "t2": 8},
        "125 x 125 x 6.5 x 9": {"H": 125, "B": 125, "t1": 6.5, "t2": 9},
        "150 x 75 x 5 x 7": {"H": 150, "B": 75, "t1": 5, "t2": 7},
        "150 x 150 x 7 x 10": {"H": 150, "B": 150, "t1": 7, "t2": 10},
        "175 x 90 x 5 x 8": {"H": 175, "B": 90, "t1": 5, "t2": 8},
        "175 x 175 x 7.5 x 11": {"H": 175, "B": 175, "t1": 7.5, "t2": 11},
        "200 x 100 x 5.5 x 8": {"H": 200, "B": 100, "t1": 5.5, "t2": 8},
        "200 x 150 x 6 x 9": {"H": 200, "B": 150, "t1": 6, "t2": 9},
        "200 x 200 x 8 x 12": {"H": 200, "B": 200, "t1": 8, "t2": 12},
        "250 x 125 x 6 x 9": {"H": 250, "B": 125, "t1": 6, "t2": 9},
        "250 x 250 x 9 x 14": {"H": 250, "B": 250, "t1": 9, "t2": 14},
        "300 x 150 x 6.5 x 9": {"H": 300, "B": 150, "t1": 6.5, "t2": 9},
        "300 x 300 x 10 x 15": {"H": 300, "B": 300, "t1": 10, "t2": 15},
    },
    "I形鋼 (Iビーム)": {
        "100 x 75 x 5 x 8": {"H": 100, "B": 75, "t1": 5, "t2": 8},
        "125 x 75 x 5.5 x 9.5": {"H": 125, "B": 75, "t1": 5.5, "t2": 9.5},
        "150 x 75 x 5.5 x 9.5": {"H": 150, "B": 75, "t1": 5.5, "t2": 9.5},
        "150 x 125 x 8.5 x 14": {"H": 150, "B": 125, "t1": 8.5, "t2": 14},
        "200 x 100 x 7 x 10": {"H": 200, "B": 100, "t1": 7, "t2": 10},
        "200 x 150 x 9 x 16": {"H": 200, "B": 150, "t1": 9, "t2": 16},
        "250 x 125 x 7.5 x 12.5": {"H": 250, "B": 125, "t1": 7.5, "t2": 12.5},
        "300 x 150 x 8 x 13": {"H": 300, "B": 150, "t1": 8, "t2": 13},
    },
    "チャンネル": {
        "75 x 40 x 5 x 7": {"H": 75, "B": 40, "t1": 5, "t2": 7},
        "100 x 50 x 5 x 7.5": {"H": 100, "B": 50, "t1": 5, "t2": 7.5},
        "125 x 65 x 6 x 8": {"H": 125, "B": 65, "t1": 6, "t2": 8},
        "150 x 75 x 5.5 x 9.5": {"H": 150, "B": 75, "t1": 5.5, "t2": 9.5},
        "150 x 75 x 6.5 x 10": {"H": 150, "B": 75, "t1": 6.5, "t2": 10},
        "200 x 80 x 7.5 x 11": {"H": 200, "B": 80, "t1": 7.5, "t2": 11},
        "200 x 90 x 8 x 13.5": {"H": 200, "B": 90, "t1": 8, "t2": 13.5},
        "250 x 90 x 9 x 13": {"H": 250, "B": 90, "t1": 9, "t2": 13},
        "300 x 90 x 9 x 13": {"H": 300, "B": 90, "t1": 9, "t2": 13},
    },
    "リップみぞ形鋼 (C型鋼)": {
        "60 x 30 x 10 x 1.6": {"H": 60, "B": 30, "C": 10, "t": 1.6},
        "60 x 30 x 10 x 2.3": {"H": 60, "B": 30, "C": 10, "t": 2.3},
        "75 x 45 x 15 x 1.6": {"H": 75, "B": 45, "C": 15, "t": 1.6},
        "75 x 45 x 15 x 2.3": {"H": 75, "B": 45, "C": 15, "t": 2.3},
        "100 x 50 x 20 x 1.6": {"H": 100, "B": 50, "C": 20, "t": 1.6},
        "100 x 50 x 20 x 2.3": {"H": 100, "B": 50, "C": 20, "t": 2.3},
        "100 x 50 x 20 x 3.2": {"H": 100, "B": 50, "C": 20, "t": 3.2},
        "125 x 50 x 20 x 2.3": {"H": 125, "B": 50, "C": 20, "t": 2.3},
        "125 x 50 x 20 x 3.2": {"H": 125, "B": 50, "C": 20, "t": 3.2},
        "150 x 50 x 20 x 2.3": {"H": 150, "B": 50, "C": 20, "t": 2.3},
        "150 x 50 x 20 x 3.2": {"H": 150, "B": 50, "C": 20, "t": 3.2},
    },
    "T形鋼": {
        "50 x 50 x 6 x 6": {"H": 50, "B": 50, "t1": 6, "t2": 6},
        "75 x 75 x 6 x 6": {"H": 75, "B": 75, "t1": 6, "t2": 6},
        "100 x 100 x 6 x 8": {"H": 100, "B": 100, "t1": 6, "t2": 8},
        "100 x 100 x 8 x 8": {"H": 100, "B": 100, "t1": 8, "t2": 8},
        "125 x 125 x 6 x 9": {"H": 125, "B": 125, "t1": 6, "t2": 9},
        "150 x 150 x 7 x 10": {"H": 150, "B": 150, "t1": 7, "t2": 10},
    },
    "等辺アングル": {
        "20 x 20 x 3": {"L": 20, "t": 3},
        "25 x 25 x 3": {"L": 25, "t": 3},
        "30 x 30 x 3": {"L": 30, "t": 3},
        "40 x 40 x 3": {"L": 40, "t": 3},
        "40 x 40 x 5": {"L": 40, "t": 5},
        "50 x 50 x 4": {"L": 50, "t": 4},
        "50 x 50 x 6": {"L": 50, "t": 6},
        "65 x 65 x 6": {"L": 65, "t": 6},
        "75 x 75 x 6": {"L": 75, "t": 6},
        "75 x 75 x 9": {"L": 75, "t": 9},
        "90 x 90 x 9": {"L": 90, "t": 9},
        "100 x 100 x 10": {"L": 100, "t": 10},
        "130 x 130 x 12": {"L": 130, "t": 12},
        "150 x 150 x 12": {"L": 150, "t": 12},
    },
    "不等辺アングル": {
        "75 x 50 x 6": {"H": 75, "B": 50, "t": 6},
        "90 x 75 x 9": {"H": 90, "B": 75, "t": 9},
        "100 x 75 x 7": {"H": 100, "B": 75, "t": 7},
        "100 x 75 x 10": {"H": 100, "B": 75, "t": 10},
        "125 x 75 x 7": {"H": 125, "B": 75, "t": 7},
        "125 x 90 x 10": {"H": 125, "B": 90, "t": 10},
        "150 x 90 x 9": {"H": 150, "B": 90, "t": 9},
        "150 x 90 x 12": {"H": 150, "B": 90, "t": 12},
    },
    "フラットバー": {
        "25 x 3": {"B": 25, "t": 3},
        "25 x 6": {"B": 25, "t": 6},
        "32 x 6": {"B": 32, "t": 6},
        "38 x 6": {"B": 38, "t": 6},
        "50 x 6": {"B": 50, "t": 6},
        "50 x 9": {"B": 50, "t": 9},
        "65 x 9": {"B": 65, "t": 9},
        "75 x 9": {"B": 75, "t": 9},
        "100 x 9": {"B": 100, "t": 9},
        "100 x 12": {"B": 100, "t": 12},
        "150 x 12": {"B": 150, "t": 12},
    },
    "四角棒": {
        "9 x 9": {"H": 9, "B": 9},
        "12 x 12": {"H": 12, "B": 12},
        "16 x 16": {"H": 16, "B": 16},
        "19 x 19": {"H": 19, "B": 19},
        "25 x 25": {"H": 25, "B": 25},
        "32 x 32": {"H": 32, "B": 32},
        "50 x 50": {"H": 50, "B": 50},
    },
    "角パイプ": {
        "50 x 50 x 1.6": {"H": 50, "B": 50, "t": 1.6},
        "50 x 50 x 2.3": {"H": 50, "B": 50, "t": 2.3},
        "60 x 60 x 2.3": {"H": 60, "B": 60, "t": 2.3},
        "75 x 75 x 3.2": {"H": 75, "B": 75, "t": 3.2},
        "100 x 100 x 3.2": {"H": 100, "B": 100, "t": 3.2},
        "100 x 100 x 4.5": {"H": 100, "B": 100, "t": 4.5},
        "125 x 125 x 3.2": {"H": 125, "B": 125, "t": 3.2},
        "150 x 150 x 4.5": {"H": 150, "B": 150, "t": 4.5},
        "200 x 200 x 6.0": {"H": 200, "B": 200, "t": 6.0},
    },
    "丸パイプ": {
        "21.7 x 2.8 (15A)": {"D": 21.7, "t": 2.8},
        "27.2 x 2.8 (20A)": {"D": 27.2, "t": 2.8},
        "34.0 x 3.2 (25A)": {"D": 34.0, "t": 3.2},
        "42.7 x 3.5 (32A)": {"D": 42.7, "t": 3.5},
        "48.6 x 2.3 (単管)": {"D": 48.6, "t": 2.3},
        "48.6 x 3.5 (40A)": {"D": 48.6, "t": 3.5},
        "60.5 x 3.8 (50A)": {"D": 60.5, "t": 3.8},
        "76.3 x 4.2 (65A)": {"D": 76.3, "t": 4.2},
        "89.1 x 4.2 (80A)": {"D": 89.1, "t": 4.2},
        "101.6 x 4.2 (90A)": {"D": 101.6, "t": 4.2},
        "114.3 x 4.5 (100A)": {"D": 114.3, "t": 4.5},
    },
    "丸棒": {
        "Φ 9": {"D": 9}, "Φ 13": {"D": 13}, "Φ 16": {"D": 16}, "Φ 19": {"D": 19},
        "Φ 22": {"D": 22}, "Φ 25": {"D": 25}, "Φ 32": {"D": 32}, "Φ 38": {"D": 38},
        "Φ 50": {"D": 50},
    },
    "六角棒": {
        "二面幅 10": {"B": 10}, "二面幅 12": {"B": 12}, "二面幅 14": {"B": 14},
        "二面幅 17": {"B": 17}, "二面幅 19": {"B": 19}, "二面幅 21": {"B": 21},
        "二面幅 24": {"B": 24}, "二面幅 27": {"B": 27}, "二面幅 30": {"B": 30},
        "二面幅 36": {"B": 36},
    }
}

# 【2. ボルト】（メートル並目ねじの有効断面積と強度区分）
BOLT_SIZES = {
    "M6": 20.1, "M8": 36.6, "M10": 58.0, "M12": 84.3, "M14": 115.0, 
    "M16": 157.0, "M18": 192.0, "M20": 245.0, "M22": 303.0, "M24": 353.0, 
    "M27": 459.0, "M30": 561.0, "M33": 694.0, "M36": 817.0
}
BOLT_CLASSES = {
    "4.6": {"Yield": 240, "Tensile": 400},
    "4.8": {"Yield": 320, "Tensile": 400},
    "8.8": {"Yield": 640, "Tensile": 800},
    "10.9": {"Yield": 900, "Tensile": 1000},
    "12.9": {"Yield": 1080, "Tensile": 1200}
}

# 【3. ワイヤーロープ】（JIS G 3525代表値：破断荷重 kN）
WIRE_DB = {
    "6×24 A種 (裸)": {
        "6mm": 19.3, "8mm": 34.3, "9mm": 43.4, "10mm": 53.6, "12mm": 77.1, 
        "14mm": 105.0, "16mm": 137.0, "18mm": 174.0, "20mm": 214.0, "22mm": 259.0, "24mm": 309.0
    },
    "6×37 A種 (裸)": {
        "8mm": 33.0, "9mm": 41.8, "10mm": 51.6, "12mm": 74.3, "14mm": 101.0,
        "16mm": 132.0, "18mm": 167.0, "20mm": 206.0, "22mm": 250.0, "24mm": 297.0
    }
}

# ==========================================
# 関数: 鋼材断面計算
# ==========================================
def calculate_section(calc_shape, params, axis="強軸 (X軸回り)"):
    """断面性能を計算する関数"""
    A = I = Z = w = 0.0
    
    if calc_shape in ["H鋼", "I形鋼 (Iビーム)"]:
        H = params.get('H', 100.0)
        B = params.get('B', 100.0)
        t1 = params.get('t1', 6.0)
        t2 = params.get('t2', 8.0)
        A = (B * H) - (B - t1) * (H - 2 * t2)
        if axis == "強軸 (X軸回り)":
            I = (B * H**3 / 12) - ((B - t1) * (H - 2 * t2)**3 / 12)
            if H > 0: Z = I / (H / 2)
        else:
            I = 2 * (t2 * B**3 / 12) + ((H - 2 * t2) * t1**3 / 12)
            if B > 0: Z = I / (B / 2)

    elif calc_shape == "チャンネル":
        H = params.get('H', 100.0)
        B = params.get('B', 100.0)
        t1 = params.get('t1', 6.0)
        t2 = params.get('t2', 8.0)
        A = (B * H) - (B - t1) * (H - 2 * t2)
        if axis == "強軸 (X軸回り)":
            I = (B * H**3 / 12) - ((B - t1) * (H - 2 * t2)**3 / 12)
            if H > 0: Z = I / (H / 2)
        else:
            if A > 0:
                Cx = (2 * (t2 * B * (B / 2)) + (H - 2 * t2) * t1 * (t1 / 2)) / A
                I = 2 * ((t2 * B**3 / 12) + (t2 * B) * (B / 2 - Cx)**2) + \
                    ((H - 2 * t2) * t1**3 / 12) + ((H - 2 * t2) * t1) * (Cx - t1 / 2)**2
                max_x = max(Cx, B - Cx)
                if max_x > 0: Z = I / max_x
            
    elif calc_shape == "リップみぞ形鋼 (C型鋼)":
        H = params.get('H', 100.0)
        B = params.get('B', 50.0)
        C = params.get('C', 20.0)
        t = params.get('t', 2.3)
        A = (H + 2 * B + 2 * C - 4 * t) * t
        if axis == "強軸 (X軸回り)":
            I = (B * H**3 / 12) - ((B - t) * (H - 2 * t)**3 / 12) - (t * (H - 2 * t - 2 * C)**3 / 12)
            if H > 0: Z = I / (H / 2)
        else:
            if A > 0:
                Cx = ((H - 2 * t) * t * (t / 2) + 2 * (B * t * (B / 2)) + 2 * (C * t * (B - t / 2))) / A
                I_web = (H - 2 * t) * t**3 / 12 + (H - 2 * t) * t * (Cx - t / 2)**2
                I_flange = 2 * ((t * B**3 / 12) + B * t * (B / 2 - Cx)**2)
                I_lip = 2 * ((C * t**3 / 12) + C * t * (B - t / 2 - Cx)**2)
                I = I_web + I_flange + I_lip
                max_x = max(Cx, B - Cx)
                if max_x > 0: Z = I / max_x

    elif calc_shape == "T形鋼":
        H = params.get('H', 100.0)
        B = params.get('B', 100.0)
        t1 = params.get('t1', 6.0)
        t2 = params.get('t2', 8.0)
        A = B * t2 + (H - t2) * t1
        if axis == "強軸 (X軸回り)":
            if A > 0:
                Cy = (B * t2 * (t2 / 2) + t1 * (H - t2) * (t2 + (H - t2) / 2)) / A
                I = (B * t2**3 / 12 + B * t2 * (Cy - t2 / 2)**2) + (t1 * (H - t2)**3 / 12 + t1 * (H - t2) * (t2 + (H - t2) / 2 - Cy)**2)
                max_y = max(Cy, H - Cy)
                if max_y > 0: Z = I / max_y
        else:
            I = (t2 * B**3 / 12) + ((H - t2) * t1**3 / 12)
            if B > 0: Z = I / (B / 2)

    elif calc_shape == "等辺アングル":
        L = params.get('L', 50.0)
        t = params.get('t', 5.0)
        A = (2 * L - t) * t
        if A > 0:
            Cy = (L * t * (t / 2) + (L - t) * t * (t + (L - t) / 2)) / A
            I = (L * t**3 / 12 + L * t * (Cy - t / 2)**2) + (t * (L - t)**3 / 12 + t * (L - t) * (L / 2 + t / 2 - Cy)**2)
            max_y = max(Cy, L - Cy)
            if max_y > 0: Z = I / max_y
            
    elif calc_shape == "不等辺アングル":
        H = params.get('H', 75.0)
        B = params.get('B', 50.0)
        t = params.get('t', 6.0)
        A = (H + B - t) * t
        if A > 0:
            if axis == "強軸 (X軸回り)":
                Cy = (B * t * (t / 2) + (H - t) * t * (t + (H - t) / 2)) / A
                I = (B * t**3 / 12 + B * t * (Cy - t / 2)**2) + (t * (H - t)**3 / 12 + t * (H - t) * (H / 2 + t / 2 - Cy)**2)
                max_y = max(Cy, H - Cy)
                if max_y > 0: Z = I / max_y
            else:
                Cx = (H * t * (t / 2) + (B - t) * t * (t + (B - t) / 2)) / A
                I = (H * t**3 / 12 + H * t * (Cx - t / 2)**2) + (t * (B - t)**3 / 12 + t * (B - t) * (B / 2 + t / 2 - Cx)**2)
                max_x = max(Cx, B - Cx)
                if max_x > 0: Z = I / max_x

    elif calc_shape == "フラットバー":
        B = params.get('B', 50.0)
        t = params.get('t', 6.0)
        A = B * t
        if axis == "強軸 (X軸回り)":
            I = (t * B**3) / 12
            if B > 0: Z = I / (B / 2)
        else:
            I = (B * t**3) / 12
            if t > 0: Z = I / (t / 2)

    elif calc_shape == "四角棒":
        H = params.get('H', 50.0)
        B = params.get('B', 50.0)
        A = B * H
        if axis == "強軸 (X軸回り)":
            I = (B * H**3) / 12
            if H > 0: Z = I / (H / 2)
        else:
            I = (H * B**3) / 12
            if B > 0: Z = I / (B / 2)

    elif calc_shape == "角パイプ":
        H = params.get('H', 100.0)
        B = params.get('B', 100.0)
        t = params.get('t', 3.2)
        A = (B * H) - ((B - 2 * t) * (H - 2 * t))
        if axis == "強軸 (X軸回り)":
            I = (B * H**3 / 12) - ((B - 2 * t) * (H - 2 * t)**3 / 12)
            if H > 0: Z = I / (H / 2)
        else:
            I = (H * B**3 / 12) - ((H - 2 * t) * (B - 2 * t)**3 / 12)
            if B > 0: Z = I / (B / 2)

    elif calc_shape == "丸パイプ":
        D = params.get('D', 100.0)
        t = params.get('t', 3.2)
        A = (math.pi / 4) * (D**2 - (D - 2 * t)**2)
        I = (math.pi / 64) * (D**4 - (D - 2 * t)**4)
        if D > 0: Z = I / (D / 2)

    elif calc_shape == "丸棒":
        D = params.get('D', 50.0)
        A = (math.pi * D**2) / 4
        I = (math.pi * D**4) / 64
        if D > 0: Z = I / (D / 2)
            
    elif calc_shape == "六角棒":
        B = params.get('B', 50.0)
        A = 0.866025 * B**2
        I = 0.06013 * B**4
        if B > 0: Z = 0.10825 * B**3

    w = A * MATERIAL_PROPS["Density"] / 1000
    return A, I, Z, w


# ==========================================
# UI 構築 (メイン処理)
# ==========================================
def main():
    st.set_page_config(
        page_title="SteelStrengthCalculationMiya", 
        layout="wide",
        menu_items={
            'About': f"### 🏗️ SteelStrengthCalculationMiya\n**バージョン:** {APP_VERSION}\n\n鋼材・ボルト・ワイヤーロープの強度を計算するアプリケーションです。"
        }
    )

    st.title("🏗️ SteelStrengthCalculationMiya")

    # --- サイドバー：計算モード切替 ---
    st.sidebar.header("🔄 計算モード切替")
    calc_mode = st.sidebar.radio(
        "対象を選択してください", 
        ["鋼材の強度計算", "ボルトの強度計算", "ワイヤーロープの計算"]
    )
    st.sidebar.divider()

    if calc_mode == "鋼材の強度計算":
        with st.sidebar:
            st.header("⚙️ 鋼材の設定")
            shape_list = list(STEEL_DB.keys())
            shape = st.selectbox("鋼材形状", shape_list)
            size_list = list(STEEL_DB[shape].keys())
            selected_size = st.selectbox("規格寸法", size_list)
            axis = st.radio("断面の向き", ["強軸 (X軸回り)", "弱軸 (Y軸回り)"])
            p = STEEL_DB[shape][selected_size]

            st.markdown("---")
            st.markdown("**【適用寸法】**")
            for key, value in p.items():
                st.markdown(f"- **{key}** : {value} mm")

            st.divider()
            L_mm = st.number_input("部材長 (支点間距離 L) (mm)", value=1000.0)
            sf = st.number_input("安全率 (推奨3.0)", value=3.0, min_value=1.0)

        # 計算実行
        A, I, Z, w = calculate_section(shape, p, axis)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"📋 断面性能 ({shape} - {selected_size})")
            st.write(f"計算対象の軸: **{axis}**")
            st.write(f"断面積 (A): **{A:.2f}** mm²")
            st.write(f"断面二次モーメント (I): **{I:.2e}** mm⁴")
            st.write(f"断面係数 (Z): **{Z:.2e}** mm³")
            st.write(f"単位重量: **{w:.2f}** kg/m")
            st.write(f"総重量: **{w * L_mm / 1000:.2f}** kg")

        with col2:
            st.subheader("⚖️ 強度計算結果")
            if L_mm > 0 and I > 0 and Z > 0:
                p_elastic = (MATERIAL_PROPS["Yield"] * Z * 4) / L_mm / 9.80665
                p_break = (MATERIAL_PROPS["Tensile"] * Z * 4) / L_mm / 9.80665
                p_safe = p_elastic / sf
                
                st.metric("許容荷重 (安全荷重)", f"{p_safe:.2f} kg")
                st.write(f"弾性限度 (降伏点基準): **{p_elastic:.2f}** kg")
                st.write(f"破断限度 (引張強さ基準): **{p_break:.2f}** kg")
                
                p_n = p_safe * 9.80665
                delta = (p_n * L_mm**3) / (48 * MATERIAL_PROPS["E"] * I)
                st.metric("許容荷重時の最大たわみ", f"{delta:.2f} mm")
            else:
                st.error("入力値が不正のため計算できません。")

        st.divider()
        st.caption("注：本アプリは単純支持梁の中央集中荷重モデルを用いた計算です。角Rやテーパー形状などは省略した矩形近似による簡易計算を行っています。アングル等の弱軸計算は主軸ではなく図心を通るY軸回りとして計算しています。")

    elif calc_mode == "ボルトの強度計算":
        with st.sidebar:
            st.header("⚙️ ボルトの設定")
            bolt_size = st.selectbox("ねじの呼び (メートル並目)", list(BOLT_SIZES.keys()))
            bolt_class = st.selectbox("強度区分", list(BOLT_CLASSES.keys()))
            sf_bolt = st.number_input("安全率 (推奨: 静荷重3.0, 動荷重5.0〜)", value=3.0, min_value=1.0)

        # 計算実行
        A_s = BOLT_SIZES[bolt_size]
        y_stress = BOLT_CLASSES[bolt_class]["Yield"]
        t_stress = BOLT_CLASSES[bolt_class]["Tensile"]
        
        # 荷重計算 (N -> kgf に変換: 1kgf = 9.80665N)
        yield_load_kg = (y_stress * A_s) / 9.80665
        break_load_kg = (t_stress * A_s) / 9.80665
        allowable_tensile = yield_load_kg / sf_bolt
        # せん断強さは一般的に引張降伏応力の約60%として計算
        allowable_shear = allowable_tensile * 0.6 

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"📋 ボルトの性能 ({bolt_size} - 強度区分{bolt_class})")
            st.write(f"有効断面積 (As): **{A_s:.1f}** mm²")
            st.write(f"降伏点 (耐力): **{y_stress}** N/mm²")
            st.write(f"引張強さ: **{t_stress}** N/mm²")
            st.write(f"降伏荷重 (伸び始め): **{yield_load_kg:.2f}** kg")
            st.write(f"破断荷重 (ちぎれる力): **{break_load_kg:.2f}** kg")

        with col2:
            st.subheader("⚖️ 強度計算結果")
            st.metric("許容引張荷重 (軸方向)", f"{allowable_tensile:.2f} kg")
            st.metric("許容せん断荷重 (横方向)", f"{allowable_shear:.2f} kg")
            st.caption(f"※安全率 {sf_bolt} で計算しています。せん断許容荷重は引張の約60%として算出しています。")

    elif calc_mode == "ワイヤーロープの計算":
        with st.sidebar:
            st.header("⚙️ ワイヤー・玉掛けの設定")
            rope_type = st.selectbox("ロープの種類", list(WIRE_DB.keys()))
            dia = st.selectbox("ロープ径", list(WIRE_DB[rope_type].keys()))
            sf_wire = st.number_input("安全率 (クレーン等玉掛け推奨: 6.0)", value=6.0, min_value=1.0)
            
            st.divider()
            st.markdown("**【玉掛け条件】**")
            num_wires = st.number_input("吊り本数", value=2, min_value=1)
            angle = st.slider("吊り角度 (度)", 0, 120, 60, step=15)

        # 計算実行
        break_load_kn = WIRE_DB[rope_type][dia]
        # kN -> kgf 変換
        break_load_kg = break_load_kn * 1000 / 9.80665
        safe_load_per_rope = break_load_kg / sf_wire
        
        # 吊り角度による張力係数（角度θのとき、cos(θ/2) 倍の荷重まで許容できる）
        angle_rad = math.radians(angle / 2)
        efficiency = math.cos(angle_rad)
        total_safe_load = safe_load_per_rope * num_wires * efficiency

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"📋 ロープ性能 ({rope_type} - {dia})")
            st.write(f"破断荷重 (カタログ値): **{break_load_kn:.2f}** kN")
            st.write(f"破断荷重 (kgf換算): **{break_load_kg:.2f}** kg")
            st.write(f"1本あたりの基本安全荷重: **{safe_load_per_rope:.2f}** kg")
            st.caption(f"※安全率 {sf_wire} で計算")

        with col2:
            st.subheader("⚖️ 玉掛け強度計算結果")
            st.write(f"吊り本数: **{num_wires}** 本")
            st.write(f"吊り角度: **{angle}** 度")
            st.metric("システム全体の許容荷重", f"{total_safe_load:.2f} kg")
            st.caption("※端末処理の効率（アイ加工やクリップ留めによる強度低下係数）は1.0として計算しています。実際の運用ではさらに20%〜程度の強度低下を見込んでください。")

    # --- サイドバー：アプリ情報・Readme表示 ---
    with st.sidebar:
        st.divider()
        with st.expander("ℹ️ アプリ情報 / Readme"):
            st.write(f"**バージョン:** {APP_VERSION}")
            st.markdown("---")
            st.markdown(get_readme_text())

if __name__ == "__main__":
    main()