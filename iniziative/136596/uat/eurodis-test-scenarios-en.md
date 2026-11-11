# SDA – EURODIS Autoproduttore: test data request

**Status**: DRAFT for review before sending · **Version**: 0.3 · **Date**: 2026-11-11
**Audience**: EURODIS (test data generation on the `receive-pan` TEST environment)
**Scope**: shipments returned by `GET /shipments/v1` (`GetShipmentResponse2`)

## 1. Purpose

SDA is going to run end-to-end acceptance tests on the integration with the EURODIS `receive-pan` API.
We need EURODIS to generate, on the TEST environment, a set of shipments covering the scenarios below.
Each scenario is **one shipment** (unless stated otherwise) that SDA will download with
`GET /shipments/v1`, so we would like to receive them **in the order of the table**, or at least be told
which `edReference` belongs to which scenario.

All data must be **fictitious**: no real names, addresses, phone numbers, e-mail addresses or IBANs.

## 2. Rules valid for all scenarios

| Field | Requirement |
|---|---|
| `edReference` | Unique, integer, no decimals. Please send us the list *scenario → edReference*. |
| `consigneeAddress` | **Always present** and complete (`companyName`, `street`, `streetNumber`, `city`, `zipcode`, `countryCode` = `IT`). The TEST payloads we have seen have it `null`. |
| `shipperAddress` | Present and complete. Country can be foreign (see S07). |
| `collis[].deliveryPartnerBarcode` | **Filled** for every parcel (the SDA waybill number). Syntax and range of the waybill numbers are still to be defined between Poste and EURODIS; once agreed, EURODIS is the owner of the syntax. Until then, any placeholder value is fine for the tests that do not depend on it. |
| `collis[].europlateBarcode` | 24 characters, unique per parcel, unless the scenario says otherwise. |
| `collis[].consignorsColloBarcode` | Free value; SDA does not use it. |
| `collis[].weightOfUnit` | In kg, greater than 0, unless the scenario says otherwise. |
| `numberOfHandlingUnits` | Equal to the number of elements in `collis`, unless the scenario says otherwise. |
| `entranceTimestamp` | Filled, unless the scenario says otherwise. |
| `deliveryService.deliveryType` | `S`, unless the scenario says otherwise. |
| `shipmentTypeIndicator`, `lineHaulIndicator` | `N` / `N`, unless the scenario says otherwise. |
| `customsService`, `hazardousADRServices`, `hazardousCollis` | Empty, except in section G. |
| Not used in these tests | Insurance, return shipments. Please leave them empty. |

## 3. Scenarios

### A – Base shipments (no additional service)

| ID | Scenario | What the payload must contain | Qty |
|---|---|---|---|
| S01 | Standard single parcel | 1 parcel, no `deliveryService`, no `cashOnDeliveryService`. | 1 |
| S02 | Multi-parcel | `numberOfHandlingUnits` = 3, 3 elements in `collis`, each with its own `deliveryPartnerBarcode`, `europlateBarcode`, `weightOfUnit`. | 1 |
| S03 | Multi-parcel with decimal weights | 3 parcels with `weightOfUnit` 1.5, 2.25 and 0.4 kg; `shipmentWeight` = 4.15. | 1 |
| S04 | Missing contacts | `contactTelephone`, `contactSMS`, `contactEMail` empty or absent on both shipper and consignee. | 1 |
| S05 | Values longer than usual | `streetNumber` of 10+ characters, `city` of 40+ characters, `companyName` of 40+ characters (within the API limits). | 1 |
| S06 | Parcel weight at zero | 1 parcel with `weightOfUnit` = 0 and no dimensions. | 1 |
| S07 | Foreign shipper | `shipperAddress.countryCode` other than `IT` (e.g. `AT`, `DE`); consignee in Italy. | 1 |
| S08 | Consignee pre-advice | `consigneePreAdvice` with `smsPreAdvice` / `eMailPreAdvice` / `telephonePreAdvice` set to true and the matching contact filled. | 1 |
| S09 | Shipment type indicator | One shipment each with `shipmentTypeIndicator` = `C` (B to C) and `X` (AUX-Pan); everything else as S01. | 2 |

