import threading
from traffic_light1 import traffic_loop1, mqtt_loop1
from traffic_light2 import traffic_loop2, mqtt_loop2
if __name__ == "__main__":
    print("Khởi động mô phỏng đèn giao thông...")
    threading.Thread(target=mqtt_loop1, daemon=True, name="1").start()
    threading.Thread(target=mqtt_loop2, daemon=True, name="2").start()
    threading.Thread(target=traffic_loop1, daemon=True, name="3").start()
    threading.Thread(target=traffic_loop2, daemon=True, name="4").start()
    while True:
        s = 1