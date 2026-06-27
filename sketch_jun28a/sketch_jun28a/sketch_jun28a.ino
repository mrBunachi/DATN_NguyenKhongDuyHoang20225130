#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

// ================= CẤU HÌNH WIFI =================
const char* ssid = "TEN_WIFI_CUA_BAN";
const char* password = "MAT_KHAU_WIFI";

// ================= CẤU HÌNH HIVEMQ =================
const char* mqtt_server = "5b6c0074c8424a62bebd26403a6e75a7.s1.eu.hivemq.cloud";
const int mqtt_port = 8883; 
const char* mqtt_user = "HoangSub1";
const char* mqtt_pass = "MAT_KHAU_CUA_HOANGSUB1"; // Điền mật khẩu của bạn
const char* mqtt_topic = "datn";

// ================= CẤU HÌNH PHẦN CỨNG =================
const int RED_PIN = D1;
const int YELLOW_PIN = D2;

// ================= BIẾN TOÀN CỤC =================
WiFiClientSecure espClient;
PubSubClient client(espClient);

unsigned long last_mqtt_time = 0;
const unsigned long TIMEOUT = 15000; // 15 giây (15000 ms)

void setup_wifi() {
  delay(10);
  Serial.print("Đang kết nối WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi đã kết nối!");
}

void callback(char* topic, byte* payload, unsigned int length) {
  // 1. Reset biến đếm thời gian ngay khi nhận được tín hiệu
  last_mqtt_time = millis();
  
  // 2. Chuyển đổi payload thành String
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.print("Nhận tín hiệu từ topic [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(message);

  // 3. Xử lý logic bật/tắt đèn
  if (message == "ON") {
    digitalWrite(RED_PIN, HIGH);  // Bật báo cháy
    digitalWrite(YELLOW_PIN, LOW); // Tắt báo lỗi
  } 
  else if (message == "OFF") {
    digitalWrite(RED_PIN, LOW);   // Tắt báo cháy
    digitalWrite(YELLOW_PIN, LOW); // Tắt báo lỗi
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Đang kết nối tới MQTT Broker... ");
    // Tạo client ID ngẫu nhiên
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
      Serial.println("Thành công!");
      client.subscribe(mqtt_topic);
      // Khi vừa kết nối lại, reset mốc thời gian để tránh báo lỗi vàng giả
      last_mqtt_time = millis(); 
    } else {
      Serial.print("Thất bại, mã lỗi (rc)=");
      Serial.print(client.state());
      Serial.println(". Thử lại sau 5 giây.");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  pinMode(RED_PIN, OUTPUT);
  pinMode(YELLOW_PIN, OUTPUT);
  
  // Khởi tạo trạng thái tắt cho cả 2 đèn
  digitalWrite(RED_PIN, LOW);
  digitalWrite(YELLOW_PIN, LOW);

  setup_wifi();

  // Bỏ qua xác thực chứng chỉ SSL/TLS (Phù hợp cho vi điều khiển cấu hình thấp)
  espClient.setInsecure(); 
  
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop(); // Lắng nghe gói tin đến

  // Kiểm tra điều kiện Timeout (15s không nhận được tín hiệu)
  // Việc dùng phép trừ (millis() - last_mqtt_time) giúp tránh lỗi tràn biến (overflow)
  if (millis() - last_mqtt_time > TIMEOUT) {
    digitalWrite(RED_PIN, LOW);    // Tắt báo cháy (vì dữ liệu đã cũ, không còn tin cậy)
    digitalWrite(YELLOW_PIN, HIGH); // Bật đèn vàng cảnh báo mất kết nối/hệ thống bất định
  }
}