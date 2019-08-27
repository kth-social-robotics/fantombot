# function that checks if string contains <, yes: match tag with category and replace with tag, no: nothing
# from fantom_util.maggie.run import lookup_table, node_utts, id_utt

# gsm = GraphSearchModel()
# gsm.load_model()

# lookup_table = gsm.model['lookup_table']
# node_utts = gsm.model['node_utts']
# id_utt = gsm.model['id_utt']

# TODO: not just perfect matching, but if any element contains the named entity string - Harry Potter, Solo, etc.'
# TODO: might be part of the database, rather than code

data = {
    "movie": [
        "Blade Runner",
        "Harry Potter",
        "Solo: A Star Wars Story",
        "Children of the Corn VII",
    ],
    "director": ["Ridley Scott"],
    "Blade Runner": {
        "director": "Ridley Scott",
        "actor": "Harrison Ford",
        "genre": "science fiction",
    },
}

last_utt = ["What is your favourite movie?"]
test_child = "My favourite movie is <movie_0>"
test_children_utts = [
    "It is <movie_0>",
    "My favourite movie is <movie_0>",
    "I like <movie_0> and <movie_1>.",
    "Cool",
    "I like movies by <director_0>",
]

# TODO: get a list of entities of the tag
# TODO: check on empty string
# TODO: indexing of tags based on existence of tags in the dictionary, not in the utterance


def entity_to_tag(user_info, text):
    for key, value in user_info.items():
        text = text.replace(user_info[key], "<" + key + ">")

    return text


def tag_info(user_utterance, child_utterances):
    info = {}  # keys = tags mentioned, values = named entities for keys

    for child_utt in child_utterances:
        if "<" in child_utt:
            tag = child_utt[child_utt.find("<") + 1 : child_utt.find("_")]
            ne = [element for element in data[tag] if (element in user_utterance)]
            info[tag] = ne

    user_info = {}
    for key, value in info.items():
        for element in value:
            index = value.index(element)
            key_new = key + "_" + str(index)
            user_info[key_new] = value[index]

    return user_info


# TODO: cannot handle tags that have not been used before
# TODO: maybe add so it splits by ':' if there is no ':_' to avoid
# TODO: test silly formatting mistakes
def tag_to_entity(system_utterance, user_info):
    tag = system_utterance.split(" <")
    x = ">"
    tags = []
    for item in tag:
        if x in item:
            tags.append(item.split(">")[0])

    system_info = {}
    y = ":"
    for item in tags:
        if y in item:
            labels = item.split(": ")
            user_ne = user_info[labels[0]]
            key = labels[1].split("_")[0]
            system_ne = data[user_ne][key]
            system_info[item] = system_ne
        else:
            system_ne = user_info[item]
            system_info[item] = system_ne

    text = system_utterance
    for key, value in system_info.items():
        text = text.replace("<" + key + ">", system_info[key])

    info = {**user_info, **system_info}

    return text, info


def children_utterances(node_id, model):
    lookup_table = model["lookup_table"]
    node_utts = model["node_utts"]
    id_utt = model["id_utt"]

    child_ids = lookup_table[node_id]
    child_utterances = []
    child_utterance_ids = []

    l = []
    for id in child_ids:
        l.append(node_utts[id])

    for item in l:
        child_utterance_ids.extend(item)

    for utt in child_utterance_ids:
        child_utt = id_utt[utt]["text"]
        child_utterances.append(child_utt)

    return child_utterances
