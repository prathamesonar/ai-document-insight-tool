# backend/main.py

import os
import re
import collections
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Union
from dotenv import load_dotenv
import pypdf
import requests
import sqlite3
from datetime import datetime
import uuid

# --- Configuration & Setup ---
load_dotenv()

# Setup detailed logging to see exactly what's happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Corrected Sarvam AI API Details and Key Loading
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
# NOTE: This is the documented API endpoint for Sarvam.
SARVAM_API_URL = "https://api.sarvam.ai/chat/completions"

DATABASE = 'document_insights.db'
UPLOADS_DIR = 'uploads'
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = FastAPI()

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Setup ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            filesize REAL NOT NULL,
            upload_date TEXT NOT NULL,
            processed_by TEXT NOT NULL,
            insights TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_table()

# --- Pydantic Models ---
class KeywordInsight(BaseModel):
    top_keywords: List[str]

class Document(BaseModel):
    id: str
    filename: str
    filesize: float
    upload_date: str
    processed_by: str
    insights: Union[str, KeywordInsight]

# --- Helper Functions ---
def extract_text_from_pdf(file_path: str) -> str:
    try:
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            text = "".join(page.extract_text() or "" for page in reader.pages)
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        return ""

def get_ai_summary(text: str) -> Union[str, None]:
    """Calls the Sarvam AI API and returns a summary, or None on failure."""
    if not SARVAM_API_KEY:
        logger.warning("SARVAM_API_KEY not found in .env file. Skipping AI summary.")
        return None

    headers = {
        "API-Subscription-Key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    # Using the correct Sarvam AI model
    payload = {
        "model": "sarvam-m",
        "messages": [
            {"role": "user", "content": f"Please provide a concise summary of the following document:\n\n{text}"}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    try:
        logger.info("Contacting Sarvam AI for summary...")
        response = requests.post(SARVAM_API_URL, headers=headers, json=payload, timeout=30)
        # This will raise an error for 4xx or 5xx status codes
        response.raise_for_status()
        
        data = response.json()
        summary = data['choices'][0]['message']['content']
        logger.info("Successfully received summary from Sarvam AI.")
        return summary
    except requests.exceptions.RequestException as e:
        # This is the crucial new logging part!
        logger.error(f"Sarvam AI API request failed: {e}")
        if e.response is not None:
            logger.error(f"Sarvam AI API Response Status: {e.response.status_code}")
            logger.error(f"Sarvam AI API Response Body: {e.response.text}")
        return None
    except (KeyError, IndexError) as e:
        logger.error(f"Failed to parse Sarvam AI response: {e}")
        return None


def get_keyword_analysis(text: str) -> List[str]:
    """Performs fallback keyword analysis."""
    logger.info("Performing fallback keyword analysis.")
    words = re.findall(r'\b\w+\b', text.lower())
    # Basic stopword list, can be expanded
    stopwords = set(["the", "a", "an", "in", "to", "of", "and", "is", "for", "with", "on", "it", "that", "this"])
    filtered_words = [word for word in words if word not in stopwords and len(word) > 2]
    most_common = collections.Counter(filtered_words).most_common(5)
    return [word for word, count in most_common]

# --- API Endpoints ---
@app.post("/upload-resume/", response_model=Document)
async def upload_resume(file: UploadFile = File(...)):
    # Save the uploaded file
    file_path = os.path.join(UPLOADS_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Could not save file.")

    # Process the file
    text_content = extract_text_from_pdf(file_path)
    if not text_content:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF.")

    summary = get_ai_summary(text_content)
    doc_id = str(uuid.uuid4())
    upload_time = datetime.now().isoformat()
    filesize_mb = os.path.getsize(file_path) / (1024 * 1024)

    conn = get_db_connection()
    if summary:
        processed_by = "AI"
        insights_to_db = summary
        keywords = []  # Initialize keywords for response
    else:
        processed_by = "Keyword"
        keywords = get_keyword_analysis(text_content)
        insights_to_db = ",".join(keywords) # Store keywords as comma-separated string

    conn.execute(
        'INSERT INTO documents (id, filename, filesize, upload_date, processed_by, insights) VALUES (?, ?, ?, ?, ?, ?)',
        (doc_id, file.filename, filesize_mb, upload_time, processed_by, insights_to_db)
    )
    conn.commit()
    conn.close()
    
    logger.info(f"Successfully processed and saved document: {file.filename}")

    # Prepare response
    insights_response = summary if processed_by == "AI" else KeywordInsight(top_keywords=keywords)
    return Document(
        id=doc_id,
        filename=file.filename,
        filesize=filesize_mb,
        upload_date=upload_time,
        processed_by=processed_by,
        insights=insights_response
    )

@app.get("/history/", response_model=List[Document])
def get_all_insights():
    conn = get_db_connection()
    docs_from_db = conn.execute('SELECT * FROM documents ORDER BY upload_date DESC').fetchall()
    conn.close()

    documents = []
    for row in docs_from_db:
        insights_data = row['insights']
        if row['processed_by'] == 'Keyword':
            insights_data = KeywordInsight(top_keywords=insights_data.split(','))
        
        documents.append(Document(
            id=row['id'],
            filename=row['filename'],
            filesize=row['filesize'],
            upload_date=row['upload_date'],
            processed_by=row['processed_by'],
            insights=insights_data
        ))
    return documents

