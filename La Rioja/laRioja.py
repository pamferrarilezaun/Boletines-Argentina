import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import os
from glob import glob
from tqdm import tqdm

CARPETA_SALIDA = 'dataset/'
# Verifico que la carpeta de salida exista
if not os.path.exists(CARPETA_SALIDA):
	os.mkdir('dataset')

ARCHIVO_SALIDA_BOLETIN = "dataset/boletinLaRioja{fecha}.pdf"

# Objeto de nueva sesion del cliente http
s = requests.session()

# Headers customizados de acuerdo a las solicitudes HTTP necesarias
headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
	'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
	'Accept-Encoding': 'gzip, deflate'
}

# URL de solicitud para obtencion de boletines
url = 'http://www.boletinoflarioja.com.ar/boletin.html'

print("EXTRAYENDO NUEVOS BOLETINES")

# Se obtiene el contenido de la pagina principal donde se encuentra el boletin del dia
r = s.get(url, headers = headers)
soup = BeautifulSoup(r.content, 'lxml')

# Se obtiene todas las etiquetas p y nos quedamos con el tiene el link del boletin del dia
pes = soup.find('div', attrs = {'id':'contenido_der'}).find_all('p')
for p in pes:
	try:
		# Se obtiene el link
		boletin_del_dia = p.find('a')['href']
		boletin_del_dia = 'http://www.boletinoflarioja.com.ar/' + boletin_del_dia
		# Se botiene la fecha
		fecha = p.find('a').text
		# Se conforma el nombre del archivo
		nombre_boletin = ARCHIVO_SALIDA_BOLETIN.format(fecha = fecha)
	except:
		continue

# Si ya encontro el archivo en la carpeta saltea la iteracion. Fue scrapeado ese documento.
if(not os.path.exists(nombre_boletin)):
	# Se obtiene el boletin del dia y se lo almacena en la carpeta correspondiente
	r = s.get(boletin_del_dia, headers = headers)
	with open(nombre_boletin, 'wb') as f:
		f.write(r.content)
		print("BOLETIN {} - GUARDADO", nombre_boletin)

# pagina donde se encuentran los boletines que no son el ultimo cargado
URL_BOLETINESCOMPLETOS = 'http://www.boletinoflarioja.com.ar/boletines_completos.php'
r = s.get(URL_BOLETINESCOMPLETOS, headers = headers)
soup = BeautifulSoup(r.content, 'lxml')

# Se obtiene los anios de los links desde el 1998 hasta la actualidad
anios = soup.find('div', attrs = {'id':'contenido_der'}).find_all('a')
# Se recorren todos los anios y se conforma el link para cada
for anio in anios:
	boletines_por_anio = 'http://www.boletinoflarioja.com.ar/boletines_completos.php' + anio['href']
	r = s.get(boletines_por_anio, headers = headers)
	soup = BeautifulSoup(r.content, 'lxml')

	# Dentro del link por cada anio se obtiene todos los links a los boletines
	link_anteriores = soup.find('table').find_all('tr')
	for link in link_anteriores:
		boletines_anteriores = 'http://www.boletinoflarioja.com.ar' + link.find('a')['href']
		fecha = link.find('a').text
		nombre_boletin = ARCHIVO_SALIDA_BOLETIN.format(fecha = fecha)
		# Si ya encontro el archivo en la carpeta saltea la iteracion. Fue scrapeado ese documento.
		if(not os.path.exists(nombre_boletin)):
			# Se obtiene el boletin y se almacena en la carpeta correspondiente
			r = s.get(boletines_anteriores, headers = headers)
			with open(nombre_boletin, 'wb') as f:
				f.write(r.content)
				print("BOLETIN {} - GUARDADO", nombre_boletin)


print("FIN DE EXTRACCION")
os.system("pause")

