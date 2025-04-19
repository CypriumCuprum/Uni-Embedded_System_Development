#include <WiFi.h>
#include <PubSubClient.h>

// pub: .\mosquitto_pub -h 172.20.10.10 -p 1889 -t traffic_lights/cycles -m "10000,4000,10000"
// sub: .\mosquitto_sub -h 172.20.10.10 -p 1889 -t traffic_light/cycles

// khai báo cột đèn giao thông
const char* road = "1";

// khai báo các topic mqtt
const char* mqtt_sub = "traffic_lights/cycles";
const char* mqtt_pub = "traffic_lights/noti";

// Khai báo thông tin Wi-Fi và MQTT Broker
const char* ssid = "nv.minh_";
const char* password = "1234567890";
const char* mqtt_server = "172.20.10.10"; // Thay đổi với địa chỉ IP của MQTT broker
const int mqtt_port = 1889;  // Cổng mặc định của MQTT broker

// Định nghĩa chân cho đèn giao thông
const int RED_LIGHT = 33;     // Đèn đỏ
const int YELLOW_LIGHT = 25;  // Đèn vàng
const int GREEN_LIGHT = 26;   // Đèn xanh

// Thời gian cho mỗi đèn (tính bằng mili giây)
int RED_TIME = 30000;      // Đèn đỏ 30 giây
int YELLOW_TIME = 5000;    // Đèn vàng 5 giây
int GREEN_TIME = 20000;    // Đèn xanh 20 giây

// Chu kỳ mới - sẽ áp dụng khi chu kỳ hiện tại kết thúc
int NEW_RED_TIME = 30000;
int NEW_YELLOW_TIME = 5000;
int NEW_GREEN_TIME = 20000;

// Biến cờ để kiểm tra xem có thay đổi chu kỳ mới không
bool cycleChanged = false;

// Chân LED 7 đoạn cho 5261BS
const int A = 15, B = 2, C = 4, D = 12, E = 27, F = 5, G = 18, DP = 19;
const int DIG1 = 22, DIG2 = 23;

// Mảng chứa chân LED
const int segments[] = {A, B, C, D, E, F, G, DP};
const int digits[] = {DIG1, DIG2};

// Mã hóa số (Common Anode - đảo ngược logic)
const byte numbers[10][7] = {
  {0, 0, 0, 0, 0, 0, 1}, // 0
  {1, 0, 0, 1, 1, 1, 1}, // 1
  {0, 0, 1, 0, 0, 1, 0}, // 2
  {0, 0, 0, 0, 1, 1, 0}, // 3
  {1, 0, 0, 1, 1, 0, 0}, // 4
  {0, 1, 0, 0, 1, 0, 0}, // 5
  {0, 1, 0, 0, 0, 0, 0}, // 6
  {0, 0, 0, 1, 1, 1, 1}, // 7
  {0, 0, 0, 0, 0, 0, 0}, // 8
  {0, 0, 0, 0, 1, 0, 0}  // 9
};

// Biến trạng thái cho đèn giao thông
enum TrafficState {RED, YELLOW, GREEN};
TrafficState currentState = RED;

// Biến thời gian
int countdown = RED_TIME / 1000;  // Ban đầu đếm ngược thời gian đèn đỏ (chuyển về giây)
unsigned long previousMillis = 0;
unsigned long lastPublishTime = 0;

WiFiClient espClient;
PubSubClient client(espClient);

// Hiển thị một chữ số
void displayDigit(int digit, int num) {
  // Tắt tất cả các chữ số trước (common anode nên đặt LOW để tắt)
  digitalWrite(DIG1, LOW);
  digitalWrite(DIG2, LOW);

  // Bật chữ số cần hiển thị (HIGH để bật với common anode)
  digitalWrite(digit, HIGH);

  // Hiển thị số num lên chữ số này
  for (int i = 0; i < 7; i++) {
    digitalWrite(segments[i], numbers[num][i]);
  }

  // Giữ digit này trong một khoảng thời gian ngắn để mắt người nhìn thấy
  delayMicroseconds(500);

  // Tắt chữ số để tránh chồng hình
  digitalWrite(digit, LOW);
}

