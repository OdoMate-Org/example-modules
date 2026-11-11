# Benutzerhandbuch: Product Sample Requests (Musteranfragen)

> Außendienstmitarbeiter fordern Produktmuster für Kunden an, Manager genehmigen und versenden sie, und Odoo erinnert an das Nachfassen und misst, wie viele Muster zu Aufträgen werden.

---

## Inhaltsverzeichnis

1. [Was macht dieses Modul](#1-was-macht-dieses-modul)
2. [Wo finde ich das Modul in Odoo](#2-wo-finde-ich-das-modul-in-odoo)
3. [Ersteinrichtung](#3-ersteinrichtung)
4. [Eine Musteranfrage anlegen](#4-eine-musteranfrage-anlegen)
5. [Hauptablauf](#5-hauptablauf)
6. [Erinnerung und Ergebnis des Nachfassens](#6-erinnerung-und-ergebnis-des-nachfassens)
7. [Berichte und Konversionsrate](#7-berichte-und-konversionsrate)
8. [Zugriffsrollen](#8-zugriffsrollen)
9. [Einschränkungen](#9-einschränkungen)

---

## 1. Was macht dieses Modul

Das Modul ersetzt E-Mails und Tabellen, mit denen Muster bisher abgestimmt wurden. Ein Vertriebsmitarbeiter legt einen **Sample Request** (`sample.request`, Musteranfrage) für einen Kunden mit einem oder mehreren Produkten und Mengen an und reicht ihn ein. Ein Vertriebsmanager genehmigt oder lehnt ihn ab. Sobald die Muster verschickt sind, klickt der Manager auf **Mark as Sent** (Als versendet markieren), und Odoo plant für den Vertriebsmitarbeiter eine To-Do-Aktivität 14 Tage später. Der Mitarbeiter erfasst, ob der Kunde bestellt hat, und das Menü Reporting zeigt die Konversionsrate Muster → Auftrag pro Vertriebsmitarbeiter.

| Funktion | Details |
|---|---|
| Musteranfragen mit Produktpositionen | Customer (Kunde), Sales Rep (Vertriebsmitarbeiter), Reason (Grund), Reason Details (Details zum Grund) und Reiter **Products** (Produkte: Product, Quantity). Jede Anfrage erhält eine Nummer wie `SR/2026/0001`. |
| Genehmigungsablauf | Draft → Submitted → Approved → Sent → Followed Up sowie Rejected und Cancelled. Jede Statusänderung wird im Chatter protokolliert. |
| Pflicht-Ablehnungsgrund | Die Schaltfläche **Reject** (Ablehnen) öffnet einen Dialog, in dem ein Grund Pflicht ist. Der Grund wird auf der Anfrage angezeigt. |
| Automatische Nachfass-Aufgabe | **Mark as Sent** erstellt für den Vertriebsmitarbeiter eine To-Do-Aktivität „Follow up on sample request“, fällig am Sent Date + 14 Tage. |
| Ergebniserfassung | Dialog **Log Outcome** (Ergebnis erfassen): Ordered / Still Thinking / Not Interested, optional mit Verknüpfung eines Sales Order (Verkaufsauftrags). |
| Konversionsbericht | Pivot- und Diagrammansicht nach Sales Rep und Status mit den Kennzahlen **Converted** und **Conversion Rate (%)**. |
| Sichtbarkeit | Vertriebsmitarbeiter sehen nur ihre eigenen Anfragen, Manager sehen alle. |

---

## 2. Wo finde ich das Modul in Odoo

Nach der Installation erscheint im Hauptmenü die App **Sample Requests** mit diesen Menüpunkten:

- **My Requests** (Meine Anfragen): Ihre eigenen Anfragen (Filter „My Requests“ ist standardmäßig aktiv). Öffnet eine Kanban-Ansicht, gruppiert nach Status. Liste, Formular, Pivot und Diagramm sind ebenfalls verfügbar.
- **Approvals** (Genehmigungen, nur Manager): alle Anfragen im Status **Submitted**, die auf eine Entscheidung warten. Neue Anfragen lassen sich hier nicht anlegen.
- **All Requests** (Alle Anfragen, nur Manager): alle Anfragen aller Vertriebsmitarbeiter.
- **Reporting** (Berichte): Pivot und Diagramm *Sample Request Analysis*, bereits mit aktivem Filter **Sent or Followed Up** geöffnet.

---

## 3. Ersteinrichtung

Außer den Benutzerrechten muss nichts eingerichtet werden. Das Modul hat keine Einstellungsseite.

1. Öffnen Sie **Settings → Users & Companies → Users** (Einstellungen → Benutzer & Unternehmen → Benutzer) und wählen Sie einen Benutzer.
2. Setzen Sie im Bereich Zugriffsrechte **Sample Request** auf **User** (Vertriebsmitarbeiter) oder **Manager** (wer Muster genehmigt und versendet).
3. Speichern. Die App **Sample Requests** erscheint im Menü dieses Benutzers.

| Wer | Zuzuweisende Gruppe |
|---|---|
| Vertriebsmitarbeiter, der Muster anfordert | `Sample Request / User` |
| Vertriebsmanager oder Logistikverantwortlicher, der genehmigt und versendet | `Sample Request / Manager` |

> Tipp: Das Administratorkonto erhält **Sample Request / Manager** bei der Installation automatisch, die App ist also sofort sichtbar.
>
> Tipp: `Sample Request / User` gewährt außerdem **Sales / User: Own Documents Only** (Verkauf / Benutzer: Nur eigene Dokumente), damit Vertriebsmitarbeiter beim Erfassen des Ergebnisses einen Verkaufsauftrag auswählen können.

---

## 4. Eine Musteranfrage anlegen

**Pfad:** `Sample Requests` → `My Requests` → `New` (Neu)

| Feld | Beschreibung |
|---|---|
| **Reference** (Nummer) | Wird beim Speichern automatisch vergeben (z. B. `SR/2026/0007`). Schreibgeschützt. |
| **Customer** (Kunde) | Pflichtfeld. Unternehmen oder Kontakt, das bzw. der die Muster erhält. |
| **Sales Rep** (Vertriebsmitarbeiter) | Pflichtfeld. Standardmäßig Sie selbst. Nur ein Manager kann es ändern, und nur solange die Anfrage im Status Draft ist. |
| **Reason** (Grund) | Optional: Deal in Progress (laufendes Geschäft), New Prospect (neuer Interessent), Existing Customer (Bestandskunde), Trade Show (Messe), Other (Sonstiges). |
| **Reason Details** (Details zum Grund) | Freitext für den Genehmiger, z. B. „Pilotcharge für die Q3-Ausschreibung, 2 Farben“. |
| Reiter **Products** (Produkte) | Eine Zeile pro Produkt: **Product** und **Quantity**. Die Menge muss größer als null sein. |

**Statusablauf:**

```
Draft ──Submit──▶ Submitted ──Approve──▶ Approved ──Mark as Sent──▶ Sent ──Log Outcome──▶ Followed Up
  │                  │
  │                  ├──Reject (Grund erforderlich)──▶ Rejected
  │                  │
  └──Cancel──────────┴──Cancel──▶ Cancelled
```

Draft = Entwurf, Submitted = Eingereicht, Approved = Genehmigt, Rejected = Abgelehnt, Sent = Versendet, Followed Up = Nachgefasst, Cancelled = Storniert.

> Achtung: Rejected und Cancelled sind Endzustände. Für einen neuen Versuch öffnen Sie die Anfrage und wählen **Actions → Duplicate** (Aktion → Duplizieren). Die Kopie beginnt als neuer Entwurf mit demselben Kunden, Grund und denselben Produktzeilen.

---

## 5. Hauptablauf

### Ablauf 1: Vertriebsmitarbeiter fordert Muster an

**Schritt 1: Anfrage ausfüllen.** Wählen Sie den **Customer**, optional **Reason** und **Reason Details**, und fügen Sie im Reiter **Products** mindestens eine Zeile hinzu.

**Schritt 2: Auf Submit (Einreichen) klicken.**
- Ist der Reiter **Products** leer, stoppt Odoo mit „Add at least one product to … before submitting it.“ (Fügen Sie vor dem Einreichen mindestens ein Produkt hinzu).
- Der Status wechselt zu **Submitted**, und die Anfrage erscheint bei allen Managern unter **Approvals**.

> Achtung: Nach dem Einreichen können Sie Kunde, Grund, Vertriebsmitarbeiter und Produkte nicht mehr ändern. Ist etwas falsch, klicken Sie auf **Cancel** (Stornieren; möglich in Draft und Submitted), duplizieren dann die Anfrage und korrigieren die Kopie.

### Ablauf 2: Manager entscheidet

Öffnen Sie **Sample Requests → Approvals** und dann die Anfrage.

- **Approve** (Genehmigen): Der Status wechselt zu **Approved**, und **Decided By** (Entschieden von) wird auf Sie gesetzt.
- **Reject** (Ablehnen): Ein Dialog verlangt einen **Rejection Reason** (Ablehnungsgrund, Pflichtfeld). Klicken Sie im Dialog auf **Reject**. Der Status wechselt zu **Rejected**, ein rotes Band „Rejected“ erscheint, und Grund sowie **Decided By** werden im Formular angezeigt.

Jeder Benutzer mit **Sample Request / Manager** kann über jede Anfrage entscheiden. Die Genehmigung ist nicht an den direkten Vorgesetzten des Vertriebsmitarbeiters gebunden.

### Ablauf 3: Manager versendet die Muster

Wenn das Paket unterwegs ist, öffnen Sie die genehmigte Anfrage und klicken auf **Mark as Sent**:

- **Sent Date** (Versanddatum) wird auf heute gesetzt. Hat ein Manager bereits ein Datum eingetragen, bleibt es erhalten.
- Der Status wechselt zu **Sent**.
- Für den Vertriebsmitarbeiter wird eine To-Do-Aktivität geplant (siehe [Abschnitt 6](#6-erinnerung-und-ergebnis-des-nachfassens)).

Solange die Anfrage im Status **Sent** ist, kann ein Manager das **Sent Date** im Formular korrigieren. Diese Änderung verschiebt die bereits erstellte Aktivität **nicht**. Passen Sie deren Fälligkeitsdatum bei Bedarf manuell an.

### Löschen

Nur Anfragen im Status **Draft** oder **Cancelled** können gelöscht werden. Bei allen anderen erscheint „Only draft or cancelled sample requests can be deleted.“ Stornieren Sie die Anfrage stattdessen, damit der Verlauf erhalten bleibt.

---

## 6. Erinnerung und Ergebnis des Nachfassens

### Die Erinnerung

**Mark as Sent** erstellt genau eine Aktivität auf der Anfrage:

| Eigenschaft | Wert |
|---|---|
| Typ | To-Do |
| Zusammenfassung | Follow up on sample request |
| Zugewiesen an | **Sales Rep** der Anfrage |
| Fälligkeit | **Sent Date** + 14 Tage |

Beispiel: Sent Date ist der **3. März 2026**, die Aktivität ist also am **17. März 2026** fällig. Der Vertriebsmitarbeiter sieht sie im Aktivitätenmenü (Uhrsymbol) und im Chatter der Anfrage.

### Ergebnis erfassen

Bei einer Anfrage im Status **Sent** klickt der zuständige Vertriebsmitarbeiter (oder ein beliebiger Manager) auf **Log Outcome**. Der Dialog *Log Follow-up Outcome* öffnet sich:

| Feld | Beschreibung |
|---|---|
| **Outcome** (Ergebnis) | Pflichtfeld: **Ordered** (Bestellt), **Still Thinking** (Überlegt noch) oder **Not Interested** (Kein Interesse). |
| **Sales Order** (Verkaufsauftrag) | Nur bei **Ordered** sichtbar, optional. Auswählbar sind nur Aufträge, deren Kunde der Kunde der Anfrage oder einer seiner Kontakte ist. Ein neuer Auftrag kann hier nicht angelegt werden. |

Klicken Sie auf **Log Outcome**. Odoo:
- setzt den Status auf **Followed Up** und speichert das **Follow-up Outcome**,
- markiert die Nachfass-Aktivität als erledigt, mit dem Feedback „Outcome: Ordered“ (bzw. dem gewählten Ergebnis),
- zeigt ein grünes Band „Ordered“, wenn das Ergebnis Ordered ist.

> Tipp: Ist der Auftrag noch nicht in Odoo, erfassen Sie **Ordered** ohne Verkaufsauftrag. Öffnen Sie die Anfrage später und tragen Sie **Sales Order** im Formular nach. Bei Anfragen mit Ergebnis Ordered bleibt das Feld bearbeitbar.
>
> Hinweis: **Still Thinking** schließt die Anfrage und ihre Aktivität ebenfalls ab. Eine zweite Erinnerung wird nicht geplant. Wenn Sie eine weitere Erinnerung möchten, planen Sie selbst eine neue Aktivität im Chatter.

---

## 7. Berichte und Konversionsrate

**Pfad:** `Sample Requests` → `Reporting`

Die Pivot-Tabelle *Sample Request Analysis* öffnet sich mit:
- **Zeilen:** Sales Rep
- **Spalten:** Status
- **Kennzahlen:** **Count** (Anzahl), **Converted** (Konvertiert), **Conversion Rate (%)** (Konversionsrate)
- **Filter:** **Sent or Followed Up** (bereits aktiv)

Jede Anfrage speichert zwei Werte:

| Kennzahl | Wert pro Anfrage | Aggregation in der Pivot-Tabelle |
|---|---|---|
| **Converted** | 1, wenn Followed Up mit Ergebnis Ordered, sonst 0 | Summe |
| **Conversion Rate (%)** | 100, wenn Followed Up mit Ergebnis Ordered, sonst 0 | Durchschnitt |

Mit dem standardmäßig aktiven Filter gilt also:

```
Conversion Rate = bestellte Anfragen ÷ (versendete + nachgefasste Anfragen) × 100
```

**Rechenbeispiel.** Anna hat 10 Anfragen im Status Sent oder Followed Up: 2 sind noch **Sent**, 8 sind **Followed Up** (3 Ordered, 4 Still Thinking, 1 Not Interested).

| Sales Rep | Count | Converted | Conversion Rate (%) |
|---|---|---|---|
| Anna | 10 | 3 | (3 × 100 + 7 × 0) ÷ 10 = **30,00** |

> Achtung: Entfernen Sie den Filter **Sent or Followed Up**, zählen Entwürfe, abgelehnte und stornierte Anfragen als 0 und drücken die Rate. Im Beispiel ergäben 5 zusätzliche Entwürfe und 1 abgelehnte Anfrage 3 ÷ 16 = **18,75 %**. Lassen Sie den Filter beim Ablesen der Rate aktiv oder betrachten Sie nur die Spalten **Sent** und **Followed Up**.

Weitere nützliche Filter und Gruppierungen in der Suche: **Pending Approval** (Genehmigung ausstehend), **Awaiting Follow-up** (Nachfassen ausstehend), **Converted to Order** (In Auftrag umgewandelt), **Sent Date** (nach Zeitraum) sowie Gruppierung nach **Outcome**, **Reason** oder **Customer**. Die Diagrammansicht zeigt ein gestapeltes Balkendiagramm der Anfragen nach Sales Rep und Status.

---

## 8. Zugriffsrollen

| Aktion | Sample Request / User (Vertrieb) | Sample Request / Manager |
|---|---|---|
| Anfragen sehen | Nur eigene (Sales Rep = ich) | Alle |
| Anfrage anlegen | Ja, für sich selbst | Ja, für jeden Vertriebsmitarbeiter |
| Anfrage / Produkte bearbeiten | Nur im Status Draft | Ja, in jedem Status (nach Draft sperrt das Formular die meisten Felder) |
| Submit | Eigene Entwürfe | Alle Entwürfe |
| Cancel (Draft / Submitted) | Eigene | Alle |
| Approve / Reject / Mark as Sent | Nein | Ja |
| Sent Date im Status Sent ändern | Nein | Ja |
| Log Outcome (im Status Sent) | Eigene | Alle |
| Sales Order bei Ordered-Anfrage verknüpfen | Eigene | Alle |
| Löschen | Eigene Draft / Cancelled | Alle Draft / Cancelled |
| Menüs | My Requests, Reporting | My Requests, Approvals, All Requests, Reporting |

`Sample Request / Manager` umfasst alle Rechte von `Sample Request / User`. `Sample Request / User` umfasst **Sales / User: Own Documents Only**. Im Reporting sieht ein Vertriebsmitarbeiter nur Kennzahlen zu seinen eigenen Anfragen.

Rollen zuweisen: **Settings → Users & Companies → Users** → Benutzer wählen → Zugriffsfeld **Sample Request**.

---

## 9. Einschränkungen

| Thema | Einschränkung |
|---|---|
| Mehrere Unternehmen | Anfragen haben kein Feld Company und keine Unternehmens-Datensatzregel. In einer Datenbank mit mehreren Unternehmen sehen Manager die Anfragen aller Unternehmen. Der Nummernkreis ist für alle Unternehmen gemeinsam. |
| Konversionsrate | Nur mit aktivem Filter **Sent or Followed Up** aussagekräftig (im Reporting standardmäßig aktiv). Ohne ihn zählen Entwürfe, abgelehnte und stornierte Anfragen als 0. |
| Verknüpfter Auftrag | Wird nicht gegen die bemusterten Produkte, Mengen oder Beträge geprüft. Jeder Auftrag des Kunden oder seiner Kontakte kann verknüpft werden, auch ein Angebotsentwurf oder ein stornierter Auftrag. |
| Auftragsauswahl | Nur Aufträge, deren Kunde der Kunde der Anfrage oder einer seiner untergeordneten Kontakte ist. Ein Auftrag auf die Muttergesellschaft oder einen fremden Partner ist nicht wählbar. Aus der Anfrage kann kein Auftrag angelegt werden. |
| Lager / Lieferung | Mark as Sent erzeugt keine Lieferung und bewegt keinen Bestand. Der Versand erfolgt außerhalb dieses Moduls. |
| Genehmigungsweg | Jeder Manager kann jede Anfrage genehmigen. Es gibt keine Genehmigungsstufen, Betragsgrenzen oder teambezogenen Genehmiger. Manager erhalten beim Einreichen keine E-Mail (nutzen Sie das Menü **Approvals** oder folgen Sie der Anfrage). |
| Erinnerungszeitpunkt | Die 14-Tage-Frist ist im Code festgelegt. Eine Änderung des Sent Date nach Mark as Sent verschiebt die vorhandene Aktivität nicht. **Still Thinking** schließt die Anfrage ohne zweite Erinnerung ab. |
| Endzustände | Rejected, Cancelled und Followed Up lassen sich nicht wieder öffnen. Für einen Neustart **Duplicate** verwenden. |
| Musterkosten | Kosten oder Werte der Muster werden weder erfasst noch ausgewertet. |
