import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import traceback

# Googleスプレッドシートの設定
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "c:/Users/ys-ot/pythonprog/grand-aileron-428101-n9-f4a26ef06f7e.json"  # サービスアカウントキーの絶対パス
SPREADSHEET_KEY = "1J7q1y6q6NH0YxF59S6HC0hUhVAlKzyJyQiaC9CIlJqg"  # スプレッドシートのキー

# ファイルの存在確認
if not os.path.exists(CREDS_FILE):
    st.error(f"サービスアカウントキーが見つかりません: {CREDS_FILE}")
    print(f"❌ サービスアカウントキーが見つかりません: {CREDS_FILE}")
    exit()
else:
    st.success("サービスアカウントキーが見つかりました。")
    print("✅ サービスアカウントキーが見つかりました。")

# Googleスプレッドシートに接続
def connect_to_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet("注文リスト")  # 最初のシートを選択
    return sheet

# スプレッドシートのA1セルの値を取得
def get_a1_value():
    try:
        sheet = connect_to_sheet()
        a1_value = sheet.acell("A1").value  # A1セルの値を取得
        st.success(f"A1セルの値: {a1_value}")
        print(f"✅ A1セルの値: {a1_value}")
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        print("❌ エラーが発生しました:")
        print(traceback.format_exc())  # エラーの詳細をターミナルに出力

# 実行
if __name__ == "__main__":
    get_a1_value()