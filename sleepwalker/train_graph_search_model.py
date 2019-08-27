import sys

import boto
from fantom_util.models.graph_search_model import GraphSearchModel

if sys.argv[1].lower() == 'beta':
    gsm = GraphSearchModel(stage='BETA')
    gsm.train(promote=True)
elif sys.argv[1].lower() == 'prod':
    s3 = boto.connect_s3()
    bucket = s3.lookup('fantom-util')
    key = bucket.lookup('models/graph_search_model-BETA-latest.pickle')
    key.copy('fantom-util', 'models/graph_search_model-PROD-latest.pickle', preserve_acl=True)
