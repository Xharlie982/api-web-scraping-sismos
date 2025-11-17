# api-web-scraping-sismos

API Serverless para hacer Web Scraping de los últimos sismos reportados por el Instituto Geofísico del Perú (IGP).

## Descripción
Este proyecto extrae los 10 últimos sismos reportados en la página web del IGP y los almacena en una tabla DynamoDB.

## Tecnologías
- AWS Lambda
- API Gateway
- DynamoDB
- Python 3.12
- Serverless Framework
- BeautifulSoup4

## Despliegue (MV Desarrollo UTEC)

1.  **Clonar repositorio:**
    ```bash
    cd /home/ubuntu/lambdas/
    git clone [https://github.com/TU_USUARIO/api-web-scraping-sismos.git](https://github.com/TU_USUARIO/api-web-scraping-sismos.git)
    cd api-web-scraping-sismos
    ```

2.  **Instalar dependencias:**
    ```bash
    pip3 install -r requirements.txt -t .
    ```

3.  **Desplegar:**
    ```bash
    sls deploy
    ```

## Endpoint
`GET` - `https://[api-id].execute-api.us-east-1.amazonaws.com/dev/scrape/sismos`
