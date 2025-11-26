"""
Script para verificar que todos los requisitos estén instalados correctamente
"""
import sys
import subprocess
import os

print("=" * 70)
print("VERIFICACIÓN DE REQUISITOS PARA TRANSCRIPCIÓN DE AUDIO")
print("=" * 70)
print()

# Lista de verificaciones
checks = {
    "Python": False,
    "FFmpeg": False,
    "Whisper": False,
    "FastAPI": False,
    "PyTorch": False
}

# 1. Verificar Python
print("1. Verificando Python...")
try:
    version = sys.version.split()[0]
    major, minor = map(int, version.split('.')[:2])
    if major == 3 and minor >= 8:
        print(f"   ✓ Python {version} instalado (Python 3.8+ requerido)")
        checks["Python"] = True
    else:
        print(f"   ✗ Python {version} instalado (Se requiere Python 3.8 o superior)")
except Exception as e:
    print(f"   ✗ Error al verificar Python: {e}")

print()

# 2. Verificar FFmpeg
print("2. Verificando FFmpeg...")
try:
    result = subprocess.run(
        ["ffmpeg", "-version"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        # Obtener la primera línea que contiene la versión
        first_line = result.stdout.split('\n')[0]
        print(f"   ✓ FFmpeg instalado: {first_line}")
        checks["FFmpeg"] = True
    else:
        print("   ✗ FFmpeg no responde correctamente")
except FileNotFoundError:
    print("   ✗ FFmpeg NO está instalado o no está en el PATH")
    print("   → Instala FFmpeg siguiendo la guía en INSTALACION_FFMPEG.md")
except subprocess.TimeoutExpired:
    print("   ✗ FFmpeg no responde (timeout)")
except Exception as e:
    print(f"   ✗ Error al verificar FFmpeg: {e}")

print()

# 3. Verificar paquetes de Python
print("3. Verificando paquetes de Python...")

# Whisper
try:
    import whisper
    print(f"   ✓ Whisper instalado (versión: {whisper.__version__ if hasattr(whisper, '__version__') else 'desconocida'})")
    checks["Whisper"] = True
except ImportError:
    print("   ✗ Whisper NO está instalado")
    print("   → Ejecuta: pip install -r requirements.txt")

# FastAPI
try:
    import fastapi
    print(f"   ✓ FastAPI instalado (versión: {fastapi.__version__})")
    checks["FastAPI"] = True
except ImportError:
    print("   ✗ FastAPI NO está instalado")
    print("   → Ejecuta: pip install -r requirements.txt")

# PyTorch
try:
    import torch
    print(f"   ✓ PyTorch instalado (versión: {torch.__version__})")
    checks["PyTorch"] = True
    
    # Verificar CUDA (opcional)
    if torch.cuda.is_available():
        print(f"   ℹ GPU CUDA disponible: {torch.cuda.get_device_name(0)}")
    else:
        print("   ℹ GPU CUDA no disponible (se usará CPU, más lento pero funcional)")
except ImportError:
    print("   ✗ PyTorch NO está instalado")
    print("   → Ejecuta: pip install -r requirements.txt")

print()

# 4. Verificar directorios
print("4. Verificando directorios necesarios...")
dirs_to_check = ["uploads", "transcripts", "cache", "temp", "static"]
all_dirs_ok = True

for dir_name in dirs_to_check:
    if os.path.exists(dir_name):
        print(f"   ✓ Directorio '{dir_name}' existe")
    else:
        print(f"   ℹ Directorio '{dir_name}' no existe (se creará automáticamente)")

print()

# 5. Verificar archivos principales
print("5. Verificando archivos principales...")
files_to_check = [
    "app.py",
    "app_reinforced.py",
    "requirements.txt",
    "static/index.html",
    "static/style.css",
    "static/script.js"
]

for file_name in files_to_check:
    if os.path.exists(file_name):
        print(f"   ✓ {file_name}")
    else:
        print(f"   ✗ {file_name} NO encontrado")

print()

# Resumen
print("=" * 70)
print("RESUMEN")
print("=" * 70)

all_ok = all(checks.values())

for check, status in checks.items():
    status_icon = "✓" if status else "✗"
    print(f"{status_icon} {check}")

print()

if all_ok:
    print("✓ ¡Todos los requisitos están instalados!")
    print()
    print("Puedes iniciar la aplicación con:")
    print("  python app.py")
    print()
    print("O con uvicorn:")
    print("  uvicorn app:app --reload --host 0.0.0.0 --port 8000")
else:
    print("✗ Faltan algunos requisitos. Por favor, revisa los errores arriba.")
    print()
    if not checks["FFmpeg"]:
        print("IMPORTANTE: FFmpeg es OBLIGATORIO")
        print("  → Consulta INSTALACION_FFMPEG.md para instrucciones de instalación")
    if not checks["Whisper"] or not checks["FastAPI"] or not checks["PyTorch"]:
        print()
        print("Para instalar los paquetes faltantes de Python:")
        print("  pip install -r requirements.txt")

print()
print("=" * 70)
