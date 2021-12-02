import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import os
from glob import glob
from tqdm import tqdm
import dateparser
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CARPETA_SALIDA = 'dataset/'
# Verifico que la carpeta de salida exista
if not os.path.exists(CARPETA_SALIDA):
	os.mkdir('dataset')

ARCHIVO_SALIDA_BOLETIN = "dataset/boletinCatamarca_{numero_boletin}_{fecha}.pdf"

# Objeto de nueva sesion del cliente http
s = requests.session()

# Headers customizados de acuerdo a las solicitudes HTTP necesarias
headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
	'Accept': 'application/vnd.api+json',
	'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
	'Accept-Encoding': 'gzip, deflate, br'
}

# URL de solicitud para obtencion de boletines
url = 'https://portal.catamarca.gob.ar/backend/api/v1/boletin_oficial/?include=instrumento,organismos&ordering=-fecha&page[number]={}&page_size=200&numero=&instrumento=&fecha='

print("EXTRAYENDO NUEVOS BOLETINES")

#Solicitusd get
r = s.get(url.format(1), headers = headers, verify = False)
data = r.json()

#proximo link
next = data['links']['next']
# el i corresponde al numero de pagina
i = 1
# da vuelta en el bucle hasta que no haya un link de siguiente
while(next):
	# si no corresponde a la primer pagina obtiene la pagina siguiente
	if(i!=1):
		r = s.get(url.format(i), headers = headers, verify = False)
		data = r.json() # en este caso es una solicitud json
		next = data['links']['next']

	# obtiene el numero de boletin y link de descarga del boletin
	for boletin in data['data']:
		numero_boletin = boletin['id']
		link_boletin = boletin['attributes']['archivo']
		# si no encuentra el link del boletin saltea la iteracion 
		if not link_boletin:
			continue
		# obtiene la fecha y la parsea para poder agregarla al nombre del boletin
		fecha = boletin['attributes']['fecha']
		fecha = dateparser.parse(fecha)
		fecha = fecha.strftime("%d-%m-%Y")
		nombre_boletin = ARCHIVO_SALIDA_BOLETIN.format(numero_boletin=numero_boletin,fecha = fecha)

		# Si ya encontro el archivo en la carpeta saltea la iteracion. Fue scrapeado ese documento.
		if(os.path.exists(nombre_boletin)):
			continue
		
		#Obtiene el boletin y lo guarda la carpeta respectiva.
		r=s.get(link_boletin, headers = headers)
		with open(nombre_boletin, 'wb') as f:
			f.write(r.content)
			print("BOLETIN {} - GUARDADO".format(nombre_boletin))

	i+=1
	 
print("FIN DE EXTRACCION")
os.system("pause")