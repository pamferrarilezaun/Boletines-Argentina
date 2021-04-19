import requests
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
import re
from os import path

ARCHIVO_SALIDA_BOLETIN = "dataset/boletin_{anio}_{mes}_{dia}.pdf"
ARCHIVO_SALIDA_BOLETIN_EXTRA = "dataset/boletin_extraordinaria_{anio}_{mes}_{dia}.pdf"

s = requests.session()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br'
}

url = 'https://boletinoficial.cba.gov.ar/{anio}/{mes}/{dia}/'

date = datetime(2006,2,28)

today = datetime.now()

while date <= today:

    dia = str(date.day).zfill(2)
    mes = str(date.month).zfill(2)

    # Se procede a la extraccion del boletin
    print("Boletin del dia: {}/{}/{}".format(dia, mes, date.year))

    r = s.get(url.format(anio=date.year,mes=mes,dia=dia), headers = headers)

    if r.status_code != 200:
        date = date + timedelta(days=1)
        continue
    
    soup = BeautifulSoup(r.content, 'lxml')

    # Edicion ordinaria
    
    # Verifico si el boletin de la fecha ya fue extraido previamente
    existe_ordinaria = path.exists(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia))
    if not existe_ordinaria:
        try:
            anchor_legislacion = soup.find(text = re.compile('Legislación – Normativas')).parent.parent
        except:
            anchor_legislacion = None

        if anchor_legislacion:
            url_pdf_legislacion = anchor_legislacion['href']
            r = s.get(url_pdf_legislacion, headers = headers)

            with open(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia), 'wb') as f:
                f.write(r.content)

    # Edicion extraordinaria

    # Verifico si el boletin de la fecha ya fue extraido previamente
    existe_extra = path.exists(ARCHIVO_SALIDA_BOLETIN_EXTRA.format(anio=date.year,mes=mes,dia=dia))
    if not existe_extra:
        try:
            anchor_legislacion_extra = soup.find(text = re.compile('EDICIÓN EXTRAORDINARIA')).parent.parent
        except:
            anchor_legislacion_extra = None

        if anchor_legislacion_extra:
            url_pdf_legislacion = anchor_legislacion_extra['href']
            r = s.get(url_pdf_legislacion, headers = headers)

            with open(ARCHIVO_SALIDA_BOLETIN_EXTRA.format(anio=date.year,mes=mes,dia=dia), 'wb') as f:
                f.write(r.content)

    date = date + timedelta(days=1)