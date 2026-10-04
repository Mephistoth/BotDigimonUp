"""
Bot isométrico - Digimon (BlueStacks)
Versión 2.5.7: Base v2.5.1 + Sistema Rompe-Bucles por Ataque Automatizado.

Teclas: G = iniciar | Q = apagar
Requisitos: pip install pyautogui opencv-python numpy keyboard mss
Archivos en la carpeta: digimon.png, digimon_espalda.png, piramide.png, cofre.png
"""
import time
import random
import logging
import sys
import cv2
import ctypes
import numpy as np 
import pyautogui
import keyboard
import mss

pyautogui.PAUSE = 0                # Elimina el retraso involuntario de pyautogui tras cada clic

# ============================== CONFIGURACIÓN ==============================
# Zona de juego en pantalla (x, y, ancho, alto).
ROI_X, ROI_Y, ROI_W, ROI_H = 430, 150, 1020, 680

BOTON_ATAQUE = (615, 890)          # en coordenadas de pantalla física
PASO_X, PASO_Y = 110, 70           # tamaño de una casilla en pantalla

UMBRAL_DIGIMON = 0.46
UMBRAL_PIRAMIDE = 0.70
UMBRAL_COFRE = 0.65                # Coincidencia segura para el cofre de la barra inferior

# Ticket naranja (Filtros HSV a escala real)
TICKET_BAJO = np.array([5, 140, 170])
TICKET_ALTO = np.array([25, 255, 255])
TICKET_AREA_MIN = 38               # px² mínimos adaptados a la reducción de escala (150 / 4)
EXCLUIR_X, EXCLUIR_Y = 28, 22      # zona de exclusión adaptada a la mitad de resolución

# Camino celeste
CELESTE_BAJO = np.array([86, 195, 170])
CELESTE_ALTO = np.array([116, 255, 255])
CASILLA_MIN_RATIO = 0.25           # % de píxeles celestes para considerar una casilla libre

# --- 🐢 Configuración de Velocidad Suavizada y Humana ---
POLL = 0.045                       # Escanea y hace clics cada 45ms (Ritmo más natural)
ESPERA_MAX = 1.5                   # Máx. esperando que reaccione tras un clic
CAMBIO_MIN = 2.0                   # Diferencia mínima para detectar movimiento
CAMBIO_ESTABLE = 1.0               # Umbral para detectar que se detuvo
ESTABLE_MAX = 0.6                  # Espera máxima de fin de animación
GIRO_ESPERA = 0.12                 # Pausa humana para girar antes de golpear (120ms)
ATAQUE_ESPERA = 0.18               # Pausa de recuperación post-ataque (180ms)
INTENTOS_ATASCO = 3                # Clics sin cambio antes de atacar
DEBUG = True                       # Guarda debug_ultimo.png a resolución completa
# ===========================================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("bot")

corriendo = True
ULTIMA_DIRECCION_ELEGIDA = None    # Almacena si el último desvío fue "arriba" o "abajo"
CONTADOR_REBOTES = 0               # Cuenta cuántas veces ha oscilado verticalmente seguidas


def apagar():
    global corriendo
    corriendo = False


