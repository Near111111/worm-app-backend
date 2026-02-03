from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = BASE_DIR / "models" / "trained" / "segmentv3.pt"

model = YOLO(str(MODEL_PATH))

ROI_AREA_CM2 = 413
ROI_AREA_M2 = ROI_AREA_CM2 / 10000

AVG_WORM_AREA = 386

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280) #adjustable
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720) #adjustable

if not cap.isOpened():
    print("❌ Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, imgsz=640, conf=0.4, verbose=False)[0]

    mask_count = 0
    total_mask_area = 0

    if results.masks is not None:
        masks = results.masks.data.cpu().numpy()

        for mask in masks:
            area = np.sum(mask)
            if area > 50:
                mask_count += 1
                total_mask_area += area

        area_est_count = total_mask_area / AVG_WORM_AREA if AVG_WORM_AREA > 0 else 0
        final_count = int(max(mask_count, area_est_count))

        larvae_per_cm2 = final_count / ROI_AREA_CM2
        larvae_per_m2 = final_count / ROI_AREA_M2

        if larvae_per_cm2 > 1.25:
            print("Alert!! Larva Density is High ",round(larvae_per_cm2,2), "/cm2" )
        
        else:
            print("Healthy Density")

    else:
        final_count = 0
        larvae_per_cm2 = 0
        larvae_per_m2 = 0

    annotated_frame = results.plot()

    cv2.putText(annotated_frame, f"Larvae: {final_count}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.putText(annotated_frame, f"Larvae/cm2: {larvae_per_cm2:.2f}", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.putText(annotated_frame, f"Larvae/m2: {larvae_per_m2:.1f}", (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    display = cv2.resize(annotated_frame, (1366, 768))
    cv2.imshow("YOLO Live Larva Counter (cm2)", display)

    if cv2.waitKey(1) & 0xFF == 27: 
        break

cap.release()
cv2.destroyAllWindows()
