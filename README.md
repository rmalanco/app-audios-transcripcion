# 🎤 Aplicación de Transcripción de Audio a Texto - Versión Reforzada

Aplicación web moderna y avanzada para convertir archivos de audio en transcripciones de texto usando **OpenAI Whisper**, con características reforzadas para mayor funcionalidad y rendimiento.

## ✨ Características

- 🎯 **Alta precisión**: Utiliza el modelo Whisper de OpenAI para transcripciones precisas
- 🌍 **Multiidioma**: Soporta múltiples idiomas (español, inglés, francés, alemán, italiano, portugués, y más)
- 🔄 **Traducción**: Opción para traducir el audio directamente al inglés
- 📁 **Múltiples formatos**: Soporta WAV, MP3, M4A, OGG, FLAC, WEBM, MP4
- 🎨 **Interfaz moderna**: Diseño elegante y fácil de usar con drag & drop
- ⚡ **Tiempo real**: Muestra el progreso de la transcripción con WebSocket
- 💾 **Múltiples formatos de exportación**: TXT, SRT, VTT, JSON
- 📊 **Segmentos con timestamps**: Visualiza la transcripción con timestamps precisos
- 📦 **Procesamiento por lotes**: Transcribe múltiples archivos simultáneamente
- 🔄 **Cache inteligente**: Reutiliza resultados para archivos procesados anteriormente
- 🛡️ **Validación robusta**: Límites de tamaño de archivo y validación de tipos
- 📝 **Logging completo**: Seguimiento detallado de operaciones
- 🐳 **Docker**: Fácil despliegue con contenedores

## 🚀 Instalación

### ⚠️ IMPORTANTE: Requisito de FFmpeg

**FFmpeg es OBLIGATORIO para que la aplicación funcione**. Sin FFmpeg, obtendrás errores como:
```
[WinError 2] El sistema no puede encontrar el archivo especificado
```

**Instalación de FFmpeg:**

- **Windows**: 
  - **Opción 1 (Recomendada)**: Usar Chocolatey: `choco install ffmpeg`
  - **Opción 2**: Descargar desde https://www.gyan.dev/ffmpeg/builds/ y agregar al PATH
  - **Ver guía detallada**: [INSTALACION_FFMPEG.md](INSTALACION_FFMPEG.md)
- **Linux**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`

**Verificar instalación:**
```bash
ffmpeg -version
```

### Opción 1: Instalación Nativa

#### Requisitos previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- **FFmpeg** (ver sección anterior - OBLIGATORIO)

#### Pasos de instalación

1. **Clonar o descargar el repositorio**

2. **Crear un entorno virtual (recomendado)**

```bash
python -m venv venv
```

3. **Activar el entorno virtual**

   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **Linux/Mac:**
     ```bash
     source venv/bin/activate
     ```

4. **Instalar las dependencias**

```bash
pip install -r requirements.txt
```

> ⚠️ **Nota**: La primera vez que ejecutes la aplicación, Whisper descargará el modelo seleccionado (por defecto "base"). Esto puede tardar unos minutos y requerir varios GB de espacio en disco.

### Opción 2: Docker (Recomendado)

#### Requisitos previos

- Docker
- Docker Compose (opcional)

#### Despliegue con Docker Compose

```bash
# Construir e iniciar la aplicación
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener la aplicación
docker-compose down
```

#### Despliegue con Docker puro

```bash
# Construir la imagen
docker build -t transcription-app .

# Ejecutar el contenedor
docker run -p 8000:8000 -v $(pwd)/uploads:/app/uploads -v $(pwd)/transcripts:/app/transcripts transcription-app
```

### Pasos de instalación

1. **Clonar o descargar el repositorio**

2. **Crear un entorno virtual (recomendado)**

```bash
python -m venv venv
```

3. **Activar el entorno virtual**

   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **Linux/Mac:**
     ```bash
     source venv/bin/activate
     ```

4. **Instalar las dependencias**

```bash
pip install -r requirements.txt
```

> ⚠️ **Nota**: La primera vez que ejecutes la aplicación, Whisper descargará el modelo seleccionado (por defecto "base"). Esto puede tardar unos minutos y requerir varios GB de espacio en disco.

## 🎮 Uso

### Iniciar el servidor

```bash
python app.py
```

O usando uvicorn directamente:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Acceder a la aplicación

Abre tu navegador y visita:

```
http://localhost:8000
```

### Usar la aplicación

#### Modo Archivo Individual
1. **Seleccionar modo**: Haz clic en "Archivo Individual"
2. **Subir archivo de audio**:
    - Arrastra y suelta un archivo de audio en la zona de carga
    - O haz clic para seleccionar un archivo

3. **Configurar opciones**:
    - Selecciona el idioma si lo conoces (o deja "Auto-detectar")
    - Elige entre "Transcribir" o "Traducir a inglés"
    - Selecciona los formatos de salida: TXT, SRT, VTT, JSON

4. **Transcribir**:
    - Haz clic en "Transcribir Audio"
    - Observa el progreso en tiempo real vía WebSocket

5. **Ver y descargar resultados**:
    - Revisa la transcripción completa
    - Explora los segmentos con timestamps
    - Descarga en múltiples formatos

#### Modo Procesamiento por Lotes
1. **Seleccionar modo**: Haz clic en "Procesamiento por Lotes"
2. **Subir múltiples archivos**:
    - Arrastra y suelta múltiples archivos de audio
    - O haz clic para seleccionar varios archivos

3. **Configurar opciones**: Igual que el modo individual
4. **Transcribir lote**: Haz clic en "Transcribir Lote"
5. **Ver resultados**: Se procesan todos los archivos y se muestran los resultados consolidados

## ⚙️ Configuración

### Modelos de Whisper

Puedes cambiar el modelo de Whisper configurando la variable de entorno `WHISPER_MODEL`:

```bash
# Windows PowerShell
$env:WHISPER_MODEL="small"
python app.py

