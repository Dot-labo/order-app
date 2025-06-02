import streamlit as st
import gspread
import pytz
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta, timezone
import os
import json

st.set_page_config(page_title="宅配お弁当注文", layout="wide")  # ←ここだけでOK

# 文字化け対策（文字コードとフォントの明示）
st.markdown("""
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP&display=swap" rel="stylesheet">
<style>
body, html, .stApp {
    font-family: 'Noto Sans JP', 'Meiryo', sans-serif;
}
</style>
""", unsafe_allow_html=True)

SPREADSHEET_KEY = "1J7q1y6q6NH0YxF59S6HC0hUhVAlKzyJyQiaC9CIlJqg"
DROPBOX_REQUEST_URL = "https://www.dropbox.com/request/bMH4Sahb8uTyymHuhgJJ"

# Googleスプレッドシート接続
def connect_to_sheet(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(os.environ["GOOGLE_CREDS_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_KEY).worksheet(sheet_name)

# ======== 担当者名をURLから取得 ========
query_params = st.query_params
car_info = query_params.get("car", "")  # 例：?car=1234
time_period = query_params.get("time", "PM")  # 例：?time=AM または ?time=PM

# --- 管理者切り替え ---
is_admin = (car_info == "加藤")
if is_admin:
    mode = st.radio("画面モードを選択", ["注文入力画面", "管理者画面"], horizontal=True)
else:
    mode = "注文入力画面"

# --- 管理者画面 ---
if mode == "管理者画面":
    import qrcode
    import re
    from io import BytesIO

    st.title("注文用QRコード生成ツール")
    st.markdown("""
    ### ❗️入力ルール
    - **半角英数字のみ** 入力してください（例：Yamamoto）
    - **日本語・空白・記号は禁止** です（文字化け防止のため）
    - `time` は AM または PM を選択してください
    """)

    car = st.text_input("担当者コードを入力（例：Yamamoto）")
    time = st.radio("時間帯を選択してください", ["AM", "PM"])

    pattern = r'^[A-Za-z0-9]+$'  # 英数字のみ

    # 作成ボタンを追加
    create_btn = st.button("QRコードを作成", key="create_qr")

    if create_btn:
        if not car:
            st.error("車両コードを入力してください。")
        elif not re.match(pattern, car):
            st.error("❌ 無効な入力です。car には半角英数字のみ使用できます（記号・空白・日本語は禁止）")
        else:
            base_url = "https://order-app-gvl0.onrender.com/"
            final_url = f"{base_url}?car={car}&time={time}"

            st.markdown("### ✅ 完成URL")
            st.code(final_url)

            qr = qrcode.make(final_url)
            buf = BytesIO()
            qr.save(buf, format="PNG")
            byte_im = buf.getvalue()

            st.image(byte_im, caption="QRコード", use_container_width=False)

            st.download_button(
                label="📥 QRコードをダウンロード",
                data=byte_im,
                file_name=f"QR_{car}_{time}.png",
                mime="image/png"
            )
    st.stop()  # 管理者画面のみ表示

# --- ここから注文入力画面（通常画面） ---
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

st.markdown(f"#### 担当者：{car_info}")
st.markdown(f"#### 時間帯：{time_period}")

customer_name = st.text_input("お客様のお名前", placeholder="例: 山田 太郎")

order_type = st.radio("注文タイプを選択してください", ["注文", "集金", "キャンセル", "変更", "その他"])

# 日本標準時 (JST)
JST = timezone(timedelta(hours=9))

# 配達日（date_input の表示そのまま）
delivery_date = st.date_input("配達日", value=datetime.now(JST).date() + timedelta(days=1))

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
        "ヘルシー", "デラックス", "ヘルシーおかず", "デラックスおかず","唐揚げ弁当", "唐揚げスペシャル弁当", "唐揚げ南蛮弁当","ブラックカレープレーン", "カツカレー", "ハンバーグカレー","スペシャルカレー","カレー大盛",
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

# セッション履歴の初期化
if "send_history" not in st.session_state:
    st.session_state["send_history"] = []

# --- 上部にも送信ボタンを追加（ここで配置） ---
submit_top = st.button("内容を送信", key="submit_top")

# --- 備考欄をお弁当の種類と数量の下に移動 ---
remarks = st.text_area("備考（自由記入欄）", placeholder="例: 白米は1個大盛、1個普通です")

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

# --- 下部の送信ボタン（既存） ---
submit = st.button("内容を送信", key="submit_bottom")

# どちらかのボタンが押されたら送信
if submit or submit_top:
    if customer_name:
        has_bento_order = any(qty > 0 for qty in bento_quantities.values())
        has_remarks = bool(remarks.strip())

        if has_bento_order or has_remarks:
            try:
                sheet_name = "AMリスト" if time_period == "AM" else "PMリスト"
                sheet = connect_to_sheet(sheet_name)
                now_str = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

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
                        # 履歴にも追加
                        st.session_state["send_history"].append(row_data)

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
                    st.session_state["send_history"].append(row_data)

                sheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")

                # 並び替え処理（1行目はタイトル、2行目以降をタイムスタンプ降順でソート）
                all_values = sheet.get_all_values()
                if len(all_values) > 2:
                    title = all_values[0]
                    data = all_values[1:]
                    # タイムスタンプ（1列目）で降順ソート
                    data.sort(key=lambda x: x[0], reverse=True)
                    sheet.clear()
                    sheet.append_row(title)
                    sheet.append_rows(data)

                st.success("注文が正常に送信されました！")
            except Exception as e:
                st.error("注文の送信中にエラーが発生しました。")
                st.text(f"エラー内容: {e}")
        else:
            st.warning("お弁当の注文か備考のいずれかを入力してください。")
    else:
        st.warning("お名前を入力してください。")

# --- 送信履歴を表で表示 ---
if st.session_state["send_history"]:
    import pandas as pd
    st.markdown("### 送信履歴（リフレッシュで消えます）")
    df = pd.DataFrame(
        st.session_state["send_history"],
        columns=["タイムスタンプ", "時間帯", "担当者", "お客様名", "注文タイプ", "配送コース", "配達日", "お弁当", "数量", "備考"]
    )
    st.dataframe(df, use_container_width=True)