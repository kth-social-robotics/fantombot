import logging
import re
import math

import numpy as np

from fantom_util.constants import DATA_DIR
from fantom_util.feature_extraction.nlp import preload_model
from fantom_util.file_io_util import unpickle_from_bucket
from fantom_util.misc import yank_tag


logger = logging.getLogger(__name__)


def spacy_model():
    import spacy

    model = spacy.load("en_coref_lg")
    with open(f"{DATA_DIR}/STOP_WORDS.txt", "r") as f:
        for word in f.readlines():
            lexeme = model.vocab[word.strip()]
            lexeme.is_stop = True
    return model


def tfidf_model():
    vocab_data = unpickle_from_bucket("SOME_AWS_BUCKET", "vocab_data_for_tfidf")
    return {
        "word_freqs": vocab_data["word_frequencies"],
        "number_of_utterances": vocab_data["number_of_utterances"],
    }


def truecaser_model():
    import pickle

    with open(f"{DATA_DIR}/english_distributions_no_nltk.obj", "rb") as f:
        return {
            "uni_dist": pickle.load(f),
            "backward_bi_dist": pickle.load(f),
            "forward_bi_dist": pickle.load(f),
            "trigram_dist": pickle.load(f),
            "word_casing_lookup": pickle.load(f),
        }


def lemma_and_oov_model():
    vocab_data = unpickle_from_bucket("SOME_AWS_BUCKET", "vocab_data_for_tfidf")
    return {"word_freqs": vocab_data["word_frequencies"]}


def convert_old_distributions_to_new():
    import pickle
    from collections import Counter

    with open(f"{DATA_DIR}/english_distributions.obj", "rb") as f:
        with open(f"{DATA_DIR}/english_distributions_no_nltk.obj", "wb") as f2:
            pickle.dump(Counter(pickle.load(f)), f2)
            pickle.dump(Counter(pickle.load(f)), f2)
            pickle.dump(Counter(pickle.load(f)), f2)
            pickle.dump(Counter(pickle.load(f)), f2)
            pickle.dump(pickle.load(f), f2)


@preload_model(spacy_model)
def nlp(spacy_nlp, text):
    if not text:
        return None
    doc = spacy_nlp(text)
    indexes = [m.span() for m in re.finditer(r"<.*?>", text, flags=re.IGNORECASE)]
    for start, end in indexes:
        doc.merge(start_idx=start, end_idx=end, pos="TAG")
    return doc


@preload_model(spacy_model)
def remove_stop_words(nlp, spacy_doc):
    if not spacy_doc:
        return None
    return [
        token
        for token in spacy_doc
        if nlp.vocab.has_vector(token.lower) and not nlp.vocab[token.lower].is_stop
    ]


def lemma(spacy_doc):
    if not spacy_doc:
        return []
    return [token.lemma_ for token in spacy_doc]


def remove_punctuation(spacy_doc):
    if not spacy_doc:
        return None
    return [token for token in spacy_doc if not token.is_punct]


def word_classes(spacy_doc):
    if not spacy_doc:
        return []
    return ["TAG" if yank_tag(str(token)) else token.pos_ for token in spacy_doc]


def named_entities(spacy_docs):
    if not spacy_docs:
        return []
    result = []
    for ent in spacy_docs.ents:
        result.append(
            {
                "text": ent.text,
                "begin_offset": ent.start_char,
                "end_offset": ent.end_char,
                "label": ent.label_,
            }
        )
    return result


@preload_model(lemma_and_oov_model)
def lemma_and_oov(model, spacy_doc):
    if not spacy_doc:
        return None
    oov_list = [
        (
            "oov"
            if (token.is_oov or model["word_freqs"][token.orth_] < 5)
            else token.lemma_
        )
        for token in spacy_doc
    ]

    return oov_list


@preload_model(tfidf_model)
def tfidf(model, spacy_docs):
    if not spacy_docs:
        return None
    """Returns np-array of tf-idfs for the words in utt."""
    freq_vec = np.asarray(
        [
            (0 if token.is_oov else model["word_freqs"][token.orth_])
            for token in spacy_docs
        ]
    )

    """Assert that there are some elements in the string"""
    assert freq_vec.shape[0] > 0

    """Treats each element as if it has occured at least once, in order to avoid
    dividing by 0"""
    freq_vec = freq_vec + 1
    return np.asarray(
        1.0 / freq_vec.shape[0] * np.log(model["number_of_utterances"] / freq_vec)
    )


