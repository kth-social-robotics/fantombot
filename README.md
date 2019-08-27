# Fantom
This repository contains code and data related to Team Fantom's involvement in the 2018 Alexa Prize Challenge. Some data and code is not eligble for sharing, and are as such not included in the repositry.

Below is a brief description of the contents.

### analysis
Contains the code and data used for the analysis in the paper "Crowdsourcing a Self-Evolving Dialog Graph", presented at the first installment of the conference on Conversational User Interfaces (CUI) 2019. Every piece of code and data used is included with the exception of the 200 utterance pairs of alexa-user dialogue, as these are not eligble for sharing. The directory specifically contains: corpora, the processed data used for analysis; raw_corpora, the unprocessed data used for analysis; extractors, the code used to process raw_corpora; and evaluation, the code used to generate and collect results from the experiment interface.

### crowdsourcing
During the process of the Alexa Prize a crowdsourcing interface was developed and installed to collect dialogue data. Included in this folder is the code for the web interface, mechanical turk and general database communication regarding the data collecting process.

### fantom-util
The majority of this directory contains all code related to development and maintaining of the graph. Graph search, a dialogue manager built on top of the graph is also included.

### sleep-walker
The contents of the sleep-walker are scripts than ran every night to update the graph, graph search and NER-models.

### Publications
[Crowdsourcing a Self-Evolving Dialog Graph](https://dl.acm.org/citation.cfm?id=3342790) (CUI paper)

[Fantom: A Crowdsourced Social Chatbot using an
Evolving Dialog Graph](https://m.media-amazon.com/images/G/01/mobile-apps/dex/alexa/alexaprize/assets/pdf/2018/Fantom.pdf) (Alexa Prize Paper, Team Fantom)