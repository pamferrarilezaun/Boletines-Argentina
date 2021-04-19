import requests
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
import re
from os import path
import dateparser

requests.packages.urllib3.disable_warnings()

ARCHIVO_SALIDA_BOLETIN = "dataset/boletin_%Y_%m_%d.pdf"
REGEX_BOLETIN = 'B.*? (?P<fecha_boletin>\d+-\d+-\d+)'

s = requests.session()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br'
}

base_url = 'https://boletinoficial.corrientes.gob.ar'
urls = ['https://boletinoficial.corrientes.gob.ar/home/boletines-del-mes/categorias?page={}',
        'https://boletinoficial.corrientes.gob.ar/home/boletines-mes-pasado/categorias?page={}',
        'https://boletinoficial.corrientes.gob.ar/home/boletines-meses-anteriores/categorias?page={}']

# urls = ['https://boletinoficial.corrientes.gob.ar/home/boletines-mes-pasado/categorias?page={}']

def iterar_adjuntos(soup):
    """
    Se itera sobre los archivos adjuntos para obtener todos los boletines oficiales de la publicacion
    
    Se recibe un objeto BeautifulSoup que contiene los N archivos disponibles en la publicacion
    """

    panel_derecho = soup.find(text = re.compile('Archivos adjuntos')).parent.parent

    urls_boletines = [base_url+item.parent['href'] for item in panel_derecho.find_all(text = re.compile(REGEX_BOLETIN))]
    fechas_boletines = [item.strip() for item in panel_derecho.find_all(text = re.compile(REGEX_BOLETIN))]

    for url_boletin, fecha_boletin in zip(urls_boletines, fechas_boletines):
        fecha_boletin = re.search(REGEX_BOLETIN,fecha_boletin).group('fecha_boletin')
        date = dateparser.parse(fecha_boletin)
        nombre_salida = date.strftime(ARCHIVO_SALIDA_BOLETIN)

        # Verifico si el boletin de la fecha ya fue extraido previamente
        existe_archivo = path.exists(nombre_salida)
        
        if not existe_archivo:
            descargar_boletin(url_boletin, nombre_salida)

def descargar_boletin(url, nombre):
    """
    Descarga y guarda el boletin a partir de la URL del mismo
    """
    r = s.get(url, headers = headers, verify = False)
    with open(nombre, 'wb') as f:
        f.write(r.content)
    
    print("Se descargo el boletin:", nombre)


def obtener_boletines(url):
    r = s.get(url.format(1), headers = headers, verify = False)
    soup = BeautifulSoup(r.content, 'lxml')


    # Determinamos si estamos dentro de una publicacion
    if soup.find(text = re.compile('Archivos adjuntos')):
        iterar_adjuntos(soup)
    # De otro modo, iteramos sobre cada publicacion en sus respectivas paginas
    else:
        if soup.find(text = re.compile('Último »')):
            total_paginas = int(soup.find(text = re.compile('Último »')).parent['href'][-1])
        else:
            total_paginas = 1
        
        # Iteracion sobre las N paginas de publicaciones disponibles en el portal
        for i in range(1,total_paginas+1):
            if i != 1:
                r = s.get(url.format(i), headers= headers, verify = False)
                soup = BeautifulSoup(r.content, 'lxml')
            
            # Obtencion de cada publicacion
            lis = soup.find('ul', attrs={'class':'media-list news-list'}).find_all('li')

            # Iteracion sobre cada una de las publicaciones
            for li in lis:
                url_boletines = li.find('a')['href']
                r = s.get(base_url+url_boletines, headers = headers, verify = False)
                soup = BeautifulSoup(r.content, 'lxml')

                if soup.find(text = re.compile('Archivos adjuntos')):
                    # Iteramos sobre cada uno de los archivos adjuntos de la publicacion
                    iterar_adjuntos(soup)



if __name__ == '__main__':

    for url in urls:
        print(url)
        obtener_boletines(url)