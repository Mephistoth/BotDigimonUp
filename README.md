# Bot Isométrico v2.7.0 — Digimon UP (Distribución Abierta Universal) 🦖⚡

Bot de automatización reactiva y enrutamiento inteligente basado en **visión artificial de baja latencia** para optimizar el avance en el modo exploración de *Digimon UP* sobre emuladores de PC (BlueStacks) [1.6].

---

## 💾 Descarga Directa (Paquete Ejecutable)

Para usuarios finales, se encuentra disponible la versión compilada autocontenida que no requiere la instalación de Python ni de dependencias externas [1.6]:

👉 **[Descargar DigiWorld Controller v2.7.0 (.EXE)](https://github.com/Mephistoth/BotDigimonUp/releases/tag/v2.7.0)** [1.6]

*Nota de Uso: Esta versión viene "limpia visualmente" para garantizar compatibilidad universal con cualquier hardware (Intel/AMD/NVIDIA). Al presionar INICIAR BOT por primera vez, el programa detectará si faltan imágenes y abrirá un cuadro de alerta instructivo guiándote para colocar tus propias capturas de pantalla en la misma carpeta [1.6].*

---

## 🚀 Innovaciones Tecnológicas Clave (v2.7.0)

El núcleo lógico del bot fue reestructurado por completo en esta versión para ofrecer una arquitectura modular abierta, un entorno gráfico interactivo y compatibilidad absoluta multi-tarjeta de video [1.6].

*   **🎯 Localizador de Ventana Asíncrono (`pygetwindow`):** Eliminación de coordenadas físicas rígidas en el monitor. El bot detecta de forma autónoma la posición de la ventana "BlueStacks App Player", adaptando la ROI y la inyección virtual de clics en caliente en cualquier PC [1.6].
*   **📋 Validador Inteligente de Entorno (Instrucciones de QA):** Ventana de alerta automatizada que se activa si faltan plantillas visuales externas en la carpeta, detallando la nomenclatura exacta de los archivos `.png` requeridos para asistir al usuario final [1.6].
*   **🔥 Filtros HSV Elásticos (Multi-GPU):** Espectro de color expandido para absorber y asimilar las variaciones de saturación, brillo y suavizado de bordes (*Anti-Aliasing*) provocados por el renderizado de tarjetas gráficas AMD Radeon, Intel y NVIDIA [1.6].
*   **🎨 Interfaz Gráfica Visual (Modo Oscuro con Hilos):** Ventana flotante en Modo Oscuro Premium. Orquestación mediante programación concurrente (*Multi-Threading*) para ejecutar el bucle matemático de OpenCV en segundo plano sin congelar los recursos de Windows [1.6].
*   **🔨 Sistema Rompe-Bucles Automático:** Algoritmo predictivo de contingencia. Si se detecta un vaivén continuo de rebote vertical (arriba/abajo) por más de 3 ciclos, interrumpe el bucle forzando un ataque de emergencia para demoler la pirámide y abrir el mapa [1.6].
*   **🏎️ Captura en Microsegundos (45ms):** Conexión nativa con la GPU mediante el ecosistema `mss` para capturar e inyectar cuadros directamente en la memoria RAM, optimizando el ritmo a una velocidad fluida y 100% humana [1.6].

---

## 📁 Arquitectura del Proyecto

El directorio mantiene una distribución modular y estandarizada para facilitar la flexibilidad y el empaquetado independiente del software [1.6]:

```text
BotDigimonUp/
├── tools/                  # Herramientas de diagnóstico e ingeniería inversa
│   ├── calibrar.py         # Script para capturar rangos de color HSV en tiempo real
│   ├── test_escaner.py     # Monitor de cuadros y detección aislada de objetos
│   └── mapa.png            # Captura base calibrada del mapa de juego
├── .gitignore              # Filtro de exclusión para evitar subir binarios y temporales
├── README.md               # Documentación técnica del proyecto (v2.7.0)
├── main.py                 # Orquestador principal e Interfaz Gráfica del bot
├── requirements.txt        # Índice de dependencias de Python estandarizado
└── *.png                   # Plantilla estética del banner interno de la interfaz (banner.png)
```

*Nota: Las plantillas de coincidencia (`digimon.png`, `digimon_espalda.png`, `piramide.png`, `ticket.png` y `cofre.png`) se generan localmente en la carpeta del ejecutable para calibrar el reconocimiento de forma óptima en cada computadora [1.6].*

---

## 🛠️ Requisitos e Instalación (Entorno de Desarrollo)

Para desplegar y ejecutar el entorno de desarrollo local basándote en el código fuente, sigue estos pasos [1.6]:

1. Clonar este repositorio o descargar la estructura de carpetas en tu máquina [1.6].
2. Asegurar una instalación limpia de Python 3 y abrir la terminal en la raíz del proyecto [1.6].
3. Instalar las dependencias de visión artificial y control dinámico ejecutando [1.6]:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🎮 Controles de Operación

La ejecución se gestiona de forma interactiva y virtual mediante los componentes nativos de la aplicación [1.6]:

*   **Botón INICIAR BOT:** Activa el motor de escaneo asíncrono, localiza dinámicamente el emulador e inicia la exploración automática del mapa [1.6].
*   **Botón DETENER:** Congela de inmediato las acciones y libera de forma segura las llamadas por hardware virtuales [1.6].
*   **Presionar Tecla [Q]:** Apagado y cierre de emergencia inmediato del script del sistema [1.6].

---

## 📢 Sobre el Proyecto
Desarrollado con fines de optimización y simulación de enrutamiento isométrico utilizando visión artificial directa sobre sistemas Windows [1.6].
