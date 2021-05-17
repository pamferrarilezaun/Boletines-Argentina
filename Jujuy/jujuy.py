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

CARPETA_SALIDA = 'dataset/'

# Verifico que la carpeta de salida exista
if not os.path.exists(CARPETA_SALIDA):
    os.mkdir('dataset')

ARCHIVO_SALIDA_BOLETIN = CARPETA_SALIDA+"boletinJujuy_{dia}-{mes}-{anio}.pdf"
ARCHIVO_SALIDA_BOLETIN_ANEXO = CARPETA_SALIDA+"anexoBoletinJujuy_{dia}-{mes}-{anio}.pdf"

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
url = 'http://boletinoficial.jujuy.gob.ar/?page_id=2017&month={}&yr={}'

# Fecha actual
today = datetime.now()

# Fecha de inicio del año en curso
date = datetime(today.year,1,1)

# Obtengo la fecha del ultimo boletin obtenido
for boletin in glob(CARPETA_SALIDA+'*.pdf'):
    date_candidata = datetime.strptime(boletin, 'dataset\\boletinJujuy_%d-%m-%Y.pdf')
    if date_candidata > date:
        date = date_candidata

print("EXTRAYENDO NUEVOS BOLETINES")
print("Fecha comienzo: {}".format(date.strftime('%d-%m-%Y')))

# Se itera a traves de todas las fechas, desde la fecha origen a la fecha actual
while date.month <= today.month:

    # Se procede a la extraccion del boletin
    mes = date.strftime('%b').lower()

    print(url.format(mes, date.year))

    # Primer paso: solicitud para obtener boletines del mes
    r  = s.get(url.format(mes, date.year), headers = headers)

    # Se parsea la respuesta HTML
    soup = BeautifulSoup(r.content, 'lxml')

    
    links = soup.find_all('span', attrs={'class':'calnk-link'})

    for link in links:
        url_boletin = link.find('a')['href']
        
        # Se realiza la solicitud para obtener el boletin
        r = s.get(url_boletin, headers = headers)

        dia = link.find_parent('td').find('span', attrs={'class':'day-number'}).text.strip()
        date_boletin = datetime(date.year, date.month, int(dia))

        # Se da formato a dia y mes, completando con un cero delante en caso de contener un solo digito
        # Ejemplo: 3 -> 03
        dia = str(date_boletin.day).zfill(2)
        mes = str(date_boletin.month).zfill(2)

        if 'anexo' in link.text.lower():
            # Si tuvimos exito, obtuvimos el boletin y se procede a guardarlo en la ruta de salida
            with open(ARCHIVO_SALIDA_BOLETIN_ANEXO.format(anio=date_boletin.year,mes=mes,dia=dia), 'wb') as f:
                f.write(r.content)
                        
            print("Anexo {} - GUARDADO".format(ARCHIVO_SALIDA_BOLETIN_ANEXO.format(anio=date.year,mes=mes,dia=dia)))
        else:
            # Si tuvimos exito, obtuvimos el boletin y se procede a guardarlo en la ruta de salida
            with open(ARCHIVO_SALIDA_BOLETIN.format(anio=date_boletin.year,mes=mes,dia=dia), 'wb') as f:
                f.write(r.content)
                        
            print("BOLETIN {} - GUARDADO".format(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia)))

    # Se continua con la siguiente iteracion.
    date = date + relativedelta(months=1)

print("FIN DE EXTRACCION")
os.system("pause")
