# Fantom

This repository contains the code and data used for the analysis in the paper "Crowdsourcing a Self-Evolving Dialog Graph", presented at the first installment of the conference on Conversational User Interfaces (CUI) 2019. Every piece of code and data used is included with the exception of the 200 utterance pairs of alexa-user dialogue, as these are not eligble for sharing. These contents can be found in the Analysis directory, as seen below.

Also included is the code that was developed by Team Fantom during the 2018 Alexa Prize. This includes the code for crowdsourcing and the graph structure presented in the CUI paper.

Below is a brief description of the contents.

### analysis
Contains: corpora, the processed data used for analysis; raw_corpora, the unprocessed data used for analysis; extractors, the code used to process raw_corpora; and evaluation, the code used to generate and collect results from the experiment interface.

### crowdsourcing
During the process of the Alexa Prize a crowdsourcing interface was developed and installed to collect dialogue data. Included in this folder is the code for the web interface, mechanical turk and general database communication regarding the data collecting process.

### fantom-util
The majority of this directory contains all code related to development and maintaining of the graph. Graph search, a dialogue manager built on top of the graph is also included.

### sleep-walker
The contents of the sleep-walker is scripts than ran every night to update the graph, graph search and NER-models.

### Publications
[Crowdsourcing a Self-Evolving Dialog Graph](https://dl.acm.org/citation.cfm?id=3342790) (CUI paper)

[Fantom: A Crowdsourced Social Chatbot using an
Evolving Dialog Graph](https://m.media-amazon.com/images/G/01/mobile-apps/dex/alexa/alexaprize/assets/pdf/2018/Fantom.pdf) (Alexa Prize Paper, Team Fantom)