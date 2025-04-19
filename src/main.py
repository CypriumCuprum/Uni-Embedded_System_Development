from fastapi import FastAPI, WebSocket, HTTPException, Body, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from typing import List, Dict, Tuple
import uvicorn
from config import settings
from database import get_database
from models import VehicleCount, AreaConfig, CountingLineConfig
from video_processor import VideoProcessor
from websocket_manager import WebSocketManager
import asyncio
import os
from pydantic import BaseModel
from mqtt_client import MQTTClient

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

# Initialize components
video_processor = VideoProcessor()
loop = asyncio.get_event_loop()
mqtt_client = MQTTClient(loop)

# Define request models
class CountingLineRequest(BaseModel):
    start: List[int]
    end: List[int]

@app.on_event("startup")
async def startup_event():
    mqtt_client.connect()
    # mqtt_client.publish(settings.mqtt_topic_pub, "30000;5000;20000")

    """Initialize video processing on server startup"""
    try:
        # Set up counting line (horizontal line at the middle of the frame)
        line_start = (0, settings.frame_height*3 // 4)  # Start from left side
        line_end = (settings.frame_width, settings.frame_height*3 // 4)  # End at right side
        video_processor.set_counting_line(line_start, line_end)
        
        # Start processing video stream
        # stream_url = "http://localhost:8080/stream.mjpg"
        stream_url = "D:\CUPRUM\PTIT\Term_8\Embedded_System_Development\BE_AI\\video\\vehicles.mp4"
        # stream_url = "http://192.168.1.10:8080/?action=stream"
        await video_processor.start_stream(stream_url)
        print("Video processing started automatically")
        print(f"Processed video stream available at: {video_processor.get_stream_url()}")
    except Exception as e:
        print(f"Error starting video processing: {e}")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with HTML page showing the video stream"""
    html_content = """
    <html>
        <head>
            <title>Vehicle Counting System</title>
            <style>
                body { margin: 0; background: #000; color: white; font-family: Arial, sans-serif; }
                .container { display: flex; flex-direction: column; align-items: center; padding: 20px; }
                .video-container { margin: 20px 0; border: 1px solid #555; }
                img { display: block; max-width: 100%; height: auto; }
                .stats { margin-top: 15px; text-align: left; width: 80%; max-width: 600px; }
                .stats h2 { text-align: center; margin-bottom: 10px; }
                .stats p { margin: 5px 0; font-size: 1.1em; }
                .stats ul { list-style: none; padding-left: 20px; }
                .stats li { margin: 3px 0; }
                #fps { font-weight: bold; }
                #total-down-count { font-weight: bold; color: #00ff00; /* Green for total */ }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Vehicle Counting System</h1>
                <div class="video-container">
                    <img src="/stream.mjpg" alt="Video Stream" id="video-stream">
                </div>
                <div class="stats">
                    <h2>Live Statistics</h2>
                    <p>Total Vehicles Down: <span id="total-down-count">0</span></p>
                    <p>FPS: <span id="fps">0.0</span></p>
                    <h3>Counts by Vehicle Type (Down):</h3>
                    <ul id="down-by-class-list">
                        <!-- Counts by class will be populated here by JS -->
                         <li>Loading...</li>
                    </ul>
                </div>
            </div>
            <script>
                const ws_protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const ws_url = `${ws_protocol}//${window.location.host}/ws/stats`;
                console.log(`Attempting to connect WebSocket to: ${ws_url}`);
                const ws = new WebSocket(ws_url);

                // Get references to HTML elements
                const totalDownElement = document.getElementById('total-down-count');
                const fpsElement = document.getElementById('fps');
                const downByClassListElement = document.getElementById('down-by-class-list');
                const videoElement = document.getElementById('video-stream');

                ws.onopen = function(event) {
                    console.log("WebSocket connection opened");
                    downByClassListElement.innerHTML = ''; // Clear loading message
                };

                ws.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        // console.log("Received data:", data); // Debugging line

                        // Update Total Down Count
                        if (data.total_down !== undefined) {
                            totalDownElement.textContent = data.total_down;
                        } else {
                            totalDownElement.textContent = 'N/A';
                        }

                        // Update FPS
                        if (data.fps !== undefined) {
                            fpsElement.textContent = data.fps.toFixed(1);
                        } else {
                            fpsElement.textContent = 'N/A';
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
                            if (downByClassListElement.innerHTML !== listHtml) {
                               downByClassListElement.innerHTML = listHtml;
                            }
                        } else {
                             if (downByClassListElement.innerHTML !== '<li>Data not available</li>') {
                                downByClassListElement.innerHTML = '<li>Data not available</li>';
                             }
                        }

                    } catch (e) {
                        console.error("Error processing WebSocket message:", e);
                        console.error("Received raw data:", event.data);
                        downByClassListElement.innerHTML = '<li>Error loading data</li>';
                    }
                };

                ws.onerror = function(event) {
                    console.error("WebSocket error observed:", event);
                    totalDownElement.textContent = 'Error';
                    fpsElement.textContent = 'Error';
                    downByClassListElement.innerHTML = '<li>WebSocket Error</li>';
                };

                ws.onclose = function(event) {
                    console.log(`WebSocket connection closed: Code=${event.code}, Reason=${event.reason}, WasClean=${event.wasClean}`);
                    totalDownElement.textContent = 'Disconnected';
                    fpsElement.textContent = 'N/A';
                    downByClassListElement.innerHTML = '<li>Connection Closed</li>';
                    // Optional: Add reconnect logic here if needed
                    // setTimeout(connectWebSocket, 5000);
                };

                // Optional: Handle image loading errors
                videoElement.onerror = function() {
                    console.error("Failed to load video stream.");
                    // You could display a placeholder image or message
                }

                // function connectWebSocket() { // Example reconnect function
                //    console.log("Attempting to reconnect WebSocket...");
                //    const newWs = new WebSocket(ws_url);
                //    // Re-assign ws handlers if needed, or manage state differently
                // }

            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/stream.mjpg")
async def video_stream():
    """Stream the processed video feed"""
    return StreamingResponse(
        video_processor.generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=boundary"
    )

@app.post("/api/video/stream")
async def configure_video_stream(stream_url: str):
    """Configure and start video stream processing"""
    try:
        await video_processor.start_stream(stream_url)
        return {"status": "success", "message": "Video stream configured"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/video/status")
async def get_stream_status():
    """Get current stream status"""
    return {
        "is_running": video_processor.is_running,
        "current_counts": video_processor.get_counts(),
        "stream_url": video_processor.get_stream_url()
    }

# @app.post("/api/config/area")
# async def set_tracking_area(config: AreaConfig):
#     try:
#         video_processor.set_tracking_area(config)
#         return {"status": "success", "message": "Tracking area configured"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config/counting-line")
async def set_counting_line(config: CountingLineRequest):
    """Set the counting line coordinates"""
    try:
        # Convert lists to tuples
        start = tuple(config.start)
        end = tuple(config.end)
        video_processor.set_counting_line(start, end)
        return {"status": "success", "message": "Counting line set"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/current")
async def get_current_config():
    return {
        "tracking_area": video_processor.get_tracking_area(),
        "counting_line": video_processor.get_counting_line()
    }

@app.get("/api/stats/current")
async def get_current_stats():
    """Get current counting statistics"""
    return video_processor.get_counts()

@app.get("/api/stats/history")
async def get_count_history():
    """Get historical count data"""
    return video_processor.get_count_history()

@app.websocket("/ws/stats")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time count updates"""
    await websocket.accept()
    client_host = websocket.client.host
    client_port = websocket.client.port
    print(f"WebSocket connection accepted from: {client_host}:{client_port}")
    try:
        while True:
            # Send current counts every second
            data_to_send = video_processor.get_counts()
            await websocket.send_json(data_to_send)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        # Client đã đóng kết nối, đây là trường hợp bình thường
        print(f"Client disconnected: {client_host}:{client_port}")
        # Không cần gọi websocket.close() ở đây vì kết nối đã đóng/đang đóng
    except asyncio.CancelledError:
        # Xử lý trường hợp task bị hủy (ví dụ: khi server tắt)
        print(f"WebSocket task cancelled for: {client_host}:{client_port}")
        # Không cần đóng ở đây nếu server đang tắt, nhưng có thể nếu muốn
    except Exception as e:
        # Xử lý các lỗi không mong muốn khác
        print(f"WebSocket error for {client_host}:{client_port}: {e} ({type(e).__name__})")
        # Trong trường hợp lỗi khác, cố gắng đóng kết nối một cách lịch sự
        try:
            await websocket.close(code=1011) # Mã lỗi 1011: Internal Server Error
        except RuntimeError as re:
            # Có thể vẫn xảy ra lỗi nếu kết nối bị hỏng hoàn toàn
            print(f"Could not close WebSocket cleanly after error for {client_host}:{client_port}: {re}")
        except Exception as close_exc:
            print(f"Unexpected error during WebSocket close after exception for {client_host}:{client_port}: {close_exc}")
    finally:
        # Khối finally vẫn sẽ chạy, nhưng chúng ta đã xử lý việc đóng kết nối
        # trong các khối except khi cần thiết. Có thể dùng để dọn dẹp tài nguyên khác nếu có.
        print(f"WebSocket handler finished for: {client_host}:{client_port}")
        # Không gọi websocket.close() ở đây nữa để tránh lỗi runtime.

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    video_processor.stop()

if __name__ == "__main__":
    # Ensure we're in the correct directory
    os.chdir(BASE_DIR)
    uvicorn.run("main:app", host="0.0.0.0", port=video_processor.stream_port, reload=True) 