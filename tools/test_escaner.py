import pyautogui
import cv2
import numpy as np
import time
import sys

print("=== INICIANDO PRUEBA DE CONEXIÓN ===", flush=True)
print("Paso A: Comprobando librerías principales...", end="", flush=True)
time.sleep(1)
print(" [OK]", flush=True)

print("Paso B: Buscando el archivo 'digimon.png' en tu carpeta...", end="", flush=True)
template = cv2.imread('digimon.png', cv2.IMREAD_GRAYSCALE)

if template is None:
    print("\n\n[ERROR]: No se encontró el archivo 'digimon.png'. Checkea el nombre.", flush=True)
    sys.exit()
else:
    print(" [OK]", flush=True)

print("Paso C: Tomando captura de tu monitor en 3 segundos...", flush=True)
print("¡Cambia a BlueStacks a pantalla completa YA!", flush=True)
time.sleep(3)

print("Capturando pantalla ahora mismo...", end="", flush=True)
img_pantalla = pyautogui.screenshot()
img_pantalla = np.array(img_pantalla)
print(" [OK]", flush=True)

print("Procesando imágenes en blanco y negro...", end="", flush=True)
img_pantalla_bgr = cv2.cvtColor(img_pantalla, cv2.COLOR_RGB2BGR)
img_pantalla_gris = cv2.cvtColor(img_pantalla_bgr, cv2.COLOR_BGR2GRAY)
alto_t, ancho_t = template.shape[::-1]
print(" [OK]", flush=True)

print("Buscando coincidencia visual de Imperialdramon...", end="", flush=True)
resultado = cv2.matchTemplate(img_pantalla_gris, template, cv2.TM_CCOEFF_NORMED)
_, max_val, _, max_loc = cv2.minMaxLoc(resultado)
print(" [OK]", flush=True)

print(f"\n[RESULTADO] Porcentaje de coincidencia encontrado: {max_val*100:.1f}%", flush=True)

if max_val >= 0.65:
    digimon_x = max_loc[0] + (ancho_t // 2)
    digimon_y = max_loc[1] + (alto_t // 2)
    print(f"¡ÉXITO! Encontrado en X: {digimon_x}, Y: {digimon_y}", flush=True)
    print("Moviendo mouse al Digimon...", flush=True)
    pyautogui.moveTo(digimon_x, digimon_y, duration=1.0)
else:
    print("ALERTA: Coincidencia muy baja. No se pudo asegurar que sea él.", flush=True)