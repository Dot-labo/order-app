import os
import glob
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import Bycd
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- グローバル設定: 定数 ---
# ユーザー名やパスワードは、実際の値に書き換えてください。
GLUSELLER_LOGIN_URL = "https://partner.gluseller.com/login"
GLUSELLER_USERNAME = "nakacyo"  # 実際のログインIDに書き換えてください
GLUSELLER_PASSWORD = "your_password_here"  # 実際のパスワードに書き換えてください

GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1EK1aYpYzkB_zfwQZH9bqjNqLi_nnpEEOWPiLD3fIfoYI/edit"
TARGET_SHEET_NAME = "生成データ"

USER_HOME_DIRECTORY = os.path.expanduser('~')
DOWNLOADS_PATH = os.path.join(USER_HOME_DIRECTORY, 'Downloads')
EXCEL_FILE_NAME = "中長様請求書顧客リスト.xlsx"
EXCEL_FILE_PATH = os.path.join(DOWNLOADS_PATH, EXCEL_FILE_NAME)


def login_to_gluseller(driver):
    """
    SeleniumのWebDriverインスタンスを使い、GLUSELLERにログインする関数。
    """
    print("\n--- GLUSELLERへのログイン処理 ---")
    try:
        driver.get(GLUSELLER_LOGIN_URL)
        print("ログインページを開きました。")

        # ログインIDとパスワードの入力フィールドを探して入力
        wait = WebDriverWait(driver, 10)
        id_field = wait.until(EC.presence_of_element_located((By.ID, "login_id")))
        id_field.send_keys(GLUSELLER_USERNAME)
        print("ログインIDを入力しました。")

        # パスワードフィールドはIDの次の要素と仮定
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(GLUSELLER_PASSWORD)
        print("パスワードを入力しました。")

        # ログインボタンをクリック
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'ログイン')]")
        login_button.click()
        print("ログインボタンをクリックしました。")
        
        # ログイン後のページ読み込みを待機（例として5秒）
        time.sleep(5)
        print("ログインが成功したと仮定し、次の処理に進みます。")

    except Exception as e:
        print(f"GLUSELLERへのログイン中にエラーが発生しました: {e}")
        # エラーが発生した場合でも処理を続行するか、ここで終了するか選択できます
        # raise  # ここでコメントを外すと、エラー発生時にスクリプトが停止します


def get_data_from_google_sheet(driver):
    """
    Googleスプレッドシートからデータを直接読み込み、pandasのDataFrameとして返す関数。
    """
    print("\n--- Googleスプレッドシートからのデータ読み取り ---")
    try:
        driver.get(GOOGLE_SHEET_URL)
        print("Googleスプレッドシートを開いています...")
        print("!!! 重要: Googleアカウントにログインしていない場合は、手動でログインしてください。 !!!")
        
        # ユーザーがログイン操作をするための待機時間
        input("Googleアカウントへのログインが完了したら、Enterキーを押してください...")

        # 「生成データ」シートのタブをクリックしてアクティブにする
        wait = WebDriverWait(driver, 30)
        sheet_tab_xpath = f"//div[contains(@class, 'goog-inline-block') and text()='{TARGET_SHEET_NAME}']"
        print(f"「{TARGET_SHEET_NAME}」シートのタブを探しています...")
        sheet_tab = wait.until(EC.element_to_be_clickable((By.XPATH, sheet_tab_xpath)))
        sheet_tab.click()
        print(f"「{TARGET_SHEET_NAME}」シートをアクティブにしました。")
        time.sleep(3) # シートの描画を待つ

        # Ctrl+A (すべて選択) と Ctrl+C (コピー) を実行
        body = driver.find_element(By.TAG_NAME, 'body')
        body.send_keys(Keys.CONTROL, 'a')
        time.sleep(1)
        body.send_keys(Keys.CONTROL, 'c')
        time.sleep(1)
        print("シートのデータをクリップボードにコピーしました。")

        # クリップボードからデータを読み込んでDataFrameを作成
        df = pd.read_clipboard(sep='\t')
        print("クリップボードからデータをDataFrameに読み込みました。")
        return df

    except Exception as e:
        print(f"Googleスプレッドシートの操作中にエラーが発生しました: {e}")
        return None


def cleanup_downloaded_pdfs(directory_path):
    """指定されたディレクトリ内の請求書・領収書・明細書PDFを削除する関数。"""
    print("\n--- PDFファイルのクリーンアップ処理 ---")
    # (この関数の中身は変更なし)
    print("削除処理を開始します...")
    file_patterns = ["請求書*.pdf", "領収書*.pdf", "明細書*.pdf"]
    deleted_count = 0
    for pattern in file_patterns:
        for file_path in glob.glob(os.path.join(directory_path, pattern)):
            try:
                os.remove(file_path)
                print(f"削除しました: {file_path}")
                deleted_count += 1
            except OSError as e:
                print(f"エラー: ファイルを削除できませんでした。{file_path} (理由: {e})")
    print(f"PDFファイルのクリーンアップが完了しました。合計 {deleted_count} 個のファイルを削除しました。")


def delete_local_excel_file(file_path):
    """指定されたローカルのExcelファイルが存在すれば削除する関数。"""
    print("\n--- ローカルExcelファイルのクリーンアップ処理 ---")
    # (この関数の中身は変更なし)
    if not os.path.exists(file_path):
        print(f"ファイルは元々存在しませんでした: {file_path}")
        return
    try:
        os.remove(file_path)
        print(f"ファイルを削除しました: {file_path}")
    except OSError as e:
        print(f"エラー: ファイルを削除できませんでした。{file_path} (理由: {e})")


def main():
    """
    スクリプトのメイン処理を順番に実行する関数。
    """
    driver = None
    try:
        # 最初に一度だけブラウザを起動
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.maximize_window() # 画面を最大化して要素を見つけやすくする

        # 1. GLUSELLERにログイン
        login_to_gluseller(driver)

        # 2. ユーザーにPDF削除の確認
        user_response = input(f"\n{DOWNLOADS_PATH} 内の請求書・領収書・明細書PDFを全て削除しますか？ (yes/no): ").lower()
        if user_response in ['yes', 'y']:
            cleanup_downloaded_pdfs(DOWNLOADS_PATH)
        else:
            print("PDFファイルの削除はキャンセルされました。")

        # 3. 既存のローカルExcelファイルを削除
        delete_local_excel_file(EXCEL_FILE_PATH)

        # 4. Googleスプレッドシートからデータを取得
        customer_df = get_data_from_google_sheet(driver)

        # 5. 取得したデータの確認
        if customer_df is not None:
            print("\n--- 取得したデータ（先頭5行） ---")
            print(customer_df.head())
            # この後、customer_dfを使って様々な処理ができます。
        else:
            print("\nデータの取得に失敗しました。")

    except Exception as e:
        print(f"\nメイン処理の実行中に予期せぬエラーが発生しました: {e}")
    finally:
        # エラー発生の有無にかかわらず、最後に必ずブラウザを閉じる
        if driver:
            print("\n全ての処理が完了したため、ブラウザを閉じます。")
            driver.quit()
        input("Enterキーを押すとプログラムを終了します...")


# このスクリプトが直接実行された場合にのみ、main()関数を呼び出す
if __name__ == "__main__":
    main()
