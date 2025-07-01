import streamlit as st
import gspread
import pytz
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta, timezone
import os
import json

st.set_page_config(page_title="宅配お弁当注文", layout="wide")

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
# DROPBOX_REQUEST_URL = "https://www.dropbox.com/request/bMH4Sahb8uTyymHuhgJJ" # This seems unused

# 日本標準時 (JST)
JST = timezone(timedelta(hours=9))

# Googleスプレッドシート接続
def connect_to_sheet(sheet_name):
    """Googleスプレッドシートに接続し、指定されたワークシートオブジェクトを返す"""
    try:
        # Check if the secret is available in st.secrets
        if "GOOGLE_CREDS_JSON" not in st.secrets:
            st.error("Google APIの認証情報が設定されていません。アプリの管理者にお問い合わせください。")
            st.info("（管理者向け）RenderのEnvironment Variablesに`GOOGLE_CREDS_JSON`というキーで認証情報を設定してください。")
            return None

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict_str = st.secrets["GOOGLE_CREDS_JSON"]
        creds_dict = json.loads(creds_dict_str)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # "注文デモ" という名前のファイルを開く
        spreadsheet = client.open("注文デモ")
        return spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Googleスプレッドシート内に '{sheet_name}' という名前のシートが見つかりません。")
        return None
    except json.JSONDecodeError:
        st.error("Google APIの認証情報（JSON）の形式が正しくありません。アプリの管理者にご確認ください。")
        return None
    except Exception as e:
        st.error(f"スプレッドシートへの接続中に予期せぬエラーが発生しました: {e}")
        return None

# ======== URLパラメータから情報を取得 ========
query_params = st.query_params
car_info = query_params.get("car", "")
time_period = query_params.get("time", "PM")

# --- 管理者判定とモード選択 ---
is_admin = car_info in ["加藤", "Yasuda"]
if is_admin:
    # 管理者にはモード選択ラジオボタンを表示
    mode = st.radio(
        "画面モードを選択",
        ["注文入力画面", "QRコード生成", "新規登録", "利用停止", "利用再開"],
        horizontal=True
    )
else:
    # 一般ユーザーは注文入力画面に固定
    mode = "注文入力画面"

