# Guida — Documento di Specifiche Funzionali (SF)

Istruzioni per chi redige la SF di un'iniziativa (di norma Mary, `/sf <id>`).
Ricavate dagli esempi in `contesto/esempi specifica funzionale/` (138972:
Reply v1.0, Reply v1.1 FileImpianti, PRJTASK0609165 SI, Enrichment LDV).

## Cos'è e per chi

È il documento che Poste (DTO / IT AS Corriere Espresso) riceve, verifica e
approva. Descrive **cosa** fa la soluzione e **quali sistemi tocca**: flussi,
regole funzionali, stati, interfacce. Il lettore conosce il dominio CE e i
sistemi SDA (Ermes, BEP, palmari, PDB), ma non il nostro lavoro interno.

**Una SF per iniziativa.** Copre tutti i microservizi dell'iniziativa,
organizzati per fase di processo o per requisito, non per microservizio.

Non è il documento per lo sviluppatore: quello è
`iniziative/<id>/sviluppo/<microservizio>.md` ed è la **fonte** della SF. La SF ne
prende il "cosa" e lascia fuori il "come" interno: niente metriche Datadog,
criteri di accettazione Given/When/Then, nomi di classi, configurazioni Helm o
default provvisori di sviluppo.

## Fonti, in ordine di autorità

1. `iniziative.yaml`: titolo, PRJ, owner, perimetro.
2. `iniziative/<id>/PUNTO.md`: decisioni prese (con data) e cosa serve dal cliente.
3. `iniziative/<id>/analisi.md` e registri dei punti aperti (PA-nn, DF-nn).
4. `iniziative/<id>/sviluppo/`:
   - `<microservizio>.md`: documento funzionale del ms, usa la versione
     indicata nel file;
   - `assessment-*`, `rapporto-*`, `verifica-*`: stato del codice; contano
     solo se più recenti della specifica, e allora la divergenza va segnalata;
   - `prompt-*.md`: **non** sono fonti, ignorali.
5. Allegati tecnici dell'iniziativa: ICD, swagger, mapping in xlsx.
6. `contesto/glossario-ce.md` per i termini.

A parità di tema vale la decisione datata più recente, da qualunque fonte
venga; l'ordine qui sopra serve solo quando mancano le date. Segnala ogni
divergenza a fine lavoro, non sceglierla in silenzio.

**Microservizio senza documento di sviluppo**: descrivilo da analisi, registri
e proposte; ciò che non è deciso è `DA DEFINIRE` con il suo Open Point.

## Struttura (obbligatoria)

La copertina (titolo della richiesta, codice iniziativa, compilato da,
versione, revisioni) la genera il template dal front-matter: **non** va nel corpo.

```
# Introduzione
## Scopo
## Definizione, Acronimi e Abbreviazioni      tabella | Sigla | Significato esteso |
## Riferimenti                               tabella | Id. Documento | Tipo di Documento | Titolo Documento | Allegato |
## Vincoli, Assunzioni, Esclusioni ed Open Point   tabella | Id | Tipo | Descrizione | Riferimento |
# Obiettivo dell'iniziativa
# Soluzione
## <fase di processo 1>            es. Acquisizione, Trasformazione, Propagazione, Tracciamento
### <componente o funzionalità>
#### <dettaglio>                   AS IS / TO BE, esiti, DTO, stati
## ...
# Elenco Sistemi Impattati          tabella | Sistema | Componente | Tipo intervento | Nuovo/Esistente |
# Allegati                          tabella | ID Documento | Tipo Documento | Titolo e Contenuto | Allegato |
```

Se l'iniziativa ha requisiti numerati dal cliente (DREQ, "Req n"), il capitolo
si chiama `# Specifiche Funzionali` e le sezioni `## Req n – <titolo>`, come
in Reply v1.0. Altrimenti si usa `# Soluzione` per fasi, come in SI.

### Cosa mettere in ogni sezione

- **Scopo**: una o due frasi. Modello: "Il presente documento contiene
  l'analisi degli impatti funzionali relativi all'Iniziativa "<id> - <titolo>"."
