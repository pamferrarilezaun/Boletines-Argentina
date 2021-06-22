import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import os
from glob import glob
from tqdm import tqdm
import dateparser

CARPETA_SALIDA = 'dataset/'
# Verifico que la carpeta de salida exista
if not os.path.exists(CARPETA_SALIDA):
	os.mkdir('dataset')

ARCHIVO_SALIDA_BOLETIN = "dataset/boletinSantaCruz_{fecha}_{nombre}.pdf"

# Objeto de nueva sesion del cliente http
s = requests.session()

# Headers customizados de acuerdo a las solicitudes HTTP necesarias
headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
	'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
	'Accept-Encoding': 'gzip, deflate, br'
}

# URL de solicitud para obtencion de boletines
url = 'https://www.santacruz.gob.ar/boletin-oficial/'

print("EXTRAYENDO NUEVOS BOLETINES")

# Se obtiene el contenido de la pagina principal donde se encuentra el boletin del dia.
# Esta provincia devuelve un error de respuesta del servidor, en ese caso, debemos volver a realizar la solicitud get() 
while True:
	try:
		r = s.get(url, headers = headers)
		soup = BeautifulSoup(r.content, 'lxml')
		break
	except:
		continue


headers_link={
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
	'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
	'Accept-Encoding': 'identyty'  # cuando tiene errores de respuesta se cambia por 'identyty' y en general no falla mas
}

#Se obtienen todos los anios donde existen boletines
anios = soup.find('div', attrs = {'class':'t3-module modulearbol'}).find_all('li')
for anio in anios:

	#Dentro de cada anio se buscan los meses que tienen boletines
	meses = anio.find_all('li')
	for mes in meses:
		link_del_mes = 'https://www.santacruz.gob.ar' + mes.find('a')['href']

		# Se obtiene el contenido donde se encuentran los boletines mes por mes dentro de un mismo anio.
		while True:
			try:
				r = s.get(link_del_mes, headers = headers)
				soup_boletin = BeautifulSoup(r.content, 'lxml')
				break
			except:
				continue

		boletines = soup_boletin.find_all('div', attrs={'class':'pd-filebox'})
		# dentro de un mismo mes se recorre para obtener todos los boletines y se conforma el link de descarga
		for boletin in boletines:
			link_boletin = boletin.find('a', attrs = {'class':'btn btn-success'})['href'].split('/../')[1]
			link_boletin = 'https://www.santacruz.gob.ar/' + link_boletin
			# print(link_boletin)

			#Se conforma el nombre unico del boletin. Esto va a servir para controlar si ese boletin existe o no.
			fecha = boletin.find('div', attrs = {'class':'pd-fl-m'}).text
			fecha = dateparser.parse(fecha)
			fecha = fecha.strftime("%d-%m-%Y")
			nombre = boletin.find('div', attrs = {'class':'pd-float'}).text
			nombre_boletin = ARCHIVO_SALIDA_BOLETIN.format(fecha = fecha, nombre = nombre)
			# print(nombre_boletin)

			# Si ya encontro el archivo en la carpeta dataset saltea la iteracion. Fue scrapeado ese boletin.
			if(not os.path.exists(nombre_boletin)):
				# Se obtiene el boletin y se almacena en la carpeta correspondiente
				r = s.get(link_boletin, headers = headers)
				with open(nombre_boletin, 'wb') as f:
					f.write(r.content)
					print("BOLETIN {} - GUARDADO", nombre_boletin)

print("FIN DE EXTRACCION")
os.system("pause")