# Prompt — documento funzionale `portal-pages` (sezione "Informazioni preavviso")

> Prompt per Mary (analyst): genera il documento funzionale del front-end `portal-pages` per
> l'iniziativa 144216.
> Output: `iniziative/144216/sviluppo/portal-pages.md`, da passare alla sviluppatrice front-end.
> Regola di progetto: un documento funzionale per microservizio.

---

# Contesto

Sei l'Analyst del progetto. Devi scrivere il **documento funzionale per la sviluppatrice** del
front-end `portal-pages` di OneTracking (Nuxt 3.14, Vue 3, Vuex 4), nell'iniziativa 144216
"Assistenza Clienti — Customer Journey preavviso" (PRJ0049429, Poste Italiane / SDA, filone PCL-127).

Nel dettaglio LdV si aggiunge la sottosezione **"Informazioni preavviso"**, fra "Informazioni LV" e
"Cliente/Mittente/Destinatario", per gli operatori dell'assistenza clienti. I dati arrivano dalla
nuova API `GET /api/preavviso/{ldv}` di `shipment-info`, sviluppata in parallelo da un'altra
sviluppatrice sul contratto di `analisi.md`. Il contratto è **vincolante**: il documento lo dettaglia,
non lo cambia. Incoerenze e buchi vanno fra le domande aperte.

Il preavviso lo sceglie il back-end (regola su `event_type` confermata da Diego il 13-11, AS-01
chiusa); il front-end mostra, formatta le date e decide la visibilità dei blocchi.

# Fonti (in `iniziative/144216/`)

- `analisi.md`: le tre sezioni, mapping, contratto JSON, assunzioni AS-01…AS-07.
- `cliente/Recupero_risottomissione_preadvising_bozza_v0.8.pptx`: mock up (slide 2 obiettivo,
  slide 3-5 i tre casi), DREQ0062862, DREQ0062864, DREQ0062865, DREQ0062866.
- `sviluppo/shipment-info.md`: documento gemello del back-end (decodifiche, esempi di risposta,
  assunzioni comuni).
- `contesto/onetracking.md`: architettura, proxy `/api`, autenticazione SiteMinder, tipologie utente.
- Codice in sola lettura (non modificare, non fare checkout):
  `gitposte/SDA/ONETRACKING/PRESENTATION/portal-pages`, in particolare `components/IndexRicerche.vue`
  (tab "Mittente/Destinatario", `caseInfoSpedizioni`, export), `components/DatiCliente.vue`
  ("Informazioni LV"), `components/InfoMittenteDestinatario.vue`, `stores/views/*`,
  `utils/safe-fetch.js`, `nuxt.config.js` (`runtimeConfig.public.wsAction*`, `routeRules`).
- Modello di forma: `iniziative/136596/sviluppo/ce-eurodis-send-tracking.md`.

# Cosa ti chiedo

Struttura: contesto e obiettivo, requisiti DREQ coperti, dove si interviene nel codice, **layout ed
etichette esattamente come nel mock up** (ordine dei blocchi, titoli, colonne, testo "N errori
riscontrati"), regole di visibilità dei blocchi (Canale solo senza file, blocco file solo con file,
errori solo con errori, nessun preavviso, errore dell'API), formati (date `dd/MM/yyyy HH:mm` ora di
Roma, `-` per i vuoti), contratto API, comportamento della chiamata e dello store, casi d'uso con
esempi (i tre casi del mock up, nessun preavviso, T&T-Repo non disponibile), criteri di accettazione
numerati, casi di test, assunzioni e domande aperte.

Approfondisci:

1. dove si inserisce il componente nel tab e che cosa succede quando il tab mostra "Dati non presenti";
2. indipendenza della chiamata dal resto del tab (errore, timeout, caricamento);
3. ricerca massiva e cambio rapido di LdV selezionata;
4. visibilità per tipologia utente (ASSISTENZA, SDA, FILIALI) ed export PDF/Excel;
5. coerenza del path `/api/preavviso` con il proxy Nitro.

# Regole

- Distingui **[FATTO]** (con la fonte), **[DECISO]** (data e riferimento), **[ASSUNTO]** (ID e default).
- Riprendi AS-01…AS-07 e usa la numerazione comune con `shipment-info.md` per le nuove (da AS-08).
- Niente dati di produzione: gli esempi a video sono inventati (non riprodurre nomi e indirizzi del
  mock up).
- Non cambiare il contratto; non spostare logica di dominio nel front-end.
- Lingua italiana; nomi file e ID ASCII.
