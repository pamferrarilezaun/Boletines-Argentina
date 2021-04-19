from icecream import ic
import json
import requests
from datetime import datetime
from datetime import timedelta
import time

#Este script se ejecuta en cualquier carpeta y dentro de la misma se guardan todos los boletines correspondientes al rango de años

# fecha del dia para extraer el boletin.
date = datetime.now()

# se obtiene la fecha para anexar al link
fecha = date.strftime("%Y-%m-%d")
#URL para la pagina principal
URL = 'https://api-restboletinoficial.buenosaires.gob.ar/obtenerBoletin/' + fecha + '/true'
ic(URL)

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
r = s.get(URL,headers = headers)
ic(r)

#convierte la respuesta en un json navegable.
data = json.loads(r.text)

#si existe esta estructura de errores es porque la fecha va en otro formato, entonces se debe volver a obtener la respuesta
if(data['errores']): 
	fecha = date.strftime("%d-%m-%Y")
	URL = 'https://api-restboletinoficial.buenosaires.gob.ar/obtenerBoletin/' + fecha + '/true'
	ic(URL)
	r = s.get(URL,headers = headers)
	ic(r)
	data = json.loads(r.text)
		
else:
	pass

#se debe comparar la fecha de la respuesta con la fecha que esta corriendo el algoritmo. La web si no tiene cargado boletin
# en un determinado dia, por defecto te trae el ultimo boletin oficial, entonces la fecha se setea en la del ultimo boletin.
# si comparamos ambas fechas y no coinciden, no se debe extraer.
fecha_de_la_respuesta = str(data['boletin']['fecha_publicacion'])
fecha_de_corrida = date.strftime("%d/%m/%Y")
if(fecha_de_la_respuesta == fecha_de_corrida):
	#URL para acceder al PDF correspondiente
	fecha = date.strftime("%Y%m%d")
	link_boletin_del_dia  = 'https://documentosboletinoficial.buenosaires.gob.ar/publico/' + fecha + '.pdf'
	ic(link_boletin_del_dia)

	#headers del nuevo link. Estos tambien pueden variar, si falla el codigo comprobar si tienen los mismos headers.
	headers_link = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
		'Accept-Encoding': 'gzip, deflate, br'
	}

	#nueva solicitud get para extraer el PDF correspondiente al boletin de la fecha.
	r_link = s.get(link_boletin_del_dia, headers = headers_link)
	ic(r_link)

	#se obtiene la fecha de ese boletin para concatenar al nombre.
	fecha = data['boletin']['fecha_publicacion'].replace('/','-')
	#el nombre de salida del archivo esta conformado por boletinBuenosAires + la fecha de ese boletin
	nombre = f'boletinBuenosAires_{fecha}.pdf'

	#Se guarda la respuesta es un archivo PDF.
	with open(nombre, 'wb') as f:
		f.write(r_link.content)
