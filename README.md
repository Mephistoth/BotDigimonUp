# Bot Isométrico v2.4.4 - Digimon UP (Alta Velocidad) 🦖⚡

Bot de automatización reactivo y de alto rendimiento basado en **visión artificial en tiempo real** para optimizar el avance en el modo exploración de *Digimon UP* sobre el emulador BlueStacks.

## 🚀 Características Principales (v2.4.4)
- **Captura Ultra Rápida (15ms):** Implementación nativa de `mss` para capturar fotogramas directamente de la GPU.
- **Procesamiento Acelerado (Downscaling):** Reducción de escala al 50% con OpenCV, disminuyendo en un 75% el uso de CPU.
- **Clics Virtuales (PostMessage):** Control mediante la API nativa de Windows (`ctypes`), enviando clics en segundo plano sin robar el mouse físico del usuario.
- **Navegación Inteligente Anti-Bucles:** Algoritmo secuencial con memoria a corto plazo para evitar atascos y vaivenes de izquierda a derecha.
- **Filtro de Recompensas (Ruta Limpia):** Ignorado inteligente de tickets si el acceso requiere destruir obstáculos de forma ineficiente.

## 🛠️ Requisitos de Instalación
El proyecto ya cuenta con una estructura limpia estructurando utilidades en la carpeta `/tools` y un archivo de dependencias estandarizado.

1. Clonar el repositorio o descargar el código.
2. Instalar las librerías necesarias ejecutando en la terminal:
   ```bash
   pip install -r requirements.txt
   ```

## 🎮 Controles
- **Tecla G:** Iniciar monitoreo y tomar el control del juego.
- **Tecla Q:** Apagado de emergencia y liberación de procesos de forma segura.
