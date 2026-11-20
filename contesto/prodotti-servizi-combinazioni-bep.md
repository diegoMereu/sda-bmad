# TESTLIST - COMBINAZIONI SERVIZI ACCESSORI / PRODOTTI

| PRODOTTO | CODICE PRODOTTO | TIPOLOGIA | CANALI SUPPORTATI |
| --- | --- | --- | --- |
| Pacco Delivery Business Express | APT000901 | Nazionale | INVIOSYSTEM, INVIOFILE, INVIOEASY, STAMPAMASSIVA |
| Pacco Delivery Business Standard | APT000902 | Nazionale | INVIOSYSTEM, INVIOFILE, INVIOEASY, STAMPAMASSIVA |
| Pacco Express Internazionale | APT000903 | Internazionale Express | INVIOSYSTEM, INVIOFILE, INVIOEASY, STAMPAMASSIVA |
| Pacco Express Internazionale Standard | APT000904 | Internazionale Standard | INVIOSYSTEM, INVIOFILE, INVIOEASY, STAMPAMASSIVA |
|  | APT001013  | International Plus |  |

## SERVIZI ACCESSORI - NAZIONALE EXPRESS (APT000901)

| CODICE | NOME SERVIZIO | PARAMETRI RICHIESTI | ESEMPIO JSON | COMPATIBILE CON | FORMATO file |
| --- | --- | --- | --- | --- | --- |
| APT000905 | Time Definite Ore 9 | Nessuno | "APT000905":{} | Contrassegno, Copertura Full, A&amp;R, Vicino, Piano, Rit.Mitt |  |
| APT000906 | Time Definite Ore 10 | Nessuno | "APT000906":{} | Contrassegno, Copertura Full, A&amp;R, Vicino, Piano, Multicollo, Rit.Mitt |  |
| APT000907 | Time Definite Ore 12 | Nessuno | "APT000907":{} | Contrassegno, Copertura Full, A&amp;R, Vicino, Piano, Multicollo, Rit.Mitt |  |
| APT000908 | Consegna su Appuntamento | Tel. Destinatario | "APT000908":{} | Contrassegno, Copertura Full, A&amp;R, Vicino, Piano, Sabato, Sera, Multicollo |  |
| APT000909 | Consegna Programmata | days (6 digit), note fasce | "APT000909":{"days":"G02100","note":"10:00-12:00"} | Contrassegno, Copertura Full, A&amp;R, Vicino, Piano, Multicollo |  |
| APT000910 | Consegna di Sabato | Nessuno | "APT000910":{} | Contrassegno, Copertura Full, A&amp;R, Appuntamento, Vicino, Piano, Multicollo |  |
| APT000911 | Consegna di Sera | Nessuno | "APT000911":{} | Contrassegno, Copertura Full, A&amp;R, Appuntamento, Vicino, Piano, Multicollo |  |
| APT000912 | Consegna Giorno/Orario Definito | days (6 digit: G+GGMM+M/P) | "APT000912":{"days":"G0910M"} | Contrassegno, Copertura Full, A&amp;R, Vicino, Piano, Multicollo |  |
| APT000913 | Consegna al Piano | note (ASCENSORE/NO) | "APT000913":{"note":"ASCENSORE"} | Tutti tranne Reverse singolo |  |
| APT000914 | Consegna al Vicino | neighbourName | "APT000914":{"neighbourName":"Nome"} | Tutti tranne Time Definite singoli |  |
| APT000918 | Contrassegno | amount, paymentMode (CON/ACM/ABM) | "APT000918":{"amount":"100.00","paymentMode":"ABM"} | Tutti tranne: Reverse A Domicilio (APT000928), Reverse PuntoPoste (APT000979), Reverse PuntoPoste Locker (APT000980), Reverse Ufficio Postale (APT000981), PuntoPoste (APT000947), PuntoPoste Locker (APT000948) |  |
| APT000919 | Copertura Full | amount | "APT000919":{"amount":"1000.00"} | Tutti |  |
| APT000928 | Reverse (Ritiro a Domicilio) | Nessuno | "APT000928":{} | Copertura Full |  |
| APT000929 | Andata &amp; Ritorno | roundtrip (AND/RIT) | "APT000929":{"roundtrip":"AND"} | Tutti tranne Reverse |  |
| APT000930 | Ritorno al Mittente/Abbandono | return (A/R) | "APT000930":{"return":"R"} | Tutti tranne: Reverse A Domicilio (APT000928), Reverse PuntoPoste (APT000979), Reverse PuntoPoste Locker (APT000980), Reverse Ufficio Postale (APT000981), Scheduled (APT000982-APT000995), Same Day (APT000996-APT001002), Instant (APT001003-APT001005) |  |
| APT000945 | Multicollo | Nessuno (gestito automaticamente) | N/A | Tutti tranne: Time Definite Ore 9 (APT000905), Contrassegno (APT000918), Reverse A Domicilio (APT000928), Reverse PuntoPoste (APT000979), Reverse PuntoPoste Locker (APT000980), Reverse Ufficio Postale (APT000981), PuntoPoste (APT000947), PuntoPoste Locker (APT000948). Per A&amp;R (APT000929): solo spedizione di Andata. Nota: la 'V' della matrice fonte per Contrassegno (APT000918) è stata assunta come typo di 'X' → Multicollo e Contrassegno sono INCOMPATIBILI. |  |
| APT000946 | Consegna a Domicilio | Nessuno | "APT000946":{} | Tutti gli accessori di consegna |  |
| APT000947 | PuntoPoste | Nessuno | "APT000947":{} | Copertura Full, Ritorno Mittente |  |
| APT000948 | PuntoPoste Locker | Nessuno | "APT000948":{} | Copertura Full, Ritorno Mittente |  |
| APT000949 | Ufficio Postale (Fermoposta) | Nessuno | "APT000949":{} | Contrassegno, Copertura Full, Multicollo, Ritorno Mittente |  |

