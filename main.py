
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

import pandas as pd
import io
import re
import os
import json
import ast


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="DataFix AI Backend",
    description="Backend API for cleaning and restructuring CSV and Excel files",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================
# Allows your HTML/JavaScript frontend running on
# localhost:5500 to communicate with this backend.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Cleaning-Report"]
)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
def home():
    return {
        "message": "DataFix AI Backend is running",
        "status": "OK"
    }


# =========================================================
# COLUMN NAME NORMALIZATION
# =========================================================

def normalize_column_name(column):

    # Convert to string
    column = str(column)

    # Remove leading/trailing spaces
    column = column.strip()

    # Convert to lowercase
    column = column.lower()

    # Replace special characters with spaces
    column = re.sub(r"[^a-zA-Z0-9]+", " ", column)

    # Remove extra spaces
    column = re.sub(r"\s+", " ", column).strip()

    # Convert spaces to underscore
    column = column.replace(" ", "_")

    return column


def normalize_columns(df):

    original_columns = list(df.columns)

    new_columns = []

    used = {}

    for column in original_columns:

        new_column = normalize_column_name(column)

        # Empty column name
        if not new_column:
            new_column = "column"

        # Handle duplicate column names
        if new_column in used:

            used[new_column] += 1

            new_column = (
                f"{new_column}_{used[new_column]}"
            )

        else:

            used[new_column] = 0

        new_columns.append(new_column)

    df.columns = new_columns

    changes = []

    for old, new in zip(
        original_columns,
        new_columns
    ):

        if str(old) != str(new):

            changes.append({
                "original": str(old),
                "normalized": new
            })

    return df, changes


# =========================================================
# TEXT CLEANING
# =========================================================

def clean_text_values(df):

    for column in df.columns:

        if df[column].dtype == "object":

            # Remove leading/trailing spaces
            df[column] = df[column].apply(
                lambda x:
                x.strip()
                if isinstance(x, str)
                else x
            )

            # Remove multiple spaces
            df[column] = df[column].apply(
                lambda x:
                re.sub(r"\s+", " ", x)
                if isinstance(x, str)
                else x
            )

    return df


# =========================================================
# MISSING VALUE DETECTION
# =========================================================

def detect_missing_values(df):

    missing = df.isnull().sum()

    missing_report = {}

    for column, count in missing.items():

        if count > 0:

            missing_report[str(column)] = int(count)

    return missing_report


# =========================================================
# DUPLICATE DETECTION
# =========================================================

def detect_duplicates(df):

    return int(
        df.duplicated().sum()
    )


# =========================================================
# REMOVE DUPLICATES
# =========================================================

def remove_duplicates(df):

    before = len(df)

    df = df.drop_duplicates(
        keep="first"
    ).reset_index(drop=True)

    after = len(df)

    removed = before - after

    return df, removed


# =========================================================
# MISSING VALUE HANDLING
# =========================================================

def handle_missing_values(df):

    report = {}

    for column in df.columns:

        missing_count = int(
            df[column].isnull().sum()
        )

        if missing_count == 0:
            continue

        # ---------------------------------------------
        # NUMERIC COLUMN
        # ---------------------------------------------

        if pd.api.types.is_numeric_dtype(
            df[column]
        ):

            median_value = df[column].median()

            if pd.isna(median_value):

                median_value = 0

            df[column] = df[column].fillna(
                median_value
            )

            report[str(column)] = {
                "missing": missing_count,
                "method": "median",
                "value": float(median_value)
            }

        # ---------------------------------------------
        # TEXT COLUMN
        # ---------------------------------------------

        else:

            df[column] = df[column].fillna(
                "Unknown"
            )

            report[str(column)] = {
                "missing": missing_count,
                "method": "filled_with",
                "value": "Unknown"
            }

    return df, report


# =========================================================
# REMOVE EMPTY ROWS
# =========================================================