### B – Delivery services (one per shipment)

| ID | Scenario | What the payload must contain | Qty |
|---|---|---|---|
| S10 | Saturday delivery | `deliveryService.deliveryService` = `6`. | 1 |
| S11 | Evening delivery | `deliveryService` = `E`. | 1 |
| S12 | Delivery before 12:00 | `deliveryService` = `M`. | 1 |
| S13 | Delivery before 10:00 | `deliveryService` = `F`. | 1 |
| S14 | Delivery by appointment | `deliveryService` = `B`, `deliveryBookInRequired` = true, consignee phone/SMS filled. | 1 |
| S15 | Delivery window | `deliveryService` = `W` with `deliveryDateWindowStart` and `deliveryTimeWindowStart`. *(to be confirmed, see section 5)* | 1 |
| S16 | Afternoon delivery | `deliveryService` = `A`. | 1 |
| S17 | Other values | One shipment each with `deliveryService` = `D`, `7`, `T`. *(to be confirmed, see section 5)* | 3 |
| S18 | Signature handling | One shipment each with `deliveryType` = `S`, `N`, `D`, no other service. | 3 |
| S19 | Pick-up point | `deliveryService` = `Z` with `consigneeAddress.pudoID` filled. *(to be confirmed, see section 5)* | 1 |

### C – Cash on delivery

| ID | Scenario | What the payload must contain | Qty |
|---|---|---|---|
| S20 | COD, cash | `cashOnDeliveryService`: `amount` 123.45, `currency` `EUR`, `identifierForCODCollection` = 3, `iban` and `accountHolder` filled. | 1 |
| S21 | COD, cheque | `identifierForCODCollection` = 5, `amount` 250.00, `currency` `EUR`. | 1 |
| S22 | COD with amount 0 | `amount` = 0, `currency` `EUR`. | 1 |
| S23 | COD in another currency | `currency` = `CHF`, `amount` 100.00. *(only if EURODIS can generate it)* | 1 |

### D – Combinations

| ID | Scenario | What the payload must contain | Qty |
|---|---|---|---|
| S30 | Delivery before 12:00 + COD | `deliveryService` = `M` and `cashOnDeliveryService` (cash). | 1 |
| S31 | Delivery before 10:00 + COD | `deliveryService` = `F` and `cashOnDeliveryService` (cash). | 1 |
| S32 | Appointment + COD | `deliveryService` = `B` and `cashOnDeliveryService` (cash). | 1 |
| S33 | Delivery before 12:00 + multi-parcel | `deliveryService` = `M`, 3 parcels. | 1 |
| S34 | COD + multi-parcel | `cashOnDeliveryService` (cash), 3 parcels. | 1 |
| S35 | Delivery before 10:00 + COD + multi-parcel | `deliveryService` = `F`, `cashOnDeliveryService` (cash), 3 parcels. | 1 |
| S36 | Appointment + multi-parcel | `deliveryService` = `B`, 3 parcels. | 1 |
| S37 | Pick-up point + COD | `deliveryService` = `Z`, `pudoID` filled, `cashOnDeliveryService`. *(to be confirmed, see section 5)* | 1 |

### E – Barcode and date variants

| ID | Scenario | What the payload must contain | Qty |
|---|---|---|---|
| S40 | Empty `consignorsColloBarcode` | 1 parcel with `consignorsColloBarcode` empty. | 1 |
| S41 | `europlateBarcode` empty | 1 parcel with `europlateBarcode` empty. | 1 |
| S42 | `europlateBarcode` = `"0"` | 1 parcel with `europlateBarcode` = `"0"` (neighbourhood business). | 1 |
| S43 | Multi-parcel, first europlate missing | 3 parcels: first with `europlateBarcode` empty, second and third filled. | 1 |
| S44 | Multi-parcel, no consignor/europlate barcodes | 3 parcels with both `consignorsColloBarcode` and `europlateBarcode` empty. | 1 |
| S45 | No `entranceTimestamp` | `entranceTimestamp` absent, `clearanceTimestamp` filled. | 1 |

