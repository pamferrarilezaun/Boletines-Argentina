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

url_nro_boletin = 'https://apicake.mendoza.gov.ar/APIcake/Servicios/getBoletinAnterior'


date = datetime(2017,1,20)

today = datetime.now()
# today = datetime(2017,1,30)

def obtener_boletin(dia, mes, anio):

    date = datetime(anio,mes,dia)
    dia = str(date.day).zfill(2)
    mes = str(date.month).zfill(2)

    fecha = '{}/{}/{}'.format(dia, mes, date.year)

    # Se procede a la extraccion del boletin
    print("Boletin fecha: {}/{}/{}".format(dia, mes, date.year))

    # Solicitud para obtener nro de Boletin
    r = s.post(url_nro_boletin, headers = headers, data = {'fecha':fecha})
    if r.status_code != 200:
        print("Hubo un problema")
        return
    
    soup = BeautifulSoup(r.content, 'lxml')

    try:
        link_pdf = soup.find(text = re.compile('Edición Impresa')).parent['href']
    except:
        print("Hubo un problema")
        return        
    
    # Solicitud para obtener indice de lo publicado
    r = s.get(link_pdf, headers = headers)

    with open(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia), 'wb') as f:
        f.write(r.content)
                
    print("BOLETIN {} - GUARDADO".format(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia)))

if __name__ == '__main__':
    """
    Parser args
    """

    dia = 3
    mes = 10
    anio = 2019

    # Verifico si el boletin de la fecha ya fue extraido previamente
    existe = path.exists(ARCHIVO_SALIDA_BOLETIN.format(anio=anio,mes=mes,dia=dia))
    if existe:
        print("El boletin especificado ya fue descargado")
    else:
        obtener_boletin(3,10,2019)

