import numpy as np

from keras.models import Sequential, load_model
from keras.layers import Dense, Activation, Dropout
import spacy

# from fantom_util.feature_extraction.spacy_extractor import spacy_model
from fantom_util.file_io_util import file_from_s3

# from fantom_util.models import Model


class RootNodeClassifierMLP:
    def __init__(self):
        weights_path = "weights_rnc_mlp.hdf5"
        file_from_s3("SOME_AWS_BUCKET", weights_path, weights_path)
        self.special_list = [
            ["what", "who", "when", "how", "where"],
            ["why", "whether", "which"],
            ["yes", "no", "sure", "course"],
            ["about"],
            ["want", "wanna", "like", "love", "hate"],
            ["chat", "talk"],
            [
                "he",
                "she",
                "it",
                "them",
                "that",
                "this",
                "those",
                "us",
                "his",
                "her",
                "their",
            ],
            ["I", "you"],
            ["else", "another", "again", "change"],
            ["something"],
            ["stop"],
            ["hi", "hello"],
        ]
        self.min_tok_pos = 83
        self.max_tok_pos = 100

        self.nlp = spacy.load("en_core_web_lg")
        # self.nlp = spacy_model()
        self.data_width = 32

        self.model = Sequential()
        self.model.add(Dense(20, activation="relu", input_shape=(self.data_width,)))
        self.model.add(Dropout(0.5))
        self.model.add(Dense(20, activation="relu"))
        self.model.add(Dropout(0.5))
        self.model.add(Dense(1, activation="sigmoid"))
        self.model.load_weights(weights_path)
        self.model.compile(
            optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"]
        )

    def prepare_data(self, utterances):
        X_data = np.zeros((len(utterances), self.max_tok_pos - self.min_tok_pos + 2))
        Y_data = np.zeros(len(utterances))
        X_additional_data = np.zeros((len(utterances), len(self.special_list) + 1))
        # X_data
        for sample_nr in range(len(utterances)):
            line_doc = self.nlp(utterances[sample_nr])
            if "tell me" == str(utterances[sample_nr])[0:7]:
                X_additional_data[sample_nr, -2] += 1.0
            for token in line_doc:
                try:
                    X_data[sample_nr, token.pos - self.min_tok_pos] += 1.0
                    for list_nr in range(len(self.special_list)):
                        if token.orth in self.special_list[list_nr]:
                            X_additional_data[sample_nr, list_nr] += 1.0
                    if not token.is_stop:
                        X_additional_data[sample_nr, -1] += 1.0
                except:
                    pass
        X_data = np.concatenate((X_data, X_additional_data), axis=1)
        return X_data

    def predict_string(self, utterance):
        return float(self.predict_list([utterance])[0][0])

    def predict_list(self, list_of_utterances):
        return self.model.predict(x=self.prepare_data(list_of_utterances))


def main():
    rnc_mlp = RootNodeClassifierMLP()
    print(
        rnc_mlp.predict_list(
            ["hi", "Let's chat about football", "my name is trevor", "do you like him"]
        )
    )
    print((rnc_mlp.predict_string("I would like to talk about chickens")))


if __name__ == "__main__":
    main()
