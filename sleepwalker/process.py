from logging.handlers import TimedRotatingFileHandler

from fantom_util.constants import FANTOM_WORKDIR, DATA_DIR
from fantom_util.graph_tools.anonymization import update_amazon_anonymous
from fantom_util.graph_tools.auto_phrase_beginning_merging import merge_multiple_phrase_beginning_lists
from fantom_util.graph_tools.auto_synonym_merging import merge_multiple_synonym_lists
from fantom_util.graph_tools.populate import populate
from fantom_util.models.graph_search_model import GraphSearchModel
from fantom_util.models.named_entity_model import NamedEntityModel
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)
logger.addHandler(TimedRotatingFileHandler(f'{FANTOM_WORKDIR}/logs/sleepwalking.log', when='midnight'))
logger.setLevel(logging.INFO)

funcs = [
    ('update_amazon_anonymous', lambda: update_amazon_anonymous()),
    ('populate', lambda: populate(automate=True)),
    ('merge_multiple_synonym_lists', lambda: merge_multiple_synonym_lists()),
    ('merge_phrase_beginnings', lambda: merge_multiple_phrase_beginning_lists()),
    ('retrain LDA', lambda: print('skipping..')),
    ('find named enteties', lambda: print('skipping..')),
    ('NamedEntityModel', lambda: NamedEntityModel(stage='BETA').train(promote=True, fresh=True)),
    ('GraphSearchModel', lambda: GraphSearchModel(stage='BETA').train(promote=True, fresh=True)),
    ('recalculate probable merges', lambda: print('skipping..'))
]

for name, func in tqdm(funcs):
    logger.info('Now running: %s', name)
    func()
