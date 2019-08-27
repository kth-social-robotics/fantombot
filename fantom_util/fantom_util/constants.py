from os import environ


FANTOM_WORKDIR = environ.get('FANTOM_WORKDIR', '')
DATA_DIR = f'{FANTOM_WORKDIR}/data'
LDA_BIN = f'{FANTOM_WORKDIR}/bin/lda'
ANONYMOUS_UTTERANCE_DIR = f'{DATA_DIR}/anonymous_utterances'
ALEXA_PRIZE_BUCKET_NAME = 'YOUR_BUCKETNAME'
ANONYMOUS_UTTERANCE_DIR_ON_S3 = 'ACUOUT_ID/FrequentUtterances'
AWS_ACCESS_KEY = 'minio'
AWS_SECRET_KEY = 'miniostorage'

JOB_EXPIRY_IN_HOURS = 1

# Parameters
LDA_SIZE = 5

SCORE_THRES_HIGH = 0.89
SCORE_THRES_LOW = 0.78

HITS_TO_POST = 10

FASTTEXT_CALCULATOR_PORT = 45623

REDIS_HOST = 'localhost'
REDIS_PORT = 6379

WORD_CLASS_WEIGHTS = {
        'ADJ': 0.4, 'ADP': 0.1,
        'ADV': 0.25, 'AUX': 0.25,
        'CCONJ': 0.1, 'DET': 0.1,
        'INTJ': 0.1, 'NOUN': 1.0,
        'NUM': 0.1, 'PART': 0.1,
        'PRON': 0.2, 'PROPN': 0.3,
        'PUNCT': 0.1, 'SCONJ': 0.1,
        'SYM': 0.1, 'VERB': 0.5,
        'X': 0.3, 'SPACE': 0.01,
        'TAG': 0.9
}

TAG_ATTRIBUTES = {
        'movies': {'display_name': 'Movie Title', 'example': 'Gladiator', 'attributes': {
            'director': {'example': 'Ridley Scott', 'display_name': 'Director of '},
            'actor': {'example': 'Russell Crowe', 'display_name': 'Actor in '},
            'genre': {'example': 'action', 'display_name': 'Genre of '},
            'composer': {'example': 'Hans Zimmer', 'display_name': 'Composer for '}
            }
        },
        'musicians': {'display_name': 'Musician', 'example': 'Freddy Mercury', 'attributes': {
            'instrument': {'example': 'piano', 'display_name': 'instrument of '},
            'band': {'example': 'Queen', 'display_name': 'band of '},
            'genre': {'example': 'rock', 'display_name': 'genre of '},
            'notable work': {'example': 'Bohemian Rhapsody', 'display_name': 'famous song by '}
            }
        },
            'bands': {'display_name': 'Band', 'example': 'Queen', 'attributes': {
                'band members': {'example': 'Freddy Mercury', 'display_name': 'member of '},
                'notable work': {'example': 'Bohemian Rhapsody', 'display_name': 'famous song by '},
                'genre': {'example': 'rock', 'display_name': 'genre of '}
                }
        },
            'books': {'display_name': 'Book', 'example': 'Harry Potter', 'attributes': {
                'author': {'example': 'JK Rowling', 'display_name': 'author of '},
                'genre': {'example': 'fantasy', 'display_name': 'genre of '},
                }
        },
            'authors': {'display_name': 'Author', 'example': 'JK Rowling', 'attributes': {
                'notable work': {'example': 'Harry Potter', 'display_name': 'genre of '},
                'genre': {'example': 'fantasy', 'display_name': 'genre of '},
                }
        },
            'moviesgenre': {'display_name': 'Movie Genre', 'example': 'action', 'attributes': {}
            }
}

SPECIES_TAG = 'tag'

REDIS_ONLY = ['word_embeddings', 'word_class_vectors']

# Regexp for curse words
EXCLUDED_UTTERANCES = r''