# Linux/Mac
export WHISPER_MODEL="small"
python app.py
```

**Modelos disponibles** (de menor a mayor precisión y tamaño):
- `tiny`: ~39 MB, más rápido, menor precisión
- `base`: ~74 MB (por defecto), balance entre velocidad y precisión
- `small`: ~244 MB, mejor precisión
- `medium`: ~769 MB, alta precisión
- `large`: ~1550 MB, máxima precisión

### Puerto del servidor

Por defecto, el servidor se ejecuta en el puerto 8000. Puedes cambiarlo modificando el código en `app.py` o usando uvicorn:

```bash
uvicorn app:app --port 8080
```

## 📁 Estructura del proyecto

```
app-audios-transcripcion/
├── app.py                 # Backend FastAPI
├── requirements.txt       # Dependencias Python
├── .env.example          # Ejemplo de configuración
├── README.md             # Este archivo
├── static/               # Frontend
│   ├── index.html       # Interfaz principal
│   ├── style.css        # Estilos
│   └── script.js        # Lógica del frontend
├── uploads/             # Archivos subidos (se crea automáticamente)
├── transcripts/         # Transcripciones guardadas (se crea automáticamente)
└── audios/              # Tus archivos de audio
```

## 🔧 API Endpoints

### `GET /`
Información básica de la API

### `GET /health`
Verificar el estado del servidor y modelo

### `POST /transcribe`
Transcribir un archivo de audio

**Parámetros:**
- `file`: Archivo de audio (multipart/form-data)
- `language`: Código de idioma (opcional, ej: "es", "en")
- `task`: "transcribe" o "translate" (opcional, por defecto "transcribe")

**Respuesta:**
```json
{
  "text": "Texto transcrito completo...",
  "language": "es",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.2,
      "text": "Primer segmento..."
    }
  ],
  "filename": "audio.wav",
  "duration": 120.5
}
```

### `GET /transcripts`
Listar todas las transcripciones guardadas

### `GET /transcripts/{filename}`
Obtener una transcripción específica

## 🐛 Solución de problemas

### Error: "[WinError 2] El sistema no puede encontrar el archivo especificado"

**Este es el error más común y significa que FFmpeg NO está instalado o no está en el PATH.**

**Solución:**
1. Instala FFmpeg siguiendo la guía: [INSTALACION_FFMPEG.md](INSTALACION_FFMPEG.md)
2. Verifica que funciona ejecutando `ffmpeg -version` en una **nueva terminal**
3. **Reinicia completamente** VS Code o tu terminal
4. Intenta de nuevo

### Error: "No module named 'whisper'"
Asegúrate de haber instalado todas las dependencias:
```bash
pip install -r requirements.txt
```

### Error: "CUDA out of memory"
Si tienes una GPU NVIDIA pero se queda sin memoria:
- Usa un modelo más pequeño (`tiny` o `base`)
- O procesa archivos más cortos

### La transcripción es lenta
- Usa un modelo más pequeño (`tiny` o `base`)
- Los archivos largos tardan más en procesarse
- El primer uso es más lento porque descarga el modelo

### Error al subir archivos grandes
Aumenta el límite de tamaño en FastAPI o divide el archivo en segmentos más pequeños.

### Errores con rutas que contienen espacios en Windows

La aplicación ahora maneja automáticamente rutas con espacios usando:
- Conversión a rutas cortas de Windows (formato 8.3)
- Copia de archivos a ubicaciones temporales sin espacios

Si aún tienes problemas, intenta mover el proyecto a una ruta sin espacios, por ejemplo:
```
C:\proyectos\app-audios-transcripcion
```

## 📝 Notas

- Las transcripciones se guardan automáticamente en la carpeta `transcripts/`
- El modelo se carga en memoria al iniciar el servidor
- Para producción, considera usar un servidor WSGI como Gunicorn
- En producción, configura CORS adecuadamente en lugar de permitir todos los orígenes

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Haz fork del proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto utiliza Whisper de OpenAI, que es de código abierto bajo la licencia MIT.

## 🙏 Agradecimientos

- [OpenAI Whisper](https://github.com/openai/whisper) por el modelo de transcripción
- [FastAPI](https://fastapi.tiangolo.com/) por el framework web
- [Uvicorn](https://www.uvicorn.org/) por el servidor ASGI

---

**Desarrollado con ❤️ para facilitar la transcripción de audio a texto**

