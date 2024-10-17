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
import cv2

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
model_8x = YOLO('yolov8n.pt')
# model_8x = YOLO('yolov8x.pt')
pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Load the YOLOv8s model for better small object detection
model_small = YOLO('yolov8s.pt')


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
async def perform_ocr(file: UploadFile = File(...), line_level: bool = False):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Convert PIL Image to numpy array
        image_np = np.array(image)
        
        # Perform OCR
        result = reader.readtext(image_np, paragraph=line_level)
        
        # Extract text from results
        text = ' '.join([item[1] for item in result])
        
        # Convert numpy types to Python native types
        processed_result = [
            {
                "bbox": [[float(coord) for coord in point] for point in item[0]],
                "text": item[1],
                "confidence": float(item[2])
            } for item in result
        ]
        
        return JSONResponse(content={
            "text": text, 
            "result": processed_result,
            "line_level": line_level
        })
    
    except Exception as e:
        logger.error(f"Error in perform_ocr: {e}")
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

@router.post("/classify/")
async def classify_small_objects(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Perform object detection
        results = model_small(image)
        
        detected_objects = []
        items_dict = {}
        errors = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                try:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    class_id = int(box.cls)
                    conf = float(box.conf)
                    label = result.names[class_id]
                    
                    # Crop the image to the bounding box
                    cropped_img = image[y1:y2, x1:x2]
                    
                    # Encode the cropped image to base64 with data URI prefix
                    _, buffer = cv2.imencode('.png', cropped_img)
                    # img_base64 = f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"
                    img_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    item = {
                        "bbox": [[x1, y1], [x2, y1], [x2, y2], [x1, y2]],
                        "confidence": round(conf, 2),
                        "text": label,
                        "image": img_base64
                    }
                    
                    detected_objects.append(item)
                    
                    # Update items_dict
                    if label in items_dict:
                        items_dict[label]["quantity"] += 1
                        items_dict[label]["bboxes"].append(item["bbox"])
                        items_dict[label]["images"].append(img_base64)
                    else:
                        items_dict[label] = {
                            "confidence": item["confidence"],
                            "quantity": 1,
                            "bboxes": [item["bbox"]],
                            "images": [img_base64]
                        }
                    
                except Exception as e:
                    logger.error(f"Error processing box: {e}")
                    continue
        
        # Sort objects by confidence (highest first)
        detected_objects.sort(key=lambda x: x['confidence'], reverse=True)
        
        return JSONResponse(content={
            "result": detected_objects,
            "items": items_dict,
            "errors": errors,
            "parameters": {
                "model": "YOLOv8s"
            }
        })
    
    except Exception as e:
        logger.error(f"Error in classify_small_objects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect-box-name/")
async def detect_box_names(
    file: UploadFile = File(...),
    min_size: int = 20,
    text_threshold: float = 0.7,
    low_text: float = 0.4,
    link_threshold: float = 0.4,
    canvas_size: int = 2560,
    mag_ratio: float = 1.0,
    slope_ths: float = 0.2,
    ycenter_ths: float = 0.5,
    height_ths: float = 0.5,
    width_ths: float = 0.3,
    add_margin: float = 0.1,
):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Convert PIL Image to numpy array
        image_np = np.array(image)
        
        # Perform OCR with optimized parameters
        result = reader.readtext(
            image_np,
            paragraph=False,
            min_size=min_size,
            text_threshold=text_threshold,
            low_text=low_text,
            link_threshold=link_threshold,
            canvas_size=canvas_size,
            mag_ratio=mag_ratio,
            slope_ths=slope_ths,
            ycenter_ths=ycenter_ths,
            height_ths=height_ths,
            width_ths=width_ths,
            add_margin=add_margin,
        )
        
        # Process results to combine closely spaced text and exclude short results
        processed_result = []
        for i, item in enumerate(result):
            if i > 0 and is_close(item[0], result[i-1][0]):
                # Combine with previous item
                prev = processed_result[-1]
                prev["text"] += " " + item[1]
                prev["bbox"][1] = item[0][1]  # Update top-right
                prev["bbox"][2] = item[0][2]  # Update bottom-right
                prev["confidence"] = (prev["confidence"] + float(item[2])) / 2
            else:
                # Add as new item if it has at least 3 non-space characters
                if len(''.join(item[1].split())) >= 3:
                    processed_result.append({
                        "bbox": [[float(coord) for coord in point] for point in item[0]],
                        "text": item[1],
                        "confidence": float(item[2])
                    })
        
        # Final filter to ensure all results have at least 3 non-space characters
        final_result = [item for item in processed_result if len(''.join(item["text"].split())) >= 3]
        
        # Create a dictionary with box names as keys
        box_dict = {}
        errors = []
        for item in final_result:
            box_name = item["text"].strip()
            if box_name in box_dict:
                errors.append(f"Duplicate box name detected: {box_name}")
            else:
                box_dict[box_name] = {
                    "bbox": item["bbox"],
                    "confidence": item["confidence"],
                    "text": item["text"]
                }
        
        return JSONResponse(content={
            "result": final_result,
            "boxes": box_dict,
            "errors": errors,
            "parameters": {
                "min_size": min_size,
                "text_threshold": text_threshold,
                "low_text": low_text,
                "link_threshold": link_threshold,
                "canvas_size": canvas_size,
                "mag_ratio": mag_ratio,
                "slope_ths": slope_ths,
                "ycenter_ths": ycenter_ths,
                "height_ths": height_ths,
                "width_ths": width_ths,
                "add_margin": add_margin,
            }
        })
    
    except Exception as e:
        logger.error(f"Error in detect_box_names: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def is_close(bbox1, bbox2, threshold=0.1):
    """Check if two bounding boxes are close to each other."""
    x1, y1 = bbox1[0]
    x2, y2 = bbox2[1]
    width = max(bbox1[1][0], bbox2[1][0]) - min(bbox1[0][0], bbox2[0][0])
    height = max(bbox1[2][1], bbox2[2][1]) - min(bbox1[0][1], bbox2[0][1])
    return abs(x2 - x1) < width * threshold and abs(y2 - y1) < height * threshold

def is_close(bbox1, bbox2, threshold=0.1):
    """Check if two bounding boxes are close to each other."""
    x1, y1 = bbox1[0]
    x2, y2 = bbox2[1]
    width = max(bbox1[1][0], bbox2[1][0]) - min(bbox1[0][0], bbox2[0][0])
    height = max(bbox1[2][1], bbox2[2][1]) - min(bbox1[0][1], bbox2[0][1])
    return abs(x2 - x1) < width * threshold and abs(y2 - y1) < height * threshold

def is_close(bbox1, bbox2, threshold=0.1):
    """Check if two bounding boxes are close to each other."""
    x1, y1 = bbox1[0]
    x2, y2 = bbox2[1]
    width = max(bbox1[1][0], bbox2[1][0]) - min(bbox1[0][0], bbox2[0][0])
    height = max(bbox1[2][1], bbox2[2][1]) - min(bbox1[0][1], bbox2[0][1])
    return abs(x2 - x1) < width * threshold and abs(y2 - y1) < height * threshold