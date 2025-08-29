# AI Document Insights

## Overview

AI Document Insights is a web application that enables users to upload PDF documents and extract intelligent insights using AI. The system consists of a FastAPI backend that handles PDF processing and AI analysis, paired with a modern frontend built with HTML, Tailwind CSS, and vanilla JavaScript. The application integrates with Sarvam AI's API to provide document analysis capabilities and uses SQLite for local data persistence.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: FastAPI for REST API development, chosen for its modern async capabilities, automatic API documentation, and excellent type safety with Pydantic models
- **PDF Processing**: PyPDF library for extracting text content from uploaded PDF documents
- **Database**: SQLite for local data storage, providing a lightweight solution for storing document metadata and analysis results without requiring external database setup
- **File Management**: Local file system storage with an `uploads` directory for managing uploaded documents
- **Configuration**: Environment variables managed through python-dotenv for secure API key storage

### Frontend Architecture
- **Technology Stack**: Vanilla HTML, CSS, and JavaScript for simplicity and minimal dependencies
- **Styling**: Tailwind CSS via CDN for rapid UI development and consistent design system
- **Typography**: Inter font from Google Fonts for modern, readable text
- **File Upload**: Drag-and-drop interface with visual feedback for enhanced user experience
- **Responsive Design**: Mobile-first approach using Tailwind's responsive utilities

### Data Storage
- **Primary Database**: SQLite database (`document_insights.db`) for storing document metadata, analysis results, and application state
- **File Storage**: Local filesystem storage in `uploads` directory for PDF documents
- **Database Connection**: Row factory configuration for easier data access and manipulation

### API Design
- **CORS Configuration**: Permissive CORS settings allowing all origins for development flexibility
- **Request Handling**: Multipart form data support for file uploads
- **Error Handling**: HTTPException usage for structured error responses
- **Logging**: Comprehensive logging system for debugging and monitoring

## External Dependencies

### AI Services
- **Sarvam AI**: Primary AI service for document analysis and chat completions
  - Endpoint: `https://api.sarvam.ai/v1/llm/chat/completions`
  - Authentication: API key-based authentication via environment variables

### Python Libraries
- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server for running the FastAPI application
- **PyPDF**: PDF text extraction and processing
- **Requests**: HTTP client for external API communications
- **Python-multipart**: File upload handling
- **Python-dotenv**: Environment variable management

### Frontend Dependencies
- **Tailwind CSS**: Utility-first CSS framework loaded via CDN
- **Google Fonts**: Inter font family for typography
- **Native Browser APIs**: File handling, drag-and-drop, and fetch for HTTP requests

### Development Tools
- **SQLite3**: Built-in Python database interface
- **OS/Path Libraries**: File system operations and path management
- **UUID**: Unique identifier generation for documents
- **Collections**: Data structure utilities for text processing
- **Datetime**: Timestamp management for document tracking