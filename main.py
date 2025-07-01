import streamlit as st
import os
import fitz
import re
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilename
import subprocess
import time
from pathlib import Path

# アプリのタイトル
st.title("PDF ツール")

# サイドバーで画面を切り替える
page = st.sidebar.selectbox("機能を選択してください", ["日付削除＆印刷ツール", "請求書・明細書印刷ツール"])

# デフォルトのフォルダパス（ダウンロードフォルダ）
default_folder = os.path.expanduser("~/Downloads")

# セッションステートでフォルダパスとAcrobatパスを管理
if "folder_path" not in st.session_state:
    st.session_state.folder_path = default_folder
if "acrobat_path" not in st.session_state:
    st.session_state.acrobat_path = r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe"
if "print_ready_files" not in st.session_state:
    st.session_state.print_ready_files = []

# フォルダ選択関数
def select_folder():
    try:
        root = Tk()
        root.withdraw()  # Tkinter ウィンドウを非表示にする
        selected_folder = askdirectory(initialdir=default_folder)
        root.destroy()  # Tkinter ウィンドウを破棄
        return selected_folder
    except Exception as e:
        st.error(f"フォルダ選択中にエラーが発生しました: {e}")
        return None

# ファイル選択関数（Acrobat.exeのパス選択用）
def select_file():
    try:
        root = Tk()
        root.withdraw()  # Tkinter ウィンドウを非表示にする
        selected_file = askopenfilename(filetypes=[("実行ファイル", "*.exe")])
        root.destroy()  # Tkinter ウィンドウを破棄
        return selected_file
    except Exception as e:
        st.error(f"ファイル選択中にエラーが発生しました: {e}")
        return None

# 管理画面セクション
with st.sidebar.expander("管理画面"):
    st.write("ここでは設定を変更できます。")

    # Acrobat.exe のパスを直接入力
    st.session_state.acrobat_path = st.text_input(
        "Acrobat.exe のパスを入力",
        value=st.session_state.acrobat_path
    )

# フォルダ選択ボタン
# if st.sidebar.button("フォルダを選択"):
#     selected_folder = select_folder()
#     if selected_folder:
#         st.session_state.folder_path = selected_folder
#         st.success(f"選択されたフォルダ: {st.session_state.folder_path}")

# フォルダパスの表示
folder_path = st.text_input(
    "印刷対象フォルダをここにペーストしてください（例：C:/Users/ys-ot/Downloads）",
    value=st.session_state.folder_path  # セッションステートの値を初期値に
)
# 入力が変わったらセッションステートも更新
st.session_state.folder_path = folder_path

st.sidebar.write(f"現在のフォルダ: {st.session_state.folder_path}")

