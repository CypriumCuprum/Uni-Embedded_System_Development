import time
import threading
import paho.mqtt.client as mqtt
import socket
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


# Cấu hình MQTT
MQTT_BROKER = get_local_ip()
MQTT_PORT = 1883
MQTT_SUB_TOPIC = "traffic_lights/cycles"
MQTT_PUB_TOPIC = "traffic_lights/noti"
ROAD = "2"

# Chu kỳ mặc định (ms)
RED_TIME = 23000
YELLOW_TIME = 3000
GREEN_TIME = 27000


# Chu kỳ mới
NEW_RED_TIME = RED_TIME
NEW_YELLOW_TIME = YELLOW_TIME
NEW_GREEN_TIME = GREEN_TIME
cycleChanged = False

# Trạng thái đèn giao thông
class TrafficState:
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"

current_state = TrafficState.GREEN
countdown = GREEN_TIME // 1000
last_pub_time = time.time()
client = mqtt.Client()

def pub_status(color, status):
    time_duration = {
        "RED": RED_TIME,
        "YELLOW": YELLOW_TIME,
        "GREEN": GREEN_TIME
    }.get(color, 0) // 1000

    message = f"{ROAD},{color},{time_duration},{status}"
    client.publish(MQTT_PUB_TOPIC, message)
    print("Đã publish:", message)

def pub_status_all(color_on):
    colors = ["RED", "YELLOW", "GREEN"]
    for c in colors:
        status = "ON" if c == color_on else "OFF"
        pub_status(c, status)

def pub_noti():
    time_duration = {
        TrafficState.RED: RED_TIME,
        TrafficState.YELLOW: YELLOW_TIME,
        TrafficState.GREEN: GREEN_TIME
    }[current_state] // 1000

    message = f"{ROAD},{current_state},{time_duration},{countdown}"
    client.publish(MQTT_PUB_TOPIC, message)
    print("Đã publish:", message)

def update_traffic_light():
    global current_state, countdown, RED_TIME, YELLOW_TIME, GREEN_TIME
    global cycleChanged, NEW_RED_TIME, NEW_YELLOW_TIME, NEW_GREEN_TIME

    if cycleChanged:
        RED_TIME = NEW_RED_TIME
        YELLOW_TIME = NEW_YELLOW_TIME
        GREEN_TIME = NEW_GREEN_TIME
        cycleChanged = False
        print("Áp dụng chu kỳ mới:")
        print("Đèn Xanh:", GREEN_TIME)
        print("Đèn Vàng:", YELLOW_TIME)
        print("Đèn Đỏ:", RED_TIME)

    if current_state == TrafficState.RED:
        current_state = TrafficState.GREEN
        countdown = GREEN_TIME // 1000
        pub_status_all("GREEN")
    elif current_state == TrafficState.GREEN:
        current_state = TrafficState.YELLOW
        countdown = YELLOW_TIME // 1000
        pub_status_all("YELLOW")
    elif current_state == TrafficState.YELLOW:
        current_state = TrafficState.RED
        countdown = RED_TIME // 1000
        pub_status_all("RED")
    
    print(f"Chuyển sang trạng thái: {current_state}, thời gian đếm ngược: {countdown}")
    pub_noti()

def on_message(client, userdata, msg):
    global NEW_GREEN_TIME, NEW_YELLOW_TIME, NEW_RED_TIME, cycleChanged
    message = msg.payload.decode()
    print(f"Nhận từ MQTT [{msg.topic}]: {message}")
    try:
        parts = list(map(int, message.split(",")))
        if(str(parts[0]) != ROAD):
            print("Not road 2")
            return
        if len(parts[1:]) == 3:
            NEW_GREEN_TIME, NEW_YELLOW_TIME, NEW_RED_TIME = parts[1:]
            cycleChanged = True
            print("Đã nhận chu kỳ mới:")
            print("GREEN:", NEW_GREEN_TIME)
            print("YELLOW:", NEW_YELLOW_TIME)
            print("RED:", NEW_RED_TIME)
    except Exception as e:
        print("Lỗi khi phân tích chuỗi:", e)
 
def traffic_loop2():
    global countdown
    global last_pub_time
    while True:
        now = time.time()
        if countdown <= 0:
            pub_noti()
            update_traffic_light()
            last_pub_time = now
        else:
            print(f"{current_state} - Còn lại: {countdown} giây")
            if(now - last_pub_time >= 5):
                pub_noti()
                last_pub_time = now
            countdown -= 1
        time.sleep(1)

def mqtt_loop2():
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(MQTT_SUB_TOPIC)
    pub_status_all(f"{current_state}")
    client.loop_forever()

client.on_message = on_message

if __name__ == "__main__":
    print("Khởi động mô phỏng đèn giao thông...")
    threading.Thread(target=mqtt_loop2, daemon=True).start()
    traffic_loop2()