## SERVIZI SCHEDULED / SAME DAY / INSTANT (PDB EXPRESS)

| CODICE | NOME SERVIZIO | FASCIA | COMPATIBILE CON |
| --- | --- | --- | --- |
| APT000982 | Scheduled Day 4 Ore | Day | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000983 | Scheduled Day 3 Ore | Day | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000984 | Scheduled Day 2 Ore | Day | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000985 | Scheduled Day 90 Minuti | Day | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000986 | Scheduled Day 60 Minuti | Day | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000987 | Scheduled Day 30 Minuti | Day | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000988 | Scheduled Anytime | Anytime | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000989 | Scheduled Night 4 Ore | Night | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000990 | Scheduled Night 3 Ore | Night | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000991 | Scheduled Night 2 Ore | Night | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000992 | Scheduled Night 90 Minuti | Night | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000993 | Scheduled Night 60 Minuti | Night | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000994 | Scheduled Night 30 Minuti | Night | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000995 | Scheduled Night 15 Minuti | Night | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000996 | Same Day 4 Ore | Same Day | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000997 | Same Day 3 Ore | Same Day | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000998 | Same Day 2 Ore | Same Day | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT000999 | Same Day 90 Minuti | Same Day | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT001000 | Same Day 60 Minuti | Same Day | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT001001 | Same Day 30 Minuti | Same Day | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT001002 | Same Day 15 Minuti | Same Day | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT001003 | Instant 1 Ora | Instant | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT001004 | Instant 2 Ore | Instant | Contrassegno, Copertura Full, Multicollo, A Domicilio |
| APT001005 | Instant 3 Ore | Instant | Contrassegno, Copertura Full, Multicollo, A Domicilio |

## SERVIZI ACCESSORI - NAZIONALE STANDARD (APT000902)

