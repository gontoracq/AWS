import json
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Netflix')

def lambda_handler(event, context):
    print("EVENT: ", json.dumps(event))

    query_params = event.get("queryStringParameters", {}) or {}
    genre = query_params.get("genre")

    if not genre:
        return {
            'statusCode': 400,
            'body': json.dumps({"error": "Missing genre parameter"})
        }

    try:
        # Empezamos el scan
        print(f"Buscando películas con el género: {genre}")
        response = table.scan(
            FilterExpression=Attr("genres").contains(genre)
        )
        
        # Inicializamos la lista para almacenar los resultados
        all_items = response.get("Items", [])

        # Continuar con la paginación si existen más páginas
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Attr("genres").contains(genre),
                ExclusiveStartKey=response['LastEvaluatedKey']  # Paginación
            )
            all_items.extend(response.get("Items", []))

        if not all_items:
            return {
                'statusCode': 404,
                'body': json.dumps({"error": "No movies found for the specified genre"})
            }

        # Obtener todas las calificaciones 'imdb_score' para calcular el promedio global C
        imdb_scores = [float(movie.get("imdb_score", 0) or 5.0) for movie in all_items]
        
        # Calcular el promedio global de todas las calificaciones
        tamData = len(imdb_scores)
        sumData = sum(imdb_scores)
        mediaC = sumData / tamData

        # Percentil 0.9 calculado externamente. Solo las peliculas que esten situadas sobre ese umbral mínimo se consideran
        min_votes = 39895

        # Calcular la calificación ponderada de Bayes para cada película
        def bayesian_rating(movie):
            rating = float(movie.get("imdb_score", 0) or 5.0)  # Usamos 'imdb_score' o 5 si no está disponible
            num_votes = float(movie.get("imdb_votes", 0) or 0)  # Número de votos de la película
            return (mediaC * min_votes + rating * num_votes) / (min_votes + num_votes)
            
        # Aplicamos la calificación ponderada de Bayes a todas las películas
        all_items = [
            {**movie, 'bayesian_rating': bayesian_rating(movie)} for movie in all_items
        ]

        # Ordenar las películas por la calificación ponderada de Bayes (de mayor a menor)
        top_movies = sorted(all_items, key=lambda x: x['bayesian_rating'], reverse=True)[:5]

        # Limpiar la respuesta para que solo devuelva los campos necesarios
        cleaned_movies = [
            {
                'id': movie.get('id'),
                'title': movie.get('title'),
                'rating': movie.get('imdb_score'),
                'num_votes': movie.get('imdb_votes'),
                'bayesian_rating': movie.get('bayesian_rating'),
                'genres': movie.get('genres'),
                'type': movie.get('type')
            }
            for movie in top_movies
        ]

        return {
            'statusCode': 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,GET",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            'body': json.dumps(cleaned_movies, indent=4)
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({"error": f"Internal server error: {str(e)}"})
        }