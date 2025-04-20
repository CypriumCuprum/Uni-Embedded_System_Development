import paho.mqtt.client as mqtt
import threading
import asyncio
from config import settings
from database import get_database
from datetime import datetime
from models import TrafficLight, TrafficLightLog
import time
from websocket_manager import WebSocketManager
lastest_mqtt_messages = {}
dem = {}
async def handle_sub_message(topic, message):
    try:
        # global lastest_mqtt_messages
        # global dem
        # lastest_mqtt_messages[topic] = message
        _db = get_database()
        road, color, timeDuration, content = message.split(",")
        # if(content not in ["ON", "OFF"]):
        #     dem[topic] = int(content)
        #     print("đếm với topic", topic, "thời gian còn lại", dem[topic])

        if(content in ["ON", "OFF"]):
            existing_traffic_light = await _db.get_traffic_light_status(color, road)
            if existing_traffic_light:
                success = await _db.update_traffic_light_status(color, content, int(timeDuration), str(road))
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
                # print("Trạng thái đèn giao thông đã được lưu:", trafficLight)
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
    def __init__(self, loop: asyncio.AbstractEventLoop, websocket_manager: WebSocketManager):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.loop = loop
        self.thread = threading.Thread(target=self._start_loop, daemon=True)
        self.websocket_manager = websocket_manager
    
    async def _periodic_websocket_update(self):
        global lastest_mqtt_messages
        global dem
            
        while True:
            if lastest_mqtt_messages and self.websocket_manager:
                # Tạo một bản sao của tin nhắn mới nhất để tránh thay đổi trong quá trình xử lý
                messages_to_send = lastest_mqtt_messages.copy()
                
                # Chuyển thành định dạng dễ đọc cho frontend
                formatted_messages = []
                for topic, message in messages_to_send.items():
                    try:
                        road, color, timeDuration, content = message.split(",")
                        print(f"MQTT Message received on hello {topic}: {message} second:{dem[topic]}")

                        formatted_messages.append({
                            "topic": topic,
                            "road": road,
                            "color": color,
                            "timeDuration": timeDuration,
                            "content": dem[topic],

                        })
                        dem[topic] -= 1
                        
                    except Exception:
                        # Nếu định dạng không đúng, gửi thông tin thô
                        formatted_messages.append({
                            "topic": topic,
                            "raw_message": message
                        })
                
                # Gửi đến tất cả clients
                if formatted_messages:
                    await self.websocket_manager.broadcast( {
                        "type": "mqtt_update",
                        "timestamp": datetime.now().isoformat(),
                        "messages": formatted_messages
                    })
                
            
            # Đợi 1 giây trước khi gửi cập nhật tiếp theo
            await asyncio.sleep(1)

    def connect(self):
        self.client.connect(settings.mqtt_broker, settings.mqtt_port, 60)
        self.thread.start()
        if self.websocket_manager:
            print("Starting periodic websocket update task")
            self.timer_task = asyncio.run_coroutine_threadsafe(
                self._periodic_websocket_update(), 
                self.loop
            )

    def _start_loop(self):
        self.client.loop_forever()

    def on_connect(self, client, userdata, flags, rc):
        print("MQTT Connected with result code " + str(rc))
        self.client.subscribe(settings.mqtt_topic_sub)

    def on_message(self, client, userdata, msg):
        global lastest_mqtt_messages, dem
        topic = msg.topic
        message = msg.payload.decode()
        # nhận message dạng "ROAD,COLOR,timeDuration,content" phần content có thể là trạng thái ON/OFF của đèn hoặc là thời gian còn lại của đèn
        # print(f"MQTT Message received on topic {topic}: {message}")
        road = message.split(",")[0]
        lastest_mqtt_messages[road] = message
        road, color, timeDuration, content = message.split(",")
        if(content not in ["ON", "OFF"]):
            dem[road] = int(content)
            print("đếm với topic", road, "thời gian còn lại", dem[road])

        asyncio.run_coroutine_threadsafe(
            handle_sub_message(topic, message),
            self.loop
        )

    def publish(self, topic: str, payload: str):
        # pub 1 message dạng "ROAD,GreenTimeDuration,YellowTimeDuration,RedTimeDuration" đơn vị ms "1,20000,5000,30000" hiện tại dùng 2 đường là 1 và 2
        self.client.publish(topic, payload)
