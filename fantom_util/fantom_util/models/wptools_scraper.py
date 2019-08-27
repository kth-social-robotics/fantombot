# import time
from titlecase import titlecase
from imdb import IMDb

ia = IMDb()

# start_time = time.time()

search_dict = {
    "director": "P57",
    "actor": "P161",
    "notablework": "P800",
    "instance": "P31",
    "genre": "P136",
    "composer": "P86",
    "basedon": "P144",
    "series": "P179",
    "occupation": "P106",
    "instrument": "P1303",
    "band": "P463",
    "movement": "P135",
    "bandmembers": "P1527",
    "author": "P50",
}
retrieve_dict = {
    "director": "director (P57)",
    "actor": "cast member (P161)",
    "notablework": "notable work (P800)",
    "instance": "instance of (P31)",
    "genre": "genre (P136)",
    "composer": "composer (P86)",
    "basedon": "based on (P144)",
    "series": "series (P179)",
    "occupation": "occupation (P106)",
    "instrument": "instrument (P1303)",
    "band": "member of (P463)",
    "movement": "movement (P135)",
    "bandmembers": "has part (P1527)",
    "author": "author (P50)",
}


def wiki_string(entity):
    if "(" in entity:
        x = entity.split("(")
        query_string = titlecase(x[0])
        query_string = query_string.replace(" ", "_")
        query_string = query_string + "(" + x[1]

    else:
        query_string = titlecase(entity)
        query_string = query_string.replace(" ", "_")

    return query_string


# print(wiki_string('Isle of dogs (film)'))

# TODO: what if we find a disambiguation
def wptools_fn(entity, **kwargs):
    import wptools

    page = wptools.page(entity)
    labels = kwargs.get("labels", None)

    if labels:
        if type(labels) is not list:
            labels = [labels]
        page.wanted_labels(labels)
    # page.get_query()

    page.get_wikidata()
    data = page.data["wikidata"]
    label = page.data["label"]

    return data, label


# print(wptools_fn('Jane_Austen'))


def common_properties(entities):
    import wptools

    if type(entities) is not list:
        entities = [entities]
    keys = []
    dict = {}
    for item in entities:
        item = wiki_string(item)
        info = wptools_fn(item)
        keys.extend(info.keys() & dict.keys())
        dict = info

    return set(keys)


def wiki_to_string(item):
    if type(item) is list:
        l = []
        for thing in item:
            l.append(wiki_to_string(thing))
        return l
    if item:
        x = item.split(" (")
        return x[0]


def get_links(entity):
    import wptools

    page = wptools.page(entity)
    page.get_query()
    links = page.data["links"]
    return links


def check_data(info, category):
    wiki_films = ["films", "animated film", "feature film", "cult film"]
    wiki_musicians = ["singer", "musician", "rapper", "singer-songwriter"]
    instance = info["instance"]

    if not isinstance(instance, list):
        instance = [instance]

    if category == "movies":
        if not all(ext in instance for ext in wiki_films):
            return True

    if category == "musicians":
        if info["occupation"]:
            occupation = info["occupation"]
            if any(ext in occupation for ext in wiki_musicians):
                return True

    if category == "authors":
        if info["occupation"]:
            occupation = info["occupation"]
            if any("writer" in ext for ext in occupation):
                return True

    if category == "bands":
        if any("band" in ext for ext in instance):
            return True

    if category == "books":
        if any("book" in ext for ext in instance):
            return True


# entity is a string, type is the type of entity (movie, book, etc.), fields is a list of fields wanted(director, actor)
def info_retrieval(entity, properties):
    import wptools

    x = wiki_string(entity)
    labels = []

    if properties:
        if type(properties) is not list:
            properties = [properties]
        for item in properties:
            labels.append(search_dict[item])
    [data, title] = wptools_fn(x, labels=labels)

    clean_data = {}
    for property in properties:
        if retrieve_dict[property] in data.keys():
            result = data[retrieve_dict[property]]
            if type(result) is list:
                clean_data[property] = wiki_to_string(result[0:4])
            else:
                clean_data[property] = wiki_to_string(result)

    instance = data["instance of (P31)"]
    instance = wiki_to_string(instance)
    clean_data["instance"] = instance
    clean_data["title"] = title

    return clean_data


def build_data(entities, properties, category):
    data = {}
    unknown = []
    unknown_category = []
    unknown_final = []

    if type(entities) is not list:
        entities = [entities]
    for item in entities:
        try:
            info = info_retrieval(item, properties)
            title = info["title"]
            if check_data(info, category):
                data[title] = info
            else:
                unknown.append(item)

        except LookupError:
            unknown.append(item)

    if category == "movies":
        for item in unknown:
            item_with = item + " (film)"
            try:
                info = info_retrieval(item_with, properties)
                title = info["title"]
                data[title] = info
            except LookupError:
                unknown_category.append(item)

        for item in unknown_category:
            try:
                movie = ia.search_movie(item)[0]
                ia.update(movie)
                year = movie.get("year")
                item_year = item + " (" + str(year) + " film)"
                try:
                    info = info_retrieval(item_year, properties)
                    title = info["title"]
                    data[title] = info
                except LookupError:
                    unknown_final.append(item)
            except IndexError:
                unknown_final.append(item)

        unknown = unknown_final

    return data, unknown


# print(build_data(['Jane Austen', 'Terry Pratchett'], ['genre', 'notablework', 'occupation', 'basedon'], 'authors'))


def create_database(entities, category):
    properties = [
        "director",
        "actor",
        "genre",
        "composer",
        "basedon",
        "series",
        "occupation",
        "notablework",
        "instrument",
        "band",
        "movement",
        "bandmembers",
        "author",
    ]
    [database, unknown] = build_data(entities, properties, category)
    database[category] = [*database]
    return database
