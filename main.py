"""
Bot Isométrico v2.7.0 — Digimon UP (Edición de Distribución Abierta)
Desarrollado por Felipe (Mephistoth).
 
Teclas: Q = apagar de emergencia
Requisitos: pip install pyautogui opencv-python numpy keyboard mss pygetwindow
Plantillas externas obligatorias en la misma carpeta: digimon.png, digimon_espalda.png, piramide.png, cofre.png, ticket.png
"""
import time
import random
import logging
import sys
import os
import threading
import tkinter as tk      
from tkinter import messagebox 
import cv2
import ctypes
import numpy as np 
import pyautogui
import keyboard
import mss
import pygetwindow as gw
 
pyautogui.PAUSE = 0                # Elimina el retraso involuntario de pyautogui tras cada clic
 
# ============================== CONFIGURACIÓN UNIVERSAL v2.7.0 ==============================
# 🎯 RADAR DINÁMICO DE HARDWARE: Localiza BlueStacks en cualquier posición de la pantalla de tus amigos
def obtener_roi_dinamica():
    try:
        ventanas = gw.getWindowsWithTitle("BlueStacks App Player")
        if ventanas:
            win = ventanas[0]
            # Retorna: left, top, width, height de la ventana real del usuario en ese milisegundo
            return win.left, win.top, win.width, win.height
    except Exception:
        pass
    return 430, 150, 1020, 680  # Respaldo nativo clásico por seguridad
 
ROI_X, ROI_Y, ROI_W, ROI_H = obtener_roi_dinamica()
 
PASO_X, PASO_Y = 110, 70           # Tamaño de una casilla en pantalla
 
# 🔥 TOLERANCIA DE HARDWARE: Ajustado para absorber el suavizado de bordes (Anti-Aliasing) de AMD
UMBRAL_DIGIMON = 0.38              # Capta a Imperialdramon aunque la GPU AMD difumine la silueta
UMBRAL_PIRAMIDE = 0.65             # Mayor estabilidad al detectar cristales morados
UMBRAL_COFRE = 0.60                # Reclamo asegurado en barras inferiores con lag
 
# Ticket naranja (Filtros HSV elásticos ampliados)
TICKET_BAJO = np.array([3, 100, 130])    # Rango ampliado para captar variaciones de naranja
TICKET_ALTO = np.array([28, 255, 255])  
TICKET_AREA_MIN = 30                     # px² mínimos adaptados a distorsiones visuales
EXCLUIR_X, EXCLUIR_Y = 28, 22
 
# Camino celeste (Filtro elástico multi-tarjeta de video)
CELESTE_BAJO = np.array([80, 120, 130])  # 🔥 Bajamos la saturación de 140 a 120 para tarjetas AMD Radeon
CELESTE_ALTO = np.array([122, 255, 255])
CASILLA_MIN_RATIO = 0.12                 # 🔥 Bajado de 0.15 a 0.12: El bot avanzará aunque la GPU pinte poco celeste
 
# --- 🐢 Configuración de Velocidad y Tolerancia al Refresco Visual ---
POLL = 0.045                      
ESPERA_MAX = 2.5                   # Aumentado de 2.2 a 2.5: Más margen para procesadores lentos o a 30 FPS
CAMBIO_MIN = 1.0                   # Valida el movimiento aunque cambien muy pocos píxeles
CAMBIO_ESTABLE = 0.8              
ESTABLE_MAX = 0.6                  
GIRO_ESPERA = 0.12                
ATAQUE_ESPERA = 0.18               
INTENTOS_ATASCO = 3               
DEBUG = True                       # Genera debug_ultimo.png para auditorías gráficas locales
# ============================================================================================
 
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("bot")
 
corriendo = False
ULTIMA_DIRECCION_ELEGIDA = None   
CONTADOR_REBOTES = 0              
hilo_bot = None
 
 
def apagar():
    global corriendo
    corriendo = False
 
 
