# OnVoke AI - SOP Generation API

A FastAPI-based application for generating Standard Operating Procedures (SOPs) using AI and document processing.

## 🏗️ Project Structure

```
onvoke_AI/
├── main.py                     # 🚀 Main entry point
├── test_structure.py           # 🧪 Test script for structure validation
├── requirements.txt            # 📦 Dependencies
├── pyproject.toml             # 🔧 Project configuration
└── app/                       # 📁 Main application package
    ├── api/                   # 🌐 API layer
    │   ├── __init__.py
    │   └── routes.py          # API endpoints
    ├── core/                  # 🏛️ Core application components
    │   ├── __init__.py
    │   ├── app.py             # FastAPI app factory
    │   └── database.py        # Database connections
    ├── config/                # ⚙️ Configuration
    │   ├── __init__.py
    │   └── config.py          # Environment and config management
    ├── models/                # 📊 Data models
    │   ├── __init__.py
    │   ├── state_schema.py    # LangGraph state models
    │   └── custom_models.py   # Custom Pydantic models
    ├── services/              # 🔧 Business logic services
    │   ├── ai_services/       # 🤖 AI-related services
    │   │   └── sop_generator.py
    │   ├── file_services/     # 📄 File processing services
    │   │   ├── create_pdf.py
    │   │   ├── docx_converter.py
    │   │   ├── file_readers.py
    │   │   ├── markdownit.py
    │   │   └── pdf_converter.py
    │   └── rag_services/      # 🔍 RAG services
    │       └── jira_rag.py
    ├── prompts/               # 💬 AI prompts
    │   └── technical_article_prompt.py
    ├── templates/             # 🎨 HTML templates
    │   └── index.html
    ├── utils/                 # 🛠️ Utility functions
    │   ├── json_parser.py
    │   └── debug_inputs/      # Debug data
    ├── workflow.py            # 🔄 LangGraph workflow
    └── app.py                 # 🔄 Legacy app file (for compatibility)
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Create a `.env` file with:
```env
GOOGLE_API_KEY=your_google_api_key
LLAMA_CLOUD_API_KEY=your_llama_cloud_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_key
```

### 3. Test the Structure
```bash
python test_structure.py
```

### 4. Run the Application
```bash
python main.py
```

The API will be available at: `http://localhost:8080`

## 📚 API Endpoints

### Health Check
- `GET /` - Root endpoint with status
- `GET /health` - Health check endpoint

### SOP Generation
- `POST /api/v1/generate_sop/` - Generate SOP from files and templates
- `POST /api/v1/download/` - Convert markdown to PDF/DOCX

## 🏛️ Architecture Overview

### Entry Points
- **`main.py`**: Primary entry point for production
- **`app/app.py`**: Legacy entry point (kept for compatibility)

### Core Components
- **`app/core/app.py`**: FastAPI application factory
- **`app/core/database.py`**: Supabase client management
- **`app/api/routes.py`**: API route definitions

### Services Layer
- **AI Services**: Handle AI model interactions and SOP generation
- **File Services**: Process various file formats (PDF, DOCX, Excel)
- **RAG Services**: Retrieve relevant information from knowledge bases

### Data Flow
1. **Request** → API Routes → Business Logic (Services)
2. **File Processing** → AI Services → LangGraph Workflow
3. **Response** → Formatted output (JSON/PDF/DOCX)

## 🔧 Development

### Running in Development Mode
```bash
# With auto-reload
python main.py

# Or directly with uvicorn
uvicorn app.core.app:create_app --factory --host 0.0.0.0 --port 8080 --reload
```

### Testing Structure
```bash
python test_structure.py
```

### Adding New Services
1. Create service module in appropriate `app/services/` subdirectory
2. Import and use in `app/api/routes.py`
3. Update workflow if needed in `app/workflow.py`

## 🔄 Migration from Old Structure

The application has been refactored from a monolithic `app.py` to a modular structure:

- **Before**: Everything in `app/app.py`
- **After**: Organized into layers (API, Core, Services, Models)

### Backward Compatibility
- `app/app.py` still exists for compatibility
- Can still run with `uvicorn app:app`
- Recommended to use `python main.py` for new deployments

## 🛠️ Technologies Used

- **FastAPI**: Web framework
- **LangGraph**: Workflow management
- **Supabase**: Database and storage
- **Google Generative AI**: AI model integration
- **PyPDF2**: PDF processing
- **Pandas**: Data manipulation
- **ReportLab**: PDF generation

## 📝 Contributing

1. Follow the established folder structure
2. Keep services modular and focused
3. Use proper imports (avoid relative imports across packages)
4. Test with `test_structure.py` before committing

---

Made with ❤️ for efficient SOP generation
