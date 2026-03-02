import os
import sys
import subprocess
import pathlib
import math
import time
import threading
import webbrowser

# --- 1. 自動起動とexe化(PyInstaller)対応の仕掛け ---
def open_browser():
    time.sleep(2)  # サーバーが立ち上がるまで2秒待機
    webbrowser.open("http://localhost:8501")

if __name__ == "__main__":
    # ▼ PyInstallerでexe化された場合の処理
    if getattr(sys, 'frozen', False):
        import streamlit.web.cli as stcli
        # exe内に一時展開された app.py のパスを取得して実行
        script_path = os.path.join(sys._MEIPASS, "app.py")
        sys.argv = ["streamlit", "run", script_path, "--server.headless=true", "--browser.gatherUsageStats=false"]
        
        threading.Thread(target=open_browser, daemon=True).start()
        sys.exit(stcli.main())
        
    # ▼ 通常の python app.py 実行の場合
    elif "STREAMLIT_RUNNING" not in os.environ:
        streamlit_dir = pathlib.Path.home() / ".streamlit"
        streamlit_dir.mkdir(exist_ok=True)
        credentials_file = streamlit_dir / "credentials.toml"
        
        if not credentials_file.exists():
            credentials_file.write_text('[general]\nemail = ""\n')

        os.environ["STREAMLIT_RUNNING"] = "1"
        os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
        os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
        
        threading.Thread(target=open_browser, daemon=True).start()
        subprocess.run([sys.executable, "-m", "streamlit", "run", os.path.abspath(__file__)])
        sys.exit()

# --- 2. ここからStreamlitのメイン処理 ---
import streamlit as st

# 【変数の初期化】VS Codeのエラー防止
shape = "H鋼"
p = {}
L_mm = 1000.0
sf = 3.0

# 鋼材の物性値（SS400相当）
MATERIAL_PROPS = {
    "E": 205000,    # 縦弾性係数 (N/mm2)
    "Yield": 235,   # 降伏点 (N/mm2)
    "Tensile": 400, # 引張強さ (N/mm2)
    "Density": 7.85 # 密度 (g/cm3)
}

def calculate_section(calc_shape, params):
    """断面性能を計算する関数（強軸方向）"""
    A = I = Z = w = 0.0
    
    if calc_shape in ["H鋼", "I形鋼 (Iビーム)", "チャンネル"]:
        H = params.get('H', 100.0)
        B = params.get('B', 100.0)
        t1 = params.get('t1', 6.0)
        t2 = params.get('t2', 8.0)
        A = (B * H) - (B - t1) * (H - 2 * t2)
        I = (B * H**3 / 12) - ((B - t1) * (H - 2 * t2)**3 / 12)
        if H > 0:
            Z = I / (H / 2)
            
    elif calc_shape == "リップみぞ形鋼 (C型鋼)":
        H = params.get('H', 100.0)
        B = params.get('B', 50.0)
        C = params.get('C', 20.0)
        t = params.get('t', 2.3)
        A = (H + 2 * B + 2 * C - 4 * t) * t
        I = (B * H**3 / 12) - ((B - t) * (H - 2 * t)**3 / 12) - (t * (H - 2 * t - 2 * C)**3 / 12)
        if H > 0:
            Z = I / (H / 2)

    elif calc_shape == "T形鋼":
        H = params.get('H', 100.0)
        B = params.get('B', 100.0)
        t1 = params.get('t1', 6.0)
        t2 = params.get('t2', 8.0)
        A = B * t2 + (H - t2) * t1
        if A > 0:
            Cy = (B * t2 * (t2 / 2) + t1 * (H - t2) * (t2 + (H - t2) / 2)) / A
            I = (B * t2**3 / 12 + B * t2 * (Cy - t2 / 2)**2) + (t1 * (H - t2)**3 / 12 + t1 * (H - t2) * (t2 + (H - t2) / 2 - Cy)**2)
            max_y = max(Cy, H - Cy)
            if max_y > 0:
                Z = I / max_y

    elif calc_shape == "等辺アングル":
        L = params.get('L', 50.0)
        t = params.get('t', 5.0)
        A = (2 * L - t) * t
        I = (t * L**3 / 3)
        if L > 0:
            Z = I / L
            
    elif calc_shape == "不等辺アングル":
        H = params.get('H', 75.0)
        B = params.get('B', 50.0)
        t = params.get('t', 6.0)
        A = (H + B - t) * t
        if A > 0:
            Cy = (B * t * (t / 2) + (H - t) * t * (t + (H - t) / 2)) / A
            I = (B * t**3 / 12 + B * t * (Cy - t / 2)**2) + (t * (H - t)**3 / 12 + t * (H - t) * (H / 2 + t / 2 - Cy)**2)
            max_y = max(Cy, H - Cy)
            if max_y > 0:
                Z = I / max_y

    elif calc_shape == "フラットバー":
        B = params.get('B', 50.0)
        t = params.get('t', 6.0)
        A = B * t
        I = (t * B**3) / 12
        if B > 0:
            Z = I / (B / 2)

    elif calc_shape == "四角棒":
        H = params.get('H', 50.0)
        B = params.get('B', 50.0)
        A = B * H
        I = (B * H**3) / 12
        if H > 0:
            Z = I / (H / 2)

    elif calc_shape == "角パイプ":
        H = params.get('H', 100.0)
        B = params.get('B', 100.0)
        t = params.get('t', 3.2)
        A = (B * H) - ((B - 2 * t) * (H - 2 * t))
        I = (B * H**3 / 12) - ((B - 2 * t) * (H - 2 * t)**3 / 12)
        if H > 0:
            Z = I / (H / 2)

    elif calc_shape == "丸パイプ":
        D = params.get('D', 100.0)
        t = params.get('t', 3.2)
        A = (math.pi / 4) * (D**2 - (D - 2 * t)**2)
        I = (math.pi / 64) * (D**4 - (D - 2 * t)**4)
        if D > 0:
            Z = I / (D / 2)

    elif calc_shape == "丸棒":
        D = params.get('D', 50.0)
        A = (math.pi * D**2) / 4
        I = (math.pi * D**4) / 64
        if D > 0:
            Z = I / (D / 2)
            
    elif calc_shape == "六角棒":
        B = params.get('B', 50.0)
        A = 0.866025 * B**2
        I = 0.06013 * B**4
        if B > 0:
            Z = 0.10825 * B**3

    w = A * MATERIAL_PROPS["Density"] / 1000
    return A, I, Z, w

