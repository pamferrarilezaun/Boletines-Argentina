import requests
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
import re
from os import path
import json
import time

ARCHIVO_SALIDA_BOLETIN = "dataset/boletin_{anio}_{mes}_{dia}.pdf"

s = requests.session()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
    'Accept': '*/*',
    'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Referer': 'https://boletinoficial.mendoza.gov.ar/'
}

payload = {"codigo": ""}



url_buscador = 'http://www.digituc.gob.ar:8000/boletin/'
url_pdf = 'http://www.digituc.gob.ar:8000/boletin/'



date = datetime(2009,1,2)

today = datetime.now()
# today = datetime(2017,1,30)

while date <= today:

    dia = str(date.day).zfill(2)
    mes = str(date.month).zfill(2)

    # Verifico si el boletin de la fecha ya fue extraido previamente
    existe = path.exists(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia))
    if existe:
        date = date + timedelta(days=1)
        continue

    # Se procede a la extraccion del boletin
    print("Boletin del dia: {}/{}/{}".format(dia, mes, date.year))

    # Solicitud para obtener nro de Boletin
    while True:
        try:
            r = s.get(url_buscador, headers = headers, timeout=5)
            break
        except:
            print("Problema")
            time.sleep(5)
            continue
    # print(r.status_code)
    if r.status_code != 200:
        date = date + timedelta(days=1)
        continue
    
    
    soup = BeautifulSoup(r.content, 'lxml')

    try:
        middleware_token = soup.find('input', attrs={'name':'csrfmiddlewaretoken'})['value']
    except:
        date = date + timedelta(days=1)
        continue        
    
    payload['csrfmiddlewaretoken'] = middleware_token
    payload['fecha_day'] = date.day
    payload['fecha_month'] = date.month
    payload['fecha_year'] = date.year
    # Solicitud para obtener indice de lo publicado
    r = s.post(url_pdf, headers = headers, data = payload)
    
    try:
        soup = BeautifulSoup(r.content, 'lxml')
        if soup.find(text = re.compile('no fue cargado')):
            date = date + timedelta(days=1)
            continue
    except:
        pass

    with open(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia), 'wb') as f:
        f.write(r.content)
                
    print("BOLETIN {} - GUARDADO".format(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia)))
    date = date + timedelta(days=1)