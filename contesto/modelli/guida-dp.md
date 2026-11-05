# Guida — Documento di Progettazione (DP)

Istruzioni per chi redige il DP di un'iniziativa (di norma Winston, `/dp <id>`).
Ricavate dall'esempio `contesto/esempi documento progettuale/138975 - Digital
Evolution - Comunicazione esiti preadvising al cliente.docx`.

## Cos'è e per chi

È il documento architetturale che Poste (DTO / ITASCE, architetti e
infrastruttura) usa per censire i sistemi applicativi impattati, i flussi fra
sistemi e le risorse infrastrutturali da allocare. Classificazione: "ad uso
interno" (il disclaimer è già nel template).

**Un DP per iniziativa.** È più corto e più tabellare della SF: la SF dice
cosa fa la soluzione, il DP dice **quali applicativi, quali flussi, quali
risorse**. Non ripete le regole funzionali: rimanda alla SF.

## Fonti, in ordine di autorità

1. `iniziative.yaml` e `iniziative/<id>/PUNTO.md` (decisioni datate).
2. La SF dell'iniziativa (`iniziative/<id>/documenti/SF_<id>_*.md`), se esiste:
   il DP deve essere coerente con la SF su nomi, flussi e sistemi.
3. `iniziative/<id>/analisi.md` e `iniziative/<id>/sviluppo/*.md`, per topic,
   persistenza, protocolli e frequenze.
4. `contesto/MICROSERVICE_TECHNICAL_BLUEPRINT.md` per lo stack standard dei ms
   `ce-` (Java/Spring Boot, OpenShift, Kafka, Helm), da riusare nel "Software".

In `sviluppo/` valgono le stesse regole della SF (vedi `guida-sf.md`, "Fonti"):
i `prompt-*.md` non sono fonti; a parità di tema vale la decisione datata più
recente. Al DP servono soprattutto i dati di deploy: namespace, risorse e
repliche nei `values.yaml` citati da assessment e rapporti. Riportali come
fatti solo se un documento li verifica; altrimenti scrivili come proposta.

## Struttura (obbligatoria, numerazione e titoli come l'esempio)

Copertina, ruoli (Redazione/Verifica/Approvazione), versioni, sommario e
disclaimer li genera il template dal front-matter: **non** vanno nel corpo.

```
# Architettura Applicativa
<prosa: scopo dell'iniziativa e come si inserisce nei processi esistenti>
## Business Architecture – <processo>
![Figura 1: Business Architecture – <processo>](...)
| Processo | Fase | Sistema Applicativo (AP) / Applicazione (PK) | Ruolo dell'Applicativo | Impatto Applicativo (S/N) | Applicativo esistente o nuovo |
Tabella 1: Business Architecture – <processo>
## Information System Architecture
<prosa: il flusso dei dati da sorgente a destinazione>
![Figura 2: Information System Architecture – <processo>](...)
| Flusso dati | Descrizione |
# Architettura Tecnica
## Application Technical Architecture
| Pacchetto Applicativo | Software | Versione | Layer Applicativo | Applicativo nuovo o esistente |
| Flusso dati | Protocollo | Origine | Destinazione | Tipologia | Frequenza | Frequenza di picco | Dimensione media dei messaggi | Dimensione massima dei messaggi | Flusso nuovo o esist. |
# Scheda HW
<prosa: cosa serve e cosa non si applica>
## Risorse on Prem
| on prem |       Tabella: Risorse on Prem (HW dedicato o Private Cloud)
| mainframe |     Tabella: Mainframe
| HW periferico | Tabella: HW Periferico
### Openshift
| Openshift |     Tabella: Openshift on Prem
## Risorse Cloud
| cloud IaaS |    Tabella: Risorse Cloud IaaS
### Openshift
| Openshift |     Tabella: Openshift Cloud
# Allegati
| Codice Documento | Nome |
```

### Cosa mettere in ogni sezione

- **Business Architecture**: una riga per sistema/applicazione coinvolto
  (topic Kafka e collezioni MongoDB no: stanno solo nella tabella pacchetti), con
  il formato `<Sistema> (AP-nnnnn) / <applicazione> (PK-nnnnn)`. Codici noti
  dall'esempio 138975: CE `AP-00988`, ce-dichiarato `PK-03089`, T&T2.0
  `AP-00960`, T&T repo `PK-03985`, Portali PCL `AP-01074`, MyPoste delivery
  business `PK-02750`. Per gli altri, e per ogni **nuovo** microservizio, il PK
  è `DA DEFINIRE`: non inventarlo. Includi anche i sistemi esterni (es. il
  partner) con il ruolo, l'impatto `N` e la dicitura "esterno". Sistemi solo
  consultati (es. F1, ce-rules): impatto `N`.
- **Information System Architecture**: i flussi numerati (Flusso dati 1, 2,
  …), nello stesso ordine della figura. Una riga = un passaggio di dati fra
  due sistemi o fra un sistema e un topic/DB.
- **Application Technical Architecture**:
  - tabella pacchetti: ogni microservizio o componente, Software
    (`Microservizio Java/Spring Boot`, `Topic Kafka`, `MongoDB`…), Versione
    (`1.0` per i nuovi; per topic, collezioni ed esistenti di versione ignota
    "Non applicabile" o `DA DEFINIRE`), Layer (`Application`, `Data`,
    `Integration`);
  - tabella flussi: stessi numeri della sezione precedente. Origine = chi
    avvia la comunicazione (il chiamante, o il produttore su un topic),
    Destinazione = chi la riceve. Protocollo (`https`,
    `Kafka`, `MongoDB`, `JDBC`), Tipologia `Sincrona`/`Asincrona`. Frequenze e
    dimensioni: valori noti o stime **dichiarate come stime** ("stima: …").
    Altrimenti `DA DEFINIRE`, mai celle vuote.
- **Scheda HW**: per i microservizi su OpenShift compila la tabella
  Openshift (on prem o cloud, secondo il cluster dell'iniziativa): una riga per
  ms e per ambiente (Sviluppo, Collaudo, Produzione), con namespace, pod e
  request/limit. Se non ci sono indicazioni di dimensionamento, proponi un
  valore minimo marcato "proposta" (es. request 250 millicore / 512 MB, limit
  1 core / 1024 MB, 1 pod) e apri un open point. Le tabelle che non si
  applicano (mainframe, HW periferico, IaaS) restano con una sola riga
  "Non applicabile". Se non è noto se il cluster è on prem o cloud, compila
  la tabella Openshift on prem, metti in cloud una riga che rimanda a quella
  e scrivi `DA DEFINIRE` la collocazione nella prosa del capitolo.
  Non riportare le frasi-istruzione del template ("Specificare nella colonna
  Ambiente…"): sono per chi compila, non per chi legge.
- **Allegati**: SF (con versione), drawio, ICD, swagger. Codice Documento =
  nome del file senza estensione, finché Poste non assegna codici `AL_…`.

Le tabelle della Scheda HW riprendono le colonne dell'esempio:

- Openshift: `| (AP/PK) | Ambiente | Nome Cluster | Tipologia cluster | Namespace | Gen | Request Core (millicore) | Request Ram (MB) | Limit Core (core) | Limit Ram (MB) | Pod | BlobStorage (GB) |`
- On prem: `| (AP/PK) | Ambiente | Server Fisico/Virtuale | Layer | Tipologia | Data Center | Cluster | RAM | Storage | CPU | Core | SO | SW |`
- Cloud IaaS: `| (AP/PK) | Ambiente | Risorsa | Tipologia | Cloud Provider | Region | Resource Group | FQDN Front Door | FQDN Backend | RAM | Storage | CPU | Core | SO | SW |`

Ogni tabella ha la didascalia `Tabella n: …` sotto, numerata in sequenza.

## Stile

- Come la SF: italiano formale, impersonale, nomi tecnici esatti.
- Prosa breve: la sostanza del DP è nelle tabelle. Ogni capitolo apre con
  2–4 frasi, non di più.
- Coerenza con la SF: stessi nomi di microservizi, topic e sistemi. Se trovi
  una differenza, segnalala a fine lavoro.

## Regole sui buchi

- Codici AP/PK, nomi di cluster, namespace e volumi non confermati sono
  `DA DEFINIRE` (evidenziati in giallo dal generatore). Le proposte si
  scrivono come tali ("proposta: …").
- Il DP non ha una sezione open point: elenca i `DA DEFINIRE` in fondo alla
  tua risposta, raggruppati per chi deve rispondere (cliente, infrastruttura,
  team).
- Figure: stessa convenzione della SF (`documenti/fig-<n>-<slug>.drawio`
  e `.png` accanto), `![Figura n: …](fig-<n>-<slug>.png)`. La figura
  dell'architettura può essere la stessa della SF. Se il file non c'è, il generatore
  lascia un segnaposto rosso. La tabella dei flussi deve comunque bastare.

## File

- La data delle revisioni è quella di emissione (in bozza non c'è
  approvazione), anche se il template chiama la colonna "Data di Approvazione".
- Master: `iniziative/<id>/documenti/DP_<id>_<slug>.md`, es.
  `DP_136596_Eurodis_autoproduttore.md`.
- Word: `python contesto/modelli/md2docx.py iniziative/<id>/documenti/DP_<id>_<slug>.md`.
  Il Word non si modifica a mano: si corregge il master e si rigenera.

### Front-matter del master

```yaml
---
tipo: dp
titolo: "<titolo dell'iniziativa>"
codice_iniziativa: "<id>"
redazione: {nome: "GDL ACN", struttura: ""}
verifica: {nome: "", struttura: ""}
approvazione: {nome: "", struttura: ""}
revisioni:
  - {versione: "0.1", data: "gg/mm/aaaa", paragrafi: "Tutti", motivazioni: "Prima emissione"}
---
```

Il markdown ammesso nel corpo è lo stesso della SF (vedi `guida-sf.md`,
"Front-matter del master").

## Prima di consegnare

- [ ] Tutti i capitoli e le tabelle dell'esempio ci sono.
- [ ] I numeri dei flussi coincidono fra Information System Architecture e
      Application Technical Architecture.
- [ ] Nessuna cella vuota: valore, stima dichiarata, `DA DEFINIRE` o "Non applicabile".
- [ ] Nomi coerenti con la SF.
- [ ] Il Word si genera senza errori.
