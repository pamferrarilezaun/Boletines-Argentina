import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import os
from glob import glob
from tqdm import tqdm
import dateparser
import time

CARPETA_SALIDA = 'dataset/'
# Verifico que la carpeta de salida exista
if not os.path.exists(CARPETA_SALIDA):
    os.mkdir('dataset')

ARCHIVO_SALIDA_BOLETIN = "dataset/boletinChubut_{dia}-{mes}-{anio}.pdf"
ARCHIVO_SALIDA_BOLETIN_EXTRA = "dataset/boletinChubut_{dia}-{mes}-{anio}-anexo.pdf"

# Objeto de nueva sesion del cliente http
s = requests.session()

# Headers customizados de acuerdo a las solicitudes HTTP necesarias
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br'
}

# URL de solicitud para obtencion de boletines
url = 'http://boletin.chubut.gov.ar/?page={}'


print("EXTRAYENDO NUEVOS BOLETINES")

# Obtengo los boletines de la primer pagina (que son los mas actuales, estan ordenados de mas recientes a mas viejos)
r = s.get(url.format(1), headers = headers)
soup = BeautifulSoup(r.content, 'lxml')

# Obtengo la cantidad de paginas que presenta el listado
cantidad_paginas = soup.find('ul', attrs={'class':'pagination'}).find_all('li')[-2].text.strip()
cantidad_paginas = int(cantidad_paginas)

# Itero cada una de las paginas hasta llegar a la ultima, o hasta encontrar un boletin que ya fue scrapeado
existe = False
i = 1
while (i<=cantidad_paginas):
    if i != 1:
        r = s.get(url.format(i), headers = headers)
        soup = BeautifulSoup(r.content, 'lxml')        

    filas_boletines = soup.find('tbody').find_all('tr')[:]

    for fila_boletin in filas_boletines:
        tds = fila_boletin.find_all('td')
        date = dateparser.parse(tds[1].text.strip())

        # Se da formato a dia y mes, completando con un cero delante en caso de contener un solo digito
        # Ejemplo: 3 -> 03
        dia = str(date.day).zfill(2)
        mes = str(date.month).zfill(2)

        # Verifico si el boletin de la fecha ya fue extraido previamente
        existe = os.path.exists(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia))
        if existe:
            continue

        try:
            url_boletin = 'https://chaco.gov.ar' + tds[3].find('a')['href']
        except:
            url_boletin = None


        # Si tuve exito, guardo el boletin
        if url_boletin:
            r = s.get(url_boletin, headers = headers)

            anexo = 'ANEXO' in tds[3].text.strip()
            if anexo:
                with open(ARCHIVO_SALIDA_BOLETIN_EXTRA.format(anio=date.year,mes=mes,dia=dia), 'wb') as f:
                    f.write(r.content)
            else:
                with open(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia), 'wb') as f:
                    f.write(r.content)
            
            print("BOLETIN {} - GUARDADO".format(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia)))
    
    i+=1
    time.sleep(1)

print("FIN DE EXTRACCION")
os.system("pause")