import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from os import path
import json
import time
from glob import glob
import os
import locale
import dateparser
from dateutil.relativedelta import relativedelta
import calendar

CARPETA_SALIDA = 'dataset/'

# Verifico que la carpeta de salida exista
if not os.path.exists(CARPETA_SALIDA):
    os.mkdir('dataset')

ARCHIVO_SALIDA_BOLETIN = CARPETA_SALIDA+"boletinNeuquen_{dia}-{mes}-{anio}.pdf"

# Objeto de nueva sesion del cliente http
s = requests.session()

# Headers customizados de acuerdo a las solicitudes HTTP necesarias
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br'
}

# URL de solicitud para obtencion de boletines
url = 'https://boficial.neuquen.gov.ar/?mes={}&nro='

# Fecha base a partir de la cual existen publicaciones
date = datetime(2001,1,1)

# Obtengo la fecha del ultimo boletin obtenido
for boletin in glob(CARPETA_SALIDA+'*.pdf'):
    date_candidata = datetime.strptime(boletin, 'dataset\\boletinNeuquen_%d-%m-%Y.pdf')
    if date_candidata > date:
        date = date_candidata

# Idioma "es-ES" (código para el español de España)
locale.setlocale(locale.LC_ALL, 'es-ES')

# Fecha actual
today = datetime.now()
ultimo_dia_mes_actual = calendar.monthrange(today.year, today.month)[1]
today = datetime(today.year, today.month, ultimo_dia_mes_actual)

print("EXTRAYENDO NUEVOS BOLETINES")
print("Fecha comienzo: {}".format(date.strftime('%d-%m-%Y')))

# Se itera a traves de todas las fechas, desde la fecha origen a la fecha actual
while date <= today:

    # Se procede a la extraccion del boletin

    # Primer paso: solicitud para obtener parametro de solicitud
    r  = s.get(url.format(date.strftime("%B %Y").title()), headers = headers)

    # Se parsea la respuesta HTML obtenida de la consula al servidor
    soup = BeautifulSoup(r.content, 'lxml')

    fechas_boletines = [div.find('h5').text.strip() for div in soup.find_all('div', attrs={'class':'cc-text'})]
    url_boletines = ['https://boficial.neuquen.gov.ar'+div.find('a')['href'] for div in soup.find_all('div', attrs={'class':'cc-text'})]

    for fecha_boletin, url_boletin in zip(fechas_boletines, url_boletines):
        date_boletin = dateparser.parse(fecha_boletin)

        # Se da formato a dia y mes, completando con un cero delante en caso de contener un solo digito
        # Ejemplo: 3 -> 03
        dia = str(date_boletin.day).zfill(2)
        mes = str(date_boletin.month).zfill(2)

        existe = os.path.exists(ARCHIVO_SALIDA_BOLETIN.format(anio=date_boletin.year,mes=mes,dia=dia))
        if existe:
            continue

        # Se realiza la solicitud para obtener el boletin
        r = s.get(url_boletin, headers = headers)



        # Si tuvimos exito, obtuvimos el boletin y se procede a guardarlo en la ruta de salida
        with open(ARCHIVO_SALIDA_BOLETIN.format(anio=date_boletin.year,mes=mes,dia=dia), 'wb') as f:
            f.write(r.content)
                    
        print("BOLETIN {} - GUARDADO".format(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia)))

    # Se continua con la siguiente iteracion.
    date = date + relativedelta(months=1)
    print(date)

print("FIN DE EXTRACCION")
os.system("pause")