# --- 管理者専用機能 ---
if is_admin:
    # --- QRコード生成画面 ---
    if mode == "QRコード生成":
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
        pattern = r'^[A-Za-z0-9]+$'

        if st.button("QRコードを作成", key="create_qr"):
            if not car:
                st.error("車両コードを入力してください。")
            elif not re.match(pattern, car):
                st.error("❌ 無効な入力です。car には半角英数字のみ使用できます（記号・空白・日本語は禁止）")
            else:
                # 本番環境のURLを想定
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
        st.stop() # このモードの場合はここで処理を終了

    # --- 新規登録フォーム ---
    elif mode == "新規登録":
        st.title("👤 新規ユーザー登録")
        with st.form("new_user_form", clear_on_submit=True):
            st.subheader("登録情報を入力してください")
            name = st.text_input("名前*")
            trial_date = st.date_input("試食初回日*", value=datetime.now(JST).date())
            source = st.radio("何を見て申し込み*", ["チラシ", "ケアマネ", "Web", "紹介", "その他"])
            payment_method = st.radio("支払方法*", ["現金都度払い", "現金週払い", "現金月払い", "口座振替", "振込"])
            remarks = st.text_area("備考")
            submitted = st.form_submit_button("登録内容を送信")

            if submitted:
                if not name:
                    st.warning("名前を入力してください。")
                else:
                    sheet = connect_to_sheet("新規ユーザー")
                    if sheet:
                        try:
                            now_str = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
                            row_data = [now_str, name, str(trial_date), source, payment_method, remarks]
                            sheet.append_row(row_data, value_input_option="USER_ENTERED")
                            st.success(f"✅ {name}様の新規登録が完了しました。")
                        except Exception as e:
                            st.error(f"シートへの書き込み中にエラーが発生しました: {e}")
        st.stop()

    # --- 利用停止フォーム ---
    elif mode == "利用停止":
        st.title("⏸️ 利用停止手続き")
        with st.form("stop_user_form", clear_on_submit=True):
            st.subheader("停止情報を入力してください")
            name = st.text_input("名前*")
            last_day = st.date_input("最終日*", value=datetime.now(JST).date())
            final_payment = st.radio("最終支払方法*", ["現金", "振込", "口座振替"])
            billing_name = st.text_input("請求先の氏名（必要な場合）")
            billing_address = st.text_input("請求先の住所（必要な場合）")
            remarks = st.text_area("備考")
            submitted = st.form_submit_button("停止内容を送信")

            if submitted:
                if not name:
                    st.warning("名前を入力してください。")
                else:
                    sheet = connect_to_sheet("停止ユーザー")
                    if sheet:
                        try:
                            now_str = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
                            row_data = [now_str, name, str(last_day), final_payment, billing_name, billing_address, remarks]
                            sheet.append_row(row_data, value_input_option="USER_ENTERED")
                            st.success(f"✅ {name}様の利用停止手続きが完了しました。")
                        except Exception as e:
                            st.error(f"シートへの書き込み中にエラーが発生しました: {e}")
        st.stop()

    # --- 利用再開フォーム ---
    elif mode == "利用再開":
        st.title("▶️ 利用再開手続き")
        with st.form("resume_user_form", clear_on_submit=True):
            st.subheader("再開情報を入力してください")
            name = st.text_input("名前*")
            resume_date = st.date_input("再開日*", value=datetime.now(JST).date())
            remarks = st.text_area("備考")
            submitted = st.form_submit_button("再開内容を送信")

            if submitted:
                if not name:
                    st.warning("名前を入力してください。")
                else:
                    sheet = connect_to_sheet("再開ユーザー")
                    if sheet:
                        try:
                            now_str = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
                            row_data = [now_str, name, str(resume_date), remarks]
                            sheet.append_row(row_data, value_input_option="USER_ENTERED")
                            st.success(f"✅ {name}様の利用再開手続きが完了しました。")
                        except Exception as e:
                            st.error(f"シートへの書き込み中にエラーが発生しました: {e}")
        st.stop()

