import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import os
from glob import glob
import os

CARPETA_SALIDA = 'dataset/'
# Verifico que la carpeta de salida exista
if not os.path.exists(CARPETA_SALIDA):
    os.mkdir('dataset')

ARCHIVO_SALIDA_BOLETIN = "dataset/boletinTierraDelFuego_{dia}-{mes}-{anio}.zip"

# Objeto de nueva sesion del cliente http
s = requests.session()

# Headers customizados de acuerdo a las solicitudes HTTP necesarias
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Content-Type': 'application/x-www-form-urlencoded',
}

#
payload = {
	"bnumerod": "",
	"bnumeroh": "",
	"btextobol": "",
	"seleccion": "3",
	"buscarbol": "%2B%2B%2B%2B%2BBuscar%2B%2B%2B%2B%2B"
}

payload = {
	"bnumerod": "",
	"bnumeroh": "",
	"btextobol": "",
	"seleccion": "3",
	"buscarbol": "+++++Buscar+++++"
}

# payload='bnumerod=&bnumeroh=&btextobol=&seleccion=3&buscarbol=%2B%2B%2B%2B%2BBuscar%2B%2B%2B%2B%2B&fechadebol={}%2F{}%2F{}&fechahabol={}%2F{}%2F{}'

# URL de solicitud para obtencion de boletines
url = 'http://recursosweb.tierradelfuego.gov.ar/webapps/decoley/resultados.php'

# r = s.get(url)
# headers['Cookie'] = r.headers['Set-Cookie'].split(';')[0]
# print(headers)

# Fecha base a partir de la cual existen publicaciones
date = datetime(2001,5,21)
# date = datetime(2001,10,1)

# Obtengo la fecha del ultimo boletin obtenido
for boletin in glob(CARPETA_SALIDA+'*.zip'):
    try:
        date_candidata = datetime.strptime(boletin, 'dataset\\boletinTierraDelFuego_%d-%m-%Y.zip')
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
    print(date)
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

    payload["fechadebol"] = payload["fechahabol"] = '{}/{}/{}'.format(dia, mes, date.year)

    while True:
        try:
            r = s.post(url, headers = headers, data = payload, timeout = 10)
            break
        except:
            continue

    # Si el servidor arroja una respuesta no exitosa, avanzamos al dia siguiente
    # Respuestas no exitosas indican, en general, la no existencia del boletin en el dia requerido
    if r.status_code != 200:
        date = date + timedelta(days=1)
        continue
    
    # Se parsea la respuesta HTML obtenida de la consula al servidor
    results = r.text[r.text.find('</html>')+7:]
    soup = BeautifulSoup(results, 'lxml')


    # Edicion ordinaria
    anchor = soup.find('div', attrs={'id':'boletines'}).find('a')

    if anchor:
        url_zip = anchor['href']

        while True:
            try:
                r = s.get(url_zip, headers = headers)
                break
            except:
                continue

        with open(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia), 'wb') as f:
            f.write(r.content)
        
        print("BOLETIN {} - GUARDADO".format(ARCHIVO_SALIDA_BOLETIN.format(anio=date.year,mes=mes,dia=dia)))

    date = date + timedelta(days=1)

print("FIN DE EXTRACCION")
os.system("pause")