def remove_empty_rows(df):

    before = len(df)

    df = df.dropna(
        how="all"
    ).reset_index(drop=True)

    after = len(df)

    return df, before - after


# =========================================================
# BASIC DATA TYPE NORMALIZATION
# =========================================================

def normalize_data_types(df):

    for column in df.columns:

        if df[column].dtype == "object":

            # Don't convert columns containing
            # dates/emails/phones blindly.

            numeric_data = pd.to_numeric(
                df[column],
                errors="coerce"
            )

            non_null_original = (
                df[column].notna().sum()
            )

            non_null_numeric = (
                numeric_data.notna().sum()
            )

            if non_null_original > 0:

                numeric_ratio = (
                    non_null_numeric /
                    non_null_original
                )

                if numeric_ratio >= 0.90:

                    df[column] = numeric_data

    return df


# =========================================================
# DATA QUALITY SCORE
# =========================================================

def calculate_quality_score(df):

    if df.empty:

        return 0

    total_cells = (
        len(df) * len(df.columns)
    )

    if total_cells == 0:

        return 0

    missing_cells = int(
        df.isnull().sum().sum()
    )

    duplicate_rows = int(
        df.duplicated().sum()
    )

    missing_ratio = (
        missing_cells /
        total_cells
    )

    duplicate_ratio = (
        duplicate_rows /
        len(df)
    )

    score = 100

    score -= missing_ratio * 50

    score -= duplicate_ratio * 50

    score = max(
        0,
        min(
            100,
            round(score)
        )
    )

    return score


# =========================================================
# MAIN CLEANING PIPELINE
# =========================================================

def clean_dataset(df):

    original_rows = len(df)

    original_columns = len(df.columns)

    # ---------------------------------------------
    # 1. Remove completely empty rows
    # ---------------------------------------------

    df, empty_rows_removed = (
        remove_empty_rows(df)
    )

    # ---------------------------------------------
    # 2. Normalize column names
    # ---------------------------------------------

    df, column_changes = (
        normalize_columns(df)
    )

    # ---------------------------------------------
    # 3. Clean text
    # ---------------------------------------------

    df = clean_text_values(df)

    # ---------------------------------------------
    # 4. Detect duplicates
    # ---------------------------------------------

    duplicates_found = (
        detect_duplicates(df)
    )

    # ---------------------------------------------
    # 5. Remove duplicates
    # ---------------------------------------------

    df, duplicates_removed = (
        remove_duplicates(df)
    )

    # ---------------------------------------------
    # 6. Detect missing values
    # ---------------------------------------------

    missing_before = (
        detect_missing_values(df)
    )

    # ---------------------------------------------
    # 7. Handle missing values
    # ---------------------------------------------

    df, missing_handled = (
        handle_missing_values(df)
    )

    # ---------------------------------------------
    # 8. Normalize data types
    # ---------------------------------------------

    df = normalize_data_types(df)

    # ---------------------------------------------
    # Final statistics
    # ---------------------------------------------

    final_rows = len(df)

    final_columns = len(df.columns)

    quality_score = (
        calculate_quality_score(df)
    )

    report = {

        "original_rows":
            original_rows,

        "final_rows":
            final_rows,

        "original_columns":
            original_columns,

        "final_columns":
            final_columns,

        "empty_rows_removed":
            empty_rows_removed,

        "duplicates_found":
            duplicates_found,

        "duplicates_removed":
            duplicates_removed,

        "missing_values_found":
            missing_before,

        "missing_values_handled":
            missing_handled,

        "column_normalization":
            column_changes,

        "quality_score":
            quality_score

    }

    return df, report


# =========================================================
# FILE READER
# =========================================================