# --- 注文入力画面（通常ユーザーと管理者の両方が利用）---
if mode == "注文入力画面":
    if time_period == "AM":
        st.markdown(
            """<h1 style="color: black; background-color: #E0F7FA; padding: 10px; border-radius: 5px;font-size: 24px;">
            宅配お弁当注文システム（午前用）</h1>""", unsafe_allow_html=True)
    else:  # PM
        st.markdown(
            """<h1 style="color: black; background-color: #FFE5B4; padding: 10px; border-radius: 5px;font-size: 24px;">
            宅配お弁当注文システム（午後用）</h1>""", unsafe_allow_html=True)

    if not car_info:
        st.warning("URLに ?car=配送車情報 を付けてアクセスしてください。")
        st.stop()

    st.markdown(f"#### 担当者：{car_info}")
    st.markdown(f"#### 時間帯：{time_period}")

    with st.form("order_form", clear_on_submit=True):
        customer_name = st.text_input("お客様のお名前*", placeholder="例: 山田 太郎")
        order_type = st.radio("注文タイプ*", ["注文", "集金", "キャンセル", "変更", "その他"])
        delivery_date = st.date_input("配達日*", value=datetime.now(JST).date() + timedelta(days=1))
        
        weekdays_ja = ["月", "火", "水", "木", "金", "土", "日"]
        weekday = weekdays_ja[delivery_date.weekday()]
        formatted_date = f"{delivery_date.year}年{delivery_date.month}月{delivery_date.day}日（{weekday}）"
        st.markdown(f"**配達日：{formatted_date}**")

        if time_period == "AM":
            delivery_course = st.radio("配送コース*", ["東員", "川越", "菰野", "羽津", "四日市1", "四日市2", "日永", "高齢者昼", "別便", "その他"])
            bento_types = ["ヘルシー", "デラックス", "ヘルシーおかず", "デラックスおかず","唐揚げ弁当", "唐揚げスペシャル弁当", "唐揚げ南蛮弁当","ブラックカレープレーン", "カツカレー", "ハンバーグカレー","スペシャルカレー","カレー大盛", "野菜", "うどん3種", "うどん2種", "うどん1種","普通食S", "塩分調整食S", "普通食M","白米", "雑穀米","サワラ", "マス", "イワシ", "ブリ", "サバ", "親子丼", "カツ丼", "牛丼","冷凍弁当","ヘルシーチケット", "デラックスチケット"]
        else:  # PM
            delivery_course = st.radio("配送コース*", ["三重郡", "四日市", "菰野", "別便", "北勢", "その他"])
            bento_types = ["普通食S", "塩分調整食S", "普通食M","白米", "雑穀米","サワラ", "マス", "イワシ", "ブリ", "サバ","親子丼", "カツ丼", "牛丼","うどん3種", "うどん2種", "うどん1種","やわらか食", "ムース食","冷凍弁当"]

        remarks = st.text_area("備考（自由記入欄）", placeholder="例: 白米は1個大盛、1個普通です")
        st.markdown("---")
        st.markdown("##### お弁当の種類と数量")

        bento_quantities = {}
        cols = st.columns(3)
        for i, bento in enumerate(bento_types):
            with cols[i % 3]:
                bento_quantities[bento] = st.number_input(bento, min_value=0, max_value=20, step=1, key=bento)

        submitted = st.form_submit_button("内容を送信")

        if submitted:
            if not customer_name:
                st.warning("お客様のお名前を入力してください。")
            else:
                has_bento_order = any(qty > 0 for qty in bento_quantities.values())
                has_remarks = bool(remarks.strip())
                if not has_bento_order and not has_remarks:
                    st.warning("お弁当の注文か備考のいずれかを入力してください。")
                else:
                    sheet_name = "AMリスト" if time_period == "AM" else "PMリスト"
                    sheet = connect_to_sheet(sheet_name)
                    if sheet:
                        now_str = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
                        rows_to_append = []
                        
                        # 注文がある場合、各お弁当を別々の行として追加
                        if has_bento_order:
                            for bento, qty in bento_quantities.items():
                                if qty > 0:
                                    row_data = [now_str, time_period, car_info, customer_name, order_type, delivery_course, formatted_date, bento, qty, remarks]
                                    rows_to_append.append(row_data)
                        # 注文がなく備考のみの場合
                        elif has_remarks:
                            row_data = [now_str, time_period, car_info, customer_name, order_type, delivery_course, formatted_date, "（注文なし）", "", remarks]
                            rows_to_append.append(row_data)

                        if rows_to_append:
                            try:
                                sheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")
                                st.success("✅ 注文が正常に送信されました！")
                                # 送信履歴をセッションに追加
                                if "send_history" not in st.session_state:
                                    st.session_state["send_history"] = []
                                st.session_state["send_history"].extend(rows_to_append)
                            except Exception as e:
                                st.error(f"シートへの書き込み中にエラーが発生しました: {e}")

    # --- 送信履歴を表で表示 ---
    if "send_history" in st.session_state and st.session_state["send_history"]:
        import pandas as pd
        st.markdown("---")
        st.markdown("### 今回のセッションでの送信履歴（ページを更新すると消えます）")
        df = pd.DataFrame(
            st.session_state["send_history"],
            columns=["タイムスタンプ", "時間帯", "担当者", "お客様名", "注文タイプ", "配送コース", "配達日", "お弁当", "数量", "備考"]
        )
        st.dataframe(df.tail(10), use_container_width=True) # 直近10件を表示
