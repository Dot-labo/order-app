import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# 設定
CREDS_FILE = "c:/Users/ys-ot/pythonprog/grand-aileron-428101-n9-f4a26ef06f7e.json"
SPREADSHEET_KEY = "1J7q1y6q6NH0YxF59S6HC0hUhVAlKzyJyQiaC9CIlJqg"
DROPBOX_REQUEST_URL = "https://www.dropbox.com/request/bMH4Sahb8uTyymHuhgJJ"

# Googleスプレッドシート接続
def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
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
    <h1 style="color: black; background-color: #E0F7FA; padding: 10px; border-radius: 5px;">
        宅配お弁当注文システム（午前用）
    </h1>
        """,
        unsafe_allow_html=True
    )
else:  # PM
    st.markdown(
        """
    <h1 style="color: black; background-color: #FFE5B4; padding: 10px; border-radius: 5px;">
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
    delivery_course = st.radio("配送コースを選択してください", ["四日市A", "三重郡A", "菰野A", "別便A", "北勢A", "委託A", "その他A"])
    st.markdown("##### お弁当の種類と数量")
    bento_types = [
        "普通食M AM", "普通食S AM", "塩分調整食S AM",
        "魚（サバ） AM", "魚（サワラ） AM", "魚（ブリ） AM", "魚（イワシ） AM", "魚（マス） AM",
        "冷凍弁当 AM", "白米 AM", "雑穀米 AM", "かつ丼 AM", "牛丼 AM", "親子丼 AM","デラックスチケット AM","ヘルシーチケット AM", "その他 AM"
    ]

else:  # PM
    # PM用の配送コース
    delivery_course = st.radio("配送コースを選択してください", ["四日市", "三重郡", "菰野", "別便", "北勢", "委託", "その他"])
    st.markdown("##### お弁当の種類と数量")
    bento_types = [
        "普通食M", "普通食S", "塩分調整食S",
        "魚（サバ）", "魚（サワラ）", "魚（ブリ）", "魚（イワシ）", "魚（マス）",
        "冷凍弁当", "白米", "雑穀米", "かつ丼", "牛丼", "親子丼","デラックスチケット","ヘルシーチケット", "その他"
    ]




columns = st.columns(3)
bento_quantities = {}
for i, bento in enumerate(bento_types):
    col = columns[i % 3]
    with col:
        # 先にラベルを表示
        current_qty = st.session_state.get(bento, 0)
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

        # その後に数値入力
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
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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