| CODICE | NOME SERVIZIO | PARAMETRI | COMPATIBILE CON |
| --- | --- | --- | --- |
| APT000908 | Consegna su Appuntamento | Tel. Destinatario | Contrassegno, Copertura Full, Vicino, Piano, Sera, Multicollo |
| APT000909 | Consegna Programmata | days, note | Contrassegno, Copertura Full, Vicino, Piano, Multicollo, A Domicilio |
| APT000911 | Consegna di Sera | Nessuno | Contrassegno, Copertura Full, Appuntamento, Vicino, Piano, Multicollo |
| APT000913 | Consegna al Piano | note (ASCENSORE) | Contrassegno, Copertura Full, Appuntamento, Vicino, Sera, Multicollo, Programmata |
| APT000914 | Consegna al Vicino | neighbourName | Contrassegno, Copertura Full, Appuntamento, Piano, Sera, Multicollo, Programmata |
| APT000918 | Contrassegno | amount, paymentMode | Tutti tranne: Reverse A Domicilio (APT000928), Reverse PuntoPoste (APT000979), Reverse PuntoPoste Locker (APT000980), Reverse Ufficio Postale (APT000981), PuntoPoste (APT000947), PuntoPoste Locker (APT000948) |
| APT000919 | Copertura Full | amount | Tutti |
| APT000928 | Reverse (Ritiro a Domicilio) | Nessuno | Copertura Full |
| APT000930 | Ritorno al Mittente/Abbandono | return (A/R) | Tutti tranne: Reverse A Domicilio (APT000928), Reverse PuntoPoste (APT000979), Reverse PuntoPoste Locker (APT000980), Reverse Ufficio Postale (APT000981), Scheduled (APT000982-APT000995) |
| APT000945 | Multicollo | Nessuno | Tutti tranne: Reverse A Domicilio (APT000928), Reverse PuntoPoste (APT000979), Reverse PuntoPoste Locker (APT000980), Reverse Ufficio Postale (APT000981), PuntoPoste (APT000947), PuntoPoste Locker (APT000948) |
| APT000946 | Consegna a Domicilio | Nessuno | Scheduled Delivery, tutti accessori consegna |
| APT000947 | PuntoPoste | Nessuno | Copertura Full, Ritorno Mittente |
| APT000948 | PuntoPoste Locker | Nessuno | Copertura Full, Ritorno Mittente |
| APT000949 | Ufficio Postale | Nessuno | Contrassegno, Copertura Full, Multicollo, Ritorno Mittente |
| Da APT000982 a APT000995 | Scheduled Delivery | Varie fasce | Contrassegno, Copertura Full, Multicollo, A Domicilio |

## SERVIZI ACCESSORI - INTERNAZIONALE EXPRESS (APT0003/APT000903)

| CODICE | NOME SERVIZIO | NOTE | COMPATIBILE CON |
| --- | --- | --- | --- |
| APT000945 | Multicollo |  | Oneri Doganali, Coperture Full, A Domicilio |
| APT000946 | Consegna a Domicilio |  | Oneri Doganali Mittente (APT000972), Multicollo (APT000945), Copertura Full fino a 1.500€ (APT000955), Copertura Full fino a 50.000€ (APT000956), Reverse Internazionale (APT000971). NON compatibile con Consegna Punto di Prossimità (APT000939) |
| APT000939 | Consegna Punto di Prossimità |  | Oneri Doganali, Coperture Full |
| APT000955 | Copertura Full (fino a 1.500€) |  | Multicollo, Oneri Doganali, A Domicilio, Punto Prossimità |
| APT000956 | Copertura Full (fino a 50.000€) |  | Multicollo, Oneri Doganali, A Domicilio, Punto Prossimità |
| APT000971 | Reverse Internazionale |  | Solo A Domicilio |
| APT000972 | Oneri Doganali al Mittente |  | Multicollo, Coperture Full, A Domicilio, Punto Prossimità |

## SERVIZI ACCESSORI - INTERNAZIONALE STANDARD (APT000904)

