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

ARCHIVO_SALIDA_BOLETIN = CARPETA_SALIDA+"boletinMisiones_{dia}-{mes}-{anio}.pdf"

# Objeto de nueva sesion del cliente http
s = requests.session()

# Headers customizados de acuerdo a las solicitudes HTTP necesarias
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br'
}

# Estructura base de los datos a enviar en las solicitudes HTTP
if not os.path.exists('payload.json'):
    print("Hubo un problema: no existe el archivo payload.json")
    os.system("pause")
    exit()

with open('payload.json', 'r') as f:
    payload = json.load(f)

# URL principal
url_principal = 'https://www.boletindigital.misiones.gov.ar/'
# URL de solicitud para obtencion de boletines
url = 'https://www.boletindigital.misiones.gov.ar/faces/boletinWEB.xhtml'

# Fecha base a partir de la cual existen publicaciones
date = datetime(2001,3,9)

# Obtengo la fecha del ultimo boletin obtenido
for boletin in glob(CARPETA_SALIDA+'*.pdf'):
    date_candidata = datetime.strptime(boletin, 'dataset\\boletinMisiones_%d-%m-%Y.pdf')
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

    # Se procede a la extraccion del boletin

    # Primer paso: solicitud para obtener parametro de solicitud
    r  = s.get(url_principal, headers = headers)
    soup = BeautifulSoup(r.content, 'lxml')

    payload['javax.faces.ViewState'] = soup.find('input', attrs={'name':'javax.faces.ViewState'})['value']

    # Se intenta obtenerlo el boletin con los parametros de busqueda correspondientes a la fecha requerida
    payload['formEventoWeb:fechaDesde_input'] = '{}/{}/{}'.format(dia, mes, date.year)
    payload['formEventoWeb:fechaHasta_input'] = '{}/{}/{}'.format(dia, mes, date.year)

    r = s.post(url, headers = headers, data = payload)

    
    # Se parsea la respuesta HTML obtenida de la consula al servidor
    soup = BeautifulSoup(r.content, 'lxml')

    # print(soup.find('div', attrs={'id':'content'}).find('div', attrs={'class':'container'}))

    # Si el servidor arroja una respuesta no exitosa, avanzamos al dia siguiente
    # Respuestas no exitosas indican, en general, la no existencia del boletin en el dia requerido
    # Para ello, buscamos la presencia del texto descargar
    texto_descargar = soup.find(text=re.compile('DESCARGAR'))
    if not texto_descargar:
        date = date + timedelta(days=1)
        continue
    
    url_boletin = 'https://www.boletindigital.misiones.gov.ar' + texto_descargar.parent['href']


    # Se realiza la solicitud para obtener el boletin
    r = s.get(url_boletin, headers = headers)

    # Si tuvimos exito, obtuvimos el boletin y se procede a guardarlo en la ruta de salida
    with open(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia), 'wb') as f:
        f.write(r.content)
                
    print("BOLETIN {} - GUARDADO".format(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia)))

    # Se continua con la siguiente iteracion.
    date = date + timedelta(days=1)

print("FIN DE EXTRACCION")
os.system("pause")