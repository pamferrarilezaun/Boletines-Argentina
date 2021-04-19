import requests
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
import re
from os import path
import json

ARCHIVO_SALIDA_BOLETIN = "dataset_pdf/boletin_{anio}_{mes}_{dia}.pdf"

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
    if r.status_code != 200:
        date = date + timedelta(days=1)
        continue
    
    
    soup = BeautifulSoup(r.content, 'lxml')

    try:
        nro_boletin = soup.find(text = re.compile('Boletín N°')).split('N°')[1].strip()
    except:
        date = date + timedelta(days=1)
        continue        
    
    link_pdf = soup.find(text = re.compile('Edición Impresa')).parent['href']
    # Solicitud para obtener indice de lo publicado
    r = s.get(link_pdf, headers = headers)

    with open(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia), 'wb') as f:
        f.write(r.content)
                
    print("SE GUARDO EL BOLETIN")
    date = date + timedelta(days=1)