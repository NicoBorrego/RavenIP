import asyncio
import websockets
import pyautogui
import base64
import io
import sys
import zlib
import os
from PIL import ImageGrab
import platform
import ssl
from OpenSSL import crypto

teclas = {
    'Digit0': '0',
    'Digit1': '1',
    'Digit2': '2',
    'Digit3': '3',
    'Digit4': '4',
    'Digit5': '5',
    'Digit6': '6',
    'Digit7': '7',
    'Digit8': '8',
    'Digit9': '9',
    'Numpad0': '0',
    'Numpad1': '1',
    'Numpad2': '2',
    'Numpad3': '3',
    'Numpad4': '4',
    'Numpad5': '5',
    'Numpad6': '6',
    'Numpad7': '7',
    'Numpad8': '8',
    'Numpad9': '9',
    'KeyA': 'a',
    'KeyB': 'b',
    'KeyC': 'c',
    'KeyD': 'd',
    'KeyE': 'e',
    'KeyF': 'f',
    'KeyG': 'g',
    'KeyH': 'h',
    'KeyI': 'i',
    'KeyJ': 'j',
    'KeyK': 'k',
    'KeyL': 'l',
    'KeyM': 'm',
    'KeyN': 'n',
    'KeyO': 'o',
    'KeyP': 'p',
    'KeyQ': 'q',
    'KeyR': 'r',
    'KeyS': 's',
    'KeyT': 't',
    'KeyU': 'u',
    'KeyV': 'v',
    'KeyW': 'w',
    'KeyX': 'x',
    'KeyY': 'y',
    'KeyZ': 'z',
    'Space': 'space',
    'Enter': 'enter',
    'Backspace': 'backspace',
    'Escape': 'esc',
    'Tab': 'tab',
    'CapsLock': 'capslock',
    'ShiftLeft': 'shiftleft',
    'ControlLeft': 'ctrlleft',
    'AltLeft': 'altleft',
    'MetaLeft': 'winleft',
    'ShiftRight': 'shiftright',
    'ControlRight': 'ctrlright',
    'AltRight': 'altright',
    'MetaRight': 'winright',
    'ArrowUp': 'up',
    'ArrowDown': 'down',
    'ArrowLeft': 'left',
    'ArrowRight': 'right',
    'F1': 'f1',
    'F2': 'f2',
    'F3': 'f3',
    'F4': 'f4',
    'F5': 'f5',
    'F6': 'f6',
    'F7': 'f7',
    'F8': 'f8',
    'F9': 'f9',
    'F10': 'f10',
    'F11': 'f11',
    'F12': 'f12',
}

ipServidor = sys.argv[1]
puerto = sys.argv[2]
ruta_cap = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Capturas")

def capturar():
    # Función para capturar la pantalla con el tamaño especificado
    ancho, alto = ImageGrab.grab().size
    
    screenshot = ImageGrab.grab(bbox=(0, 0, ancho, alto))
    
    # Convertir la captura a bytes
    cap_bytes = io.BytesIO()
    screenshot.save(cap_bytes, format='PNG')
    screenshot_comprimido = zlib.compress(cap_bytes.getvalue())
    screenshot_base64 = base64.b64encode(screenshot_comprimido).decode('utf-8')

    return screenshot_base64

async def instrucciones(websocket):
    pyautogui.FAILSAFE = False
    tecla=""
    try:
        while True:
            # Espera recibir instrucciones del servidor
            mensaje = await websocket.recv()
            cadena = mensaje.split(':') 
            if cadena[0] == "move":
                pyautogui.moveTo(float(cadena[1]),float(cadena[2]))
            elif cadena[0] == "click":
                pyautogui.click(float(cadena[1]),float(cadena[2]))
            elif cadena[0] == "rclick":
                pyautogui.moveTo(float(cadena[1]),float(cadena[2]))
                pyautogui.click(button="right")
            elif cadena[0] == "key":
                tecla=teclas[cadena[1]]
                if tecla!= "":
                    pyautogui.press(tecla)
            elif cadena[0] == "wheel":
                pyautogui.scroll(int(cadena[1]))
            elif cadena[0] == "drag":
                pyautogui.dragTo(cadena[1],cadena[2], button='left')
            else:
                continue
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Error en la conexión: {e}")

async def enviar_capturas_al_servidor():
    global ipServidor,puerto, captura, capture
    uri = f"wss://{ipServidor}:{puerto}"
    cert_pem = os.path.join(os.path.dirname(os.path.realpath(__file__)), "RavenIP_ClientWS.crt")
    private_key_pem = os.path.join(os.path.dirname(os.path.realpath(__file__)), "RavenIP_ClientWS.pem")

    # Crea un contexto SSL
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.load_verify_locations(cafile=os.path.join(os.path.dirname(os.path.realpath(__file__)), "RavenIP_CA.crt"))

    # Carga el certificado .pem y la clave privada .pem
    ssl_context.load_cert_chain(cert_pem, private_key_pem)
    while True:
        try:
            async with websockets.connect(uri, timeout=10, ssl=ssl_context) as websocket:
                websocket.max_size = 268435456
                print(f"Conexión establecida correctamente con el servidor {puerto}.")
                # Inicia la corutina para recibir instrucciones
                asyncio.create_task(instrucciones(websocket))

                while True:
                    await websocket.send(capturar())
                    await asyncio.sleep(0.5)
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Error en la conexión: {e}")
            break
        except Exception as e:
            print(f"Error general en el cliente: {e}")
            break

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(enviar_capturas_al_servidor())
