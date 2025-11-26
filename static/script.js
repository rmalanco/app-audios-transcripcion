// Elementos del DOM
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const transcribeBtn = document.getElementById('transcribeBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultsSection = document.getElementById('resultsSection');
const transcriptionText = document.getElementById('transcriptionText');
const languageBadge = document.getElementById('languageBadge');
const durationBadge = document.getElementById('durationBadge');
const segments = document.getElementById('segments');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const errorMessage = document.getElementById('errorMessage');
const languageSelect = document.getElementById('language');
const taskSelect = document.getElementById('task');

// Nuevos elementos para características reforzadas
const outputFormats = document.getElementById('outputFormats');
const batchModeBtn = document.getElementById('batchModeBtn');
const singleModeBtn = document.getElementById('singleModeBtn');
const batchControls = document.getElementById('batchControls');
const fileList = document.getElementById('fileList');
const clearBatchBtn = document.getElementById('clearBatchBtn');
const transcribeBatchBtn = document.getElementById('transcribeBatchBtn');
const websocketStatus = document.getElementById('websocketStatus');
const downloadSrtBtn = document.getElementById('downloadSrtBtn');
const downloadVttBtn = document.getElementById('downloadVttBtn');
const downloadJsonBtn = document.getElementById('downloadJsonBtn');

let selectedFile = null;
let currentTranscription = null;
let batchFiles = [];
let isBatchMode = false;
let websocket = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// Event listeners
uploadArea.addEventListener('click', () => fileInput.click());
uploadArea.addEventListener('dragover', handleDragOver);
uploadArea.addEventListener('dragleave', handleDragLeave);
uploadArea.addEventListener('drop', handleDrop);
fileInput.addEventListener('change', handleFileSelect);
transcribeBtn.addEventListener('click', handleTranscribe);
copyBtn.addEventListener('click', handleCopy);
downloadBtn.addEventListener('click', handleDownload);

// Nuevos event listeners para características reforzadas
singleModeBtn.addEventListener('click', () => switchMode(false));
batchModeBtn.addEventListener('click', () => switchMode(true));
clearBatchBtn.addEventListener('click', clearBatch);
transcribeBatchBtn.addEventListener('click', handleBatchTranscribe);
downloadSrtBtn.addEventListener('click', () => downloadFormat('srt'));
downloadVttBtn.addEventListener('click', () => downloadFormat('vtt'));
downloadJsonBtn.addEventListener('click', () => downloadFormat('json'));

// Inicializar WebSocket
initializeWebSocket();

function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        if (isBatchMode) {
            // Procesar múltiples archivos en modo lote
            Array.from(files).forEach(processFile);
        } else {
            // Procesar solo el primer archivo en modo individual
            processFile(files[0]);
        }
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        if (isBatchMode) {
            // Procesar múltiples archivos en modo lote
            Array.from(files).forEach(processFile);
        } else {
            // Procesar solo el primer archivo en modo individual
            processFile(files[0]);
        }
    }
}

function processFile(file) {
    // Validar tipo de archivo
    const allowedTypes = ['audio/', 'video/'];
    const isValidType = allowedTypes.some(type => file.type.startsWith(type));

    if (!isValidType) {
        showError('Por favor, selecciona un archivo de audio o video válido.');
        return;
    }

    if (isBatchMode) {
        // Modo lote: agregar a la lista
        if (!batchFiles.some(f => f.name === file.name && f.size === file.size)) {
            batchFiles.push(file);
            updateFileList();
        }
    } else {
        // Modo individual: seleccionar archivo
        selectedFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        fileInfo.style.display = 'flex';
        resultsSection.style.display = 'none';
        errorMessage.style.display = 'none';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

async function handleTranscribe() {
    if (!selectedFile) {
        showError('Por favor, selecciona un archivo primero.');
        return;
    }
    
    // Ocultar resultados anteriores
    resultsSection.style.display = 'none';
    errorMessage.style.display = 'none';
    
    // Mostrar progreso
    progressSection.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = 'Subiendo archivo...';
    
    // Deshabilitar botón
    transcribeBtn.disabled = true;
    transcribeBtn.textContent = 'Procesando...';
    
    try {
        // Simular progreso
        simulateProgress();
        
        // Preparar FormData
        const formData = new FormData();
        formData.append('file', selectedFile);

        const language = languageSelect.value;
        const task = taskSelect.value;
        const outputFormats = getSelectedFormats();

        // Construir URL con parámetros
        let url = '/transcribe';
        const params = new URLSearchParams();
        if (language) params.append('language', language);
        if (task) params.append('task', task);
        outputFormats.forEach(fmt => params.append('output_formats', fmt));
        if (params.toString()) url += '?' + params.toString();
        
        // Enviar request
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al transcribir el audio');
        }
        
        const result = await response.json();
        currentTranscription = result;
        
        // Mostrar resultados
        displayResults(result);
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Ocurrió un error al transcribir el audio. Por favor, intenta de nuevo.');
    } finally {
        // Ocultar progreso
        progressSection.style.display = 'none';
        progressFill.style.width = '0%';
        
        // Habilitar botón
        transcribeBtn.disabled = false;
        transcribeBtn.textContent = 'Transcribir Audio';
    }
}

function simulateProgress() {
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        
        progressFill.style.width = progress + '%';
        
        if (progress >= 90) {
            progressText.textContent = 'Transcribiendo audio... Esto puede tardar unos momentos.';
        }
        
        if (progress >= 100 || !progressSection.style.display || progressSection.style.display === 'none') {
            clearInterval(interval);
        }
    }, 500);
}