# 日付削除＆印刷ツール
if page == "日付削除＆印刷ツール":
    st.header("日付削除＆印刷ツール")
    st.write("領収書 PDFファイルの領収日を削除し、印刷します。")
    if st.button("日付削除を実行しますか？"):
        if folder_path and os.path.isdir(folder_path):
            try:
                date_pattern = re.compile(r"\d{4}年\d{1,2}月\d{1,2}日")
                log = []

                for filename in os.listdir(folder_path):
                    if filename.lower().endswith(".pdf") and "領収書" in filename:
                        filepath = os.path.join(folder_path, filename)
                        doc = fitz.open(filepath)
                        modified = False

                        for page in doc:
                            rects = page.search_for("領収日")
                            if rects:
                                x0 = rects[0].x1 + 5
                                y0 = rects[0].y0 - 2
                                y1 = rects[0].y1 + 2
                                matches = date_pattern.findall(page.get_text())
                                for match in matches:
                                    areas = page.search_for(match)
                                    for area in areas:
                                        if area.x0 > x0 and y0 < area.y0 < y1:
                                            page.add_redact_annot(area, fill=(1, 1, 1))
                                            modified = True
                            if modified:
                                page.apply_redactions()

                        if modified:
                            output_path = os.path.join(folder_path, f"cleaned_{filename}")
                            doc.save(output_path)
                            log.append(f"✅ {filename} → cleaned_{filename}")
                            st.session_state.print_ready_files.append(output_path)
                        doc.close()

                if log:
                    st.write("### 処理結果:")
                    st.text("\n".join(log))
                else:
                    st.info("日付の空白処理対象はありませんでした。")
            except Exception as e:
                st.error(f"処理中にエラーが発生しました: {e}")
        else:
            st.error("有効なフォルダパスを入力してください。")

    # 印刷確認
    if st.session_state.print_ready_files:
        # `cleaned_領収書` に限定し、通し番号順にソート
        filtered_files = sorted(
            [f for f in st.session_state.print_ready_files if os.path.basename(f).startswith("cleaned_")],
            key=lambda x: x
        )
        if filtered_files:
            st.write("印刷を実行しますか？")
            st.write(f"印刷対象PDF: {len(filtered_files)} 件")
            st.text("\n".join(filtered_files))
            col1, col2 = st.columns(2)
            with col1:
                if st.button("はい"):
                    try:
                        for i, pdf_file in enumerate(filtered_files, 1):
                            st.write(f"[{i}/{len(filtered_files)}] 印刷中: {pdf_file}")
                            subprocess.Popen([st.session_state.acrobat_path, "/p", "/h", pdf_file])
                            time.sleep(5)
                            subprocess.run(["taskkill", "/IM", "Acrobat.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            time.sleep(2)
                        st.success("印刷が完了しました！")
                        st.session_state.print_ready_files = []  # 印刷リストをリセット
                    except Exception as e:
                        st.error(f"印刷中にエラーが発生しました: {e}")
            with col2:
                if st.button("いいえ"):
                    st.info("印刷をキャンセルしました。")
                    st.session_state.print_ready_files = []  # 印刷リストをリセット
        else:
            st.info("印刷対象のファイルがありません。")

# 請求書・明細書印刷ツール
elif page == "請求書・明細書印刷ツール":
    st.header("請求書・明細書・領収書印刷ツール")
    st.write("請求書・明細書・領収書 の名前のPDFファイルを通し番号順に印刷します。")

    # 印刷対象リストがなければ「印刷を実行しますか？」ボタンを表示
    if not st.session_state.print_ready_files:
        if st.button("印刷を実行しますか？"):
            if folder_path and os.path.isdir(folder_path):
                try:
                    folder_path_obj = Path(folder_path)
                    pdf_files = sorted(
                        [f for f in folder_path_obj.glob("*.pdf") if any(keyword in f.name for keyword in ["請求書", "領収書", "明細書"])],
                        key=lambda f: int(re.search(r'_(\d+)\.pdf$', f.name).group(1)) if re.search(r'_(\d+)\.pdf$', f.name) else float('inf')
                    )
                    st.session_state.print_ready_files = [str(pdf_file) for pdf_file in pdf_files]
                except Exception as e:
                    st.error(f"印刷対象PDFの取得中にエラーが発生しました: {e}")
            else:
                st.error("有効なフォルダパスを入力してください。")

    # 印刷対象リストがあれば「はい」「いいえ」ボタンを表示
    if st.session_state.print_ready_files:
        st.write(f"印刷対象PDF: {len(st.session_state.print_ready_files)} 件")
        st.text("\n".join(st.session_state.print_ready_files))
        col1, col2 = st.columns(2)
        with col1:
            if st.button("はい", key="print_invoice"):
                try:
                    for i, pdf_file in enumerate(st.session_state.print_ready_files, 1):
                        st.write(f"[{i}/{len(st.session_state.print_ready_files)}] 印刷中: {pdf_file}")
                        subprocess.Popen([st.session_state.acrobat_path, "/p", "/h", pdf_file])
                        time.sleep(2)
                        subprocess.run(["taskkill", "/IM", "Acrobat.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        time.sleep(2)
                    st.success("印刷が完了しました！")
                    st.session_state.print_ready_files = []  # 印刷リストをリセット
                except Exception as e:
                    st.error(f"印刷中にエラーが発生しました: {e}")
        with col2:
            if st.button("いいえ", key="cancel_invoice"):
                st.info("印刷をキャンセルしました。")
                st.session_state.print_ready_files = []  # 印刷リストをリセット