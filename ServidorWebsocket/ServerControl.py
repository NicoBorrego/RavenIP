import asyncio
import websockets
import os
import json
import base64
import sys
import imageio
from datetime import date
from datetime import datetime
from PIL import Image
import cv2
import zlib
import ssl


cliente_alumno = None
cliente_profesor = None
semaforo = asyncio.Semaphore(value=0.5)
ip_profesor = "192.168.1.41"
puerto = sys.argv[1]
guardar = False
terminado = False
directorio = ""

def guardarCaptura(imagen):
    global cliente_alumno, directorio
    
    if not os.path.exists(directorio):
        os.makedirs(directorio)

    if len(imagen) > 0:
        # Obtener la fecha y hora actual
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Guardar la imagen en el servidor con un nombre único que incluya el tiempo
        image_filename = os.path.join(directorio, f"cap_{cliente_alumno.remote_address[0]}_{timestamp}.png")
        with open(image_filename, 'wb') as image_file:
            image_file.write(imagen)
        print(f"Captura guardada como {image_filename}")
    else:
        print("Datos de captura no válidos.")

def crearVideo(ruta_capturas):
    # Obtener la lista de nombres de archivos de imágenes en la carpeta
    global cliente_alumno
    fps = 2
    nombre = "(" + str(date.today().strftime('%Y-%m-%d')) + ")" + str(cliente_alumno.remote_address[0]) + ".mp4"
    ruta_video = os.path.join(ruta_capturas, nombre)  # Ruta del video

    # Obtener la lista de nombres de archivos de imágenes ordenados por tiempo de creación
    archivos_imagenes = sorted(os.listdir(ruta_capturas), key=lambda x: os.path.getctime(os.path.join(ruta_capturas, x)))

    # Obtener las dimensiones de la primera imagen para establecer el tamaño del video
    primera_imagen = cv2.imread(os.path.join(ruta_capturas, archivos_imagenes[0]))
    height, width, _ = primera_imagen.shape
    # Crear el objeto de escritura de video
    writer = cv2.VideoWriter(ruta_video, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    # Iterar sobre cada imagen y agregarla al video
    for nombre_archivo in archivos_imagenes:
        ruta_imagen = os.path.join(ruta_capturas, nombre_archivo)
        imagen = cv2.imread(ruta_imagen)
        writer.write(imagen)

    # Cerrar el objeto de escritura de video
    writer.release()

    print(f"Video creado exitosamente como {ruta_video}")
async def instrucciones(mensaje,alumno):
    global guardar, terminado
    # Envía la instrucción al cliente
    try:
        async with semaforo:
            if mensaje == "capturar":
                guardar = True
                terminado = False
            elif mensaje == "parar":
                guardar = False
                terminado = True
            await alumno.send(mensaje)
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Error en la conexión: {e}")

async def vnc_server(websocket, path):
    global cliente_profesor, cliente_alumno, guardar, terminado, directorio

    # Obtiene la dirección IP del cliente
    cliente_ip = websocket.remote_address[0]
    print(f"Nuevo cliente conectado desde la IP: {cliente_ip}")

    try:
        # Si el cliente es el profesor, lo establece como el cliente_profesor
        if cliente_ip == ip_profesor:
            cliente_profesor = websocket
            print("Cliente profesor conectado.")
        else:
            # Asigna un identificador único al alumno y guarda su conexión
            cliente_alumno = websocket
            directorio = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)),"Capturas"),cliente_alumno.remote_address[0])
            print(f"Alumno conectado.")
        while True:
            # Recibe la captura de pantalla del cliente (ya sea profesor o alumno)
            screenshot_data = await websocket.recv()
            # Envía la captura de pantalla al cliente profesor
            if cliente_profesor and cliente_alumno:
                if cliente_ip == ip_profesor:
                    try:
                        asyncio.create_task(instrucciones(screenshot_data,cliente_alumno))
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(f"Error en la conexión con el profesor: {e}")
                else:
                    try:
                        image_data = base64.b64decode(screenshot_data)
                        screenshot_decompressed = zlib.decompress(image_data)
                        image_base64 = base64.b64encode(screenshot_decompressed).decode('utf-8')
                        if guardar:
                            guardarCaptura(screenshot_decompressed)
                        elif terminado:
                            crearVideo(directorio)
                            terminado = False
                        await cliente_profesor.send(image_base64)
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(f"Error en la conexión con el profesor: {e}")

            await asyncio.sleep(0.1)
    except websockets.exceptions.ConnectionClosedOK:
        print(f"Cliente desconectado. clientid: {cliente_ip}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Error en la conexión: {e}")
    except Exception as e:
        print(f"Error en el servidor: {e}")
    finally:
        # Si el cliente desconectado es el profesor, lo elimina como cliente_profesor
        if cliente_ip == ip_profesor:
            cliente_profesor = None
            print("Cliente profesor desconectado.")
        elif cliente_ip == cliente_alumno.remote_address[0]:
            # Elimina la conexión del alumno desconectado del diccionario
            cliente_ip = None
            print(f"Alumno desconectado.")


if __name__ == "__main__":
    size = 10 * 1024 * 1024
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(os.path.join(os.path.dirname(os.path.realpath(__file__)),"RavenIP_ServerWS.crt"), os.path.join(os.path.dirname(os.path.realpath(__file__)),"RavenIP_ServerWS.pem"))
    start_server = websockets.serve(vnc_server, "0.0.0.0", puerto, ssl=ssl_context, ping_interval=5, ping_timeout=2,max_size=size)
    print(f"Servidor WebSocket VNC en ejecución en ws://0.0.0.0:{puerto}")
    try:
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("Servidor detenido por el usuario.")
    except Exception as e:
        print(f"Error general en el servidor: {e}")
    finally:
        asyncio.get_event_loop().close()