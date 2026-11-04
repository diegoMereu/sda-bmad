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
4. `iniziative/<id>/sviluppo/*.md`: un documento funzionale per microservizio.
5. Allegati tecnici dell'iniziativa: ICD, swagger, mapping in xlsx.
6. `contesto/glossario-ce.md` per i termini.

Se due fonti divergono vale la più recente con una decisione datata; segnala la
divergenza a fine lavoro, non sceglierla in silenzio.

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
- **Riferimenti**: i documenti citati nel testo, numerati; nel testo si
  rimanda con "documento di riferimento ID n".
- **Vincoli, Assunzioni, Esclusioni ed Open Point**: qui confluiscono i punti
  aperti che interessano il cliente: domande a partner o a terzi, decisioni non
  prese, esclusioni di perimetro. Tipo = Vincolo | Assunzione | Esclusione |
  Open Point. Non riportare i punti interni già chiusi.
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
- Lunghezza: quanto serve al cliente per approvare. Per un'iniziativa a tre
  microservizi sono 6–12 pagine, non 40. Rimanda agli allegati per i mapping
  campo per campo.

## Regole sui buchi

- **Non inventare.** Codici AP/PK, nomi di namespace, volumi, nomi di topic
  non ancora confermati: si scrive `DA DEFINIRE` (il generatore lo evidenzia in
  giallo) e si aggiunge una riga in "Vincoli, Assunzioni, Esclusioni ed Open
  Point".
- Ciò che è proposto ma non deciso si scrive come proposta ("si propone
  di…") e ha la sua riga di Open Point.
- Dati di produzione (nomi, indirizzi, CF, P.IVA) mai, nemmeno negli esempi
  di DTO: si usano valori fittizi evidenti.
- Le figure (architettura, sequence) sono drawio del team: nel master metti
  `![Figura n: <didascalia>](<file>.png)`. Se il file non c'è, il generatore
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

## Prima di consegnare

- [ ] Ogni sezione obbligatoria c'è (anche con "Non applicabile").
- [ ] Ogni `DA DEFINIRE` ha la sua riga negli Open Point.
- [ ] Ogni documento citato è in Riferimenti o Allegati.
- [ ] Nessun dettaglio solo interno (metriche, test, classi, default provvisori).
- [ ] Il Word si genera senza errori.
- [ ] In fondo alla risposta, non nel documento: le domande per Diego.
