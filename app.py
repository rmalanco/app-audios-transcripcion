"""
Aplicación de transcripción de audio a texto - Versión Reforzada
Usa Whisper de OpenAI para convertir archivos de audio en texto
Mejoras: procesamiento por lotes, WebSockets, subtítulos, logging, etc.
"""

import os
import tempfile
import warnings
import logging
import asyncio
from pathlib import Path
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from datetime import datetime
import uuid

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suprimir advertencias de FP16 en CPU (es normal)
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

import whisper
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

# Importaciones locales
import models
import auth
from database import engine, get_db

# Crear tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

# Modelos Pydantic para validación
class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TranscriptionRequest(BaseModel):
    language: Optional[str] = None
    task: str = "transcribe"
    output_formats: List[str] = ["txt"]

class BatchTranscriptionRequest(BaseModel):
    files: List[str]  # Lista de IDs de archivos
    language: Optional[str] = None
    task: str = "transcribe"
    output_formats: List[str] = ["txt"]

class TranscriptionResult(BaseModel):
    id: str
    text: str
    language: str
    segments: List[dict]
    filename: str
    duration: float
    created_at: datetime

# Configuración
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
SUPPORTED_FORMATS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4", ".wmv"}
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]

app = FastAPI(
    title="Transcripción de Audio a Texto - Versión Reforzada",
    description="API avanzada para convertir archivos de audio en transcripciones de texto usando Whisper",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorios
UPLOAD_DIR = Path("uploads")
TRANSCRIPTS_DIR = Path("transcripts")
CACHE_DIR = Path("cache")
TEMP_DIR = Path("temp")

for dir_path in [UPLOAD_DIR, TRANSCRIPTS_DIR, CACHE_DIR, TEMP_DIR]:
    dir_path.mkdir(exist_ok=True)

# Pool de hilos para procesamiento
executor = ThreadPoolExecutor(max_workers=4)

# Cache de modelos
model_cache = {}

# Cargar modelo Whisper
MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")
logger.info(f"Cargando modelo Whisper: {MODEL_SIZE}...")

try:
    model = whisper.load_model(MODEL_SIZE)
    logger.info("Modelo cargado exitosamente!")
except Exception as e:
    logger.error(f"Error al cargar el modelo: {e}")
    logger.info("Intentando con modelo 'tiny' como alternativa...")
    try:
        model = whisper.load_model("tiny")
        MODEL_SIZE = "tiny"
        logger.info("Modelo 'tiny' cargado exitosamente!")
    except Exception as e2:
        logger.critical(f"Error crítico: No se pudo cargar ningún modelo. {e2}")
        raise

# Funciones de utilidad
def get_file_hash(file_path: Path) -> str:
    """Calcula el hash SHA256 de un archivo para cache"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def format_timestamp(seconds: float) -> str:
    """Formatea segundos a timestamp SRT (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def create_srt_content(segments: List[dict]) -> str:
    """Crea contenido SRT desde segmentos"""
    srt_lines = []
    for i, segment in enumerate(segments, 1):
        start_time = format_timestamp(segment['start'])
        end_time = format_timestamp(segment['end'])
        text = segment['text'].strip()

        srt_lines.extend([
            str(i),
            f"{start_time} --> {end_time}",
            text,
            ""
        ])

    return "\n".join(srt_lines)

def create_vtt_content(segments: List[dict]) -> str:
    """Crea contenido VTT desde segmentos"""
    vtt_lines = ["WEBVTT", ""]

    for segment in segments:
        start_time = format_timestamp(segment['start'])
        end_time = format_timestamp(segment['end'])
        text = segment['text'].strip()

        vtt_lines.extend([
            f"{start_time} --> {end_time}",
            text,
            ""
        ])

    return "\n".join(vtt_lines)

async def process_transcription(
    file_path: Path,
    language: Optional[str] = None,
    task: str = "transcribe",
    websocket: Optional[WebSocket] = None
) -> dict:
    """Procesa la transcripción de un archivo de audio"""
    try:
        # Calcular hash para cache
        file_hash = get_file_hash(file_path)
        cache_file = CACHE_DIR / f"{file_hash}.json"

        # Verificar cache
        if cache_file.exists():
            logger.info(f"Usando resultado cacheado para {file_path.name}")
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)

        # Enviar progreso inicial
        if websocket:
            await websocket.send_json({"status": "processing", "progress": 10, "message": "Iniciando transcripción..."})

        # Configurar opciones de transcripción
        transcribe_options = {
            "task": task,
            "verbose": False,
            "fp16": False
        }

        if language:
            transcribe_options["language"] = language

        # Callback de progreso
        def progress_callback(progress):
            if websocket:
                asyncio.create_task(
                    websocket.send_json({
                        "status": "processing",
                        "progress": 10 + int(progress * 80),
                        "message": f"Transcribiendo... {int(progress * 100)}%"
                    })
                )

        # Verificar que el archivo existe antes de transcribir
        if not file_path.exists():
            raise Exception(f"Archivo temporal no encontrado: {file_path}")

        logger.info(f"Iniciando transcripción de {file_path}")

        # Convertir a ruta absoluta y asegurar que es una cadena
        abs_file_path = str(file_path.resolve())
        
        # Verificar nuevamente con la ruta absoluta
        if not os.path.exists(abs_file_path):
            raise Exception(f"Archivo no encontrado en ruta absoluta: {abs_file_path}")
        
        # Verificar que el archivo es accesible
        try:
            with open(abs_file_path, 'rb') as test_file:
                test_file.read(1)
        except Exception as e:
            raise Exception(f"Archivo no es accesible: {abs_file_path}, error: {e}")
        
        logger.info(f"Ruta absoluta verificada y accesible: {abs_file_path}")

        # Función auxiliar para ejecutar la transcripción en el executor
        def run_transcription():
            # Crear una copia del archivo en una ruta más simple (sin espacios problemáticos)
            import shutil
            import subprocess
            
            # Obtener la extensión del archivo original
            original_path = Path(abs_file_path)
            file_ext = original_path.suffix if original_path.suffix else '.wav'
            
            # En Windows, usar una ruta absolutamente simple sin espacios
            # Usar el directorio temp del proyecto en lugar del sistema
            temp_dir = str(TEMP_DIR.resolve())
            simple_filename = f"w_{uuid.uuid4().hex[:8]}{file_ext}"
            simple_path = os.path.join(temp_dir, simple_filename)
            
            # En Windows, obtener ruta corta (8.3 format) si es posible
            if os.name == 'nt':  # Windows
                try:
                    # Intentar obtener el nombre corto de Windows (sin espacios)
                    import ctypes
                    from ctypes import wintypes
                    
                    _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
                    _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
                    _GetShortPathNameW.restype = wintypes.DWORD
                    
                    def get_short_path_name(long_name):
                        """Convierte una ruta larga a formato 8.3 de Windows"""
                        output_buf_size = 0
                        while True:
                            output_buf = ctypes.create_unicode_buffer(output_buf_size)
                            needed = _GetShortPathNameW(long_name, output_buf, output_buf_size)
                            if output_buf_size >= needed:
                                return output_buf.value
                            else:
                                output_buf_size = needed
                    
                    # Asegurarse de que el directorio temp existe antes de obtener ruta corta
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir, exist_ok=True)
                    
                    # Obtener ruta corta del directorio temp
                    try:
                        short_temp_dir = get_short_path_name(temp_dir)
                        simple_path = os.path.join(short_temp_dir, simple_filename)
                        logger.info(f"Usando ruta corta de Windows: {simple_path}")
                    except Exception as e:
                        logger.warning(f"No se pudo obtener ruta corta, usando ruta normal: {e}")
                        
                except Exception as e:
                    logger.warning(f"No se pudo usar API de Windows para rutas cortas: {e}")
            
            try:
                # Copiar el archivo a la ubicación simple
                logger.info(f"Copiando archivo de: {abs_file_path}")
                logger.info(f"Copiando archivo a: {simple_path}")
                
                # Asegurar que el directorio existe
                os.makedirs(os.path.dirname(simple_path), exist_ok=True)
                
                shutil.copy2(str(abs_file_path), simple_path)
                
                # Verificar que la copia existe y es accesible
                if not os.path.exists(simple_path):
                    raise Exception(f"No se pudo crear copia del archivo: {simple_path}")
                
                # Verificar tamaño del archivo copiado
                original_size = os.path.getsize(abs_file_path)
                copied_size = os.path.getsize(simple_path)
                logger.info(f"Archivo copiado: {copied_size} bytes (original: {original_size} bytes)")
                
                if copied_size != original_size:
                    raise Exception(f"El archivo copiado tiene tamaño diferente: {copied_size} vs {original_size}")
                
                logger.info(f"Archivo copiado exitosamente, iniciando transcripción...")
                
                # Esperar un poco para asegurar que el archivo está completamente escrito
                import time
                time.sleep(0.1)
                
                # Suprimir advertencias durante la transcripción
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore")
                    # Usar la ruta simple para Whisper
                    # Convertir a string absoluto para evitar cualquier problema
                    whisper_path = os.path.abspath(simple_path)
                    logger.info(f"Ruta absoluta para Whisper: {whisper_path}")
                    result = model.transcribe(whisper_path, **transcribe_options)
                
                logger.info(f"Transcripción completada exitosamente")
                return result
            except Exception as e:
                logger.error(f"Error durante la transcripción: {e}")
                logger.error(f"Ruta del archivo copiado: {simple_path}")
                logger.error(f"Archivo copiado existe: {os.path.exists(simple_path)}")
                raise
            finally:
                # Limpiar el archivo temporal copiado
                try:
                    if os.path.exists(simple_path):
                        os.unlink(simple_path)
                        logger.info(f"Archivo temporal copiado eliminado: {simple_path}")
                except Exception as e:
                    logger.warning(f"No se pudo eliminar archivo temporal copiado: {e}")

        # Ejecutar transcripción en el executor
        result = await asyncio.get_event_loop().run_in_executor(
            executor,
            run_transcription
        )

        logger.info(f"Transcripción completada para {file_path}")

        # Enviar progreso final
        if websocket:
            await websocket.send_json({"status": "processing", "progress": 90, "message": "Finalizando..."})

        # Extraer información
        transcription = {
            "id": str(uuid.uuid4()),
            "text": result["text"].strip(),
            "language": result.get("language", "unknown"),
            "segments": [
                {
                    "id": seg["id"],
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip()
                }
                for seg in result.get("segments", [])
            ],
            "filename": file_path.name,
            "duration": result.get("duration", 0),
            "created_at": datetime.now().isoformat()
        }

        # Guardar en cache
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(transcription, f, ensure_ascii=False, indent=2)

        # Enviar resultado final
        if websocket:
            await websocket.send_json({"status": "completed", "progress": 100, "result": transcription})

        return transcription

    except Exception as e:
        logger.error(f"Verificando existencia del archivo antes del error: {file_path.exists()}")
        logger.error(f"Ruta del archivo: {file_path}")
        logger.error(f"Ruta absoluta: {file_path.resolve()}")
        error_msg = f"Error al transcribir {file_path.name}: {str(e)}"
        logger.error(error_msg)
        if websocket:
            await websocket.send_json({"status": "error", "message": error_msg})
        raise HTTPException(status_code=500, detail=error_msg)

