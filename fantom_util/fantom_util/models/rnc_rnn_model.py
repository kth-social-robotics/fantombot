from __future__ import print_function, unicode_literals
import spacy

from keras.models import Model, Sequential, load_model
from keras.layers import Input, concatenate, Embedding, Dense, LSTM, Activation, Dropout
import numpy as np

from fantom_util.file_io_util import file_from_s3


class RootNodeClassifierRNN:
    def __init__(
        self,
        embed_dim1=10,
        embed_dim2=5,
        hidden_dim1=5,
        hidden_dim2=10,
        hidden_dim3=3,
        dropout_rate1=0.2,
        dropout_rate2=0.5,
    ):

        weights_path = "weights_rnc_rnn.hdf5"
        # Embedding
        self.input1 = Input(shape=(None,), name="input1")
        self.embeddings1 = Embedding(19, embed_dim1, mask_zero=True)(self.input1)
        self.embeddings1drop = Dropout(dropout_rate1)(self.embeddings1)
        self.lstm = LSTM(
            hidden_dim1,
            dropout=dropout_rate1,
            recurrent_dropout=dropout_rate1,
            return_sequences=False,
        )(self.embeddings1drop)

        # Special data
        self.input2 = Input(shape=(14,), name="input2")
        self.input2drop = Dropout(dropout_rate1)(self.input2)
        self.embeddings2 = Dense(embed_dim2)(self.input2drop)
        self.embeddings2drop = Dropout(dropout_rate1)(self.embeddings2)

        # Concatenating the embedded vectors
        self.concatenated = concatenate([self.lstm, self.embeddings2drop])
        self.processing1 = Dense(hidden_dim2, activation="relu")(self.concatenated)
        self.processing1drop = Dropout(dropout_rate1)(self.processing1)

        self.processing2 = Dense(hidden_dim3, activation="relu")(self.processing1drop)
        self.processing2drop = Dropout(dropout_rate2)(self.processing2)

        self.predictions = Dense(1, activation="sigmoid")(self.processing2drop)
        self.model = Model(inputs=[self.input1, self.input2], outputs=self.predictions)
        try:
            file_from_s3("fantom-model-bucket", weights_path, weights_path)
            self.model.load_weights(weights_path)
        except:
            print("Coulfn't find pretrained weights")
        self.model.compile(
            optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"]
        )
        self.nlp = spacy.load("en_core_web_lg")
        # self.nlp = spacy_model()

    def retrain(self, x, y):
        callbacks = self.model.fit(
            x, y, batch_size=32, epochs=500, verbose=1, validation_split=0.20
        )
        return callbacks

    def predict_list(self, utterances):
        return self.model.predict(x=self.preprocess_data(utterances))

    def predict_string(self, utterance):
        return float(self.predict_list([utterance])[0][0])

    def preprocess_data(self, utterances):
        max_len = 20
        nr_of_samples = len(utterances)
        min_tok_pos = 83
        max_tok_pos = 100

        X_data = np.zeros((nr_of_samples, max_len))
        dim1 = max_tok_pos - min_tok_pos + 2

        special_list = [
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

        X_additional_data = np.zeros((nr_of_samples, len(special_list) + 2))

        # X_data
        for sample_nr in range(len(utterances)):
            line_doc = self.nlp(utterances[sample_nr])
            if "tell me" == (str(utterances[sample_nr])[0:7]):
                X_additional_data[sample_nr, -2] += 1.0
            for token in line_doc:
                for list_nr in range(len(special_list)):
                    if token.orth in special_list[list_nr]:
                        X_additional_data[sample_nr, list_nr] += 1.0
                    if not token.is_stop:
                        X_additional_data[sample_nr, -1] += 1.0
            tok_nr = 0
            for token in line_doc:
                try:
                    # print(token.text)
                    # print(token.text, token.pos, token.pos_)
                    X_data[sample_nr, tok_nr] = token.pos - min_tok_pos + 1
                    tok_nr += 1
                except:
                    pass
        return [X_data, X_additional_data]


def main():
    rnc_rnn = RootNodeClassifierRNN()
    print(
        rnc_rnn.predict_list(
            ["hi", "Let's chat about football", "my name is trevor", "do you like him"]
        )
    )
    print((rnc_rnn.predict_string("I would like to talk about chickens")))


if __name__ == "__main__":
    main()
