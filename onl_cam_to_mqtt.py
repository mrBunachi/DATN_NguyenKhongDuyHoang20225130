import cv2
import time
import requests
import numpy as np
from ultralytics import YOLO
import paho.mqtt.client as mqtt
import ssl

# ==========================================
# CẤU HÌNH HIVEMQ CLOUD (TLS)
# ==========================================
BROKER = "5b6c0074c8424a62bebd26403a6e75a7.s1.eu.hivemq.cloud" # Lấy từ Cluster URL của bạn
PORT = 8883
USERNAME = "HoangPub1"
PASSWORD = "HoangPub1" # Hãy điền password của credentials vào đây
TOPIC = "datn"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Đã kết nối thành công tới HiveMQ Cloud!")
    else:
        print(f"[MQTT] Kết nối thất bại, mã lỗi: {rc}")

# Khởi tạo client MQTT
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS) # Bắt buộc phải có khi dùng HiveMQ Cloud Port 8883
client.on_connect = on_connect
client.connect(BROKER, PORT, 60)
client.loop_start() # Chạy thread ngầm xử lý mạng

# ==========================================
# CẤU HÌNH YOLO & CAMERA
# ==========================================
model_path = r"runs\detect\train_chinh_thuc\weights\best_int_openvino_model"
model = YOLO(model_path, task='detect')
# Link này có thể thay đổi, cần check lại trong arduino ide
stream_url = "http://192.168.1.15/stream"

print("Đang kết nối qua thư viện requests... ấn q để thoát")

def run_detection():
    last_process_time = 0
    interval = 5.0 # Chu kỳ 5 giây
    
    # Biến lưu trạng thái hiển thị
    fire_detected = False
    smoke_detected = False

    while True:
        try:
            r = requests.get(stream_url, stream=True, timeout=5)
            if r.status_code != 200:
                print("Không thể lấy luồng video, thử lại sau 2s...")
                time.sleep(2)
                continue
            
            bytes_data = b''
            for chunk in r.iter_content(chunk_size=1024):
                bytes_data += chunk
                
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')
                
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    
                    if frame is None:
                        continue
                    
                    current_time = time.time()
                    
                    # ---------------------------------------------------------
                    # 1. TRÍCH XUẤT MÔ HÌNH VÀ PUBLISH MQTT MỖI 5 GIÂY
                    # ---------------------------------------------------------
                    if current_time - last_process_time >= interval:
                        # Đưa frame vào YOLO
                        results = model(frame, imgsz=640, conf=0.5, verbose=False)
                        
                        # Reset trạng thái mỗi lần quét
                        fire_detected = False
                        smoke_detected = False
                        
                        for box in results[0].boxes:
                            cls_id = int(box.cls[0])
                            if cls_id == 0:
                                fire_detected = True
                            elif cls_id == 1:
                                smoke_detected = True
                        
                        # Publish tín hiệu lên Broker (kèm retain=True)
                        if fire_detected:
                            client.publish(TOPIC, "ON", qos=1, retain=True)
                            print(f"[{time.strftime('%H:%M:%S')}] MQTT Sent: ON")
                        else:
                            client.publish(TOPIC, "OFF", qos=1, retain=True)
                            print(f"[{time.strftime('%H:%M:%S')}] MQTT Sent: OFF")
                            
                        last_process_time = current_time

                    # ---------------------------------------------------------
                    # 2. XỬ LÝ HIỂN THỊ VIDEO (Chạy liên tục không chờ 5s)
                    # ---------------------------------------------------------
                    display_frame = frame.copy()
                    
                    if fire_detected:
                        cv2.putText(display_frame, "WARNING: FIRE DETECTED!", (30, 50), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3, cv2.LINE_AA)
                                    
                    if smoke_detected:
                        cv2.putText(display_frame, "WARNING: SMOKE DETECTED!", (30, 90), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 3, cv2.LINE_AA)
                    
                    cv2.imshow("DATN Fire Detection - ESP32 Requests", display_frame)
                    
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    client.loop_stop() # Dừng luồng MQTT trước khi thoát
                    return
        except Exception as e:
            print(f"Lỗi đọc stream hoặc mất mạng: {e}, đợi 2s để reconnect...")
            time.sleep(2)

if __name__ == "__main__":
    # Nhớ cài đặt thư viện trước khi chạy: pip install paho-mqtt
    run_detection()
    cv2.destroyAllWindows()