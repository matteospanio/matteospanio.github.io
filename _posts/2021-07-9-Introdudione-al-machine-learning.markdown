---
layout: post
title: "Il cervello e la macchina"
date: 2021-07-9 11:42:27 +0200
image: /assets/images/Apple-fruit.jpg
lang: it
ref: machine-learning
categories: AI machinelearning
---

> Le macchine "imparano"? E possono pensare? E cosa centra tutto ciò con il machine learning?

Immaginiamo una mela e disegnamola.

Come abbiamo fatto?

Cos'è successo nel nostro cervello per renderci in grado di rievocare un'immagine, capire che è quella giusta e poi riprodurla? Probabilmente da qualche parte nella testa c'è un posto dove vengono immagazzinate le immagini della categoria astratta "mela".

![diz]({{ site.url }}/assets/images/diz.png)

Supponiamo di avere delle categorie astratte in testa e che queste diano vita al fenomeno della _noesis_ platonica, ossia il riconoscimento degli oggetti esterni attraverso il confronto con idee che li rappresentino.

Se così fosse, ci potremmo immaginare di avere un cervello che si comporta in maniera simile al computer: i circuiti addetti a memorizzare (i flip-flop) immagazzinano i valori dei pixel che rappresentano l'immagine e per accedervi bisogna conscere l'indirizzo di memoria a cui si trovano. Nell'analogia col cervello umano i flip-flop potrebbero essere i neuroni e per trovare gli indirizzi di questi neuroni potremmo immaginare che il processo di ricerca avvenga attraverso un'associazione chiave-valore. Una volta trovato il punto nel cervello dove inizia l'immagine della mela la iniziamo a 'leggere' e la visualizziamo nella mente...

Cambiamo il problema ora: supponiamo che qualcuno ci faccia vedere solo un piccolo frammento di buccia di mela, nonostante lo stimolo sia diverso probabilmente saremo in grado di immaginare comunque una mela del colore della buccia. Allora non è così semplice come avevamo immaginato!

#### Come sono fatte le nostre idee allora per essere così versatili a riconoscere stimoli di natura diversa?

Lo studioso _Frank Rosenblatt_ ha provato a fornire un modello per comprendere il fenomeno appena descritto teorizzando che nel cervello potrebbero essere memorizzate le **relazioni** che le immagini hanno con gli stimoli che le generano, anzichè le immagini stesse.

Intuitivamente vuol dire che non abbiamo da nessuna parte l'immagine della mela, ma ci sarebbero una serie di sinapsi che si attivano quando ci viene mostrato qualcosa che riguardi le mele e che tali connessioni neurali generino sinteticamente una mela. Queso è il modello che sta alla base della memoria associativa.

## Machine Learning

A questo punto bisogna chiarire com'è fatto e come funziona un neurone.

Il neurone è una cellula specializzata che svolge un compito molto semplice: riceve dei segnali, li elabora e li rispedisce. Per esempio i nervi uditivi ricevono dalle cellule ciliate l'input attraverso i dendriti, il segnale viene elaborato dalle cellule e poi trasmesso attraverso l'assone, in questo caso questi neuroni formano il nervo acustivo e vanno direttamente a comunicare col cervello.

Le reti neurali prendono spunto dal modello umano e tentano di copiarne sia la struttura che il comportamento: i neuroni vengono quindi chiamati percettroni e trattati come oggetti matematici che collegati tra loro formano delle reti neurali.

![neurone_vs_percettrone.png]({{ site.url }}/assets/images/neurone_vs_percettrone.png)

In questo caso si fa apprezzare la concisa notazione matematica per descrivere in maniera generale una rete neurale:

\\[y = \phi(\sum_{i=1}^n w_i x_i + b) = \phi(W^T x + b)\\]

Quindi come fa un neurone a imparare?

Le connessioni tra i neuroni non sono stabilite in maniera definitiva: nell'arco del tempo possono cambiare sia in numero che in intensità. Questa plasticità è lo stesso meccanismo che permette al cervello di recuperare alcune funzionalità dopo un trauma o un incidente.

Ad ogni modo nel contesto dell'apprendimento ad un dato episodio corrispondono degli input per i neuroni che sono collegati a loro volta ad altri neuroni. Se al termine dell'episodio le aspettative del cervello sono state soddisfatte, le sinapsi attivate in quell'istante vengono rafforzate, se invece i segnali nervosi non soddisfano le aspettative le sinapsi vengono disinibite.

Facciamo un esempio pratico: quando un bambino di pochi mesi tenta di afferrare per la prima volta un oggetto che non conosce non sa ciò che potrebbe succedere, sa solo muovere le mani e le braccia, quando il bambino decide di muoversi e prendere l'oggetto attiva certi neuroni, se riesce nell'impresa le sinapsi attivate si rafforzeranno, se invece qualcosa va storto il cervello rimanda indietro un segnale di risposta che "ricalibra" i collegamenti tra i neuroni[^1].

### Footnotes

[^1]: Nel campo del machine learning il processo di input è detto _forward propagation_, mentre quello di risposta del cervello è chiamato _backward propagation_.
