# Dockerfile para la aplicación de transcripción de audio reforzada
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY app_reinforced.py .
COPY static/ ./static/

# Crear directorios necesarios
RUN mkdir -p uploads transcripts cache temp

# Exponer puerto
EXPOSE 8000

# Variables de entorno
ENV WHISPER_MODEL=base
ENV PORT=8000

# Comando para ejecutar la aplicación
CMD ["python", "app_reinforced.py"]