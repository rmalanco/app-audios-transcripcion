# 🔧 Guía de Instalación de FFmpeg para Windows

FFmpeg es **REQUERIDO** para que Whisper pueda procesar archivos de audio. Sin FFmpeg, obtendrás el error:
```
[WinError 2] El sistema no puede encontrar el archivo especificado
```

## ¿Por qué necesito FFmpeg?

Whisper utiliza FFmpeg para:
- Convertir diferentes formatos de audio (MP3, WAV, M4A, etc.)
- Procesar y normalizar archivos de audio
- Extraer audio de archivos de video (MP4, WEBM, etc.)

## Opciones de Instalación

### Opción 1: Usando Chocolatey (Recomendado para usuarios de Windows)

Si tienes [Chocolatey](https://chocolatey.org/) instalado:

1. Abre PowerShell **como Administrador**
2. Ejecuta:
   ```powershell
   choco install ffmpeg
   ```
3. Cierra y vuelve a abrir tu terminal

### Opción 2: Usando Scoop

Si usas [Scoop](https://scoop.sh/):

1. Abre PowerShell
2. Ejecuta:
   ```powershell
   scoop install ffmpeg
   ```

### Opción 3: Instalación Manual (Más común)

#### Paso 1: Descargar FFmpeg

1. Ve a https://www.gyan.dev/ffmpeg/builds/
2. Descarga **ffmpeg-release-essentials.zip** (alrededor de 70-80 MB)
   - O usa este link directo: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip

#### Paso 2: Extraer el archivo

1. Extrae el archivo ZIP a una ubicación permanente, por ejemplo:
   ```
   C:\ffmpeg
   ```
2. Asegúrate de que la carpeta contenga subcarpetas como `bin`, `doc`, etc.
3. Dentro de `C:\ffmpeg\bin` deberías ver archivos como `ffmpeg.exe`, `ffprobe.exe`, etc.

#### Paso 3: Agregar FFmpeg al PATH de Windows

##### Método Gráfico (Recomendado):

1. **Abre el menú de inicio** y busca "variables de entorno"
2. Haz clic en **"Editar las variables de entorno del sistema"**
3. En la ventana "Propiedades del sistema", haz clic en **"Variables de entorno..."**
4. En la sección **"Variables del sistema"** (la parte inferior), busca la variable **"Path"** y haz clic en **"Editar..."**
5. Haz clic en **"Nuevo"**
6. Agrega la ruta completa a la carpeta `bin` de FFmpeg:
   ```
   C:\ffmpeg\bin
   ```
   (ajusta la ruta si instalaste FFmpeg en otra ubicación)
7. Haz clic en **"Aceptar"** en todas las ventanas para guardar los cambios

##### Método PowerShell:

```powershell
# Ejecutar como Administrador
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\ffmpeg\bin", "Machine")
```

#### Paso 4: Verificar la instalación

1. **Cierra y vuelve a abrir** PowerShell o Command Prompt
2. Ejecuta:
   ```powershell
   ffmpeg -version
   ```

Deberías ver algo como:
```
ffmpeg version 2024-11-25-git-... Copyright (c) 2000-2024 the FFmpeg developers
built with gcc ...
```

## Verificación Completa

Para asegurarte de que todo funciona correctamente:

1. Abre una **nueva terminal** (es importante que sea nueva para que cargue el PATH actualizado)
2. Ejecuta estos comandos:

```powershell
# Verificar FFmpeg
ffmpeg -version

# Verificar FFprobe (también se instala con FFmpeg)
ffprobe -version
```

## Solución de Problemas

### "ffmpeg no se reconoce como un comando"

**Causa**: El PATH no está configurado correctamente o no has reiniciado la terminal.

**Solución**:
1. Verifica que agregaste la ruta correcta al PATH
2. **Cierra TODAS las ventanas de PowerShell/CMD**
3. Abre una **nueva terminal**
4. Intenta de nuevo

### "El sistema no puede encontrar la ruta especificada"

**Causa**: La ruta que agregaste al PATH no existe o es incorrecta.

**Solución**:
1. Verifica que `C:\ffmpeg\bin` (o la ruta que usaste) realmente existe
2. Verifica que dentro de esa carpeta hay archivos como `ffmpeg.exe`
3. Corrige la ruta en el PATH si es necesario

### La aplicación sigue sin funcionar después de instalar FFmpeg

**Solución**:
1. **Reinicia Visual Studio Code completamente**
2. Si estás ejecutando la app desde un terminal, abre un **nuevo terminal**
3. Verifica que `ffmpeg -version` funciona en ese nuevo terminal
4. Intenta ejecutar la aplicación de nuevo

## Prueba con la Aplicación

Una vez instalado FFmpeg:

1. Cierra cualquier instancia de la aplicación que esté corriendo
2. Cierra y vuelve a abrir VS Code o el terminal
3. Navega al directorio de la aplicación:
   ```powershell
   cd "C:\Users\DarkG\Documents\Visual Studio Code\app-audios-transcripcion"
   ```
4. Inicia la aplicación:
   ```powershell
   python app.py
   ```
5. Intenta transcribir un archivo de audio

## Recursos Adicionales

- Sitio oficial de FFmpeg: https://ffmpeg.org/
- Documentación de FFmpeg: https://ffmpeg.org/documentation.html
- Builds de FFmpeg para Windows: https://www.gyan.dev/ffmpeg/builds/

---

**¿Necesitas ayuda?** Si sigues teniendo problemas, asegúrate de:
1. Haber reiniciado completamente tu terminal/VS Code
2. Haber agregado la ruta correcta al PATH del sistema
3. Poder ejecutar `ffmpeg -version` exitosamente en una nueva terminal
