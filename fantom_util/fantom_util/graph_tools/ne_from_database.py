from fantom_util.models.wptools_scraper import create_database
from fantom_util.feature_extraction.named_entities import named_entities_model
from fantom_util.database import db_session
from fantom_util.database.models import Conversation, Node
from sqlalchemy.orm import joinedload
from fantom_util.feature_extraction.named_entities import tagged_text, named_entities
from fantom_util.graph_tools.node_tools import create_new_node

from tqdm import tqdm

categories = ["movies", "musicians", "bands", "authors", "books"]


def getting_ne(ne_list):
    ne = []
    for text in ne_list:
        text = text[0]
        # print(f'stringified text {text}')
        if "," in text:
            entities = text.split(",")
        else:
            entities = [text]
        for entity in entities:
            ne.append(entity.split("-")[1])
    ne = list(set(ne))
    return ne


def create_tagged_children(children, node_id):
    test_children_utts = [
        "<movies_0>",
        "<musicians_0>",
        "<bands_0>",
        "<authors_0>",
        "<books_0>",
    ]
    candidates = {}

    for child in children:
        for utt in child.utterances:
            info = named_entities(utt.utterance_text, test_children_utts)
            if info:
                tagged = tagged_text(utt.utterance_text, info)
                if tagged in candidates.keys():
                    candidates[tagged] += 1
                else:
                    candidates[tagged] = 1
    filtered = [key for key in candidates.keys() if candidates[key] > 3]

    for child in children:
        for index, utt in enumerate(child.utterances):
            if utt.utterance_text in filtered:
                filtered.pop(index)

    for utt in filtered:
        print(f"Creating new node with parent id {node_id} and utterance {utt}")
        create_new_node(
            utt,
            source="automatic_tagged",
            parent_id=node_id,
            commit=True,
            species="tagged",
        )
    return f"Done creating tagged nodes for node {node_id}"


def automatic_tagged_nodes():
    nodes = db_session.query(Node).all()
    for node in tqdm(nodes):
        if not node.is_user:
            create_tagged_children(node.children, node.id)
    return "Automatic creation of tagged nodes finished"


print(automatic_tagged_nodes())