# ------------------------------- Captura Ultra Rápida ----------------------------------
def capturar():
    """Captura la pantalla basándose en las coordenadas dinámicas actuales de BlueStacks."""
    global ROI_X, ROI_Y, ROI_W, ROI_H
    # Recalculamos la posición por si el usuario movió el emulador de lugar en medio del juego
    ROI_X, ROI_Y, ROI_W, ROI_H = obtener_roi_dinamica()
    
    with mss.mss() as sct:
        monitor = {"left": ROI_X, "top": ROI_Y, "width": ROI_W, "height": ROI_H}
        crudo = sct.grab(monitor)
        bgr = np.array(crudo)[:, :, :3]  
        
    bgr_chico = cv2.resize(bgr, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST)
    gris_chico = cv2.cvtColor(bgr_chico, cv2.COLOR_BGR2GRAY)
    hsv_chico = cv2.cvtColor(bgr_chico, cv2.COLOR_BGR2HSV)
    
    return bgr, gris_chico, hsv_chico
 
 
# ------------------------------ Detección Acelerada ---------------------------------
def nms_puntos(candidatos, dist_min):
    elegidos = []
    for score, x, y in sorted(candidatos, reverse=True):
        if all(abs(x - ex) >= dist_min or abs(y - ey) >= dist_min for _, ex, ey in elegidos):
            elegidos.append((score, x, y))
    return [(x, y) for _, x, y in elegidos]
 
 
