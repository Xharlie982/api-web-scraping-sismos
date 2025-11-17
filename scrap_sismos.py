import requests
import boto3
import uuid
import json
from datetime import datetime

def lambda_handler(event, context):
    
    # URL de la API del IGP - dinámico por año
    year = datetime.now().year
    url = f"https://ultimosismo.igp.gob.pe/api/ultimo-sismo/ajaxb/{year}"
    
    # Realizar la solicitud HTTP a la API
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        sismos_data = response.json()  # La respuesta ya es JSON
    except requests.RequestException as e:
        return {
            'statusCode': 500, 
            'body': json.dumps({'error': f'Error al acceder a la API: {str(e)}'})
        }
    except json.JSONDecodeError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Error al parsear JSON: {str(e)}'})
        }

    # Validar que obtuvimos datos
    if not sismos_data or not isinstance(sismos_data, list):
        return {
            'statusCode': 404, 
            'body': json.dumps({'error': 'No se encontraron datos de sismos'})
        }

    # Limitar a los 10 más recientes
    sismos_data = sismos_data[:10]

    rows = []
    for i, sismo in enumerate(sismos_data, 1):
        try:
            # Extraer datos del JSON
            item = {
                'id': str(uuid.uuid4()),
                '#': i,
                'codigo': sismo.get('codigo', ''),
                'fecha_hora_local': f"{sismo.get('fecha_local', '')} {sismo.get('hora_local', '')}",
                'fecha_utc': f"{sismo.get('fecha_utc', '')} {sismo.get('hora_utc', '')}",
                'latitud': str(sismo.get('latitud', '')),
                'longitud': str(sismo.get('longitud', '')),
                'magnitud': str(sismo.get('magnitud', '')),
                'profundidad': f"{sismo.get('profundidad', '')} km",
                'referencia': sismo.get('referencia', ''),
                'intensidad': sismo.get('intensidad', ''),
                'reporte_pdf': sismo.get('reporte_acelerometrico_pdf', ''),
                'createdAt': sismo.get('createdAt', ''),
                'updatedAt': sismo.get('updatedAt', '')
            }
            rows.append(item)
        except Exception as e:
            # Si hay error con un sismo específico, continuar con el siguiente
            print(f"Error procesando sismo {i}: {str(e)}")
            continue

    if not rows:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'No se pudieron procesar los sismos'})
        }

    # Guardar en DynamoDB
    try:
        dynamodb = boto3.resource('dynamodb')
        table_db = dynamodb.Table('TablaSismos')

        # Eliminar todos los elementos de la tabla
        scan = table_db.scan()
        with table_db.batch_writer() as batch:
            for each in scan['Items']:
                batch.delete_item(Key={'id': each['id']})

        # Insertar los nuevos datos
        for row in rows:
            table_db.put_item(Item=row)
    
    except Exception as e:
        return {
            'statusCode': 500, 
            'body': json.dumps({'error': f'Error al guardar en DynamoDB: {str(e)}'})
        }

    # Retornar el resultado
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': f'Se extrajeron y guardaron {len(rows)} sismos correctamente',
            'total_sismos': len(rows),
            'sismos': rows
        }, ensure_ascii=False)
    }
