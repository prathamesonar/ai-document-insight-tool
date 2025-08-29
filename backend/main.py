import os
import re
import collections
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from dotenv import load_dotenv
import pypdf
import requests
import sqlite3
from datetime import datetime
import uuid

# --- Configuration & Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API Key from environment. For security, never hardcode keys.
# I am using the key you provided in the prompt. In a real-world scenario,
# you would replace this with your actual key in the .env file.
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "sk_m89a86ja_QlNeF7Iei6LPjCs3q7ZqgyEo")
SARVAM_API_URL = "https://api.sarvam.ai/v1/llm/chat/completions" # Note: This is a placeholder URL

DATABASE = 'document_insights.db'
UPLOADS_DIR = 'uploads'
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = FastAPI()

# --- CORS Middleware ---
# Allows the frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Database Setup ---
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    """Creates the database table if it doesn't exist."""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            filesize REAL NOT NULL,
            upload_date TEXT NOT NULL,
            processed_by TEXT NOT NULL, -- 'AI' or 'Keyword'
            insights TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database on startup
create_table()


# --- Pydantic Models (for data validation and serialization) ---
class KeywordInsight(BaseModel):
    top_keywords: List[str]

class Document(BaseModel):
    id: str
    filename: str
    filesize: float
    upload_date: str
    processed_by: str # 'AI' or 'Keyword'
    insights: Union[str, KeywordInsight]


# --- Helper Functions ---
def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text content from a PDF file."""
    try:
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract text from PDF.")

def get_ai_summary(text: str) -> Optional[str]:
    """Gets a summary from Sarvam AI."""
    headers = {
        "Authorization": f"Bearer {SARVAM_API_KEY}",
        "Content-Type": "application/json"
    }
    # Simple prompt for summarization
    prompt = f"Please provide a concise summary of the following resume text in about 50-70 words, highlighting key skills and experiences:\n\n{text}"
    
    payload = {
        "model": "meta/llama-3-8b-instruct", # Example model
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    try:
        response = requests.post(SARVAM_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        summary = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        return summary if summary else None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Sarvam AI request failed: {e}")
        return None

def get_top_keywords(text: str, num_keywords: int = 5) -> KeywordInsight:
    """Calculates the most frequent words in the text as a fallback."""
    # Basic text cleaning: lowercase and find words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Simple stop words list
    stop_words = set([
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 
        'he', 'him', 'his', 'she', 'her', 'it', 'its', 'they', 'them', 'their', 'what', 'which', 
        'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 
        'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 
        'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 
        'for', 'with', 'about', 'to', 'from', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 
        'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 
        'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
    ])
    
    # Filter out stop words and short words
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count frequencies
    word_counts = collections.Counter(filtered_words)
    
    # Get the most common words
    top_words = [word for word, count in word_counts.most_common(num_keywords)]
    
    return KeywordInsight(top_keywords=top_words)

# --- API Endpoints ---
@app.post("/upload-resume/", response_model=Document)
async def upload_resume(file: UploadFile = File(...)):
    """Handles PDF upload, processing, and storing insights."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    file_path = os.path.join(UPLOADS_DIR, file.filename)
    
    # Save the uploaded file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        filesize_mb = os.path.getsize(file_path) / (1024 * 1024)
    except Exception as e:
        logger.error(f"Failed to save file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Could not save file.")

    # Process the PDF
    text = extract_text_from_pdf(file_path)
    if not text:
        raise HTTPException(status_code=500, detail="PDF is empty or text could not be extracted.")

    # Try getting AI summary, with fallback to keywords
    insights_content = get_ai_summary(text)
    processed_by = "AI"
    
    if not insights_content:
        logger.info(f"AI summary failed for {file.filename}. Using keyword fallback.")
        insights_content_model = get_top_keywords(text)
        processed_by = "Keyword"
        insights_json = insights_content_model.json()
    else:
        insights_json = insights_content

    # Save to database
    doc_id = str(uuid.uuid4())
    upload_time = datetime.now().isoformat()

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO documents (id, filename, filesize, upload_date, processed_by, insights) VALUES (?, ?, ?, ?, ?, ?)",
        (doc_id, file.filename, filesize_mb, upload_time, processed_by, insights_json)
    )
    conn.commit()
    conn.close()

    return Document(
        id=doc_id,
        filename=file.filename,
        filesize=filesize_mb,
        upload_date=upload_time,
        processed_by=processed_by,
        insights=insights_content if processed_by == "AI" else insights_content_model
    )

@app.get("/history/", response_model=List[Document])
def get_history():
    """Retrieves the list of all processed documents."""
    conn = get_db_connection()
    docs_cursor = conn.execute("SELECT * FROM documents ORDER BY upload_date DESC").fetchall()
    conn.close()

    documents = []
    for row in docs_cursor:
        insights_data = row['insights']
        processed_by = row['processed_by']
        
        # Parse insights based on how they were processed
        if processed_by == 'Keyword':
            insights_obj = KeywordInsight.parse_raw(insights_data)
        else: # AI
            insights_obj = insights_data

        documents.append(Document(
            id=row['id'],
            filename=row['filename'],
            filesize=row['filesize'],
            upload_date=row['upload_date'],
            processed_by=processed_by,
            insights=insights_obj
        ))
    return documents

@app.get("/insights/{document_id}", response_model=Document)
def get_insights(document_id: str):
    """Retrieves insights for a specific document."""
    conn = get_db_connection()
    doc_row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    conn.close()
    
    if doc_row is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    insights_data = doc_row['insights']
    processed_by = doc_row['processed_by']
    
    if processed_by == 'Keyword':
        insights_obj = KeywordInsight.parse_raw(insights_data)
    else: # AI
        insights_obj = insights_data

    return Document(
        id=doc_row['id'],
        filename=doc_row['filename'],
        filesize=doc_row['filesize'],
        upload_date=doc_row['upload_date'],
        processed_by=processed_by,
        insights=insights_obj
    )
