# SteelStrengthCalculationMiya

鋼材・ボルト・ワイヤーロープの断面性能および強度を計算するブラウザベースのアプリケーションです。
実行すると自動的にブラウザが立ち上がり、すぐに計算を開始できます。

## ⚠️ exe化（実行ファイル化）時の注意点
StreamlitアプリをPyInstallerでexe化する場合、ブラウザで「404 Error」が出ないようにするため、**Streamlitのフロントエンドデータ（staticフォルダ）を含める**必要があります。

以下のコマンドを実行してexe化してください。

```bash
pyinstaller --noconfirm --onedir --windowed --copy-metadata streamlit --collect-data streamlit app.py