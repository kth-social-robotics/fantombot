from fantom_util.feature_extraction.nlp import preload_model
from fantom_util.constants import DATA_DIR


WH = ["which", "where", "what", "when", "who", "whose", "how", "whom", "why"]
CLARIFICATIONS = ["pardon?", "pardon me?", "sorry?", "excuse me?"]


def stanford_nlp_model():
    from stanfordcorenlp import StanfordCoreNLP

    return StanfordCoreNLP(r"{}/stanford".format(DATA_DIR))


@preload_model(stanford_nlp_model)
def yes_no_question(model, utterance):
    if not utterance:
        return False
    for word in WH:
        if word in utterance.lower():
            return False
    if "SQ" in model.parse(utterance) or "SQ" in model.parse(
        utterance.lower()
    ):  # or "SQ" in model.parse(utterance + '?') or "SQ" in model.parse(utterance.lower() + '?'):
        return True
    for clarification in CLARIFICATIONS:
        if clarification in utterance.lower() and utterance.count("?") == 1:
            return False
    if "?" in utterance.lower():
        return True
    else:
        return False
