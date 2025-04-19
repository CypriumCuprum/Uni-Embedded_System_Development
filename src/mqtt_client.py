import paho.mqtt.client as mqtt
import threading
import asyncio
from config import settings
from database import get_database
from datetime import datetime
from models import TrafficLight, TrafficLightLog

async def handle_sub_message(topic, message):
    try:
        _db = get_database()
        road, color, timeDuration, content = message.split(",")
        if(content in ["ON", "OFF"]):
            existing_traffic_light = await _db.get_traffic_light_status(color)
            if existing_traffic_light:
                success = await _db.update_traffic_light_status(color, content, int(timeDuration))
                if success:
                    print(f"Đèn {color} đã được cập nhật trạng thái thành {content}")
                else:
                    print("Lỗi khi cập nhật trạng thái đèn.")
            else:
                trafficLight = TrafficLight(
                    color=color,
                    road=road,
                    status=content,
                    timeDuration=int(timeDuration)
                )
                await _db.save_traffic_light_status(trafficLight)
                print("Trạng thái đèn giao thông đã được lưu:", trafficLight)
        else:
            status = "ON"
            if(int(content) == 0):
                status  = "OFF"
            trafficLightLog = TrafficLightLog(
                color=color,
                road=road,
                status=status,
                timeDuration=int(timeDuration),
                timeRemaning=int(content),
                timestamp=datetime.utcnow()
            )
            await _db.save_traffic_light_log(trafficLightLog)
            print("Traffic light log saved:", trafficLightLog)
    except Exception as e:
        print("Error handling MQTT message:", e)

class MQTTClient:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.loop = loop
        self.thread = threading.Thread(target=self._start_loop, daemon=True)

    def connect(self):
        self.client.connect(settings.mqtt_broker, settings.mqtt_port, 60)
        self.thread.start()

    def _start_loop(self):
        self.client.loop_forever()

    def on_connect(self, client, userdata, flags, rc):
        print("MQTT Connected with result code " + str(rc))
        self.client.subscribe(settings.mqtt_topic_sub)

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        message = msg.payload.decode()
        # nhận message dạng "ROAD,COLOR,timeDuration,content" phần content có thể là trạng thái ON/OFF của đèn hoặc là thời gian còn lại của đèn
        print(f"MQTT Message received on topic {topic}: {message}")
        asyncio.run_coroutine_threadsafe(
            handle_sub_message(topic, message),
            self.loop
        )

    def publish(self, topic: str, payload: str):
        # pub 1 message dạng "GreenTimeDuration, YellowTimeDuration, RedTimeDuration" đơn vị ms "20000;5000;30000"
        self.client.publish(topic, payload)
