import requests
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
import re
from os import path
import dateparser
import os

# Desabilitamos warnings que arroja la libraria requests
requests.packages.urllib3.disable_warnings()


CARPETA_SALIDA = 'dataset/'

# Verifico que la carpeta de salida exista
if not os.path.exists(CARPETA_SALIDA):
    os.mkdir('dataset')

ARCHIVO_SALIDA_BOLETIN = CARPETA_SALIDA+"boletinCorrientes_{dia}-{mes}-{anio}.pdf"

# Expresion regular para obtener enlaces y fecha de boletin a extraer a partir del listado de cada publicacion
REGEX_BOLETIN = 'B.*? (?P<fecha_boletin>\d+-\d+-\d+)'

# Objeto de nueva sesion del cliente http
s = requests.session()

# Headers customizados de acuerdo a las solicitudes HTTP necesarias
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br'
}

# URL base para la obtencion de los boletines
base_url = 'https://boletinoficial.corrientes.gob.ar'

# Lista de URLS donde existen publicaciones de boletines, a saber: 
# - Boletines del mes
# - Boletines del mes pasado
# - Boletines de mese anteriores
urls = ['https://boletinoficial.corrientes.gob.ar/home/boletines-del-mes/categorias?page={}',
        'https://boletinoficial.corrientes.gob.ar/home/boletines-mes-pasado/categorias?page={}',
        'https://boletinoficial.corrientes.gob.ar/home/boletines-meses-anteriores/categorias?page={}']

def iterar_adjuntos(soup):
    """
    Funcion para iterar sobre los archivos adjuntos y obtener todos los boletines oficiales de la publicacion
    
    Entrada: objeto BeautifulSoup que contiene los N archivos disponibles en la publicacion

    Salida: archivos pdf correspondientes a los boletines oficiales.
    """

    # Obtenemos los archivos adjuntos presentes en el panel derecho de cada publicacion
    panel_derecho = soup.find(text = re.compile('Archivos adjuntos')).parent.parent

    # Obtenemos fechas y numeros de boletines, a partir del uso de las REGEX previamente definidas
    urls_boletines = [base_url+item.parent['href'] for item in panel_derecho.find_all(text = re.compile(REGEX_BOLETIN))]
    fechas_boletines = [item.strip() for item in panel_derecho.find_all(text = re.compile(REGEX_BOLETIN))]

    # Iteramos sobre los boletines encontrados en los archivos adjuntos
    for url_boletin, fecha_boletin in zip(urls_boletines, fechas_boletines):
        # Se obtiene la fecha del boletin
        fecha_boletin = re.search(REGEX_BOLETIN,fecha_boletin).group('fecha_boletin')
        date = dateparser.parse(fecha_boletin)

        # Se da formato a dia y mes, completando con un cero delante en caso de contener un solo digito
        # Ejemplo: 3 -> 03
        dia = str(date.day).zfill(2)
        mes = str(date.month).zfill(2)

        # Se genera el archivo de salida
        nombre_salida = ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia)

        # Verifico si el boletin de la fecha ya fue extraido previamente
        existe_archivo = path.exists(nombre_salida)
        
        if not existe_archivo:
            descargar_boletin(url_boletin, nombre_salida)

def descargar_boletin(url, nombre):
    """
    Descarga y guarda el boletin a partir de la URL del mismo.

    Entrada: url del pdf del boletin, nombre de salida
    Salida: archivo pdf del boletin
    """
    r = s.get(url, headers = headers, verify = False)
    with open(nombre, 'wb') as f:
        f.write(r.content)
    
    print("Se descargo el boletin:", nombre)


def obtener_boletines(url):
    """
    Funcion para iterar sobre las paginas de publicaciones que contienen boletines
    
    Entrada: url de seccion de publicaciones (boletines del mes, boletines del mes anterior o boletines de meses anteriores)

    Salida: -
    """

    r = s.get(url.format(1), headers = headers, verify = False)
    soup = BeautifulSoup(r.content, 'lxml')


    # Determinamos si estamos dentro de una publicacion
    if soup.find(text = re.compile('Archivos adjuntos')):
        iterar_adjuntos(soup)
    # De otro modo, iteramos sobre cada publicacion en sus respectivas paginas
    else:
        # Comprobamos si existen multiples paginas de publicaciones
        # De esta forma obtenemos la cantidad de paginas sobre las cuales iterar
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
    """
    Funcion main, itera las URL de cada seccion e invoca la funcion obtener boletines.
    """

    print("EXTRAYENDO NUEVOS BOLETINES")
    for url in urls:
        obtener_boletines(url)

    print("FIN DE EXTRACCION")
    os.system("pause")