// Hiển thị số hai chữ số
void displayNumber(int num) {
  // Giới hạn số từ 0-99
  num = constrain(num, 0, 99);
  
  int digit1 = num / 10;     // Chữ số hàng chục
  int digit2 = num % 10;     // Chữ số hàng đơn vị

  // Quét từng chữ số
  displayDigit(DIG1, digit1);
  displayDigit(DIG2, digit2);
}

// Cập nhật đèn giao thông và chuyển trạng thái
void updateTrafficLight() {
  // Nếu có thay đổi chu kỳ, áp dụng chu kỳ mới
  if (cycleChanged) {
    RED_TIME = NEW_RED_TIME;
    YELLOW_TIME = NEW_YELLOW_TIME;
    GREEN_TIME = NEW_GREEN_TIME;
    cycleChanged = false;
    
    Serial.println("Áp dụng chu kỳ mới:");
    Serial.print("Đèn Xanh: "); Serial.println(GREEN_TIME);
    Serial.print("Đèn Vàng: "); Serial.println(YELLOW_TIME);
    Serial.print("Đèn Đỏ: "); Serial.println(RED_TIME);
  }

  // Tắt tất cả đèn
  digitalWrite(RED_LIGHT, LOW);
  digitalWrite(YELLOW_LIGHT, LOW);
  digitalWrite(GREEN_LIGHT, LOW);

  // Xác định trạng thái tiếp theo và đặt thời gian đếm ngược
  switch (currentState) {
    case RED:
      // Khi đang là RED, chuyển sang GREEN
      currentState = GREEN;
      digitalWrite(GREEN_LIGHT, HIGH);
      countdown = GREEN_TIME / 1000;  // Chuyển đổi milis sang giây
      break;
      
    case GREEN:
      // Khi đang là GREEN, chuyển sang YELLOW
      currentState = YELLOW;
      digitalWrite(YELLOW_LIGHT, HIGH);
      countdown = YELLOW_TIME / 1000;  // Chuyển đổi milis sang giây
      break;
      
    case YELLOW:
      // Khi đang là YELLOW, chuyển sang RED
      currentState = RED;
      digitalWrite(RED_LIGHT, HIGH);
      countdown = RED_TIME / 1000;  // Chuyển đổi milis sang giây
      break;
  pubNoti()
  }
  
  Serial.print("Chuyển sang trạng thái: ");
  Serial.print(currentState);
  Serial.print(", Thời gian đếm ngược: ");
  Serial.println(countdown);
}

// Callback khi nhận được thông điệp từ MQTT
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.print("Nhận tin nhắn [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(message);
  
  // Xử lý thông điệp nhận được từ MQTT
  if (String(topic) == "traffic_lights/cycles") {
    // Tách thông số chu kỳ đèn từ thông điệp
    int greenTime = message.substring(0, message.indexOf(",")).toInt();
    message = message.substring(message.indexOf(",") + 1);
    
    int yellowTime = message.substring(0, message.indexOf(",")).toInt();
    message = message.substring(message.indexOf(",") + 1);
    
    int redTime = message.toInt();
    
    // Lưu chu kỳ mới vào biến tạm, sẽ áp dụng sau khi chu kỳ hiện tại kết thúc
    NEW_GREEN_TIME = greenTime;
    NEW_YELLOW_TIME = yellowTime;
    NEW_RED_TIME = redTime;
    cycleChanged = true;
    
    Serial.println("Đã nhận chu kỳ mới (sẽ áp dụng sau khi chu kỳ hiện tại kết thúc):");
    Serial.print("Đèn Xanh: "); Serial.println(NEW_GREEN_TIME);
    Serial.print("Đèn Vàng: "); Serial.println(NEW_YELLOW_TIME);
    Serial.print("Đèn Đỏ: "); Serial.println(NEW_RED_TIME);
  }
}

