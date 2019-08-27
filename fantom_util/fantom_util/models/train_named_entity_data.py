from fantom_util.models.wptools_scraper import get_links, create_database
from imdb import IMDb
from tqdm import tqdm

ia = IMDb()

# AVAILABLE CATEGORIES: MOVIES, MUSICIANS, BANDS, AUTHORS, BOOKS


def get_entities(category):
    filter = [
        "in film",
        "in television",
        "in home video",
        "in architecture",
        "in music",
        "in science",
    ]
    entities = []
    webs = []
    if category == "movies":
        webs = ["2010s_in_film", "2000s_in_film", "2018_in_film"]

        top250 = ia.get_top250_movies()
        for item in top250:
            item = str(item)
            entities.append(item)

    if category == "musicians":
        webs = [
            "2010s_in_music",
            "List_of_best-selling_music_artists",
            "2000s_in_music",
            "List_of_alternative_rock_artists",
        ]

    if category == "bands":
        webs = [
            "2010s_in_music",
            "List_of_best-selling_music_artists",
            "2000s_in_music",
            "List_of_alternative_rock_artists",
        ]

    if category == "books":
        webs = [
            "List_of_best-selling_books",
            "Pulitzer_Prize_for_Fiction",
            "List_of_winners_and_shortlisted_authors_of_the_Booker_Prize",
            "The_New_York_Times_Non-Fiction_Best_Sellers_of_2016",
            "The_New_York_Times_Non-Fiction_Best_Sellers_of_2017",
            "The_New_York_Times_Non-Fiction_Best_Sellers_of_2018",
            "The_New_York_Times_Fiction_Best_Sellers_of_2018",
            "The_New_York_Times_Fiction_Best_Sellers_of_2017",
            "The_New_York_Times_Fiction_Best_Sellers_of_2016",
        ]

    if category == "authors":
        webs = [
            "List_of_best-selling_fiction_authors",
            "List_of_best-selling_books",
            "Pulitzer_Prize_for_Fiction",
            "List_of_winners_and_shortlisted_authors_of_the_Booker_Prize",
            "The_New_York_Times_Non-Fiction_Best_Sellers_of_2016",
            "The_New_York_Times_Non-Fiction_Best_Sellers_of_2017",
            "The_New_York_Times_Non-Fiction_Best_Sellers_of_2018",
            "The_New_York_Times_Fiction_Best_Sellers_of_2018",
            "The_New_York_Times_Fiction_Best_Sellers_of_2017",
            "The_New_York_Times_Fiction_Best_Sellers_of_2016",
        ]

    for item in tqdm(webs):
        l = get_links(item)
        for link in l:
            if all(ext not in link for ext in filter):
                entities.append(link)

    entities = list(set(entities))
    return entities


def full_scrape(category):
    entities = get_entities(category)
    database = create_database(entities, category)
    return database

