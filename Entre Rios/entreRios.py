from icecream import ic
import json
import requests
from datetime import datetime
from datetime import timedelta
import time
from bs4 import BeautifulSoup
import locale
from os import path

print("Extrayendo nuevos boletines")

# Idioma "es-ES" (código para el español de España)
locale.setlocale(locale.LC_ALL, 'es-ES')

#Este script se ejecuta en cualquier carpeta y dentro de la misma se guardan todos los boletines correspondientes 
# al rango de años

# fecha desde la cual existen boletines oficiales en Ciudad De Buenos Aires.
date = datetime(2021,3,1)
today = datetime.now()

# se scrapea todo hasta la fecha actual.
while date < today:

	#se obtiene la fecha
	fecha = date.strftime("%d-%m-%Y")
	#el nombre de salida del archivo esta conformado por boletinProvBuenosAires + la fecha de ese boletin
	ARCHIVO_SALIDA_BOLETIN = f'boletinEntreRios_{fecha}.pdf'
	# Verifico si el boletin de la fecha ya fue extraido previamente
	existe = path.exists(ARCHIVO_SALIDA_BOLETIN)
	if existe:
		date = date + timedelta(days=1)
		continue

	# Apertura de sesion
	s = requests.session()

	# Headers: encabezados necesarios para que nos detecte como navegador, no como un script
	#si en un futuro el script no funciona es importante revisar los headers
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
		'Accept-Encoding': 'gzip, deflate, br'
	}

	#se conforma el link para la solicitud en el formato requerido.
	URL = 'https://www.entrerios.gov.ar/boletin/calendario/Boletin/'
	anio = date.strftime("%Y") # se extrae el anio en el formato requerido
	mes = date.strftime("%B").title() #se extrae el mes en el formato requerido: la primera con mayuscula
	fecha = date.strftime("%d-%m") #se extrae la fecha en el formato dia-mes-anio
	fecha_anio = date.strftime("%Y")[-2:]#el anio requiere solo dos digitos
	URL = URL + anio + '/' + mes + '/' + fecha + '-' + fecha_anio + '.pdf'

	# solicitud get. Obtenemos el contenido de esa URL
	contador = 0
	while contador < 5:
		try:
			r = s.get(URL,headers = headers)
			break
		except:
			contador += 1
		if(contador == 5):
			print("Problema de conexión. Intente mas tarde")
			break

	#se comprueba si hay boletin oficial ese dia. En caso de que no haya continua, si no, se guarda el boletin.
	soup = BeautifulSoup(r.content, 'lxml') # se tranforma en una estrucutra navegable para poder acceder al contenido
	try:
		if(soup.find('h1').text == 'Not Found'):
			pass
	except:
		#se conforma la fecha para el nombre del archivo
		fecha_salida = date.strftime("%d-%m-%Y")
		#el nombre de salida del archivo esta conformado por boletinEntreRios + la fecha de ese boletin
		nombre_oficial = f'boletinEntreRios_{fecha_salida}.pdf'

		#Se guarda la respuesta en un archivo PDF.
		with open(nombre_oficial, 'wb') as f:
			f.write(r.content)
			print("BOLETIN {} - GUARDADO".format(nombre_oficial))

	#se va al siguiente dia
	date = date + timedelta(days=1)

print("Fin de extraccion")