# AI Document Insights Application

A full-stack web application for analyzing PDF documents using AI-powered insights and keyword extraction.

## Features

- **PDF Upload**: Drag & drop or browse to upload PDF files
- **AI Analysis**: Uses Sarvam AI for document summarization (requires API key)
- **Fallback Analysis**: Basic keyword extraction when AI is unavailable
- **Document History**: View all previously uploaded documents
- **Responsive UI**: Clean, modern interface built with Tailwind CSS
---

##  Tech Stack

- **Frontend:** HTML, TailwindCSS, JavaScript  
- **Backend:** FastAPI (Python)  
- **Database:** SQLite (for lightweight persistence)  
- **AI Integration:** Sarvam AI (recommended) or any HTTP based AI service  
- **Dev tools:** uvicorn, python venv

---
## Prerequisites

- Python 3.11 or higher
- Git (for cloning)

## Quick Start

### Windows Users:
Double-click `start.bat` or run:
```bash
start.bat
```

### macOS/Linux Users:
Make the script executable and run:
```bash
chmod +x start.sh
./start.sh
```

### Manual Setup:

1. **Install dependencies:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API Key (optional):**
   Edit `backend/.env` and add your Sarvam AI API key:
   ```
   SARVAM_API_KEY=your_actual_api_key_here
   ```

3. **Start backend server:**
   ```bash
   cd backend
   uvicorn main:app --host localhost --port 8000 --reload
   ```

4. **Start frontend server** (in new terminal):
   ```bash
   cd frontend
   python -m http.server 5000
   ```

5. **Access the application:**
   Open http://localhost:5000 in your browser

## API Endpoints

- `POST /upload-resume/` - Upload and analyze PDF document
- `GET /history/` - Get document analysis history

## File Structure

```
├── backend/
│   ├── main.py          # FastAPI application
│   ├── requirements.txt # Python dependencies
│   ├── .env            # Environment variables (create this)
│   └── uploads/        # Uploaded PDF files
├── frontend/
│   └── index.html      # Web interface
├── start.sh           # Linux/macOS startup script
├── start.bat          # Windows startup script
└── README.md          # This file
```

## Notes

- The application will work without an API key, but will only perform basic keyword analysis
- For AI features, get a free API key from [Sarvam AI](https://sarvam.ai)
- Uploaded files are stored in `backend/uploads/` and metadata in SQLite database
