import logging
import re

from fantom_util.feature_extraction.nlp import preload_model
from fantom_util.misc import tag_matcher

logger = logging.getLogger(__name__)

# given a user utterance and a list of children utterances, checks our named entity database for named entities of tags
# mentioned in children utterances and creates a dictionary of the ones it found

# input: text, list of children utterance


def named_entities_model():
    from fantom_util.models.named_entity_model import NamedEntityModel

    nem = NamedEntityModel("BETA")
    nem.load_model()
    return nem.model


@preload_model(named_entities_model)
def named_entities(model, text, child_utterances):
    if not all([text, child_utterances]):
        return {}
    logger.debug("named entity extractor recieved text: %s", text)
    logger.debug(
        "named entity extractor recieved child_utterances %s", child_utterances
    )

    if not child_utterances:
        child_utterances = []

    if isinstance(child_utterances, str):
        child_utterances = [child_utterances]

    info = {}  # keys = tags mentioned, values = named entities for keys

    for child_utt in child_utterances:
        for tag, tag_id, attribute in tag_matcher(child_utt):
            logger.debug("the tag: %s", tag)
            value = sorted(model[tag], key=lambda x: len(x), reverse=True)
            logger.debug("length of value list: %d", len(value))
            ne = re.findall(
                rf'\b{"|".join(map(re.escape, value))}\b', text, re.IGNORECASE
            )
            info[tag] = ne
            logger.debug("ne: %s", ne)

    user_info = {}
    for key, value in info.items():
        for element in value:
            index = value.index(element)
            key_new = key + "_" + str(index)
            user_info[key_new] = value[index]
    logger.debug("user info: %s", user_info)

    return user_info


def tagged_text(text, info):
    for key, value in info.items():
        text = re.sub(rf"\b{value}\b", f"<{key}>", text, flags=re.IGNORECASE)
    return text


def untagged_text(system_utterance, user_info, data):
    if not all([system_utterance, user_info, data]):
        return system_utterance, user_info
    tags = re.findall(r"<(.+?)>", system_utterance)
    system_info = {}

    for tag in tags:
        tag_and_attribute_match = re.search(r"<(.+?): (.+?)>", tag)
        if tag_and_attribute_match:
            entity, attribute = tag_and_attribute_match.groups()
            user_ne = user_info[entity]

            try:
                system_ne = data[user_ne][attribute]
                if isinstance(system_ne, list):
                    system_ne = system_ne[0]
                system_info[tag] = system_ne
            except KeyError:
                return system_utterance, user_info
        else:
            system_info[tag] = user_info[tag]

    text = system_utterance
    for key, value in system_info.items():
        text = text.replace(f"<{key}>", system_info[key])

    info = {**user_info, **system_info}

    return text, info
