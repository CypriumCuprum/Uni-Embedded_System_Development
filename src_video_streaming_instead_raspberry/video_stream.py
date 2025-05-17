import cv2
import numpy as np
from flask import Flask, Response
import threading
import time
import argparse

app = Flask(__name__)

# Global variables
camera = None
is_running = True
frame_width = 720
frame_height = 1280
fps = 25
port = 8678

def init_camera():
    """Initialize the camera"""
    global camera
    # camera = cv2.VideoCapture(0)  # 0 is usually the default webcam
    camera = cv2.VideoCapture("D:\CUPRUM\PTIT\Term_8\Embedded_System_Development\BE_AI\\video\\video_20250516_170346.mp4")  # Use the first camera device
    if not camera.isOpened():
        raise Exception("Could not open camera")
    # Set resolution and FPS
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    camera.set(cv2.CAP_PROP_FPS, fps)

def generate_frames():
    """Generate frames from camera"""
    global is_running
    while is_running:
        success, frame = camera.read()
        if not success:
            break
        # Convert frame to JPEG format with quality 85 for better performance
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_bytes = buffer.tobytes()
        yield (b'--boundary\r\n'
               b'Content-Type: image/jpeg\r\n'
               b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
               frame_bytes + b'\r\n')
        time.sleep(1.0/fps)  # Maintain specified FPS

@app.route('/')
def stream():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=boundary')

@app.route('/root')
def index():
    """Serve a simple page with the video stream"""
    return """
    <html>
        <head>
            <title>MJPEG Stream</title>
            <style>
                body { margin: 0; background: #000; }
                img { width: 100%; height: 100vh; object-fit: contain; }
            </style>
        </head>
        <body>
            <img src="/stream.mjpg" alt="Video Stream">
        </body>
    </html>
    """

def main():
    """Main function"""
    global is_running, frame_width, frame_height, fps, port
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='MJPEG Streamer')
    parser.add_argument('-r', '--resolution', default='1280x720',
                      help='Resolution (widthxheight)')
    parser.add_argument('-f', '--fps', type=int, default=30,
                      help='Frames per second')
    parser.add_argument('-p', '--port', type=int, default=8678,
                      help='Port number')
    
    args = parser.parse_args()
    
    # Parse resolution
    try:
        frame_width, frame_height = map(int, args.resolution.split('x'))
    except:
        print("Invalid resolution format. Use widthxheight (e.g., 1280x720)")
        return
    
    fps = args.fps
    port = args.port
    
    try:
        # Initialize camera
        init_camera()
        print(f"Starting MJPEG streamer on port {port}")
        print(f"Resolution: {frame_width}x{frame_height} @ {fps} FPS")
        
        # Run Flask server
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        is_running = False
        if camera is not None:
            camera.release()

if __name__ == '__main__':
    main() 