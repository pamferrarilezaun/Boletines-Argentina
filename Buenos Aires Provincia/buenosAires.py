from icecream import ic
import json
import requests
from datetime import datetime
from datetime import timedelta
import time
from bs4 import BeautifulSoup

# fecha desde la cual existen boletines oficiales en Ciudad De Buenos Aires.
date = datetime(2010,7,2)

# se scrapea todo hasta la fecha puesta.
while date < datetime(2021,4,6):
	#fechas necesarias para la conformacion del link de la URL principal
	fecha = date.strftime("%d/%m/%Y")

	# URL correspondiente a la seccion oficial
	URL_oficial = 'https://www.boletinoficial.gba.gob.ar/buscar?search[date_gteq]=' + fecha + '&search[date_lteq]=' + fecha + '&search[section]=OFICIAL&search[words]=&search[sort]=by_match_desc&commit=Buscar'
	# URL correspondiente a la seccion suplemento
	URL_suplemento = 'https://www.boletinoficial.gba.gob.ar/buscar?search[date_gteq]=' + fecha + '&search[date_lteq]=' + fecha + '&search[section]=SUPLEMENTO&search[words]=&search[sort]=by_match_desc&commit=Buscar'
	
	# Apertura de sesion
	s = requests.session()

	# Headers
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
		'Accept-Encoding': 'gzip, deflate, br'
	}

	#solicitud get a la URL para seccion oficial
	r_oficial = s.get(URL_oficial,headers = headers)
	#la libreria BeautifulSoup transforma el HTML es una estructura navegable.
	soup_oficial = BeautifulSoup(r_oficial.content, 'lxml')

	#solicitud get a la URL para la seccion suplemento
	r_suplemento = s.get(URL_suplemento,headers = headers)
	soup_suplemento = BeautifulSoup(r_suplemento.content, 'lxml')

	# Seccion oficial.
	# considera en el if los casos que no hay boletin subido el dia de la fecha y en el else los casos en los que hay
	if(soup_oficial.find('div', attrs = {'class':'alert alert-info'})):
		pass
	else:
		#busca la clase que corresponde dentro de la estructura y luego accede al parametro 'href' que contiene parte del link
		link_oficial = soup_oficial.find('div', attrs = {'class':'title'}).find('a')['href']
		#se completa el link para hacer la solicitud correspondiente
		link_oficial = 'https://www.boletinoficial.gba.gob.ar' + link_oficial

		#solicitud get
		oficial = s.get(link_oficial,headers = headers)

		#se obtiene la fecha de ese boletin para concatenar al nombre.
		fecha = date.strftime("%d-%m-%Y")
		#el nombre de salida del archivo esta conformado por boletinProvBuenosAires + la fecha de ese boletin
		nombre_oficial = f'boletinProvBuenosAires_SeccionOficial_{fecha}.pdf'

		#Se guarda la respuesta en un archivo PDF.
		with open(nombre_oficial, 'wb') as f:
			f.write(oficial.content)

	#Seccion suplemento.
	#considera en el if los casos que no hay boletin subido el dia de la fecha y en el else los casos en los que hay
	if(soup_suplemento.find('div', attrs = {'class':'alert alert-info'})):
		pass
	else:
		#busca la clase que corresponde dentro de la estructura y luego accede al parametro 'href' que contiene parte del link
		link_suplemento = soup_suplemento.find('div', attrs = {'class':'title'}).find('a')['href']
		#se completa el link para hacer la solicitud correspondiente
		link_suplemento = 'https://www.boletinoficial.gba.gob.ar' + link_suplemento
		ic(link_suplemento)

		#solicitud get
		suplemento = s.get(link_suplemento,headers = headers)
		ic(suplemento)

		#se obtiene la fecha de ese boletin para concatenar al nombre.
		fecha = date.strftime("%d-%m-%Y")
		#el nombre de salida del archivo esta conformado por boletinProvBuenosAires + la fecha de ese boletin
		nombre_suplemento = f'boletinProvBuenosAires_SeccionSuplemento_{fecha}.pdf'

		#Se guarda la respuesta es un archivo PDF.
		with open(nombre_suplemento, 'wb') as f:
			f.write(suplemento.content)

	#se va al siguiente dia
	date = date + timedelta(days=1)
