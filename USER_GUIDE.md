# 📖 BUHO VISION - GUÍA DE USUARIO
## Sistema Automatizado de Generación de Gráficos Deportivos

---

## 🎯 ¿Qué es Buho Vision?
Buho Vision es un sistema automatizado que genera gráficos profesionales de marcadores deportivos para tus videos. Con solo un archivo de texto con los resultados de los partidos, el sistema genera automáticamente gráficos PNG de alta calidad con los escudos de los equipos y el marcador.

### ✨ Características Principales
- ⚡ **Rápido**: Genera 5 gráficos en ~10 segundos
- 💰 **Gratuito**: No requiere Photoshop ni licencias costosas
- 🎨 **Profesional**: Diseño limpio con transparencia PNG
- 🔄 **Automático**: Procesa múltiples partidos de una vez
- 🛡️ **Inteligente**: Detecta logos faltantes y crea placeholders

---

## 🚀 INICIO RÁPIDO

### Paso 1: Preparar los Datos del Partido
1. Abre el archivo: `Automation Process\1_Data_Input\game_data.txt`
2. Escribe los resultados en este formato:
   ```
   EQUIPO_LOCAL vs EQUIPO_VISITANTE GOLES_LOCAL-GOLES_VISITANTE Liga Kings
   ```

**Ejemplo:**
```
LA NOCHE vs LA CREMA 4-2 Liga Kings
ATLETICO MINEIRO vs LA 4 1-6 Liga Kings
JUVENTUS vs MILAN 2-1 Liga Kings
```

### Paso 2: Ejecutar el Generador
1. Abre una terminal/símbolo del sistema
2. Navega a la carpeta del proyecto:
   ```
   cd C:\Users\mgarr\Documents\claude-projects\AI-Tutoring\buho_vision
   ```
3. Ejecuta el comando:
   ```
   python "Automation Process\2_Graphics_Generation\generate_graphics.py"
   ```

### Paso 3: Encontrar los Gráficos
Los gráficos se guardan automáticamente en:
```
Output\Liga Kings\[EQUIPO_LOCAL] VS [EQUIPO_VISITANTE] Liga Kings.png
```

---

## 📁 ESTRUCTURA DE CARPETAS

```
buho_vision/
│
├── 📂 Automation Process/
│   ├── 📂 1_Data_Input/
│   │   ├── game_data.txt         ← AQUÍ ESCRIBES LOS PARTIDOS
│   │   └── data_parser.py        (procesador de datos)
│   │
│   └── 📂 2_Graphics_Generation/
│       ├── generate_graphics.py   ← EJECUTAR ESTE ARCHIVO
│       ├── scoreboard_template.html
│       └── config.json           (configuración)
│
└── 📂 Output/
    └── 📂 Liga Kings/             ← AQUÍ SE GUARDAN LOS GRÁFICOS
        ├── LA NOCHE VS LA CREMA Liga Kings.png
        ├── ATLETICO MINEIRO VS LA 4 Liga Kings.png
        └── missing_logos.txt      (reporte de logos faltantes)
```

---

## 🎨 FORMATO DE DATOS

### Formato de Entrada (game_data.txt)
```
EQUIPO_LOCAL vs EQUIPO_VISITANTE GOLES_LOCAL-GOLES_VISITANTE LIGA
```

### Reglas Importantes:
- ✅ Usa "vs" en minúsculas entre los equipos
- ✅ Separa los goles con guión (4-2)
- ✅ El nombre de la liga al final (Liga Kings)
- ✅ Un partido por línea
- ✅ Los nombres deben coincidir con los archivos de logos

### Ejemplos Correctos:
```
✅ LA NOCHE vs LA CREMA 4-2 Liga Kings
✅ REAL BARRIO vs DEPORTIVO LB 0-3 Liga Kings
✅ BAYERN vs ARSENAL 2-2 Liga Kings
```

### Ejemplos Incorrectos:
```
❌ LA NOCHE VS LA CREMA 4-2 Liga Kings    (VS en mayúsculas)
❌ LA NOCHE - LA CREMA 4-2 Liga Kings      (guión en vez de vs)
❌ LA NOCHE vs LA CREMA Liga Kings         (falta el marcador)
```

---

## 🖼️ LOGOS DE EQUIPOS

### Ubicación de Logos
Los logos deben estar en:
```
C:\Users\mgarr\Desktop\buho\1- Liga Kings-*\1- Liga Kings\1 - Escudos\
```

### Formato de Logos
- **Formato**: PNG con transparencia
- **Nombre**: Debe coincidir exactamente con el nombre en game_data.txt
- **Ejemplos**:
  - `LA NOCHE.png`
  - `LA CREMA.png`
  - `ATLETICO MINEIRO.png`

