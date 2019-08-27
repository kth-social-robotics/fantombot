from fantom_util.feature_extraction import fasttext_extractor
from fantom_util.feature_extraction import spacy_extractor
from fantom_util.feature_extraction.LDA import lda
from fantom_util.feature_extraction.named_entities import named_entities, tagged_text
from fantom_util.feature_extraction.sentiment import sentiment
from fantom_util.feature_extraction.topic import topic
from fantom_util.feature_extraction.word_classes import (
    word_class_score,
    word_class_vectors,
)
from fantom_util.feature_extraction.yes_no_question import yes_no_question
from fantom_util.misc import (
    gen_feature_dict,
    remove_new_lines,
    normalize_text,
    stringify_list,
    list_to_string,
)

TEXT = {"name": "text", "history_turns": 0, "cobot-name": "text"}

LAST_SYSTEM_TEXT = {
    "name": "last_system_text",
    "history_turns": 1,
    "cobot-name": "response",
}

PREVIOUS_USER_TEXT = {
    "name": "previous_user_text",
    "history_turns": 1,
    "cobot-name": "text",
}

CHILD_UTTERANCES = {
    "name": "child_utterances",
    "history_turns": 1,
    "cobot-name": "child_utterances",
}

TRANSFORM = {
    "name": "transform",
    "history_turns": 1,
    "cobot-name": "topic_change_transform",
}

CLEAN_TEXT = {
    "name": "clean_text",
    "steps": [
        TEXT["name"],
        normalize_text,
        remove_new_lines,
        spacy_extractor.nlp,
        spacy_extractor.remove_punctuation,
        spacy_extractor.remove_stop_words,
        spacy_extractor.lemma,
        list_to_string,
    ],
}

CLEAN_TEXT2 = {
    "name": "clean_text",
    "steps": [
        TEXT["name"],
        normalize_text,
        remove_new_lines,
        spacy_extractor.nlp,
        spacy_extractor.remove_punctuation,
        spacy_extractor.remove_stop_words,
        spacy_extractor.lemma_and_oov,
        list_to_string,
    ],
}

LDA = {"name": "lda", "steps": [CLEAN_TEXT2["steps"], lda]}

TFIDF = {"name": "tfidf", "steps": [TEXT["name"], spacy_extractor.tfidf]}

YES_NO_QUESTION = {"name": "yes_no_question", "steps": [TEXT["name"], yes_no_question]}

SENTENCE_EMBEDDINGS = {
    "name": "sentence_embeddings",
    "steps": [TEXT["name"], fasttext_extractor.sentence_embeddings],
}

############################# LAYER 0? #############################


TRUECASER = {
    "name": "truecaser",
    "steps": [TEXT["name"], spacy_extractor.nlp, spacy_extractor.truecaser],
    "cobot-name": "truecaser",
    "cobot-steps": [TEXT["name"], spacy_extractor.nlp, spacy_extractor.truecaser],
    "cobot-input": [TEXT],
}


############################# LAYER 1 #############################

COREFERENCE = {
    "name": "coreference",
    "steps": [
        (
            [TEXT["name"], spacy_extractor.nlp, spacy_extractor.truecaser],
            [LAST_SYSTEM_TEXT["name"], spacy_extractor.nlp, spacy_extractor.truecaser],
            [
                PREVIOUS_USER_TEXT["name"],
                spacy_extractor.nlp,
                spacy_extractor.truecaser,
            ],
            TRANSFORM["name"],
        ),
        spacy_extractor.coreference,
    ],
    "cobot-name": "coreference",
    "cobot-steps": [
        (
            [TEXT["name"], spacy_extractor.nlp, spacy_extractor.truecaser],
            [LAST_SYSTEM_TEXT["name"], spacy_extractor.nlp, spacy_extractor.truecaser],
            [
                PREVIOUS_USER_TEXT["name"],
                spacy_extractor.nlp,
                spacy_extractor.truecaser,
            ],
            TRANSFORM["name"],
        ),
        spacy_extractor.coreference,
    ],
    "cobot-input": [TEXT, LAST_SYSTEM_TEXT, PREVIOUS_USER_TEXT, TRANSFORM],
}


############################# LAYER 2 #############################

NAMED_ENTITIES = {
    "name": "named_entities",
    "cobot-name": "named_entities",
    "steps": [(TEXT["name"], CHILD_UTTERANCES["name"]), named_entities],
    "cobot-steps": [
        (COREFERENCE["cobot-name"], CHILD_UTTERANCES["cobot-name"]),
        named_entities,
    ],
    "cobot-input": [COREFERENCE, CHILD_UTTERANCES],
}

# Independent of layer > 1
NER = {
    "name": "ner",
    "cobot-name": "ner",
    "steps": [TRUECASER["steps"], spacy_extractor.nlp, spacy_extractor.named_entities],
    "cobot-steps": [
        COREFERENCE["cobot-name"],
        spacy_extractor.nlp,
        spacy_extractor.named_entities,
    ],
    "cobot-input": [COREFERENCE],
}

