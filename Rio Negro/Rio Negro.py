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

REGEX_CATEGORIA = 'documentos ID (?P<categoria>\d+) \(\d+\)'

CARPETA_SALIDA = 'dataset/'

# Verifico que la carpeta de salida exista
if not os.path.exists(CARPETA_SALIDA):
    os.mkdir('dataset')

ARCHIVO_SALIDA_BOLETIN = CARPETA_SALIDA+"boletinRioNegro_{dia}-{mes}-{anio}.pdf"

# Objeto de nueva sesion del cliente http
s = requests.session()

# Headers customizados de acuerdo a las solicitudes HTTP necesarias
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br'
}

url_base = 'https://www.rionegro.gov.ar/'
# URL de solicitud para obtencion de boletines
url = 'https://www.rionegro.gov.ar/?catID=31.'

# URL Post documentos
url_post = 'https://www.rionegro.gov.ar/pages/ajax/getBoletinDataJson.php?catid={}'

# Boletiones
url_boletin = 'https://www.rionegro.gov.ar/download/boletin/{}'

print("EXTRAYENDO NUEVOS BOLETINES")

r = s.get(url, headers = headers)
soup = BeautifulSoup(r.content, 'lxml')

ediciones = soup.find(text=re.compile('Ediciones por año')).parent.parent.find_next_sibling()

url_anios = [url_base + a['href'] for a in ediciones.find_all('a')]

for url_anio in url_anios:
    print(url_anio)
    r = s.get(url_anio, headers = headers)
    try:
        id_categoria = re.search(REGEX_CATEGORIA, r.text).group('categoria')
        print(id_categoria)
    except:
        continue

    r = s.get(url_post.format(id_categoria))
    data = json.loads(r.text)

    for mes in data[0]['documentos']:

        for boletin in mes['elementos']:


            print(url_boletin.format(boletin['nombre']))
            date = dateparser.parse(boletin['fecha'])

            # Se da formato a dia y mes, completando con un cero delante en caso de contener un solo digito
            # Ejemplo: 3 -> 03
            dia = str(date.day).zfill(2)
            mes = str(date.month).zfill(2)

            # Verifico si el boletin de la fecha ya fue extraido previamente
            existe = os.path.exists(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia))
            if existe:
                continue

            r = s.get(url_boletin.format(boletin['nombre']), headers = headers)

            # Si tuvimos exito, obtuvimos el boletin y se procede a guardarlo en la ruta de salida
            with open(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia), 'wb') as f:
                f.write(r.content)
                        
            print("BOLETIN {} - GUARDADO".format(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia)))


print("FIN DE EXTRACCION")
os.system("pause")
