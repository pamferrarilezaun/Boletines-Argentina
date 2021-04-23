from icecream import ic
import json
import requests
from datetime import datetime
from datetime import timedelta
import time
from bs4 import BeautifulSoup
import re
from os import path

print("Extrayendo nuevos boletines")

#Este script se ejecuta en cualquier carpeta y dentro de la misma se guardan todos los boletines correspondientes al rango de años

def guardarBoletin(r, tipo_oficial, date):
	"""
	Guarda el boletin en un archivo PDF.

	Parametros: 
		r: respuesta a la solicitud HTML del servidor.
		tipo: boolean que indica tipo boletin si es verdadero, y anexo en otro caso.
		date: fecha del boletin
	"""

	#se conforma la fecha para el nombre del archivo
	fecha_salida = date.strftime("%d-%m-%Y")

	if tipo_oficial:
		#el nombre de salida del archivo esta conformado por boletinSalta + la fecha de ese boletin
		nombre_oficial = f'boletinSalta_{fecha_salida}.pdf'
	else:
		nombre_oficial = f'AnexoSalta_{fecha_salida}.pdf'
	
	#Se guarda la respuesta en un archivo PDF.
	with open(nombre_oficial, 'wb') as f:
		f.write(r.content)
		print("BOLETIN {} - GUARDADO".format(nombre_oficial))


# fecha desde la cual existen boletines oficiales en Ciudad De Buenos Aires.
date = datetime(2021,3,7)
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
	headers_link = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
		'Accept-Encoding': 'gzip, deflate',
		'Connection': 'keep-alive'
	}

	#En este tipo de estructura HTML primero se deben obtener los valores generados dinamicamente que corresponden al link principal
	#Luego se debe conforma dicho link principal y obtener el valor dinamico que corresponde a la url del boletin.

	dia = date.strftime("%d") # se extrae el dia en el formato requerido
	mes = date.strftime("%m") # se extrae el mes en el formato requerido
	anio = date.strftime("%Y") # se extrae el anio en el formato requerido
	#se conforma el link para la solicitud en el formato requerido.
	URL_valoresdinamicos = 'http://boletinoficialsalta.gob.ar/NewMostrarBusquedaBoletinesPDF.php?seguir=Continuar&elegido=F&nrobolet=&dd=' + dia + '&mm=' + mes + '&aaaa=' + anio + '&tipo=A'
	

	# solicitud get. Obtenemos el contenido de la URL 
	contador = 0
	while contador < 5:
		try:
			r_valoresdinamicos = s.get(URL_valoresdinamicos,headers = headers_link)
			break
		except:
			contador += 1
			print("Problema de conexión")
		if(contador == 5):
			print("Problema de conexión. Intente mas tarde")
			exit()

	soup = BeautifulSoup(r_valoresdinamicos.content, 'lxml')
	# Valida que el boletin se encuentre presente, si no continua con la ejecucion del codigo.
	if soup.find(text=re.compile('Este Boletín Oficial no se encuentra')):
		date = date + timedelta(days=1)
		continue

	# se utlizan expresiones regulares en la salida del get para obtener el valor dinamico y el link principal.
	regex = 'var pagina="(?P<valores_dinamicos>.*?)"'
	match = re.search(regex, r_valoresdinamicos.text)
	valores_dinamicos = match.group('valores_dinamicos')

	# Tiene 3 tipos de estructura: se armo un codigo para una de las mismas. 

	if('biblioteca.boletinoficialsalta' in valores_dinamicos):
		# en valores dinamicos te tira el link directamente al boletin
		r = s.get(valores_dinamicos, headers = headers_link)

		if r.status_code == 200:
			guardarBoletin(r, True, date)

	elif ('MostrarBoletinesPDFmayor2004' in valores_dinamicos):
		# Obtenes PDF directamente.

		# Conformamos la solicitud para la obtencion del PDF
		url = 'http://boletinoficialsalta.gob.ar/' + valores_dinamicos
		r = s.get(url, headers = headers_link)

		if r.status_code == 200:
			guardarBoletin(r, True, date)

	elif ('BoletinPDFAnteriores' in valores_dinamicos):
		# No se puede obtener el link directo
		valores_dinamicos = match.group('valores_dinamicos').split('?')[1]
		valores_dinamicos = str(valores_dinamicos)

		URL_principal = 'http://boletinoficialsalta.gob.ar/NewBoletinPDFAnteriores.php?' + valores_dinamicos
		# solicitud get. Obtenemos el contenido de la URL principal
		r = s.get(URL_principal,headers = headers_link)
		#vuelve navegable la estructura
		soup = BeautifulSoup(r.content, 'lxml')
		#tomamos de la estrucutra lo que corresponde al numero de boletin 
		numero_de_boletin = soup.find('td', attrs = {'class':'PPModuleTtlTxt'}).text
		#nos quedamos solo con el numero, el resto no es utilidad
		numero_de_boletin = numero_de_boletin.split('Boletin:')[1].strip()
		#conformamos el link necesario para extraer el boletin.
		link = 'http://biblioteca.boletinoficialsalta.gob.ar/boletindigital/' + anio + '/' + numero_de_boletin + '.pdf'
		#conformamos en link para extraer el anexo
		link_anexo = 'http://boletinoficialsalta.gob.ar/anexodigital/' + anio + '/' + numero_de_boletin + '.pdf'
		# solicitud get. Obtenemos el contenido del link donde se encuentra el boletin
		r = s.get(link,headers = headers_link)
		# solicitud get. Obtenemos el contenido del anexo
		r_anexo = s.get(link_anexo,headers = headers_link)

		if(r_anexo.status_code == 200):
			guardarBoletin(r, False, date)

		if(r.status_code == 200):
			guardarBoletin(r, True, date)


	#se va al siguiente dia
	date = date + timedelta(days=1)

print("Fin de extraccion")
