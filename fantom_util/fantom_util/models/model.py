from abc import ABC, abstractmethod
from datetime import datetime
from fantom_util.file_io_util import *


class Model(ABC):

    def __init__(self, stage=None):
        self.model = None
        self.stage = stage
        self.dh = None
    
    @abstractmethod
    def prepare_data(self):
        """get and prepare your training data"""
        pass

    @abstractmethod
    def build(self):
        """Build or train from scratch"""
        pass
        
    def train(self, promote=False, fresh=False):
        """Use fresh data from prepare, build and save."""
        self.prepare_data()
        self.build(fresh)
        return self.save_model(promote)

    def save_model(self, promote=False):
        """Save to s3 bucket as pickle."""
        version = datetime.now().replace(microsecond=0).isoformat()
        if promote:
            pickle_to_bucket(self.model, 'SOME_AWS_BUCKET', self._build_model_path('latest'))

        return pickle_to_bucket(self.model, 'SOME_AWS_BUCKET', self._build_model_path(version))

    def _build_model_path(self, version=''):
        """Generate a model file path"""
        name = f'models/{self.__name__}'

        if self.stage:
            name += '-' + self.stage

        if version:
            name += '-' + version

        return name

    def load_model(self, version='latest'):
        """Load from s3 bucket pickle into instance model variable."""

        self.model = unpickle_from_bucket('SOME_AWS_BUCKET', self._build_model_path(version))