### G – Customs and hazardous goods (ADR)

| ID | Scenario | What the payload must contain | Qty |
|---|---|---|---|
| S60 | Customs data | `customsService`: `commercialValueOfGoods` 500.00, `currency` `EUR`, `dutyCode`, `sign`, `number`, `descriptionOfGoods` filled. Shipper outside the EU (e.g. `CH`), consignee in Italy. | 1 |
| S61 | Customs data, other currency | As S60 with `currency` = `CHF`. | 1 |
| S62 | Hazardous goods, single parcel | `hazardousADRServices` with one element (`unNumber`, `packingGroup`, `transportCategory`, `tunnelLimitationCode`, `adrGrossWeight`, `materialDescription`, `technicalName`, `identifierMassOrVolume`); `hazardousCollis` with one element. | 1 |
| S63 | Hazardous goods, multi-parcel | 3 parcels; `hazardousADRServices` with two elements; `hazardousCollis` with three elements. | 1 |
| S64 | Hazardous goods + customs | S62 data plus `customsService` as in S60. | 1 |
| S65 | Hazardous goods + COD | S62 data plus `cashOnDeliveryService` (cash). | 1 |

### F – Anomalous data (optional)

SDA can simulate these cases with its own mock of the API. Please generate them **only if** the TEST
environment allows it; otherwise ignore this section.

| ID | Scenario | What the payload must contain |
|---|---|---|
| S50 | Consignee without city | `consigneeAddress.city` empty. |
| S51 | Consignee without zip code | `consigneeAddress.zipcode` empty. |
| S52 | No consignee | `consigneeAddress` = `null`. |
| S53 | No `deliveryPartnerBarcode` | `deliveryPartnerBarcode` absent on the parcel. |
| S54 | Parcel count mismatch | `numberOfHandlingUnits` = 3 with 2 elements in `collis`. |
| S55 | No shipper | `shipperAddress` = `null`. |
| S56 | Shipper with an empty field | One shipment per field left empty in `shipperAddress`: `companyName`, `zipcode`, `city`, `street`, `countryCode` (5 shipments). |
| S57 | Consignee with an empty field | One shipment per field left empty in `consigneeAddress`: `companyName`, `street`, `countryCode` (3 shipments). |
| S58 | Consignee values too long | One shipment each with `companyName` of 45 characters, `streetNumber` of 8 characters, `city` of 40 characters (3 shipments). |
| S59 | Parcel extremes | One shipment each with `weightOfUnit` = 10000 (kg), `length` = 1000 (cm), `collis` = `null` (3 shipments). |

## 4. Deliverable we ask from EURODIS

1. The shipments above available on `GET /shipments/v1` of the TEST environment (or the agreed alternative).
2. The table *scenario ID → `edReference`* (and, for multi-parcel scenarios, the barcodes of each parcel).
3. The expected date when the data will be available.

## 5. Open points to be agreed

| # | Topic |
|---|---|
| 1 | `deliveryService` `W`, `D`, `7`, `T`: are these values really sent to SDA in production, and with which meaning? (S15, S17) |
| 2 | Delivery to a pick-up point (`Z` + `pudoID`): is it in the scope of the first release? Which field carries the name of the pick-up point? (S19, S37) |
| 3 | Customs and hazardous goods (section G): which of the fields are always filled in production for shipments to Italy, and which values are admitted (e.g. `packingGroup`, `transportCategory`)? |
| 4 | Repeated `GET /shipments/v1` on TEST returns always the same data: can the set above be consumed once and then re-generated on request (for repetitions)? |
| 5 | Re-read of a shipment (`GET /shipment/{edReference}/v1`): we will use it in the recovery tests, please confirm it works on TEST for the shipments above. |
| 6 | Time zone of the timestamps: same as the existing file exchange. Please confirm. |
