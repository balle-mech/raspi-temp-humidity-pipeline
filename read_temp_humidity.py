import time

device0 = "/sys/bus/iio/devices/iio:device0"

# ファイルの先頭行を読み取って整数値を返す関数
def readFirstLine(filename):
    try:
        f = open(filename,"rt")
        value = int(f.readline())
        f.close()
        return True, value
    except ValueError:
        f.close()
        return False, -1
    except OSError:
        return False, 0

try:
    while True:
        # 温度を取得
        Flag, Temperature = readFirstLine(device0 + "/in_temp_input")
        print("Temperature:", end="")
        if Flag:
            print(Temperature // 1000, "℃", end="\t")
        else:
            print("N.A.", end="\t")

        # 湿度を取得
        Flag, Humidity = readFirstLine(device0 + "/in_humidityrelative_input")
        print("Humidity:", end="")
        if Flag:
            print(Humidity // 1000, "%")
        else:
            print("N.A.")

        time.sleep(2.0)
except KeyboardInterrupt:
    pass
