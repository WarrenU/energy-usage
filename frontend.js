// --- DOM element references ---
const dropArea = document.getElementById('drop-area');
const fileElem = document.getElementById('fileElem');
const fileList = document.getElementById('file-list');
const form = document.getElementById('csv-form');
const thresholdInput = document.getElementById('threshold');
const alertsDiv = document.getElementById('alerts');
const summaryDiv = document.getElementById('summary');
let files = [];

// --- Drag-and-drop and file selection logic ---
// Highlight drop area on drag
['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
        dropArea.classList.add('highlight');
    }, false);
});
// Remove highlight on drag leave or drop
['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
        dropArea.classList.remove('highlight');
    }, false);
});
// Handle files dropped into the area
dropArea.addEventListener('drop', e => {
    files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.csv'));
    updateFileList();
});
// Handle files selected via the file input
fileElem.addEventListener('change', e => {
    files = Array.from(e.target.files);
    updateFileList();
});
// Update the file list display
function updateFileList() {
    fileList.innerHTML = files.map(f => `<div>${f.name}</div>`).join('');
}

// --- Form submission and API call ---
form.addEventListener('submit', async e => {
    e.preventDefault();
    alertsDiv.innerHTML = '';
    summaryDiv.innerHTML = '';
    // Validate at least one file selected
    if (!files.length) {
        alertsDiv.innerHTML = '<div class="alert">Please select at least one CSV file.</div>';
        return;
    }
    // Prepare form data for upload
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    formData.append('threshold', thresholdInput.value);
    try {
        // Send POST request to FastAPI backend
        const res = await fetch('http://127.0.0.1:8000/energy/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        // Display alerts (errors or threshold warnings)
        if (data.alerts && data.alerts.length) {
            alertsDiv.innerHTML = data.alerts.map(a => `<div class="${a.startsWith('ALERT') ? 'alert' : 'log'}">${a}</div>`).join('');
        }
        // Display summary of days exceeding threshold
        if (data.exceededThresholds && data.exceededThresholds.length) {
            summaryDiv.innerHTML = '<b>Days Exceeding Threshold:</b><ul>' +
                data.exceededThresholds.map(e => `<li>${e.date} (${e.filename}): ${e.usage} (threshold: ${e.threshold})</li>`).join('') + '</ul>';
        }
        // Reset file list on success
        if (data.status === 'success') {
            files = [];
            updateFileList();
            fileElem.value = '';
        }
    } catch (err) {
        alertsDiv.innerHTML = '<div class="alert">Upload failed.</div>';
    }
}); 