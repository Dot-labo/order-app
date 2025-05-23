import streamlit as st
import gspread
import pytz
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

import os
import json
from oauth2client.service_account import ServiceAccountCredentials

SPREADSHEET_KEY = "1J7q1y6q6NH0YxF59S6HC0hUhVAlKzyJyQiaC9CIlJqg"
DROPBOX_REQUEST_URL = "https://www.dropbox.com/request/bMH4Sahb8uTyymHuhgJJ"

# Googleスプレッドシート接続
def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # 環境変数 "GOOGLE_CREDS_JSON" に格納された JSON 文字列を辞書として読み込み
    creds_dict = json.loads(os.environ["GOOGLE_CREDS_JSON"])

    # Google 認証情報を作成
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

    # 認証してスプレッドシートにアクセス
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_KEY).worksheet("注文リスト")

# ======== 担当者名をURLから取得 ========
query_params = st.query_params
car_info = query_params.get("car", "")  # 例：?car=1234
time_period = query_params.get("time", "PM")  # 例：?time=AM または ?time=PM

# Streamlit UI
st.set_page_config(page_title="宅配お弁当注文", layout="wide")

if time_period == "AM":
    st.markdown(
        """
    <h1 style="color: black; background-color: #E0F7FA; padding: 10px; border-radius: 5px;font-size: 24px;">
        宅配お弁当注文システム（午前用）
    </h1>
        """,
        unsafe_allow_html=True
    )
else:  # PM
    st.markdown(
        """
    <h1 style="color: black; background-color: #FFE5B4; padding: 10px; border-radius: 5px;font-size: 24px;">
        宅配お弁当注文システム（午後用）
    </h1>
        """,
        unsafe_allow_html=True
    )

if not car_info:
    st.warning("URLに ?car=配送車情報 を付けてアクセスしてください。")
    st.stop()

st.markdown(f"#### 配送車情報：{car_info}")
st.markdown(f"#### 時間帯：{time_period}")

customer_name = st.text_input("お客様のお名前", placeholder="例: 山田 太郎")

order_type = st.radio("注文タイプを選択してください", ["注文", "集金", "その他"])


# 配達日（date_input の表示そのまま）
delivery_date = st.date_input("配達日", value=datetime.now().date() + timedelta(days=1))

# 日本語曜日変換
weekdays_ja = ["月", "火", "水", "木", "金", "土", "日"]
weekday = weekdays_ja[delivery_date.weekday()]

formatted_date = f"{delivery_date.year}年{delivery_date.month}月{delivery_date.day}日（{weekday}）"
st.markdown(f"#### 配達日：{formatted_date}")


# 配送コースとお弁当の種類を時間帯に応じて切り替え
if time_period == "AM":
    delivery_course = st.radio("配送コースを選択してください", [
        "東員", "川越", "菰野", "羽津", "四日市1", "四日市2", "日永", "高齢者昼", "別便", "その他"
    ])
    st.markdown("##### お弁当の種類と数量")
    bento_types = [
        "ヘルシー", "デラックス", "ヘルシーおかず", "デラックスおかず","唐揚げ弁当", "唐揚げスペシャル弁当", "唐揚げ南蛮弁当","ブラックカレープレーン", "カツカレー", "ハンバーグカレー",
        "野菜", "うどん3種", "うどん2種", "うどん1種","普通食S", "塩分調整食S", "普通食M","白米", "雑穀米","サワラ", "マス", "イワシ", "ブリ", "サバ",
        "親子丼", "カツ丼", "牛丼","冷凍弁当","ヘルシーチケット", "デラックスチケット"
    ]

else:  # PM
    delivery_course = st.radio("配送コースを選択してください", [
        "三重郡", "四日市", "菰野", "別便", "北勢", "その他"
    ])
    st.markdown("##### お弁当の種類と数量")
    bento_types = [
        "普通食S", "塩分調整食S", "普通食M","白米", "雑穀米","サワラ", "マス", "イワシ", "ブリ", "サバ","親子丼", "カツ丼", "牛丼","うどん3種", "うどん2種", "うどん1種","やわらか食", "ムース食","冷凍弁当"
    ]




columns = st.columns(3)
bento_quantities = {}
for bento in bento_types:
    current_qty = st.session_state.get(bento, 0)

    # ラベル表示（色つき）
    if current_qty > 0:
        st.markdown(
            f"<div style='color:red; font-weight:bold; font-size:18px;'>{bento}: {current_qty}個</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div style='color:gray; font-size:18px;'>{bento}: {current_qty}個</div>",
            unsafe_allow_html=True
        )

    # 数量入力欄（ラベル非表示）
    qty = st.number_input(
        f"{bento}",
        min_value=0,
        max_value=20,
        step=1,
        value=current_qty,
        key=bento,
        label_visibility="collapsed"
    )
    bento_quantities[bento] = qty

remarks = st.text_area("備考（自由記入欄）", placeholder="例: 白米は1個大盛、1個普通です")

# st.markdown(f"""
# 📎 添付資料がある方はこちらからアップロードしてください：  
# 👉 [Dropboxにファイルをアップロード]({DROPBOX_REQUEST_URL})
# """)

# dropbox_uploaded = st.checkbox("Dropboxに添付資料をアップロード済み")

submit = st.button("注文を送信")

# 注文送信処理
if submit:
    if customer_name:
        has_bento_order = any(qty > 0 for qty in bento_quantities.values())
        has_remarks = bool(remarks.strip())

        if has_bento_order or has_remarks:
            try:
                sheet = connect_to_sheet()
                # 日本時間（JST）を取得
                jst = pytz.timezone('Asia/Tokyo')
                now_str = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

                rows_to_append = []

                for bento, qty in bento_quantities.items():
                    if qty > 0:
                        row_data = [
                            now_str,
                            time_period,
                            car_info,
                            customer_name,
                            order_type,
                            delivery_course,
                            formatted_date,
                            bento,
                            qty,
                            remarks
                        ]
                        rows_to_append.append(row_data)

                # 備考だけの場合でも行を1つ追加（注文なしだが備考あり）
                if not rows_to_append and has_remarks:
                    row_data = [
                        now_str,
                        time_period,
                        car_info,
                        customer_name,
                        order_type,
                        delivery_course,
                        formatted_date,
                        "（注文なし）",
                        "",
                        remarks
                    ]
                    rows_to_append.append(row_data)

                sheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")
                st.success("注文が正常に送信されました！")
            except Exception as e:
                st.error("注文の送信中にエラーが発生しました。")
                st.text(f"エラー内容: {e}")
        else:
            st.warning("お弁当の注文か備考のいずれかを入力してください。")
    else:
        st.warning("お名前を入力してください。")