| CODICE | NOME SERVIZIO | NOTE | COMPATIBILE CON |
| --- | --- | --- | --- |
| APT000918 | Contrassegno |  | Multicollo (APT000945), Copertura Full fino a 1.500€ (APT000955), Copertura Full fino a 50.000€ (APT000956), Consegna a Domicilio (APT000946) |
| APT000945 | Multicollo |  | Contrassegno, Coperture Full, Supplemento Import, A Domicilio |
| APT000946 | Consegna a Domicilio |  | Multicollo, Contrassegno, Coperture Full, Reverse |
| APT000955 | Copertura Full (fino a 1.500€) |  | Multicollo, Contrassegno, A Domicilio, Fermoposta/Locker |
| APT000956 | Copertura Full (fino a 50.000€) |  | Multicollo, Contrassegno, A Domicilio, Fermoposta/Locker |
| APT000961 | Fermoposta/Casella/Locker/Prossimità |  | Coperture Full |
| APT000962 | Supplemento Import |  | Multicollo (APT000945), Copertura Full fino a 1.500€ (APT000955), Copertura Full fino a 50.000€ (APT000956) |
| APT000971 | Reverse Internazionale |  | A Domicilio |

## CASI DI TEST SUGGERITI (COMBINAZIONI TIPICHE)

| # | PRODOTTO | CANALE | SERVIZI COMBINATI | SCENARIO | ESITO ATTESO | NOTE / VERIFICA |
| --- | --- | --- | --- | --- | --- | --- |
| TC001 | APT0001 | INVIOSYSTEM | Base senza accessori | Spedizione semplice monocollo | POSITIVO | Caso base monocollo: nessun accessorio, nessun vincolo. |
| TC002 | APT0001 | INVIOSYSTEM | APT000918 (Contrassegno) | Contrassegno contanti | POSITIVO | Verificare parametri obbligatori: amount + paymentMode (CON/ACM/ABM). |
| TC003 | APT0001 | INVIOSYSTEM | APT000918 + APT000919 | Contrassegno + Copertura Full | POSITIVO | Contrassegno (APT000918) + Copertura Full (APT000919=Tutti): compatibili. |
| TC004 | APT0001 | INVIOSYSTEM | APT000905 + APT000918 + APT000913 | TD Ore 9 + Contrassegno + Al Piano | POSITIVO | TD Ore 9 compatibile con Contrassegno e Piano. BORDO: TD Ore 9 NON ammette Multicollo (vedi caso negativo TC019). |
| TC005 | APT0001 | INVIOSYSTEM | APT000929 | Andata &amp; Ritorno | POSITIVO | A&amp;R (APT000929) param roundtrip (AND/RIT). Non compatibile con Reverse. |
| TC006 | APT0001 | INVIOFILE | APT000946 + APT000908 | A Domicilio + Su Appuntamento | POSITIVO | A Domicilio (APT000946) + Appuntamento (APT000908): compatibili. |
| TC007 | APT0001 | INVIOEASY | APT000912 + APT000913 | Giorno Definito + Al Piano | POSITIVO | Giorno Definito (APT000912) + Al Piano (APT000913): compatibili. Param days G+GGMM+M/P. |
| TC008 | APT0001 | INVIOSYSTEM | APT000947 | Consegna PuntoPoste | POSITIVO | PuntoPoste (APT000947): compatibile SOLO con Copertura Full e Ritorno Mittente. |
| TC009 | APT0001 | INVIOSYSTEM | APT000948 | Consegna Locker | POSITIVO | Locker (APT000948): compatibile SOLO con Copertura Full e Ritorno Mittente. |
| TC010 | APT000902 | INVIOSYSTEM | Base | Standard senza accessori | POSITIVO | Caso base Standard: nessun accessorio. |
| TC011 | APT000902 | INVIOSYSTEM | APT000918 + APT000909 | Contrassegno + Programmata | POSITIVO | Contrassegno + Programmata (APT000909) su STD: compatibili. Param days 6 cifre + note fasce. |
| TC012 | APT000902 | INVIOFILE | APT000982 + APT000946 | Scheduled Day 4h + A Domicilio | POSITIVO | Scheduled Day 4h (APT000982) + A Domicilio (APT000946) su STD: compatibili. |
| TC013 | APT0003 | INVIOSYSTEM | APT000972 | Int. Express + Oneri Doganali Mittente | POSITIVO | Int. Express + Oneri Doganali Mittente (APT000972): compatibile. |
| TC014 | APT0003 | INVIOSYSTEM | APT000955 + APT000945 | Int. Express + Copertura + Multicollo | POSITIVO | Int. Express: Copertura 1.500€ (APT000955) + Multicollo (APT000945): compatibili. |
| TC015 | APT000904 | INVIOSYSTEM | APT000918 + APT000955 | Int. Standard + Contrassegno + Copertura | POSITIVO | Int. Standard: Contrassegno (APT000918) + Copertura 1.500€ (APT000955): compatibili. |
| TC016 | APT000904 | INVIOFILE | APT000961 | Int. Standard + Fermoposta | POSITIVO | Int. Standard + Fermoposta/Locker (APT000961): compatibile con Coperture Full. |
| TC017 | APT0001 | STAMPAMASSIVA | APT000945 | Stampa Massiva Multicollo | DA VERIFICARE | Canale STAMPAMASSIVA ammesso solo su Nazionali (APT0001/902). Verificare supporto effettivo a valle del flusso. |

