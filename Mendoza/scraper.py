import requests
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
import re
from os import path
import json
import time

ARCHIVO_SALIDA_BOLETIN = "dataset/boletin_{anio}_{mes}_{dia}.json"

s = requests.session()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
    'Accept': '*/*',
    'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Referer': 'https://boletinoficial.mendoza.gov.ar/'
}

payload_norma = {
	"numero": "",
	"tipo_busqueda": "NORMA",
	"tipo_boletin": "2",
	"edicto_id": "",
	"norma_edicto_id": "111",
	"fecha_desde": "2017-01-20",
	"fecha_hasta": "2017-01-20"
}

REGEX_NORMA = "getBoletinDetalleNorma\('\d+-\d+-\d+','(?P<tipo_boletin>\d+)','(?P<norma_edicto_id>\d+)'\);"
# REGEX_ARTICULO = "Artículo (?P<nro_articulo>\d+)[°|º]\.?-? ?(?P<contenido_articulo>.*)"

url_nro_boletin = 'https://apicake.mendoza.gov.ar/APIcake/Servicios/getBoletinAnterior'
url_indice_boletin = 'https://apicake.mendoza.gov.ar/APIcake/Servicios/getBoletinIndice'
url_detalle_boletin = 'https://apicake.mendoza.gov.ar/APIcake/Servicios/getBoletinDetalle'


date = datetime(2017,1,20)

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
    
    fecha = '{}/{}/{}'.format(dia, mes, date.year)
    fecha_payload = '{}-{}-{}'.format(date.year, mes, dia)

    # Se procede a la extraccion del boletin
    print("Boletin del dia: {}/{}/{}".format(dia, mes, date.year))

    # Solicitud para obtener nro de Boletin
    r = s.post(url_nro_boletin, headers = headers, data = {'fecha':fecha})
    # print(r.status_code)
    if r.status_code != 200:
        date = date + timedelta(days=1)
        continue
    
    
    soup = BeautifulSoup(r.content, 'lxml')

    try:
        nro_boletin = soup.find(text = re.compile('Boletín N°')).split('N°')[1].strip()
    except:
        date = date + timedelta(days=1)
        continue        
    
    print(nro_boletin)
    boletin = {'fecha': fecha, 'nro': nro_boletin}
    # Solicitud para obtener indice de lo publicado
    r = s.post(url_indice_boletin, headers = headers, data = {'fecha': fecha_payload, 'numero': nro_boletin})
    soup = BeautifulSoup(r.content, 'lxml')

    seccion_general = soup.find('div', attrs={'id':'collapseGeneral'})

    # En caso de que no haya publicacion ese dia
    if not seccion_general:
        date = date + timedelta(days=1)
        continue

    secciones = seccion_general.find_all('div', attrs={'class':'panel-default'})

    for seccion in secciones:
        nombre_seccion = seccion.find('h4').text.strip().lower()

        normas = seccion.find('div', attrs={'class':'panel-body'}).find_all('div')

        boletin[nombre_seccion] = []

        for norma in normas:
            norma_dict = {}

            get_data = norma.find('a')['onclick']
            match = re.search(REGEX_NORMA, get_data)

            payload_norma['tipo_boletin'] = match.group('tipo_boletin')
            payload_norma['norma_edicto_id'] = match.group('norma_edicto_id')
            payload_norma['fecha_desde'] = fecha_payload
            payload_norma['fecha_hasta'] = fecha_payload

            r = s.post(url_detalle_boletin, headers = headers, data = payload_norma)
            time.sleep(1)
            soup = BeautifulSoup(r.content, 'lxml')

            norma_dict['emisor'] = soup.find(text = re.compile('Origen:')).parent.parent.text.replace('Origen:','').strip()
            norma_dict['tema'] = soup.find(text = re.compile('Tema:')).parent.parent.text.replace('Tema:','').strip()
            norma_dict['fecha'] = soup.find(text = re.compile('Fecha:')).parent.parent.text.replace('Fecha:','').strip()
            
            # print(norma_dict['emisor'])

            lineas = soup.find_all('p')

            # norma_dict['articulos'] = {}

            norma_dict['texto'] = '\n'.join([linea.text.strip() for linea in lineas])

            # for linea in lineas:
            #     match = re.match(REGEX_ARTICULO, linea.text)
            #     if match:
            #         norma_dict['articulos'][match.group('nro_articulo')] = match.group('contenido_articulo')
            
            boletin[nombre_seccion].append(norma_dict)

    with open(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia), 'w', encoding='utf8') as f:
        json.dump(boletin, f)
                

    date = date + timedelta(days=1)