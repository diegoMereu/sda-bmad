---
iniziativa: 136596
nome_file: TOTALE_ST_SDA_136596_Eurodis_Autoproduttore_v1.xlsx
titolo_iniziativa: Eurodis
piattaforma: SDA
test_manager: Piergentili Alessandro
workpackage: BC-POS
consegna_completa: SI
default_id1: MA01
default_macro: Caricamento Preadvising
default_risk: 2
default_pri: 2
default_durata: 00:20
default_tipologia: Funzionalità
default_livello: Integrato
---

# Test list UAT - EURODIS API (derivata da SpecificaDiTest)

<!-- Master della test list. Si modifica qui; l'Excel si rigenera con md2xlsx.py. -->
<!-- Per test: sezione `Prerequisiti` = step P, `Azioni e verifiche` = step 1; -->
<!-- la colonna Descrizione e note dell'Excel e' la loro concatenazione. -->

## C001 - OK - EURODIS API - Spedizione standard senza servizi accessori (Nessun accessorio)

### C001_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Spedizione standard senza servizi accessori (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C001_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C001_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C001_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C001_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C001_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C001_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C001_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C001_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-smistatore

Verifiche:
O1: pubblica sul topic "preadvising.completed.poste" (se prodotti Poste)
O2: pubblica sul topic "PSDA-20-04.SDA.EVENTTT.ANALDV" (Palmari) (1 msg per volta)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C001_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C001_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
consumer-sew-sped-poste

