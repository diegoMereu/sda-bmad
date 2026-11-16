<!-- Descrizione generale dell'iniziativa ricevuta il 2026-11-16, riportata così come arrivata.
     Nel titolo l'id è "146023": l'iniziativa è la 146073 (refuso da confermare).
     Per Accenture gli impatti di riferimento sono quelli degli HLD in questa cartella. -->

# Iniziativa 146023 – attività sui servizi Preadvising

## 1. Scopo del documento

Questo documento raccoglie le indicazioni per il team dedicato che prenderà in carico gli adeguamenti della catena Preadvising relativi all’iniziativa **Compliance USA Entry Type 13**.

Il componente `ce-dichiarato-builder` è esplicitamente escluso da queste attività perché resta nel perimetro del team applicativo attuale. Il builder deve acquisire e normalizzare i nuovi dati e pubblicarli sui canali di cambio stato e pre-enrichment; il team Preadvising deve garantirne la successiva gestione lungo il ciclo di lavorazione.

Sono escluse anche le modifiche ai portali, ai servizi di spedizione, a Internazionale/SLP, ai componenti Partner, alle mappe Sterling e al nuovo microservizio centralizzato verso Zonos, salvo le integrazioni necessarie per invocarlo e gestirne gli esiti.

## 2. Dati da gestire

### FASE 1 – dati di accettazione

| Campo | Cardinalità | Provenienza | Regola principale |
|---|---|---|---|
| `Account Key` | una per spedizione | canale business di acquisizione | obbligatoria per le spedizioni USA contenenti merce; lunghezza prevista di 52 caratteri |
| `Product ID` | uno per articolo | canale business di acquisizione | obbligatorio per ciascun articolo; lunghezza da 1 a 255 caratteri |

I servizi Preadvising non devono richiedere nuovamente i due campi né modificarne il valore. Devono conservarne la diversa cardinalità: l’`Account Key` appartiene alla spedizione, mentre il `Product ID` appartiene al singolo articolo.

### FASE 2 – risultato della lavorazione Zonos

| Campo | Cardinalità | Provenienza | Utilizzo |
|---|---|---|---|
| `Declaration ID` | uno per spedizione/dichiarazione | risposta del microservizio Zonos | associazione alla spedizione e propagazione verso i destinatari previsti |
| Dazi | secondo il contratto Zonos | risposta del microservizio Zonos | persistenza e propagazione downstream |
| Fee | secondo il contratto Zonos | risposta del microservizio Zonos | persistenza e propagazione downstream |

Le chiamate a Zonos devono transitare dal nuovo microservizio comune. Non devono essere implementate integrazioni dirette e indipendenti verso Zonos nei singoli servizi Preadvising.

## 3. Flusso atteso

```text
Canali business di acquisizione
        |
        | Account Key a livello spedizione
        | Product ID a livello articolo
        v
ce-dichiarato-builder                         [fuori da questo documento]
        |
        | dichiarato pubblicato su cambio stato / pre-enrichment
        v
Servizi Preadvising
        |
        | validazione, propagazione, associazione LDV e smistamento
        v
Nuovo microservizio comune Zonos              [realizzato dal team applicativo]
        |
        | Declaration ID, dazi e fee oppure errore bloccante
        v
Servizi Preadvising
        |
        | persistenza dello stato e propagazione downstream
        v
PDB / IPER / altri destinatari previsti
```

## 4. Attività per servizio

### `ce-dichiarato-validatore`

Attività FASE 1:

- estendere i DTO e i contratti interni ricevuti dal builder con `Account Key` e `Product ID`;
- mantenere l’`Account Key` sulla testata della spedizione e il `Product ID` nella collezione degli articoli;
- applicare le regole di obbligatorietà solamente alle spedizioni business dirette negli USA, contenenti merce e appartenenti ai prodotti interessati;
- verificare presenza e lunghezza dell’`Account Key`;
- verificare presenza e lunghezza del `Product ID` per ciascun articolo;
- produrre un errore puntuale che permetta di identificare il campo e, per il `Product ID`, l’articolo non valido;
- non effettuare lookup su anagrafiche e non invocare Zonos per validare semanticamente i valori.

Non sono previste attività specifiche di FASE 2, salvo l’eventuale validazione formale del contratto interno concordato per gli esiti Zonos.

### `ce-dichiarato-orchestratore`

Attività FASE 1:

- propagare `Account Key` e `Product ID` senza perdita di informazione nei diversi rami della lavorazione;
- garantire che retry, ripartenze e lavorazioni asincrone conservino i nuovi dati;
- impedire che la trasformazione dei messaggi appiattisca il `Product ID` a livello spedizione o perda l’associazione con l’articolo.

Attività FASE 2:

- introdurre l’orchestrazione della lavorazione Zonos tramite il microservizio comune;
- avviare la lavorazione nel punto concordato del processo, quando siano disponibili i dati necessari;
- gestire separatamente esito positivo, errore funzionale, timeout ed errore tecnico;
- impedire il completamento positivo dell’accettazione quando la chiamata Zonos non termina con successo;
- evitare invocazioni duplicate in caso di ridelivery o ripartenza, utilizzando una chiave di idempotenza condivisa;
- rendere disponibili `Declaration ID`, dazi e fee alle lavorazioni successive.

