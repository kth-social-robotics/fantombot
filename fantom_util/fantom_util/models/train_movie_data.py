from fantom_util.models.wptools_scraper import build_data, get_links
from imdb import IMDb

ia = IMDb()

properties = ["director", "actor", "genre", "composer", "based on", "series"]


def gen_movies():

    movies = [
        "Blade Runner",
        "Solo: A Star Wars Story",
        "children of the Corn: Revelation",
        "Apocalypse Now",
        "Iron Man",
        "Black Panther",
        "Incredibles 2",
        "Moonrise Kingdom",
        "Isle of dogs",
        "Despicable Me 3",
        "Monty Python and the Holy Grail",
    ]

    top250 = ia.get_top250_movies()
    for item in top250:
        item = str(item)
        movies.append(item)

    websites = [
        "2018_in_film",
        "2017_in_film",
        "2016_in_film",
        "2015_in_film",
        "2014_in_film",
        "2013_in_film",
        "2012_in_film",
        "2011_in_film",
        "2010_in_film",
    ]

    webs = ["2010s_in_film", "2000s_in_film"]

    filter = [
        "in film",
        "in television",
        "in home video",
        "in architecture",
        "in music",
        "in science",
        "in philosophy",
        "in sports",
        "in archaeology",
        "in literature",
        "2010s",
    ]
    for item in webs:
        l = get_links(item)
        for link in l:
            if all(ext not in link for ext in filter):
                movies.append(link)

    movies = list(set(movies))
    return movies


def create_database(movies):
    [database, unknown] = build_data(movies, properties, category="film")
    database["movies"] = [*database]  # list(database.keys())
    return database
