import cv2
import time
import requests
import numpy as np
from ultralytics import YOLO

# update laj dduog ddan chuan k loj nua
model_path = r"runs\detect\train_chinh_thuc\weights\best_int_openvino_model"
model = YOLO(model_path, task='detect')

# THAY ddoj: ddam bao ddug IP moj lay tu serial monitor
stream_url = "http://192.168.1.15/stream"

print("dang ket noj qua thu vjen requests... an q dde thoat")

def run_detection():
    while True:
        try:
            # dung requests stream dde lay doc tung chunk byte
            r = requests.get(stream_url, stream=True, timeout=5)
            if r.status_code != 200:
                print("ko the lay luog video, thuj thu laj sau 2s...")
                time.sleep(2)
                continue
            
            bytes_data = b''
            for chunk in r.iter_content(chunk_size=1024):
                bytes_data += chunk
                
                # tjm ddm dau va cuoj cua 1 file anh jpeg
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')
                
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    
                    # decode mang byte thanh frame anh opencv
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    
                    if frame is None:
                        continue
                        
                    # dday frame vao yolo conf 0.5 de thuc thj detect
                    results = model(frame, imgsz=640, conf=0.5, verbose=False)
                    
                    # Ve box mac dinh cua YOLO
                    annotated_frame = results[0].plot()
                    
                    # ==========================================
                    # LOGIC BÓC TÁCH NHÃN KHÓI / LỬA
                    # ==========================================
                    fire_detected = False
                    smoke_detected = False
                    
                    for box in results[0].boxes:
                        cls_id = int(box.cls[0])
                        # Kiem tra ID class (0 thuong la lua, 1 thuong la khoi)
                        if cls_id == 0:
                            fire_detected = True
                        elif cls_id == 1:
                            smoke_detected = True
                            
                    # Ve canh bao rieng biet len goc man hinh
                    if fire_detected:
                        cv2.putText(annotated_frame, "WARNING: FIRE DETECTED!", (30, 50), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3, cv2.LINE_AA)
                                    
                    if smoke_detected:
                        cv2.putText(annotated_frame, "WARNING: SMOKE DETECTED!", (30, 90), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 3, cv2.LINE_AA)
                    
                    # Hien thi video
                    cv2.imshow("DATN Fire Detection - ESP32 Requests", annotated_frame)
                    
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    return
        except Exception as e:
            print(f"Loj doc stream hoac mat mang: {e}, ddoi 2s dde reconnect...")
            time.sleep(2)

if __name__ == "__main__":
    run_detection()
    cv2.destroyAllWindows()