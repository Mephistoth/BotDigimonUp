# Bot Isométrico v2.5.0 — Digimon UP (Edición Avanzada) 🦖⚡

Bot de automatización reactiva y enrutamiento inteligente basado en **visión artificial de baja latencia** para optimizar el avance en el modo exploración de *Digimon UP* sobre emuladores de PC (BlueStacks).

---

## 🚀 Innovaciones Tecnológicas Clave (v2.5.0)

El núcleo lógico del bot fue reestructurado en esta versión para actuar con un comportamiento estratega y fluido, priorizando el rendimiento del procesador y la eficiencia en la caminata.

*   **🌐 Escaneo Perimetral (Evasión Anticipada):** Algoritmo predictivo que analiza la densidad de carriles a 2 pasos de profundidad. Si el frente está obstruido, el bot calcula cuál desvío ofrece un terreno más abierto y libre, descartando de forma drástica rutas que exijan demoler pirámides si hay suelo celeste libre.
*   **🏎️ Captura en Microsegundos (15ms):** Conexión nativa con la GPU mediante el ecosistema `mss` para capturar e inyectar cuadros directamente en la memoria RAM, eliminando el lag visual tradicional.
*   **📉 Procesamiento Asíncrono (Downscaling 50%):** Reducción dinámica de resolución con interpolación de vecindad más cercana a través de OpenCV, lo que alivia el consumo de CPU en un 75% sin perder precisión matemática.
*   **🖱️ Inyección Virtual de Clics (0ms):** Control por hardware en segundo plano utilizando llamadas nativas a la API de Windows a través de `ctypes`. El bot opera de forma invisible dentro del emulador sin robar ni mover el puntero físico del mouse del usuario.
*   **🏆 Enrutamiento Manhattan para Premios:** Al detectar tickets naranjas, el bot activa un árbol de decisión geométrico avanzado (Rodeos diagonales en "L" de 360°), calculando desvíos eficientes antes de tomar la decisión de romper.

---

## 📁 Arquitectura del Proyecto

El directorio mantiene una distribución modular y estandarizada para facilitar la futura portabilidad y empaquetado del software:

```text
BotDigimonUp/
├── tools/                  # Herramientas de diagnóstico e ingeniería inversa
│   ├── calibrar.py         # Script para capturar rangos de color HSV en tiempo real
│   ├── test_escaner.py     # Monitor de cuadros y detección aislada de objetos
│   └── mapa.png            # Captura base calibrada del mapa de juego
├── .gitignore              # Filtro de exclusión para evitar subir capturas temporales
├── README.md               # Documentación técnica del proyecto
├── main.py                 # Orquestador principal y bucle eléctrico del bot
├── requirements.txt        # Índice de dependencias de Python estandarizado
└── *.png                   # Plantillas visuales de referencia (Digimon, Pirámides, Tickets)
```

---

## 🛠️ Requisitos e Instalación

Para desplegar y ejecutar el entorno de desarrollo local, sigue estos pasos:

1. Clonar este repositorio o descargar la estructura de carpetas en tu máquina.
2. Asegurar una instalación limpia de Python 3 y abrir la terminal en la raíz del proyecto.
3. Instalar las dependencias de visión artificial ejecutando:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🎮 Controles de Operación

La ejecución se gestiona mediante eventos de escucha de teclado globales:

*   **Presionar Tecla [G]:** Activa el motor de escaneo, sincroniza el refresco de pantalla y toma el control automático del juego de forma virtual.
*   **Presionar Tecla [Q]:** Apagado de emergencia inmediato. Detiene los hilos de captura y libera los recursos del sistema de forma segura.

---

## 📢 Sobre el Proyecto
Desarrollado con fines de optimización y simulación de enrutamiento isométrico utilizando visión artificial directa sobre sistemas Windows.
