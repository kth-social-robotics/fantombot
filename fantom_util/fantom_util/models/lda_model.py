from collections import defaultdict
import atexit
import subprocess
import os
from tempfile import NamedTemporaryFile
import numpy as np
from fantom_util.models.model import Model

from fantom_util.file_io_util import *
from fantom_util.constants import LDA_SIZE, LDA_BIN, DATA_DIR
from fantom_util.feature_extraction.specifications import CLEAN_TEXT


class LDAModel(Model):

    __name__ = "lda_model"

    popen_arguments = [
        LDA_BIN,
        "-inf",
        "-dir",
        f"{DATA_DIR}/lda_model",
        "-model",
        "model-final",
        "-niters",
        "1",
        "-twords",
        "20",
    ]

    features = {CLEAN_TEXT["name"]: CLEAN_TEXT["steps"]}

    def __init__(self):
        self.model = None

    def prepare_data(self):
        """Provide a filename for lda training"""
        data = ""

        return data

    def build(self):

        return

    def train(self):
        # prepare data
        with NamedTemporaryFile(
            mode="w", dir=f"{DATA_DIR}/lda_model", delete=True
        ) as tmpf:
            from fantom_util.data_handler import DataHandler
            from fantom_util.misc import gen_feature_dict

            features = gen_feature_dict(CLEAN_TEXT)
            dh = DataHandler(features)
            utterances = []
            dialogs = {}
            for key in dh.node_lookup_table[None]:
                dialogs[key] = [] + [key]
            for key in dialogs.keys():
                stack = []
                if key in dh.node_lookup_table.keys():
                    stack = stack + dh.node_lookup_table[key]
                while stack != []:
                    dialogs[key] = dialogs[key] + [stack[0]]
                    if stack[0] in dh.node_lookup_table.keys():
                        stack = stack + dh.node_lookup_table[stack[0]]
                    del stack[0]
            dialogs_key = {}
            for key in dialogs.keys():
                dialogs_key[key] = []
                for uttID in dialogs[key]:
                    dialogs_key[key] = dialogs_key[key] + dh.node_utts[uttID]

            for key in dialogs_key.keys():
                temp_utt = ""
                for uttID in dialogs_key[key]:
                    temp_utt = temp_utt + dh.id_utt[uttID]["clean_text"] + " "
                utterances.append(temp_utt)

            count = 0
            for utt in utterances:
                if utt.replace(" ", "") != "":
                    count = count + 1
            tmpf.write(str(count))
            tmpf.flush()
            tmpf.write("\n")
            tmpf.flush()
            for utt in utterances:
                if utt.replace(" ", "") != "":
                    tmpf.write(utt)
                    tmpf.write("\n")
                    tmpf.flush()
            lda_arguments = [
                LDA_BIN,
                "-est",
                "-alpha",
                "0.5",
                "-beta",
                "0.1",
                "-ntopics",
                str(LDA_SIZE),
                "-niters",
                "1000",
                "-savestep",
                "100",
                "-twords",
                "20",
                "-dfile",
                f"{tmpf.name}",
            ]
            p = subprocess.Popen(lda_arguments)
            p.wait()

    def save_model(self):
        return pickle_to_bucket(self.model, "SOME_AWS_BUCKET", "lda_model")

    def load_model(self):
        lda_arguments = [
            LDA_BIN,
            "-inf",
            "-dir",
            f"{DATA_DIR}/lda_model",
            "-model",
            "model-final",
            "-niters",
            "1",
            "-twords",
            "20",
        ]
        self.model = subprocess.Popen(
            lda_arguments, stdout=subprocess.PIPE, stdin=subprocess.PIPE
        )
        atexit.register(self.terminateProcess)
        return self.model

    def infer(self, utterance):
        """Return an LDA probability distribution."""
        if utterance == "":
            return list(1 / LDA_SIZE * np.ones(LDA_SIZE))
        utterance = "{}\n".format(utterance).encode("utf-8")
        self.model.stdin.write(utterance)
        self.model.stdin.flush()

        return list(
            map(float, self.model.stdout.readline().decode("utf-8").strip().split(" "))
        )

    def terminateProcess(self):
        self.model.terminate()
