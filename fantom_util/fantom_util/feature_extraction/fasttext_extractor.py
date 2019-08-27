import logging
from multiprocessing import Process

from fantom_util.constants import DATA_DIR, FASTTEXT_CALCULATOR_PORT
from fantom_util.feature_extraction.nlp import preload_model
from fantom_util.misc import normalize_vector

logger = logging.getLogger(__name__)


def fasttext_model():
    import zmq

    context = zmq.Context()
    s = context.socket(zmq.REQ)
    s.connect(f"tcp://localhost:{FASTTEXT_CALCULATOR_PORT}")
    return s


@preload_model(fasttext_model)
def word_embeddings(fasttext_socket, tokens):
    """Calculate FastText word embeddings for each token."""
    if not tokens:
        return None
    fasttext_socket.send_pyobj(tokens)
    return fasttext_socket.recv_pyobj()


@preload_model(fasttext_model)
def sentence_embeddings(model, text):
    """Calculate FastText sentence embeddings for each token."""
    if not text:
        return None
    return model.get_sentence_vector(text)


calculate_fasttext_started = False


def start_calculate_fasttext_process():
    global calculate_fasttext_started
    if not calculate_fasttext_started:
        calculate_fasttext_started = True
        p = Process(target=calculate_fasttext)
        p.daemon = True
        p.start()


def calculate_fasttext():
    import zmq
    from fastText import load_model
    context = zmq.Context()
    s = context.socket(zmq.REP)
    s.bind(f"tcp://*:{FASTTEXT_CALCULATOR_PORT}")
    logger.info("Started fasttext server at port %s", FASTTEXT_CALCULATOR_PORT)
    logger.info(
        "about to load model from: %s", f"{DATA_DIR}/wiki-news-300d-1M-subword.bin"
    )
    model = load_model(f"{DATA_DIR}/wiki-news-300d-1M-subword.bin")
    logger.info("Loaded fasttext model. Waiting for jobs")
    while True:
        tokens = s.recv_pyobj()
        logger.debug("tokens received %s", tokens)
        s.send_pyobj(
            [normalize_vector(model.get_word_vector(token)) for token in tokens]
        )