# Independent of layer > 1
TOPIC = {
    "name": "topic",
    "cobot-name": "topic",
    "steps": [TRUECASER["steps"], topic],
    "cobot-steps": [COREFERENCE["cobot-name"], topic],
    "cobot-input": [COREFERENCE],
}

SENTIMENT = {
    "name": "sentiment",
    "cobot-name": "sentiment",
    "steps": [TRUECASER["steps"], sentiment],
    "cobot-steps": [COREFERENCE["cobot-name"], sentiment],
    "cobot-input": [COREFERENCE],
}

############################# LAYER 3 #############################

TAGGED_TEXT = {
    "name": "tagged_text",
    "cobot-name": "tagged_text",
    "cobot-steps": [
        (COREFERENCE["cobot-name"], NAMED_ENTITIES["cobot-name"]),
        tagged_text,
    ],
    "cobot-input": [COREFERENCE, NAMED_ENTITIES],
}

############################# LAYER 4 #############################

TOKENS = {
    "name": "tokens",
    "cobot-name": "tokens",
    "cobot-steps": [TAGGED_TEXT["cobot-name"], spacy_extractor.nlp, stringify_list],
    "cobot-input": [TAGGED_TEXT],
}

LEMMA = {
    "name": "lemma",
    "cobot-name": "lemma",
    "steps": [TEXT["name"], spacy_extractor.nlp, spacy_extractor.lemma],
    "cobot-steps": [
        TAGGED_TEXT["cobot-name"],
        spacy_extractor.nlp,
        spacy_extractor.lemma,
    ],
    "cobot-input": [TAGGED_TEXT],
}

WORD_CLASSES = {
    "name": "word_classes",
    "cobot-name": "word_classes",
    "steps": [TEXT["name"], spacy_extractor.nlp, spacy_extractor.word_classes],
    "cobot-steps": [
        TAGGED_TEXT["cobot-name"],
        spacy_extractor.nlp,
        spacy_extractor.word_classes,
    ],
    "cobot-input": [TAGGED_TEXT],
}

############################# LAYER 5 #############################

WORD_EMBEDDINGS = {
    "name": "word_embeddings",
    "cobot-name": "word_embeddings",
    "steps": [
        TEXT["name"],
        spacy_extractor.nlp,
        stringify_list,
        fasttext_extractor.word_embeddings,
    ],
    "cobot-steps": [TOKENS["cobot-name"], fasttext_extractor.word_embeddings],
    "cobot-input": [TOKENS],
}


WORD_CLASS_SCORE = {
    "name": "word_class_score",
    "cobot-name": "word_class_score",
    "steps": [WORD_CLASSES["steps"], word_class_score],
    "cobot-steps": [WORD_CLASSES["cobot-name"], word_class_score],
    "cobot-input": [WORD_CLASSES],
}

############################# LAYER 6 #############################

WORD_CLASS_VECTORS = {
    "name": "word_class_vectors",
    "cobot-name": "word_class_vectors",
    "steps": [(WORD_EMBEDDINGS["steps"], WORD_CLASSES["steps"]), word_class_vectors],
    "cobot-steps": [
        (WORD_EMBEDDINGS["cobot-name"], WORD_CLASSES["cobot-name"]),
        word_class_vectors,
    ],
    "cobot-input": [WORD_EMBEDDINGS, WORD_CLASSES],
}

# WEIGHTED_AVERAGE_WORD_EMBEDDINGS = {
#        'name': 'weighted_average_word_embeddings',
#        'cobot-name': 'weighted_average_word_embeddings',
#        'steps': [
#            (WORD_EMBEDDINGS['steps'], WORD_CLASS_SCORE['steps']),
#            weighted_average_word_embeddings
#        ],
#        'cobot-steps': [
#            (WORD_EMBEDDINGS['cobot-name'], WORD_CLASS_SCORE['cobot-name']),
#            weighted_average_word_embeddings
#        ],
#        'cobot-input': [WORD_EMBEDDINGS, WORD_CLASS_SCORE]
# }

GRAPHSEARCH_MODEL_FEATURES = gen_feature_dict(
    WORD_EMBEDDINGS,
    WORD_CLASS_SCORE,
    SENTIMENT,
    TOPIC,
    WORD_CLASSES,
    WORD_CLASS_VECTORS,
    #        WEIGHTED_AVERAGE_WORD_EMBEDDINGS
)


GRAPHSEARCH_INFERENCE_FEATURES = gen_feature_dict(
    WORD_EMBEDDINGS,
    WORD_CLASS_SCORE,
    SENTIMENT,
    TOPIC,
    WORD_CLASSES,
    WORD_CLASS_VECTORS,
    NAMED_ENTITIES,
    TAGGED_TEXT,
    #        WEIGHTED_AVERAGE_WORD_EMBEDDINGS
)