st.set_page_config(page_title="鋼材強度計算Miya", layout="wide")
st.title("🏗️ 鋼材強度計算アプリ")

with st.sidebar:
    st.header("⚙️ 設定")
    
    shape_list = [
        "H鋼", "I形鋼 (Iビーム)", "チャンネル", "リップみぞ形鋼 (C型鋼)", 
        "T形鋼", "等辺アングル", "不等辺アングル", "フラットバー", 
        "四角棒", "角パイプ", "丸パイプ", "丸棒", "六角棒"
    ]
    shape = st.selectbox("鋼材形状", shape_list)
    
    if shape in ["H鋼", "I形鋼 (Iビーム)", "チャンネル", "T形鋼"]:
        p['H'] = st.number_input("高さ H (mm)", value=100.0)
        p['B'] = st.number_input("幅 B (mm)", value=100.0)
        p['t1'] = st.number_input("ウェブ厚 t1 (mm)", value=6.0)
        p['t2'] = st.number_input("フランジ厚 t2 (mm)", value=8.0)
        
    elif shape == "リップみぞ形鋼 (C型鋼)":
        p['H'] = st.number_input("高さ H (mm)", value=100.0)
        p['B'] = st.number_input("幅 B (mm)", value=50.0)
        p['C'] = st.number_input("リップ C (mm)", value=20.0)
        p['t'] = st.number_input("厚み t (mm)", value=2.3)
        
    elif shape == "等辺アングル":
        p['L'] = st.number_input("辺 L (mm)", value=50.0)
        p['t'] = st.number_input("厚み t (mm)", value=5.0)
        
    elif shape == "不等辺アングル":
        p['H'] = st.number_input("長辺 H (mm)", value=75.0)
        p['B'] = st.number_input("短辺 B (mm)", value=50.0)
        p['t'] = st.number_input("厚み t (mm)", value=6.0)
        
    elif shape == "フラットバー":
        p['B'] = st.number_input("幅 B (mm)", value=50.0)
        p['t'] = st.number_input("厚み t (mm)", value=6.0)

    elif shape == "四角棒":
        p['H'] = st.number_input("高さ H (mm)", value=50.0)
        p['B'] = st.number_input("幅 B (mm)", value=50.0)
        
    elif shape == "角パイプ":
        p['H'] = st.number_input("高さ H (mm)", value=100.0)
        p['B'] = st.number_input("幅 B (mm)", value=100.0)
        p['t'] = st.number_input("厚み t (mm)", value=3.2)
        
    elif shape == "丸パイプ":
        p['D'] = st.number_input("外径 D (mm)", value=100.0)
        p['t'] = st.number_input("厚み t (mm)", value=3.2)
        
    elif shape in ["丸棒", "六角棒"]:
        label = "二面幅 B (mm)" if shape == "六角棒" else "外径 D (mm)"
        p['B' if shape == "六角棒" else 'D'] = st.number_input(label, value=50.0)

    st.divider()
    L_mm = st.number_input("部材長 (支点間距離 L) (mm)", value=1000.0)
    sf = st.number_input("安全率 (推奨3.0)", value=3.0, min_value=1.0)

A, I, Z, w = calculate_section(shape, p)

col1, col2 = st.columns(2)
with col1:
    st.subheader(f"📋 断面性能 ({shape})")
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
        st.error("入力値が不正のため計算できません。（各寸法や部材長などを確認してください）")

st.divider()
st.caption("注：本アプリは単純支持梁の中央集中荷重モデルを用いた計算です。断面の向きは原則「強軸」を想定しており、角Rやテーパー形状などは省略した矩形近似による簡易計算を行っています。")