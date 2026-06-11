# Hệ thống cảnh báo cháy sớm ứng dụng mô hình thu nhỏ chạy trên thiết bị nhúng và Hybrid Edge Cloud

Dự án xây dựng một giải pháp phát hiện và cảnh báo cháy sớm tối ưu hóa hiệu năng thời gian thực. Hệ thống sử dụng mô hình thị giác máy tính lượng tử hóa triển khai tại bộ định tuyến biên (Edge Gateway) kết hợp với hạ tầng truyền thông đám mây (Cloud Broker) để điều khiển cơ cấu chấp hành phần cứng tại mô hình thu nhỏ.

## 1. Kiến trúc hệ thống (Hybrid Edge Cloud)
* **Thiết bị đầu cuối (Edge Nodes):** ESP32-CAM đóng vai trò thu thập luồng dữ liệu hình ảnh (MJPEG Stream) độc lập qua môi trường mạng cục bộ (AP Mode).
* **Bộ điều khiển (Actuator Node):** Vi điều khiển ESP8266 (Wemos D1 Mini) nhận lệnh điều khiển thông qua giao thức truyền thông MQTT.
* **Cổng xử lý biên (Edge Gateway):** Máy tính cá nhân thực thi mô hình nhận diện được tối ưu hóa đồ thị tính toán bằng bộ công cụ OpenVINO (định dạng cấu trúc `INT8`), đảm bảo tốc độ đáp ứng thời gian thực (FPS cao) trên kiến trúc CPU x86.
* **Hạ tầng đám mây (Cloud Components):** Cloud MQTT Broker (HiveMQ Cloud) quản lý, định tuyến và phân phối các gói tin điều khiển trạng thái hệ thống bảo mật qua Port 8883.

## 2. Cấu trúc thư mục dự án
```text
Output/
├── dataset/                      # Tập dữ liệu hình ảnh khói/lửa (được bỏ qua qua .gitignore)
├── runs/
│   └── detect/
│       └── train_chinh_thuc/     # Kết quả huấn luyện mô hình YOLOv8s 150 Epochs
│           └── weights/
│               ├── best_int_openvino_model/   # Mô hình chuẩn định dạng OpenVINO INT8
│               │   ├── best.xml
│               │   └── best.bin
│               ├── best.pt       # Trọng số gốc PyTorch FP16
│               └── best.onnx     # Mô hình xuất định dạng ONNX FP32
├── esp32_cam_source/             # Mã nguồn C++ nạp cho vi điều khiển ESP32-CAM
├── test_webcam.py                # Kịch bản thực thi kiểm thử luồng hình ảnh thời gian thực
├── .gitignore                    # Các tệp ngoại trừ khi đồng bộ Git
└── README.md                     # Tài liệu hướng dẫn hệ thống

## 3. Hướng dẫn cài đặt và vận hành

### Yêu cầu hệ thống
* Python 3.10 hoặc cao hơn
* Trình biên dịch Arduino IDE (cho phần mã nguồn nhúng)

### Các bước khởi chạy bộ định tuyến biên

1. Khởi tạo và kích hoạt môi trường ảo Python:
```bash
python -m venv venv
.\venv\Scripts\activate
Cài đặt các gói thư viện phụ thuộc:

```bash
pip install ultralytics openvino opencv-python
Kết nối vào mạng không dây do ESP32-CAM phát ra (ESP32_CAM_HOTSPOT), sau đó thực thi kịch bản xử lý kiểm thử:

```bash
python test_webcam.py
