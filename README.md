# ITAD Pro v2.0 — Guía de Compilación a .EXE

## Estructura de archivos necesaria

```
tu_carpeta/
├── itad_pro.py          ← Aplicativo principal
├── itad_pro.spec        ← Configuración PyInstaller
├── build.bat            ← Script de compilación (este archivo)
├── assets/
│   └── icon.ico         ← Ícono (se genera automáticamente si no existe)
└── dist/
    └── ITAD_Pro.exe     ← Resultado final (se crea al compilar)
```

---

## Requisitos previos

- **Windows 10/11** (64-bit)
- **Python 3.10 o superior** → https://www.python.org/downloads/
  - ✅ Marcar "Add Python to PATH" durante la instalación
- **Conexión a Internet** (para descargar PyInstaller en el primer uso)

---

## Compilación en 1 paso

1. Coloca todos los archivos en la misma carpeta
2. Haz clic derecho en `build.bat` → **Ejecutar como administrador**
3. Espera 1–3 minutos
4. El `.exe` estará en `dist\ITAD_Pro.exe`

---

## Solución de problemas comunes

### ❌ `ModuleNotFoundError: customtkinter`
```
pip install customtkinter
```

### ❌ El .exe se abre y se cierra inmediatamente
Compila temporalmente con `console=True` en el `.spec` para ver el error:
```
# En itad_pro.spec, línea console=False → cámbiala a True
console=True,
```

### ❌ Falta el archivo `darkdetect`
```
pip install darkdetect
```

### ❌ `FileNotFoundError: icon.ico`
El script `build.bat` genera el ícono automáticamente. Si falla, crea
manualmente una carpeta `assets\` y coloca cualquier archivo `icon.ico`.

---

## Reducir falsos positivos de Windows Defender / antivirus

El archivo `.exe` generado con PyInstaller puede ser detectado erróneamente
por algunos antivirus. Esto es un **falso positivo** muy común con ejecutables
Python empaquetados. Estrategias para reducirlo:

### 1. Excluir la carpeta `dist\` en Windows Defender (recomendado para desarrollo)
```
Seguridad de Windows → Protección contra virus → 
Configuración de protección → Exclusiones → Agregar exclusión → Carpeta
→ Seleccionar dist\
```

### 2. Firma de código (elimina alertas de SmartScreen permanentemente)
Con un certificado de firma de código (EV Code Signing Certificate):
```bat
signtool sign ^
  /tr http://timestamp.digicert.com ^
  /td sha256 /fd sha256 ^
  /n "Nombre de tu empresa" ^
  dist\ITAD_Pro.exe
```
Proveedores: DigiCert, Sectigo, SSL.com (~$200–500/año)

### 3. Subir a VirusTotal antes de distribuir
https://www.virustotal.com/gui/home/upload

### 4. Alternativa: compilar en modo directorio (menos sospechoso para AV)
En `itad_pro.spec`, cambia la sección `EXE` para no usar `onefile`:
```python
# Añade esta sección después de EXE:
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ITAD_Pro',
)
```
Y compila: `pyinstaller itad_pro.spec`
El resultado será una **carpeta** `dist\ITAD_Pro\` con el `.exe` dentro.
Algunos AV son menos agresivos con este formato.

### 5. NO usar UPX si el AV es muy agresivo
En `itad_pro.spec`, cambia:
```python
upx=True,   →   upx=False,
```
UPX comprime el ejecutable de forma similar a como lo hace el malware,
lo que puede disparar heurísticas.

---

## Notas técnicas del .spec

| Opción | Valor | Razón |
|---|---|---|
| `console=False` | Sin ventana negra | Aplicativo GUI puro |
| `uac_admin=True` | Solicita UAC | Necesario para acceso a discos físicos |
| `onefile` | Sí (default) | Un solo .exe portable |
| `upx=True` | Compresión | Reduce ~30% el tamaño |
| `version_info.txt` | Metadatos | Aparece en Propiedades del .exe |
| `excludes=[...]` | Módulos excluidos | Reduce tamaño y superficie de detección |

---

## Tamaño esperado del .exe

| Configuración | Tamaño aprox. |
|---|---|
| Con UPX | 25–35 MB |
| Sin UPX | 40–55 MB |
| Modo carpeta (COLLECT) | 60–80 MB (carpeta completa) |

---

## Distribución corporativa

Para despliegue en entornos corporativos con políticas de grupo (GPO):

1. Firma el `.exe` con certificado EV
2. Agrega el hash SHA-256 a la lista blanca del antivirus corporativo:
   ```
   certutil -hashfile dist\ITAD_Pro.exe SHA256
   ```
3. Despliega vía SCCM/Intune como aplicación Win32
4. El ejecutable ya solicita elevación UAC por su manifiesto embebido

---

*ITAD Pro v2.0 — Uso exclusivo corporativo / IT Asset Disposal*