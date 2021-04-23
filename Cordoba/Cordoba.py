import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import os
from glob import glob

CARPETA_SALIDA = 'dataset/'
# Verifico que la carpeta de salida exista
if not os.path.exists(CARPETA_SALIDA):
    os.mkdir('dataset')

ARCHIVO_SALIDA_BOLETIN = "dataset/boletinCordoba_{dia}-{mes}-{anio}.pdf"
ARCHIVO_SALIDA_BOLETIN_EXTRA = "dataset/extraordinariaCordoba_{dia}-{mes}-{anio}.pdf"

# Objeto de nueva sesion del cliente http
s = requests.session()

# Headers customizados de acuerdo a las solicitudes HTTP necesarias
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br'
}

# URL de solicitud para obtencion de boletines
url = 'https://boletinoficial.cba.gov.ar/{anio}/{mes}/{dia}/'

# Fecha base a partir de la cual existen publicaciones
date = datetime(2006,2,28)

# Obtengo la fecha del ultimo boletin obtenido
for boletin in glob(CARPETA_SALIDA+'*.pdf'):
    try:
        date_candidata = datetime.strptime(boletin, 'dataset\\boletinCordoba_%d-%m-%Y.pdf')
    except:
        continue
    if date_candidata > date:
        date = date_candidata

# Fecha actual
today = datetime.now()

print("EXTRAYENDO NUEVOS BOLETINES")
print("Fecha comienzo: {}".format(date.strftime('%d-%m-%Y')))

# Se itera a traves de todas las fechas, desde la fecha origen a la fecha actual
while date <= today:

    # Se da formato a dia y mes, completando con un cero delante en caso de contener un solo digito
    # Ejemplo: 3 -> 03
    dia = str(date.day).zfill(2)
    mes = str(date.month).zfill(2)

    # Verifico si el boletin de la fecha ya fue extraido previamente
    # En tal caso, paso al siguiente dia
    existe = os.path.exists(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia))
    if existe:
        date = date + timedelta(days=1)
        continue

    # Se procede a la extraccion del boletin
    #print("Boletin del dia: {}/{}/{}".format(dia, mes, date.year))

    # Primer paso: solicitud para obtener nro de Boletin
    r = s.get(url.format(anio=date.year,mes=mes,dia=dia), headers = headers)

    # Si el servidor arroja una respuesta no exitosa, avanzamos al dia siguiente
    # Respuestas no exitosas indican, en general, la no existencia del boletin en el dia requerido
    if r.status_code != 200:
        date = date + timedelta(days=1)
        continue
    
    # Se parsea la respuesta HTML obtenida de la consula al servidor
    soup = BeautifulSoup(r.content, 'lxml')

    # Edicion ordinaria
    
    # Verifico si el boletin de la fecha ya fue extraido previamente
    existe_ordinaria = os.path.exists(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia))
    if not existe_ordinaria:
        # Inteto obtener las normativas
        try:
            anchor_legislacion = soup.find(text = re.compile('Legislación – Normativas')).parent.parent
        except:
            anchor_legislacion = None

        # Si tuve exito, guardo el boletin
        if anchor_legislacion:
            url_pdf_legislacion = anchor_legislacion['href']
            r = s.get(url_pdf_legislacion, headers = headers)

            with open(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia), 'wb') as f:
                f.write(r.content)
            
            print("BOLETIN {} - GUARDADO".format(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia)))

    # Edicion extraordinaria

    # Verifico si el boletin de la fecha ya fue extraido previamente
    existe_extra = os.path.exists(ARCHIVO_SALIDA_BOLETIN_EXTRA.format(anio=date.year,mes=mes,dia=dia))
    if not existe_extra:
        try:
            anchor_legislacion_extra = soup.find(text = re.compile('EDICIÓN EXTRAORDINARIA')).parent.parent
        except:
            anchor_legislacion_extra = None

        if anchor_legislacion_extra:
            url_pdf_legislacion = anchor_legislacion_extra['href']
            r = s.get(url_pdf_legislacion, headers = headers)

            with open(ARCHIVO_SALIDA_BOLETIN_EXTRA.format(anio=date.year,mes=mes,dia=dia), 'wb') as f:
                f.write(r.content)
            
            print("BOLETIN {} - GUARDADO".format(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia)))

    date = date + timedelta(days=1)

print("FIN DE EXTRACCION")
os.system("pause")