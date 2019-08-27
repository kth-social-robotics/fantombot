from fantom_util.feature_extraction.nlp import preload_model


def sentiment_model():
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    model = SentimentIntensityAnalyzer()
    return model


@preload_model(sentiment_model)
def sentiment(model, text):
    if not text:
        return None
    return model.polarity_scores(text)
