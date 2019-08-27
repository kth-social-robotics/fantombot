from fantom_util.models.model import Model
from fantom_util.models.train_movie_data import create_database, gen_movies
from fantom_util.models.train_named_entity_data import full_scrape
import logging

logger = logging.getLogger(__name__)
moviesgenres = [
    "sci-fi",
    "science fiction",
    "comedy",
    "horror",
    "drama",
    "animated",
    "cartoon",
    "anime",
    "thriller",
    "rom com",
    "romantic",
    "romantic comedy",
    "thriller",
    "western",
    "action",
    "fantasy",
    "romance",
    "superhero",
]

literaturegenres = [
    "fantasy",
    "sci-fi",
    "science fiction",
    "comedy",
    "horror",
    "romantic",
    "thriller",
    "detective",
    "romance",
    "comic",
    "young adult",
    "children",
    "fiction",
    "non fiction",
    "historical",
    "historical fiction",
    "mystery",
    "adventure",
    "true crime",
    "crime",
]
musicgenres = [
    "pop",
    "country",
    "rap",
    "hip hop",
    "classical",
    "funk",
    "rock",
    "classic rock",
    "jazz",
    "blues",
    "rock and roll",
    "k pop",
    "heavy metal",
    "christian",
    "alternative",
    "indie rock",
    "soft rock",
    "electronic",
    "techno",
    "dubstep",
    "oldies",
    "edm",
]


class NamedEntityModel(Model):
    __name__ = "named_entity_model"
    categories = ["movies", "musicians", "bands", "books", "authors"]

    def prepare_data(self):
        return

    def build(self, fresh=False):
        if fresh:
            self.model = {}
            for category in self.categories:
                self.model.update(full_scrape(category))
            self.model["movies_genre"] = moviesgenres
            self.model["moviesgenre"] = moviesgenres
            self.model["literaturegenres"] = literaturegenres
            self.model["musicgenres"] = musicgenres
            return
        else:
            logger.info("Only fresh build implemented")
            return

    def infer(self, named_entity):
        return self.model.get(named_entity)

