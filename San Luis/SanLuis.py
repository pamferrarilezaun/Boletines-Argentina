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

ARCHIVO_SALIDA_BOLETIN = CARPETA_SALIDA+"boletinSanLuis_{nombre}_{dia}-{mes}-{anio}.doc"

# Objeto de nueva sesion del cliente http
s = requests.session()

# Datos del formulario a enviar
payload = {
	"javax.faces.partial.ajax": "true",
	"javax.faces.source": "form:dateSearchButton",
	"javax.faces.partial.execute": "@all",
	"javax.faces.partial.render": "form",
	"form:dateSearchButton": "form:dateSearchButton",
	"form": "form",
	"form:j_idt43_focus": "",
	"form:j_idt46_focus": "",
	"form:inputSearch": ""
}

# URL de solicitud para obtencion de boletines
url = 'http://www.boletinoficial.sanluis.gov.ar/boletin-oficial-webapp/public/index/index.jsf'
url_boletin = 'http://www.boletinoficial.sanluis.gov.ar/boletin-oficial-webapp/public/index/boletin.jsf'
url_archivo = 'http://www.boletinoficial.sanluis.gov.ar/boletin-oficial-webapp/public/index/categoriaList.jsf'

# Obtengo parametro para solicitud
r = s.get(url)
soup = BeautifulSoup(r.content, 'lxml')

viewstate= soup.find('input', attrs={'name':'javax.faces.ViewState'})['value']
payload['javax.faces.ViewState'] = viewstate

# Fecha base a partir de la cual existen publicaciones
date = datetime(2010,1,1)

# Obtengo la fecha del ultimo boletin obtenido
for boletin in glob(CARPETA_SALIDA+'*.pdf'):
    date_candidata = datetime.strptime(boletin, 'dataset\\boletinSanLuis_%d-%m-%Y.pdf')
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

    payload['form:j_idt43_input'] = date.strftime('%Y')
    payload['form:j_idt46_input'] = date.strftime('%B').title()

    # Primer paso: solicitud para obtener parametro de solicitud
    r  = s.post(url, data = payload)

    # Se parsea la respuesta HTML
    soup = BeautifulSoup(r.content, 'lxml')

    boletines = soup.find('div', attrs={'class':'row boletin-list'}).find_all('tr')

    # Se itera sobre el listado de boletines del mes
    for boletin in boletines:
        # Se obtienen los parametros necesarios para acceder
        # a las secciones del boletin
        form_param = boletin.find('a')['id']
        payload_boletin = payload.copy()
        payload_boletin[form_param] = form_param

        # Se obtiene la fecha del boletin
        date_boletin = boletin.find('a').text.strip().split('(')[1].split(')')[0]
        # date_boletin = datetime.strptime('%d/%m/%Y', date_boletin)
        date_boletin = dateparser.parse(date_boletin, languages=['es'])

        dia = str(date_boletin.day).zfill(2)
        mes = str(date_boletin.month).zfill(2)
        anio = date_boletin.year

        # Se realizan las dos consultas necesarias al servidor para obtener
        # las secciones del boletin
        r = s.post(url, data = payload_boletin)
        r = s.get(url_boletin)
        soup = BeautifulSoup(r.content, 'lxml')

        # Se obtienen los parametros necesarios para obtener la seccion legislativa
        payload_legislativa = {
            "form": "form",
            "form:legislativeSearchButton": "form:legislativeSearchButton"
        }

        viewstate= soup.find('input', attrs={'name':'javax.faces.ViewState'})['value']
        payload_legislativa['javax.faces.ViewState'] = viewstate

        # Se obtiene la seccion legislativa
        r = s.post(url_boletin, data = payload_legislativa)
        soup = BeautifulSoup(r.content, 'lxml')

        # Se obtiene parametro para descarga de archivos de la seccion legislativa
        viewstate= soup.find('input', attrs={'name':'javax.faces.ViewState'})['value']

        # Se obtiene el listado de archivos de la seccion legislativa
        trs = soup.find('div', attrs={'class':'row boletin-list'}).find_all('tr')

        # Se iteran los archivos de la seccion legislativa
        for tr in trs:
            # Se obtienen parametros de solicitud de archivo
            payload_archivo = {
                "form": "form"
            }
            payload_archivo['javax.faces.ViewState'] = viewstate

            nombre = tr.find('label').text.strip()
            form_param = tr.find('a')['id']
            payload_archivo[form_param] = form_param

            
            # Verifico la existencia
            nombre_archivo = ARCHIVO_SALIDA_BOLETIN.format(nombre=nombre, dia=dia,mes=mes, anio=anio)

            existe = os.path.exists(nombre_archivo)

            if existe:
                continue
            
            # Se realiza la solicitud del archivo
            r = s.post(url_archivo, data = payload_archivo)

            # Se guarda el archivo final
            with open(nombre_archivo, 'wb') as f:
                f.write(r.content)
    # Se continua con la siguiente iteracion.
    date = date + relativedelta(months=1)

print("FIN DE EXTRACCION")
os.system("pause")
