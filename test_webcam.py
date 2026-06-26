import cv2
from ultralytics import YOLO

# update lai duong dan chuan roi nha k so loi nua
model_path = r"runs\detect\train_chinh_thuc\weights\best_int_openvino_model"

# load cai model len, set task detect luon cho chac
model = YOLO(model_path, task='detect')

# bat cam cua laptop
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("toang roi k the bat duoc cam")
    exit()

print("dang load mo hinh openvino... an phim q de thoat")

while True:
    ret, frame = cap.read()
    if not ret:
        print("k nhan dc hinh anh tu cam")
        break

    # day frame vao model chay thoi
    results = model(frame, imgsz=640, conf=0.5, verbose=False)

    # lay ket qua ve cai box tren anh
    annotated_frame = results[0].plot()

    # show man hinh ket qua ra cho ae xem
    cv2.imshow("DATN Fire Detection - Test", annotated_frame)

    # bam q de thoat vong lap
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# don dep may cai tai nguyen cam cho may no nhe
cap.release()
cv2.destroyAllWindows()