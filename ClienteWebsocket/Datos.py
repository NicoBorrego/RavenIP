import time
import json
import os
from datetime import datetime, timedelta
import psutil
import speedtest

# Ruta del archivo JSON donde se guardarán los datos
ruta_json = os.path.join(os.path.dirname(os.path.realpath(__file__)),"datos.json")

def convertir(nbytes):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])

def eliminarRegistrosAntiguos(info):
    # hora actual
    ahora = datetime.now()
    # maximo de tiempo para guardar registros
    tiempo_maximo = timedelta(minutes=5)
    # Filtra los registros con menos de 5 minutos
    datos_nuevos = [registro for registro in info if (ahora - datetime.strptime(ahora.strftime("%Y-%m-%d") + " " + registro['Hora'], "%Y-%m-%d %H:%M:%S")) < tiempo_maximo]
    return {"data":datos_nuevos}

def obtenerDatos():
    global ruta_json
    # Obtener la hora actual
    tiempo = datetime.now().strftime("%H:%M:%S")
    
    
    # Recopilar información de CPU
    cpu = psutil.cpu_percent()
    
    # Recopilar información de memoria
    mem = psutil.virtual_memory()
    mem_percent = mem.percent
    
    # Recopilar información de disco
    disco = psutil.disk_usage('/')
    disco_percent = disco.percent
    
    # Realizar una prueba de velocidad de la conexión a Internet
    st = speedtest.Speedtest(secure=True)
    st.get_best_server()
    velocidad_descarga = st.download()
    velocidad_subida = st.upload()
    
    # Crear un diccionario con los datos y la hora de recopilación
    datos = {
        'Hora': tiempo,
        'CPU': cpu,
        'Memoria': mem_percent,
        'Disco': disco_percent,
        'Velocidad_Descarga': convertir(velocidad_descarga),
        'Velocidad_Subida': convertir(velocidad_subida)
    }
    print(datos)
    # Verificar si el archivo JSON ya existe
    if os.path.exists(ruta_json):
        # Si existe, cargar datos actuales
        with open(ruta_json, 'r') as archivo:
            datos_json = json.load(archivo)
            datos_antiguos = datos_json["data"]
    else:
        # Si no existe, crear una lista vacía de datos antiguos
        datos_antiguos = []
    # Agregar el nuevo diccionario a la lista de datos antiguos
    datos_antiguos.append(datos)
    
    
    # Guardar los datos en el archivo JSON
    with open(ruta_json, 'w') as archivo:
        json.dump(eliminarRegistrosAntiguos(datos_antiguos), archivo, indent=4)
    
    
# Función principal
def main():
    # Ejecutar infinitamente
    while True:
        obtenerDatos()
        # Esperar un intervalo de tiempo antes de recopilar datos nuevamente
        time.sleep(30)

if __name__ == "__main__":
    main()
