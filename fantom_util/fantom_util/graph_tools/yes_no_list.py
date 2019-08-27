from fantom_util.database import db_session
from fantom_util.database.models import Node
import fantom_util.feature_extraction.yes_no_question as yn



def return_yes_no_nodes():
	nodes = db_session.query(Node).filter(Node.is_user == False).all()
	yes_no_nodes = []
	for node in nodes:
		add = False
		for utt in node.utterances:
			if(yn.yes_no_question(utt.utterance_text)):
				add = True
		if add:
			yes_no_nodes = yes_no_nodes + [node]

	return yes_no_nodes
Î