### ⚠️ Logos Faltantes
Si un logo no existe:
1. El sistema genera un placeholder automático (círculo azul con iniciales)
2. Se registra en `Output\Liga Kings\missing_logos.txt`
3. El gráfico se genera igualmente (no se detiene el proceso)

---

## 🔧 CONFIGURACIÓN AVANZADA

### Archivo: `config.json`
```json
{
  "leagues": {
    "Liga Kings": {
      "logo_folder": "C:\\Users\\mgarr\\Desktop\\buho\\...\\1 - Escudos",
      "league_logo": "C:\\Users\\mgarr\\Desktop\\buho\\...\\LIGA_KINGS.png",
      "output_folder": "Liga Kings",
      "colors": {
        "home": "#1E3A8A",
        "away": "#DC2626",
        "background": "#F3F4F6"
      }
    }
  }
}
```

### Personalizar Colores y Estilos
Edita `scoreboard_template.html` para cambiar:
- Colores del marcador
- Tamaño de fuentes
- Diseño del tablero
- Posición de elementos

---

## ✅ VERIFICACIÓN DE RESULTADOS

### Gráfico Exitoso
- ✅ Archivo PNG con transparencia
- ✅ Logos de ambos equipos visibles
- ✅ Marcador correcto
- ✅ Logo de la liga en el centro
- ✅ Nombre del archivo: `[LOCAL] VS [VISITANTE] Liga Kings.png`

### Revisar Calidad
1. Abre los PNG en cualquier visor de imágenes
2. Verifica transparencia (fondo a cuadros)
3. Confirma que los logos sean correctos
4. Revisa que el marcador sea legible

---

## 🚨 SOLUCIÓN DE PROBLEMAS

### Error: "No se encuentra el logo"
**Solución:**
1. Verifica que el nombre del equipo sea exacto
2. Revisa `missing_logos.txt` para ver qué logos faltan
3. Añade los logos faltantes a la carpeta de Escudos

### Error: "playwright not installed"
**Solución:**
```bash
pip install playwright
python -m playwright install chromium
```

### Error: "No se generan gráficos"
**Verificar:**
1. El archivo game_data.txt tiene el formato correcto
2. Python está instalado (versión 3.7+)
3. La terminal está en la carpeta correcta
4. Los permisos de escritura en la carpeta Output

### Los gráficos se ven mal
**Revisar:**
1. Los logos son PNG con transparencia
2. La resolución de los logos es adecuada (mínimo 200x200px)
3. El navegador Chromium está actualizado

---

## 💡 CONSEJOS Y TRUCOS

### Procesamiento por Lotes
Puedes procesar múltiples partidos a la vez:
```
LA NOCHE vs LA CREMA 4-2 Liga Kings
ATLETICO MINEIRO vs LA 4 1-6 Liga Kings
JUVENTUS vs MILAN 2-1 Liga Kings
REAL BARRIO vs DEPORTIVO LB 0-3 Liga Kings
BAYERN vs ARSENAL 2-2 Liga Kings
```

### Organización de Archivos
- Mantén una copia de seguridad de game_data.txt
- Crea carpetas por fecha: `Output\Liga Kings\2024-01-15\`
- Guarda los logos en alta resolución

### Automatización Adicional
Puedes crear un archivo .bat para ejecutar con doble clic:
```batch
@echo off
cd C:\Users\mgarr\Documents\claude-projects\AI-Tutoring\buho_vision
python "Automation Process\2_Graphics_Generation\generate_graphics.py"
pause
```

---

## 📊 RENDIMIENTO ESPERADO

| Cantidad | Tiempo Estimado | Calidad |
|----------|----------------|---------|
| 1 gráfico | ~2 segundos | Alta |
| 5 gráficos | ~10 segundos | Alta |
| 20 gráficos | ~40 segundos | Alta |
| 50 gráficos | ~100 segundos | Alta |

---

## 🆘 SOPORTE

### Archivos de Log
- `missing_logos.txt` - Lista de logos no encontrados
- Mensajes en la terminal durante la ejecución

### Contacto
Para problemas técnicos, revisa:
1. Este manual
2. El archivo TODO.md para características pendientes
3. Los mensajes de error en la terminal

---

## 🎉 ¡FELICIDADES!
Ya estás listo para generar gráficos profesionales de manera automática.

### Resumen del Proceso:
1. 📝 Escribe los partidos en `game_data.txt`
2. 🚀 Ejecuta `generate_graphics.py`
3. 🖼️ Encuentra los gráficos en `Output\Liga Kings\`
4. 🎬 Usa los PNG en tus videos

---

*Última actualización: Sistema funcionando con Liga Kings*
*Versión: 1.0 - HTML/CSS Solution*