- **Acronimi**: solo le sigle usate nel testo (LDV, ICD, ms, PDB, CE...).
- **Riferimenti**: documenti che esistono altrove (altre SF, specifiche,
  riscontri del cliente), numerati, con percorso SharePoint o link nella
  colonna Allegato; se non lo conosci, `DA DEFINIRE` e una domanda per Diego.
  Nel testo si rimanda con "documento di riferimento ID n".
- **Allegati** (ultimo capitolo): i file consegnati insieme alla SF (ICD con
  mapping, swagger, drawio). Un file non ancora prodotto si scrive
  "in preparazione".
- **Vincoli, Assunzioni, Esclusioni ed Open Point**: qui confluiscono i punti
  aperti che interessano il cliente: domande a partner o a terzi, decisioni non
  prese, esclusioni di perimetro. Non riportare i punti interni già chiusi.
  Formato:
  - Id numerico 1..n, citato nel testo come "Open Point n" (o "vincolo n",
    "assunzione n");
  - Tipo = Vincolo | Assunzione | Esclusione | Open Point, in quest'ordine;
  - gli Open Point sono ordinati per interlocutore (partner, cliente, SDA,
    team), così ognuno trova i suoi in un blocco;
  - Riferimento = "<sezione>; <interlocutore>";
  - niente codici interni PA-nn / DF-nn;
  - un'esclusione di perimetro non ancora confermata resta Esclusione, con
    "da confermare" nel testo;
  - i rilievi su sistemi esistenti di altri team sono un Open Point verso il
    loro responsabile, più un N.B. nella sezione che li usa.
- **Obiettivo dell'iniziativa**: l'esigenza di business in prosa (perché
  serve), poi gli obiettivi in elenco. Mezza pagina.
- **Soluzione**: apre con una frase che elenca i temi trattati (elenco
  puntato) e con la figura dell'architettura. Poi una sezione per fase. Per
  ogni fase:
  - prima il **funzionale** in prosa: cosa succede, chi lo fa, con quali dati;
  - poi, se serve, i **passi numerati** in tabella `| Passo | Descrizione |`
    ("Il ms X legge dal topic Y…"), come la tabella 1.A/1.B di Reply;
  - **esiti e stati** in tabella `| Esito/Stato | Descrizione |`;
  - **DTO o schema del messaggio** in un blocco di codice, se è un'interfaccia
    verso un altro sistema;
  - chiude con il paragrafo **"Ulteriori dettagli:"**, che nomina il
    microservizio che implementa la funzione, il namespace OpenShift, i topic
    letti e scritti. È il modo degli esempi di legare funzionale e componente.
- **Elenco Sistemi Impattati**: tutti i sistemi toccati, nuovi ed esistenti.
- **Allegati**: ICD, mapping, swagger, drawio, con il nome file.

## Stile

