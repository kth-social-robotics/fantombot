import re
from fantom_util.constants import EXCLUDED_UTTERANCES
from fantom_util.database import db_session
from fantom_util.database.models import Utterance
from fantom_util.file_io_util import list_files_in_s3_bucket_dir, file_from_s3
import os
from fantom_util.misc import normalize_text

PATH_TO_UTTERANCES = 'anonymous_utterances'
BUCKET_NAME = 'AWS_SOME_BUCKET'
DIR_ON_S3 = 'AWS_SOME_DIR'


def get_filename(path):
    return path.rsplit('/', 1)[1]

if not os.path.exists(PATH_TO_UTTERANCES):
    os.makedirs(PATH_TO_UTTERANCES)

files_to_process = []
for file in list_files_in_s3_bucket_dir(BUCKET_NAME, DIR_ON_S3):
    file_name = get_filename(file.key)
    file_from_s3(BUCKET_NAME, file.key, f'{PATH_TO_UTTERANCES}/{file_name}.tmp')
    files_to_process.append(f'{PATH_TO_UTTERANCES}/{file_name}.tmp')

anonymous_utterances = []
for file_path in files_to_process:
    with open(file_path, 'r') as f:
        for line in f.readlines():
            if re.search(EXCLUDED_UTTERANCES, normalize_text(line)):
                print('removed utterance', line.strip())
                continue
            anonymous_utterances.append(line.strip().lower())
anonymous_utterances = set(anonymous_utterances)
print('-----', len(anonymous_utterances))
utterances = db_session.query(Utterance).all()


for utterance in utterances:
    if utterance.utterance_text in anonymous_utterances:
        if not utterance.amazon_anonymous:
            print('setting anonymous:', utterance.utterance_text)
            utterance.amazon_anonymous = True
        anonymous_utterances.remove(utterance.utterance_text)

print('-----', len(anonymous_utterances), anonymous_utterances)
for new_utterance in anonymous_utterances:
    db_session.add(Utterance(utterance_text=new_utterance, amazon_anonymous=True))

db_session.commit()
for file_path in files_to_process:
    os.rename(file_path, file_path[:-4])