### CASI NEGATIVI (INCOMPATIBILITÀ ATTESE - DEVONO ESSERE RESPINTI)

| # | PRODOTTO | CANALE | SERVIZI COMBINATI | SCENARIO | ESITO ATTESO | NOTE / VERIFICA |
| --- | --- | --- | --- | --- | --- | --- |
| TC018 | APT0001 | INVIOSYSTEM | APT000945 + APT000918 | Multicollo + Contrassegno (incompatibili) | NEGATIVO (KO) | Assumendo la 'V' della matrice fonte come typo di 'X' (riga A29): Multicollo (APT000945) esclude Contrassegno (APT000918). La combinazione deve essere RESPINTA. |
| TC019 | APT0001 | INVIOSYSTEM | APT000905 + APT000945 | TD Ore 9 + Multicollo | NEGATIVO (KO) | TD Ore 9 (APT000905) è l'UNICA Time Definite esclusa dal Multicollo (riga A29). Deve essere respinto. |
| TC020 | APT0001 | INVIOSYSTEM | APT000947 + APT000918 | PuntoPoste + Contrassegno | NEGATIVO (KO) | Contrassegno esclude esplicitamente PuntoPoste (APT000947). Deve essere respinto. |
| TC021 | APT0001 | INVIOSYSTEM | APT000948 + APT000918 | Locker + Contrassegno | NEGATIVO (KO) | Contrassegno esclude PuntoPoste Locker (APT000948). Deve essere respinto. |
| TC022 | APT0001 | INVIOSYSTEM | APT000928 + APT000918 | Reverse a Domicilio + Contrassegno | NEGATIVO (KO) | Reverse (APT000928) compatibile SOLO con Copertura Full. Contrassegno deve essere respinto. |
| TC023 | APT0001 | INVIOSYSTEM | APT000928 + APT000929 | Reverse + Andata&amp;Ritorno | NEGATIVO (KO) | A&amp;R (APT000929) = 'Tutti tranne Reverse'. Deve essere respinto. |
| TC024 | APT0001 | INVIOSYSTEM | APT000947 + APT000948 | PuntoPoste + Locker | NEGATIVO (KO) | Due punti di consegna mutuamente esclusivi. Deve essere respinto. |
| TC025 | APT000904 | INVIOSYSTEM | APT000961 + APT000918 | Int.STD Fermoposta + Contrassegno | NEGATIVO (KO) | Fermoposta/Locker (APT000961) compatibile SOLO con Coperture Full. Contrassegno KO. |
| TC026 | APT0003 | INVIOSYSTEM | APT000946 + APT000939 | Int.EXP A Domicilio + Punto Prossimità | NEGATIVO (KO) | A Domicilio (APT000946) NON compatibile con Punto di Prossimità (APT000939, riga A89). KO. |
| TC027 | APT0003 | INVIOSYSTEM | APT000971 + APT000945 | Int.EXP Reverse + Multicollo | NEGATIVO (KO) | Reverse Internazionale (APT000971) compatibile SOLO con A Domicilio. Multicollo KO. |
| TC028 | APT0001 | STAMPAMASSIVA | APT000972 | Nazionale + Oneri Doganali | NEGATIVO (KO) | Oneri Doganali è accessorio internazionale: non applicabile a prodotto Nazionale. KO. |

### CASI DI BORDO / REVERSE / SAME DAY / INSTANT