- Italiano formale e impersonale, al presente o futuro ("il microservizio
  legge…", "verrà implementato…"). Niente prima persona, niente "noi".
- Prosa continua, con elenchi brevi solo per enumerazioni. Gli esempi non
  usano grassetti diffusi né emoji.
- Nomi tecnici esatti: microservizi in minuscolo (`ce-dichiarato-eurodis-in`),
  topic Kafka e tabelle come sono (`preadvising.pre-enrichment`,
  `sew_spedizioni_work`), campi dell'ICD con il loro nome.
- Le decisioni si scrivono come fatti della soluzione ("lo storico viene
  salvato su…"), non come cronaca ("il 30-10 si è deciso…"). Se la decisione è
  del cliente e serve tracciarla, va bene "In data gg/mm/aaaa è stato deciso…"
  (stile Reply, Req 10).
- Il "N.B." si usa per vincoli transitori o di convivenza col legacy.
- **Livello di dettaglio.** Nella SF vanno ciò che vede chi integra o
  approva: interfacce e contratti verso altri sistemi (topic, chiave, schema
  del messaggio), stati di business, regole funzionali, comportamento in caso
  di errore. Restano nel documento di sviluppo: parametri di esecuzione
  (cadenze, numero di tentativi, timeout), stati tecnici interni
  dell'esecuzione, header tecnici come `traceparent`, nomi di collezioni e
  classi. Una frase di sintesi ("lo scarico è periodico e non viene ripetuto
  automaticamente") sostituisce il parametro.
- Lunghezza: quanto serve al cliente per approvare. Per un'iniziativa a tre
  microservizi sono 6–12 pagine **di corpo**, esclusa la tabella degli Open
  Point. Rimanda agli allegati per i mapping campo per campo.

## Regole sui buchi

- **Non inventare.** Codici AP/PK, nomi di namespace, volumi, nomi di topic
  non ancora confermati: si scrive `DA DEFINIRE` (il generatore lo evidenzia in
  giallo) e si aggiunge una riga in "Vincoli, Assunzioni, Esclusioni ed Open
  Point".
- Ciò che è proposto ma non deciso si scrive come proposta ("si propone
  di…") e ha la sua riga di Open Point.
- Dati di produzione (nomi, indirizzi, CF, P.IVA) mai, nemmeno negli esempi
  di DTO: si usano valori fittizi evidenti.
- Le figure (architettura, sequence) sono drawio del team, salvati in
  `iniziative/<id>/documenti/fig-<n>-<slug>.drawio` con l'export
  `fig-<n>-<slug>.png` accanto. Nel master metti
  `![Figura n: <didascalia>](fig-<n>-<slug>.png)`. Se il file non c'è, il generatore
  lascia un segnaposto rosso. Descrivi comunque in testo o in tabella quello
  che la figura mostra: il documento deve reggere anche senza figura.

## File

- Master: `iniziative/<id>/documenti/SF_<id>_<slug>.md`. Lo slug è il titolo
  in ASCII con trattini bassi, es. `SF_136596_Eurodis_autoproduttore.md`.
- Word: si genera con
  `python contesto/modelli/md2docx.py iniziative/<id>/documenti/SF_<id>_<slug>.md`
  e finisce accanto al master, stesso nome `.docx`. Il Word non si modifica a
  mano: si corregge il master e si rigenera. All'apertura Word chiede di
  aggiornare i campi: rispondere sì, così si aggiorna il sommario.

### Front-matter del master

```yaml
---
tipo: sf
titolo: "<titolo della richiesta, come in iniziative.yaml>"
codice_iniziativa: "<id>"
prj: "<PRJ o null>"
ticket: null              # TICKET STS, se esiste
compilato_da: "GDL ACN"
verificato_da: ""
approvato_da: ""
versione: "0.1"
distribuito_a: "DTO/IT/BASSPDCB/IT AS COR ESPR"
revisioni:
  - {data: "gg/mm/aaaa", versione: "0.1", stato: "Bozza", descrizione: "Prima emissione", autore: "ACN"}
---
```

Markdown ammesso nel corpo (il generatore capisce solo questo): titoli
`#`…`####`, paragrafi, elenchi `- ` e `1. `, tabelle pipe (a capo in cella con
`<br>`), blocchi ```, immagini `![..](..)`, didascalie `Figura n: …` /
`Tabella n: …` su riga propria, `**grassetto**`, `*corsivo*`, `` `codice` ``.
Niente Mermaid, HTML, note a piè di pagina o link markdown.
Limiti del generatore: gli elenchi numerati sono testo "1. " (non numerazione
Word) e gli elenchi annidati non sono supportati; usa una tabella se serve
una struttura a due livelli.

## Prima di consegnare

- [ ] Ogni sezione obbligatoria c'è (anche con "Non applicabile").
- [ ] Ogni `DA DEFINIRE` ha la sua riga negli Open Point.
- [ ] Ogni documento citato è in Riferimenti o Allegati.
- [ ] Nessun dettaglio solo interno (metriche, test, classi, default provvisori).
- [ ] Il Word si genera senza errori.
- [ ] In fondo alla risposta, non nel documento: le domande per Diego.
