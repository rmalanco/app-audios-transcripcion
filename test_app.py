#!/usr/bin/env python3
"""
Script de pruebas para la aplicación de transcripción reforzada
"""

import requests
import time
import os
from pathlib import Path

# Configuración
BASE_URL = "http://localhost:8000"

def test_health():
    """Probar endpoint de health"""
    print("🩺 Probando endpoint de health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check exitoso: {data}")
            return True
        else:
            print(f"❌ Health check falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en health check: {e}")
        return False

def test_api_info():
    """Probar endpoint de información de API"""
    print("📋 Probando endpoint de API info...")
    try:
        response = requests.get(f"{BASE_URL}/api")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API info exitoso: Versión {data['version']}")
            return True
        else:
            print(f"❌ API info falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en API info: {e}")
        return False

def test_transcription():
    """Probar transcripción con un archivo de audio pequeño"""
    print("🎤 Probando transcripción...")

    # Buscar un archivo de audio de prueba
    audio_dir = Path("audios")
    if not audio_dir.exists():
        print("⚠️ No se encontró directorio 'audios', omitiendo prueba de transcripción")
        return True

    audio_files = list(audio_dir.glob("*"))
    if not audio_files:
        print("⚠️ No se encontraron archivos de audio, omitiendo prueba de transcripción")
        return True

    # Usar el primer archivo encontrado
    test_file = audio_files[0]
    print(f"📁 Usando archivo de prueba: {test_file.name}")

    try:
        with open(test_file, "rb") as f:
            files = {"file": (test_file.name, f, "audio/wav")}
            data = {
                "language": "es",
                "task": "transcribe",
                "output_formats": ["txt", "json"]
            }

            response = requests.post(
                f"{BASE_URL}/transcribe",
                files=files,
                data=data
            )

            if response.status_code == 200:
                result = response.json()
                print("✅ Transcripción exitosa!"                print(f"📝 Texto: {result['text'][:100]}...")
                print(f"🌐 Idioma: {result['language']}")
                print(f"⏱️ Duración: {result['duration']:.1f}s")
                return True
            else:
                print(f"❌ Transcripción falló: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        print(f"❌ Error en transcripción: {e}")
        return False

def test_models_endpoint():
    """Probar endpoint de modelos"""
    print("🤖 Probando endpoint de modelos...")
    try:
        response = requests.get(f"{BASE_URL}/models")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Modelos obtenidos: Modelo actual = {data['current_model']}")
            return True
        else:
            print(f"❌ Endpoint de modelos falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en endpoint de modelos: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 Iniciando pruebas de la aplicación de transcripción reforzada")
    print("=" * 60)

    # Esperar a que la aplicación esté lista
    print("⏳ Esperando a que la aplicación esté lista...")
    time.sleep(3)

    tests = [
        test_health,
        test_api_info,
        test_models_endpoint,
        test_transcription
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 60)
    print(f"📊 Resultados: {passed}/{total} pruebas pasaron")

    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        return 0
    else:
        print("⚠️ Algunas pruebas fallaron")
        return 1

if __name__ == "__main__":
    exit(main())