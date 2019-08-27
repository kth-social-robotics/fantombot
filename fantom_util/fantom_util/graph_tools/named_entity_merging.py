# want to look through utterances of the children of this node, match them with movies in named entity model and
# merge those that are in there and don't have any children

from fantom_util.database import db_session
from fantom_util.database.models import Node
from fantom_util.feature_extraction.named_entities import named_entities_model
from sqlalchemy.orm import joinedload

# For testing NODE_ID = 649613
nem = named_entities_model()


def named_entity_merge(node_id):
    nodes = (
        db_session.query(Node)
        .options(joinedload(Node.utterances), joinedload(Node.node_utterances))
        .filter(Node.parent_id == node_id)
        .all()
    )
    to_merge = []
    categories = ["movies", "musicians", "bands"]

    for node in nodes:
        done = False
        if not node.children:
            for utterance in node.utterances:
                utterance_text = utterance.utterance_text
                # print(utterance_text)
                for category in categories:
                    for item in nem[category]:
                        if f" {item.lower()} " in f" {utterance_text} ":
                            print(f"found {item} in {utterance_text}")
                            to_merge.append(node)
                            done = True
                        if done:
                            break
                    if done:
                        break
                if done:
                    break
    return to_merge