Verifiche:
O1: Scrittura sul DB ERMES,
 se CONDIZ_BS=FALSE sulle tabelle del vecchio Processo:
     - sew_spedizioni_poste
     - sew_spedizioni_poste_extender
     - associazioni_ldv_internazionale
     - prtn_articolo
     - prtn_collo
     - sew_spedizioni_poste_inter
     - prtn_spedizione
     - timedef_arch
     - sew_extender_scarto (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - dhl_scarti          (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - sew_inter_scarto    (solo per evitare che eventuali scarti del nuovo finiscano qui)
 oppure sulle corrispondenti tabelle del nuovo Processo (con suffisso "_2")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C001_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C002 - OK (osservazione) - EURODIS API - shipmentTypeIndicator C (B2C), non mappato (Nessun accessorio)

### C002_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: shipmentTypeIndicator C (B2C), non mappato (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Nota: shipmentTypeIndicator = C (flag B2C) è nel payload ma ignorato dal mapper (DF-15)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C002_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: shipmentTypeIndicator ignorato: spedizione trattata come ordinaria, nessun campo ICD valorizzato da esso
O5: eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori; eventuali warning DA VERIFICARE
OP: dato non mappato in fase 1: atteso DA RICONFERMARE dopo la decisione sul mapping; fino ad allora il test è di osservazione
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C002_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C002_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C002_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C002_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C002_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C002_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C002_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-smistatore

Verifiche:
O1: pubblica sul topic "preadvising.completed.poste" (se prodotti Poste)
O2: pubblica sul topic "PSDA-20-04.SDA.EVENTTT.ANALDV" (Palmari) (1 msg per volta)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C002_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C002_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
consumer-sew-sped-poste

Verifiche:
O1: Scrittura sul DB ERMES,
 se CONDIZ_BS=FALSE sulle tabelle del vecchio Processo:
     - sew_spedizioni_poste
     - sew_spedizioni_poste_extender
     - associazioni_ldv_internazionale
     - prtn_articolo
     - prtn_collo
     - sew_spedizioni_poste_inter
     - prtn_spedizione
     - timedef_arch
     - sew_extender_scarto (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - dhl_scarti          (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - sew_inter_scarto    (solo per evitare che eventuali scarti del nuovo finiscano qui)
 oppure sulle corrispondenti tabelle del nuovo Processo (con suffisso "_2")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C002_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C003 - OK (osservazione) - EURODIS API - shipmentTypeIndicator X (AUX-Pan), non mappato (Nessun accessorio)

### C003_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: shipmentTypeIndicator X (AUX-Pan), non mappato (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Nota: shipmentTypeIndicator = X (AUX-Pan) è nel payload ma ignorato dal mapper (DF-15)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C003_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: shipmentTypeIndicator ignorato: spedizione trattata come ordinaria
O5: eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori; eventuali warning DA VERIFICARE
OP: dato non mappato in fase 1: atteso DA RICONFERMARE dopo la decisione sul mapping; fino ad allora il test è di osservazione
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C003_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C003_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C003_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C003_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C003_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C003_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C003_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-smistatore

Verifiche:
O1: pubblica sul topic "preadvising.completed.poste" (se prodotti Poste)
O2: pubblica sul topic "PSDA-20-04.SDA.EVENTTT.ANALDV" (Palmari) (1 msg per volta)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C003_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C003_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
consumer-sew-sped-poste

Verifiche:
O1: Scrittura sul DB ERMES,
 se CONDIZ_BS=FALSE sulle tabelle del vecchio Processo:
     - sew_spedizioni_poste
     - sew_spedizioni_poste_extender
     - associazioni_ldv_internazionale
     - prtn_articolo
     - prtn_collo
     - sew_spedizioni_poste_inter
     - prtn_spedizione
     - timedef_arch
     - sew_extender_scarto (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - dhl_scarti          (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - sew_inter_scarto    (solo per evitare che eventuali scarti del nuovo finiscano qui)
 oppure sulle corrispondenti tabelle del nuovo Processo (con suffisso "_2")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C003_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C004 - OK - EURODIS API - Spedizione multicollo senza servizi accessori (Nessun accessorio (multicollo da n. colli))

### C004_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), più colli (es. 3) - scenario: Spedizione multicollo senza servizi accessori (Nessun accessorio (multicollo da n. colli))
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C004_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: numero_colli = numberOfHandlingUnits, un collo[] per ogni collis[], peso in grammi per ciascun collo
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C004_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C004_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C004_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C004_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C004_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C004_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C004_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-smistatore

Verifiche:
O1: pubblica sul topic "preadvising.completed.poste" (se prodotti Poste)
O2: pubblica sul topic "PSDA-20-04.SDA.EVENTTT.ANALDV" (Palmari) (1 msg per volta)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C004_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C004_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
consumer-sew-sped-poste

Verifiche:
O1: Scrittura sul DB ERMES,
 se CONDIZ_BS=FALSE sulle tabelle del vecchio Processo:
     - sew_spedizioni_poste
     - sew_spedizioni_poste_extender
     - associazioni_ldv_internazionale
     - prtn_articolo
     - prtn_collo
     - sew_spedizioni_poste_inter
     - prtn_spedizione
     - timedef_arch
     - sew_extender_scarto (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - dhl_scarti          (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - sew_inter_scarto    (solo per evitare che eventuali scarti del nuovo finiscano qui)
 oppure sulle corrispondenti tabelle del nuovo Processo (con suffisso "_2")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C004_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C005 - KO VALID (1083: peso collo a zero) - EURODIS API - Peso collo a zero (Nessun accessorio)

### C005_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Peso e dimensioni collo a zero (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C005_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: weightOfUnit = 0 → collo[].peso = 0; il mapper pubblica comunque (la verifica è a valle)
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C005_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1083 "Collo Peso fuori range (ammessi valori tra 0 e 9.999.900 grammi)"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
O4: la regola pdb_10047 richiede peso > 0; nessun default di peso nel validatore (la SF prevede i default: DA CONFERMARE)
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C005_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C005_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C006 - OK - EURODIS API - Telefono/e-mail mittente e destinatario assenti (Nessun accessorio)

### C006_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Telefono/e-mail mittente e destinatario assenti (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C006_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: telefono/e-mail di mittente e destinatario assenti → campi vuoti, spedizione pubblicata
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C006_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C006_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C006_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C006_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C006_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C006_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C006_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-smistatore

Verifiche:
O1: pubblica sul topic "preadvising.completed.poste" (se prodotti Poste)
O2: pubblica sul topic "PSDA-20-04.SDA.EVENTTT.ANALDV" (Palmari) (1 msg per volta)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C006_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C006_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
consumer-sew-sped-poste

Verifiche:
O1: Scrittura sul DB ERMES,
 se CONDIZ_BS=FALSE sulle tabelle del vecchio Processo:
     - sew_spedizioni_poste
     - sew_spedizioni_poste_extender
     - associazioni_ldv_internazionale
     - prtn_articolo
     - prtn_collo
     - sew_spedizioni_poste_inter
     - prtn_spedizione
     - timedef_arch
     - sew_extender_scarto (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - dhl_scarti          (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - sew_inter_scarto    (solo per evitare che eventuali scarti del nuovo finiscano qui)
 oppure sulle corrispondenti tabelle del nuovo Processo (con suffisso "_2")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C006_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C007 - [DA CONFERMARE] EURODIS API - Troncamento civico e localita' (Nessun accessorio)

### C007_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] La SF prevede l'adeguamento ai limiti BEP a valle; le regole PDB_INVIOSYSTEM rifiutano civico > 4 e località > 30 (1292, 1294): vedi C101-C103

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Troncamento civico e localita' (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C007_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] La SF prevede l'adeguamento ai limiti BEP a valle; le regole PDB_INVIOSYSTEM rifiutano civico > 4 e località > 30 (1292, 1294): vedi C101-C103

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: civico e località più lunghi della dimensione ICD passano interi (nessun troncamento): l'atteso del flusso a file (troncamento) NON vale più
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C007_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] La SF prevede l'adeguamento ai limiti BEP a valle; le regole PDB_INVIOSYSTEM rifiutano civico > 4 e località > 30 (1292, 1294): vedi C101-C103

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C007_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] La SF prevede l'adeguamento ai limiti BEP a valle; le regole PDB_INVIOSYSTEM rifiutano civico > 4 e località > 30 (1292, 1294): vedi C101-C103

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C007_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] La SF prevede l'adeguamento ai limiti BEP a valle; le regole PDB_INVIOSYSTEM rifiutano civico > 4 e località > 30 (1292, 1294): vedi C101-C103

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C007_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)
- note_esecuzione: [DA CONFERMARE] La SF prevede l'adeguamento ai limiti BEP a valle; le regole PDB_INVIOSYSTEM rifiutano civico > 4 e località > 30 (1292, 1294): vedi C101-C103

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C007_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] La SF prevede l'adeguamento ai limiti BEP a valle; le regole PDB_INVIOSYSTEM rifiutano civico > 4 e località > 30 (1292, 1294): vedi C101-C103

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C007_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply
- note_esecuzione: [DA CONFERMARE] La SF prevede l'adeguamento ai limiti BEP a valle; le regole PDB_INVIOSYSTEM rifiutano civico > 4 e località > 30 (1292, 1294): vedi C101-C103

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C007_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] La SF prevede l'adeguamento ai limiti BEP a valle; le regole PDB_INVIOSYSTEM rifiutano civico > 4 e località > 30 (1292, 1294): vedi C101-C103

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-smistatore

Verifiche:
O1: pubblica sul topic "preadvising.completed.poste" (se prodotti Poste)
O2: pubblica sul topic "PSDA-20-04.SDA.EVENTTT.ANALDV" (Palmari) (1 msg per volta)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C007_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] La SF prevede l'adeguamento ai limiti BEP a valle; le regole PDB_INVIOSYSTEM rifiutano civico > 4 e località > 30 (1292, 1294): vedi C101-C103

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C007_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] La SF prevede l'adeguamento ai limiti BEP a valle; le regole PDB_INVIOSYSTEM rifiutano civico > 4 e località > 30 (1292, 1294): vedi C101-C103

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
consumer-sew-sped-poste

Verifiche:
O1: Scrittura sul DB ERMES,
 se CONDIZ_BS=FALSE sulle tabelle del vecchio Processo:
     - sew_spedizioni_poste
     - sew_spedizioni_poste_extender
     - associazioni_ldv_internazionale
     - prtn_articolo
     - prtn_collo
     - sew_spedizioni_poste_inter
     - prtn_spedizione
     - timedef_arch
     - sew_extender_scarto (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - dhl_scarti          (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - sew_inter_scarto    (solo per evitare che eventuali scarti del nuovo finiscano qui)
 oppure sulle corrispondenti tabelle del nuovo Processo (con suffisso "_2")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C007_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] La SF prevede l'adeguamento ai limiti BEP a valle; le regole PDB_INVIOSYSTEM rifiutano civico > 4 e località > 30 (1292, 1294): vedi C101-C103

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C008 - OK (osservazione) - EURODIS API - Pre-avviso destinatario richiesto (consigneePreAdvice), non mappato (Nessun accessorio)

### C008_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Pre-avviso destinatario richiesto (consigneePreAdvice), non mappato (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Nota: consigneePreAdvice (smsPreAdvice, eMailPreAdvice, telephonePreAdvice) è nel payload ma non mappato (SF OP 29)
OP: record type del tracciato CSV (RT_xx) non presenti nel payload API: mappatura campo CSV → payload API DA DEFINIRE
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C008_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: consigneePreAdvice NON mappato: notifiche_sms e notifiche_email vuote; spedizione pubblicata
O5: eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori; eventuali warning DA VERIFICARE
OP: dato non mappato in fase 1: atteso DA RICONFERMARE dopo la decisione sul mapping; fino ad allora il test è di osservazione
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C008_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C008_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C008_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C008_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C008_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C008_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C008_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-smistatore

Verifiche:
O1: pubblica sul topic "preadvising.completed.poste" (se prodotti Poste)
O2: pubblica sul topic "PSDA-20-04.SDA.EVENTTT.ANALDV" (Palmari) (1 msg per volta)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C008_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C008_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
consumer-sew-sped-poste

Verifiche:
O1: Scrittura sul DB ERMES,
 se CONDIZ_BS=FALSE sulle tabelle del vecchio Processo:
     - sew_spedizioni_poste
     - sew_spedizioni_poste_extender
     - associazioni_ldv_internazionale
     - prtn_articolo
     - prtn_collo
     - sew_spedizioni_poste_inter
     - prtn_spedizione
     - timedef_arch
     - sew_extender_scarto (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - dhl_scarti          (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - sew_inter_scarto    (solo per evitare che eventuali scarti del nuovo finiscano qui)
 oppure sulle corrispondenti tabelle del nuovo Processo (con suffisso "_2")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C008_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C009 - OK - EURODIS API - Combinazione di piu' condizioni non bloccanti su multicollo (Nessun accessorio)

### C009_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), più colli (es. 3) - scenario: Combinazione di piu' condizioni non bloccanti su multicollo (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C009_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: numero_colli = numberOfHandlingUnits, un collo[] per ogni collis[], peso in grammi per ciascun collo
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C009_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C009_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C009_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C009_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C009_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C009_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C009_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-smistatore

Verifiche:
O1: pubblica sul topic "preadvising.completed.poste" (se prodotti Poste)
O2: pubblica sul topic "PSDA-20-04.SDA.EVENTTT.ANALDV" (Palmari) (1 msg per volta)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C009_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C009_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
consumer-sew-sped-poste

Verifiche:
O1: Scrittura sul DB ERMES,
 se CONDIZ_BS=FALSE sulle tabelle del vecchio Processo:
     - sew_spedizioni_poste
     - sew_spedizioni_poste_extender
     - associazioni_ldv_internazionale
     - prtn_articolo
     - prtn_collo
     - sew_spedizioni_poste_inter
     - prtn_spedizione
     - timedef_arch
     - sew_extender_scarto (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - dhl_scarti          (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - sew_inter_scarto    (solo per evitare che eventuali scarti del nuovo finiscano qui)
 oppure sulle corrispondenti tabelle del nuovo Processo (con suffisso "_2")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C009_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C010 - OK (osservazione) - EURODIS API - Consegna presso PUDO / Punto Poste (Punto Poste)

### C010_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Consegna presso PUDO / Punto Poste (Punto Poste)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Nota: Punto Poste (deliveryService Z, pudoID) non mappato in fase 1
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C010_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: Punto Poste NON mappato: nessun codice APT000947, consegna.codice_frazionario vuoto; spedizione pubblicata come consegna ordinaria
O5: eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori; eventuali warning DA VERIFICARE
OP: dato non mappato in fase 1: atteso DA RICONFERMARE dopo la decisione sul mapping; fino ad allora il test è di osservazione
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C010_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C010_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C010_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C010_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C010_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C010_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C010_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-smistatore

Verifiche:
O1: pubblica sul topic "preadvising.completed.poste" (se prodotti Poste)
O2: pubblica sul topic "PSDA-20-04.SDA.EVENTTT.ANALDV" (Palmari) (1 msg per volta)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C010_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C010_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
consumer-sew-sped-poste

Verifiche:
O1: Scrittura sul DB ERMES,
 se CONDIZ_BS=FALSE sulle tabelle del vecchio Processo:
     - sew_spedizioni_poste
     - sew_spedizioni_poste_extender
     - associazioni_ldv_internazionale
     - prtn_articolo
     - prtn_collo
     - sew_spedizioni_poste_inter
     - prtn_spedizione
     - timedef_arch
     - sew_extender_scarto (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - dhl_scarti          (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - sew_inter_scarto    (solo per evitare che eventuali scarti del nuovo finiscano qui)
 oppure sulle corrispondenti tabelle del nuovo Processo (con suffisso "_2")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C010_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C011 - OK - EURODIS API - Delivery Service 6 (Consegna di Sabato)

### C011_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Delivery Service 6 (Consegna di Sabato)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C011_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: codici_servizi coerenti con deliveryService {deliveryService, deliveryType} (tabella 6.8 del mapper). OP: corrispondenza dei codici servizio del flusso a file con deliveryService EURODIS DA VERIFICARE
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C011_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C011_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C011_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C011_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C011_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C011_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C011_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-smistatore

Verifiche:
O1: pubblica sul topic "preadvising.completed.poste" (se prodotti Poste)
O2: pubblica sul topic "PSDA-20-04.SDA.EVENTTT.ANALDV" (Palmari) (1 msg per volta)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C011_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C011_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
consumer-sew-sped-poste

Verifiche:
O1: Scrittura sul DB ERMES,
 se CONDIZ_BS=FALSE sulle tabelle del vecchio Processo:
     - sew_spedizioni_poste
     - sew_spedizioni_poste_extender
     - associazioni_ldv_internazionale
     - prtn_articolo
     - prtn_collo
     - sew_spedizioni_poste_inter
     - prtn_spedizione
     - timedef_arch
     - sew_extender_scarto (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - dhl_scarti          (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - sew_inter_scarto    (solo per evitare che eventuali scarti del nuovo finiscano qui)
 oppure sulle corrispondenti tabelle del nuovo Processo (con suffisso "_2")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C011_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C012 - OK - EURODIS API - Delivery Service E (Consegna di Sera)

### C012_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Delivery Service E (Consegna di Sera)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C012_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: codici_servizi coerenti con deliveryService {deliveryService, deliveryType} (tabella 6.8 del mapper). OP: corrispondenza dei codici servizio del flusso a file con deliveryService EURODIS DA VERIFICARE
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C012_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
(300 regole)

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C012_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C012_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMREQUEST") - Il msg è Valido? E' in linea con la lavorazione ?
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C012_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO che consuma il topic di input , fa le sue verifiche OK e pubblica sul topic di output

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMRESPONSE") - segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C012_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
Se l'Esito asincrono da BEP è OK 
    - se la lavorazione richiede un RITIRO:
       O1: esegue una chiamata sincrona WS al sistema SAP-EM (nome servizio?) e registra il relativo esito SAP-EM
    - altrimenti:
	   NESSUNA chiamata sincrona WS al sistema SAP-EM dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") entrambi gli esiti OK/KO BEP e SAP-EM (Opzionale)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C012_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (nome servizio?)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C012_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C012_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C012_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-state-machine-handler

Verifiche:
Se nel file oggetto di elaborazione trova tutti i records "elaborati" (sia OK che con KO):

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
filePreAdvising:
- FILE_ELABORATO_CON_SUCCESSO (ST_F0006) (con spostamento del file su BS nel path "PDB/lavorati")
- FILE_ELABORATO_CON_SCARTO () (con spostamento del file su BS nel path "PDB/lavorati")
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C012_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C013 - OK - EURODIS API - Delivery Service M (Time Definite Ore 12)

### C013_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Delivery Service M (Time Definite Ore 12)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C013_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: codici_servizi coerenti con deliveryService {deliveryService, deliveryType} (tabella 6.8 del mapper). OP: corrispondenza dei codici servizio del flusso a file con deliveryService EURODIS DA VERIFICARE
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C013_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
(300 regole)

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C013_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C013_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMREQUEST") - Il msg è Valido? E' in linea con la lavorazione ?
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C013_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO che consuma il topic di input , fa le sue verifiche OK e pubblica sul topic di output

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMRESPONSE") - segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C013_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
Se l'Esito asincrono da BEP è OK 
    - se la lavorazione richiede un RITIRO:
       O1: esegue una chiamata sincrona WS al sistema SAP-EM (nome servizio?) e registra il relativo esito SAP-EM
    - altrimenti:
	   NESSUNA chiamata sincrona WS al sistema SAP-EM dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") entrambi gli esiti OK/KO BEP e SAP-EM (Opzionale)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C013_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (nome servizio?)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C013_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C013_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C013_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-state-machine-handler

Verifiche:
Se nel file oggetto di elaborazione trova tutti i records "elaborati" (sia OK che con KO):

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
filePreAdvising:
- FILE_ELABORATO_CON_SUCCESSO (ST_F0006) (con spostamento del file su BS nel path "PDB/lavorati")
- FILE_ELABORATO_CON_SCARTO () (con spostamento del file su BS nel path "PDB/lavorati")
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C013_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C014 - OK - EURODIS API - Delivery Service F (Time Definite Ore 10)

### C014_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Delivery Service F (Time Definite Ore 10)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C014_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: codici_servizi coerenti con deliveryService {deliveryService, deliveryType} (tabella 6.8 del mapper). OP: corrispondenza dei codici servizio del flusso a file con deliveryService EURODIS DA VERIFICARE
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C014_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
(300 regole)

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C014_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C014_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMREQUEST") - Il msg è Valido? E' in linea con la lavorazione ?
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C014_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO che consuma il topic di input , fa le sue verifiche OK e pubblica sul topic di output

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMRESPONSE") - segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C014_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
Se l'Esito asincrono da BEP è OK 
    - se la lavorazione richiede un RITIRO:
       O1: esegue una chiamata sincrona WS al sistema SAP-EM (nome servizio?) e registra il relativo esito SAP-EM
    - altrimenti:
	   NESSUNA chiamata sincrona WS al sistema SAP-EM dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") entrambi gli esiti OK/KO BEP e SAP-EM (Opzionale)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C014_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (nome servizio?)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C014_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C014_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C014_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-state-machine-handler

Verifiche:
Se nel file oggetto di elaborazione trova tutti i records "elaborati" (sia OK che con KO):

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
filePreAdvising:
- FILE_ELABORATO_CON_SUCCESSO (ST_F0006) (con spostamento del file su BS nel path "PDB/lavorati")
- FILE_ELABORATO_CON_SCARTO () (con spostamento del file su BS nel path "PDB/lavorati")
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C014_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C015 - OK - EURODIS API - Consegna su appuntamento (booking) (Consegna su appuntamento)

### C015_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Consegna su appuntamento (booking) (Consegna su appuntamento)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C015_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: codici_servizi coerenti con deliveryService {deliveryService, deliveryType} (tabella 6.8 del mapper). OP: corrispondenza dei codici servizio del flusso a file con deliveryService EURODIS DA VERIFICARE
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C015_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
(300 regole)

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C015_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C015_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMREQUEST") - Il msg è Valido? E' in linea con la lavorazione ?
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C015_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO che consuma il topic di input , fa le sue verifiche OK e pubblica sul topic di output

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMRESPONSE") - segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C015_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
Se l'Esito asincrono da BEP è OK 
    - se la lavorazione richiede un RITIRO:
       O1: esegue una chiamata sincrona WS al sistema SAP-EM (nome servizio?) e registra il relativo esito SAP-EM
    - altrimenti:
	   NESSUNA chiamata sincrona WS al sistema SAP-EM dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") entrambi gli esiti OK/KO BEP e SAP-EM (Opzionale)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C015_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (nome servizio?)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C015_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C015_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C015_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-state-machine-handler

Verifiche:
Se nel file oggetto di elaborazione trova tutti i records "elaborati" (sia OK che con KO):

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
filePreAdvising:
- FILE_ELABORATO_CON_SUCCESSO (ST_F0006) (con spostamento del file su BS nel path "PDB/lavorati")
- FILE_ELABORATO_CON_SCARTO () (con spostamento del file su BS nel path "PDB/lavorati")
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C015_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C016 - OK - EURODIS API - Contrassegno in contanti (Contrassegno)

### C016_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Contrassegno in contanti (Contrassegno)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C016_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: contrassegno.* = cashOnDeliveryService (amount, currency=EUR, identifierForCODCollection)
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C016_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
(300 regole)

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C016_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C016_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMREQUEST") - Il msg è Valido? E' in linea con la lavorazione ?
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C016_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO che consuma il topic di input , fa le sue verifiche OK e pubblica sul topic di output

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMRESPONSE") - segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C016_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
Se l'Esito asincrono da BEP è OK 
    - se la lavorazione richiede un RITIRO:
       O1: esegue una chiamata sincrona WS al sistema SAP-EM (nome servizio?) e registra il relativo esito SAP-EM
    - altrimenti:
	   NESSUNA chiamata sincrona WS al sistema SAP-EM dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") entrambi gli esiti OK/KO BEP e SAP-EM (Opzionale)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C016_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (nome servizio?)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C016_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C016_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C016_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-state-machine-handler

Verifiche:
Se nel file oggetto di elaborazione trova tutti i records "elaborati" (sia OK che con KO):

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
filePreAdvising:
- FILE_ELABORATO_CON_SUCCESSO (ST_F0006) (con spostamento del file su BS nel path "PDB/lavorati")
- FILE_ELABORATO_CON_SCARTO () (con spostamento del file su BS nel path "PDB/lavorati")
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C016_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C018 - OK - EURODIS API - Combinazione di servizi accessori (Time Definite Ore 12 | Contrassegno)

### C018_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Combinazione di servizi accessori (Time Definite Ore 12 | Contrassegno)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C018_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: contrassegno.* = cashOnDeliveryService (amount, currency=EUR, identifierForCODCollection); codici_servizi coerenti con deliveryService {deliveryService, deliveryType} (tabella 6.8 del mapper). OP: corrispondenza dei codici servizio del flusso a file con deliveryService EURODIS DA VERIFICARE
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C018_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
(300 regole)

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C018_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C018_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMREQUEST") - Il msg è Valido? E' in linea con la lavorazione ?
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C018_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO che consuma il topic di input , fa le sue verifiche OK e pubblica sul topic di output

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMRESPONSE") - segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C018_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
Se l'Esito asincrono da BEP è OK 
    - se la lavorazione richiede un RITIRO:
       O1: esegue una chiamata sincrona WS al sistema SAP-EM (nome servizio?) e registra il relativo esito SAP-EM
    - altrimenti:
	   NESSUNA chiamata sincrona WS al sistema SAP-EM dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") entrambi gli esiti OK/KO BEP e SAP-EM (Opzionale)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C018_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (nome servizio?)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C018_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C018_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C018_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-state-machine-handler

Verifiche:
Se nel file oggetto di elaborazione trova tutti i records "elaborati" (sia OK che con KO):

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
filePreAdvising:
- FILE_ELABORATO_CON_SUCCESSO (ST_F0006) (con spostamento del file su BS nel path "PDB/lavorati")
- FILE_ELABORATO_CON_SCARTO () (con spostamento del file su BS nel path "PDB/lavorati")
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C018_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C019 - OK - EURODIS API - Combinazione di servizi accessori (Time Definite Ore 10 | Contrassegno)

### C019_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Combinazione di servizi accessori (Time Definite Ore 10 | Contrassegno)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C019_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: contrassegno.* = cashOnDeliveryService (amount, currency=EUR, identifierForCODCollection); codici_servizi coerenti con deliveryService {deliveryService, deliveryType} (tabella 6.8 del mapper). OP: corrispondenza dei codici servizio del flusso a file con deliveryService EURODIS DA VERIFICARE
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C019_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
(300 regole)

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C019_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C019_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMREQUEST") - Il msg è Valido? E' in linea con la lavorazione ?
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C019_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO che consuma il topic di input , fa le sue verifiche OK e pubblica sul topic di output

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMRESPONSE") - segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C019_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
Se l'Esito asincrono da BEP è OK 
    - se la lavorazione richiede un RITIRO:
       O1: esegue una chiamata sincrona WS al sistema SAP-EM (nome servizio?) e registra il relativo esito SAP-EM
    - altrimenti:
	   NESSUNA chiamata sincrona WS al sistema SAP-EM dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") entrambi gli esiti OK/KO BEP e SAP-EM (Opzionale)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C019_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (nome servizio?)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C019_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C019_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C019_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-state-machine-handler

Verifiche:
Se nel file oggetto di elaborazione trova tutti i records "elaborati" (sia OK che con KO):

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
filePreAdvising:
- FILE_ELABORATO_CON_SUCCESSO (ST_F0006) (con spostamento del file su BS nel path "PDB/lavorati")
- FILE_ELABORATO_CON_SCARTO () (con spostamento del file su BS nel path "PDB/lavorati")
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C019_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C020 - OK - EURODIS API - Combinazione di servizi accessori (Consegna su appuntamento | Contrassegno)

### C020_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Combinazione di servizi accessori (Consegna su appuntamento | Contrassegno)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C020_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: contrassegno.* = cashOnDeliveryService (amount, currency=EUR, identifierForCODCollection); codici_servizi coerenti con deliveryService {deliveryService, deliveryType} (tabella 6.8 del mapper). OP: corrispondenza dei codici servizio del flusso a file con deliveryService EURODIS DA VERIFICARE
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C020_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
(300 regole)

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C020_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C020_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMREQUEST") - Il msg è Valido? E' in linea con la lavorazione ?
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C020_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO che consuma il topic di input , fa le sue verifiche OK e pubblica sul topic di output

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMRESPONSE") - segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C020_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
Se l'Esito asincrono da BEP è OK 
    - se la lavorazione richiede un RITIRO:
       O1: esegue una chiamata sincrona WS al sistema SAP-EM (nome servizio?) e registra il relativo esito SAP-EM
    - altrimenti:
	   NESSUNA chiamata sincrona WS al sistema SAP-EM dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") entrambi gli esiti OK/KO BEP e SAP-EM (Opzionale)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C020_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (nome servizio?)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C020_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C020_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C020_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-state-machine-handler

Verifiche:
Se nel file oggetto di elaborazione trova tutti i records "elaborati" (sia OK che con KO):

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
filePreAdvising:
- FILE_ELABORATO_CON_SUCCESSO (ST_F0006) (con spostamento del file su BS nel path "PDB/lavorati")
- FILE_ELABORATO_CON_SCARTO () (con spostamento del file su BS nel path "PDB/lavorati")
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C020_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C021 - OK (osservazione) - EURODIS API - Combinazione di servizi accessori (Punto Poste | Contrassegno)

### C021_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo - scenario: Combinazione di servizi accessori (Punto Poste | Contrassegno)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Nota: Punto Poste (deliveryService Z, pudoID) non mappato in fase 1
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C021_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: contrassegno.* = cashOnDeliveryService (amount, currency=EUR, identifierForCODCollection)
O4: verifica scenario: Punto Poste NON mappato: nessun codice APT000947, consegna.codice_frazionario vuoto; spedizione pubblicata come consegna ordinaria; contrassegno.* = cashOnDeliveryService, codici_servizi = APT000918
O5: eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori; eventuali warning DA VERIFICARE
OP: dato non mappato in fase 1: atteso DA RICONFERMARE dopo la decisione sul mapping; fino ad allora il test è di osservazione
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C021_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
(300 regole)

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C021_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C021_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMREQUEST") - Il msg è Valido? E' in linea con la lavorazione ?
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C021_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO che consuma il topic di input , fa le sue verifiche OK e pubblica sul topic di output

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMRESPONSE") - segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C021_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
Se l'Esito asincrono da BEP è OK 
    - se la lavorazione richiede un RITIRO:
       O1: esegue una chiamata sincrona WS al sistema SAP-EM (nome servizio?) e registra il relativo esito SAP-EM
    - altrimenti:
	   NESSUNA chiamata sincrona WS al sistema SAP-EM dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") entrambi gli esiti OK/KO BEP e SAP-EM (Opzionale)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C021_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (nome servizio?)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C021_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C021_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C021_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-state-machine-handler

Verifiche:
Se nel file oggetto di elaborazione trova tutti i records "elaborati" (sia OK che con KO):

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
filePreAdvising:
- FILE_ELABORATO_CON_SUCCESSO (ST_F0006) (con spostamento del file su BS nel path "PDB/lavorati")
- FILE_ELABORATO_CON_SCARTO () (con spostamento del file su BS nel path "PDB/lavorati")
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C021_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C022 - OK - EURODIS API - Combinazione di servizi accessori (Time Definite Ore 12 | Multicollo)

### C022_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), più colli (es. 3) - scenario: Combinazione di servizi accessori (Time Definite Ore 12 | Multicollo)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C022_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: numero_colli = numberOfHandlingUnits, un collo[] per ogni collis[], peso in grammi per ciascun collo; codici_servizi coerenti con deliveryService {deliveryService, deliveryType} (tabella 6.8 del mapper). OP: corrispondenza dei codici servizio del flusso a file con deliveryService EURODIS DA VERIFICARE
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C022_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
(300 regole)

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C022_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C022_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMREQUEST") - Il msg è Valido? E' in linea con la lavorazione ?
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C022_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO che consuma il topic di input , fa le sue verifiche OK e pubblica sul topic di output

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMRESPONSE") - segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C022_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
Se l'Esito asincrono da BEP è OK 
    - se la lavorazione richiede un RITIRO:
       O1: esegue una chiamata sincrona WS al sistema SAP-EM (nome servizio?) e registra il relativo esito SAP-EM
    - altrimenti:
	   NESSUNA chiamata sincrona WS al sistema SAP-EM dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") entrambi gli esiti OK/KO BEP e SAP-EM (Opzionale)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C022_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (nome servizio?)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C022_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C022_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C022_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-state-machine-handler

Verifiche:
Se nel file oggetto di elaborazione trova tutti i records "elaborati" (sia OK che con KO):

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
filePreAdvising:
- FILE_ELABORATO_CON_SUCCESSO (ST_F0006) (con spostamento del file su BS nel path "PDB/lavorati")
- FILE_ELABORATO_CON_SCARTO () (con spostamento del file su BS nel path "PDB/lavorati")
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C022_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C023 - OK - EURODIS API - Combinazione di servizi accessori (Contrassegno | Multicollo)

### C023_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), più colli (es. 3) - scenario: Combinazione di servizi accessori (Contrassegno | Multicollo)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C023_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: numero_colli = numberOfHandlingUnits, un collo[] per ogni collis[], peso in grammi per ciascun collo; contrassegno.* = cashOnDeliveryService (amount, currency=EUR, identifierForCODCollection)
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C023_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
(300 regole)

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C023_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C023_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMREQUEST") - Il msg è Valido? E' in linea con la lavorazione ?
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C023_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO che consuma il topic di input , fa le sue verifiche OK e pubblica sul topic di output

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMRESPONSE") - segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C023_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
Se l'Esito asincrono da BEP è OK 
    - se la lavorazione richiede un RITIRO:
       O1: esegue una chiamata sincrona WS al sistema SAP-EM (nome servizio?) e registra il relativo esito SAP-EM
    - altrimenti:
	   NESSUNA chiamata sincrona WS al sistema SAP-EM dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") entrambi gli esiti OK/KO BEP e SAP-EM (Opzionale)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C023_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (nome servizio?)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C023_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C023_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C023_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-state-machine-handler

Verifiche:
Se nel file oggetto di elaborazione trova tutti i records "elaborati" (sia OK che con KO):

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
filePreAdvising:
- FILE_ELABORATO_CON_SUCCESSO (ST_F0006) (con spostamento del file su BS nel path "PDB/lavorati")
- FILE_ELABORATO_CON_SCARTO () (con spostamento del file su BS nel path "PDB/lavorati")
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C023_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C024 - OK - EURODIS API - Combinazione di servizi accessori (Time Definite Ore 10 | Contrassegno | Multicollo)

### C024_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), più colli (es. 3) - scenario: Combinazione di servizi accessori (Time Definite Ore 10 | Contrassegno | Multicollo)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C024_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: numero_colli = numberOfHandlingUnits, un collo[] per ogni collis[], peso in grammi per ciascun collo; contrassegno.* = cashOnDeliveryService (amount, currency=EUR, identifierForCODCollection); codici_servizi coerenti con deliveryService {deliveryService, deliveryType} (tabella 6.8 del mapper). OP: corrispondenza dei codici servizio del flusso a file con deliveryService EURODIS DA VERIFICARE
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C024_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
(300 regole)

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C024_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C024_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMREQUEST") - Il msg è Valido? E' in linea con la lavorazione ?
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C024_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO che consuma il topic di input , fa le sue verifiche OK e pubblica sul topic di output

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMRESPONSE") - segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C024_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
Se l'Esito asincrono da BEP è OK 
    - se la lavorazione richiede un RITIRO:
       O1: esegue una chiamata sincrona WS al sistema SAP-EM (nome servizio?) e registra il relativo esito SAP-EM
    - altrimenti:
	   NESSUNA chiamata sincrona WS al sistema SAP-EM dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") entrambi gli esiti OK/KO BEP e SAP-EM (Opzionale)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C024_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (nome servizio?)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C024_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C024_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C024_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-state-machine-handler

Verifiche:
Se nel file oggetto di elaborazione trova tutti i records "elaborati" (sia OK che con KO):

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
filePreAdvising:
- FILE_ELABORATO_CON_SUCCESSO (ST_F0006) (con spostamento del file su BS nel path "PDB/lavorati")
- FILE_ELABORATO_CON_SCARTO () (con spostamento del file su BS nel path "PDB/lavorati")
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C024_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C025 - OK - EURODIS API - Combinazione di servizi accessori (Consegna su appuntamento | Multicollo)

### C025_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), più colli (es. 3) - scenario: Combinazione di servizi accessori (Consegna su appuntamento | Multicollo)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C025_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: numero_colli = numberOfHandlingUnits, un collo[] per ogni collis[], peso in grammi per ciascun collo; codici_servizi coerenti con deliveryService {deliveryService, deliveryType} (tabella 6.8 del mapper). OP: corrispondenza dei codici servizio del flusso a file con deliveryService EURODIS DA VERIFICARE
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C025_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
(300 regole)

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C025_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C025_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMREQUEST") - Il msg è Valido? E' in linea con la lavorazione ?
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C025_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO che consuma il topic di input , fa le sue verifiche OK e pubblica sul topic di output

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMRESPONSE") - segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C025_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
Se l'Esito asincrono da BEP è OK 
    - se la lavorazione richiede un RITIRO:
       O1: esegue una chiamata sincrona WS al sistema SAP-EM (nome servizio?) e registra il relativo esito SAP-EM
    - altrimenti:
	   NESSUNA chiamata sincrona WS al sistema SAP-EM dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") entrambi gli esiti OK/KO BEP e SAP-EM (Opzionale)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C025_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (nome servizio?)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C025_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C025_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C025_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-state-machine-handler

Verifiche:
Se nel file oggetto di elaborazione trova tutti i records "elaborati" (sia OK che con KO):

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
filePreAdvising:
- FILE_ELABORATO_CON_SUCCESSO (ST_F0006) (con spostamento del file su BS nel path "PDB/lavorati")
- FILE_ELABORATO_CON_SCARTO () (con spostamento del file su BS nel path "PDB/lavorati")
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C025_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C031 - KO MAPPER (destinatario_assente: località mancante) - EURODIS API - Località destinatario mancante (Nessun accessorio)

### C031_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (anomalia iniettata tramite mock-eurodis) - scenario: Località destinatario mancante (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C031_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: NESSUNA pubblicazione su "preadvising.pre-enrichment" per la spedizione: spedizione non mappabile (destinatario_assente: consigneeAddress senza località)
O2: log di scarto con motivo ed edReference; span eurodis.mapper.elabora; metrica eurodis_mapper_spedizioni_total (esito=non_mappabile, motivo=destinatario_assente)
O3: nessun retry né recoverer (non è un errore tecnico)

### C031_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore

Verifiche:
O1: NESSUN messaggio ricevuto con rif_spedizione = edReference dello scenario (spedizione scartata dal mapper)
O2: nessun evento PREAD_EMESSO / PREADVISING_PARZIALE_E_BLOCCATO su preadvising.evensource per la spedizione
O3: lo scarto avviene nel mapper (destinatario_assente), non nel validatore
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C031_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA (lo scarto avviene nel mapper, a valle di -in)
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C031_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C032 - KO MAPPER (destinatario_assente: CAP mancante) - EURODIS API - CAP destinatario mancante (Nessun accessorio)

### C032_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (anomalia iniettata tramite mock-eurodis) - scenario: CAP destinatario mancante (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C032_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: NESSUNA pubblicazione su "preadvising.pre-enrichment" per la spedizione: spedizione non mappabile (destinatario_assente: consigneeAddress senza CAP)
O2: log di scarto con motivo ed edReference; span eurodis.mapper.elabora; metrica eurodis_mapper_spedizioni_total (esito=non_mappabile, motivo=destinatario_assente)
O3: nessun retry né recoverer (non è un errore tecnico)

### C032_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore

Verifiche:
O1: NESSUN messaggio ricevuto con rif_spedizione = edReference dello scenario (spedizione scartata dal mapper)
O2: nessun evento PREAD_EMESSO / PREADVISING_PARZIALE_E_BLOCCATO su preadvising.evensource per la spedizione
O3: lo scarto avviene nel mapper (destinatario_assente), non nel validatore
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C032_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA (lo scarto avviene nel mapper, a valle di -in)
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C032_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C037 - WARNING MAPPER (valuta contrassegno vuota) - EURODIS API - Valuta contrassegno vuota (Contrassegno)

### C037_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (anomalia iniettata tramite mock-eurodis) - scenario: Valuta contrassegno vuota (Contrassegno)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C037_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: spedizione PUBBLICATA con warning: cashOnDeliveryService.currency vuota → warning sulla valuta. OP: DA VERIFICARE se la valuta vuota genera lo stesso warning di "valuta diversa da EUR"
O5: eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C037_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore

Verifiche:
O1: messaggio ricevuto da preadvising.pre-enrichment con canale EUD_INVIOSYSTEM
O2: preadvising.evensource: PREAD_EMESSO (eventType="ST_R0002"; aggregateType: "ldv")
OP: comportamento del validatore sul campo interessato per il canale EUD_INVIOSYSTEM DA DEFINIRE
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C037_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C037_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C040 - OK MAPPER (consignorsColloBarcode vuoto) - EURODIS API - consignorsColloBarcode vuoto, non mappato (Nessun accessorio)

### C040_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: spedizione fittizia (anomalia iniettata tramite mock-eurodis) - scenario: consignorsColloBarcode vuoto, non mappato (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C040_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: collis[].consignorsColloBarcode vuoto: campo NON mappato, nessun effetto; collo[].id_ldv = deliveryPartnerBarcode valorizzato.
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C040_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore

Verifiche:
O1: messaggio ricevuto da preadvising.pre-enrichment con canale EUD_INVIOSYSTEM
O2: preadvising.evensource: PREAD_EMESSO (eventType="ST_R0002"; aggregateType: "ldv")
OP: comportamento del validatore sul campo interessato per il canale EUD_INVIOSYSTEM DA DEFINIRE
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C040_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C040_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C041 - OK MAPPER (europlateBarcode vuoto) - EURODIS API - europlateBarcode vuoto, id_ldv_itz non valorizzato (Nessun accessorio)

### C041_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: spedizione fittizia (anomalia iniettata tramite mock-eurodis) - scenario: europlateBarcode vuoto, id_ldv_itz non valorizzato (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C041_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: collis[].europlateBarcode vuoto → internazionale.id_ldv_itz vuoto, spedizione pubblicata senza scarto
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C041_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore

Verifiche:
O1: messaggio ricevuto da preadvising.pre-enrichment con canale EUD_INVIOSYSTEM
O2: preadvising.evensource: PREAD_EMESSO (eventType="ST_R0002"; aggregateType: "ldv")
OP: comportamento del validatore sul campo interessato per il canale EUD_INVIOSYSTEM DA DEFINIRE
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C041_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C041_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C043 - OK MAPPER (europlateBarcode vuoto) - EURODIS API - Europlate mancante su un collo di multicollo (Nessun accessorio)

### C043_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: spedizione fittizia (anomalia iniettata tramite mock-eurodis) - scenario: Europlate mancante su un collo di multicollo (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C043_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: multicollo con europlateBarcode vuoto sul primo collo e valorizzato sul secondo → internazionale.id_ldv_itz = primo europlateBarcode non vuoto e diverso da "0"; numero_colli = numberOfHandlingUnits, un collo[] per ogni collis[], peso in grammi per ciascun collo
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C043_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore

Verifiche:
O1: messaggio ricevuto da preadvising.pre-enrichment con canale EUD_INVIOSYSTEM
O2: preadvising.evensource: PREAD_EMESSO (eventType="ST_R0002"; aggregateType: "ldv")
OP: comportamento del validatore sul campo interessato per il canale EUD_INVIOSYSTEM DA DEFINIRE
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C043_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C043_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C047 - KO MAPPER (destinatario_assente: località e CAP mancanti) - EURODIS API - Località e CAP destinatario mancanti (Nessun accessorio)

### C047_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (anomalia iniettata tramite mock-eurodis) - scenario: Località e CAP destinatario mancanti (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C047_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: NESSUNA pubblicazione su "preadvising.pre-enrichment" per la spedizione: spedizione non mappabile (destinatario_assente: consigneeAddress senza località e senza CAP)
O2: log di scarto con motivo ed edReference; span eurodis.mapper.elabora; metrica eurodis_mapper_spedizioni_total (esito=non_mappabile, motivo=destinatario_assente)
O3: nessun retry né recoverer (non è un errore tecnico)

### C047_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore

Verifiche:
O1: NESSUN messaggio ricevuto con rif_spedizione = edReference dello scenario (spedizione scartata dal mapper)
O2: nessun evento PREAD_EMESSO / PREADVISING_PARZIALE_E_BLOCCATO su preadvising.evensource per la spedizione
O3: lo scarto avviene nel mapper (destinatario_assente), non nel validatore
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C047_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA (lo scarto avviene nel mapper, a valle di -in)
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C047_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C048 - OK MAPPER (consignorsColloBarcode ed europlateBarcode vuoti) - EURODIS API - Multicollo con consignorsColloBarcode ed europlateBarcode mancanti (Nessun accessorio)

### C048_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: spedizione fittizia (anomalia iniettata tramite mock-eurodis) - scenario: Multicollo con consignorsColloBarcode ed europlateBarcode mancanti (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C048_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: multicollo con consignorsColloBarcode (non mappato) ed europlateBarcode vuoti → spedizione pubblicata, id_ldv_itz vuoto, collo[].id_ldv = deliveryPartnerBarcode; numero_colli = numberOfHandlingUnits, un collo[] per ogni collis[], peso in grammi per ciascun collo
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C048_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore

Verifiche:
O1: messaggio ricevuto da preadvising.pre-enrichment con canale EUD_INVIOSYSTEM
O2: preadvising.evensource: PREAD_EMESSO (eventType="ST_R0002"; aggregateType: "ldv")
OP: comportamento del validatore sul campo interessato per il canale EUD_INVIOSYSTEM DA DEFINIRE
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C048_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C048_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C049 - KO MAPPER (destinatario_assente: CAP mancante) - EURODIS API - CAP destinatario mancante e valuta contrassegno vuota (Contrassegno)

### C049_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (anomalia iniettata tramite mock-eurodis) - scenario: CAP destinatario mancante e valuta contrassegno vuota (Contrassegno)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C049_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: NESSUNA pubblicazione su "preadvising.pre-enrichment" per la spedizione: spedizione non mappabile (destinatario_assente: consigneeAddress senza CAP; la valuta vuota non produce effetti perché la spedizione è scartata - DA VERIFICARE)
O2: log di scarto con motivo ed edReference; span eurodis.mapper.elabora; metrica eurodis_mapper_spedizioni_total (esito=non_mappabile, motivo=destinatario_assente)
O3: nessun retry né recoverer (non è un errore tecnico)

### C049_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore

Verifiche:
O1: NESSUN messaggio ricevuto con rif_spedizione = edReference dello scenario (spedizione scartata dal mapper)
O2: nessun evento PREAD_EMESSO / PREADVISING_PARZIALE_E_BLOCCATO su preadvising.evensource per la spedizione
O3: lo scarto avviene nel mapper (destinatario_assente), non nel validatore
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C049_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA (lo scarto avviene nel mapper, a valle di -in)
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C049_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C050 - KO BEP (114) - EURODIS API - Contratto non riconosciuto da BEP (NO_ACCESSORIO)

### C050_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con contratto non riconosciuto da BEP (errore BEP 114). OP: valore di contratto da usare DA DEFINIRE con BEP
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C050_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C050_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C050_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C050_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C050_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C050_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C050_TC008

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C050_TC009

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C051 - KO BEP (115) - EURODIS API - Centro di costo non riconosciuto da BEP (NO_ACCESSORIO)

### C051_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con centro di costo non riconosciuto da BEP (errore BEP 115). OP: valore di centro di costo da usare DA DEFINIRE con BEP
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C051_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C051_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C051_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C051_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C051_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C051_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C051_TC008

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C051_TC009

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C052 - Misto OK/KO - EURODIS API - Scarico con più spedizioni, di cui una non mappabile e una non identificabile (NO_ACCESSORIO)

### C052_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: scarico con 3 spedizioni fittizie: A valida; B con consigneeAddress senza CAP (non mappabile); C senza edReference (NON_IDENTIFICABILE)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (3 ricevute, 2 inviate, 1 non identificabile), stato finale INVIO_PARZIALE
O2: eurodis_spedizioni: A e B stato_invio=INVIATA; C stato_invio=NON_IDENTIFICABILE, JSON conservato, NON pubblicata
O3: preadvising.evensource: ST_F0002, poi ST_F0005 (aggregateType=file, canale=EUD_INVIOSYSTEM, linkFileFisicoInviato=eurodis_scarichi/<id>); numeroRecord = numero di spedizioni del grezzo, comprese le non identificabili
O4: preadvising.eud.pre.build: 2 messaggi (A, B) con chiave edReference, corpo identico e header completi (idFile = id_file di O1)
O5: span eurodis.receive_pan.get ed eurodis.elaborazione; metrica eurodis_in_evento_total
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C052_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: A pubblicata su preadvising.pre-enrichment; B NON pubblicata (destinatario_assente); C non ricevuta (non inviata da -in)
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C052_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
(300 regole)

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C052_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C052_TC005

- fase: Verifiche formali, Arricchimento (seconda esecuzione)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" (* NEW - FASE 2 *) 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore (con "Message"."tipo_lavorazione": "validato")

2 MSG (ha risposto solo il NORM oppure PDB) non fa nulla

3 MSG (hanno risposto entrambi NORM e PDB) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP o SAP-EM *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C052_TC006

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMREQUEST") - Il msg è Valido? E' in linea con la lavorazione ?
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C052_TC007

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO che consuma il topic di input , fa le sue verifiche OK e pubblica sul topic di output

Verifiche:
O1: pubblica sul topic "PACCHI.BEP.MEDIATION.INVIOSYSTEMRESPONSE") - segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C052_TC008

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv bep

Verifiche:
Se l'Esito asincrono da BEP è OK 
    - se la lavorazione richiede un RITIRO:
       O1: esegue una chiamata sincrona WS al sistema SAP-EM (nome servizio?) e registra il relativo esito SAP-EM
    - altrimenti:
	   NESSUNA chiamata sincrona WS al sistema SAP-EM dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") entrambi gli esiti OK/KO BEP e SAP-EM (Opzionale)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C052_TC009

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (nome servizio?)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C052_TC010

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C052_TC011

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIO_PARZIALE
O2: eurodis_spedizioni: A e B stato_invio=INVIATA; C stato_invio=NON_IDENTIFICABILE
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C052_TC012

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-state-machine-handler

Verifiche:
Se nel file oggetto di elaborazione trova tutti i records "elaborati" (sia OK che con KO):

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
filePreAdvising:
- FILE_ELABORATO_CON_SUCCESSO (ST_F0006) (con spostamento del file su BS nel path "PDB/lavorati")
- FILE_ELABORATO_CON_SCARTO () (con spostamento del file su BS nel path "PDB/lavorati")
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C052_TC013

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C053 - OK API (HTTP 404: nessuna spedizione nuova) - EURODIS API - Nessuna spedizione nuova

### C053_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: mock-eurodis configurato per rispondere HTTP 404 (404 = nessuna spedizione nuova, esito regolare)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: GET /shipments/v1 eseguita una sola volta dal job di scarico; risposta HTTP 404
O2: eurodis_scarichi: riga dell'esecuzione con esito HTTP 404 registrato; nessuna riga in eurodis_spedizioni
O3: nessun messaggio su preadvising.eud.pre.build né su preadvising.evensource
O4: span eurodis.scarico ed eurodis.receive_pan.get senza errore; nessun alert (RF-05, RNF-04); metrica eurodis_in_chiamata_total{esito=404} +1
Stato finale atteso dello scarico: NESSUNA_SPEDIZIONE (ce-dichiarato-eurodis-in.md 0.6.1, sez. stati dello scarico)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C053_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale NESSUNA_SPEDIZIONE
O2: eurodis_spedizioni: nessuna riga per lo scarico
O3: preadvising.evensource: nessun evento ST_F000x per lo scarico; preadvising.eud.pre.build: nessun messaggio
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C054 - OK API (array vuoto) - EURODIS API - Nessuna spedizione da scaricare

### C054_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: mock-eurodis configurato per rispondere HTTP 200 con array vuoto []
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: GET /shipments/v1 con risposta HTTP 200 e corpo []
O2: eurodis_scarichi: riga con esito HTTP 200, corpo [] e conteggi a 0; nessuna riga in eurodis_spedizioni
O3: nessun messaggio su preadvising.eud.pre.build
Nessun evento ST_F0002/ST_F0005: per uno scarico vuoto non si crea il file fittizio
Stato finale atteso dello scarico: NESSUNA_SPEDIZIONE (ce-dichiarato-eurodis-in.md 0.6.1, sez. stati dello scarico)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C054_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale NESSUNA_SPEDIZIONE
O2: eurodis_spedizioni: nessuna riga per lo scarico
O3: preadvising.evensource: nessun evento per lo scarico
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C055 - KO API (HTTP 401) - EURODIS API - Chiave X-API-Key non valida

### C055_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: mock-eurodis configurato per rispondere HTTP 401 (X-API-Key errata nel secret dell'ambiente di test)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: GET /shipments/v1 eseguita una sola volta dal job di scarico; risposta HTTP 401
O2: eurodis_scarichi: riga dell'esecuzione con esito HTTP 401 registrato; nessuna riga in eurodis_spedizioni
O3: nessun messaggio su preadvising.eud.pre.build né su preadvising.evensource
O4: span eurodis.receive_pan.get con errore; metrica eurodis_in_evento_total con esito di errore
O5: nessun dato nei log che esponga il valore della chiave
Stato finale atteso dello scarico: ERRORE_CHIAMATA (ce-dichiarato-eurodis-in.md 0.6.1, sez. stati dello scarico)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C055_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale ERRORE_CHIAMATA
O2: eurodis_spedizioni: nessuna riga per lo scarico
O3: preadvising.evensource: nessun evento ST_F000x per lo scarico; preadvising.eud.pre.build: nessun messaggio
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C056 - KO API (HTTP 424) - EURODIS API - Errore di dipendenza lato EURODIS

### C056_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: mock-eurodis configurato per rispondere HTTP 424 (errore di dipendenza lato EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: GET /shipments/v1 eseguita una sola volta dal job di scarico; risposta HTTP 424
O2: eurodis_scarichi: riga dell'esecuzione con esito HTTP 424 registrato; nessuna riga in eurodis_spedizioni
O3: nessun messaggio su preadvising.eud.pre.build né su preadvising.evensource
O4: span eurodis.receive_pan.get con errore; metrica eurodis_in_evento_total con esito di errore
Stato finale atteso dello scarico: ERRORE_CHIAMATA (ce-dichiarato-eurodis-in.md 0.6.1, sez. stati dello scarico)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C056_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale ERRORE_CHIAMATA
O2: eurodis_spedizioni: nessuna riga per lo scarico
O3: preadvising.evensource: nessun evento ST_F000x per lo scarico; preadvising.eud.pre.build: nessun messaggio
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C057 - KO API (HTTP 451) - EURODIS API - Scarico da recuperare con rilettura puntuale

### C057_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: mock-eurodis configurato per rispondere HTTP 451 (anomalia iniettata)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: GET /shipments/v1 eseguita una sola volta dal job di scarico; risposta HTTP 451
O2: eurodis_scarichi: riga dell'esecuzione con esito HTTP 451 registrato; nessuna riga in eurodis_spedizioni
O3: nessun messaggio su preadvising.eud.pre.build né su preadvising.evensource
O4: span eurodis.receive_pan.get con errore; metrica eurodis_in_evento_total con esito di errore
O5: lo scarico risulta da recuperare con la rilettura puntuale (vedi catena C080)
Stato finale atteso dello scarico: ERRORE_CHIAMATA (ce-dichiarato-eurodis-in.md 0.6.1, sez. stati dello scarico)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C057_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale ERRORE_CHIAMATA
O2: eurodis_spedizioni: nessuna riga per lo scarico
O3: preadvising.evensource: nessun evento ST_F000x per lo scarico; preadvising.eud.pre.build: nessun messaggio
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C058 - KO API (HTTP 500) - EURODIS API - Errore interno EURODIS

### C058_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: mock-eurodis configurato per rispondere HTTP 500 (errore interno)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: GET /shipments/v1 eseguita una sola volta dal job di scarico; risposta HTTP 500
O2: eurodis_scarichi: riga dell'esecuzione con esito HTTP 500 registrato; nessuna riga in eurodis_spedizioni
O3: nessun messaggio su preadvising.eud.pre.build né su preadvising.evensource
O4: span eurodis.receive_pan.get con errore; metrica eurodis_in_evento_total con esito di errore
Stato finale atteso dello scarico: ERRORE_CHIAMATA (ce-dichiarato-eurodis-in.md 0.6.1, sez. stati dello scarico)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C058_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale ERRORE_CHIAMATA
O2: eurodis_spedizioni: nessuna riga per lo scarico
O3: preadvising.evensource: nessun evento ST_F000x per lo scarico; preadvising.eud.pre.build: nessun messaggio
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C059 - KO API (timeout connessione 10 s) - EURODIS API - EURODIS non raggiungibile

### C059_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: mock-eurodis non raggiungibile (es. servizio fermo o porta chiusa) per più di 10 s
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: la GET /shipments/v1 va in timeout di connessione dopo 10 s
O2: eurodis_scarichi: esecuzione registrata con errore di timeout; nessuna riga in eurodis_spedizioni
O3: nessun messaggio su preadvising.eud.pre.build né su preadvising.evensource
O4: span eurodis.receive_pan.get con errore di timeout
Stato finale atteso dello scarico: ERRORE_CHIAMATA (ce-dichiarato-eurodis-in.md 0.6.1, sez. stati dello scarico)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C059_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale ERRORE_CHIAMATA
O2: eurodis_spedizioni: nessuna riga per lo scarico
O3: preadvising.evensource: nessun evento ST_F000x per lo scarico; preadvising.eud.pre.build: nessun messaggio
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C060 - KO API (timeout lettura 120 s) - EURODIS API - Risposta EURODIS troppo lenta

### C060_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: mock-eurodis configurato con ritardo di risposta superiore a 120 s
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: la GET /shipments/v1 va in timeout di lettura dopo 120 s
O2: eurodis_scarichi: esecuzione registrata con errore di timeout; nessuna riga in eurodis_spedizioni
O3: nessun messaggio su preadvising.eud.pre.build né su preadvising.evensource
O4: span eurodis.receive_pan.get con errore di timeout
O5: la risposta arrivata in ritardo NON viene salvata; lo scarico è da recuperare con la rilettura puntuale (vedi catena C080)
Stato finale atteso dello scarico: ERRORE_CHIAMATA (ce-dichiarato-eurodis-in.md 0.6.1, sez. stati dello scarico)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C060_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale ERRORE_CHIAMATA
O2: eurodis_spedizioni: nessuna riga per lo scarico
O3: preadvising.evensource: nessun evento ST_F000x per lo scarico; preadvising.eud.pre.build: nessun messaggio
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C061 - KO API (pod caduto durante la chiamata) - EURODIS API - Scarico rimasto in CHIAMATA_IN_CORSO

### C061_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: mock-eurodis con ritardo di risposta; il pod di ce-dichiarato-eurodis-in viene arrestato durante la GET
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: eurodis_scarichi: la riga dell'esecuzione resta in stato CHIAMATA_IN_CORSO
O2: nessun messaggio su preadvising.eud.pre.build né su preadvising.evensource
O3: al riavvio del pod: OP: comportamento sullo scarico rimasto in CHIAMATA_IN_CORSO DA DEFINIRE
O4: ShedLock rilasciato alla scadenza del lock; lo scheduler successivo riparte regolarmente
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C061_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale CHIAMATA_IN_CORSO (OP: evoluzione dopo il riavvio DA DEFINIRE)
O2: eurodis_spedizioni: nessuna riga per lo scarico
O3: preadvising.evensource: nessun evento ST_F000x per lo scarico; preadvising.eud.pre.build: nessun messaggio
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C062 - KO API (grezzo non JSON) - EURODIS API - Scarico NON_ELABORABILE

### C062_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: mock-eurodis configurato per rispondere HTTP 200 con corpo non JSON
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: eurodis_scarichi: riga con esito HTTP 200 e corpo identico al grezzo ricevuto
O2: il job di elaborazione non riesce a dividere il grezzo: scarico NON_ELABORABILE; nessuna riga in eurodis_spedizioni
O3: nessun messaggio su preadvising.eud.pre.build
O4: span eurodis.elaborazione con errore
Nessun evento su preadvising.evensource: nessun file fittizio per un grezzo non JSON
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C062_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale NON_ELABORABILE
O2: eurodis_spedizioni: nessuna riga per lo scarico
O3: preadvising.evensource: nessun evento per lo scarico
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C063 - OK (servizio disabilitato) - EURODIS API - EURODIS_IN_ABILITATO=false, nessuno scarico

### C063_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=false; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: spedizioni disponibili su mock-eurodis; ce-dichiarato-eurodis-in con EURODIS_IN_ABILITATO=false
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: nessuna chiamata GET /shipments/v1 verso EURODIS (log di mock-eurodis senza accessi)
O2: nessuna nuova riga in eurodis_scarichi né in eurodis_spedizioni
O3: nessun messaggio su preadvising.eud.pre.build né su preadvising.evensource
O4: riportando il flag a true, lo scheduler successivo esegue lo scarico regolarmente
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C063_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale nessuna riga creata mentre il servizio è disabilitato
O2: eurodis_spedizioni: nessuna riga per lo scarico
O3: preadvising.evensource: nessun evento ST_F000x per lo scarico; preadvising.eud.pre.build: nessun messaggio
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C064 - OK (ShedLock con 2 pod) - EURODIS API - Un solo scarico per esecuzione

### C064_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: ce-dichiarato-eurodis-in scalato a 2 pod; 1 spedizione fittizia disponibile su mock-eurodis (es. edReference 7319003746401)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: a ogni esecuzione dello scheduler un solo pod esegue la GET /shipments/v1 (ShedLock su PostgreSQL); l'altro pod salta l'esecuzione
O2: eurodis_scarichi: una sola riga per esecuzione
O3: eurodis_spedizioni: 1 riga, numero_ricezioni=1
O4: preadvising.eud.pre.build: 1 solo messaggio per la spedizione (nessun doppione)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C064_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: una sola coppia ST_F0002/ST_F0005 per l'idFile
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C065 - KO (spedizione non identificabile) - EURODIS API - Spedizione senza edReference, scarico INVIO_PARZIALE

### C065_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: scarico con 2 spedizioni fittizie: A valida (es. edReference 7319003746401), B senza edReference
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: eurodis_scarichi: riga con esito HTTP 200, corpo identico al grezzo, conteggi coerenti (2 ricevute, 1 inviata, 1 non identificabile)
O2: eurodis_spedizioni: A stato_invio=INVIATA; B stato_invio=NON_IDENTIFICABILE con JSON conservato
O3: preadvising.evensource: ST_F0002, poi ST_F0005 (canale=EUD_INVIOSYSTEM); numeroRecord = numero di spedizioni del grezzo, comprese le non identificabili
O4: preadvising.eud.pre.build: 1 messaggio (A); B NON pubblicata
O5: span eurodis.elaborazione; metrica eurodis_in_evento_total
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C065_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIO_PARZIALE
O2: eurodis_spedizioni: A stato_invio=INVIATA; B stato_invio=NON_IDENTIFICABILE
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C065_TC003

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C066 - KO MAPPER (destinatario_assente) - EURODIS API - consigneeAddress null

### C066_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401) con consigneeAddress = null (anomalia iniettata tramite mock-eurodis)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C066_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: NESSUNA pubblicazione su "preadvising.pre-enrichment" per la spedizione: spedizione non mappabile (destinatario_assente: consigneeAddress null)
O2: log di scarto con motivo ed edReference; span eurodis.mapper.elabora; metrica eurodis_mapper_spedizioni_total (esito=non_mappabile, motivo=destinatario_assente)
O3: nessun retry né recoverer (non è un errore tecnico)

### C066_TC003

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA (lo scarto avviene nel mapper, a valle di -in)
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C066_TC004

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C067 - WARNING MAPPER (data spedizione vuota) - EURODIS API - entranceTimestamp vuoto

### C067_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con entranceTimestamp vuoto
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C067_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: spedizione PUBBLICATA con warning: entranceTimestamp vuoto → data_spedizione/ora_spedizione non valorizzate. OP: fallback su clearanceTimestamp DA DECIDERE (DF-01)
O5: eurodis_mapper_campo_mancante_total{campo=data_spedizione} +1 (RF-07); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C067_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C067_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C067_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C067_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C067_TC007

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per tutte le spedizioni dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C067_TC008

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C068 - WARNING MAPPER (id_ldv vuoto) - EURODIS API - deliveryPartnerBarcode assente

### C068_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con collis[].deliveryPartnerBarcode vuoto
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C068_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: spedizione PUBBLICATA con warning: collo[].id_ldv vuoto (deliveryPartnerBarcode assente)
O5: eurodis_mapper_campo_mancante_total{campo=collo[].id_ldv} +1 (RF-07); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C068_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C068_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C068_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)
O4: verificare il comportamento di ce-dichiarato-ldv-pdb con collo.id_ldv vuoto. OP: esito atteso (KO BEP o default) DA DEFINIRE

### C068_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C068_TC007

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per tutte le spedizioni dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C068_TC008

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C069 - KO VALID (1083: peso assente) - EURODIS API - weightOfUnit assente

### C069_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con collis[].weightOfUnit vuoto
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C069_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: spedizione PUBBLICATA con warning: collo[].peso non valorizzato
O5: eurodis_mapper_campo_mancante_total{campo=collo[].peso} +1 (RF-07); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C069_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1083 "Collo Peso fuori range (ammessi valori tra 0 e 9.999.900 grammi)"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
O4: il mapper imposta peso = 0 (RF-07, warning campo_mancante) e il validatore lo rifiuta con 1083
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C069_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per tutte le spedizioni dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C069_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C070 - WARNING MAPPER (colli incoerenti) - EURODIS API - numberOfHandlingUnits diverso dal numero di collis

### C070_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con numberOfHandlingUnits=3 e 2 elementi in collis[]
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C070_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: spedizione PUBBLICATA con warning: numero_colli = numberOfHandlingUnits (3) diverso dal numero di collo[] (2). OP: valore da usare per numero_colli DA VERIFICARE
O5: eurodis_mapper_avvisi_total{motivo=colli_incoerenti} +1; eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C070_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C070_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C070_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C070_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C070_TC007

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per tutte le spedizioni dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C070_TC008

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C071 - WARNING MAPPER (valuta non EUR) - EURODIS API - Contrassegno in valuta diversa da EUR

### C071_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con cashOnDeliveryService.currency diversa da EUR (es. CHF)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C071_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: spedizione PUBBLICATA con warning: contrassegno con valuta diversa da EUR
O5: eurodis_mapper_avvisi_total{motivo=valuta_non_eur} +1; eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C071_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C071_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C071_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C071_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C071_TC007

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per tutte le spedizioni dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C071_TC008

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C072 - WARNING MAPPER (tipo contrassegno sconosciuto) - EURODIS API - Tipo contrassegno non previsto

### C072_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con cashOnDeliveryService di tipo non previsto dalla tabella 6.8 del mapper
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C072_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: spedizione PUBBLICATA con warning: tipo contrassegno sconosciuto: codice servizio non determinato
O5: eurodis_mapper_avvisi_total{motivo=tipo_cod_sconosciuto} +1; eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C072_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C072_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C072_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C072_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C072_TC007

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per tutte le spedizioni dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C072_TC008

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C073 - WARNING MAPPER (ce-anagrafica KO) - EURODIS API - Codici nazione non risolti

### C073_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia valida; servizio ce-anagrafica non disponibile o in errore durante il mapping
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C073_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: spedizione PUBBLICATA con warning: codici nazione ISO3/ISO4 non risolti da ce-anagrafica; il mapper pubblica comunque, senza retry (RF-15): per IT/ITA/ITA1 usa le codifiche italiane di configurazione; metrica eurodis_mapper_avvisi_total{motivo=anagrafica_ko}
O5: eurodis_mapper_avvisi_total{motivo=anagrafica_ko} +1; eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C073_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C073_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C073_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C073_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C073_TC007

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per tutte le spedizioni dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C073_TC008

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C074 - KO TECNICO (Kafka pre.build non disponibile) - EURODIS API - Spedizione in ERRORE_INVIO dopo i tentativi

### C074_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401); topic preadvising.eud.pre.build non raggiungibile da ce-dichiarato-eurodis-in. OP: modalità di simulazione dell'indisponibilità Kafka DA DEFINIRE
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: eurodis_scarichi: riga con esito HTTP 200 e corpo identico al grezzo
O2: eurodis_spedizioni: la spedizione resta stato_invio=DA_INVIARE; nuovi tentativi di invio dopo 5 minuti, poi ogni 2 minuti, fino a 10 tentativi
O3: dopo il 10° tentativo fallito: stato_invio=ERRORE_INVIO
O4: nessun messaggio su preadvising.eud.pre.build; span eurodis.elaborazione con errore; metrica eurodis_in_evento_total con esito di errore
O5: ripristinato Kafka prima del 10° tentativo, la spedizione viene pubblicata e passa a INVIATA
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C074_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale NESSUN_INVIO
O2: eurodis_spedizioni: stato_invio=ERRORE_INVIO dopo 10 tentativi falliti
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C075 - KO TECNICO (errore Kafka nel mapper) - EURODIS API - Retry e recoverer del mapper

### C075_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401); pubblicazione su preadvising.pre-enrichment non disponibile per ce-dichiarato-eurodis-mapper
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C075_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: il consumo del messaggio da preadvising.eud.pre.build fallisce per errore tecnico Kafka
O2: 3 tentativi a 2 s di distanza (log e span eurodis.mapper.elabora con errore)
O3: esauriti i tentativi interviene il recoverer: messaggio non perso e offset gestito come da specifica
OP: Dead Letter Topic per il mapper DA DECIDERE (PA-32)
O4: nessun messaggio su preadvising.pre-enrichment per la spedizione finché l'errore persiste

### C075_TC003

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA (l'errore avviene nel mapper, a valle di -in)
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C076 - KO TECNICO (evensource non disponibile) - EURODIS API - Scarico rimasto DA_ELABORARE

### C076_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401); topic preadvising.evensource non raggiungibile da ce-dichiarato-eurodis-in. OP: modalità di simulazione DA DEFINIRE
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: eurodis_scarichi: riga con esito HTTP 200 e corpo identico al grezzo
O2: la pubblicazione di ST_F0002/ST_F0005 fallisce: lo scarico resta DA_ELABORARE
O3: nessun messaggio su preadvising.eud.pre.build (gli eventi di file vanno emessi prima delle spedizioni)
O4: ripristinato il topic, il job di elaborazione successivo riprende lo scarico ed emette eventi e spedizioni
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C076_TC002

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale DA_ELABORARE finché il topic non è disponibile; poi INVIATO_TUTTO
O2: eurodis_spedizioni: nessuna riga finché lo scarico resta DA_ELABORARE; poi stato_invio=INVIATA
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

## C077 - OK (reinvio stessa spedizione) - EURODIS API - Spedizione ricevuta due volte

### C077_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: stessa spedizione fittizia (es. edReference 7319003746401) restituita da mock-eurodis in due scarichi successivi
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: eurodis_scarichi: 2 righe (una per scarico), ciascuna con il proprio id_file
O2: eurodis_spedizioni: 1 sola riga per l'edReference con numero_ricezioni=2 e json aggiornato
O3: preadvising.eud.pre.build: la spedizione viene pubblicata a ogni ricezione (header idFile del rispettivo scarico)
O4: preadvising.evensource: ST_F0002/ST_F0005 per ciascun idFile
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C077_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: 2 messaggi su preadvising.pre-enrichment con lo stesso rif_spedizione e id_preadvising diversi
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C077_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)
O4: seconda ricezione della stessa spedizione (stessa LDV, nuovo id_preadvising): il validatore la scarta con 099 "Ldv presente" (gestisciDuplicatoBase), eventi ST_R0002 e ST_R0003 PREAD_DUPLICATO, nessun messaggio su preadvising.enrichment

### C077_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO per entrambi gli scarichi
O2: eurodis_spedizioni: 1 riga, numero_ricezioni=2, stato_invio=INVIATA
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C077_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C078 - OK (recupero manuale) - EURODIS API - Recupero di spedizioni per edReference

### C078_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401) già scaricata in precedenza; richiesta di recupero manuale tramite proprietà eurodis.in.recupero.ed-references
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: richiesta registrata nella tabella eurodis_richieste_manuali con l'elenco degli edReference
O2: chiamata a EURODIS per gli edReference richiesti; grezzo salvato in eurodis_scarichi
O3: eurodis_spedizioni aggiornata; spedizione pubblicata su preadvising.eud.pre.build con header completi
O4: eurodis_richieste_manuali: richiesta marcata come eseguita; esito = stato dello scarico di rilettura (RECUPERO) o esito del reinvio (RIPUBBLICA), chiave (tipo, ed_reference)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C078_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: spedizione recuperata pubblicata su preadvising.pre-enrichment
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C078_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C078_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per tutte le spedizioni dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C078_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C079 - OK (ripubblicazione) - EURODIS API - Ripubblicazione di spedizioni già scaricate

### C079_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401) già presente in eurodis_spedizioni; richiesta di ripubblicazione tramite proprietà eurodis.in.ripubblica.ed-references
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: richiesta registrata in eurodis_richieste_manuali
O2: la spedizione viene ripubblicata su preadvising.eud.pre.build con il json conservato in eurodis_spedizioni
OP: DA VERIFICARE se la ripubblicazione avviene senza nuova chiamata a EURODIS (nessun nuovo accesso nel log di mock-eurodis)
O3: eurodis_spedizioni: stato_invio=INVIATA
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C079_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: spedizione ripubblicata su preadvising.pre-enrichment
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C079_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)
O4: seconda ricezione della stessa spedizione (stessa LDV, nuovo id_preadvising): il validatore la scarta con 099 "Ldv presente" (gestisciDuplicatoBase), eventi ST_R0002 e ST_R0003 PREAD_DUPLICATO, nessun messaggio su preadvising.enrichment

### C079_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per tutte le spedizioni dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C079_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C080 - OK (rilettura puntuale) - EURODIS API - Recupero entro 60 giorni dopo timeout

### C080_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401) non scaricata a causa di un timeout di lettura precedente (vedi catena C060); rilettura puntuale entro 60 giorni
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: rilettura puntuale eseguita entro la finestra di 60 giorni; grezzo salvato in eurodis_scarichi con nuovo id_file
O2: eurodis_spedizioni: riga creata/aggiornata con stato_invio=INVIATA
O3: preadvising.evensource: ST_F0002/ST_F0005 per il nuovo idFile
O4: preadvising.eud.pre.build: spedizione pubblicata con header completi
OP: modalità di attivazione della rilettura puntuale (automatica o manuale) DA VERIFICARE sulla specifica
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C080_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: spedizione recuperata pubblicata su preadvising.pre-enrichment
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C080_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C080_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per tutte le spedizioni dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C080_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C081 - [IN ATTESA DECISIONE] OK (fallback clearanceTimestamp) - EURODIS API - entranceTimestamp assente, clearanceTimestamp valorizzato

### C081_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [IN ATTESA DECISIONE] Fallback su clearanceTimestamp DA DECIDERE (DF-01): test eseguibile solo dopo la decisione

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401) con entranceTimestamp vuoto e clearanceTimestamp valorizzato
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
OP: fallback su clearanceTimestamp DA DECIDERE (DF-01): test eseguibile solo dopo la decisione
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C081_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [IN ATTESA DECISIONE] Fallback su clearanceTimestamp DA DECIDERE (DF-01): test eseguibile solo dopo la decisione

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: data_spedizione/ora_spedizione valorizzate da clearanceTimestamp. OP: comportamento atteso DA DECIDERE (DF-01)
O5: eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C081_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [IN ATTESA DECISIONE] Fallback su clearanceTimestamp DA DECIDERE (DF-01): test eseguibile solo dopo la decisione

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C081_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [IN ATTESA DECISIONE] Fallback su clearanceTimestamp DA DECIDERE (DF-01): test eseguibile solo dopo la decisione

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C081_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [IN ATTESA DECISIONE] Fallback su clearanceTimestamp DA DECIDERE (DF-01): test eseguibile solo dopo la decisione

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C081_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)
- note_esecuzione: [IN ATTESA DECISIONE] Fallback su clearanceTimestamp DA DECIDERE (DF-01): test eseguibile solo dopo la decisione

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C081_TC007

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [IN ATTESA DECISIONE] Fallback su clearanceTimestamp DA DECIDERE (DF-01): test eseguibile solo dopo la decisione

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per tutte le spedizioni dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C081_TC008

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [IN ATTESA DECISIONE] Fallback su clearanceTimestamp DA DECIDERE (DF-01): test eseguibile solo dopo la decisione

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C082 - OK (europlateBarcode "0") - EURODIS API - Europlate con valore 0 non usato come id_ldv_itz

### C082_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401) con collis[].europlateBarcode = "0"
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C082_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: europlateBarcode "0" scartato: internazionale.id_ldv_itz vuoto (o valorizzato con il primo europlateBarcode non vuoto e diverso da "0" di un altro collo)
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C082_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C082_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C082_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C082_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C082_TC007

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per tutte le spedizioni dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C082_TC008

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C083 - OK (contrassegno con importo 0) - EURODIS API - cashOnDeliveryService.amount = 0

### C083_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401) con cashOnDeliveryService.amount = 0 e currency EUR
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C083_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: contrassegno.importo = 0. OP: DA VERIFICARE se il mapper emette warning o pubblica senza contrassegno
O5: eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C083_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C083_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C083_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)
O4: contrassegno con importo 0 non scartato da ce-dichiarato-ldv-pdb: OP: esito atteso DA DEFINIRE (Open Point 32)

### C083_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C083_TC007

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per tutte le spedizioni dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C083_TC008

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C084 - OK - EURODIS API - Multicollo 3 colli con pesi decimali (Nessun accessorio)

### C084_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401) con numberOfHandlingUnits=3 e 3 collis[] con weightOfUnit 1.5 / 2.25 / 0.4 kg
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C084_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: numero_colli=3; 3 collo[] con id_ldv = rispettivo deliveryPartnerBarcode e peso 1500 / 2250 / 400 g
O5: nessun warning (eurodis_mapper_avvisi_total e eurodis_mapper_campo_mancante_total invariate); eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C084_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C084_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C084_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C084_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C084_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C084_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C084_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-smistatore

Verifiche:
O1: pubblica sul topic "preadvising.completed.poste" (se prodotti Poste)
O2: pubblica sul topic "PSDA-20-04.SDA.EVENTTT.ANALDV" (Palmari) (1 msg per volta)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C084_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per tutte le spedizioni dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C084_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
consumer-sew-sped-poste

Verifiche:
O1: Scrittura sul DB ERMES,
 se CONDIZ_BS=FALSE sulle tabelle del vecchio Processo:
     - sew_spedizioni_poste
     - sew_spedizioni_poste_extender
     - associazioni_ldv_internazionale
     - prtn_articolo
     - prtn_collo
     - sew_spedizioni_poste_inter
     - prtn_spedizione
     - timedef_arch
     - sew_extender_scarto (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - dhl_scarti          (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - sew_inter_scarto    (solo per evitare che eventuali scarti del nuovo finiscano qui)
 oppure sulle corrispondenti tabelle del nuovo Processo (con suffisso "_2")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C084_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C085 - [IN ATTESA DECISIONE] OK (facoltativa) - EURODIS API - Invio tracking verso EURODIS

### C085_TC001

- fase: Tracking verso EURODIS (ce-eurodis-send-tracking)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [IN ATTESA DECISIONE] Sorgente degli eventi di tracking DA DEFINIRE (SF OP 35); catena facoltativa, da decidere se tenerla

#### Prerequisiti

Prerequisito:
I1: spedizione EURODIS già acquisita ed elaborata (es. catena C001)
I2: OP: sorgente degli eventi di tracking DA DEFINIRE
I3: OP: mock per consignorsColloBarcode DA DEFINIRE
Rif.: SF_136596_Eurodis_autoproduttore 0.3 (§2)

#### Azioni e verifiche

Descrizione:
ce-eurodis-send-tracking
Catena facoltativa: la fase di tracking verso EURODIS non è aggiunta alle singole catene.

Verifiche:
O1: OP: evento di tracking atteso, formato e destinazione DA DEFINIRE
O2: OP: uso di consignorsColloBarcode come riferimento verso EURODIS DA DEFINIRE (§2)
O3: OP: gestione errori e retry DA DEFINIRE
OP: DA DECIDERE se tenere la catena nel perimetro di questa specifica

## C086 - OK (osservazione) - EURODIS API - Dogana: customsService in EUR (Nessun accessorio)

### C086_TC086

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo, mittente extra-UE (es. CH), destinatario IT, customsService valorizzato (commercialValueOfGoods 500.00, dutyCode, sign, number, descriptionOfGoods), currency EUR - scenario: Dogana: customsService in EUR (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C086_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: customsService NON mappato in fase 1: descrizione_contenuto/valore/internazionale.* vuoti o 0, nessun effetto; spedizione trattata come nazionale (SF, assunzione 5)
O5: eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori; eventuali warning DA VERIFICARE
OP: dogana fuori dalla fase 1 (PA-13): atteso DA RICONFERMARE dopo la decisione sul mapping; fino ad allora il test è di osservazione. ADR non gestiti (conferma Chiapponi 2026-11-12)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C086_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C086_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C086_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C086_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C086_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C086_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C086_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-smistatore

Verifiche:
O1: pubblica sul topic "preadvising.completed.poste" (se prodotti Poste)
O2: pubblica sul topic "PSDA-20-04.SDA.EVENTTT.ANALDV" (Palmari) (1 msg per volta)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C086_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C086_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
consumer-sew-sped-poste

Verifiche:
O1: Scrittura sul DB ERMES,
 se CONDIZ_BS=FALSE sulle tabelle del vecchio Processo:
     - sew_spedizioni_poste
     - sew_spedizioni_poste_extender
     - associazioni_ldv_internazionale
     - prtn_articolo
     - prtn_collo
     - sew_spedizioni_poste_inter
     - prtn_spedizione
     - timedef_arch
     - sew_extender_scarto (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - dhl_scarti          (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - sew_inter_scarto    (solo per evitare che eventuali scarti del nuovo finiscano qui)
 oppure sulle corrispondenti tabelle del nuovo Processo (con suffisso "_2")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C086_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C087 - OK (osservazione) - EURODIS API - Dogana: customsService in valuta diversa da EUR (Nessun accessorio)

### C087_TC087

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia (es. edReference 7319003746401), 1 collo, mittente extra-UE (es. CH), destinatario IT, customsService valorizzato (commercialValueOfGoods 500.00, dutyCode, sign, number, descriptionOfGoods), currency CHF - scenario: Dogana: customsService in valuta diversa da EUR (Nessun accessorio)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C087_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: customsService NON mappato in fase 1: valuta e valore non riportati; nessun warning atteso per la valuta della dogana (il warning valuta_non_eur riguarda solo il contrassegno)
O5: eurodis_mapper_spedizioni_total{esito=pubblicata} +1; span eurodis.mapper.elabora senza errori; eventuali warning DA VERIFICARE
OP: dogana fuori dalla fase 1 (PA-13): atteso DA RICONFERMARE dopo la decisione sul mapping; fino ad allora il test è di osservazione. ADR non gestiti (conferma Chiapponi 2026-11-12)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C087_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
in validazione applica una quota parte delle regole non-PDB (semantiche + logiche) già in essere per i canali IS/IE/IF/SM. OP In attesa doc. specifiche con dettaglio Regole di Validazione

Verifiche:
O1: in assenza di errori di validazione, pubblica sul topic "preadvising.enrichment" (con "source": "/ce-dichiarato-validatore") - il msg è valido? Tutti i campi sono in linea con il pre-enrichment? Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.xxx"
O2: pubblica sul topic "preadvising.evensource" -Come? Utilizziamo Magic Kafka (OP: strumento DA DEFINIRE) con apposito filtro JAVASCRIPT/Topic "preadvising.evensource"
 - stati movimentati:
recordList:
- PREAD_EMESSO (eventType="ST_R0002";  aggregateType: "ldv") * sempre *
- PREAD_DUPLICATO (eventType="ST_R0003";  aggregateType: "ldv") * SOLO  se l'errore riscontrato dal Validatore è di Ldv Duplicata * – per EURODIS: seconda ricezione della stessa LDV (099 "Ldv presente")
- PREADVISING_PARZIALE_E_BLOCCATO (eventType="ST_R0006";  aggregateType: "ldv") * SOLO se l'errore riscontrato dal Validatore è diverso da Ldv Duplicata *
O3: Mongo (dichiarato_events, preadvising_history): stato 0 alla ricezione, 3 se validato, 2 se KO o duplicato
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C087_TC004

- fase: Verifiche formali, Arricchimento
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-orchestratore

Verifiche:
Per il Preadvise oggetto del test, esegue un MERGE di tutti i MSG del "preadvising.enrichment"

se trova:
1 MSG (l'ha pubblicato il Validatore - NUOVO EVENTO):
O1: pubblica sul topic "preadvising.enrichment.pdb" 
O2: pubblica sul topic "preadvising.enrichment.normalizzatore" (con "Message"."tipo_lavorazione": "validato")

4 MSG (hanno risposto tutti NORMALIZZATORE, PDB, ADAPTER) -->
 - c'è stato un errore lato PDB?
      - SI: registra l'errore
               - PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006) * se sono stati riscontrati errori da BEP *
     -NO:
             O3: pubblica sul topic "preadvising.completed"  -          Verificare che sia in linea con l'atteso (dati normalizzati + dati specifici del test in corso)

O4: pubblica sul topic "preadvising.evensource" - stati movimentati:
O5: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C087_TC005

- fase: Verifiche Sistemi Esterni (BEP- REQ)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.enrichment.pdb"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-ldv-pdb

Verifiche:
O1: chiamata sincrona WS al sistema SAP-BEP dovrà essere fatta (se possibile, verificare sui logs che non siano presenti)
O2: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "????") l'esito OK/KO BEP
O2: Insert/Update su DB Mongo – OP: uso di Mongo nel flusso API DA DEFINIRE
O3: verificare che collo.id_ldv (= collis[].deliveryPartnerBarcode) sia passato a BEP (previsto solo per il canale INVIOSYSTEM)
OP: verificare che BepChannel.fromCanale riconosca EUD_INVIOSYSTEM
OP: osservazioni aperte su ce-dichiarato-ldv-pdb: ISO4 non risolto, nessun default per peso e dimensioni, canale POU o WEBSERVICE, contrassegno con importo 0 non scartato (SF, Open Point 32)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C087_TC006

- fase: waybillCreate Sistemi Esterni (BEP)
- sistema: BEP (Sistema Esterno)
- fornitore: BEP (Sistema Esterno)

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena

#### Azioni e verifiche

Descrizione:
SISTEMA_ESTERNO fa le sue verifiche e risponre in modo sincrono al WS  (REST/JSON waybillCreate)

Verifiche:
O1:- segnalare a BEP eventuali differenze sul msg rispetto allo scenario atteso
O2: verificare che la LDV ricevuta da BEP coincida con collis[].deliveryPartnerBarcode della spedizione EURODIS
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C087_TC007

- fase: Arricchimento da BEP
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "PACCHI.BEP.ALL.ANAG_LDV" * VIENE PUBBLICATO SOLO IN CASO DI RISPOSTA OK DA PARTE DI BEP *

#### Azioni e verifiche

Descrizione:
ce-dichiarato-adapter

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" arricchendo il msg con alcune info prese dal msg di input
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C087_TC008

- fase: Normalizzazione indirizzi + CAP Fittizi
- sistema: SDA-NEW
- fornitore: Reply

#### Prerequisiti

Prerequisito:
Esecuzione test TC004
I1: Consuma il topic "preadvising.enrichment.normalizzatore"

#### Azioni e verifiche

Descrizione:
ms-dichiarato-normalizzatore

Verifiche:
O1: pubblica sul topic "preadvising.enrichment" (con "Message"."tipo_lavorazione": "NORMALIZZAZIONE")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C087_TC009

- fase: Smistatore
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test TC004, TC005, TC006, TC007, TC008
I1: Consuma il topic "preadvising.completed"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-smistatore

Verifiche:
O1: pubblica sul topic "preadvising.completed.poste" (se prodotti Poste)
O2: pubblica sul topic "PSDA-20-04.SDA.EVENTTT.ANALDV" (Palmari) (1 msg per volta)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C087_TC010

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C087_TC011

- fase: Elaborazione Dichiarato (scrittura su ERMES)
- sistema: ACN-OLD
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.completed.poste"

#### Azioni e verifiche

Descrizione:
consumer-sew-sped-poste

Verifiche:
O1: Scrittura sul DB ERMES,
 se CONDIZ_BS=FALSE sulle tabelle del vecchio Processo:
     - sew_spedizioni_poste
     - sew_spedizioni_poste_extender
     - associazioni_ldv_internazionale
     - prtn_articolo
     - prtn_collo
     - sew_spedizioni_poste_inter
     - prtn_spedizione
     - timedef_arch
     - sew_extender_scarto (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - dhl_scarti          (solo per evitare che eventuali scarti del nuovo finiscano qui)
     - sew_inter_scarto    (solo per evitare che eventuali scarti del nuovo finiscano qui)
 oppure sulle corrispondenti tabelle del nuovo Processo (con suffisso "_2")
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

### C087_TC012

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-monitoring-pdb

Verifiche:
O1: pubblica sul topic "PRE-ADV.MONITORAGGIO-CAMBIO-STATO" (Da capire se sarà questo il topic con oppurtuno CANALE oppure se verrà fatto un Topic dedicato) 
Da capire anche se gli eventi verranno visulaizzati sulla console Monitoraggio (fase 1 adeguata) oppure da una nuova Console
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C092 - KO VALID (1023/1024/1039/1051/1052/1063: mittente assente) - EURODIS API - shipperAddress null (come nei dati TEST)

### C092_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con shipperAddress = null (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C092_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: shipperAddress assente: mittente.* tutti vuoti, nessuna chiamata a ce-anagrafica; il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C092_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1023 "Mittente CAP: Campo obbligatorio mancante"; 1024 "Mittente Localita: Campo obbligatorio mancante"; 1039 "Mittente Codice Nazione: Campo obbligatorio mancante"; 1051 "Mittente Indirizzo: Campo obbligatorio mancante"; 1052 "Mittente Ragione Sociale: Campo obbligatorio mancante"; 1063 "Mittente Nazione: Campo obbligatorio mancante"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
O4: 1193 "Dati Mittente mancanti" solo se il mapper non emette l'oggetto mittente: DA VERIFICARE
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C092_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C092_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C093 - KO VALID (1052: ragione sociale mittente vuota) - EURODIS API - Ragione sociale mittente vuota

### C093_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con shipperAddress.companyName vuoto (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C093_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: mittente.ragione_sociale vuota; il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C093_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1052 "Mittente Ragione Sociale: Campo obbligatorio mancante"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C093_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C093_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C094 - KO VALID (1023: CAP mittente vuoto) - EURODIS API - CAP mittente vuoto

### C094_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con shipperAddress.zipcode vuoto (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C094_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: mittente.cap vuoto; il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C094_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1023 "Mittente CAP: Campo obbligatorio mancante"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C094_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C094_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C095 - KO VALID (1024: località mittente vuota) - EURODIS API - Località mittente vuota

### C095_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con shipperAddress.city vuoto (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C095_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: mittente.localita vuota; il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C095_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1024 "Mittente Localita: Campo obbligatorio mancante"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C095_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C095_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C096 - KO VALID (1051: indirizzo mittente vuoto) - EURODIS API - Indirizzo mittente vuoto

### C096_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con shipperAddress.street vuoto (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C096_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: mittente.indirizzo vuoto; il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C096_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1051 "Mittente Indirizzo: Campo obbligatorio mancante"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C096_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C096_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C097 - KO VALID (1039/1063: codice paese mittente vuoto) - EURODIS API - Codice paese mittente vuoto

### C097_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con shipperAddress.countryCode vuoto (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C097_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: mittente.nazione e codici nazione vuoti, nessuna chiamata a ce-anagrafica; il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C097_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1039 "Mittente Codice Nazione: Campo obbligatorio mancante"; 1063 "Mittente Nazione: Campo obbligatorio mancante"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C097_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C097_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C098 - KO VALID (1019: ragione sociale destinatario vuota) - EURODIS API - Ragione sociale destinatario vuota

### C098_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con consigneeAddress.companyName vuoto (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C098_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: destinatario.ragione_sociale vuota; il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C098_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1019 "Destinatario Ragione Sociale: Campo obbligatorio mancante"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C098_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C098_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C099 - KO VALID (1042: indirizzo destinatario vuoto) - EURODIS API - Indirizzo destinatario vuoto

### C099_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con consigneeAddress.street vuoto (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C099_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: destinatario.indirizzo vuoto; il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C099_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1042 "Destinatario Indirizzo: Campo obbligatorio mancante"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C099_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C099_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C100 - KO VALID (1064: codice paese destinatario vuoto) - EURODIS API - Codice paese destinatario vuoto

### C100_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con consigneeAddress.countryCode vuoto (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C100_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: destinatario.nazione vuota; il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C100_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1064 "Destinatario Nazione: Campo obbligatorio mancante"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C100_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C100_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C101 - [DA CONFERMARE] KO VALID (1289: ragione sociale destinatario oltre 40 caratteri) - EURODIS API - Ragione sociale destinatario oltre 40 caratteri

### C101_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con consigneeAddress.companyName di 45 caratteri (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C101_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: destinatario.ragione_sociale passa intera (nessun troncamento); il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C101_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1289 "Il campo 'ragione_sociale' del destinatario non può superare i 40 caratteri"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C101_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C101_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C102 - [DA CONFERMARE] KO VALID (1292: civico destinatario oltre 4 caratteri) - EURODIS API - Numero civico destinatario oltre 4 caratteri

### C102_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con consigneeAddress.streetNumber di 8 caratteri (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C102_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: destinatario.numero_civico passa intero (nessun troncamento); il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C102_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1292 "Il campo 'numero_civico' del destinatario non può superare i 4 caratteri"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C102_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C102_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C103 - [DA CONFERMARE] KO VALID (1294: località destinatario oltre 30 caratteri) - EURODIS API - Località destinatario oltre 30 caratteri

### C103_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con consigneeAddress.city di 40 caratteri (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C103_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: destinatario.localita passa intera (nessun troncamento); il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C103_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1294 "Il campo 'localita' del destinatario non può superare i 30 caratteri"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C103_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C103_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN
- note_esecuzione: [DA CONFERMARE] Atteso secondo le regole PDB_INVIOSYSTEM attuali (rifiuto); la SF prevede l'adeguamento ai limiti BEP: confermare con il responsabile del validatore

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C104 - KO VALID (1083: peso collo oltre il massimo) - EURODIS API - Peso collo oltre 9.999.900 grammi

### C104_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con collis[0].weightOfUnit = 10000 (kg) (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C104_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: collo[].peso = 10000000 (grammi); il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C104_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1083 "Collo Peso fuori range (ammessi valori tra 0 e 9.999.900 grammi)"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C104_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C104_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C105 - KO VALID (1084: dimensione collo oltre 999,99) - EURODIS API - Dimensione collo oltre 999,99

### C105_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con collis[0].length = 1000 (cm), height e width valorizzate (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C105_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: collo[].lunghezza = 1000; il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C105_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1084 "Dimensioni superiori a 999.99 in Collo"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C105_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C105_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C106 - KO VALID (1173: collis assente) - EURODIS API - Nessun collo nella spedizione

### C106_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 1 spedizione fittizia con collis = null (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C106_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: collo[] vuoto (collis null); il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C106_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1173 "Dati Collo mancanti"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C106_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C106_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C107 - KO VALID (1162: stessa edReference con LDV diversa) - EURODIS API - Stessa edReference con LDV diversa

### C107_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 2 spedizioni: la prima valida e già elaborata; la seconda con la stessa edReference ma deliveryPartnerBarcode diverso (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C107_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: secondo messaggio con lo stesso rif_spedizione e id_preadvising nuovo; il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C107_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREADVISING_PARZIALE_E_BLOCCATO (ST_R0006, aggregateType=ldv) con errore/i: 1162 "Numero Riferimento Spedizione già utilizzato"
O3: Mongo: dichiarato_events con stato 2 ed errori valorizzati; preadvising_history stato 2
O4: il controllo è su rif_spedizione (checkAndStoreNumeroOrdine) e non conta se il precedente è stato scartato (stato 2)
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C107_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C107_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)

## C108 - KO VALID (099: stessa LDV con edReference diversa) - EURODIS API - Stessa LDV su spedizioni diverse

### C108_TC001

- fase: Scarico API EURODIS (ce-dichiarato-eurodis-in)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: ce-dichiarato-eurodis-in attivo sull'ambiente (svil/coll) con EURODIS_IN_ABILITATO=true; scheduler interno svil/coll ogni 2 minuti (0 */2 * * * *), job di elaborazione 30 s dopo. OP: deploy Jenkins di -in da fare; ambienti di test dell'intera catena DA DEFINIRE
I2: sorgente dati: mock-eurodis (chiave test-key-sda, anomalie iniettabili) oppure https://testapi.eurodis.com/receive-pan con header X-API-Key (secret OpenShift). OP: ambiente TEST EURODIS non rappresentativo (indirizzi a null, deliveryPartnerBarcode assente)
I3: 2 spedizioni con edReference diverse ma lo stesso deliveryPartnerBarcode; la prima valida e già elaborata (anomalia da generare: mock-eurodis da estendere oppure dati di EURODIS)
- Prodotto: APT000901 (mock-eurodis, config/prodotti.yaml)
- Cliente/contratto: OP: DA DEFINIRE (mapper.cliente.codice / mapper.cliente.codice-contratto, valori da ricevere da Poste)
- LDV in collis[].deliveryPartnerBarcode: OP: range LDV DA DEFINIRE (sintassi LDV chiesta a Marzilli, eventuale condivisione con BEP); OP: mock-eurodis oggi scrive la LDV in consignorsColloBarcode, va allineato
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in
Job di scarico (scheduler interno + ShedLock su PostgreSQL, un solo pod alla volta): GET /shipments/v1 senza body né parametri, salvataggio del grezzo.
Job di elaborazione: divide il grezzo e pubblica una spedizione per messaggio.

Verifiche:
O1: PostgreSQL ce_eud_api_in, tabella eurodis_scarichi: nuova riga con esito HTTP 200, corpo identico al grezzo ricevuto, id_file (UUID), nome_file eurodis.<yyyyMMddHHmmssSSS>.json (OP: formato DA DECIDERE), conteggi coerenti (1 spedizioni)
O2: eurodis_spedizioni: 1 righe con chiave edReference, colonna json valorizzata, stato_invio=INVIATA, numero_ricezioni=1
O3: preadvising.evensource: ST_F0002 FILE_PRESO_IN_CARICO, poi ST_F0005 FILE_IN_ELABORAZIONE (aggregateType=file, canale=EUD_INVIOSYSTEM, numeroRecord=1, linkFileFisicoInviato=eurodis_scarichi/<id>), emessi prima delle spedizioni
O4: preadvising.eud.pre.build: 1 messaggi (una spedizione per messaggio) con chiave edReference e corpo identico al testo ricevuto; header edReference, idEsecuzione, ricevutoIl, fonte, rifGrezzo, idFile (= id_file di O1), ambiente, schemaVersion, traceparent
O5: span eurodis.receive_pan.get ed eurodis.elaborazione senza errori; metrica eurodis_in_evento_total incrementata (/actuator/prometheus, porta 8091)
OP: fuso orario dei timestamp DA VERIFICARE sui dati del flusso FTP
OP: strumento di lettura Kafka (Magic Kafka) DA DEFINIRE

### C108_TC002

- fase: Mapping ICD v11 (ce-dichiarato-eurodis-mapper)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.eud.pre.build" (una spedizione per messaggio, chiave edReference, header idFile)
Rif.: ce-dichiarato-eurodis-mapper.md 0.4 (sez. 6); ICD v11 foglio "Mapping EURODIS"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-mapper

Verifiche:
O1: pubblica 1 messaggio per spedizione sul topic "preadvising.pre-enrichment" con chiave rif_spedizione = edReference (stringa senza decimali)
O2: tracciato ICD v11 conforme alla sez. 6 del mapper:
- canale=EUD_INVIOSYSTEM, flag_autoproduttore="S"
- id_file = header idFile; id_preadvising = nuovo UUID
- collo[].id_ldv = collis[].deliveryPartnerBarcode (consignorsColloBarcode NON mappato)
- internazionale.id_ldv_itz = primo collis[].europlateBarcode non vuoto e diverso da "0"
- collo[].peso = weightOfUnit × 1000 (grammi); numero_colli = numberOfHandlingUnits
- id_ldv_partner_master = dispatchPartnersDomesticShipmentNumber
- mittente/destinatario da shipperAddress/consigneeAddress; codici nazione ISO3/ISO4 da ce-anagrafica
- contrassegno.* da cashOnDeliveryService; codici_servizi da deliveryService + cashOnDeliveryService (tabella 6.8 del mapper)
- data_spedizione/ora_spedizione = entranceTimestamp. OP: campo in verifica con EURODIS; fallback clearanceTimestamp DA DECIDERE (DF-01)
O3: nessun troncamento: i valori passano interi anche oltre la dimensione ICD
O4: verifica scenario: secondo messaggio con LDV già presente su un altro id_preadvising; il mapper pubblica comunque (la verifica è a valle)
OP: id_canale vuoto DA DEFINIRE (PA-15)
OP: ldv_partner_collo assente nell'ICD v11, DA DECIDERE (DF-31)

### C108_TC003

- fase: Validazione
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test precedente in catena
I1: Consuma il topic "preadvising.pre-enrichment"

#### Azioni e verifiche

Descrizione:
ce-dichiarato-validatore
Canale EUD_INVIOSYSTEM: regole PDB (pdbKSession, file ce-pdb-rules.drl), come per PDB_INVIOSYSTEM.

Verifiche:
O1: NESSUN messaggio su "preadvising.enrichment" per la spedizione (rif_spedizione = edReference dello scenario)
O2: preadvising.evensource: PREAD_EMESSO (ST_R0002, aggregateType=ldv), poi PREAD_DUPLICATO (ST_R0003, aggregateType=ldv), errore 099 "Ldv presente"
O3: Mongo: stato 2 (duplicato), nessun nuovo record in preadvising_history
O4: duplicato per LDV (gestisciDuplicatoBase): eventi ST_R0002 e ST_R0003 PREAD_DUPLICATO al posto di ST_R0006
OP: regole PDB_INVIOSYSTEM da estendere a EUD_INVIOSYSTEM (oggi nel file ce-pdb-rules.drl compare solo EUD_INVIOFILE); branch del validatore in verifica del Test Manager
Canale atteso: EUD_INVIOSYSTEM

### C108_TC004

- fase: Chiusura scarico (eurodis_scarichi)
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
Esecuzione test "Scarico API EURODIS (ce-dichiarato-eurodis-in)" della catena
I1: Lettura PostgreSQL ce_eud_api_in (eurodis_scarichi, eurodis_spedizioni)
Rif.: ce-dichiarato-eurodis-in.md 0.6.1; ddl-ce-eurodis-api-in.md; eurodis-receive-pan-swagger-v1.json; SF_136596_Eurodis_autoproduttore 0.3

#### Azioni e verifiche

Descrizione:
ce-dichiarato-eurodis-in (stato finale dello scarico)

Verifiche:
O1: eurodis_scarichi: stato finale INVIATO_TUTTO
O2: eurodis_spedizioni: stato_invio=INVIATA per la spedizione dello scarico
O3: preadvising.evensource: per l'idFile presenti solo ST_F0002 FILE_PRESO_IN_CARICO e ST_F0005 FILE_IN_ELABORAZIONE; ST_F0006 FILE_ELABORATO_CON_SUCCESSO e ST_F0008 FILE_COMPLETAMENTE_SCARTATO NON emessi
OP: FILE_ELABORATO_CON_SCARTO non previsto, DA DEFINIRE
OP: esito verso EURODIS: nessuno scarto o rifiuto previsto (PA-08); uso del sistema di errori EURODIS (A03.2) da discutere in call

### C108_TC005

- fase: Monitoring
- sistema: SDA-NEW
- fornitore: ACN

#### Prerequisiti

Prerequisito:
I1: Consuma il topic "preadvising.evensource"

#### Azioni e verifiche

Descrizione:
ce-event-handler-file-pdb

Verifiche:
O1: produce un file con gli esiti dell'elaborazione. Nomenclatura???? Formato???? In caso di OK, il file deve contenere le ultime 3 colonne
OP: console di monitoring DA DEFINIRE (stessa console o nuova)
Canale atteso: EUD_INVIOSYSTEM
OP: DA DEFINIRE se la fase resta invariata e se ci sono differenze per canale (EUD_INVIOSYSTEM)
