
const API_URL = "https://datamedic-api.onrender.com";

let selectedFile = null;
let cleanedFileBlob = null;


// --------------------------------------------f------
// ELEMENTS
// --------------------------------------------------

const fileInput = document.getElementById("fileInput");
const dropZone = document.getElementById("dropZone");

const selectedFileBox =
    document.getElementById("selectedFile");

const fileName =
    document.getElementById("fileName");

const fileSize =
    document.getElementById("fileSize");

const removeFile =
    document.getElementById("removeFile");

const actions =
    document.getElementById("actions");

const analyzeBtn =
    document.getElementById("analyzeBtn");

const cleanBtn =
    document.getElementById("cleanBtn");

const dashboard =
    document.getElementById("dashboard");

const loading =
    document.getElementById("loading");

const loadingText =
    document.getElementById("loadingText");

const cleaningResults =
    document.getElementById("cleaningResults");

const downloadBtn =
    document.getElementById("downloadBtn");


// --------------------------------------------------
// FILE SELECTION
// --------------------------------------------------

fileInput.addEventListener("change", function () {

    if (this.files.length > 0) {

        handleFile(this.files[0]);

    }

});


function handleFile(file) {

    const allowedExtensions =
        ["csv", "xlsx", "xls"];

    const extension =
        file.name.split(".").pop().toLowerCase();

    if (!allowedExtensions.includes(extension)) {

        alert(
            "Please upload a CSV or Excel file."
        );

        return;
    }

    selectedFile = file;

    fileName.textContent = file.name;

    fileSize.textContent =
        formatFileSize(file.size);

    selectedFileBox.classList.remove("hidden");

    dropZone.classList.add("hidden");

    actions.classList.remove("hidden");

    dashboard.classList.add("hidden");

    cleaningResults.classList.add("hidden");

}


// --------------------------------------------------
// FILE SIZE
// --------------------------------------------------

function formatFileSize(bytes) {

    if (bytes < 1024) {

        return bytes + " Bytes";

    }

    if (bytes < 1024 * 1024) {

        return (
            (bytes / 1024).toFixed(1)
            + " KB"
        );

    }

    return (
        (bytes / (1024 * 1024)).toFixed(1)
        + " MB"
    );

}


// --------------------------------------------------
// REMOVE FILE
// --------------------------------------------------

removeFile.addEventListener("click", function () {

    selectedFile = null;

    fileInput.value = "";

    selectedFileBox.classList.add("hidden");

    dropZone.classList.remove("hidden");

    actions.classList.add("hidden");

    dashboard.classList.add("hidden");

});


// --------------------------------------------------
// DRAG AND DROP
// --------------------------------------------------

dropZone.addEventListener(
    "dragover",
    function (event) {

        event.preventDefault();

        dropZone.classList.add("dragover");

    }
);


dropZone.addEventListener(
    "dragleave",
    function () {

        dropZone.classList.remove(
            "dragover"
        );

    }
);


dropZone.addEventListener(
    "drop",
    function (event) {

        event.preventDefault();

        dropZone.classList.remove(
            "dragover"
        );

        const files =
            event.dataTransfer.files;

        if (files.length > 0) {

            handleFile(files[0]);

        }

    }
);


// --------------------------------------------------
// ANALYZE FILE
// --------------------------------------------------

analyzeBtn.addEventListener(
    "click",
    async function () {

        if (!selectedFile) {

            alert("Please select a file first.");

            return;

        }

        showLoading(
            "Analyzing your dataset..."
        );

        const formData = new FormData();

        formData.append(
            "file",
            selectedFile
        );


        try {

            const response =
                await fetch(
                    `${API_URL}/analyze`,
                    {
                        method: "POST",
                        body: formData
                    }
                );


            if (!response.ok) {

                const error =
                    await response.json();

                throw new Error(
                    error.detail ||
                    "Analysis failed"
                );

            }


            const data =
                await response.json();


            displayAnalysis(data);


        } catch (error) {

            alert(
                "Backend Error: "
                + error.message
            );

        } finally {

            hideLoading();

        }

    }
);


// --------------------------------------------------
// DISPLAY ANALYSIS
// --------------------------------------------------

function displayAnalysis(data) {

    dashboard.classList.remove(
        "hidden"
    );


    // Rows

    document.getElementById(
        "rowsCount"
    ).textContent =
        data.rows.toLocaleString();


    // Columns

    document.getElementById(
        "columnsCount"
    ).textContent =
        data.columns;


    // Duplicates

    document.getElementById(
        "duplicatesCount"
    ).textContent =
        data.duplicates;


    // Missing values

    let totalMissing = 0;

    for (
        const column in data.missing_values
    ) {

        totalMissing +=
            data.missing_values[column];

    }


    document.getElementById(
        "missingCount"
    ).textContent =
        totalMissing;


    document.getElementById(
        "missingBadge"
    ).textContent =
        totalMissing;


    document.getElementById(
        "columnBadge"
    ).textContent =
        data.columns;


    // Quality score

    calculateQuality(
        data,
        totalMissing
    );


    // Missing list

    displayMissingValues(
        data.missing_values
    );


    // Column list

    displayColumns(
        data.column_names
    );

}


// --------------------------------------------------
// QUALITY SCORE
// --------------------------------------------------

function calculateQuality(
    data,
    missing
) {

    let score = 100;

    if (data.rows > 0) {

        const duplicatePenalty =
            (
                data.duplicates /
                data.rows
            ) * 40;

        score -= duplicatePenalty;

    }


    if (data.columns > 0) {

        const missingPenalty =
            Math.min(
                40,
                (
                    missing /
                    (data.rows *
                        data.columns)
                ) * 100
            );

        score -= missingPenalty;

    }


    score =
        Math.max(
            0,
            Math.round(score)
        );


    const badge =
        document.getElementById(
            "qualityBadge"
        );


    badge.textContent =
        `Quality Score: ${score}%`;

}


