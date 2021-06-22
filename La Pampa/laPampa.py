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


ARCHIVO_SALIDA_BOLETIN = "dataset/boletinLaPampa_{fecha}_{numero}_{nombre}.pdf"

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
url = 'https://www.lapampa.gob.ar/ano-2020.html'

print("EXTRAYENDO NUEVOS BOLETINES")

# Se obtiene el contenido de la pagina principal donde se encuentra el boletin del dia.
# En todas las solicitudes 'r' se va a intentar hasta que el servidor de respuesta porque cada tantas solicitudes falla.
while True:
    try:
        r = s.get(url, headers = headers)
        soup = BeautifulSoup(r.content, 'lxml')
        break
    except:
        continue

anio_en_curso = datetime.now().year

#Se buscan todos los anios donde hay boletin
anios = soup.find('div', attrs = {'class':'panel-body'}).find_all('li')
for anio in anios[9:]:
    i = 0
    #Se conforma el link de cada anio. 
    link_anio = 'https://www.lapampa.gob.ar' + anio.find('a')['href']

    #Se van a recorrer todas las paginas dentro de cada anio. El while recorre la paginacion. Dentro de un anio hay muchas
    # publicaciones y varias paginas. 
    # existen dos variales bandera, una llamada paginacion y otra llamada existe. La primera se pone en false cuando se llego
    # a la ultima pagina y la segunda se pone en false cuando ya existe el archivo en la carpeta dataset. El while continua
    # siempre y cuando no se hayan recorrido todas las paginas y los archivos no hayan sido descargados.

    bandera_paginacion = bandera_existe = True
    while(bandera_paginacion and bandera_existe):

        # Se agregan los iteradores para las diferentes paginas 
        link_anio2 = link_anio + '?start=' + str(i)

        #Se obtienen los links que llevan a la siguiente pagina donde estan los boletines
        while True:
            try:
                r = s.get(link_anio2, headers = headers, timeout=10)
                soup = BeautifulSoup(r.content, 'lxml')
                break
            except:
                continue

        # Se obtienen los links donde estan las publicaciones por anio. Si no existe tbody es porque no hay publicaciones
        tbody = soup.find('tbody')
        if tbody:
            # Dentro de un mismo anio hay muchas publicaciones por pagina. Se deben iterar cada pagina y todas las publicaciones
            # Dentro de cada publicacion se encuentran varios archivos PDF correspondiente a los boletines.
            publicaciones_por_anio = tbody.find_all('tr')
            for publicacion in publicaciones_por_anio:
                link_boletines_por_anio = 'https://www.lapampa.gob.ar' + publicacion.find('a')['href']

                while True:
                    try:
                        r = s.get(link_boletines_por_anio, headers = headers, timeout=10)
                        soup_boletin = BeautifulSoup(r.content, 'lxml')
                        break
                    except:
                        continue

                #Se obtienen todos los boletines dentro de un anio y dentro de una pagina
                boletines = soup_boletin.find('div', attrs = {'itemprop':'articleBody'}).find_all('a')

                # Numero secuencial para la conformacion del nombre de salida del boletin
                numero = 0

                # Se obtiene la fecha del boletin. Cambia la forma de obtenerla dependiendo el anio
                try:
                    fecha = soup_boletin.find('div', attrs = {'itemprop':'articleBody'}).find('h4').text.split(',')[1].strip()
                    fecha = dateparser.parse(fecha)                
                    fecha = fecha.strftime("%d-%m-%Y")
                except:
                    try:
                        fecha = soup_boletin.find('div', attrs = {'itemprop':'articleBody'}).find('h3').text.split(',')[1].strip()
                        fecha = dateparser.parse(fecha)                
                        fecha = fecha.strftime("%d-%m-%Y")
                    except:
                        fecha = soup_boletin.find('h2', attrs = {'itemprop':'headline'}).text.split('-')[1].strip()
                        fecha = dateparser.parse(fecha)                
                        fecha = fecha.strftime("%d-%m-%Y")

                # El tipo (si es boletin o separata)
                tipo = soup_boletin.find('h2', attrs = {'itemprop':'headline'}).text.split('-')[0].strip()

                # Comprueba si existe algun archivo en la carpeta dataset con el tipo dado para esa fecha
                # Si existe ese tipo es porque ya fueron descargados esos boletines.
                # Con lo cual, pone la bandera en False y sale del while y ademas el break corta el for de publicaciones por anio
                archivos_match = glob(CARPETA_SALIDA + '*{}*'.format(tipo))
                for nombre in archivos_match:
                    # dentro del nombre que tiene el PDF descargado nos quedamos con el tipo.
                    tipo_archivo = nombre.split('-')[-1].replace('.pdf','').strip()
                    # Si el tipo del archivo descargado es igual al tipo que devuelve la pagina y la fecha es la misma
                    # entonces el el mismo boletin y no debemos volver a descargarlo.
                    if tipo == tipo_archivo and fecha in nombre:
                        bandera_existe = False
                        break

                # Esta sentencia la hacemos porque si entra al if anterior debemos cortar la ejecucion, el script debe terminar
                if not bandera_existe:
                    break

                for boletin in boletines:
                    print("Link boletin por anio:", link_boletines_por_anio)

                    # Se obtiene el nombre del boletin. Esta conformado por dos partes: el tipo (si es boletin o separata)
                    # y el nombre que tiene el archivo PDF en la web.
                    archivo = boletin.text.replace('/', '-')
                    nombre = archivo + '-' + tipo

                    # Se conforma el nombre del archivo de salida
                    nombre_boletin = ARCHIVO_SALIDA_BOLETIN.format(fecha = fecha, numero = numero, nombre = nombre)
                    nombre_boletin = nombre_boletin.replace('*','-')


                    try:
                        # Se conforma el link del archivo PDF dentro de una fecha determinada
                        #En algunos casos no existe el link.
                        link_boletin = 'https://www.lapampa.gob.ar' + boletin['href']
                    except:
                        continue

                    # Si ya encontro el archivo en la carpeta dataset saltea la iteracion. Fue scrapeado ese boletin.
                    if(not os.path.exists(nombre_boletin)):
                        # Se obtiene el boletin y se almacena en la carpeta correspondiente
                        while True:
                            try:
                                r = s.get(link_boletin, headers = headers)
                                break
                            except:
                                continue
                        with open(nombre_boletin, 'wb') as f:
                            f.write(r.content)
                            print("BOLETIN {} - GUARDADO".format(nombre_boletin))

                    # Se le agrega un numero secuencial al nombre del archivo boletin porque no tiene un nombre unico en la web
                    # por ejemplo: dentro de una misma fecha (dia, mes y anio) hay varios archivos llamados "Anexo1" O "Anexo2"
                    # Cuando cambia de dia, mes y anio, la numeracion vuelve a empezar.
                    numero = numero + 1

            # Para pasar a la siguiente pagina
            # Se supone que el anio en curso muestra siempre 10 elementos por página
            # y los años anteriores 20 por página
            if anio == anio_en_curso:
                i+=10
            else:
                i+=20
        else:
            bandera_paginacion = False

    if(bandera_existe == False):
        break
print("FIN DE EXTRACCION")
os.system("pause")