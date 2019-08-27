from fantom_util.database import db_session
from fantom_util.database.models import Node, NodeUtterance
from sqlalchemy import or_
from sqlalchemy.orm import subqueryload


def get_graph():
    nodes = db_session.query(Node).filter(Node.active.is_(True)).all()

    max_visits = 0
    for node in nodes:
        max_visits = max(max_visits, node.visited_count)

    output = ['digraph {']
    # For each node
    for node in nodes:
        text = '<br/>'.join(['- {} (nu: {}, u: {})'.format(x.utterance.utterance_text.replace("'", "\\'").replace('"', '\\"'), x.id, x.utterance.id) for x in node.node_utterances])

        # set the color to grey if it is a user utterance otherwise black
        color = '#000000' if node.is_user else '#00ff00'

        thickness = max(1, 4 * node.visited_count/max_visits)

        # print the node with it's properties
        output.append(f'{node.id}[label=<<b>{node.id}</b> ({node.visited_count})<br/>{text}>,color="{color}",penwidth={thickness}];')

        # if the root node is not this nodes parent
        if node.parent_id:
            # print it with a link to it's parent
            output.append(f'{node.parent_id} -> {node.id};')

    output.append('}')
    return ' '.join(output)


def get_nodes(parent_id=None, visited_count_limit=1):
    visisted_count_limit_list = []
    if not parent_id:
        visisted_count_limit_list.append(or_(Node.visited_count > visited_count_limit, Node.child_count > 0))
    return db_session\
        .query(Node) \
        .options(subqueryload(Node.node_utterances).subqueryload(NodeUtterance.incoherent_node_utterance_statuses), subqueryload(Node.utterances))\
        .filter(Node.parent_id == parent_id, Node.active.is_(True), *visisted_count_limit_list)\
        .order_by(Node.visited_count.desc())\
        .all()


def get_parents(node_id):
    if not node_id:
        return []

    node = db_session.query(Node).get(node_id)
    nodes = db_session.query(Node).filter(Node.id.in_(node.path), Node.active.is_(True)).order_by(Node.path_length).all()
    return nodes


def get_current_node(node_id):
    if not node_id:
        return None
    return db_session.query(Node).get(node_id)