def detectar_digimon(gris, plantilla_frente, plantilla_espalda):
    pf_chica = cv2.resize(plantilla_frente, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST)
    alto_f, ancho_f = pf_chica.shape[:2]
    res_f = cv2.matchTemplate(gris, pf_chica, cv2.TM_CCOEFF_NORMED)
    _, val_f, _, loc_f = cv2.minMaxLoc(res_f)
    
    if val_f >= UMBRAL_DIGIMON:
        return (loc_f[0] + ancho_f // 2) * 2, (loc_f[1] + alto_f // 2) * 2
 
    if plantilla_espalda is not None:
        pe_chica = cv2.resize(plantilla_espalda, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST)
        alto_e, ancho_e = pe_chica.shape[:2]
        res_e = cv2.matchTemplate(gris, pe_chica, cv2.TM_CCOEFF_NORMED)
        _, val_e, _, loc_e = cv2.minMaxLoc(res_e)
        
        if val_e >= UMBRAL_DIGIMON:
            return (loc_e[0] + ancho_e // 2) * 2, (loc_e[1] + alto_e // 2) * 2
            
    return None
 
 
def detectar_piramides(gris, plantilla):
    if plantilla is None:
        return []
    p_chica = cv2.resize(plantilla, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST)
    alto, ancho = p_chica.shape[:2]
    res = cv2.matchTemplate(gris, p_chica, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(res >= UMBRAL_PIRAMIDE)
    cands = [(float(res[y, x]), int(x + ancho // 2), int(y + alto // 2)) for x, y in zip(xs, ys)]
    
    puntos_chicos = nms_puntos(cands, min(ancho, alto) // 2)
    return [(px * 2, py * 2) for px, py in puntos_chicos]
 
 
def detectar_tickets(hsv, dig_real):
    dig_chico = (dig_real[0] // 2, dig_real[1] // 2)
    
    mascara = cv2.inRange(hsv, TICKET_BAJO, TICKET_ALTO)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    tickets = []
    
    for c in contornos:
        if cv2.contourArea(c) < TICKET_AREA_MIN:
            continue
        x, y, w, h = cv2.boundingRect(c)
        cx, cy = x + w // 2, y + h // 2
        
        if abs(cx - dig_chico[0]) < EXCLUIR_X and abs(cy - dig_chico[1]) < EXCLUIR_Y:
            continue
        if cx < dig_chico[0] - 15:
            continue
            
        tickets.append((cx * 2, cy * 2))
        
    tickets.sort(key=lambda t: abs(t[0] - dig_real[0]) + abs(t[1] - dig_real[1]))
    return tickets
 
 
def hay_piramide(piramides, x, y):
    return any(abs(x - px) < 45 and abs(y - py) < 45 for px, py in piramides)
 
 
def casilla_libre(camino_chico, x_real, y_real):
    cx, cy = x_real // 2, y_real // 2
    if not (0 <= cx < (camino_chico.shape[1]) and 0 <= cy < (camino_chico.shape[0])):
        return False
    
    parche = camino_chico[max(0, cy - 8):cy + 8, max(0, cx - 8):cx + 8]
    return parche.size > 0 and (np.count_nonzero(parche) / parche.size) >= CASILLA_MIN_RATIO
 
 
def detectar_cofres_listos(gris_chico, plantilla_cofre):
    if plantilla_cofre is None:
        return []
    c_chica = cv2.resize(plantilla_cofre, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST)
    alto, ancho = c_chica.shape[:2]
    
    y_limite_chico = max(0, int((gris_chico.shape[0] - 120) // 2))
    barra_gris = gris_chico[y_limite_chico:, :]
    
    res = cv2.matchTemplate(barra_gris, c_chica, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    
    if max_val >= UMBRAL_COFRE:
        cx_chico = max_loc[0] + ancho // 2
        cy_chico = y_limite_chico + max_loc[1] + alto // 2
        return [(cx_chico * 2, cy_chico * 2)]
        
    return []
 
 
# -------------------------------- Acciones --------------------------------
def clic(x, y):
    """
    Envía un clic físico dinámico adaptado a la posición de la ventana.
    v2.8.0: Reducción leve de la velocidad introduciendo una pausa entre pulsaciones.
    """
    pantalla_x = ROI_X + x + random.randint(-2, 2)
    pantalla_y = ROI_Y + y + random.randint(-2, 2)
    
    # Movemos el cursor a la coordenada de forma precisa
    ctypes.windll.user32.SetCursorPos(pantalla_x, pantalla_y)
    
    # Presionamos el botón del mouse (Click Down)
    ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)
    
    # ⏱️ RITMO HUMANO SUAVIZADO: Pausa de milisegundos simulando la pulsación real
    time.sleep(random.uniform(0.04, 0.075))
    
    # Soltamos el botón del mouse (Click Up)
    ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)
 
 
def atacar():
    """Calcula y ejecuta el clic en el botón de ataque de forma proporcional al emulador."""
    click_x = ROI_X + int(ROI_W * (615 / 1020))
    click_y = ROI_Y + int(ROI_H * (890 / 680))
    pyautogui.click(click_x, click_y)
    time.sleep(ATAQUE_ESPERA)
 
 
def esperar_reaccion(gris_antes_chico):
    previo = cv2.resize(gris_antes_chico, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST)
    referencia = previo
    t0 = time.time()
    t_cambio = None
    
    while corriendo:
        ahora = time.time() - t0
        if t_cambio is None and ahora > ESPERA_MAX:
            break
        if t_cambio is not None and ahora - t_cambio > ESTABLE_MAX:
            break
 
        time.sleep(POLL)
        _, gris_actual_chico, _ = capturar()
        chico = cv2.resize(gris_actual_chico, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST)
        if t_cambio is None:
            if cv2.absdiff(chico, referencia).mean() > CAMBIO_MIN:
                t_cambio = time.time() - t0
        elif cv2.absdiff(chico, previo).mean() < CAMBIO_ESTABLE:
            break
        previo = chico
    return t_cambio is not None
 
 
def paso_hacia(dig, objetivo):
    tx = (objetivo[0] - dig[0]) / PASO_X
    ty = (objetivo[1] - dig[1]) / PASO_Y
    if abs(tx) >= abs(ty):
        return (dig[0] + int(np.sign(tx)) * PASO_X, dig[1])
    return (dig[0], dig[1] + int(np.sign(ty)) * PASO_Y)
 
 
def paso_esquivando(dig, objetivo, bloqueado, piramides, camino_chico):
    direcciones = [(PASO_X, 0), (0, -PASO_Y), (0, PASO_Y)]
    libres = []
    for dx, dy in direcciones:
        v1 = (dig[0] + dx, dig[1] + dy)
        if v1 == bloqueado:
            continue
        if hay_piramide(piramides, *v1) or not casilla_libre(camino_chico, *v1):
            continue
        carril_completamente_limpio = True
        for ddx, ddy in direcciones:
            if (dx + ddx == 0) and (dy + ddy == 0):
                continue
            v2 = (v1[0] + ddx, v1[1] + ddy)
            if hay_piramide(piramides, *v2):
                carril_completamente_limpio = False
                break
        if carril_completamente_limpio:
            d = abs(v1[0] - objetivo[0]) / PASO_X + abs(v1[1] - objetivo[1]) / PASO_Y
            libres.append((d, v1))
    if libres:
        return min(libres)[1]
    return None
 
 
def evaluar_densidad_ruta(pos_inicial, direccion_nombre, camino_chico, piramides):
    puntos_libre = 0
    tiene_obstaculo = False
    x, y = pos_inicial[0], pos_inicial[1]
    if direccion_nombre == "abajo":
        paso_inmediato = (x, y + PASO_Y)
        if hay_piramide(piramides, *paso_inmediato) or not casilla_libre(camino_chico, *paso_inmediato):
            return 0
        pasos_futuros = [
            paso_inmediato,
            (x, y + (PASO_Y * 2)),
            (x + PASO_X, y + PASO_Y),
            (x, y + (PASO_Y * 3)),
            (x + PASO_X, y + (PASO_Y * 2)),
            (x + (PASO_X * 2), y + PASO_Y),
        ]
    elif direccion_nombre == "arriba":
        paso_inmediato = (x, y - PASO_Y)
        if hay_piramide(piramides, *paso_inmediato) or not casilla_libre(camino_chico, *paso_inmediato):
            return 0
        pasos_futuros = [
            paso_inmediato,
            (x, y - (PASO_Y * 2)),
            (x + PASO_X, y - PASO_Y),
            (x, y - (PASO_Y * 3)),
            (x + PASO_X, y - (PASO_Y * 2)),
            (x + (PASO_X * 2), y - PASO_Y),
        ]
    else:
        return 0
    for p_futuro in pasos_futuros:
        if hay_piramide(piramides, *p_futuro):
            tiene_obstaculo = True
        elif casilla_libre(camino_chico, *p_futuro):
            puntos_libre += 1
    if tiene_obstaculo:
        puntos_libre = max(1, puntos_libre - 3)
    return puntos_libre
 
 
def guardar_debug(bgr, dig, piramides, tickets, destino):
    img = bgr.copy()
    cv2.circle(img, dig, 12, (0, 255, 0), 2)
    for px, py in piramides:
        cv2.rectangle(img, (px - 40, py - 40), (px + 40, py + 40), (255, 0, 255), 2)
    for tx, ty in tickets:
        cv2.circle(img, (tx, ty), 18, (0, 165, 255), 2)
    if destino:
        cv2.drawMarker(img, destino, (0, 0, 255), cv2.MARKER_CROSS, 25, 2)
    cv2.imwrite("debug_ultimo.png", img)
 
 
# -------------------------------- Decisión -------------------------------
def decidir(dig, piramides, tickets, camino_chico, ultima_vert, cofres):
    global ULTIMA_DIRECCION_ELEGIDA, CONTADOR_REBOTES

    # --- 🏆 PRIORIDAD 1: RECLAMO DE COFRES ---
    if cofres:
        return "reclamar", cofres[0], "¡Cofre de recompensa brillando! Reclamando premio de metros"

    derecha = (dig[0] + PASO_X, dig[1])
    arriba = (dig[0], dig[1] - PASO_Y)
    abajo = (dig[0], dig[1] + PASO_Y)

    # 🔥 SISTEMA ROMPE-BUCLES POR ATAQUE (Evita atascos en esquinas)
    if CONTADOR_REBOTES >= 3:
        CONTADOR_REBOTES = 0
        ULTIMA_DIRECCION_ELEGIDA = None
        return "romper", derecha, "[SOLUCIÓN BUCLE] Vaivén vertical detectado: Forzando demolición frontal"

    # --- 🎯 PRIORIDAD 2: CACERÍA INTELIGENTE DE TICKETS NARANJAS ---
    if tickets:
        objetivo = tickets[0]
        destino = paso_hacia(dig, objetivo)

        if not hay_piramide(piramides, *destino):
            time.sleep(0.05)
            direc_actual = "arriba" if destino[1] < dig[1] else "abajo" if destino[1] > dig[1] else "derecha"
            if direc_actual in ["arriba", "abajo"]:
                if ULTIMA_DIRECCION_ELEGIDA and direc_actual != ULTIMA_DIRECCION_ELEGIDA:
                    CONTADOR_REBOTES += 1
                else:
                    CONTADOR_REBOTES = 0
                ULTIMA_DIRECCION_ELEGIDA = direc_actual
            return "mover", destino, f"Asegurando captura de ticket en {objetivo}"

        alterno = paso_esquivando(dig, objetivo, destino, piramides, camino_chico)
        if alterno:
            direc_actual = "arriba" if alterno[1] < dig[1] else "abajo" if alterno[1] > dig[1] else "derecha"
            if direc_actual in ["arriba", "abajo"]:
                if ULTIMA_DIRECCION_ELEGIDA and direc_actual != ULTIMA_DIRECCION_ELEGIDA:
                    CONTADOR_REBOTES += 1
                else:
                    CONTADOR_REBOTES = 0
                ULTIMA_DIRECCION_ELEGIDA = direc_actual
            return "mover", alterno, "Desvío inteligente hacia ticket"

    # --- 🚀 PRIORIDAD 3: REGLA DE ORO DEL AVANCE RECTO (Frena la caída infinita) ---
    # Si el frente está limpio, el bot avanza a la derecha de forma obligatoria, rompiendo
    # cualquier imantación o inercia hacia abajo.
    if not hay_piramide(piramides, *derecha) and casilla_libre(camino_chico, *derecha):
        CONTADOR_REBOTES = 0
        ULTIMA_DIRECCION_ELEGIDA = None
        return "mover", derecha, "Bandejón central despejado: priorizando avance recto ➡️"

    # --- 🧭 PRIORIDAD 4: EXPLORACIÓN GENERAL CON RADAR EN ABANICO ---
    densidad_abajo = evaluar_densidad_ruta(dig, "abajo", camino_chico, piramides)
    densidad_arriba = evaluar_densidad_ruta(dig, "arriba", camino_chico, piramides)

    if densidad_abajo > densidad_arriba:
        candidatos = [("abajo", abajo), ("arriba", arriba)]
    elif densidad_arriba > densidad_abajo:
        candidatos = [("arriba", arriba), ("abajo", abajo)]
    else:
        # Desempate inteligente corregido: Si las densidades son iguales, elige el lado opuesto 
        # al último paso vertical realizado para mantener la caminata centrada y equilibrada.
        if ultima_vert == "abajo":
            candidatos = [("arriba", arriba), ("abajo", abajo)]
        else:
            candidatos = [("abajo", abajo), ("arriba", arriba)]

    bloqueadas = []
    for nombre, pos in candidatos:
        if hay_piramide(piramides, *pos):
            if nombre == "derecha":
                bloqueadas.insert(0, pos)
            else:
                bloqueadas.append(pos)
        elif casilla_libre(camino_chico, *pos):
            if nombre in ["arriba", "abajo"]:
                if ULTIMA_DIRECCION_ELEGIDA and nombre != ULTIMA_DIRECCION_ELEGIDA:
                    CONTADOR_REBOTES += 1
                else:
                    CONTADOR_REBOTES = 0
                ULTIMA_DIRECCION_ELEGIDA = nombre
            return "mover", pos, f"Línea de exploración despejada hacia {nombre}"

    CONTADOR_REBOTES = 0
    ULTIMA_DIRECCION_ELEGIDA = None
    if bloqueadas:
        return "romper", derecha, "Frente obstruido sin desvíos válidos: demoliendo frontal"
    return "romper", derecha, "Lectura de suelo inconsistente: forzando despeje"
 
 
# ----------------------------- Interfaz y Main -----------------------------
def interfaz_iniciar():
    global corriendo, hilo_bot
    if not corriendo:
        corriendo = True
        btn_iniciar.config(state=tk.DISABLED)
        btn_detener.config(state=tk.NORMAL)
        lbl_estado.config(text="ESTADO: EJECUTANDO 🦖⚡", fg="#00FF00")
        hilo_bot = threading.Thread(target=bucle_principal_bot, daemon=True)
        hilo_bot.start()
 
 
def interfaz_detener():
    global corriendo
    if corriendo:
        corriendo = False
        btn_iniciar.config(state=tk.NORMAL)
        btn_detener.config(state=tk.DISABLED)
        lbl_estado.config(text="ESTADO: APAGADO 🛑", fg="#FF3333")
 
 
def bucle_principal_bot():
    """
    Módulo v2.7.0 Distribución Abierta: Corre el motor en segundo plano.
    Obliga al usuario a colocar sus propios archivos .png personalizados en la carpeta.
    """
    global corriendo
    
    # 📁 ENTORNO MODULAR: El bot lee las imágenes locales generadas por tus amigos en su PC
    t_digimon_frente = cv2.imread("digimon.png", cv2.IMREAD_GRAYSCALE)
    t_digimon_espalda = cv2.imread("digimon_espalda.png", cv2.IMREAD_GRAYSCALE)
    t_piramide = cv2.imread("piramide.png", cv2.IMREAD_GRAYSCALE)
    t_cofre = cv2.imread("cofre.png", cv2.IMREAD_GRAYSCALE)
    t_ticket = cv2.imread("ticket.png", cv2.IMREAD_GRAYSCALE)
    
    # 📋 SISTEMA DE INSTRUCCIONES: Validación estricta para guiar a tus amigos paso a paso
    archivos_faltantes = []
    if t_digimon_frente is None: archivos_faltantes.append("- digimon.png (Tu Digimon de frente)")
    if t_digimon_espalda is None: archivos_faltantes.append("- digimon_espalda.png (Tu Digimon de espalda)")
    if t_piramide is None: archivos_faltantes.append("- piramide.png (Obstáculo del mapa)")
    if t_cofre is None: archivos_faltantes.append("- cofre.png (Premio de la barra inferior)")
    if t_ticket is None: archivos_faltantes.append("- ticket.png (Ticket naranja de farmeo)")
    
    if archivos_faltantes:
        mensaje_instrucciones = (
            "¡Hola! Para activar DigiWorld Controller en tu PC, necesitas colocar tus propias "
            "capturas de pantalla recortadas en esta misma carpeta.\n\n"
            "Por favor, toma un recorte de tu BlueStacks y guarda los siguientes archivos faltantes:\n" +
            "\n".join(archivos_faltantes) +
            "\n\nUna vez guardados los archivos, presiona INICIAR BOT nuevamente."
        )
        messagebox.showwarning("Faltan Plantillas Visuales", mensaje_instrucciones)
        interfaz_detener()
        return
 
    ultima_vert = None
    while corriendo:
        bgr, gris_chico, hsv_chico = capturar()
        dig = detectar_digimon(gris_chico, t_digimon_frente, t_digimon_espalda)
        if dig is None:
            time.sleep(0.3)
            continue
        piramides = detectar_piramides(gris_chico, t_piramide)
        tickets = detectar_tickets(hsv_chico, dig)
        camino_chico = cv2.inRange(hsv_chico, CELESTE_BAJO, CELESTE_ALTO)
        cofres = detectar_cofres_listos(gris_chico, t_cofre)
        tipo, destino, motivo = decidir(dig, piramides, tickets, camino_chico, ultima_vert, cofres)
        if DEBUG:
            guardar_debug(bgr, dig, piramides, tickets, destino)
        if tipo == "reclamar":
            clic(*destino)
            time.sleep(0.15)
        elif tipo == "mover":
            clic(*destino)
            # CORRECCIÓN DE INERCIA: Evaluamos el eje Y [1] para saber si realmente bajó o subió
            if destino[1] != dig[1]:
                ultima_vert = "abajo" if destino[1] > dig[1] else "arriba"
            esperar_reaccion(gris_chico)
        else:
            clic(*destino)
            time.sleep(GIRO_ESPERA)
            atacar()
            esperar_reaccion(gris_chico)
 
 
def recurso_path(relative_path):
    """ Obtiene la ruta absoluta de los recursos empaquetados dinámicamente por PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
 
 
def main():
    """Construye la ventana visual premium con las medidas reales del banner (v2.7.0)."""
    global btn_iniciar, btn_detener, lbl_estado, corriendo
    corriendo = False
 
    ventana = tk.Tk()
    ventana.title("DigiWorld Controller v2.7.0")
    ventana.geometry("700x520")
    ventana.configure(bg="#121212")
    ventana.resizable(False, False)
 
    marco_izquierdo = tk.Frame(ventana, bg="#121212")
    marco_izquierdo.pack(side=tk.LEFT, padx=(20, 10), pady=10)
 
    try:
        ruta_banner = recurso_path("banner.png")
        img_banner = tk.PhotoImage(file=ruta_banner)
        lbl_banner = tk.Label(marco_izquierdo, image=img_banner, bg="#121212", bd=0, highlightthickness=0)
        lbl_banner.image = img_banner
        lbl_banner.pack()
    except Exception:
        lbl_respaldo = tk.Label(marco_izquierdo, text="[ REPOSITORIO\nDIGIMON ]",
                                bg="#1F1F1F", fg="#666666", width=35, height=25,
                                font=("Arial", 10, "bold"))
        lbl_respaldo.pack()
 
    marco_derecho = tk.Frame(ventana, bg="#121212")
    marco_derecho.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=(10, 25), pady=40)
 
    tk.Label(marco_derecho, text="DIGIMON UP",
             bg="#121212", fg="#00FF00", font=("Arial", 20, "bold")).pack(anchor=tk.W, pady=(20, 2))
    tk.Label(marco_derecho, text="Exploración Universal Automática",
             bg="#121212", fg="#888888", font=("Arial", 11, "italic")).pack(anchor=tk.W, pady=(0, 40))
 
    lbl_estado = tk.Label(marco_derecho, text="ESTADO: APAGADO 🛑",
                          bg="#1F1F1F", fg="#FF3333", font=("Arial", 12, "bold"),
                          width=22, height=3, bd=0, relief=tk.FLAT)
    lbl_estado.pack(pady=(0, 45))
 
    btn_iniciar = tk.Button(marco_derecho, text="INICIAR BOT", bg="#00CC00", fg="#FFFFFF",
                            activebackground="#00FF00", font=("Arial", 11, "bold"),
                            width=20, height=2, bd=0, relief=tk.FLAT, cursor="hand2",
                            command=interfaz_iniciar)
    btn_iniciar.pack(pady=8)
 
    btn_detener = tk.Button(marco_derecho, text="DETENER", bg="#CC0000", fg="#FFFFFF",
                            activebackground="#FF0000", font=("Arial", 11, "bold"),
                            width=20, height=2, bd=0, relief=tk.FLAT, cursor="hand2",
                            state=tk.DISABLED, command=interfaz_detener)
    btn_detener.pack(pady=8)
 
    ventana.mainloop()
 
 
if __name__ == "__main__":
    main()