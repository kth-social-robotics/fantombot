import datetime
import random
import re

from fantom_util.constants import EXCLUDED_UTTERANCES, FANTOM_WORKDIR
from fantom_util.database import db_session
from fantom_util.database.models import Conversation, Node, AnonymousUtterance
from fantom_util.graph_tools.misc import get_full_child_count
from fantom_util.graph_tools.node_tools import create_new_node, merge_nodes
from sqlalchemy.orm import joinedload
from tqdm import tqdm
import logging
from fantom_util.misc import normalize_text
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


STOP_REGEX = r"""
(alexa)?(don\'t (want|like) (to )?(talk|chat|speak|discuss|hear) (anymore|to you|any further|with you|to you))|
(alexa|echo|amazon|computer) (cancel|exit|stop|off|turn off|zip it|quit|shut up|bye|goodbye|good night)|
(cancel|exit|stop|off|turn off|zip it|quit|shut up|bye|goodbye|good night) (alexa|echo|amazon|computer)|
(stop stop|turn off turn off|shut up shut up|exit exit|quit quit)
"""

STOP_WORDS = [
    "cancel",
    "exit",
    "stop",
    "off",
    "turn off",
    "zip it",
    "quit",
    "shut up",
    "bye",
    "goodbye",
    "good night",
]


REPEAT_PHRASES = [
    "what did you say",
    "what did you just say",
    "can you say that again",
    "i didn't catch that",
    "i did not catch that",
    "come again",
    "repeat",
    "sorry repeat",
    "repeat please",
    "what",
]

REPEAT_REGEX = r"""
(alexa|echo|computer|amazon) repeat|
repeat (alexa|echo|computer|amazon)|
repeat that|
repeat repeat|
(can|could) (you )?(please )?repeat|
repeat (your|the )?(last )?sentence
"""


def process_conversation(conversation_id, root_node_utterances, automate):
    conversations = (
        db_session.query(Conversation)
        .filter(Conversation.conversation_id == conversation_id)
        .order_by(Conversation.interaction_timestamp)
        .all()
    )

    logger.debug("processing conversation_id: %s", conversation_id)

    conversation_chunks = []
    processed = 0
    for conversation in conversations:
        if conversation.intent == "LaunchRequestIntent":
            processed += 1
            continue
        if root_node_utterances.get(normalize_text(conversation.user_utterance)):
            conversation_chunks.append([])
        if not conversation_chunks:
            conversation_chunks = [[]]
        for conversation_chunk in conversation_chunks:
            conversation_chunk.append(conversation)
        if conversation.processed:
            processed += 1
    if processed >= len(conversations):
        logger.debug("skipping due to all being processed")
        return None

    logger.debug([[y.user_utterance for y in x] for x in conversation_chunks])
    processed_time = datetime.datetime.now()
    for conversations in conversation_chunks:
        parent = None
        child_nodes = root_node_utterances

        for idx, conversation in enumerate(conversations):
            text = normalize_text(conversation.user_utterance)

            if conversation.intent == "LaunchRequestIntent":
                logger.debug(
                    "skipping: LaunchRequestIntent: %d %s",
                    idx,
                    conversation.user_utterance,
                )
                continue
            if not text:
                logger.debug(
                    "skipping: user utterance is empty: %d %s",
                    idx,
                    conversation.user_utterance,
                )
                continue

            if re.search(EXCLUDED_UTTERANCES, text) or re.search(
                EXCLUDED_UTTERANCES, conversation.user_utterance
            ):
                logger.debug(
                    "breaking:  Detected excluded utterance %s -> %s",
                    conversation.user_utterance,
                    text,
                )
                break

            logger.debug("- %d %s %s", idx, conversation.user_utterance, text)
            if parent:
                child_nodes = _get_utterance_lookup_table(parent)

            show_kids = str(child_nodes.keys()) if len(child_nodes.keys()) < 4 else ""
            logger.debug(
                f"-- Searching among {len(child_nodes.keys())} nodes. %s", show_kids
            )
            node_utterance = child_nodes.get(text)

            if node_utterance:
                node = node_utterance.node
                if not node.active:
                    logger.debug(f"This node ({node.id}) has been marked as inactive.")
                    break
                logger.debug(
                    "--- Found existing node node_id: %s, node_utterance_id: %s",
                    node.id,
                    node_utterance.id,
                )

                if (
                    not conversation.processed
                    or conversation.processed == processed_time
                ):
                    node.visited_count += 1
                    logger.debug(
                        "---- Increase count for node %s (%d)",
                        node.id,
                        node.visited_count,
                    )

                    db_session.add(node)
                    conversation.processed = processed_time
                    db_session.add(conversation)

                parent = None
                for child in node.children:
                    for utterance in child.utterances:
                        if utterance.id == conversation.graphsearch_matched_utterance_id or normalize_text(
                            utterance.utterance_text
                        ) == normalize_text(
                            conversation.system_utterance
                        ):
                            logger.debug(
                                "----- Found system response: %s",
                                utterance.utterance_text,
                            )
                            if (
                                not conversation.processed
                                or conversation.processed == processed_time
                            ):
                                logger.debug(
                                    "----- Increase count for child node %s (%d)",
                                    child.id,
                                    child.visited_count,
                                )
                                child.visited_count += 1
                                db_session.add(child)
                            parent = child
                    if parent:
                        break
                if not parent:
                    logger.debug(
                        "---- No system response found: %s",
                        conversation.system_utterance,
                    )
                    break
            else:
                logger.debug("--- No existing node found")
                if (
                    not conversation.processed
                    or conversation.processed == processed_time
                ):
                    if parent:
                        logger.debug(
                            "--- Adding new node %s", conversation.user_utterance
                        )
                        node = create_new_node(
                            [conversation.user_utterance],
                            parent_id=parent.id if parent else None,
                            source="automatic_population",
                        )
                    else:
                        # root_node_utterances[text] = node.node_utterances[0]
                        try:
                            logger.debug(
                                "--- New potential root node: "
                                + conversation.user_utterance
                            )

                            with open(file_name, "a") as storage_file:
                                logger.debug(
                                    "---XXXXXXXXXXXXXXXXXXXXXXX: Adding first utterance to "
                                    + file_name
                                )
                                storage_file.write(conversation.user_utterance + "\n")
                        except:
                            logger.debug("--- File not found")
                    conversation.processed = processed_time
                break

    if not automate:
        response = input("Populate? N/y\n")
        if response.lower() == "y":
            db_session.commit()
            logger.debug("committing!")
        else:
            db_session.rollback()
    else:
        db_session.commit()