| # | PRODOTTO | CANALE | SERVIZI COMBINATI | SCENARIO | ESITO ATTESO | NOTE / VERIFICA |
| --- | --- | --- | --- | --- | --- | --- |
| TC029 | APT0001 | INVIOSYSTEM | APT000928 + APT000919 | Reverse a Domicilio + Copertura Full | POSITIVO | Unica combinazione valida del Reverse (APT000928): solo con Copertura Full (APT000919). |
| TC030 | APT0001 | INVIOSYSTEM | APT000929 + APT000945 | A&amp;R + Multicollo (solo Andata) | POSITIVO (con vincolo) | Per A&amp;R il Multicollo si applica SOLO alla spedizione di Andata (nota riga A29). Verificare gestione. |
| TC031 | APT0001 | INVIOEASY | APT000996 + APT000946 | Same Day 4 Ore + A Domicilio | POSITIVO | Same Day (APT000996) compatibile con A Domicilio, Contrassegno, Copertura Full, Multicollo. |
| TC032 | APT0001 | INVIOSYSTEM | APT001003 + APT000919 | Instant 1 Ora + Copertura Full | POSITIVO | Instant (APT001003) compatibile con Copertura Full. Verificare fascia oraria Instant. |
| TC033 | APT0001 | INVIOSYSTEM | APT000988 + APT000930 | Scheduled Anytime + Ritorno Mittente | NEGATIVO (KO) | Ritorno Mittente (APT000930) esclude Scheduled (APT000982-995). Anytime=APT000988 → KO. |
| TC034 | APT0001 | INVIOSYSTEM | APT000914 + APT000905 | Consegna al Vicino + TD Ore 9 | NEGATIVO (KO) | Consegna al Vicino (APT000914) = 'Tutti tranne Time Definite singoli'. Con TD Ore 9 → KO. |
| TC035 | APT000904 | INVIOFILE | APT000971 + APT000946 | Int.STD Reverse + A Domicilio | POSITIVO | Reverse Internazionale (APT000971) compatibile con A Domicilio (riga A107). Caso valido. |

### VALIDAZIONE PARAMETRI OBBLIGATORI

| # | PRODOTTO | CANALE | SERVIZI COMBINATI | SCENARIO | ESITO ATTESO | NOTE / VERIFICA |
| --- | --- | --- | --- | --- | --- | --- |
| TC036 | APT0001 | INVIOSYSTEM | APT000918 (paymentMode mancante) | Contrassegno senza paymentMode | NEGATIVO (KO) | paymentMode obbligatorio (CON/ACM/ABM). Se assente → errore di validazione atteso. |
| TC037 | APT0001 | INVIOSYSTEM | APT000909 (days non 6 cifre) | Programmata con days errato | NEGATIVO (KO) | days deve essere 6 cifre (es. G02100). Formato errato → errore validazione atteso. |
| TC038 | APT0001 | INVIOSYSTEM | APT000919 (amount mancante) | Copertura Full senza importo | NEGATIVO (KO) | amount obbligatorio per Copertura Full. Se assente → errore di validazione atteso. |
| TC039 | APT0001 | INVIOSYSTEM | APT000912 (days formato G+GGMM+M/P errato) | Giorno/Orario formato errato | NEGATIVO (KO) | days formato G+GGMM+M/P (es. G0910M). Formato errato → errore validazione atteso. |
| TC040 | APT0003 | INVIOSYSTEM | APT000955 + APT000956 | Int.EXP doppia Copertura Full | NEGATIVO (KO) | Copertura 1.500€ e 50.000€ mutuamente esclusive (una sola fascia). Deve essere respinto. |

## LEGENDA ESITO ATTESO:

| Esito atteso | Significato |
| --- | --- |
| POSITIVO | Combinazione valida: la LDV deve essere accettata |
| NEGATIVO (KO) | Combinazione incompatibile / parametri errati: deve essere RESPINTA con errore |
| DA CONFERMARE | Ambiguità nella matrice fonte (es. 'V' vs 'X'): validare con Poste prima del test |
| DA VERIFICARE | Funzionalità/canale da confermare a valle del flusso |