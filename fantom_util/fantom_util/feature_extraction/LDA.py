from fantom_util.feature_extraction.nlp import preload_model


def lda_model():
    from fantom_util.models.lda_model import LDAModel

    model = LDAModel()
    model.load_model()
    model.infer("start")
    return model


@preload_model(lda_model)
def lda(model, text):
    """Calculate an LDA probability distribution."""
    if not text:
        return None
    return model.infer(text)
