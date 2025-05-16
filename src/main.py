from fastapi import Depends, FastAPI, WebSocket, HTTPException, Body, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from typing import List, Dict, Tuple
import uvicorn
from config import settings
from database import Database, get_database
from models import VehicleCount, AreaConfig, CountingLineConfig
from video_processor import VideoProcessor
from websocket_manager import WebSocketManager
import asyncio
import os
from pydantic import BaseModel
from mqtt_client import MQTTClient
from light_controller import Light_Controller
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
import config
from models import Road, Device, PyObjectId
# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Vehicle Counting System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define ports for each processor
PORT1 = 8080  # Main application port

# Initialize components
video_processor1 = VideoProcessor(stream_port=PORT1)
video_processor2 = VideoProcessor(stream_port=PORT1)
loop = asyncio.get_event_loop()
mqtt_websocket_manager = WebSocketManager()
mqtt_client = MQTTClient(loop,mqtt_websocket_manager)

light_controller = Light_Controller(mqtt=mqtt_client, is_auto=False)

# Database dependency
async def get_db():
    return get_database()

# Define request models
class CountingLineRequest(BaseModel):
    start: List[int]
    end: List[int]
    processor_id: int = 1  # Default to first processor


@app.on_event("startup")
async def startup_event():
    try:
        mqtt_client.connect()
    except:
        print("MQTT connection failed. Please check your broker settings.")
    # mqtt_client.publish(settings.mqtt_topic_pub, "30000;5000;20000")

    """Initialize video processing on server startup"""
    try:
        # Set up counting line (horizontal line at the middle of the frame)
        line_start = (0, settings.frame_height * 3 // 4)  # Start from left side
        line_end = (settings.frame_width, settings.frame_height * 3 // 4)  # End at right side

        # Configure both processors
        video_processor1.set_counting_line(line_start, line_end)
        video_processor2.set_counting_line(line_start, line_end)

        # Start processing video streams
        stream_url1 = settings.video_url
        stream_url2 = settings.video_url
        # stream_url2 = "http://192.168.1.152:8080/?action=stream" 

        await video_processor1.start_stream(stream_url1)
        await video_processor2.start_stream(stream_url2)

        print("Video processing started automatically")
        print(f"First processed video stream available at: http://localhost:{PORT1}/stream1.mjpg")
        print(f"Second processed video stream available at: http://localhost:{PORT1}/stream2.mjpg")
    except Exception as e:
        print(f"Error starting video processing: {e}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with HTML page showing both video streams"""
    html_content = """
    <html>
        <head>
            <title>Dual Vehicle Counting System</title>
            <style>
                body { margin: 0; background: #000; color: white; font-family: Arial, sans-serif; }
                .container { display: flex; flex-direction: column; align-items: center; padding: 20px; }
                .video-container { margin: 20px 0; border: 1px solid #555; }
                .stream-container { display: flex; flex-direction: row; justify-content: space-around; width: 100%; }
                .stream { width: 48%; margin: 0 1%; border: 1px solid #444; padding: 10px; background: #1a1a1a; }
                img { display: block; width: 100%; height: auto; }
                .stats { margin-top: 15px; text-align: left; width: 100%; }
                .stats h2 { text-align: center; margin-bottom: 10px; }
                .stats p { margin: 5px 0; font-size: 1.1em; }
                .stats ul { list-style: none; padding-left: 20px; }
                .stats li { margin: 3px 0; }
                #fps1, #fps2 { font-weight: bold; }
                #total-down-count1, #total-down-count2 { font-weight: bold; color: #00ff00; /* Green for total */ }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Dual Vehicle Counting System</h1>

                <div class="stream-container">
                    <!-- First stream -->
                    <div class="stream">
                        <h2>Camera 1</h2>
                        <div class="video-container">
                            <img src="/stream1.mjpg" alt="Video Stream 1" id="video-stream1">
                        </div>
                        <div class="stats">
                            <h3>Live Statistics</h3>
                            <p>Total Vehicles Down: <span id="total-down-count1">0</span></p>
                            <p>FPS: <span id="fps1">0.0</span></p>
                            <h4>Counts by Vehicle Type (Down):</h4>
                            <ul id="down-by-class-list1">
                                <li>Loading...</li>
                            </ul>
                        </div>
                    </div>

                    <!-- Second stream -->
                    <div class="stream">
                        <h2>Camera 2</h2>
                        <div class="video-container">
                            <img src="/stream2.mjpg" alt="Video Stream 2" id="video-stream2">
                        </div>
                        <div class="stats">
                            <h3>Live Statistics</h3>
                            <p>Total Vehicles Down: <span id="total-down-count2">0</span></p>
                            <p>FPS: <span id="fps2">0.0</span></p>
                            <h4>Counts by Vehicle Type (Down):</h4>
                            <ul id="down-by-class-list2">
                                <li>Loading...</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            <script>
                // Connect WebSocket for first camera
                const ws1_protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const ws1_url = `${ws1_protocol}//${window.location.host}/ws/stats/1`;
                console.log(`Attempting to connect WebSocket to: ${ws1_url}`);
                const ws1 = new WebSocket(ws1_url);

                // Connect WebSocket for second camera
                const ws2_protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const ws2_url = `${ws2_protocol}//${window.location.host}/ws/stats/2`;
                console.log(`Attempting to connect WebSocket to: ${ws2_url}`);
                const ws2 = new WebSocket(ws2_url);

                // Get references to HTML elements for camera 1
                const totalDownElement1 = document.getElementById('total-down-count1');
                const fpsElement1 = document.getElementById('fps1');
                const downByClassListElement1 = document.getElementById('down-by-class-list1');
                const videoElement1 = document.getElementById('video-stream1');

                // Get references to HTML elements for camera 2
                const totalDownElement2 = document.getElementById('total-down-count2');
                const fpsElement2 = document.getElementById('fps2');
                const downByClassListElement2 = document.getElementById('down-by-class-list2');
                const videoElement2 = document.getElementById('video-stream2');

                // WebSocket handlers for camera 1
                ws1.onopen = function(event) {
                    console.log("WebSocket connection 1 opened");
                    downByClassListElement1.innerHTML = ''; // Clear loading message
                };

                ws1.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);

                        // Update Total Down Count
                        if (data.total_down !== undefined) {
                            totalDownElement1.textContent = data.total_down;
                        } else {
                            totalDownElement1.textContent = 'N/A';
                        }

                        // Update FPS
                        if (data.fps !== undefined) {
                            fpsElement1.textContent = data.fps.toFixed(1);
                        } else {
                            fpsElement1.textContent = 'N/A';
                        }

                        // Update Down by Class List
                        if (data.down_by_class && typeof data.down_by_class === 'object') {
                            let listHtml = '';
                            // Sort keys alphabetically for consistent order
                            const sortedKeys = Object.keys(data.down_by_class).sort();
                            for (const vehicleType of sortedKeys) {
                                const count = data.down_by_class[vehicleType];
                                listHtml += `<li>${vehicleType}: ${count}</li>`;
                            }
                            // Only update if content has changed to reduce flickering
                            if (downByClassListElement1.innerHTML !== listHtml) {
                               downByClassListElement1.innerHTML = listHtml;
                            }
                        } else {
                             if (downByClassListElement1.innerHTML !== '<li>Data not available</li>') {
                                downByClassListElement1.innerHTML = '<li>Data not available</li>';
                             }
                        }

                    } catch (e) {
                        console.error("Error processing WebSocket 1 message:", e);
                        console.error("Received raw data:", event.data);
                        downByClassListElement1.innerHTML = '<li>Error loading data</li>';
                    }
                };

                ws1.onerror = function(event) {
                    console.error("WebSocket 1 error observed:", event);
                    totalDownElement1.textContent = 'Error';
                    fpsElement1.textContent = 'Error';
                    downByClassListElement1.innerHTML = '<li>WebSocket Error</li>';
                };

                ws1.onclose = function(event) {
                    console.log(`WebSocket 1 connection closed: Code=${event.code}, Reason=${event.reason}, WasClean=${event.wasClean}`);
                    totalDownElement1.textContent = 'Disconnected';
                    fpsElement1.textContent = 'N/A';
                    downByClassListElement1.innerHTML = '<li>Connection Closed</li>';
                };

                // WebSocket handlers for camera 2
                ws2.onopen = function(event) {
                    console.log("WebSocket connection 2 opened");
                    downByClassListElement2.innerHTML = ''; // Clear loading message
                };

                ws2.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);

                        // Update Total Down Count
                        if (data.total_down !== undefined) {
                            totalDownElement2.textContent = data.total_down;
                        } else {
                            totalDownElement2.textContent = 'N/A';
                        }

                        // Update FPS
                        if (data.fps !== undefined) {
                            fpsElement2.textContent = data.fps.toFixed(1);
                        } else {
                            fpsElement2.textContent = 'N/A';
                        }

                        // Update Down by Class List
                        if (data.down_by_class && typeof data.down_by_class === 'object') {
                            let listHtml = '';
                            // Sort keys alphabetically for consistent order
                            const sortedKeys = Object.keys(data.down_by_class).sort();
                            for (const vehicleType of sortedKeys) {
                                const count = data.down_by_class[vehicleType];
                                listHtml += `<li>${vehicleType}: ${count}</li>`;
                            }
                            // Only update if content has changed to reduce flickering
                            if (downByClassListElement2.innerHTML !== listHtml) {
                               downByClassListElement2.innerHTML = listHtml;
                            }
                        } else {
                             if (downByClassListElement2.innerHTML !== '<li>Data not available</li>') {
                                downByClassListElement2.innerHTML = '<li>Data not available</li>';
                             }
                        }

                    } catch (e) {
                        console.error("Error processing WebSocket 2 message:", e);
                        console.error("Received raw data:", event.data);
                        downByClassListElement2.innerHTML = '<li>Error loading data</li>';
                    }
                };

                ws2.onerror = function(event) {
                    console.error("WebSocket 2 error observed:", event);
                    totalDownElement2.textContent = 'Error';
                    fpsElement2.textContent = 'Error';
                    downByClassListElement2.innerHTML = '<li>WebSocket Error</li>';
                };

                ws2.onclose = function(event) {
                    console.log(`WebSocket 2 connection closed: Code=${event.code}, Reason=${event.reason}, WasClean=${event.wasClean}`);
                    totalDownElement2.textContent = 'Disconnected';
                    fpsElement2.textContent = 'N/A';
                    downByClassListElement2.innerHTML = '<li>Connection Closed</li>';
                };

                // Optional: Handle image loading errors
                videoElement1.onerror = function() {
                    console.error("Failed to load video stream 1.");
                };

                videoElement2.onerror = function() {
                    console.error("Failed to load video stream 2.");
                };
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/auto_control")
async def auto_control(is_auto:bool):
    if is_auto is None:
        raise HTTPException(status_code=400, detail="Khong biet")
    light_controller.is_auto = is_auto
    try:
        await light_controller.control(video_processor1=video_processor1, video_processor2=video_processor2, topic=settings.mqtt_topic_pub)
    except:
        raise HTTPException(status_code=400, detail="Khong biet")
    return {"status": 200, "messsage":"auto ok"}
    

# Stream endpoints for both cameras
@app.get("/stream1.mjpg")
async def video_stream1():
    """Stream the first processed video feed"""
    return StreamingResponse(
        video_processor1.generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=boundary"
    )


@app.get("/stream2.mjpg")
async def video_stream2():
    """Stream the second processed video feed"""
    return StreamingResponse(
        video_processor2.generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=boundary"
    )


@app.post("/api/video/stream/{processor_id}")
async def configure_video_stream(processor_id: int, stream_url: str):
    """Configure and start video stream processing for a specific processor"""
    try:
        if processor_id == 1:
            await video_processor1.start_stream(stream_url)
        elif processor_id == 2:
            await video_processor2.start_stream(stream_url)
        else:
            raise HTTPException(status_code=400, detail="Invalid processor_id. Must be 1 or 2.")
        return {"status": "success", "message": f"Video stream {processor_id} configured"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/video/status/{processor_id}")
async def get_stream_status(processor_id: int):
    """Get current stream status for a specific processor"""
    if processor_id == 1:
        processor = video_processor1
    elif processor_id == 2:
        processor = video_processor2
    else:
        raise HTTPException(status_code=400, detail="Invalid processor_id. Must be 1 or 2.")

    return {
        "is_running": processor.is_running,
        "current_counts": processor.get_counts(),
        "stream_url": processor.get_stream_url()
    }


@app.post("/api/config/counting-line")
async def set_counting_line(config: CountingLineRequest):
    """Set the counting line coordinates for a specific processor"""
    try:
        # Convert lists to tuples
        start = tuple(config.start)
        end = tuple(config.end)

        # Apply to specified processor (default is 1)
        if config.processor_id == 1:
            video_processor1.set_counting_line(start, end)
        elif config.processor_id == 2:
            video_processor2.set_counting_line(start, end)
        else:
            raise HTTPException(status_code=400, detail="Invalid processor_id. Must be 1 or 2.")

        return {"status": "success", "message": f"Counting line set for processor {config.processor_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/current/{processor_id}")
async def get_current_config(processor_id: int):
    """Get current configuration for a specific processor"""
    if processor_id == 1:
        processor = video_processor1
    elif processor_id == 2:
        processor = video_processor2
    else:
        raise HTTPException(status_code=400, detail="Invalid processor_id. Must be 1 or 2.")

    return {
        "counting_line": processor.get_counting_line()
    }


@app.get("/api/stats/current/{processor_id}")
async def get_current_stats(processor_id: int):
    """Get current counting statistics for a specific processor"""
    if processor_id == 1:
        return video_processor1.get_counts()
    elif processor_id == 2:
        return video_processor2.get_counts()
    else:
        raise HTTPException(status_code=400, detail="Invalid processor_id. Must be 1 or 2.")


@app.get("/api/stats/history/{processor_id}")
async def get_count_history(processor_id: int):
    """Get historical count data for a specific processor"""
    if processor_id == 1:
        return video_processor1.get_count_history()
    elif processor_id == 2:
        return video_processor2.get_count_history()
    else:
        raise HTTPException(status_code=400, detail="Invalid processor_id. Must be 1 or 2.")

# endpoint to change traffic cycles
@app.post("/api/cycle")
async def change_cycle(message: str):
    greenTime1, redTime1 = map(int, message.split(","))
    yellowTime1 = 3
    redTime2 = greenTime1 + yellowTime1
    yellowTime2 = 3
    greenTime2 = redTime1 - yellowTime1
    message1 = f"1,{greenTime1*1000},{yellowTime1*1000},{redTime1*1000}"
    message2 = f"2,{greenTime2*1000},{yellowTime2*1000},{redTime2*1000}"
    mqtt_client.publish(settings.mqtt_topic_pub, message1)
    mqtt_client.publish(settings.mqtt_topic_pub, message2)
    return {f"message_pub to {settings.mqtt_topic_pub}"}


# WebSocket endpoints for both cameras
@app.websocket("/ws/stats/1")
async def websocket_endpoint1(websocket: WebSocket):
    """WebSocket endpoint for real-time count updates from camera 1"""
    await websocket.accept()
    client_host = websocket.client.host
    client_port = websocket.client.port
    print(f"WebSocket connection 1 accepted from: {client_host}:{client_port}")
    try:
        while True:
            # Send current counts every second
            data_to_send = video_processor1.get_counts()
            await websocket.send_json(data_to_send)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print(f"Client disconnected from websocket 1: {client_host}:{client_port}")
    except asyncio.CancelledError:
        print(f"WebSocket 1 task cancelled for: {client_host}:{client_port}")
    except Exception as e:
        print(f"WebSocket 1 error for {client_host}:{client_port}: {e} ({type(e).__name__})")
        try:
            await websocket.close(code=1011)
        except Exception as close_exc:
            print(f"Unexpected error during WebSocket 1 close: {close_exc}")
    finally:
        print(f"WebSocket 1 handler finished for: {client_host}:{client_port}")


@app.websocket("/ws/stats/2")
async def websocket_endpoint2(websocket: WebSocket):
    """WebSocket endpoint for real-time count updates from camera 2"""
    await websocket.accept()
    client_host = websocket.client.host
    client_port = websocket.client.port
    print(f"WebSocket connection 2 accepted from: {client_host}:{client_port}")
    try:
        while True:
            # Send current counts every second
            data_to_send = video_processor2.get_counts()
            await websocket.send_json(data_to_send)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print(f"Client disconnected from websocket 2: {client_host}:{client_port}")
    except asyncio.CancelledError:
        print(f"WebSocket 2 task cancelled for: {client_host}:{client_port}")
    except Exception as e:
        print(f"WebSocket 2 error for {client_host}:{client_port}: {e} ({type(e).__name__})")
        try:
            await websocket.close(code=1011)
        except Exception as close_exc:
            print(f"Unexpected error during WebSocket 2 close: {close_exc}")
    finally:
        print(f"WebSocket 2 handler finished for: {client_host}:{client_port}")
    
# WebSocket endpoint for MQTT data
@app.websocket("/ws/mqtt1")
async def websocket_mqtt_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time MQTT updates"""
    await websocket.accept()  # Sử dụng accept trực tiếp vì chưa có phương thức connect trong code bạn chia sẻ
    client_host = websocket.client.host
    client_port = websocket.client.port
    print(f"MQTT WebSocket connection accepted from: {client_host}:{client_port}")
    # Thêm websocket vào danh sách kết nối của mqtt_websocket_manager
    if not hasattr(mqtt_websocket_manager, "active_connections"):
        mqtt_websocket_manager.active_connections = []
    mqtt_websocket_manager.active_connections.append(websocket)
    mqtt_websocket_manager.list_channel["mqtt1"] = websocket
    
    try:
        # Gửi thông báo kết nối thành công
        await websocket.send_json({
            "type": "mqtt_connection",
            "status": "connected",
            "message": "Connected to MQTT WebSocket endpoint"
        })
        
        # Giữ kết nối mở
        while True:
            # Chờ tin nhắn từ client (nếu cần)
            data = await websocket.receive_text()
            # Xử lý tin nhắn từ client nếu cần
            print(f"Received message from MQTT WebSocket client")
    except WebSocketDisconnect:
        print(f"Client disconnected from MQTT websocket: {client_host}:{client_port}")
        # Xóa websocket khỏi danh sách kết nối
        if websocket in mqtt_websocket_manager.active_connections:
            mqtt_websocket_manager.active_connections.remove(websocket)
    except Exception as e:
        print(f"MQTT WebSocket error: {e}")
        # Xóa websocket khỏi danh sách kết nối trong trường hợp lỗi
        if hasattr(mqtt_websocket_manager, "active_connections"):
            if websocket in mqtt_websocket_manager.active_connections:
                mqtt_websocket_manager.active_connections.remove(websocket)
                mqtt_websocket_manager.list_channel.pop("mqtt1")

# WebSocket endpoint for MQTT data
@app.websocket("/ws/mqtt2")
async def websocket_mqtt_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time MQTT updates"""
    await websocket.accept()  # Sử dụng accept trực tiếp vì chưa có phương thức connect trong code bạn chia sẻ
    client_host = websocket.client.host
    client_port = websocket.client.port
    print(f"MQTT WebSocket connection accepted from: {client_host}:{client_port}")
    
    # Thêm websocket vào danh sách kết nối của mqtt_websocket_manager
    if not hasattr(mqtt_websocket_manager, "active_connections"):
        mqtt_websocket_manager.active_connections = []
    mqtt_websocket_manager.active_connections.append(websocket)
    mqtt_websocket_manager.list_channel["mqtt2"] = websocket
    try:
        # Gửi thông báo kết nối thành công
        await websocket.send_json({
            "type": "mqtt_connection",
            "status": "connected",
            "message": "Connected to MQTT WebSocket endpoint"
        })
        
        # Giữ kết nối mở
        while True:
            # Chờ tin nhắn từ client (nếu cần)
            data = await websocket.receive_text()
            # Xử lý tin nhắn từ client nếu cần
            print(f"Received message from MQTT WebSocket client")
    except WebSocketDisconnect:
        print(f"Client disconnected from MQTT websocket: {client_host}:{client_port}")
        # Xóa websocket khỏi danh sách kết nối
        if websocket in mqtt_websocket_manager.active_connections:
            mqtt_websocket_manager.active_connections.remove(websocket)
    except Exception as e:
        print(f"MQTT WebSocket error: {e}")
        # Xóa websocket khỏi danh sách kết nối trong trường hợp lỗi
        if hasattr(mqtt_websocket_manager, "active_connections"):
            if websocket in mqtt_websocket_manager.active_connections:
                mqtt_websocket_manager.active_connections.remove(websocket)
                mqtt_websocket_manager.list_channel.pop("mqtt2")

# ========== Road Endpoints ==========

@app.get("/api/roads", response_model=List[Road])
async def list_roads(db: Database = Depends(get_db)):
    roads = await db.get_all_roads()
    return roads

@app.post("/api/roads", response_model=Road)
async def create_road(road: Road, db: Database = Depends(get_db)):
    road_dict = road.dict(exclude={"id"})
    # Remove any None values for MongoDB
    road_dict = {k: v for k, v in road_dict.items() if v is not None}
    
    # Create the road
    created_road = await db.create_road(road_dict)
    return created_road

@app.get("/api/roads/{road_id}", response_model=Road)
async def get_road(road_id: str, db: Database = Depends(get_db)):
    road = await db.get_road_by_id(road_id)
    if not road:
        raise HTTPException(status_code=404, detail="Road not found")
    return road

@app.put("/api/roads/{road_id}", response_model=Road)
async def update_road(road_id: str, road: Road, db: Database = Depends(get_db)):
    # Check if road exists
    existing_road = await db.get_road_by_id(road_id)
    if not existing_road:
        raise HTTPException(status_code=404, detail="Road not found")
    
    # Prepare data for update
    road_dict = road.dict(exclude={"id"})
    road_dict = {k: v for k, v in road_dict.items() if v is not None}
    
    # Update the road
    updated_road = await db.update_road(road_id, road_dict)
    if not updated_road:
        raise HTTPException(status_code=500, detail="Failed to update road")
    return updated_road

@app.delete("/api/roads/{road_id}")
async def delete_road(road_id: str, db: Database = Depends(get_db)):
    # Check if road exists
    existing_road = await db.get_road_by_id(road_id)
    if not existing_road:
        raise HTTPException(status_code=404, detail="Road not found")
    
    # Delete the road
    success = await db.delete_road(road_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete road")
    return {"message": "Road successfully deleted"}

# ========== Device Endpoints ==========

@app.get("/api/devices", response_model=List[Device])
async def list_devices(db: Database = Depends(get_db)):
    devices = await db.get_all_devices()
    return devices

@app.post("/api/devices", response_model=Device)
async def create_device(device: Device, db: Database = Depends(get_db)):
    # Check if road exists
    road = await db.get_road_by_id(device.road_id)
    if not road:
        raise HTTPException(status_code=404, detail=f"Road with ID {device.road_id} not found")
    
    device_dict = device.dict(exclude={"id"})
    # Remove any None values for MongoDB
    device_dict = {k: v for k, v in device_dict.items() if v is not None}
    
    # Create the device
    created_device = await db.create_device(device_dict)
    return created_device

@app.get("/api/devices/{device_id}", response_model=Device)
async def get_device(device_id: str, db: Database = Depends(get_db)):
    device = await db.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@app.put("/api/devices/{device_id}", response_model=Device)
async def update_device(device_id: str, device: Device, db: Database = Depends(get_db)):
    # Check if device exists
    existing_device = await db.get_device_by_id(device_id)
    if not existing_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Check if road exists
    road = await db.get_road_by_id(device.road_id)
    if not road:
        raise HTTPException(status_code=404, detail=f"Road with ID {device.road_id} not found")
    
    # Prepare data for update
    device_dict = device.dict(exclude={"id"})
    device_dict = {k: v for k, v in device_dict.items() if v is not None}
    
    # Update the device
    updated_device = await db.update_device(device_id, device_dict)
    if not updated_device:
        raise HTTPException(status_code=500, detail="Failed to update device")
    return updated_device

@app.delete("/api/devices/{device_id}")
async def delete_device(device_id: str, db: Database = Depends(get_db)):
    # Check if device exists
    existing_device = await db.get_device_by_id(device_id)
    if not existing_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Delete the device
    success = await db.delete_device(device_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete device")
    return {"message": "Device successfully deleted"}

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    video_processor1.stop()
    video_processor2.stop()


if __name__ == "__main__":
    # Ensure we're in the correct directory
    os.chdir(BASE_DIR)
    # We'll run the application on PORT1, and each video processor will expose its stream on its own port
    uvicorn.run("main:app", host="0.0.0.0", port=PORT1, reload=True)