def read_uploaded_file(
    file_bytes,
    filename
):

    extension = (
        os.path.splitext(filename)[1]
        .lower()
    )

    try:

        # ---------------------------------------------
        # CSV
        # ---------------------------------------------

        if extension == ".csv":

            try:

                df = pd.read_csv(
                    io.BytesIO(file_bytes)
                )

            except UnicodeDecodeError:

                df = pd.read_csv(
                    io.BytesIO(file_bytes),
                    encoding="latin1"
                )

        # ---------------------------------------------
        # EXCEL
        # ---------------------------------------------

        elif extension in [
            ".xlsx",
            ".xls"
        ]:

            df = pd.read_excel(
                io.BytesIO(file_bytes)
            )

        # ---------------------------------------------
        # INVALID FILE
        # ---------------------------------------------

        else:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Only CSV and Excel files "
                    "are supported."
                )
            )

        return df

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unable to read file: {str(e)}"
            )
        )


# =========================================================
# FILE VALIDATION
# =========================================================

async def validate_and_read_file(file):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file uploaded."
        )

    extension = (
        os.path.splitext(
            file.filename
        )[1]
        .lower()
    )

    allowed_extensions = [
        ".csv",
        ".xlsx",
        ".xls"
    ]

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid file type. "
                "Upload CSV, XLSX or XLS."
            )
        )

    file_bytes = await file.read()

    if not file_bytes:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    df = read_uploaded_file(
        file_bytes,
        file.filename
    )

    if df.empty:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file contains no data."
        )

    return df


# =========================================================
# ANALYZE API
# =========================================================

@app.post("/analyze")
async def analyze_file(
    file: UploadFile = File(...)
):

    df = await validate_and_read_file(
        file
    )

    rows = len(df)

    columns = len(df.columns)

    duplicates = (
        detect_duplicates(df)
    )

    missing = (
        detect_missing_values(df)
    )

    total_missing = sum(
        missing.values()
    )

    quality_score = (
        calculate_quality_score(df)
    )

    return {

        "success": True,

        "filename":
            file.filename,

        "rows":
            rows,

        "columns":
          columns,

        "column_names": [
            str(column)
            for column in df.columns
        ],

        "duplicates":
            duplicates,

        "total_missing":
            total_missing,

        "missing_values":
            missing,

        "data_types": {

            str(column):
                str(dtype)

            for column, dtype
            in df.dtypes.items()

        },

        "quality_score":
            quality_score

    }


# =========================================================
# CLEAN API
# =========================================================

@app.post("/clean")
async def clean_file(
    file: UploadFile = File(...)
):

    df = await validate_and_read_file(
        file
    )

    # Clean dataset
    cleaned_df, report = (
        clean_dataset(df)
    )

    # ---------------------------------------------
    # Convert cleaned dataframe to CSV
    # ---------------------------------------------

    output = io.StringIO()

    cleaned_df.to_csv(
        output,
        index=False
    )

    csv_data = output.getvalue()

    # ---------------------------------------------
    # Convert report to JSON
    # ---------------------------------------------

    report_json = json.dumps(
        report
    )

    # ---------------------------------------------
    # Return cleaned CSV
    # ---------------------------------------------

    return StreamingResponse(

        iter([csv_data]),

        media_type="text/csv",

        headers={

            "Content-Disposition":
                "attachment; "
                "filename=cleaned_data.csv",

            "X-Cleaning-Report":
                report_json

        }

    )


# =========================================================
# CLEAN + JSON REPORT API
# =========================================================
# This endpoint is useful if your frontend wants
# the cleaning report as JSON instead of a CSV response.

@app.post("/clean-report")
async def clean_report(
    file: UploadFile = File(...)
):

    df = await validate_and_read_file(
        file
    )

    cleaned_df, report = (
        clean_dataset(df)
    )

    # Convert cleaned CSV to bytes
    output = io.StringIO()

    cleaned_df.to_csv(
        output,
        index=False
    )

    csv_bytes = (
        output.getvalue()
        .encode("utf-8")
    )

    return JSONResponse({

        "success": True,

        "filename":
            file.filename,

        "report":
            report,

        "cleaned_data":
            csv_bytes.decode("utf-8")

    })


__all__ = ["app"]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