# ------------------------------- Captura Ultra Rápida ----------------------------------
def capturar():
    """Captura usando mss de forma directa y genera copias a mitad de escala para OpenCV."""
    with mss.MSS() as sct:
        monitor = {"left": ROI_X, "top": ROI_Y, "width": ROI_W, "height": ROI_H}
        crudo = sct.grab(monitor)
        bgr = np.array(crudo)[:, :, :3]  # Descartar canal Alpha directamente en memoria
        
    # Downscaling: Reducimos dimensiones al 50% usando el método de interpolación más rápido
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
    """Busca al Digimon reduciendo la plantilla para acoplarse al Downscaling."""
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
    if not (0 <= cx < (ROI_W // 2) and 0 <= cy < (ROI_H // 2)):
        return False
    
    parche = camino_chico[max(0, cy - 8):cy + 8, max(0, cx - 8):cx + 8]
    return parche.size > 0 and (np.count_nonzero(parche) / parche.size) >= CASILLA_MIN_RATIO


def detectar_cofres_listos(gris_chico, plantilla_cofre):
    """Módulo v2.5.1: Busca el cofre en la franja inferior usando Template Matching."""
    if plantilla_cofre is None:
        return []
    c_chica = cv2.resize(plantilla_cofre, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST)
    alto, ancho = c_chica.shape[:2]
    
    y_limite_chico = int((ROI_H - 120) // 2)
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
    """Envía un clic físico instantáneo (0 ms) mediante la API de Windows."""
    pantalla_x = ROI_X + x + random.randint(-2, 2)
    pantalla_y = ROI_Y + y + random.randint(-2, 2)
    
    ctypes.windll.user32.SetCursorPos(pantalla_x, pantalla_y)
    ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0) # left down
    ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0) # left up


def atacar():
    pyautogui.click(*BOTON_ATAQUE)
    time.sleep(ATAQUE_ESPERA)


def esperar_reaccion(gris_antes_chico):
    """Monitorea el cambio de frames usando la matriz optimizada reducida."""
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
    """
    Versión 2.5.7 Ultra-Evasión: Evalúa rutas de escape limpias hacia el ticket.
    Aplica descarte absoluto: si un carril proyectado a futuro contiene una pirámide,
    la ruta se elimina por completo para forzar rodeos 100% limpios y sin golpes.
    """
    direcciones = [
        (PASO_X, 0),   # Derecha
        (0, -PASO_Y),  # Arriba
        (0, PASO_Y)    # Abajo
    ]
    
    libres = []
    
    for dx, dy in direcciones:
        v1 = (dig[0] + dx, dig[1] + dy)
        if v1 == bloqueado:
            continue
            
        # Filtro inmediato: Si la casilla de desvío inicial tiene pirámide o no es celeste, se salta
        if hay_piramide(piramides, *v1) or not casilla_libre(camino_chico, *v1):
            continue
            
        # Proyección profunda de carril a 2 pasos hacia el ticket
        carril_completamente_limpio = True
        for ddx, ddy in direcciones:
            if (dx + ddx == 0) and (dy + ddy == 0):
                continue
            v2 = (v1[0] + ddx, v1[1] + ddy)
            
            # Si el camino se cierra más adelante, marcamos el peligro
            if hay_piramide(piramides, *v2):
                carril_completamente_limpio = False
                break

        # 🚫 ULTRA-EVASIÓN: Si el carril no está 100% limpio a futuro, lo ignoramos por completo.
        # Ya no le sumamos "+ 10"; preferimos descartarlo para obligar al bot a buscar otra alternativa.
        if carril_completamente_limpio:
            d = abs(v1[0] - objetivo[0]) / PASO_X + abs(v1[1] - objetivo[1]) / PASO_Y
            libres.append((d, v1))

    # Si encontramos una ruta impecable, el bot avanza por ella
    if libres:
        return min(libres)[1]
        
    return None


def evaluar_densidad_ruta(pos_inicial, direccion_nombre, camino_chico, piramides):
    """Versión 2.5.6 Unificada: Radar en abanico a 3 pasos de profundidad."""
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


#Decisión -------------------------------
def decidir(dig, piramides, tickets, camino_chico, ultima_vert, cofres):
    global ULTIMA_DIRECCION_ELEGIDA, CONTADOR_REBOTES

    # --- 🏆 PRIORIDAD 1: RECLAMO DE COFRES ---
    if cofres:
        return "reclamar", cofres[0], "¡Cofre de recompensa brillando! Reclamando premio de metros"

    derecha = (dig[0] + PASO_X, dig[1])
    arriba = (dig[0], dig[1] - PASO_Y)
    abajo = (dig[0], dig[1] + PASO_Y)

    # 🔥 SISTEMA ROMPE-BUCLES POR ATAQUE (v2.5.7)
    if CONTADOR_REBOTES >= 3:
        CONTADOR_REBOTES = 0
        ULTIMA_DIRECCION_ELEGIDA = None
        return "romper", derecha, "[SOLUCIÓN BUCLE] Vaivén vertical detectado: Forzando demolición frontal"

    # --- 🎯 PRIORIDAD 2: CASERÍA DE TICKETS NARANJAS ---
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
            return "mover", alterno, f"Desvío inteligente para buscar ruta limpia hacia ticket"

    # --- 🚀 PRIORIDAD 3: REGLA DEL BANDEJÓN CENTRAL LIBRE ---
    if not hay_piramide(piramides, *derecha) and casilla_libre(camino_chico, *derecha):
        CONTADOR_REBOTES = 0
        ULTIMA_DIRECCION_ELEGIDA = None
        return "mover", derecha, "Bandejón central despejado: priorizando avance recto"

    # --- 🧭 PRIORIDAD 4: EXPLORACIÓN GENERAL CON RADAR EN ABANICO ---
    densidad_abajo = evaluar_densidad_ruta(dig, "abajo", camino_chico, piramides)
    densidad_arriba = evaluar_densidad_ruta(dig, "arriba", camino_chico, piramides)

    if densidad_abajo > densidad_arriba:
        candidatos = [("abajo", abajo), ("arriba", arriba)]
    elif densidad_arriba > densidad_abajo:
        candidatos = [("arriba", arriba), ("abajo", abajo)]
    else:
        verticales = [arriba, abajo]
        if ultima_vert == "abajo":
            verticales.reverse()
        candidatos = [("arriba" if v == arriba else "abajo", v) for v in verticales]

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

    # --- 🔨 ÚLTIMO RECURSO ABSOLUTO ---
    CONTADOR_REBOTES = 0
    ULTIMA_DIRECCION_ELEGIDA = None
    if bloqueadas:
        return "romper", derecha, "Frente obstruido sin desvíos válidos: demoliendo frontal"
    return "romper", derecha, "Lectura de suelo inconsistente: forzando despeje"


#Main
def main():
    print("=" * 52)
    print("  BOT ISOMÉTRICO v2.5.7 - ROMPE-BUCLES AUTOMÁTICO")
    print("  G = iniciar | Q = apagar")
    print("=" * 52)

    t_digimon_frente = cv2.imread("digimon.png", cv2.IMREAD_GRAYSCALE)
    t_digimon_espalda = cv2.imread("digimon_espalda.png", cv2.IMREAD_GRAYSCALE)
    t_piramide = cv2.imread("piramide.png", cv2.IMREAD_GRAYSCALE)
    t_cofre = cv2.imread("cofre.png", cv2.IMREAD_GRAYSCALE)

    if t_digimon_frente is None:
        log.error("Falta digimon.png en el directorio actual. Abortando.")
        return

    keyboard.add_hotkey("q", apagar)
    print("\n[RENDIMIENTO] Esperando la tecla 'G' para tomar el control...")
    keyboard.wait("g")

    for i in range(3, 0, -1):
        log.info("Iniciando en %d... Pon la ventana de BlueStacks al frente", i)
        time.sleep(1)

    ultima_vert = None
    sin_cambio = 0
    sin_digimon = 0
    t_ciclo = None

    while corriendo:
        if DEBUG and t_ciclo is not None:
            log.info("Análisis de ciclo: %.3fs", time.time() - t_ciclo)
        t_ciclo = time.time()

        bgr, gris_chico, hsv_chico = capturar()
        dig = detectar_digimon(gris_chico, t_digimon_frente, t_digimon_espalda)

        if dig is None:
            sin_digimon += 1
            log.warning("Buscando al Digimon en la matriz reducida (%d)...", sin_digimon)
            time.sleep(0.3)
            continue

        sin_digimon = 0
        piramides = detectar_piramides(gris_chico, t_piramide)
        tickets = detectar_tickets(hsv_chico, dig)
        camino_chico = cv2.inRange(hsv_chico, CELESTE_BAJO, CELESTE_ALTO)
        cofres = detectar_cofres_listos(gris_chico, t_cofre)
        tipo, destino, motivo = decidir(dig, piramides, tickets, camino_chico, ultima_vert, cofres)

        if DEBUG:
            guardar_debug(bgr, dig, piramides, tickets, destino)
        log.info("[%s] %s -> Objetivo: %s", tipo.upper(), motivo, destino)

        if tipo == "reclamar":
            clic(*destino)
            time.sleep(0.15)
        elif tipo == "mover":
            clic(*destino)
            if destino[0] == dig[0]:
                ultima_vert = "arriba" if destino[1] < dig[1] else "abajo"
            if esperar_reaccion(gris_chico):
                sin_cambio = 0
            else:
                sin_cambio += 1
                log.warning("Sin respuesta de movimiento (%d/%d)", sin_cambio, INTENTOS_ATASCO)
                if sin_cambio >= INTENTOS_ATASCO:
                    log.info("[EMERGENCIA] Ejecutando ataque por falta de refresco visual")
                    atacar()
                    sin_cambio = 0
        elif tipo == "romper":
            clic(*destino)
            time.sleep(GIRO_ESPERA)
            atacar()
            esperar_reaccion(gris_chico)

    log.info("Bot de alta velocidad apagado de forma segura.")


if __name__ == "__main__":
    main()