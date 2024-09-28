from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from ultralytics import YOLO
from app.logging.logger import logger
import easyocr
import pytesseract
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont
import io
import easyocr
import numpy as np
import os
import base64
router = APIRouter()

current_dir = os.path.dirname(os.path.abspath(__file__))
# Set the model directory in your project
MODEL_DIR = os.path.join(current_dir, "ocr_model")
tesseract_path = os.path.join(current_dir, 'Tesseract-OCR', 'tesseract.exe')

# Ensure the model directory exists
os.makedirs(MODEL_DIR, exist_ok=True)

# Set the environment variable for model download location
os.environ['EASYOCR_MODULE_PATH'] = MODEL_DIR

# Load the YOLO model
model = YOLO('yolov8n.pt')
model_8x = YOLO('yolov8x.pt')
pytesseract.pytesseract.tesseract_cmd = tesseract_path

@router.get("/")
async def health_check():
    return {"message": "Welcome to the Object Detection API"}

@router.post("/detect/")
async def detect_objects(file: UploadFile = File(...), model = model):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Perform object detection
        results = model(image)
        
        # Draw bounding boxes and labels on the image
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        
        width, height = image.size
        
        detected_objects = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                try:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    # Ensure coordinates are valid and within image boundaries
                    x1 = max(0, min(x1, width - 1))
                    x2 = max(0, min(x2, width - 1))
                    y1 = max(0, min(y1, height - 1))
                    y2 = max(0, min(y2, height - 1))
                    
                    # Ensure x1 < x2 and y1 < y2
                    x1, x2 = min(x1, x2), max(x1, x2)
                    y1, y2 = min(y1, y2), max(y1, y2)
                    
                    # Skip if the box has no area
                    if x1 == x2 or y1 == y2:
                        logger.warning(f"Skipping zero-area box: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
                        continue
                    
                    class_id = int(box.cls)
                    conf = float(box.conf)
                    label = f"{result.names[class_id]} {conf:.2f}"
                    
                    # Draw bounding box
                    draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
                    
                    # Draw label
                    text_width = draw.textlength(label, font=font)
                    text_height = font.size
                    draw.rectangle([x1, y1 - text_height, x1 + text_width, y1], fill="red")
                    draw.text((x1, y1 - text_height), label, fill="white", font=font)
                    
                    detected_objects.append({
                        "class": result.names[class_id],
                        "confidence": round(conf, 2),
                        "bbox": [x1, y1, x2, y2]
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing box: {e}")
                    continue
        
        # Save the image to a bytes buffer
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Encode the image as base64
        encoded_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        
        # Prepare the response
        return JSONResponse(content={
            "image": encoded_image,
            "objects": detected_objects
        })
    
    except Exception as e:
        logger.error(f"Error in detect_objects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect-8x-img/")
async def detect_objects_8x(file: UploadFile = File(...)):
    return await detect_objects_img(file, model=model_8x)
        


@router.post("/detect-img/")
async def detect_objects_img(file: UploadFile = File(...), model = model):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Perform object detection
        results = model(image)
        
        # Draw bounding boxes and labels on the image
        draw = ImageDraw.Draw(image)
        # Use a larger font size (e.g., 36)
        font = ImageFont.truetype("arial.ttf", 20)  # You may need to adjust the font path
        
        width, height = image.size
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                try:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    # Ensure coordinates are valid and within image boundaries
                    x1 = max(0, min(x1, width - 1))
                    x2 = max(0, min(x2, width - 1))
                    y1 = max(0, min(y1, height - 1))
                    y2 = max(0, min(y2, height - 1))
                    
                    # Ensure x1 < x2 and y1 < y2
                    x1, x2 = min(x1, x2), max(x1, x2)
                    y1, y2 = min(y1, y2), max(y1, y2)
                    
                    # Skip if the box has no area
                    if x1 == x2 or y1 == y2:
                        logger.warning(f"Skipping zero-area box: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
                        continue
                    
                    class_id = int(box.cls)
                    conf = float(box.conf)
                    label = f"{result.names[class_id]} {conf:.2f}"
                    
                    # Draw bounding box
                    draw.rectangle([x1, y1, x2, y2], outline="red", width=4)  # Increased width for visibility
                    
                    # Draw label with larger font
                    text_bbox = draw.textbbox((x1, y1), label, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    draw.rectangle([x1, y1 - text_height - 5, x1 + text_width + 5, y1], fill="red")
                    draw.text((x1 + 2, y1 - text_height - 3), label, fill="white", font=font)
                    
                except Exception as e:
                    logger.error(f"Error processing box: {e}")
                    continue
        
        # Save the image to a bytes buffer
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return StreamingResponse(img_byte_arr, media_type="image/png")
    
    except Exception as e:
        logger.error(f"Error in detect_objects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Initialize the OCR reader with the custom model directory
reader = easyocr.Reader(['en'], model_storage_directory=MODEL_DIR, download_enabled=True)

@router.post("/ocr/")
async def perform_ocr(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Convert PIL Image to numpy array
        image_np = np.array(image)
        
        # Perform OCR
        result = reader.readtext(image_np)
        
        # Extract text from results
        text = ' '.join([item[1] for item in result])
        
        return JSONResponse(content={"text": text})
    
    except Exception as e:
        print(f"Error in perform_ocr: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ocr-light/")
async def perform_ocr_light(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Perform OCR with pytesseract
        text = pytesseract.image_to_string(image)
        
        return JSONResponse(content={"text": text.strip()})
    
    except Exception as e:
        print(f"Error in perform_ocr_light: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Print the model download locations
print(f"EasyOCR models are stored in: {MODEL_DIR}")

# Print the model download location
print(f"EasyOCR models are stored in: {MODEL_DIR}")
