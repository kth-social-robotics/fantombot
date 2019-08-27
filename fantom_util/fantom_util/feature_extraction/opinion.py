import subprocess
from collections import defaultdict

from fantom_util.constants import DATA_DIR
from fantom_util.feature_extraction.nlp import preload_model

# jar_file_path = f'{DATA_DIR}/stanford'
# command = ['java', '-mx1g', '-cp',
#         f'{jar_file_path}/stanford-corenlp-3.9.1.jar:' +
#         f'{jar_file_path}/stanford-corenlp-3.9.1-models.jar:' +
#         f'{jar_file_path}/CoreNLP-to-HTML.xsl:' +
#         f'{jar_file_path}/slf4j-api.jar:' +
#         f'{jar_file_path}/slf4j-simple.jar:',
#         'edu.stanford.nlp.naturalli.OpenIE'
# ]
jar_file_path = f"{DATA_DIR}/openie"
command = [
    "java",
    "-mx4g",
    "-cp",
    f"{jar_file_path}/stanford-openie.jar:"
    + f"{jar_file_path}/stanford-openie-models.jar:"
    + f"{jar_file_path}/lib/*",
    "edu.stanford.nlp.naturalli.OpenIE",
    "-format",
    "ollie",
]


def openIE():
    return subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE)


@preload_model(openIE)
def opinion(model, text, user_attributes):

    keys = ["loves", "hates"]

    if not user_attributes:
        user_attributes = dict((key, []) for key in keys)

    if text:
        model.stdin.write(f"{text}\n".encode("utf-8"))
        model.stdin.flush()
        information = model.stdout.readline().decode("utf-8")
    else:
        return None
    # TODO: populate the user_attributes using infmation object

    return information


print(opinion("my favorite movie is jurrasic park", None))

