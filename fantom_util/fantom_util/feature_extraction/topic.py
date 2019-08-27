from fantom_util.feature_extraction.nlp import preload_model
import json
from io import BytesIO
from unidecode import unidecode
import logging

logger = logging.getLogger(__name__)


def topic_request_obj():
    import pycurl
    import certifi

    c = pycurl.Curl()
    c.setopt(
        c.URL,
        "https://TOPIC_EXTRACTOR",
    )

    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.CAINFO, certifi.where())
    c.setopt(
        c.HTTPHEADER,
        [
            "Content-Type: application/json;charset=utf-8",
            "x-api-key: API_KEY",
        ],
    )

    return c


@preload_model(topic_request_obj)
def topic(request_obj, utterance):
    if not utterance:
        return "UNCATEGORIZED"
    buffer = BytesIO()
    request_obj.setopt(request_obj.WRITEDATA, buffer)
    logger.debug('About to send to topic model: "%s"', unidecode(utterance))
    request_obj.setopt(
        request_obj.POSTFIELDS, json.dumps({"utterances": [unidecode(utterance)]})
    )
    request_obj.perform()
    try:
        response = buffer.getvalue()
        logger.debug("got topic response %s", response)
        return json.loads(response)["topics"][0]["topicClass"]
    except KeyError:
        return None
