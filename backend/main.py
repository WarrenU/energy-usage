import os
import csv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional, Tuple
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from decimal import Decimal

# --- Config ---
MOCK_S3_DIR = 'mock_s3'
DYNAMODB_TABLE = 'EnergyUsage'
USER_ID = 'demo-user'
EXPECTED_HEADERS = ['Date', 'Usage']

# --- FastAPI Setup ---
app = FastAPI(title="Energy Usage Upload API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DynamoDB Setup (local) ---
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-west-2',
    endpoint_url='http://localhost:8000',  # DynamoDB Local default
    aws_access_key_id='fakeMyKeyId',
    aws_secret_access_key='fakeSecretAccessKey',
)

def get_table():
    return dynamodb.Table(DYNAMODB_TABLE)  # type: ignore[attr-defined]

# --- Ensure mock S3 dir exists ---
os.makedirs(MOCK_S3_DIR, exist_ok=True)

def validate_and_read_file(file: UploadFile) -> Optional[bytes]:
    if not file:
        raise HTTPException(status_code=400, detail="No file sent.")
    content = file.file.read() if hasattr(file.file, 'read') else None
    if content is None or content == b'':
        return None
    return content

def save_to_mock_s3(filename: str, content: bytes):
    s3_path = os.path.join(MOCK_S3_DIR, filename)
    with open(s3_path, 'wb') as f:
        f.write(content)

def parse_csv_content(content: bytes, filename: str) -> Tuple[list, list]:
    content_str = content.decode('utf-8')
    reader = csv.reader(content_str.splitlines())
    try:
        headers = next(reader)
    except StopIteration:
        return [], [f"LOG: File '{filename}' is empty."]
    if headers != EXPECTED_HEADERS:
        raise HTTPException(status_code=400, detail=f"File '{filename}' headers do not match {EXPECTED_HEADERS}.")
    rows = list(reader)
    if not rows:
        return [], [f"LOG: File '{filename}' has headers but no data rows."]
    return rows, []

def store_row_in_dynamodb(date: str, usage: float, alerts: list, filename: str):
    try:
        get_table().put_item(Item={
            'userId': USER_ID,
            'date': date,
            'usage': Decimal(str(usage))
        })
    except (BotoCoreError, ClientError) as e:
        alerts.append(f"LOG: DynamoDB error for '{filename}' on {date}: {str(e)}")

def check_threshold(date: str, usage: float, threshold: float, filename: str, alerts: list, exceeded_summary: list):
    if usage > threshold:
        alert_msg = f"ALERT: Usage of {usage} on {date} in '{filename}' exceeds threshold of {threshold}"
        alerts.append(alert_msg)
        exceeded_summary.append({
            'date': date,
            'usage': usage,
            'threshold': threshold,
            'filename': filename
        })

def should_skip_file(filename: str, content: bytes) -> Tuple[bool, Optional[str]]:
    if not content:
        return True, f"LOG: File '{filename}' is empty."
    if not (filename.lower().endswith('.csv') or filename.lower().endswith('.txt')):
        return True, f"LOG: File '{filename}' is not a .csv or .txt file and was skipped."
    return False, None

@app.post("/energy/upload", summary="Upload CSV energy usage data", response_description="Upload status and alerts", response_model=Dict[str, Any])
async def upload_energy_csv(
    files: List[UploadFile] = File(..., description="CSV files to upload"),
    threshold: float = Form(30, description="Usage threshold for alerts")
):
    """
    Upload one or more CSV files with daily energy usage data. Each file must have headers: Date,Usage.
    Stores files in mock S3, records in DynamoDB, and returns alerts for days exceeding the threshold.
    """
    alerts = []
    exceeded_summary = []
    for file in files:
        filename = file.filename or "uploaded.csv"
        content = await file.read()
        skip, alert = should_skip_file(filename, content)
        if skip:
            if alert:
                alerts.append(alert)
            continue
        save_to_mock_s3(filename, content)
        rows, parse_alerts = parse_csv_content(content, filename)
        alerts.extend(parse_alerts)
        if not rows:
            continue
        for row in rows:
            try:
                date, usage = row[0], float(row[1])
            except Exception:
                alerts.append(f"LOG: File '{filename}' has invalid row: {row}")
                continue
            store_row_in_dynamodb(date, usage, alerts, filename)
            check_threshold(date, usage, threshold, filename, alerts, exceeded_summary)
    return JSONResponse(content={
        'status': 'success',
        'alerts': alerts,
        'userId': USER_ID,
        'exceededThresholds': exceeded_summary
    }) 