from mqtt_client import MQTTClient
import time
from database import get_database
from video_processor import VideoProcessor

db = get_database()

class Light_Controller:
    def __init__(self, mqtt: MQTTClient, is_auto: bool):
        self.mqtt = mqtt
        self.is_auto = is_auto
        self.total_time = 40

    async def control(self, video_processor1: VideoProcessor, video_processor2: VideoProcessor, topic, duration=60, total =40):
        while True:
            if self.is_auto == False:
                return
            time.sleep(duration)
            count_1 = video_processor1.counts_all
            count_2 = video_processor2.counts_all
            video_processor1.counts_all = 0
            video_processor2.counts_all = 0

            ratio1 = count_1/(count_1 + count_2)
            time_green = int(total*ratio1)
            time_red = total - time_green
            time_yellow = 3000

            time_green2 = time_red - time_yellow
            time_red2 = time_yellow + time_green
            time_yellow2 = 3000


            message1 = f"1,{time_green*1000},{time_yellow},{time_red*1000}"
            message2 = f"1,{time_green2*1000},{time_yellow2},{time_red2*1000}"
            self.mqtt.publish(topic=topic, payload=message1)
            self.mqtt.publish(topic=topic, payload=message2)
    
    def cal_time():
        pass



            
            