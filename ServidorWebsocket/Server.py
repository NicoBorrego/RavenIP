import asyncio
import websockets
import os
import json
import base64
import subprocess
import zlib
import ssl
import os
import pathlib

# Diccionario para almacenar las conexiones de los alumnos
alumnos_conexiones = {}
cliente_profesor = None
ip_profesor = "192.168.1.41"
inicio = 8765
servidores = {}
servicios = []
puertos = []
cap = True

def buscarPuerto(inicio,servicios,puertos):
    encontrado = False
    puerto = inicio
    while encontrado == False:
        try:
            print(puerto)
            puertos.index(puerto)
            puerto+=1
        except:
            encontrado = True
    puertos.append(puerto)
    return puerto

def pararProceso(proceso):
    proceso.kill()
    print("Proceso terminado")


async def servidor(websocket, path):
    global cliente_profesor, alumnos_conexiones, puerto, servicios, inicio, puertos, cap

    # Obtiene la dirección IP del cliente
    cliente_ip = websocket.remote_address[0]
    print(f"Nuevo cliente conectado desde la IP: {cliente_ip}")

    try:
        clientid = None  # Inicializar clientid en caso de que el cliente sea el profesor
        # Si el cliente es el profesor, lo establece como el cliente_profesor
        if cliente_ip == ip_profesor:
            cliente_profesor = websocket
            print("Cliente profesor conectado.")
        else:
            # Asigna un identificador único al alumno y guarda su conexión
            clientid = cliente_ip
            alumnos_conexiones[clientid] = websocket
            print(f"Alumno conectado. clientid: {clientid}")

        while True:
            # Recibe la captura de pantalla del cliente (ya sea profesor o alumno)
            screenshot_data = await websocket.recv()
            if cap is False:
                try:
                    datos = json.loads(screenshot_data)
                    informacion = {
                        "action": "informe",
                        "datos" : datos
                    }
                    print("Enviando............. ",informacion)
                    if datos:
                        await cliente_profesor.send(json.dumps(informacion))
                    cap = True
                except json.JSONDecodeError:
                    cap = True
            else:
                # Envía la captura de pantalla al cliente profesor
                if cliente_profesor and clientid:
                    try:
                        screenshot_decompressed = zlib.decompress(screenshot_data)
                        screenshot_data_base64 = base64.b64encode(screenshot_decompressed).decode('utf-8')
                        # En lugar de enviar una cadena directamente, envía un objeto JSON
                        data_to_send = {
                            "clientid": clientid,
                            "imageData": screenshot_data_base64
                        }
                        await cliente_profesor.send(json.dumps(data_to_send))
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(f"Error en la conexión con el profesor: {e}")
            if cliente_ip == ip_profesor:
                try:
                    # Convertir el mensaje JSON a un diccionario
                    message_data = json.loads(screenshot_data)
                    print(f"Mensaje recibido: {message_data}")
                    if message_data.get("command") == "shell" and message_data.get("clientid"):
                        command_clientid = message_data["clientid"]
                        if command_clientid in alumnos_conexiones:
                            # El mensaje es un comando shell del profesor
                            alumno_ip = alumnos_conexiones[command_clientid].remote_address[0]
                            comando_ssh = f"ssh Nico@{alumno_ip}"
                            subprocess.run(["start", "cmd", "/k", comando_ssh], shell=True)

                        else:
                            print(f"No se permitió ejecutar el comando shell. No se encontró el alumno con clientid: {command_clientid}")
                    if message_data.get("command") == "control" and message_data.get("clientid"):
                        puerto = buscarPuerto(inicio,servicios,puertos)
                        await alumnos_conexiones[message_data.get("clientid")].send(f"control:{ip_profesor}:{puerto}")
                        informacion = {
                            "clientid": ip_profesor,
                            "puerto": puerto
                        }
                        await cliente_profesor.send(json.dumps(informacion))
                        print("Mensaje enviado")
                        proceso_servidor = subprocess.Popen(["python", "./ServerControl.py", str(puerto)])
                        # Almacenar el objeto Popen en un diccionario usando el puerto como clave
                        servidores[int(puerto)] = proceso_servidor
                    if message_data.get("action") == "cerrado" and message_data.get("puerto"):
                        await alumnos_conexiones[message_data.get("clientid")].send("terminado")
                        print(f"Parando socket en el puerto {message_data.get("puerto")}")
                        puertos.remove(int(message_data.get("puerto")))
                        print(puertos)
                        pararProceso(proceso_servidor)
                    if message_data.get("action") == "informe" and message_data.get("clientid"):
                        cap = False
                        await alumnos_conexiones[message_data.get("clientid")].send(f"informe")
                        print("Mensaje enviado")
                        await alumnos_conexiones[message_data.get("clientid")].send("informe")
                    if message_data.get("action") == "apagar" and message_data.get("clientid"):
                        await alumnos_conexiones[message_data.get("clientid")].send("apagar")
                    if message_data.get("action") == "reiniciar" and message_data.get("clientid"):
                        await alumnos_conexiones[message_data.get("clientid")].send("reiniciar")

                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"Error en la conexión con el profesor: {e}")

            await asyncio.sleep(0.1)
    except websockets.exceptions.ConnectionClosedOK:
        print(f"Cliente desconectado. clientid: {clientid}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Error en la conexión: {e}")
    except Exception as e:
        print(f"Error en el servidor: {e}")
    finally:
        # Si el cliente desconectado es el profesor, lo elimina como cliente_profesor
        if cliente_ip == ip_profesor:
            cliente_profesor = None
            print("Cliente profesor desconectado.")
        elif clientid in alumnos_conexiones:
            # Elimina la conexión del alumno desconectado del diccionario
            del alumnos_conexiones[clientid]
            print(f"Alumno desconectado. clientid: {clientid}")
            informacion = {
                "clientid": clientid,
                "estado": "desconectado"
            }
            await cliente_profesor.send(json.dumps(informacion))

if __name__ == "__main__":
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(os.path.join(os.path.dirname(os.path.realpath(__file__)),"RavenIP_ServerWS.crt"), os.path.join(os.path.dirname(os.path.realpath(__file__)),"RavenIP_ServerWS.pem"))
    start_server = websockets.serve(servidor, "0.0.0.0", inicio, ssl=ssl_context, ping_interval=5, ping_timeout=2, max_size=1024*1024*56)
    servicios.append(inicio)
    servidores[inicio]="Principal"
    print(f"Servidor WebSocket VNC en ejecución en wss://0.0.0.0:{inicio}")
    puertos.append(inicio)
    try:
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("Servidor detenido por el usuario.")
    except Exception as e:
        print(f"Error general en el servidor: {e}")
    finally:
        asyncio.get_event_loop().close()
