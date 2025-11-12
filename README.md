# Piedra, Papel o Tijeras por Visión (MediaPipe + OpenCV)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE) ![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

Juego de Piedra-Papel-Tijeras controlado por tu mano usando MediaPipe Hands y OpenCV. Incluye un oponente IA sencillo que aprende de tus jugadas y un registro en CSV de los resultados.

## Requisitos
- Python 3.10+
- Cámara web
- Dependencias: `mediapipe`, `opencv-python`

## Instalación (Windows PowerShell)
```powershell
# Dentro de esta carpeta (rps)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso
```powershell
python rps_cv.py
```
- `SPACE`: inicia una ronda con cuenta atrás de 3s.
- `r`: reinicia el marcador.
- `q` o `ESC`: salir.

La detección clasifica: rock (puño), paper (mano abierta), scissors (índice+medio extendidos). El archivo `rps_log.csv` se crea automáticamente en esta carpeta con el historial de partidas.

## Consejos
- Asegúrate de tener buena iluminación y que la mano esté centrada.
- Si no abre la cámara, verifica permisos del sistema o intenta con otro índice de cámara (edita `cv2.VideoCapture(0)`).

## Licencia
Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo [LICENSE](./LICENSE) para más detalles.
