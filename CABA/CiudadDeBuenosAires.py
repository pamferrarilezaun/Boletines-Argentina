from icecream import ic
import json
import requests
from datetime import datetime
from datetime import timedelta
from os import path
import time

#Este script se ejecuta en cualquier carpeta y dentro de la misma se guardan todos los boletines 
# correspondientes al rango de años

print("Extrayendo nuevos boletines")

# fecha desde la cual existen boletines oficiales en Ciudad De Buenos Aires y fecha del dia.
date = datetime(2021,3,22)
today = datetime.now()

# se scrapea todo hasta la fecha actual.
while date < today:

	#se obtiene la fecha de ese boletin para concatenar al nombre.
	fecha = date.strftime("%d-%m-%Y")
	#el nombre de salida del archivo esta conformado por boletinBuenosAires + la fecha de ese boletin
	ARCHIVO_SALIDA_BOLETIN = f'boletinBuenosAires_{fecha}.pdf'

	# Verifico si el boletin de la fecha ya fue extraido previamente
	existe = path.exists(ARCHIVO_SALIDA_BOLETIN)
	if existe:
		date = date + timedelta(days=1)
		continue

	# A partir de esta fecha cambia la estructura de los links
	fecha_modificacion = datetime(2017,8,17)
	if(date > fecha_modificacion):
		# se obtiene la fecha para anexar al link
		fecha = date.strftime("%Y-%m-%d")
		#URL para la pagina principal
		URL = 'https://api-restboletinoficial.buenosaires.gob.ar/obtenerBoletin/' + fecha + '/true'
	else:
		# se obtiene la fecha para anexar al link de la pagina principal
		fecha = date.strftime("%#d-%m-%Y")
		#URL para la pagina principal
		URL = 'https://api-restboletinoficial.buenosaires.gob.ar/obtenerBoletin/' + fecha + '/true'

	# Apertura de sesion
	s = requests.session()

	# Headers: encabezados necesarios para que nos detecte como navegador, no como un script
	#si en un futuro el script no funciona es importante revisar los headers
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
		'Accept': 'application/json, text/javascript, */*; q=0.01',
		'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
		'Accept-Encoding': 'gzip, deflate, br',
		'Origin': 'https://boletinoficial.buenosaires.gob.ar',
		'Connection': 'keep-alive'
	}

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

	#convierte la respuesta en un json navegable.
	data = json.loads(r.text)
	
	#si existe esta estructura de errores es porque la fecha va en otro formato, entonces se debe volver a obtener la respuesta
	try:
		if(data['errores']): 
			fecha = date.strftime("%d-%m-%Y")
			URL = 'https://api-restboletinoficial.buenosaires.gob.ar/obtenerBoletin/' + fecha + '/true'
			r = s.get(URL,headers = headers)
			data = json.loads(r.text)
	except:
		continue

	#se debe comparar la fecha de la respuesta con la fecha que esta corriendo el algoritmo. La web si no tiene cargado boletin
	# en un determinado dia, por defecto te trae el ultimo boletin oficial, entonces la fecha se setea en la del ultimo boletin.
	# si comparamos ambas fechas y no coinciden, no se debe extraer.
	fecha_de_la_respuesta = str(data['boletin']['fecha_publicacion'])
	fecha_de_corrida = date.strftime("%d/%m/%Y")
	if(fecha_de_la_respuesta == fecha_de_corrida):
		#dependiendo la fecha a extraer cambia la estructura del link
		if (date > fecha_modificacion):
			#URL para acceder al PDF correspondiente
			fecha = date.strftime("%Y%m%d")
			link_boletin_del_dia  = 'https://documentosboletinoficial.buenosaires.gob.ar/publico/' + fecha + '.pdf'
			# ic(link_boletin_del_dia)
		else:
			# se obtiene el numero para anexar al link que corresponde al PDF
			numero = numero = data['boletin']['nombre']
			numero = numero.split('.')[0]
			#URL para acceder al PDF correspondiente
			link_boletin_del_dia  = 'https://documentosboletinoficial.buenosaires.gob.ar/publico/' + numero + '.pdf'
			# ic(link_boletin_del_dia)

		#headers del nuevo link. Estos tambien pueden variar, si falla el codigo comprobar si tienen los mismos headers.
		headers_link = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
			'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
			'Accept-Encoding': 'gzip, deflate, br'
		}

		#nueva solicitud get para extraer el PDF correspondiente al boletin de la fecha.
		r_link = s.get(link_boletin_del_dia, headers = headers_link)
		# ic(r_link)

		#Se guarda la respuesta es un archivo PDF.
		with open(ARCHIVO_SALIDA_BOLETIN, 'wb') as f:
			f.write(r_link.content)
			print("BOLETIN {} - GUARDADO".format(ARCHIVO_SALIDA_BOLETIN))

	#se va al siguiente dia
	date = date + timedelta(days=1)

print("Fin de extraccion")