@preload_model(spacy_model)
def coreference(nlp, user_utt, system_utt, last_user_utt, transform):
    if not all([user_utt, system_utt, last_user_utt]):
        return user_utt

    u_u = last_user_utt + " " + user_utt
    s_u = system_utt + " " + user_utt
    args = [u_u, s_u]

    for arg in args:
        doc = nlp(arg)
        coref_list = doc._.coref_clusters
        if coref_list:
            logger.debug("found coref for " + arg)
            logger.debug(coref_list)
            for item in coref_list:
                x = item.mentions
                key = x[0].text

                for thing in x:
                    thing = thing.text
                    if thing in user_utt:
                        user_utt = re.sub(rf"\b{thing}\b", key, user_utt)
            break
    if transform:
        for pattern, value in transform.items():
            if re.search(pattern, user_utt, re.IGNORECASE):
                user_utt = value
                logger.info('replacing: "%s" with: "%s"', user_utt, value)
                break

    return user_utt


def _getScore(
    prevToken,
    possibleToken,
    nextToken,
    wordCasingLookup,
    uniDist,
    backwardBiDist,
    forwardBiDist,
    trigramDist,
):
    pseudoCount = 5.0

    # Get Unigram Score
    nominator = uniDist[possibleToken] + pseudoCount
    denominator = 0
    for alternativeToken in wordCasingLookup[possibleToken.lower()]:
        denominator += uniDist[alternativeToken] + pseudoCount

    unigramScore = nominator / denominator

    # Get Backward Score
    bigramBackwardScore = 1
    if prevToken != None:
        nominator = backwardBiDist[prevToken + "_" + possibleToken] + pseudoCount
        denominator = 0
        for alternativeToken in wordCasingLookup[possibleToken.lower()]:
            denominator += (
                backwardBiDist[prevToken + "_" + alternativeToken] + pseudoCount
            )

        bigramBackwardScore = nominator / denominator

    # Get Forward Score
    bigramForwardScore = 1
    if nextToken != None:
        nextToken = nextToken.lower()  # Ensure it is lower case
        nominator = forwardBiDist[possibleToken + "_" + nextToken] + pseudoCount
        denominator = 0
        for alternativeToken in wordCasingLookup[possibleToken.lower()]:
            denominator += (
                forwardBiDist[alternativeToken + "_" + nextToken] + pseudoCount
            )

        bigramForwardScore = nominator / denominator

    # Get Trigram Score
    trigramScore = 1
    if prevToken != None and nextToken != None:
        nextToken = nextToken.lower()  # Ensure it is lower case
        nominator = (
            trigramDist[prevToken + "_" + possibleToken + "_" + nextToken] + pseudoCount
        )
        denominator = 0
        for alternativeToken in wordCasingLookup[possibleToken.lower()]:
            denominator += (
                trigramDist[prevToken + "_" + alternativeToken + "_" + nextToken]
                + pseudoCount
            )

        trigramScore = nominator / denominator

    result = (
        math.log(unigramScore)
        + math.log(bigramBackwardScore)
        + math.log(bigramForwardScore)
        + math.log(trigramScore)
    )
    # print "Scores: %f %f %f %f = %f" % (unigramScore, bigramBackwardScore, bigramForwardScore, trigramScore, math.exp(result))

    return result


@preload_model(truecaser_model)
def truecaser(model, spacy_doc):
    if not spacy_doc:
        return None
    tokens_true_case = []
    for token in spacy_doc:
        if token.is_punct or token.is_digit:
            tokens_true_case.append(token.text_with_ws)
        else:
            if token.text in model["word_casing_lookup"]:
                if len(model["word_casing_lookup"][token.text]) == 1:
                    tokens_true_case.append(
                        list(model["word_casing_lookup"][token.text])[0]
                        + token.whitespace_
                    )
                else:
                    prev_token = tokens_true_case[-1].strip() if token.i > 0 else None
                    next_token = (
                        token.nbor().text if token.i < len(spacy_doc) - 1 else None
                    )

                    best_token = None
                    highest_score = float("-inf")

                    for possibleToken in model["word_casing_lookup"][token.text]:
                        score = _getScore(
                            prev_token,
                            possibleToken,
                            next_token,
                            model["word_casing_lookup"],
                            model["uni_dist"],
                            model["backward_bi_dist"],
                            model["forward_bi_dist"],
                            model["trigram_dist"],
                        )

                        if score > highest_score:
                            best_token = possibleToken
                            highest_score = score

                    tokens_true_case.append(best_token + token.whitespace_)

                if token.i == 0:
                    tokens_true_case[0] = tokens_true_case[0].title()

            else:  # Token out of vocabulary
                tokens_true_case.append(token.text.title() + token.whitespace_)

    return "".join(tokens_true_case)

