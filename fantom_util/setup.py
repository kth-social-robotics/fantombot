#!/usr/bin/env python

from setuptools import setup, find_packages

#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='Fantom Util',
    install_requires=[
        'python-dateutil<2.7.0,>=2.1',
        'pandas',
        'progressbar2',
        'numpy',
        'psycopg2-binary',
        'spacy',
        'boto3',
        'gensim',
        'argh',
        'sqlalchemy',
        'sqlalchemy_utils',
        'sqlalchemy-repr',
        'sqlparse',
        'pySqsListener',
        'tabulate',
        'tqdm',
        'imdbpy',
        'titlecase',
        'Unidecode'
    ],
    python_requires='>=3',
    version='1.14.1',
    description='The fantom utilities!',
    author='Team Fantom',
    author_email='pjjonell@kth.se',
    scripts=[
        'fantom_util/bin/fantom_toolbelt',
        'fantom_util/bin/model_reloader',
        'fantom_util/bin/test_scoring',
        'fantom_util/bin/fasttext_calculator'
    ],
    packages=find_packages(),
)
