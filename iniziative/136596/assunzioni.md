# 136596 — Assunzioni su EURODIS receive-pan

Assunzioni sulle 13 domande girate a Gianluca Chiapponi (mail del 26-10).
Il 09-11 sono arrivate le risposte di EURODIS (via Chiapponi) e il documento
**A03.2 «API – Data interchange & standard interfaces»** (versione 0.01 del
12-03-2026, in `documenti/A032 API Data interchange.pdf`). Ogni sezione riporta
la risposta e dice se l'assunzione è confermata, cambiata o ancora aperta.

Per ognuna: cosa assumiamo, cosa succede se è falsa, cosa resta da chiedere.

Legenda stato: `proposta` · `concordata` · `confermata da EURODIS` ·
`superata` · `riaperta` · `da verificare`

## Riepilogo dopo le risposte di EURODIS (09-11)

| ID | Tema | Stato | Esito |
|---|---|---|---|
| AS-D01 | Consegna delle spedizioni | confermata, con recupero da concordare | EURODIS rimanda tutto su richiesta; il come è da concordare |
| AS-D02 | Prima chiamata | confermata da EURODIS | si riceve solo ciò che non è già stato ricevuto |
| AS-D03 | Modifiche e annullamenti | confermata da EURODIS | non si considerano (solo prima dell'attivazione) |
| AS-D04 | Limiti di chiamata | confermata, frequenza nostra | nessun limite; si resta a 2 minuti |
| AS-D05 | Rilettura puntuale | confermata da EURODIS | 60 giorni (assunti 30) |
| AS-D06 | Fuso orario e accesso | chiave chiusa, fuso da verificare | chiavi senza rotazione; il fuso non è UTC per forza |
| AS-D07 | Errori e scarti | **riaperta** | EURODIS: non rifiutare; da discutere in call |
| AS-D08 | Tracking | confermata da EURODIS | `send-tracking` e `send-pod` già disponibili |
| AS-D09 | Produzione | confermata da EURODIS | si cambia endpoint e chiave |
| AS-D10 | Payload di produzione | non risolta | nessun esempio; rimandano alla documentazione |
| AS-D11 | Volumi e frequenza | da verificare | i volumi li ricaviamo noi dal flusso FTP |
| AS-D12 | Dogana e ADR | risposta di EURODIS | nel perimetro dell'interfaccia |
| AS-D13 | Rollout incrementale | risposta di EURODIS | ibrido, passo per passo; call da fare |

**Temi per la call proposta da Chiapponi**: come si chiede il rimando dei dati
(AS-D01), errori e rifiuti (AS-D07), rollout ibrido (AS-D13), `consigneeAddress`
e LDV in produzione (AS-D10).

---

## AS-D01 — Consegna delle spedizioni (domanda 1; PA-05, PA-09)

**Stato**: confermata da EURODIS, con recupero da concordare

**Risposta EURODIS**: si ricevono solo le spedizioni non ancora ricevute, e
questo non cambia. Se ci sono problemi nel travaso su database, si può chiedere
che EURODIS rimetta **tutti i dati** nella richiesta successiva. Consigliano di
scrivere i dati ricevuti, in parallelo, anche su uno script o log locale e poi
travasarli nel database (Post AT fa così).

**Fatti** (swagger `eurodis-receive-pan-swagger-v1.json`, A03.2 §5.2.3)
- `GET /shipments/v1`: «Deploys all new shipments, that have not already been
  deployed to the partner». Nessun parametro, quindi nessun filtro per data.
- Nessun endpoint di conferma (ack).
- A03.2 §5.2.3: restituisce tutto ciò che è attivato e non ancora ritirato al
  momento della richiesta.

**Assunzione**
1. EURODIS considera consegnata una spedizione nel momento in cui la restituisce
   e non la rimanda più, **salvo richiesta nostra di rimando totale**.
2. La durabilità passa a noi: appena arriva la risposta HTTP, `-in` scrive il
   JSON grezzo su Mongo (`eurodis_scarichi`) prima di qualsiasi altra
   operazione. Ogni errore successivo si recupera rielaborando il grezzo
   salvato, senza richiamare EURODIS.
3. In caso di perdita (per esempio crash tra la risposta HTTP e la scrittura su
   Mongo) il recupero è la **richiesta a EURODIS di rimandare tutto**. Come si
   chiede (mail, ticket, parametro, endpoint) **è da concordare**. Finché non è
   concordato, il rischio di perdere un lotto resta, e ne sappiamo solo la
   mitigazione.
4. Il consiglio di EURODIS di tenere una copia in un log locale parallela al
   database non è ancora nel design di `-in`: vedi appunti per lo sviluppo.

**Se è falsa**
- Se il rimando non è disponibile o ha tempi lunghi, il lotto perso non si
  recupera.
- Se EURODIS rimanda anche spedizioni già ricevute (rimando totale), arrivano
  **doppioni**: il design li regge, perché non c'è filtro sui duplicati e si
  filtra a valle. Da quel momento «a valle» deve davvero filtrare.

**Da concordare con EURODIS**: come si richiede il rimando totale, se è
immediato, se rimanda solo il non ricevuto o anche lo già ricevuto.

---

## AS-D02 — Prima chiamata (domanda 2; PA-06)

**Stato**: confermata da EURODIS

**Risposta EURODIS**: si ricevono solo le spedizioni non ancora ricevute.

**Fatti**
- Nessun parametro di data nello swagger.
- A03.2 §5.2.2: una spedizione resta in un pre-database finché non è attivata da
  uno scan, e non è visibile al partner ricevente; resta fino a 60 giorni se non
  c'è scan (quelle con linehaul `DL` o `DI` si attivano subito).
- `-in` ha un solo interruttore, `eurodis.in.abilitato` (RF-01, default `false`).

**Assunzione**
1. La prima chiamata restituisce tutte le spedizioni già attivate e non ancora
   ritirate. Non c'è un limite di data e il volume della prima risposta non è
   noto.
2. Lo storico arretrato si **elabora tutto**: nessun filtro per data né scarto
   (decisione Paolo, 09-11).
3. La prima abilitazione dello scarico è un'operazione controllata.

**Se è falsa**
- Se alla prima chiamata arriva molto più del previsto: tempi di risposta,
  timeout e documento grezzo enorme su Mongo (limite 16 MB per documento BSON), e
  una raffica di messaggi verso il mapper e il preadvising.

---

## AS-D03 — Aggiornamenti e annullamenti (domanda 3; PA-27)

**Stato**: confermata da EURODIS

**Risposta EURODIS**: modifica e annullamento sono possibili solo se i dati non
sono attivati e non sono condivisi con il partner di consegna. **Non è un tema
da considerare.**

**Fatti**
- A03.2 §5.2.2 lo conferma: fino all'attivazione il partner mittente aggiorna i
  campi con una `PUT`, la spedizione non è visibile ai partner di transito e di
  consegna.
- Resi e rettifiche (R, D, A, L, M) sono spedizioni nuove con un proprio
  `edReference`, legate all'originale da `referencedEurodisShipmentNumber`
  (PA-17).

**Assunzione**
1. Una spedizione ricevuta da `receive-pan` non viene più modificata né annullata
   da EURODIS: non serve gestire aggiornamenti o annullamenti.
2. Un secondo messaggio con lo stesso `edReference` non è atteso, salvo il caso
   del rimando totale di AS-D01 (doppioni).

**Se è falsa**
- Se compaiono modifiche o annullamenti dopo l'attivazione, `-in` li tratta come
  spedizioni nuove: a valle possono risultare doppioni con dati diversi.

---

## AS-D04 — Limiti di chiamata (domanda 4; PA-27)

**Stato**: confermata da EURODIS; la frequenza è una nostra decisione

**Risposta EURODIS**: nessun limite, per ora; se servirà in futuro si cercherà
una soluzione. Consigliano una chiamata ogni **15-20 minuti**. Il numero di
spedizioni sarà assolutamente gestibile.

**Fatti**
- Nessuna paginazione né limite documentato nello swagger.
- Decisione di progetto del 04-11, **confermata da Paolo il 09-11**: scarico ogni
  2 minuti. È più frequente di quanto consiglia EURODIS.
- Il vincolo di 30 minuti tra due richieste in A03.2 riguarda **Receive POD**
  (§5.4.2), non `receive-pan`.

**Assunzione**
1. Ogni chiamata restituisce tutto ciò che è in coda, in un'unica risposta, senza
   paginazione né rate limit.
2. Si scarica ogni 2 minuti, nonostante il consiglio di 15-20 minuti. Se EURODIS
   introduce un limite, si rallenta.
3. Se la risposta è troppo grande o la chiamata va in timeout, lo scarico fallisce
   e si ritenta al ciclo successivo.
4. Se un timeout o un errore di rete fa perdere un lotto, vale AS-D01 (punto 3):
   recupero con la richiesta di rimando totale a EURODIS.

**Se è falsa**
- Se EURODIS introduce un limite o contesta la frequenza, errori (probabilmente
  429) e ritmo da rallentare.

**Da dire a EURODIS**: scaricheremo ogni 2 minuti, più spesso di quanto
consigliato. Va bene?

---

## AS-D05 — Rilettura puntuale (domanda 5; PA-27)

**Stato**: confermata da EURODIS

**Risposta EURODIS**: **60 giorni**.

**Fatti**
- `GET /shipment/{edReference}/v1` rilegge una singola spedizione.
- `-in` la usa già per il recupero puntuale (RF-16, run `RILETTURA`, AC-14,
  implementata): gli `edReference` si elencano in
  `eurodis.in.recupero.ed-references`.

**Assunzione**
1. Una spedizione già consegnata resta rileggibile per `edReference` per **60
   giorni**.
2. La rilettura è uno strumento di recupero **manuale**, per `edReference` noti.
   Non è un canale ordinario e non sostituisce il salvataggio del grezzo.
3. Non permette di ritrovare un lotto di cui non si conoscono gli id: per quello
   vale AS-D01 (punto 3).

**Se è falsa**
- Se dopo i 60 giorni serve una spedizione, si usa solo il grezzo salvato:
  la sua conservazione su Mongo va decisa di conseguenza.

---

## AS-D06 — Fuso orario e accesso (domanda 6; PA-27)

**Stato**: chiave chiusa; **fuso da verificare**

**Risposta EURODIS**: le chiavi API **non ruotano**. Il fuso è lo standard che SDA
usa oggi per lo scambio file su FTP.

**Fatti**
- Lo swagger non dichiara il fuso dei timestamp. Gli esempi non hanno offset
  (`2024-03-29T06:53:55`).
- A03.2 indica `GMT+1` per le finestre orarie dei PUDO: è un dato su un altro
  servizio, non una prova per i timestamp di `receive-pan`.
- Paolo, 09-11: il fuso dello scambio FTP si ricava controllando i dati che
  EURODIS invia oggi su quel flusso; **da verificare**.

**Assunzione**
1. **Il fuso dei timestamp non è noto**: è quello dello scambio FTP attuale, da
   ricavare dai dati esistenti. L'assunzione precedente (UTC) è **superata**.
2. Fino alla verifica i timestamp si passano come arrivano, senza conversione.
3. La chiave API sta in un **secret OpenShift**, per ambiente (Paolo, 09-11). Non
   ruota: nessun processo di rotazione da prevedere.

**Se è falsa**
- Se si assume il fuso sbagliato, ogni orario risulta sfasato di 1 o 2 ore (ora
  legale) rispetto alla realtà: eventi, orari di invio e confronti con i dati SDA.

**Da fare**: verificare il fuso sui dati EURODIS del flusso FTP esistente e
fissarlo qui.

---

## AS-D07 — Errori e scarti (domanda 7; PA-08, PA-32)

**Stato**: **riaperta** (era concordata il 09-11, prima della risposta di EURODIS)

**Risposta EURODIS**: da discutere a fondo. Dal loro punto di vista **SDA non
dovrebbe rifiutare le spedizioni** ricevute: EURODIS ha già un sistema di errori e
rifiuti in funzione (A03.2), a cui SDA ha accesso e che dovrebbe **riprendere**.
Rifiutare con una logica propria non sarebbe fruttuoso.

**Fatti** (A03.2 §6)
- La tabella «Error codes PAN» descrive le risposte del sistema a informazioni
  mancanti nell'invio dei dati di spedizione (`send-pan`) da parte del partner
  mittente. EURODIS **non valida il contenuto** dei campi: controlla solo che
  siano valorizzati e del tipo giusto (numerico, alfabetico, alfanumerico).
- Alcuni errori sono avvisi (`warning`), altri rifiuti (`reject`). Esempi di
  rifiuto: dati di contrassegno (IBAN, importo, valuta) mancanti, dati ADR
  mancanti, ritiro senza data, reso senza riferimento all'originale.
- Un destinatario con città o paese ignoti, o senza via, è un errore del
  sistema EURODIS in ingresso: quindi in teoria non dovrebbe arrivare a `receive-pan`.
  Questa è una **nostra lettura**, non scritta nel documento.
- Decisione di Paolo del 09-11 (da riconsiderare): gli scarti si comunicano con
  una mail, come in `EUD_INVIOFILE`, appoggiandosi al ms esistente di un altro
  gruppo, insieme agli errori di `INVIOFILE`.
- `receive-pan` non ha un canale per rifiutare una spedizione.

**Assunzione provvisoria**
1. SDA **non comunica rifiuti a EURODIS** tramite `receive-pan`, che non li
   prevede, e non usa l'evento di eccezione di `send-tracking` come canale di
   rifiuto.
2. **Cosa significa «riprendere» il sistema di errori EURODIS** (fare in SDA gli
   stessi controlli di A03.2 §6? usare i loro codici? accettare tutto senza
   rifiutare?) **non è chiaro**: è il tema principale della call.
3. Gli scarti **interni** (messaggio non mappabile, dato che SDA non può usare)
   restano registrati da noi (grezzo, esito, metrica). La mail concordata il 09-11
   e il ms dell'altro gruppo restano **candidati**, da riconsiderare dopo la call.

**Se è falsa**
- Se EURODIS si aspetta comunque un rifiuto esplicito, per loro la spedizione
  risulta presa in carico da SDA anche se da noi è scartata.
- Se SDA rifiuta con una logica propria, EURODIS la considera non utile:
  rischio di rifiuti incoerenti con i loro.

**Da chiarire in call**
- Cosa significa riprendere il loro sistema errori/rifiuti (A03.2, §6).
- Se un destinatario senza indirizzo (DF-30) può arrivare in produzione o è già
  respinto da EURODIS.
- Se la mail di scarto di `INVIOFILE` e il ms dell'altro gruppo restano il
  canale, e come si consegna loro lo scarto.

---

## AS-D08 — Tracking (domanda 8; PA-07, PA-34, PA-35, PA-36)

**Stato**: confermata da EURODIS

**Risposta EURODIS**: gli endpoint sono già a disposizione:
`https://api.eurodis.com/send-tracking/documentation/index.html` e
`https://api.eurodis.com/send-pod/documentation/index.html`.

**Fatti**
- `send-tracking`: swagger letto, client implementato; eventi di spedizione e di
  collo, singoli o a lotti; A03.2 §5.3 aggiunge il livello «Pickup».
- `send-pod` (A03.2 §5.4.1): PoD a livello di spedizione o di collo; formati JPG,
  JPEG, PNG, TIF, TIFF, GIF; nessuna restrizione sul numero.
- `send-pod` è già implementato da un altro gruppo, con un meccanismo che
  useremo (Paolo, 09-11). Non descritto nel repository.

**Assunzione**
1. Gli eventi di tracking si restituiscono con `send-tracking`.
2. Per `send-pod` si usa il meccanismo già implementato.
3. Codici evento, sorgente delle tracce SDA, correlazione LDV ↔ `edReference` e
   comportamenti non scritti nello swagger restano nei punti aperti PA-34, PA-35
   e PA-36.

**Se è falsa**
- Se `send-pod` non è riusabile per `EUD_INVIOSYSTEM`, serve un'integrazione
  nostra, non prevista oggi nel perimetro.

---

## AS-D09 — Ambiente di produzione (domanda 9; PA-12)

**Stato**: confermata da EURODIS

**Risposta EURODIS**: va bene. A fine sviluppo e test basta cambiare l'endpoint e
sostituire la chiave di test con quella di produzione.

**Fatti**
- A03.2 §3 elenca gli endpoint di produzione (`api.eurodis.com`) e di test
  (`testapi.eurodis.com`) per ogni servizio. Le chiavi si generano con EURODIS
  durante l'integrazione (§5.1).
- Nessun ambiente intermedio. Go-live atteso a **fine gennaio 2027** (Paolo).
- `-in` ha `eurodis.in.abilitato=false` come default; URL e chiave stanno per
  ambiente (secret OpenShift).

**Assunzione**
1. Produzione ha le stesse API di TEST. Si passa da TEST a produzione cambiando
   URL e chiave, senza modifiche di codice.
2. TEST basta fino al go-live. Ciò che TEST non copre (campi opzionali, dati reali,
   volumi) resta non verificato fino alla produzione.
3. La chiave di produzione va richiesta a EURODIS in tempo per il go-live.

**Se è falsa**
- Se produzione differisce da TEST, emerge solo al primo scarico reale.
- Se la chiave arriva tardi, il go-live di fine gennaio slitta.

**Da chiedere a EURODIS**: una data di consegna della chiave di produzione
compatibile con il go-live.

---

## AS-D10 — Payload di esempio di produzione (domanda 10; PA-24, DF-02, DF-30)

**Stato**: non risolta da EURODIS; l'assunzione resta

**Risposta EURODIS**: nessun esempio di produzione. I campi obbligatori,
condizionali e opzionali sono descritti nella documentazione (asterisco rosso =
obbligatorio, i condizionali sono spiegati nel testo). Rimandano inoltre al
documento A03.2.

**Fatti**
- In TEST `consignorsColloBarcode` arriva vuoto e `consigneeAddress` e
  `shipperAddress` sono `null`: c'è solo `returnAddress`.
- Decisione provvisoria su DF-30: si pubblica con campi vuoti e una metrica;
  `returnAddress` non si usa.
- La risposta **non dice** se in produzione `consigneeAddress` e
  `consignorsColloBarcode` sono sempre valorizzati.

**Assunzione**
1. In produzione la LDV è valorizzata in `consignorsColloBarcode`
   (→ `collo.id_ldv`, decisione del 22-10 confermata il 06-11). Non abbiamo
   evidenza: è ciò che il design richiede.
2. Per il destinatario vale la decisione provvisoria di DF-30.
3. I campi opzionali (per esempio `entranceTimestamp`) restano non verificati e il
   mapper li tratta come facoltativi.
4. Un eventuale payload di produzione, con dati sensibili oscurati, si usa per
   verificare questi campi prima del go-live e non si versiona.

**Se è falsa**
- Se `consignorsColloBarcode` è vuoto anche in produzione, la spedizione non ha
  LDV del collo.
- Se `consigneeAddress` è `null` anche in produzione, cap e località del
  destinatario mancano e le spedizioni non sono utilizzabili a valle.

**Da chiarire in call**: `consigneeAddress` e `consignorsColloBarcode` sono sempre
valorizzati in produzione? I dati di TEST sono rappresentativi?

---

## AS-D11 — Volumi e frequenza (domanda 11; PA-14)

**Stato**: da verificare

**Risposta EURODIS**: oggi SDA riceve le stesse spedizioni via FTP, ora le
riceverà solo via API; i volumi SDA li conosce meglio di loro.

**Fatti**
- Scarico ogni 2 minuti (AS-D04). Volumi giornalieri non noti.
- Il grezzo di uno scarico sta in un solo documento Mongo (appunti sotto).

**Assunzione**
1. I volumi si ricavano dal **flusso FTP esistente**, non da EURODIS: **da
   verificare**, con un numero da inserire qui.
2. Il dimensionamento (repliche, retention Kafka, spazio Mongo) si fa dopo la
   verifica.

**Se è falsa**
- Se i volumi sono molto più alti del previsto, il grezzo può superare il limite
  del documento e il ciclo da 2 minuti può non smaltire la coda.

**Da fare**: ricavare i volumi giornalieri dal flusso FTP e inserirli qui.

---

## AS-D12 — Dogana e ADR (domanda 12; PA-13)

**Stato**: risposta di EURODIS; implicazioni da decidere

**Risposta EURODIS**: sì, sono parte dell'interfaccia. Le stesse informazioni
dell'FTP sono disponibili nell'API.

**Fatti**
- A03.2 §6 elenca campi di dogana e ADR (descrizione merce, codice dazio, valore
  della merce, numero UN, categoria di trasporto, gruppo di imballaggio...).
- SDA non offre il servizio di dogana/ADR, ma non sappiamo se i partner mittenti
  possano comunque generare questi dati.

**Assunzione**
1. I dati di dogana e ADR possono arrivare in `receive-pan` per le spedizioni che
   li prevedono.
2. Cosa ne fa il mapper (si passano, si ignorano, si scartano) **non è deciso**:
   è un tema per PA-17/PA-22 e per le decisioni sul perimetro.

**Se è falsa**
- Se arrivano dati che SDA non gestisce e nessuno decide cosa farne, spedizioni
  con merci pericolose possono entrare nella catena senza controllo.

---

## AS-D13 — Rollout incrementale (domanda 13; PA-28)

**Stato**: risposta di EURODIS; da discutere in call

**Risposta EURODIS**: all'inizio si può lavorare in modo **ibrido**; da discutere,
meglio in call. EURODIS sostiene un passaggio graduale, **settimana per
settimana**, senza spostare tutto subito sull'API.

**Assunzione**
1. Un rollout incrementale è possibile: parte delle spedizioni via API e il resto
   via FTP, con perimetro allargato di settimana in settimana.
2. **Come si seleziona il sottoinsieme** (per mittente, cliente, volume) e come
   evitare spedizioni doppie o mancanti fra FTP e API **non è deciso**.

**Se è falsa**
- Se non si può filtrare, il go-live è «big bang» e il rischio si sposta tutto
  sul primo scarico.
- Se FTP e API sono entrambi attivi per lo stesso cliente, rischio di spedizioni
  duplicate.

---

## Appunti per lo sviluppo (non sono assunzioni)

- **Copia locale del grezzo** (consiglio di EURODIS, 09-11): scrivere i dati
  ricevuti anche su un log/script locale, in parallelo al database. Oggi `-in`
  scrive su Mongo prima di elaborare. Da decidere se serve un secondo punto di
  scrittura (file, log strutturato) per coprire il caso di Mongo non
  raggiungibile subito dopo la risposta HTTP.
- **Interruttore di pubblicazione separato** (da valutare, 09-11): `-in` oggi ha
  solo `eurodis.in.abilitato`. Per la prima abilitazione in produzione potrebbe
  servire poter scaricare e salvare con la pubblicazione spenta, per guardare il
  grezzo prima di far partire la catena. Il recupero c'è già (RF-11 ripubblica i
  `DA_INVIARE`, RF-17 reinvia dal salvato senza chiamare EURODIS), manca solo il
  modo di tenere i record fermi. Da decidere con Diego/Amelia se aggiungerlo.
- **Dimensione del grezzo** (da verificare): `eurodis_scarichi` tiene il JSON
  dell'intero scarico in un documento. Con lo storico arretrato della prima
  chiamata può superare i 16 MB di Mongo. Verificare come `-in` salva il grezzo e
  se regge risposte grandi.
- **Richiesta di rimando totale** (AS-D01): se il recupero passa da una richiesta
  a EURODIS e riporta anche spedizioni già ricevute, il filtro duplicati a valle
  diventa necessario, mentre oggi `-in` non filtra nulla.
