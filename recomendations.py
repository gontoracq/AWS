import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)

netflix = pd.read_csv(r'C:/Users/torre/OneDrive/Escritorio/GONZALO/PROFESIONAL/DATASETS/titles.csv')

#Calificación promedio de todas las películas en la base de datos.
M = netflix['imdb_score'].mean()

#Umbral minimo 
q = netflix['imdb_votes'].quantile(0.9)

print(q)

#Peliculas por encima del umbral
q_movies = netflix.copy().loc[netflix['imdb_votes'] >= q]

'''Calificación Ponderada de Bayes
Este método simplemente ajusta una calificación para reflejar mejor la 
popularidad y confiabilidad de los votos.
- Favorece películas con más votos, dándoles más peso en el ranking.
- Evita la sobrevaloración de películas con pocos votos, reduciendo el impacto de puntuaciones extremas.
- Usa un umbral mínimo de votos (q) para estabilizar la calificación.'''

def weighted_rating(x, q=q, M=M):
    v = x['imdb_votes']
    R = x['imdb_score']
    return (v/(v+q) * R) + (q/(q+v) * M)

#Aplicar el rating ponderado y guardarlo en score
q_movies['score'] = q_movies.apply(weighted_rating, axis=1)

#Ordena las peliculas
q_movies = q_movies.sort_values('score', ascending=False)

#Top 10 de peliculas
#print(q_movies[['title', 'imdb_votes', 'imdb_score', 'score']].head(10))

netflix = netflix.dropna() 

netflix['weighted_rating'] = netflix.apply(weighted_rating, axis=1)


#Funcion para recomendaciones basadas en genero y popularidad
def get_genre_recommendations(genre, num_recommendations=10):
    genre_movies = netflix[netflix['genres'].apply(lambda x: genre in x)]
    if genre_movies.empty:
        print(f"No movies found for genre: {genre}")
        return pd.DataFrame()
    else:
        genre_movies = genre_movies.sort_values('weighted_rating', ascending=False)
        return genre_movies[['title', 'genres', 'weighted_rating']].head(num_recommendations)

print(get_genre_recommendations('action').head(5))


