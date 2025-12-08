# server.py

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import base64
import numpy as np
import cv2
import os
import time
import warnings
import uvicorn

from src.anti_spoof_predict import AntiSpoofPredict
from src.generate_patches import CropImage
from src.utility import parse_model_name

warnings.filterwarnings("ignore")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Constants =====
MODEL_DIR = "./resources/anti_spoof_models"
DEVICE_ID = 0

# Initialize model classes
model_test = AntiSpoofPredict(DEVICE_ID)
image_cropper = CropImage()

# ===== Base64 Decode Utility =====
def decode_base64_image(data: str) -> np.ndarray:
    header, encoded = data.split(",", 1) if "," in data else ("", data)
    img_bytes = base64.b64decode(encoded)
    img_np = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    return img

# ===== Image Dimension Check =====
def check_image(image):
    height, width, channel = image.shape
    if round(width / height, 2) != 3 / 4:
        return False
    return True

# ===== Request Schema =====
class ImageBase64Request(BaseModel):
    images: List[str]  # base64 strings

# ===== Endpoint =====
@app.post("/detect-liveness-base64")
async def detect_liveness_base64(payload: ImageBase64Request):
    results = []

    for idx, img_b64 in enumerate(payload.images):
        try:
            image = decode_base64_image(img_b64)
        except Exception:
            results.append({
                "index": idx,
                "error": "Invalid base64 image"
            })
            continue

        if not check_image(image):
            results.append({
                "index": idx,
                "error": "Invalid image aspect ratio. Required 4:3"
            })
            continue

        try:
            image_bbox = model_test.get_bbox(image)
            prediction = np.zeros((1, 3))
            test_speed = 0

            for model_name in os.listdir(MODEL_DIR):
                h_input, w_input, model_type, scale = parse_model_name(model_name)
                param = {
                    "org_img": image,
                    "bbox": image_bbox,
                    "scale": scale,
                    "out_w": w_input,
                    "out_h": h_input,
                    "crop": False,
                }
                if scale is None:
                    param["crop"] = False
                img = image_cropper.crop(**param)
                start = time.time()
                prediction += model_test.predict(img, os.path.join(MODEL_DIR, model_name))
                test_speed += time.time() - start

            label = int(np.argmax(prediction))
            value = float(prediction[0][label] / 2)
            result_label = "real" if label == 1 else "fake"

            results.append({
                "index": idx,
                "label": result_label,
                "score": value,
                "bbox": {
                    "x": int(image_bbox[0]),
                    "y": int(image_bbox[1]),
                    "w": int(image_bbox[2]),
                    "h": int(image_bbox[3]),
                },
                "inference_time": round(test_speed, 2)
            })
        except Exception as e:
            results.app
            
    return JSONResponse(content={"results": results})

if __name__ == "__main__":
    uvicorn.run(
        "server:app", # format: filename:FastAPI_instance
        host="0.0.0.0",
        port=8000,
    )
