from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = BASE_DIR / "models" / "trained" / "segmentv3.pt"

model = YOLO(str(MODEL_PATH))

IMAGE_PATH = r"C:\Programming\real-2.jpg"

ROI_AREA_M2 = 0.0413  
AVG_WORM_AREA = 386  # average worm pixel area (fixed camera height)

frame = cv2.imread(IMAGE_PATH)

if frame is None:
    print("❌ Image not found or cannot be read")
    exit()

h, w, _ = frame.shape

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

    larvae_per_m2 = final_count / ROI_AREA_M2
    larvae_per_cm2 = larvae_per_m2 / 10000  # ✅ conversion

    print("Mask count:", mask_count)
    print("Area estimated count:", round(area_est_count, 2))
    print("Estimated Larva Count:", final_count)
    print("Larvae per cm²:", round(larvae_per_cm2, 2))

    if larvae_per_cm2 > 1.25:
        print("Alert!! Larva Density is High ",round(larvae_per_cm2,2), "/cm2" )
    
    else:
        print("Healthy Density")

else:
    final_count = 0
    larvae_per_m2 = 0
    larvae_per_cm2 = 0
    print("No larvae detected")

annotated_frame = results.plot(line_width=2)   
#annotated_frame = results.plot(boxes=False)

cv2.putText(
    annotated_frame,
    f"Estimated Larvae Count: {final_count}",
    (20, 40),
    cv2.FONT_HERSHEY_SIMPLEX,
    1,
    (0, 255, 0),
    2
)

cv2.putText(
    annotated_frame,
    f"Larvae/cm2: {larvae_per_cm2:.2f} /cm2",
    (20, 120),
    cv2.FONT_HERSHEY_SIMPLEX,
    1,
    (0, 255, 0),
    2
)

cv2.namedWindow("YOLO Segmentation Result", cv2.WINDOW_NORMAL)
cv2.resizeWindow("YOLO Segmentation Result", 640, 640)

cv2.imshow("YOLO Segmentation Result", annotated_frame)
cv2.waitKey(0)
cv2.destroyAllWindows()
