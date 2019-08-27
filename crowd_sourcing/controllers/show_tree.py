from fantom_util.database import db_session
from fantom_util.database.models import Node
from random import shuffle


def nodes():
    nodes = db_session.query(Node).filter(Node.parent_id.is_(None), Node.active.is_(True))
    count = 0
    allNode = []
    returnNode = {}
    for node in nodes:
        allNode.append(node)
    shuffle(allNode)
    for node in allNode:
        utt = []
        tree_nodes = []
        stack = [node]
        while stack:
            cur_node = stack[0]
            stack = stack[1:]
            tree_nodes.append(cur_node)
            for child in cur_node.children:
                stack.append(child)
        for el in tree_nodes:
            for utterances in el.utterances:
                utt.append(utterances.utterance_text)
        returnNode[count] = utt
        count = count+1
        if count == 30:
            break
    return returnNode
