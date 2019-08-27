import sys
from fantom_util.models.named_entity_model import NamedEntityModel

if sys.argv[1].lower() == 'beta':
    nem = NamedEntityModel(stage='BETA')
    nem.train(promote=True, fresh=True)
elif sys.argv[1].lower() == 'prod':
    nem = NamedEntityModel(stage='PROD')
    nem.train(promote=True, fresh=True)
