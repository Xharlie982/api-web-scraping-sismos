import requests
from bs4 import BeautifulSoup
import boto3
import uuid
import json

def lambda_handler(event, context):
    
    # URL de la página web de sismos
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"
    
    # Realizar la solicitud HTTP a la página web
    try:
        response = requests.get(url, timeout=15) # Timeout de 15 seg
        response.raise_for_status() # Lanza error si la petición falla (ej. 404, 500)
    except requests.RequestException as e:
        return {
            'statusCode': 500, 
            'body': json.dumps({'error': f'Error al acceder a la página web: {str(e)}'})
        }

    # Parsear el contenido HTML
    soup = BeautifulSoup(response.content, 'html.parser')

    # --- Esta es la lógica CORREGIDA ---
    # 1. Encontrar el contenedor principal de la lista de sismos
    # La clase correcta es 'sismos-list'
    sismo_container = soup.find('div', class_='sismos-list')
    
    if not sismo_container:
        return {
            'statusCode': 404, 
            'body': json.dumps({'error': 'No se encontró el contenedor de sismos (clase: sismos-list)'})
        }

    # 2. Encontrar los 10 últimos sismos (son etiquetas <article>)
    sismos = sismo_container.find_all('article', limit=10)
    # --- Fin de la lógica corregida ---

    if not sismos:
        return {
            'statusCode': 404, 
            'body': json.dumps({'error': 'No se encontraron items de sismos (<article>) en la lista'})
        }

    rows = []
    i = 1
    # 3. Iterar sobre los 10 sismos y extraer datos
    for sismo in sismos:
        try:
            # Extraer los datos de cada sismo usando sus clases
            fecha_hora_local = sismo.find_all('p')[0].text.strip()
            referencia = sismo.find_all('p')[1].text.strip()
            magnitud = sismo.find('div', class_='sismo-mag').find('p').text.strip()
            profundidad = sismo.find('div', class_='sismo-prof').find('p').text.strip()

            item = {
                'id': str(uuid.uuid4()), # Generar un ID único
                '#': i,
                'fecha_hora_local': fecha_hora_local,
                'referencia': referencia,
                'magnitud': magnitud,
                'profundidad': profundidad
            }
            rows.append(item)
            i += 1
        except Exception as e:
            # Si un <article> tiene una estructura diferente, lo saltamos
            continue 

    # 4. Guardar los datos en DynamoDB
    try:
        dynamodb = boto3.resource('dynamodb')
        table_db = dynamodb.Table('TablaSismos') # Nombre de la tabla de serverless.yml

        # Eliminar todos los elementos de la tabla
        scan = table_db.scan()
        with table_db.batch_writer() as batch:
            for each in scan['Items']:
                batch.delete_item(
                    Key={
                        'id': each['id']
                    }
                )

        # Insertar los nuevos datos
        for row in rows:
            table_db.put_item(Item=row)
    
    except Exception as e:
        return {
            'statusCode': 500, 
            'body': json.dumps({'error': f'Error al guardar en DynamoDB: {str(e)}'})
        }

    # 5. Retornar el resultado como JSON
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*' # Para CORS
        },
        'body': json.dumps({
            'message': f'Se extrajeron y guardaron {len(rows)} sismos correctamente',
            'total_sismos': len(rows),
            'sismos': rows
        }, ensure_ascii=False) # ensure_ascii=False para que no escape tildes
    }
