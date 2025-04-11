# Backend AI for counting vehicle from video streaming 

## Note
Có thể là máy chưa cài đặt hoặc sử dụng GPU nên nó chậm hơn, nhưng chắc ko sao hehe tại yolov khá oke với CPU rồi
## Cài đặt và Chạy 

1.  **Clone Repository:**
    ```bash
    git clone https://github.com/CypriumCuprum/-Uni-Embedded_System_Development.git
    cd https://github.com/CypriumCuprum/-Uni-Embedded_System_Development.git
    ```
2.  **Tạo và Kích hoạt Môi trường ảo (Rất nên dùng hoặc tạo conda !!!):**
    ```bash
    python -m venv env
    or
    virtualenv env
    # Trên Linux/macOS
    source env/bin/activate
    # Trên Windows Chạy lệnh này để kích hoạt môi trường ảo vừa tạo
    .\env\Scripts\activate
    ```
3.  **Cài đặt library/dependency:**
    ```bash
    pip install -r requirements.txt
    ```
4.  Run main cứ file main mà run thế là xong hehehehe

## API Endpoints (Thanks Gemini 2.5 Pro kaka)

Ứng dụng cung cấp các endpoint sau (mặc định chạy trên `http://localhost:8081`):

---

### Giao diện người dùng và Video Stream

*   **`GET /`**
    *   **Mô tả:** Cung cấp trang HTML chính hiển thị luồng video đã xử lý và số liệu thống kê trực tiếp từ WebSocket.
    *   **Phản hồi:** `text/html`

*   **`GET /stream.mjpg`**
    *   **Mô tả:** Cung cấp luồng video đã xử lý dưới dạng MJPEG. Thích hợp để nhúng vào thẻ `<img>` trong HTML.
    *   **Phản hồi:** `multipart/x-mixed-replace; boundary=boundary`

---

### Cấu hình Video và Đường kẻ

*   **`POST /api/video/stream`**
    *   **Mô tả:** Cấu hình và khởi động (hoặc khởi động lại) quá trình xử lý video từ một nguồn mới (URL hoặc đường dẫn file cục bộ).
    *   **Request Body:** `string` (plain text) - Chứa URL hoặc đường dẫn file video.
    *   **Phản hồi thành công (200 OK):**
        ```json
        {
          "status": "success",
          "message": "Video stream configured"
        }
        ```
    *   **Phản hồi lỗi (500 Internal Server Error):** Nếu không thể mở stream.

*   **`POST /api/config/counting-line`**
    *   **Mô tả:** Thiết lập tọa độ cho đường kẻ dùng để đếm phương tiện.
    *   **Request Body (JSON):**
        *   `start`: List hoặc Tuple chứa tọa độ điểm bắt đầu `[x1, y1]`.
        *   `end`: List hoặc Tuple chứa tọa độ điểm kết thúc `[x2, y2]`.
        ```json
        {
          "start": [0, 360],
          "end": [1280, 360]
        }
        ```
    *   **Phản hồi thành công (200 OK):**
        ```json
        {
          "status": "success",
          "message": "Counting line set"
        }
        ```
    *   **Phản hồi lỗi (500 Internal Server Error):** Nếu có lỗi xảy ra.

---

### Trạng thái và Thống kê

*   **`GET /api/video/status`**
    *   **Mô tả:** Lấy trạng thái hiện tại của bộ xử lý video, bao gồm trạng thái chạy, số liệu đếm mới nhất và URL nguồn video đang được xử lý.
    *   **Phản hồi (200 OK):**
        ```json
        {
          "is_running": true,
          "current_counts": {
            "total_down": 15,
            "down_by_class": {
              "car": 8,
              "motorcycle": 5,
              "truck": 2,
              "bus": 0
            },
            "fps": 25.5
          },
          "stream_url": "D:\\Path\\To\\video\\vehicles.mp4"
        }
        ```
        *(Lưu ý: `is_running` có thể là `false`, `stream_url` có thể là `null`)*

*   **`GET /api/config/current`**
    *   **Mô tả:** Lấy cấu hình hiện tại đang được sử dụng, chủ yếu là tọa độ đường kẻ đếm. (Tracking area hiện chưa được triển khai đầy đủ).
    *   **Phản hồi (200 OK):**
        ```json
        {
          "tracking_area": null,
          "counting_line": [[0, 360], [1280, 360]]
        }
        ```
        *(Lưu ý: `tracking_area` có thể có cấu trúc khác nếu được triển khai, `counting_line` có thể là `null` nếu chưa được thiết lập)*

*   **`GET /api/stats/current`**
    *   **Mô tả:** Lấy số liệu thống kê đếm phương tiện mới nhất.
    *   **Phản hồi (200 OK):**
        ```json
        {
          "total_down": 15,
          "down_by_class": {
            "car": 8,
            "motorcycle": 5,
            "truck": 2,
            "bus": 0
          },
          "fps": 25.5
        }
        ```

*   **`GET /api/stats/history`**
    *   **Mô tả:** Lấy lịch sử số liệu đếm đã được ghi lại (nếu tính năng lưu history được bật và hoạt động trong `VideoProcessor`).
    *   **Phản hồi (200 OK):** `List[Dict]`
        ```json
        [
          {
            "timestamp": "2023-10-27T10:30:00.123456",
            "counts": {
              "total_down": 10,
              "down_by_class": {"car": 5, "motorcycle": 4, "truck": 1, "bus": 0},
              "fps": 26.1
            }
          },
          {
            "timestamp": "2023-10-27T10:30:01.123456",
            "counts": {
              "total_down": 11,
              "down_by_class": {"car": 5, "motorcycle": 5, "truck": 1, "bus": 0},
              "fps": 25.8
            }
          }
        ]
        ```

---

### WebSocket

*   **Path:** `/ws/stats`
*   **Mô tả:** Cung cấp một kênh giao tiếp WebSocket để gửi dữ liệu thống kê đếm phương tiện theo thời gian thực từ server đến client. Server sẽ gửi bản cập nhật khoảng mỗi giây.
*   **Định dạng tin nhắn (Server -> Client - JSON):**
    ```json
    {
      "total_down": 16,
      "down_by_class": {
        "car": 9,
        "motorcycle": 5,
        "truck": 2,
        "bus": 0
      },
      "fps": 25.9
    }
    ```

## TODO / Cải tiến tiềm năng

*   Thêm khả năng cấu hình vùng theo dõi (tracking area) phức tạp hơn (polygon).
*   Triển khai đếm phương tiện theo hướng đi lên ('up').
*   Xử lý lỗi và khôi phục kết nối mạnh mẽ hơn cho video stream và WebSocket.
*   Thêm xác thực API (ví dụ: API keys).
*   Cải thiện giao diện người dùng (frontend).
*   Thêm Unit Test và Integration Test.
*   Tối ưu hóa hiệu suất xử lý video.