import os
import json
import time
import subprocess
import websockets
import asyncio
import zlib
import io
from PIL import ImageGrab
import platform
from datetime import datetime, timedelta
import psutil
import speedtest
import ssl
from OpenSSL import crypto

# Ruta archivo de datos
ruta_json = os.path.join(os.path.dirname(os.path.realpath(__file__)),"datos.json")
# Ruta de exe de python
ruta_python = os.path.join(os.getenv('LOCALAPPDATA'),"Programs","Python","Python312","python.exe")
# Ruta del script de control
ruta_control = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ClienteControl.py")
ipServidor = "192.168.1.41"
puerto = "8765"
datos = []
proc = None
procCapturas = None
data = []
datos_antiguos = []
informe = False
ruta = os.path.join(os.path.dirname(os.path.realpath(__file__)),"datos.json")

def capturar():
    # Ancho y alto de pantalla
    ancho, alto = ImageGrab.grab().size
    # Captura desde 
    screenshot = ImageGrab.grab(bbox=(0, 0, ancho, alto))
    
    # Convertir la captura a bytes
    cap_bytes = io.BytesIO()
    # Guardo como PNG
    screenshot.save(cap_bytes, format='PNG')
    # Compresión para el envío
    screenshot_comprimido = zlib.compress(cap_bytes.getvalue())

    return screenshot_comprimido
def load_pfx_certificate(pfx_path, password):
    with open(pfx_path, "rb") as pfx_file:
        pfx_data = pfx_file.read()

    pfx = crypto.load_pkcs12(pfx_data, password.encode())
    cert = pfx.get_certificate()
    private_key = pfx.get_privatekey()

    return cert, private_key

async def instrucciones(websocket):
    global proc, data, informe, ruta_control, ruta_python
    try:
        await asyncio.sleep(5)
        while True:
            # Espera recibir instrucciones del servidor
            mensaje = await websocket.recv()
            instrucciones = mensaje.split(':')
            if instrucciones[0] == "control":
                proc = subprocess.Popen(["start", "cmd", "/c", f"{ruta_python} {ruta_control} {instrucciones[1]} {instrucciones[2]}"], shell=True)
            elif instrucciones[0] == "terminado":
                proc.kill()
                print("Proceso de control terminado")
                proc = None
            elif instrucciones[0] == "informe":
                informe = True
            elif instrucciones[0] == "apagar":
                os.system('shutdown -p')
            elif instrucciones[0] == "reiniciar":
                os.system('shutdown -r -t 0')
            
    except websockets.exceptions.ConnectionClosedError as e:
        if isinstance(e, websockets.exceptions.ConnectionClosedOK):
            print("Conexión cerrada por el servidor.")
        else:
            print(f"Error en la conexión: {e}")

async def enviar_capturas_al_servidor():
    global ipServidor,puerto, data, informe, ancho, alto, ruta_json
    uri = f"wss://{ipServidor}:{puerto}"
    datos_json = {}

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
                print("Conexión establecida correctamente con el servidor.")
                asyncio.create_task(instrucciones(websocket))
                while True:
                    if informe is False:
                        await websocket.send(capturar())
                        await asyncio.sleep(3)
                    else:
                        with open(ruta_json, 'r') as archivo:
                            datos_json = json.load(archivo)
                            data = {
                                "Sistema operativo": platform.system() + " " + platform.release(),
                                "Monitoreo": datos_json["data"]
                            }
                        print("Datos a enviar: ",data)
                        await websocket.send(json.dumps(data))
                        informe = False
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Error en la conexión: {e}")
            break
        except Exception as e:
            print(f"Error general en el cliente: {e}")


if __name__ == "__main__":
    print("Iniciando el servicio...")
    asyncio.get_event_loop().run_until_complete(enviar_capturas_al_servidor())
