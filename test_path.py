"""
Script de prueba para verificar el manejo de rutas con espacios en Windows
"""
import os
import ctypes
from ctypes import wintypes
from pathlib import Path

def get_short_path_name(long_name):
    """Convierte una ruta larga a formato 8.3 de Windows"""
    if os.name != 'nt':
        return long_name
    
    try:
        _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
        _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        _GetShortPathNameW.restype = wintypes.DWORD
        
        output_buf_size = 0
        while True:
            output_buf = ctypes.create_unicode_buffer(output_buf_size)
            needed = _GetShortPathNameW(long_name, output_buf, output_buf_size)
            if output_buf_size >= needed:
                return output_buf.value
            else:
                output_buf_size = needed
    except Exception as e:
        print(f"Error al obtener ruta corta: {e}")
        return long_name

# Probar con el directorio actual
current_dir = os.getcwd()
print(f"Directorio actual: {current_dir}")
print(f"Tiene espacios: {'Yes' if ' ' in current_dir else 'No'}")

if ' ' in current_dir:
    short_path = get_short_path_name(current_dir)
    print(f"Ruta corta: {short_path}")
    print(f"Ruta corta tiene espacios: {'Yes' if ' ' in short_path else 'No'}")
else:
    print("No hay espacios en la ruta, no es necesario convertir")

# Probar con el directorio temp
temp_dir = Path("temp").resolve()
print(f"\nDirectorio temp: {temp_dir}")
print(f"Tiene espacios: {'Yes' if ' ' in str(temp_dir) else 'No'}")

if ' ' in str(temp_dir):
    if temp_dir.exists():
        short_temp = get_short_path_name(str(temp_dir))
        print(f"Ruta corta del temp: {short_temp}")
        print(f"Ruta corta tiene espacios: {'Yes' if ' ' in short_temp else 'No'}")
    else:
        print("El directorio temp no existe aún")