// Hàm để kết nối lại với MQTT broker nếu mất kết nối
void reconnect() {
  // Loop until we're reconnected
  int retries = 0;
  while (!client.connected() && retries < 5) {
    Serial.print("Đang kết nối MQTT...");
    if (client.connect("ESP32TrafficLight")) {
      Serial.println("kết nối thành công");
      client.subscribe(mqtt_sub);
    } else {
      Serial.print("lỗi, rc=");
      Serial.print(client.state());
      Serial.println(" thử lại sau 5 giây");
      delay(5000);
      retries++;
    }
  }
}

void pubNoti(){
  String colorStr;
  switch (currentState) {
      case RED:
        colorStr = "RED";
        break;
      case GREEN:
        colorStr = "GREEN";
        break;
      case YELLOW:
        colorStr = "YELLOW";
        break;
    }

    String message = road + ";" + colorStr + ";" + String(countdown);
    client.publish("mqtt_pub", message.c_str());
    
    Serial.print("Đã publish: ");
    Serial.println(message);
}

void setup() {
  Serial.begin(115200);

  // Cấu hình chân đèn giao thông
  pinMode(RED_LIGHT, OUTPUT);
  pinMode(YELLOW_LIGHT, OUTPUT);
  pinMode(GREEN_LIGHT, OUTPUT);

  // Cấu hình chân LED 7 đoạn
  for (int i = 0; i < 8; i++) {
    pinMode(segments[i], OUTPUT);
    digitalWrite(segments[i], HIGH); // Mặc định tắt tất cả các đoạn (HIGH với common anode)
  }

  pinMode(DIG1, OUTPUT);
  pinMode(DIG2, OUTPUT);
  digitalWrite(DIG1, LOW); // Mặc định tắt các chữ số (LOW với common anode)
  digitalWrite(DIG2, LOW);

  // Bắt đầu với đèn đỏ
  digitalWrite(RED_LIGHT, HIGH);
  digitalWrite(YELLOW_LIGHT, LOW);
  digitalWrite(GREEN_LIGHT, LOW);
  currentState = RED;
  countdown = RED_TIME / 1000;
  
  // Khởi tạo chu kỳ mới bằng giá trị mặc định
  NEW_RED_TIME = RED_TIME;
  NEW_YELLOW_TIME = YELLOW_TIME;
  NEW_GREEN_TIME = GREEN_TIME;
  
  // Kết nối Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Đang kết nối WiFi...");
    
    // Hiển thị đếm ngược trên LED trong khi đợi kết nối
    displayNumber(countdown);
  }
  Serial.println("Đã kết nối WiFi");
  
  // Kết nối với MQTT broker
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);
  
  Serial.print("Thời gian đèn Xanh: ");
  Serial.println(GREEN_TIME);
  Serial.print("Thời gian đèn Vàng: ");
  Serial.println(YELLOW_TIME);
  Serial.print("Thời gian đèn Đỏ: ");
  Serial.println(RED_TIME);
  
  Serial.println("Hệ thống đèn giao thông bắt đầu hoạt động");
}

void loop() {
  // Nếu không có dữ liệu mới từ MQTT, kết nối lại
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Cập nhật đồng hồ đếm ngược
  unsigned long currentMillis = millis();
  
  // Hiển thị số đếm ngược liên tục
  displayNumber(countdown);
  
  // Cập nhật đếm ngược mỗi giây
  if (currentMillis - previousMillis >= 1000) {
    previousMillis = currentMillis;
    
    if (countdown > 0) {
      countdown--;
    } else {
      // Chuyển sang trạng thái tiếp theo khi đếm ngược hết
      updateTrafficLight();
    }
  }

  // pub thông báo về server
  if (currentMillis - lastPublishTime >= 5000) {
    lastPublishTime = currentMillis;
    pubNoti()
  }
  
  // Thêm delay nhỏ để giảm flicker của LED
  delay(5);
}