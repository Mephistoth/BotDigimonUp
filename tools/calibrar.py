import cv2
import numpy as np
import sys

# Cargar la foto completa del juego que guardaste
img = cv2.imread('mapa.png')

if img is None:
    print("[ERROR] No se encontró el archivo 'mapa.png' en la carpeta.")
    sys.exit()

# Convertimos la imagen a formato HSV (el que usa el bot)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

print("====================================================")
print("          CALIBRADOR DE COLORES PARA EL BOT         ")
print("====================================================")
print("1. Se abrirá una ventana con la foto de tu juego.")
print("2. Haz CLIC IZQUIERDO sobre el CAMINO CELESTE.")
print("3. En esta terminal aparecerán los números HSV exactos.")
print("4. Presiona cualquier tecla en la foto para cerrar.")
print("====================================================\n")

def click_evento(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # Obtener el píxel HSV donde hiciste clic
        pixel_hsv = hsv[y, x]
        print(f"¡Color detectado! -> H: {pixel_hsv[0]} | S: {pixel_hsv[1]} | V: {pixel_hsv[2]}")
        print(f"Para tu bot usa estos rangos sugeridos:")
        print(f"BAJO = np.array([{max(0, pixel_hsv[0]-15)}, {max(50, pixel_hsv[1]-40)}, {max(50, pixel_hsv[2]-40)}])")
        print(f"ALTO = np.array([{min(180, pixel_hsv[0]+15)}, {min(255, pixel_hsv[1]+40)}, {min(255, pixel_hsv[2]+40)}])\n")

cv2.imshow('Haz clic en el camino celeste', img)
cv2.setMouseCallback('Haz clic en el camino celeste', click_evento)
cv2.waitKey(0)
cv2.destroyAllWindows()