function displayResults(result) {
    // Texto principal
    transcriptionText.textContent = result.text;
    
    // Badges de información
    const languageNames = {
        'es': 'Español',
        'en': 'Inglés',
        'fr': 'Francés',
        'de': 'Alemán',
        'it': 'Italiano',
        'pt': 'Portugués'
    };
    
    languageBadge.textContent = `🌐 ${languageNames[result.language] || result.language}`;
    durationBadge.textContent = `⏱️ ${formatDuration(result.duration)}`;
    
    // Segmentos con timestamps
    if (result.segments && result.segments.length > 0) {
        segments.innerHTML = '<h3 style="margin-bottom: 15px; color: var(--text-secondary);">Segmentos:</h3>';
        result.segments.forEach(segment => {
            const segmentDiv = document.createElement('div');
            segmentDiv.className = 'segment';
            segmentDiv.innerHTML = `
                <div class="segment-header">
                    <span>ID: ${segment.id}</span>
                    <span>${formatTime(segment.start)} → ${formatTime(segment.end)}</span>
                </div>
                <div class="segment-text">${segment.text}</div>
            `;
            segments.appendChild(segmentDiv);
        });
    } else {
        segments.innerHTML = '';
    }
    
    // Mostrar sección de resultados
    resultsSection.style.display = 'block';
    progressFill.style.width = '100%';
    progressText.textContent = '¡Transcripción completada!';
    
    // Scroll a resultados
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatDuration(seconds) {
    if (seconds < 60) {
        return `${Math.round(seconds)}s`;
    }
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
}

function handleCopy() {
    if (!currentTranscription) return;
    
    navigator.clipboard.writeText(currentTranscription.text).then(() => {
        copyBtn.textContent = '✓ Copiado';
        setTimeout(() => {
            copyBtn.textContent = '📋 Copiar';
        }, 2000);
    }).catch(err => {
        console.error('Error al copiar:', err);
        showError('No se pudo copiar al portapapeles.');
    });
}

function handleDownload() {
    if (!currentTranscription) return;
    
    const blob = new Blob([currentTranscription.text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedFile.name.replace(/\.[^/.]+$/, '')}_transcripcion.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Funciones para características reforzadas

function switchMode(batchMode) {
    isBatchMode = batchMode;
    singleModeBtn.classList.toggle('active', !batchMode);
    batchModeBtn.classList.toggle('active', batchMode);
    batchControls.style.display = batchMode ? 'block' : 'none';
    fileInfo.style.display = batchMode ? 'none' : (selectedFile ? 'flex' : 'none');

    if (batchMode) {
        fileInput.setAttribute('multiple', 'true');
        uploadArea.querySelector('h2').textContent = 'Arrastra múltiples archivos de audio aquí';
    } else {
        fileInput.removeAttribute('multiple');
        uploadArea.querySelector('h2').textContent = 'Arrastra tu archivo de audio aquí';
        clearBatch();
    }
}

function clearBatch() {
    batchFiles = [];
    updateFileList();
    transcribeBatchBtn.disabled = true;
}

function updateFileList() {
    fileList.innerHTML = '';
    batchFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="file-info">
                <span class="file-name">${file.name}</span>
                <span class="file-size">${formatFileSize(file.size)}</span>
            </div>
            <button class="remove-file" onclick="removeFromBatch(${index})">×</button>
        `;
        fileList.appendChild(fileItem);
    });
    transcribeBatchBtn.disabled = batchFiles.length === 0;
}

function removeFromBatch(index) {
    batchFiles.splice(index, 1);
    updateFileList();
}

function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/transcribe`;

    websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
        updateWebSocketStatus('connected', 'Conectado');
        reconnectAttempts = 0;
    };

    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    websocket.onclose = () => {
        updateWebSocketStatus('disconnected', 'Desconectado');
        attemptReconnect();
    };

    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateWebSocketStatus('disconnected', 'Error de conexión');
    };
}

function updateWebSocketStatus(status, message) {
    const indicator = document.getElementById('statusIndicator');
    const text = document.getElementById('statusText');

    indicator.className = `status-indicator status-${status}`;
    text.textContent = message;
}

function attemptReconnect() {
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        updateWebSocketStatus('connecting', `Reconectando... (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
        setTimeout(initializeWebSocket, 2000 * reconnectAttempts);
    }
}

function handleWebSocketMessage(data) {
    switch (data.status) {
        case 'processing':
            progressSection.style.display = 'block';
            progressFill.style.width = data.progress + '%';
            progressText.textContent = data.message;
            break;
        case 'completed':
            displayResults(data.result);
            break;
        case 'error':
            showError(data.message);
            break;
    }
}

async function handleBatchTranscribe() {
    if (batchFiles.length === 0) return;

    // Preparar archivos para el lote
    const fileIds = [];
    for (const file of batchFiles) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            fileIds.push(result.file_id);
        } catch (error) {
            showError(`Error al subir ${file.name}: ${error.message}`);
            return;
        }
    }

    // Enviar lote para transcripción
    const batchRequest = {
        files: fileIds,
        language: languageSelect.value,
        task: taskSelect.value,
        output_formats: getSelectedFormats()
    };

    try {
        const response = await fetch('/batch/transcribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(batchRequest)
        });

        if (!response.ok) throw new Error('Error en procesamiento por lotes');

        const result = await response.json();
        displayBatchResults(result);

    } catch (error) {
        showError(`Error en procesamiento por lotes: ${error.message}`);
    }
}

function getSelectedFormats() {
    const checkboxes = outputFormats.querySelectorAll('input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function displayBatchResults(result) {
    // Mostrar resultados del lote
    let successCount = result.results.length;
    let errorCount = result.errors.length;

    const message = `Lote procesado: ${successCount} exitosos, ${errorCount} errores`;
    if (errorCount > 0) {
        showError(message);
    } else {
        alert(message);
    }

    // Mostrar el último resultado exitoso
    if (result.results.length > 0) {
        displayResults(result.results[result.results.length - 1]);
    }
}

function downloadFormat(format) {
    if (!currentTranscription) return;

    const baseName = selectedFile.name.replace(/\.[^/.]+$/, '');
    let content = '';
    let mimeType = 'text/plain';
    let extension = format;

    switch (format) {
        case 'srt':
            content = createSRTContent(currentTranscription.segments);
            break;
        case 'vtt':
            content = createVTTContent(currentTranscription.segments);
            mimeType = 'text/vtt';
            break;
        case 'json':
            content = JSON.stringify(currentTranscription, null, 2);
            mimeType = 'application/json';
            break;
        default:
            return;
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${baseName}_transcripcion.${extension}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function createSRTContent(segments) {
    return segments.map((segment, index) => {
        const start = formatTimestamp(segment.start);
        const end = formatTimestamp(segment.end);
        return `${index + 1}\n${start} --> ${end}\n${segment.text}\n`;
    }).join('\n');
}

function createVTTContent(segments) {
    let content = 'WEBVTT\n\n';
    segments.forEach(segment => {
        const start = formatTimestamp(segment.start);
        const end = formatTimestamp(segment.end);
        content += `${start} --> ${end}\n${segment.text}\n\n`;
    });
    return content;
}

function formatTimestamp(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const millis = Math.floor((seconds % 1) * 1000);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${millis.toString().padStart(3, '0')}`;
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    setTimeout(() => {
        errorMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}

