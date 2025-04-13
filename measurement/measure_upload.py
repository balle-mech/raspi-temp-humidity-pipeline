import time
import csv
import os, sys
from datetime import datetime, timedelta

# プロジェクトのルートディレクトリをsys.pathに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from upload import upload_to_adls

measurement_interval_seconds = 120.0
csv_rotation_interval_minutes = 2880
device0 = os.environ["DEVICE0"]
csv_directory = os.path.join(os.getcwd(), 'local_raw_data')


# ファイルの先頭行を読み取って整数値を返す関数
def readFirstLine(filename):
    try:
        with open(filename, "rt") as f:
            value = int(f.readline())
            return True, value
    except ValueError:
        return False, -1
    except OSError:

        return False, 0


# 新しいCSVファイルを作成する関数
def create_new_csv():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"temp_humidity_{timestamp}.csv"
    filepath = os.path.join(csv_directory, filename)
    with open(filepath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Timestamp", "Temperature (℃)", "Humidity (%)"])
    return filepath

# メイン処理
try:
    current_csv = create_new_csv()
    start_time = datetime.now()

    while True:
        # 温度を取得
        Flag, Temperature = readFirstLine(device0 + "/in_temp_input")
        temperature = Temperature // 1000 if Flag else "N.A."

        # 湿度を取得
        Flag, Humidity = readFirstLine(device0 + "/in_humidityrelative_input")
        humidity = Humidity // 1000 if Flag else "N.A."

        # 現在時刻を取得
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # データをCSVに記録
        with open(current_csv, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([timestamp, temperature, humidity])

        print(f"[{timestamp}] Temperature: {temperature} ℃, Humidity: {humidity} %")

        # 30分経過したらファイルをADLSに送信し、新しいCSVファイルを作成
        if datetime.now() - start_time >= timedelta(minutes=csv_rotation_interval_minutes):
            upload_to_adls.upload_csv(current_csv)
            current_csv = create_new_csv()
            start_time = datetime.now()

        time.sleep(measurement_interval_seconds)

except KeyboardInterrupt:
    print("\n計測を終了しました。")
