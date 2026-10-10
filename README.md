# DataMedic 🩺 (DataFix AI)

> **Turn messy data into clean, structured data in seconds.**  
> Built for **TriCity Aithon 2026**.

---

## 📌 Overview
**DataMedic** is an automated data cleansing and quality analysis platform for CSV and Excel (`.xlsx`, `.xls`) datasets. It diagnoses data health issues, calculates a composite Data Quality Score, handles duplicate/missing data, normalizes schemas, and provides cleaned datasets for download.

---

## 🚀 Key Features
- **Data Quality Score (0–100%)**: Instant composite score reflecting missing cells, empty rows, and duplicates.
- **Header & Schema Normalization**: Auto-formats column names to consistent `snake_case` and resolves name collisions.
- **Smart Imputation**: Imputes missing numeric values using column medians and categoricals using `"Unknown"`.
- **Deduplication & Empty Row Cleanup**: Detects and purges repeated rows and blanks.
- **Interactive UI**: Drag-and-drop dashboard with live feedback and instant download of cleaned files.

---

## 🛠️ Tech Stack
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism & SVG Vector Theme), Vanilla JavaScript.
- **Backend API**: Python 3.10+, FastAPI, Pandas, Uvicorn.

---

## 💻 Local Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/datamedic.git
cd datamedic
```

### 2. Set up the Python Backend
```bash
# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn main:app --reload --port 8000
```
Backend will run at: `http://127.0.0.1:8000` (API Docs: `http://127.0.0.1:8000/docs`).

### 3. Launch Frontend
Open `index.html` in your browser, or serve it using VS Code Live Server / Python HTTP server:
```bash
python -m http.server 5500
```
Visit `http://localhost:5500` in your web browser.
