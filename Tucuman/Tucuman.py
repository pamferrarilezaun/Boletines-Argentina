import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from os import path
import json
import time
from glob import glob
import os

CARPETA_SALIDA = 'dataset/'

# Verifico que la carpeta de salida exista
if not os.path.exists(CARPETA_SALIDA):
    os.mkdir('dataset')

ARCHIVO_SALIDA_BOLETIN = CARPETA_SALIDA+"boletinTucuman_{dia}-{mes}-{anio}.pdf"

# Objeto de nueva sesion del cliente http
s = requests.session()

# Headers customizados de acuerdo a las solicitudes HTTP necesarias
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
    'Accept': '*/*',
    'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
}

# Estructura base de los datos a enviar en las solicitudes HTTP
payload = {"codigo": ""}

# URL de solicitud para obtencion de boletines
url = 'http://www.digituc.gob.ar:8000/boletin/'

# Fecha base a partir de la cual existen publicaciones
date = datetime(2009,1,2)

# Obtengo la fecha del ultimo boletin obtenido
for boletin in glob(CARPETA_SALIDA+'*.pdf'):
    date_candidata = datetime.strptime(boletin, 'dataset\\boletinTucuman_%d-%m-%Y.pdf')
    if date_candidata > date:
        date = date_candidata

# Fecha actual
today = datetime.now()

print("EXTRAYENDO NUEVOS BOLETINES")
print("Fecha comienzo: {}".format(date.strftime('%d-%m-%Y')))

# Se itera a traves de todas las fechas, desde la fecha origen a la fecha actual
while date <= today:

    # Se da formato a dia y mes, completando con un cero delante en caso de contener un solo digito
    # Ejemplo: 3 -> 03
    dia = str(date.day).zfill(2)
    mes = str(date.month).zfill(2)

    # Verifico si el boletin de la fecha ya fue extraido previamente
    # En tal caso, paso al siguiente dia
    existe = path.exists(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia))
    if existe:
        date = date + timedelta(days=1)
        continue

    # Se procede a la extraccion del boletin
    #print("Boletin del dia: {}/{}/{}".format(dia, mes, date.year))

    # Primer paso: solicitud para obtener nro de Boletin
    # Se intenta obtenerlo hasta que el servidor arroja respuesta
    while True:
        try:
            r = s.get(url, headers = headers, timeout=5)
            break
        except:
            #print("Problema")
            time.sleep(5)
            continue
    
    # Si el servidor arroja una respuesta no exitosa, avanzamos al dia siguiente
    # Respuestas no exitosas indican, en general, la no existencia del boletin en el dia requerido
    if r.status_code != 200:
        date = date + timedelta(days=1)
        continue
    
    # Se parsea la respuesta HTML obtenida de la consula al servidor
    soup = BeautifulSoup(r.content, 'lxml')

    # Intentamos obtener el token necesario para la posterior obtencion del boletin
    # En caso de haber un problema, procedemos al siguiente dia.
    # Nuevamente, los problemas en este punto indican en general la no existencia del boletin.
    try:
        middleware_token = soup.find('input', attrs={'name':'csrfmiddlewaretoken'})['value']
    except:
        date = date + timedelta(days=1)
        continue        
    
    # Segundo paso: si tuvimos exito en el paso anterior, definimos la carga que enviaremos en la proxima solicitud
    # Aqui obtendremos efectivamente el boletin requerido.
    payload['csrfmiddlewaretoken'] = middleware_token
    payload['fecha_day'] = date.day
    payload['fecha_month'] = date.month
    payload['fecha_year'] = date.year

    # Se realiza la solicitud para obtener el boletin
    r = s.post(url, headers = headers, data = payload)
    
    # Verificamos si el boletin fue efectivamente cargado, caso contrario procedemos con el siguiente dia
    try:
        soup = BeautifulSoup(r.content, 'lxml')
        if soup.find(text = re.compile('no fue cargado')):
            date = date + timedelta(days=1)
            continue
    except:
        pass

    # Si tuvimos exito, obtuvimos el boletin y se procede a guardarlo en la ruta de salida
    with open(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia), 'wb') as f:
        f.write(r.content)
                
    print("BOLETIN {} - GUARDADO".format(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia)))

    # Se continua con la siguiente iteracion.
    date = date + timedelta(days=1)

print("FIN DE EXTRACCION")
os.system("pause")