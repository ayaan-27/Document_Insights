# Document Insights

Document Insights is an intelligent document processing platform that automates the extraction, validation, and review of structured data from scanned PDFs and images. It uses AWS Textract for OCR and key-value / table extraction, wraps it in a Flask REST API backend, and pairs it with an Angular frontend — creating an end-to-end workflow for document processing teams operating across multiple roles.

---

## Overview

The platform is built around a human-in-the-loop document workflow. Documents are uploaded, automatically processed via AWS Textract, and then routed to team members for review and quality control — with dashboards and analytics tracking throughput, accuracy, and average handling time at every stage.

```
Upload Document → OCR & Extraction (AWS Textract)
    → Document Processor Review → QC Review → Manager Sign-off
        → Verified Data → Analytics & Reporting
```

---

## Features

**Automated Document Extraction**
- Converts PDFs to images (via PyMuPDF) and sends them to AWS Textract
- Extracts forms (key-value pairs), tables, and line-level text with bounding box coordinates
- Captures extraction confidence scores at both average and minimum levels per field
- Saves structured output to PostgreSQL for downstream review

**Role-Based Document Workflow**
- Three roles: **Document Processor**, **QC Reviewer**, and **Manager**
- Documents are assigned to team members per role; each sees only their queue
- Processors mark fields and submit; QC verifies or returns documents for correction
- Full audit trail: processed, verified, and seen flags tracked per document

**Field-Level Review & Correction**
- Extracted fields displayed with confidence scores and bounding box overlays
- Reviewers can correct incorrect fields and flag them for re-extraction
- Tracks which fields were edited, which were missing, and which were low/high confidence

**Analytics & Reporting**
- Average handling time (AHT) per processor and QC reviewer
- Documents processed per day, per employee, and per document type
- Accuracy metrics: mean extraction accuracy, high/low confidence breakdowns
- Field-level stats: fields identified, uncaptured values, edited fields, corrections made
- Queue visibility: unassigned, in-progress, in QC, and completed document counts

**Background Processing Service**
- Polling service (`service_doc_preprocessor.py`) continuously monitors the database for unprocessed documents and triggers Textract extraction automatically — decoupling upload from processing

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Angular 12 |
| Backend API | Flask + Flask-CORS |
| Database | PostgreSQL (psycopg2) |
| OCR & Extraction | AWS Textract (boto3) |
| PDF Processing | PyMuPDF (fitz) |
| Data Processing | pandas |

---

## Project Structure

```
Document_Insights/
├── flask app/
│   ├── app.py                          # Flask API — all routes for docs, users, analytics
│   ├── service_doc_preprocessor.py     # Background polling service for OCR processing
│   ├── textract_extraction.py          # AWS Textract calls, form/table/line extraction
│   ├── analyze_table_forms.py          # Parses Textract responses into DataFrames
│   ├── value_confidences.py            # Extracts average confidence scores per field
│   ├── value_confidences_min.py        # Extracts minimum confidence scores per field
│   ├── pdf_to_png.py                   # Converts PDF pages to PNG via PyMuPDF
│   └── uploads/                        # Uploaded document storage
│
├── Textract_forms_scripts/
│   ├── FORMS_main.py                   # Standalone script for running Textract on images
│   ├── analyze_table_forms.py          # Shared form/table/line parsing utilities
│   ├── value_confidences.py
│   └── value_confidences_min.py
│
└── UI/                                 # Angular 12 frontend
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js & Angular CLI
- PostgreSQL
- AWS account with Textract access and configured credentials

### 1. Clone the repository

```bash
git clone https://github.com/ayaan-27/Document_Insights.git
cd Document_Insights
```

### 2. Set up the backend

```bash
cd "flask app"
pip install flask flask-cors flask-session psycopg2-binary pandas boto3 trp PyMuPDF opencv-python
```

Update the database connection details in `app.py` and `service_doc_preprocessor.py`:

```python
DB_HOST = "your-db-host"
DB_NAME = "DeepInsights"
DB_USER = "your-user"
DB_PASS = "your-password"
```

Configure your AWS credentials for Textract access:

```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=eu-west-1
```

### 3. Run the Flask API

```bash
cd "flask app"
python app.py
```

The API will be available at `http://localhost:5000`.

### 4. Run the background processing service

In a separate terminal, start the polling service that picks up uploaded documents and runs Textract on them:

```bash
cd "flask app"
python service_doc_preprocessor.py
```

### 5. Run the Angular frontend

```bash
cd UI
npm install
ng serve
```

The UI will be available at `http://localhost:4200`.

---

## API Overview

| Endpoint | Description |
|---|---|
| `POST /documents` | Fetch a document by ID |
| `POST /get_docs` | Get document queue for a given user and role |
| `POST /add_newdoc` | Upload and register a new document |
| `POST /fetch_document` | Fetch extracted data for a document |
| `POST /assignprocessor` / `/assignqc` | Assign a document to a processor or QC reviewer |
| `POST /updateprocessed` / `/updateverified` | Mark a document as processed or verified |
| `POST /returntoprocessor` | Return a document from QC back to the processor |
| `POST /extracted_data` | Get extracted field data for a document |
| `POST /update` | Update extracted field values |
| `POST /incorrect_fields` | Flag incorrect fields |
| `GET /mean_acc` | Mean extraction accuracy across all documents |
| `GET /avg_proc_time` | Average processing time |
| `GET /doc_day` | Documents processed per day |
| `GET /high_conf_extraction` / `/low_conf_extraction` | High/low confidence extraction stats |
| `POST /aht_processor` / `/aht_qc` | Average handling time per processor or QC |
| `GET /unassigned_docs` | Documents not yet assigned |
| `GET /docs_completed` | Count of fully completed documents |

---

## Notes

- The `Textract_forms_scripts/` folder contains standalone scripts that can be used to test Textract extraction independently of the full application stack.
- Database credentials are currently hardcoded — move these to environment variables or a config file before any production or public deployment.
- The AWS Textract client is configured for `eu-west-1` — update the region in `textract_extraction.py` to match your setup.