### `ce-dichiarato-ldv`

Attività FASE 1:

- mantenere `Account Key` e `Product ID` durante la generazione o associazione della lettera di vettura;
- conservare la relazione fra spedizione, LDV e articoli;
- garantire la rilettura dei campi nelle lavorazioni successive, senza richiedere modifiche alle stampe LDV.

Attività FASE 2:

- coordinare l’invocazione della lavorazione Zonos quando la LDV/S10 richiesta dal processo è disponibile;
- associare il `Declaration ID` restituito da Zonos alla spedizione corretta;
- conservare dazi e fee insieme al risultato della lavorazione, secondo il modello dati condiviso;
- evitare una nuova chiamata Zonos quando esiste già un risultato positivo valido per la medesima spedizione e versione dei dati doganali.

### `ce-dichiarato-smistatore`

Attività FASE 1:

- estendere DTO e mapping utilizzati per lo smistamento;
- preservare `Account Key` e l’elenco dei `Product ID` nei rami downstream interessati;
- inoltrare i nuovi dati solamente ai destinatari previsti dai rispettivi contratti;
- mantenere la compatibilità con i destinatari non ancora adeguati, se richiesta dai contratti di integrazione.

Per la FASE 2 occorre verificare se lo smistatore debba inoltrare anche `Declaration ID`, dazi e fee. In assenza di un destinatario esplicito non va introdotta una propagazione indiscriminata.

### `ce-dichiarato-adapter`

Attività FASE 1:

- aggiornare i contratti e i mapping verso PDB, IPER e gli altri destinatari confermati;
- mappare `Account Key` a livello spedizione;
- mappare ciascun `Product ID` sull’articolo corrispondente;
- gestire l’assenza dei campi negli scenari non applicabili senza alterare i flussi esistenti.

Attività FASE 2:

- estendere i contratti downstream con `Declaration ID`, dazi e fee solamente dove richiesto;
- trasformare importi e valute secondo il contratto di destinazione, senza perdita di precisione;
- impedire l’invio di un esito parziale come se fosse una lavorazione Zonos completata;
- mantenere l’idempotenza nei reinvii.

### `ce-event-handler-event-store`

Attività FASE 1:

- estendere il modello degli eventi con `Account Key` e `Product ID`;
- conservare la cardinalità per articolo durante serializzazione e deserializzazione;
- garantire che replay, consultazione e recupero dello stato ricostruiscano correttamente i nuovi dati;
- valutare la compatibilità degli eventi già memorizzati che non contengono i nuovi campi.

Attività FASE 2:

- persistere lo stato della lavorazione Zonos e il relativo esito;
- conservare `Declaration ID`, dazi e fee quando la lavorazione termina con successo;
- conservare le informazioni necessarie a distinguere timeout, errore tecnico ed errore funzionale;
- supportare replay e ripartenza senza generare chiamate duplicate o perdere un esito già acquisito.

### `ce-dichiarato-state-machine-handler`

Attività FASE 2:

- introdurre o adeguare gli stati della lavorazione Zonos;
- prevedere almeno gli stati di richiesta avviata, completata con successo e terminata con errore;
- gestire timeout, risposta non valida, errore di autorizzazione ed esito funzionale negativo;
- rendere bloccanti gli esiti diversi dal successo rispetto al completamento dell’accettazione;
- consentire retry o ripartenza solamente secondo le regole concordate, senza creare doppie dichiarazioni;
- propagare al chiamante un errore comprensibile e coerente con lo stato persistito.


## 5. Regole trasversali

- `Account Key` e `Product ID` non devono essere normalizzati, convertiti o ricalcolati nei servizi Preadvising.
- Il `Product ID` deve restare associato all’articolo corretto anche con più articoli, retry e reinvii.
- La presenza dei nuovi campi non deve rendere incompatibili gli eventi storici o gli scenari non USA.
- La chiamata Zonos deve essere effettuata esclusivamente tramite il microservizio comune.
- Timeout, errori tecnici, errori di autorizzazione, risposta non valida ed esiti funzionali negativi sono bloccanti.
- Ogni retry deve essere idempotente e non deve produrre più dichiarazioni per la stessa versione della spedizione.
- Non sono richiesti, in questa fase, un framework comune aggiuntivo di logging o un nuovo `correlation ID`.
- Non sono previste modifiche alle stampe.

## 6. Casi di test minimi

### FASE 1

- spedizione USA con un articolo, `Account Key` e `Product ID` validi;
- spedizione USA con più articoli e `Product ID` distinti;
- `Account Key` assente o con lunghezza non valida;
- un singolo articolo senza `Product ID`;
- retry e replay senza perdita dei nuovi campi;
- ricostruzione dello stato dall’event store;
- spedizione non USA e spedizione USA contenente documenti senza obbligatorietà dei nuovi campi;
- compatibilità con eventi storici privi dei nuovi attributi;
- propagazione downstream con corretta cardinalità spedizione/articolo.