def _get_utterance_lookup_table(parent):
    nodes = db_session.query(Node).filter(Node.parent == parent).all()
    node_utterances = {}
    for node in nodes:
        for node_utterance in node.node_utterances:
            db_session.add(node_utterance)
            text = normalize_text(node_utterance.utterance.utterance_text)
            if not node_utterances.get(text):
                node_utterances[text] = node_utterance
            elif node_utterances.get(text).node.id != node.id:
                other_node = node_utterances.get(text).node

                node_child_size = get_full_child_count(node)
                other_node_child_size = get_full_child_count(other_node)

                if node_child_size > other_node_child_size:
                    logger.info(f"merging.. {node.id} <- {other_node.id}")
                    merge_nodes(node.id, other_node.id, True)
                else:
                    logger.info(f"merging.. {other_node.id} <- {node.id}")
                    merge_nodes(other_node.id, node.id, True)

    return node_utterances


def populate(conversation_id=None, automate=False):
    root_node_utterances = _get_utterance_lookup_table(None)
    global file_name
    file_name = (
        FANTOM_WORKDIR + "/fantom_util/fantom_util/graph_tools/possible_root_nodes.txt"
    )
    os.system("aws s3 cp s3://SOME_AWS_BUCKET_URL/possible_root_nodes.txt " + file_name)
    if not conversation_id:
        conversation_ids = (
            db_session.query(Conversation.conversation_id)
            .filter(Conversation.conversation_id != None)
            .distinct(Conversation.conversation_id)
            .all()
        )
        if automate:
            for conversation_id in tqdm(conversation_ids):
                process_conversation(conversation_id, root_node_utterances, automate)
        else:
            stop = False
            while not stop:
                conversation_id = random.choice(conversation_ids)[0]
                process_conversation(conversation_id, root_node_utterances, automate)
                response = input("Continue? Y/n\n")
                if response.lower() == "n":
                    stop = True
    else:
        process_conversation(conversation_id, root_node_utterances, False)

    os.system(
        "aws s3 cp " + file_name + " s3://SOME_AWS_BUCKET_URL/possible_root_nodes.txt"
    )


if __name__ == "__main__":
    populate()
