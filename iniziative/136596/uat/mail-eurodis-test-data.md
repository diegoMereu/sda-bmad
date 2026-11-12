**Subject: SDA – receive-pan TEST: shipments requested for acceptance tests**

Hi,

in order to run our acceptance tests on `GET /shipments/v1`, could you generate on the TEST environment one shipment for each scenario below? Please send us the mapping *scenario ID → `edReference`* (and the parcel barcodes for multi-parcel scenarios).

Common rules: fictitious data only; `consigneeAddress` always complete with `countryCode` = IT; `shipperAddress` complete; `deliveryPartnerBarcode` filled on every parcel; `numberOfHandlingUnits` = number of `collis`; `entranceTimestamp` filled; `deliveryType` = `S`; no hazardous goods data (`hazardousADRServices`, `hazardousCollis` empty); unless the scenario says otherwise.

| ID | Scenario | What the payload must contain | Qty |
|---|---|---|---|
| **A – Base** | | | |
| S01 | Standard, single parcel | 1 parcel, no `deliveryService`, no `cashOnDeliveryService` | 1 |
| S02 | Multi-parcel | 3 parcels, each with its own barcodes and weight | 1 |
| S03 | Multi-parcel, decimal weights | `weightOfUnit` 1.5 / 2.25 / 0.4 kg | 1 |
| S04 | No contacts | phone, SMS and e-mail empty on shipper and consignee | 1 |
| S05 | Long values | `streetNumber` 10+ chars, `city` and `companyName` 40+ chars (within API limits) | 1 |
| S06 | Zero weight | `weightOfUnit` = 0 | 1 |
| S07 | Foreign shipper | `shipperAddress.countryCode` ≠ IT (e.g. AT, DE) | 1 |
| S08 | Consignee pre-advice | `consigneePreAdvice` flags true with matching contact | 1 |
| S09 | Shipment type | `shipmentTypeIndicator` = `C`, then `X` | 2 |
| **B – Delivery services** | | | |
| S10 | Saturday | `deliveryService` = `6` | 1 |
| S11 | Evening | `E` | 1 |
| S12 | Before 12:00 | `M` | 1 |
| S13 | Before 10:00 | `F` | 1 |
| S14 | By appointment | `B`, `deliveryBookInRequired` = true, consignee phone filled | 1 |
| S15 | Delivery window (*to be confirmed*) | `W` with date and time window | 1 |
| S16 | Afternoon | `A` | 1 |
| S17 | Other values (*to be confirmed*) | `D`, `7`, `T` | 3 |
| S18 | Signature handling | `deliveryType` = `S`, `N`, `D` | 3 |
| S19 | Pick-up point (*to be confirmed*) | `Z` + `consigneeAddress.pudoID` | 1 |
| **C – Cash on delivery** | | | |
| S20 | COD, cash | `amount` 123.45 EUR, `identifierForCODCollection` = 3, IBAN and account holder | 1 |
| S21 | COD, cheque | `identifierForCODCollection` = 5, 250.00 EUR | 1 |
| S22 | COD amount 0 | `amount` = 0 EUR | 1 |
| S23 | COD other currency (*if possible*) | `currency` = CHF | 1 |
| **D – Combinations** | | | |
| S30 | Before 12:00 + COD | `M` + COD | 1 |
| S31 | Before 10:00 + COD | `F` + COD | 1 |
| S32 | Appointment + COD | `B` + COD | 1 |
| S33 | Before 12:00 + multi-parcel | `M`, 3 parcels | 1 |
| S34 | COD + multi-parcel | COD, 3 parcels | 1 |
| S35 | Before 10:00 + COD + multi-parcel | `F`, COD, 3 parcels | 1 |
| S36 | Appointment + multi-parcel | `B`, 3 parcels | 1 |
| S37 | Pick-up point + COD (*to be confirmed*) | `Z`, `pudoID`, COD | 1 |
| **E – Barcode and date variants** | | | |
| S40 | Empty consignor barcode | `consignorsColloBarcode` empty | 1 |
| S41 | Empty europlate | `europlateBarcode` empty | 1 |
| S42 | Europlate "0" | `europlateBarcode` = `"0"` | 1 |
| S43 | Multi-parcel, first europlate missing | 3 parcels, first europlate empty | 1 |
| S44 | Multi-parcel, no barcodes | 3 parcels, consignor and europlate barcodes empty | 1 |
| S45 | No `entranceTimestamp` | `entranceTimestamp` absent, `clearanceTimestamp` filled | 1 |
| **G – Customs** | | | |
| S60 | Customs data | `customsService` filled, 500.00 EUR, shipper outside the EU, consignee in Italy | 1 |
| S61 | Customs, other currency | as S60 with CHF | 1 |

**Total: 44 shipments.**

**Optional – anomalous data** (we can simulate them on our side; please generate only if the TEST environment allows it):

| ID | Scenario | What the payload must contain | Qty |
|---|---|---|---|
| S50 | Consignee without city | `consigneeAddress.city` empty | 1 |
| S51 | Consignee without zip code | `consigneeAddress.zipcode` empty | 1 |
| S52 | No consignee | `consigneeAddress` = `null` | 1 |
| S53 | No parcel barcode | `deliveryPartnerBarcode` absent | 1 |
| S54 | Parcel count mismatch | `numberOfHandlingUnits` = 3 with 2 `collis` | 1 |
| S55 | No shipper | `shipperAddress` = `null` | 1 |
| S56 | Shipper, one empty field | `companyName`, `zipcode`, `city`, `street`, `countryCode` (one shipment each) | 5 |
| S57 | Consignee, one empty field | `companyName`, `street`, `countryCode` (one shipment each) | 3 |
| S58 | Consignee, values too long | `companyName` 45 chars, `streetNumber` 8 chars, `city` 40 chars (one shipment each) | 3 |
| S59 | Parcel extremes | `weightOfUnit` = 10000 kg, `length` = 1000 cm, `collis` = `null` (one shipment each) | 3 |

**Total optional: 20 shipments.**

**Questions for EURODIS**

1. Are `deliveryService` `W`, `D`, `7`, `T` sent in production, and with which meaning? (S15, S17)
2. Is delivery to a pick-up point (`Z` + `pudoID`) in scope, and which field carries the name of the point? (S19, S37)
3. For customs (section G): which fields are always filled for shipments to Italy?
4. `GET /shipments/v1` on TEST always returns the same data: can the set above be consumed once and regenerated on request?
5. Please confirm that the re-read `GET /shipment/{edReference}/v1` works on TEST for these shipments.
6. Please confirm that the timestamps use the same time zone as the existing file exchange.

Best regards