# Endpoints de la API
@app.get("/api")
async def api_info():
    """Información de la API"""
    return {
        "message": "API de Transcripción de Audio - Versión Reforzada",
        "version": "2.0.0",
        "model": MODEL_SIZE,
        "max_file_size": MAX_FILE_SIZE,
        "supported_formats": list(SUPPORTED_FORMATS)
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model_size": MODEL_SIZE,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/transcribe")
async def transcribe_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: Optional[str] = None,
    task: str = "transcribe",
    output_formats: List[str] = ["txt"],
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Transcribe un archivo de audio a texto

    Args:
        file: Archivo de audio
        language: Código de idioma (opcional)
        task: "transcribe" o "translate"
        output_formats: Formatos de salida ["txt", "srt", "vtt", "json"]

    Returns:
        JSON con la transcripción y metadatos
    """
    # Validar archivo
    if not file.filename:
        raise HTTPException(status_code=400, detail="No se proporcionó un archivo")

    # Validar extensión
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado. Formatos permitidos: {', '.join(SUPPORTED_FORMATS)}"
        )

    # Validar tamaño del archivo
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo demasiado grande. Máximo permitido: {MAX_FILE_SIZE / (1024*1024):.0f}MB"
        )

    # Crear archivo temporal en nuestro directorio temp
    temp_path = None
    try:
        # Sanitizar el nombre del archivo para evitar problemas con espacios y caracteres especiales
        import re
        # Obtener solo el nombre sin la extensión
        file_stem = Path(file.filename).stem
        file_ext = Path(file.filename).suffix
        
        # Sanitizar el nombre (mantener solo letras, números, guiones y guiones bajos)
        safe_stem = re.sub(r'[^\w\-_]', '_', file_stem)
        safe_stem = re.sub(r'_+', '_', safe_stem)  # Eliminar guiones bajos múltiples
        safe_stem = safe_stem.strip('_')  # Eliminar guiones bajos al inicio/final
        
        # Combinar con extensión
        safe_filename = f"{safe_stem}{file_ext}"
        
        # Crear nombre único para el archivo temporal
        import uuid
        temp_filename = f"whisper_{uuid.uuid4().hex}_{safe_filename}"
        temp_path = TEMP_DIR / temp_filename

        # Asegurar que el directorio existe
        TEMP_DIR.mkdir(exist_ok=True)

        # Escribir contenido del archivo
        with open(temp_path, "wb") as tmp_file:
            tmp_file.write(file_content)
            tmp_file.flush()
            # Forzar escritura al disco
            if hasattr(tmp_file, 'fileno'):
                try:
                    os.fsync(tmp_file.fileno())
                except:
                    pass

        # Verificar que el archivo se creó correctamente
        if not temp_path.exists():
            raise HTTPException(status_code=500, detail="Error al crear archivo temporal")
        
        # Obtener ruta absoluta pero mantener como Path
        temp_path = temp_path.resolve()
        logger.info(f"Archivo temporal creado: {temp_path}")

        # Pequeña pausa para asegurar que el archivo esté completamente escrito
        await asyncio.sleep(0.2)
        
        # Verificar nuevamente que existe antes de procesar
        if not temp_path.exists():
            raise HTTPException(status_code=500, detail="Archivo temporal desapareció antes de procesar")
        
        # Verificar que podemos leer el archivo
        try:
            with open(temp_path, 'rb') as test:
                test.read(1)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Archivo temporal no es accesible: {e}")

        # Procesar transcripción (pasar como Path, no como string)
        result = await process_transcription(
            temp_path,
            language=language,
            task=task
        )

        # Generar archivos de salida adicionales
        output_files = {}
        base_name = Path(file.filename).stem

        for fmt in output_formats:
            if fmt == "txt":
                transcript_file = TRANSCRIPTS_DIR / f"{base_name}.txt"
                with open(transcript_file, "w", encoding="utf-8") as f:
                    f.write(result["text"])
                output_files["txt"] = str(transcript_file)

            elif fmt == "srt":
                srt_file = TRANSCRIPTS_DIR / f"{base_name}.srt"
                srt_content = create_srt_content(result["segments"])
                with open(srt_file, "w", encoding="utf-8") as f:
                    f.write(srt_content)
                output_files["srt"] = str(srt_file)

            elif fmt == "vtt":
                vtt_file = TRANSCRIPTS_DIR / f"{base_name}.vtt"
                vtt_content = create_vtt_content(result["segments"])
                with open(vtt_file, "w", encoding="utf-8") as f:
                    f.write(vtt_content)
                output_files["vtt"] = str(vtt_file)

            elif fmt == "json":
                json_file = TRANSCRIPTS_DIR / f"{base_name}.json"
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                output_files["json"] = str(json_file)

        result["output_files"] = output_files
        
        # Guardar en base de datos
        db_transcript = models.Transcript(
            filename=file.filename,
            text=result["text"],
            language=result["language"],
            duration=result["duration"],
            user_id=current_user.id,
            file_path=output_files.get("txt", "") # Guardamos la ruta del TXT como referencia
        )
        db.add(db_transcript)
        db.commit()
        db.refresh(db_transcript)
        
        # Añadir ID de base de datos al resultado
        result["db_id"] = db_transcript.id
        
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error en transcripción: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Limpiar archivo temporal (solo después de que la transcripción termine)
        # No eliminar aquí, dejar que se elimine después de procesar
        # El archivo se eliminará en un background task después de un delay
        if temp_path and temp_path.exists():
            async def cleanup_file():
                await asyncio.sleep(5)  # Esperar 5 segundos después de completar
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                        logger.info(f"Archivo temporal eliminado: {temp_path}")
                except (OSError, PermissionError) as e:
                    logger.warning(f"No se pudo eliminar archivo temporal {temp_path}: {e}")
            
            # Programar limpieza en background
            background_tasks.add_task(cleanup_file)

@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """WebSocket para transcripción en tiempo real"""
    await websocket.accept()
    try:
        # Recibir configuración inicial
        config = await websocket.receive_json()
        logger.info(f"Conexión WebSocket iniciada con config: {config}")

        # Procesar archivo si se proporciona
        if "file_id" in config:
            file_path = UPLOAD_DIR / config["file_id"]
            if not file_path.exists():
                await websocket.send_json({"status": "error", "message": "Archivo no encontrado"})
                return

            await process_transcription(
                file_path,
                language=config.get("language"),
                task=config.get("task", "transcribe"),
                websocket=websocket
            )

    except WebSocketDisconnect:
        logger.info("Cliente WebSocket desconectado")
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
        await websocket.send_json({"status": "error", "message": str(e)})

@app.post("/batch/transcribe")
async def batch_transcribe(request: BatchTranscriptionRequest):
    """
    Transcribe múltiples archivos de audio por lotes

    Args:
        request: Configuración del lote con lista de archivos

    Returns:
        Resultados de todas las transcripciones
    """
    results = []
    errors = []

    for file_id in request.files:
        try:
            file_path = UPLOAD_DIR / file_id
            if not file_path.exists():
                errors.append({"file_id": file_id, "error": "Archivo no encontrado"})
                continue

            result = await process_transcription(
                file_path,
                language=request.language,
                task=request.task
            )
            results.append(result)

        except Exception as e:
            errors.append({"file_id": file_id, "error": str(e)})

    return {
        "results": results,
        "errors": errors,
        "total_processed": len(results),
        "total_errors": len(errors)
    }

@app.get("/transcripts")
async def list_transcripts(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Lista las transcripciones del usuario actual"""
    transcripts = db.query(models.Transcript).filter(models.Transcript.user_id == current_user.id).all()
    return {"transcripts": transcripts}

@app.get("/transcripts/{filename}")
async def get_transcript(filename: str):
    """Obtiene el contenido de una transcripción"""
    transcript_file = TRANSCRIPTS_DIR / filename

    if not transcript_file.exists():
        raise HTTPException(status_code=404, detail="Transcripción no encontrada")

    with open(transcript_file, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "filename": filename,
        "content": content,
        "size": transcript_file.stat().st_size
    }

@app.get("/models")
async def list_models():
    """Lista los modelos Whisper disponibles"""
    return {
        "current_model": MODEL_SIZE,
        "available_models": WHISPER_MODELS,
        "recommendations": {
            "tiny": "Más rápido, menor precisión",
            "base": "Balance velocidad/precisión",
            "small": "Mejor precisión",
            "medium": "Alta precisión",
            "large": "Máxima precisión"
        }
    }

# Servir archivos estáticos (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Servir index.html en la ruta raíz
@app.get("/", response_class=FileResponse)
async def serve_index():
    """Sirve el frontend en la ruta raíz"""
    return FileResponse("static/index.html")

if __name__ == "__main__":
    logger.info("Iniciando servidor de transcripción reforzado...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )