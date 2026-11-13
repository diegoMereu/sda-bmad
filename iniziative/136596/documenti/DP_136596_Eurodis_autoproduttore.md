---
tipo: dp
titolo: "EURODIS Autoproduttore"
codice_iniziativa: "136596"
redazione: {nome: "GDL ACN", struttura: ""}
verifica: {nome: "", struttura: ""}
approvazione: {nome: "", struttura: ""}
revisioni:
  - {versione: "0.1", data: "05/11/2026", paragrafi: "Tutti", motivazioni: "Prima emissione"}
  - {versione: "0.2", data: "10/11/2026", paragrafi: "Tutti", motivazioni: "Persistenza su PostgreSQL al posto di MongoDB, area di appoggio locale con recupero, eventi di stato su preadvising.evensource, ce-anagrafica consultato dal mapper, F1 non consultato, catena a valle per il canale EUD_INVIOSYSTEM, frequenze per ambiente, allineamento alla SF 0.3"}
  - {versione: "0.3", data: "13/11/2026", paragrafi: "1.1, 3.1", motivazioni: "Codice PK delle applicazioni CE (PK-03089, dalle label pkcode dei chart Helm)"}
---

# Architettura Applicativa

L'iniziativa ha lo scopo di prendere in carico le spedizioni del consorzio EURODIS in modalità autoproduttore: la lettera di vettura è assegnata da EURODIS e i dati di spedizione (PAN) vengono prelevati dall'API EURODIS `receive-pan`, invece che dal dichiarato tradizionale. Le spedizioni acquisite vengono convertite nel tracciato unico del preadvising con il nuovo canale `EUD_INVIOSYSTEM` e immesse nella catena di preadvising esistente, che le valida, le arricchisce e le crea su PDB; SDA restituisce infine a EURODIS le tracce delle spedizioni prese in carico. Le regole funzionali sono descritte nella Specifica Funzionale dell'iniziativa (allegato SF_136596_Eurodis_autoproduttore, versione 0.3).

## Business Architecture – Preadvising EURODIS autoproduttore

![Figura 1: Business Architecture – Preadvising EURODIS autoproduttore](fig-1-architettura.png)

| Processo | Fase | Sistema Applicativo (AP) / Applicazione (PK) | Ruolo dell'Applicativo | Impatto Applicativo (S/N) | Applicativo esistente o nuovo |
|---|---|---|---|---|---|
| Preadvising | Acquisizione spedizioni | EURODIS / API `receive-pan` | Piattaforma del partner: espone le spedizioni affidate a SDA | N | Esistente (esterno) |
| Preadvising | Acquisizione e storicizzazione | CE (AP-00988) / `ce-dichiarato-eurodis-in` (PK-03089) | Scarica periodicamente le spedizioni da `receive-pan`, le appoggia su un'area locale, ne salva lo storico su PostgreSQL, pubblica gli eventi di stato della presa in carico su `preadvising.evensource` e una spedizione per messaggio su `preadvising.eud.pre.build` | S | Nuovo |
| Preadvising | Trasformazione nel tracciato unico | CE (AP-00988) / `ce-dichiarato-eurodis-mapper` (PK-03089) | Converte la spedizione EURODIS nel tracciato unico (ICD v11, canale `EUD_INVIOSYSTEM`), ricava i codici nazione da `ce-anagrafica` e pubblica su `preadvising.pre-enrichment` | S | Nuovo |
| Preadvising | Codici nazione | CE (AP-00988) / `ce-anagrafica` (PK-03089) | Restituisce i codici ISO3, ISO4 Poste e ISO2 della nazione di mittente e destinatario | N | Esistente |
| Preadvising | Validazione del tracciato unico | CE (AP-00988) / `ce-dichiarato-validatore` (PK-03089) | Consuma il tracciato da `preadvising.pre-enrichment` e lo valida con le regole del canale `EUD_INVIOSYSTEM` (riuso delle regole `PDB_INVIOSYSTEM`); deve accettare i valori oltre le dimensioni ICD (vincolo 2 della SF) | S | Esistente |
| Preadvising | Orchestrazione | CE (AP-00988) / `ce-dichiarato-orchestratore` (PK-03089) | Per il canale `EUD_INVIOSYSTEM` esegue normalizzazione, arricchimento BEP e creazione su PDB, poi pubblica su `preadvising.completed` | S | Esistente |
| Preadvising | Arricchimento | CE (AP-00988) / ce-rules (PK-03089) | Determinazione di prodotto e servizi, consultato dalla catena esistente | N | Esistente |
| Preadvising | Propagazione verso PDB | CE (AP-00988) / `ce-dichiarato-ldv-pdb` (PK-03089) | Converte il tracciato unico nella richiesta PDB e crea la spedizione con `waybillCreate`. Nessuno sviluppo previsto: verifica delle osservazioni della SF, eventuali correzioni a carico del responsabile | N | Esistente |
| Preadvising | Creazione spedizione | PDB (AP DA DEFINIRE) / servizio `waybillCreate` | Crea la spedizione con la LDV assegnata da EURODIS | N | Esistente |
| Preadvising | Smistamento | CE (AP-00988) / `ce-dichiarato-smistatore` (PK-03089) | Instrada il tracciato completato del canale `EUD_INVIOSYSTEM` tra i canali Poste | S | Esistente |
| Preadvising | Ricezione LDV | BEP (AP DA DEFINIRE) | Riceve la LDV dal tracciato unico | N | Esistente |
| Tracciamento | Invio tracce al partner | CE (AP-00988) / `ce-eurodis-send-tracking` (PK-03089) | Traduce gli stati SDA nei codici evento EURODIS e li invia a EURODIS | S | Nuovo |
| Tracciamento | Ricezione tracce | EURODIS / API `send-tracking` | Piattaforma del partner: riceve gli eventi di tracciamento | N | Esistente (esterno) |

Tabella 1: Business Architecture – Preadvising EURODIS autoproduttore

## Information System Architecture

Il dato nasce sulla piattaforma EURODIS e viene letto da `ce-dichiarato-eurodis-in`, che lo scrive su un'area di appoggio locale, lo storicizza su PostgreSQL, pubblica gli eventi di stato della presa in carico e lo invia, una spedizione per messaggio, sul topic `preadvising.eud.pre.build`. `ce-dichiarato-eurodis-mapper` lo converte nel tracciato unico, consultando `ce-anagrafica`, e lo pubblica su `preadvising.pre-enrichment`, da cui la catena di preadvising esistente lo valida, lo orchestra fino a `ce-dichiarato-ldv-pdb` e PDB e lo pubblica completato su `preadvising.completed`. Le tracce SDA tornano a EURODIS tramite `ce-eurodis-send-tracking`.

![Figura 2: Information System Architecture – Preadvising EURODIS autoproduttore](fig-2-flussi-dati.png)

| Flusso dati | Descrizione |
|---|---|
| Flusso dati 1 | `ce-dichiarato-eurodis-in` invoca periodicamente `GET /shipments/v1` dell'API EURODIS `receive-pan` e riceve le spedizioni non ancora consegnate al partner. Su richiesta da configurazione invoca anche la rilettura puntuale `GET /shipment/{edReference}/v1`, disponibile per 60 giorni. |
| Flusso dati 2 | `ce-dichiarato-eurodis-in` scrive la risposta integrale su un file dell'area di appoggio locale (volume del pod), prima del salvataggio su database, e lo cancella dopo il salvataggio riuscito. Un job di recupero salva su database i file rimasti, per esempio dopo un'indisponibilità del database. |
| Flusso dati 3 | `ce-dichiarato-eurodis-in` salva su PostgreSQL (database `ce_eud_api_in`, tabella `eurodis_scarichi`) ogni chiamata con esito HTTP, orari e risposta integrale, prima di qualsiasi elaborazione. |
| Flusso dati 4 | `ce-dichiarato-eurodis-in` scompone la risposta e registra su PostgreSQL (tabella `eurodis_spedizioni`) un record per spedizione, identificato da `edReference`, con stato di invio e ora di invio. |
| Flusso dati 5 | Per ogni scarico con spedizioni, trattato come un file fittizio con un proprio `idFile`, `ce-dichiarato-eurodis-in` pubblica sul topic `preadvising.evensource` gli eventi di stato `ST_F0002` (file preso in carico) e `ST_F0005` (file in elaborazione), prima delle spedizioni. |
| Flusso dati 6 | `ce-dichiarato-eurodis-in` pubblica ogni spedizione, così come ricevuta, sul topic `preadvising.eud.pre.build`, con chiave `edReference` e metadati negli header, compreso `idFile`. |
| Flusso dati 7 | `ce-dichiarato-eurodis-mapper` consuma la spedizione dal topic `preadvising.eud.pre.build`. |
| Flusso dati 8 | `ce-dichiarato-eurodis-mapper` invoca `ce-anagrafica` (`GET /anagrafica/indirizzi/nazione/{codice}`) per i codici nazione di mittente e destinatario. |
| Flusso dati 9 | `ce-dichiarato-eurodis-mapper` pubblica il tracciato unico (ICD v11, canale `EUD_INVIOSYSTEM`, `id_file` = `idFile`) sul topic `preadvising.pre-enrichment`. |
| Flusso dati 10 | `ce-dichiarato-validatore` consuma il tracciato unico dal topic `preadvising.pre-enrichment` e lo valida. |
| Flusso dati 11 | `ce-dichiarato-validatore` pubblica il tracciato validato sul topic `preadvising.enrichment`. |
| Flusso dati 12 | `ce-dichiarato-orchestratore` consuma il tracciato da `preadvising.enrichment` ed esegue, per il canale `EUD_INVIOSYSTEM`, le azioni di normalizzazione e di arricchimento BEP della catena esistente. |
| Flusso dati 13 | `ce-dichiarato-orchestratore` invia il tracciato a `ce-dichiarato-ldv-pdb` tramite il topic `preadvising.enrichment.pdb` (azione `ldv-pdb`). |
| Flusso dati 14 | `ce-dichiarato-ldv-pdb` crea la spedizione su PDB invocando il servizio sincrono `waybillCreate`. |
| Flusso dati 15 | `ce-dichiarato-orchestratore` pubblica il tracciato completato sul topic `preadvising.completed`. |
| Flusso dati 16 | `ce-dichiarato-smistatore` consuma il tracciato da `preadvising.completed` e lo instrada tra i canali Poste. |
| Flusso dati 17 | `ce-eurodis-send-tracking` acquisisce le tracce SDA delle spedizioni EURODIS da una sorgente DA DEFINIRE (proposta: il topic degli esiti SDA indicato da SDA). |
| Flusso dati 18 | `ce-eurodis-send-tracking` invia le tracce a EURODIS tramite l'API `send-tracking` (`POST /event/parcel/v1` e variante a lotti), con la stessa chiave API del partner e lo stato SDA tradotto nel codice evento EURODIS. |

Tabella 2: Information System Architecture – Flussi dati

# Architettura Tecnica

## Application Technical Architecture

I nuovi microservizi seguono lo stack standard dei microservizi `ce-` del preadvising: Java 17 e Spring Boot, deploy su OpenShift con chart Helm e pipeline Jenkins ALM, integrazione via Kafka e persistenza su PostgreSQL con accesso JDBC, come `ce-db-sync`. La versione di Spring Boot è 3.5.14 per `ce-dichiarato-eurodis-in` e `ce-eurodis-send-tracking`; `ce-dichiarato-eurodis-mapper` è oggi alla 4.1.2, da riallineare alla decisione di usare 3.5.14 su tutta la catena. Lo scarico gira ogni 2 minuti in sviluppo e collaudo e ogni 10 minuti in produzione; volumi e dimensioni non ancora noti sono indicati come stima o `DA DEFINIRE`.

| Pacchetto Applicativo | Software | Versione | Layer Applicativo | Applicativo nuovo o esistente |
|---|---|---|---|---|
| `ce-dichiarato-eurodis-in` | Microservizio Java 17 / Spring Boot 3.5.14 | 1.0 | Application | Nuovo |
| `ce-dichiarato-eurodis-mapper` | Microservizio Java 17 / Spring Boot 4.1.2 (da riallineare a 3.5.14) | 1.0 | Application | Nuovo |
| `ce-eurodis-send-tracking` | Microservizio Java 17 / Spring Boot 3.5.14 | 1.0 | Application | Nuovo |
| `preadvising.eud.pre.build` | Topic Kafka | 1.0 | Integration | Nuovo |
| `preadvising.pre-enrichment` | Topic Kafka | Non applicabile | Integration | Esistente (nuovo produttore) |
| `preadvising.evensource` | Topic Kafka | Non applicabile | Integration | Esistente (nuovo produttore) |
| `ce_eud_api_in` (tabelle `eurodis_scarichi`, `eurodis_spedizioni`, `eurodis_richieste_manuali`, `shedlock`) | PostgreSQL | Non applicabile | Data | Nuovo (database e tabelle) |
| Area di appoggio locale di `ce-dichiarato-eurodis-in` | Volume OpenShift `emptyDir` (1 Gi, montato su `/buffer`) | Non applicabile | Data | Nuovo |
| `ce-anagrafica` | Microservizio | DA DEFINIRE | Application | Esistente |
| `ce-dichiarato-validatore` | Microservizio | DA DEFINIRE | Application | Esistente (nuovo canale) |
| `ce-dichiarato-orchestratore` | Microservizio | DA DEFINIRE | Application | Esistente (nuovo canale) |
| `ce-dichiarato-ldv-pdb` | Microservizio | DA DEFINIRE | Application | Esistente |
| `ce-dichiarato-smistatore` | Microservizio | DA DEFINIRE | Application | Esistente (nuovo canale) |
| PDB `waybillCreate` | Servizio applicativo | Non applicabile | Application | Esistente |
| EURODIS `receive-pan` | API REST esterna (Release v1) | v1 | Integration | Esistente (esterno) |
| EURODIS `send-tracking` | API REST esterna (Release v1) | v1 | Integration | Esistente (esterno) |

Tabella 3: Preadvising EURODIS autoproduttore – dettaglio applicativi

<!-- orientamento: orizzontale -->

| Flusso dati | Protocollo | Origine | Destinazione | Tipologia | Frequenza | Frequenza di picco | Dimensione media dei messaggi | Dimensione massima dei messaggi | Flusso nuovo o esist. |
|---|---|---|---|---|---|---|---|---|---|
| Flusso 1 | https | `ce-dichiarato-eurodis-in` | EURODIS `receive-pan` | Sincrona | Ogni 2 minuti in sviluppo e collaudo, ogni 10 minuti in produzione; rilettura puntuale su richiesta | Una sola chiamata per ciclo, nessun nuovo tentativo automatico | DA DEFINIRE | DA DEFINIRE (soglia di guardia del servizio: 100 MB) | Nuovo |
| Flusso 2 | File system (volume del pod) | `ce-dichiarato-eurodis-in` | Area di appoggio locale `/buffer` | Sincrona | A ogni risposta con spedizioni; job di recupero ogni 2 minuti | Come il Flusso 1 | DA DEFINIRE | DA DEFINIRE (volume da 1 Gi) | Nuovo |
| Flusso 3 | JDBC | `ce-dichiarato-eurodis-in` | PostgreSQL `ce_eud_api_in`, tabella `eurodis_scarichi` | Sincrona | A ogni ciclo di scarico (una riga per chiamata, anche senza spedizioni) | Come il Flusso 1 | DA DEFINIRE | DA DEFINIRE (soglia di guardia: 100 MB) | Nuovo |
| Flusso 4 | JDBC | `ce-dichiarato-eurodis-in` | PostgreSQL `ce_eud_api_in`, tabella `eurodis_spedizioni` | Sincrona | A ogni ciclo di elaborazione, 30 secondi dopo lo scarico; una riga per spedizione | DA DEFINIRE (volumi) | stima: circa 3 KB per spedizione | DA DEFINIRE | Nuovo |
| Flusso 5 | Kafka | `ce-dichiarato-eurodis-in` | Topic `preadvising.evensource` | Asincrona | Due eventi per scarico con spedizioni | Come il Flusso 1 | stima: circa 1 KB | stima: circa 1 KB | Nuovo |
| Flusso 6 | Kafka | `ce-dichiarato-eurodis-in` | Topic `preadvising.eud.pre.build` | Asincrona | A ogni ciclo di elaborazione; un messaggio per spedizione | DA DEFINIRE (volumi) | stima: circa 3 KB (esempio di spedizione EURODIS monocollo) | DA DEFINIRE (limite del topic) | Nuovo |
| Flusso 7 | Kafka | Topic `preadvising.eud.pre.build` | `ce-dichiarato-eurodis-mapper` | Asincrona | A evento | DA DEFINIRE (volumi) | stima: circa 3 KB | DA DEFINIRE | Nuovo |
| Flusso 8 | https | `ce-dichiarato-eurodis-mapper` | `ce-anagrafica` | Sincrona | Due chiamate per spedizione (mittente e destinatario) | DA DEFINIRE (volumi) | stima: inferiore a 1 KB | stima: inferiore a 1 KB | Nuovo |
| Flusso 9 | Kafka | `ce-dichiarato-eurodis-mapper` | Topic `preadvising.pre-enrichment` | Asincrona | A evento, un tracciato per spedizione | DA DEFINIRE (volumi) | stima: 3-4 KB (tracciato unico del flusso `EUD_INVIOFILE`) | DA DEFINIRE | Nuovo |
| Flusso 10 | Kafka | Topic `preadvising.pre-enrichment` | `ce-dichiarato-validatore` | Asincrona | A evento | DA DEFINIRE (volumi) | stima: 3-4 KB | DA DEFINIRE | Esistente (nuovo canale) |
| Flusso 11 | Kafka | `ce-dichiarato-validatore` | Topic `preadvising.enrichment` | Asincrona | A evento | DA DEFINIRE (volumi) | stima: 3-4 KB | DA DEFINIRE | Esistente (nuovo canale) |
| Flusso 12 | Kafka | Topic `preadvising.enrichment` | `ce-dichiarato-orchestratore` | Asincrona | A evento | DA DEFINIRE (volumi) | stima: 3-4 KB | DA DEFINIRE | Esistente (nuovo canale) |
| Flusso 13 | Kafka | `ce-dichiarato-orchestratore` | `ce-dichiarato-ldv-pdb`, tramite il topic `preadvising.enrichment.pdb` | Asincrona | A evento | DA DEFINIRE (volumi) | stima: 3-4 KB | DA DEFINIRE | Esistente (nuovo canale) |
| Flusso 14 | DA DEFINIRE | `ce-dichiarato-ldv-pdb` | PDB `waybillCreate` | Sincrona | A evento, una chiamata per spedizione | DA DEFINIRE (volumi) | DA DEFINIRE | DA DEFINIRE | Esistente |
| Flusso 15 | Kafka | `ce-dichiarato-orchestratore` | Topic `preadvising.completed` | Asincrona | A evento | DA DEFINIRE (volumi) | stima: 3-4 KB | DA DEFINIRE | Esistente (nuovo canale) |
| Flusso 16 | Kafka | Topic `preadvising.completed` | `ce-dichiarato-smistatore` | Asincrona | A evento | DA DEFINIRE (volumi) | stima: 3-4 KB | DA DEFINIRE | Esistente (nuovo canale) |
| Flusso 17 | DA DEFINIRE (proposta: Kafka) | Sorgente delle tracce SDA (DA DEFINIRE) | `ce-eurodis-send-tracking` | DA DEFINIRE | DA DEFINIRE | DA DEFINIRE | DA DEFINIRE | DA DEFINIRE | Nuovo |
| Flusso 18 | https | `ce-eurodis-send-tracking` | EURODIS `send-tracking` | Sincrona | DA DEFINIRE | DA DEFINIRE | DA DEFINIRE | DA DEFINIRE | Nuovo |

Tabella 4: Preadvising EURODIS autoproduttore – dettaglio flussi

# Scheda HW

L'iniziativa non richiede server dedicati, mainframe, HW periferico né risorse cloud IaaS: i tre nuovi microservizi sono deployati su OpenShift nel namespace esistente `corriere-espresso-preadvising`. Il database `ce_eud_api_in` è creato sui server PostgreSQL già usati da `ce-db-sync` (sviluppo e collaudo), con le stesse credenziali (secret `ce-postgres`); server e database di certificazione e produzione sono DA DEFINIRE. La collocazione del cluster (on prem o cloud) è DA DEFINIRE: i dimensionamenti sono riportati nella tabella Openshift on prem e vanno spostati nella tabella Openshift cloud se il cluster è in cloud. Topic `preadvising.eud.pre.build` (partizioni e retention) e spazio del database sono su infrastruttura esistente, con dimensionamento DA DEFINIRE sui volumi.

## Risorse on Prem


| (AP/PK) | Ambiente | Server Fisico/Virtuale | Layer | Tipologia | Data Center | Cluster | RAM | Storage | CPU | Core | SO | SW |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile |

Tabella 5: Risorse on Prem (HW dedicato o Private Cloud)

| Componente | Ambiente | MIPS | Tipologia elaborazione | Capacità di storage | Storage Tape |
|---|---|---|---|---|---|
| Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile |

Tabella 6: Mainframe

| Tipologia | Marca | Modello | Caratteristica tecnica 1 | Caratteristica tecnica 2 | Caratteristica tecnica 3 | Caratteristica tecnica 4 |
|---|---|---|---|---|---|---|
| Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile |

Tabella 7: HW Periferico

### Openshift

Namespace esistente `corriere-espresso-preadvising`, condiviso con gli altri microservizi del preadvising. Request, limit e pod di sviluppo e collaudo sono quelli dei chart Helm dei tre microservizi (request 100 millicore / 256 MB, limit 500 millicore / 1024 MB, 1 pod); per la produzione sono una proposta, da confermare con l'infrastruttura.

| (AP/PK) | Ambiente | Nome Cluster | Tipologia cluster | Namespace | Gen | Request Core (millicore) | Request Ram (MB) | Limit Core (core) | Limit Ram (MB) | Pod | BlobStorage (GB) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AP-00988 / `ce-dichiarato-eurodis-in` (PK-03089) | Sviluppo | DA DEFINIRE (esistente) | DA DEFINIRE | `corriere-espresso-preadvising` (esistente) | DA DEFINIRE | 100 | 256 | 0,5 | 1024 | 1 | Non applicabile |
| AP-00988 / `ce-dichiarato-eurodis-in` (PK-03089) | Collaudo | DA DEFINIRE | DA DEFINIRE | `corriere-espresso-preadvising` (esistente) | DA DEFINIRE | 100 | 256 | 0,5 | 1024 | 1 | Non applicabile |
| AP-00988 / `ce-dichiarato-eurodis-in` (PK-03089) | Produzione | DA DEFINIRE | DA DEFINIRE | `corriere-espresso-preadvising` (esistente) | DA DEFINIRE | proposta: 100 | proposta: 256 | proposta: 0,5 | proposta: 1024 | proposta: 1 | Non applicabile |
| AP-00988 / `ce-dichiarato-eurodis-mapper` (PK-03089) | Sviluppo | DA DEFINIRE (esistente) | DA DEFINIRE | `corriere-espresso-preadvising` (esistente) | DA DEFINIRE | 100 | 256 | 0,5 | 1024 | 1 | Non applicabile |
| AP-00988 / `ce-dichiarato-eurodis-mapper` (PK-03089) | Collaudo | DA DEFINIRE | DA DEFINIRE | `corriere-espresso-preadvising` (esistente) | DA DEFINIRE | 100 | 256 | 0,5 | 1024 | 1 | Non applicabile |
| AP-00988 / `ce-dichiarato-eurodis-mapper` (PK-03089) | Produzione | DA DEFINIRE | DA DEFINIRE | `corriere-espresso-preadvising` (esistente) | DA DEFINIRE | proposta: 100 | proposta: 256 | proposta: 0,5 | proposta: 1024 | proposta: 1 | Non applicabile |
| AP-00988 / `ce-eurodis-send-tracking` (PK-03089) | Sviluppo | DA DEFINIRE (esistente) | DA DEFINIRE | `corriere-espresso-preadvising` (esistente) | DA DEFINIRE | 100 | 256 | 0,5 | 1024 | 1 | Non applicabile |
| AP-00988 / `ce-eurodis-send-tracking` (PK-03089) | Collaudo | DA DEFINIRE | DA DEFINIRE | `corriere-espresso-preadvising` (esistente) | DA DEFINIRE | 100 | 256 | 0,5 | 1024 | 1 | Non applicabile |
| AP-00988 / `ce-eurodis-send-tracking` (PK-03089) | Produzione | DA DEFINIRE | DA DEFINIRE | `corriere-espresso-preadvising` (esistente) | DA DEFINIRE | proposta: 100 | proposta: 256 | proposta: 0,5 | proposta: 1024 | proposta: 1 | Non applicabile |

Tabella 8: Openshift on Prem

N.B. `ce-dichiarato-eurodis-in` esegue i job di scarico ed elaborazione su una sola istanza alla volta anche con più repliche (lock su tabella `shedlock` di PostgreSQL): il numero di pod in Produzione può essere aumentato per disponibilità senza chiamate concorrenti a EURODIS. L'area di appoggio locale è un volume `emptyDir` da 1 Gi per pod: copre l'indisponibilità del database con il pod attivo, non la cancellazione del pod; un volume persistente (PVC, già previsto dal chart) richiederebbe storage class e quota dall'infrastruttura (DA DEFINIRE). Il limit di memoria va verificato sulla dimensione massima delle risposte EURODIS, oggi non nota.

## Risorse Cloud


| (AP/PK) | Ambiente | Risorsa | Tipologia | Cloud Provider | Region | Resource Group | FQDN Front Door | FQDN Backend | RAM | Storage | CPU | Core | SO | SW |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile |

Tabella 9: Risorse Cloud IaaS

### Openshift

| (AP/PK) | Ambiente | Nome Cluster | Tipologia cluster | Namespace | Gen | Request Core (millicore) | Request Ram (MB) | Limit Core (core) | Limit Ram (MB) | Pod | BlobStorage (GB) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DA DEFINIRE: da compilare con i valori della Tabella 8 se il cluster è in cloud | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile | Non applicabile |

Tabella 10: Openshift Cloud

<!-- orientamento: verticale -->

# Allegati

| Codice Documento | Nome |
|---|---|
| SF_136596_Eurodis_autoproduttore | Specifica Funzionale dell'iniziativa 136596 - EURODIS Autoproduttore, versione 0.3 |
| ICD_PREADVISING_LDV_EVENT_SOURCE_v11 | ICD v11 del tracciato unico preadvising, con il mapping EURODIS |
| eurodis-receive-pan-swagger-v1 | Specifica OpenAPI dell'API EURODIS `receive-pan`, Release v1 |
| eurodis-send-tracking-swagger-v1 | Specifica OpenAPI dell'API EURODIS `send-tracking`, Release v1 |
| ddl-ce-eurodis-api-in | Script DDL del database PostgreSQL `ce_eud_api_in` |
| alert-datadog-eurodis | Monitor Datadog proposti per i tre microservizi |
| fig-1-architettura | Schema drawio della soluzione: pagina "Architettura" (Figura 1) e pagina "Flussi dati" (Figura 2) |