// --------------------------------------------------
// MISSING VALUES
// --------------------------------------------------

function displayMissingValues(
    missingValues
) {

    const container =
        document.getElementById(
            "missingList"
        );


    container.innerHTML = "";


    const keys =
        Object.keys(missingValues);


    if (keys.length === 0) {

        container.innerHTML =
            `<p class="empty">
                ✓ No missing values detected.
             </p>`;

        return;

    }


    keys.forEach(column => {

        const row =
            document.createElement(
                "div"
            );

        row.className =
            "list-item";


        row.innerHTML = `

            <span>${escapeHtml(column)}</span>

            <span class="missing-count">
                ${missingValues[column]} missing
            </span>

        `;


        container.appendChild(row);

    });

}


// --------------------------------------------------
// COLUMNS
// --------------------------------------------------

function displayColumns(
    columns
) {

    const container =
        document.getElementById(
            "columnList"
        );


    container.innerHTML = "";


    columns.forEach(column => {

        const tag =
            document.createElement(
                "span"
            );

        tag.className =
            "column-tag";

        tag.textContent =
            column;

        container.appendChild(tag);

    });

}


// --------------------------------------------------
// CLEAN FILE
// --------------------------------------------------

cleanBtn.addEventListener(
    "click",
    async function () {

        if (!selectedFile) {

            alert(
                "Please select a file first."
            );

            return;

        }


        showLoading(
            "Cleaning and restructuring your data..."
        );


        const formData =
            new FormData();

        formData.append(
            "file",
            selectedFile
        );


        try {

            const response =
                await fetch(
                    `${API_URL}/clean`,
                    {
                        method: "POST",
                        body: formData
                    }
                );


            if (!response.ok) {

                const error =
                    await response.json();

                throw new Error(
                    error.detail ||
                    "Cleaning failed"
                );

            }


            // Get cleaned CSV

            cleanedFileBlob =
                await response.blob();


            // Get cleaning report
            // from backend header

            const reportHeader =
                response.headers.get(
                    "X-Cleaning-Report"
                );


            let report = null;


            if (reportHeader) {

                try {

                    report =
                        parseCleaningReport(
                            reportHeader
                        );

                } catch (e) {

                    console.log(
                        "Report parsing failed"
                    );

                }

            }


            displayCleaningResults(
                report
            );


        } catch (error) {

            alert(
                "Backend Error: "
                + error.message
            );

        } finally {

            hideLoading();

        }

    }
);


// --------------------------------------------------
// PARSE CLEANING REPORT
// --------------------------------------------------

function parseCleaningReport(
    text
) {

    /*
       Python dictionary format is not
       exactly JSON, so we extract
       important values using regex.
    */

    const report = {};


    let match;


    match =
        text.match(
            /'original_rows':\s*(\d+)/
        );

    if (match) {

        report.original_rows =
            Number(match[1]);

    }


    match =
        text.match(
            /'final_rows':\s*(\d+)/
        );

    if (match) {

        report.final_rows =
            Number(match[1]);

    }


    match =
        text.match(
            /'duplicates_removed':\s*(\d+)/
        );

    if (match) {

        report.duplicates_removed =
            Number(match[1]);

    }


    match =
        text.match(
            /'empty_rows_removed':\s*(\d+)/
        );

    if (match) {

        report.empty_rows_removed =
            Number(match[1]);

    }


    return report;

}


// --------------------------------------------------
// DISPLAY CLEANING RESULTS
// --------------------------------------------------

function displayCleaningResults(
    report
) {

    cleaningResults.classList.remove(
        "hidden"
    );


    if (!report) {

        return;

    }


    document.getElementById(
        "originalRows"
    ).textContent =
        report.original_rows || 0;


    document.getElementById(
        "finalRows"
    ).textContent =
        report.final_rows || 0;


    document.getElementById(
        "duplicatesRemoved"
    ).textContent =
        report.duplicates_removed || 0;


    document.getElementById(
        "emptyRowsRemoved"
    ).textContent =
        report.empty_rows_removed || 0;

}


// --------------------------------------------------
// DOWNLOAD
// --------------------------------------------------

downloadBtn.addEventListener(
    "click",
    function () {

        if (!cleanedFileBlob) {

            alert(
                "Please clean the dataset first."
            );

            return;

        }


        const url =
            window.URL.createObjectURL(
                cleanedFileBlob
            );


        const link =
            document.createElement(
                "a"
            );


        link.href = url;

        link.download =
            "cleaned_data.csv";


        document.body.appendChild(
            link
        );

        link.click();


        document.body.removeChild(
            link
        );


        window.URL.revokeObjectURL(
            url
        );

    }
);


// --------------------------------------------------
// LOADING
// --------------------------------------------------

function showLoading(message) {

    loadingText.textContent =
        message;

    loading.classList.remove(
        "hidden"
    );

    analyzeBtn.disabled = true;

    cleanBtn.disabled = true;

}


function hideLoading() {

    loading.classList.add(
        "hidden"
    );

    analyzeBtn.disabled = false;

    cleanBtn.disabled = false;

}


// --------------------------------------------------
// SECURITY
// --------------------------------------------------

function escapeHtml(text) {

    const div =
        document.createElement(
            "div"
        );

    div.textContent = text;

    return div.innerHTML;

}
