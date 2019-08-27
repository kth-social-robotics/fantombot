from collections import Counter
import re
import os

from fantom_util.constants import (
    EXCLUDED_UTTERANCES,
    ANONYMOUS_UTTERANCE_DIR,
    ALEXA_PRIZE_BUCKET_NAME,
    ANONYMOUS_UTTERANCE_DIR_ON_S3,
)
from fantom_util.file_io_util import list_files_in_s3_bucket_dir, file_from_s3
from fantom_util.misc import normalize_text
from fantom_util.database import db_session
from fantom_util.database.models import Conversation, AnonymousUtterance, Utterance
from sqlalchemy import func, exists
import logging

logger = logging.getLogger(__name__)

ANONYMIZED_THRESHOLD = 7


def get_utterance_counts():
    conversations = db_session.query(Conversation.user_utterance).all()
    utterances = [utterance[0] for utterance in conversations]
    utterance_counts = Counter(utterances)
    return utterance_counts


def get_anonymized_list():
    utterance_counts = get_utterance_counts()
    anonymized_utterances = [
        utterance
        for utterance, count in utterance_counts.items()
        if count >= ANONYMIZED_THRESHOLD
    ]
    return anonymized_utterances


def old_anonymize():
    while True:
        utterance, count = (
            db_session.query(
                Conversation.user_utterance, func.count(Conversation.user_utterance)
            )
            .group_by(Conversation.user_utterance)
            .order_by(func.count(Conversation.user_utterance).desc())
            .filter(
                ~exists().where(Conversation.user_utterance == AnonymousUtterance.text)
            )
            .first()
        )
        print(count, utterance)
        user_input = input("Appropriate? Y/n/q ")
        if user_input.lower() == "q":
            exit()
        elif user_input.lower() == "n":
            print("-")
            db_session.add(AnonymousUtterance(text=utterance, appropriate=False))
        elif user_input == "" or user_input.lower() == "y":
            print("+")
            db_session.add(AnonymousUtterance(text=utterance, appropriate=True))
        db_session.commit()


def update_amazon_anonymous():
    if not os.path.exists(ANONYMOUS_UTTERANCE_DIR):
        os.makedirs(ANONYMOUS_UTTERANCE_DIR)

    files_to_process = []
    for file in list_files_in_s3_bucket_dir(
        ALEXA_PRIZE_BUCKET_NAME, ANONYMOUS_UTTERANCE_DIR_ON_S3
    ):
        file_name = file.key.rsplit("/", 1)[1]
        file_from_s3(
            ALEXA_PRIZE_BUCKET_NAME,
            file.key,
            f"{ANONYMOUS_UTTERANCE_DIR}/{file_name}.tmp",
        )
        files_to_process.append(f"{ANONYMOUS_UTTERANCE_DIR}/{file_name}.tmp")

    anonymous_utterances = []
    for file_path in files_to_process:
        with open(file_path, "r") as f:
            for line in f.readlines():
                if re.search(EXCLUDED_UTTERANCES, normalize_text(line)):
                    logger.info("removed utterance: %s", line.strip())
                    continue
                anonymous_utterances.append(line.strip().lower())
    anonymous_utterances = set(anonymous_utterances)
    logger.info("anonymous_utterances %d", len(anonymous_utterances))
    utterances = db_session.query(Utterance).all()

    for utterance in utterances:
        if utterance.utterance_text in anonymous_utterances:
            if not utterance.amazon_anonymous:
                logger.info("setting anonymous: %s", utterance.utterance_text)
                utterance.amazon_anonymous = True
            anonymous_utterances.remove(utterance.utterance_text)

    logger.info("anonymous_utterances left %d", len(anonymous_utterances))
    logger.info("to be added: %s", anonymous_utterances)
    for new_utterance in anonymous_utterances:
        db_session.add(Utterance(utterance_text=new_utterance, amazon_anonymous=True))

    db_session.commit()
    for file_path in files_to_process:
        os.rename(file_path, file_path[:-4])
