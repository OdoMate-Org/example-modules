# Buchhaltungs-Prüfungsberichte — Benutzerhandbuch

Modul: `odomate_account_ledger_reports` · Odoo 19.0 · Version 19.0.1.0.1 · Lizenz LGPL-3

## Inhaltsverzeichnis

1. [Was dieses Modul leistet](#1-was-dieses-modul-leistet)
2. [Installation](#2-installation)
3. [Wer es nutzen darf](#3-wer-es-nutzen-darf)
4. [Wo die Berichte zu finden sind](#4-wo-die-berichte-zu-finden-sind)
5. [Der gemeinsame Filter](#5-der-gemeinsame-filter)
6. [Hauptbuch](#6-hauptbuch)
7. [Partnerkonten](#7-partnerkonten)
8. [Offene-Posten-Altersstruktur](#8-offene-posten-altersstruktur)
9. [Steuerbericht](#9-steuerbericht)
10. [Journalprüfung](#10-journalprüfung)
11. [Buchungssatz-Ausdruck](#11-buchungssatz-ausdruck)
12. [Buchungszeilen-Ansichten](#12-buchungszeilen-ansichten)
13. [Bekannte Einschränkungen](#13-bekannte-einschränkungen)
14. [Für Entwickler: der stabile Vertrag](#14-für-entwickler-der-stabile-vertrag)

---

## 1. Was dieses Modul leistet

Es ergänzt die sechs klassischen Prüfungsausdrucke, die Wirtschaftsprüfer und Buchhalter anfordern, als einfache PDF-Dokumente sowie zwei fertige Buchungszeilen-Ansichten.

| Bericht | Beantwortet |
|---|---|
| Hauptbuch | Welche Bewegungen es je Konto gab, mit laufendem Saldo |
| Partnerkonten | Welche Bewegungen es je Kunden-/Lieferantenkonto gab und was noch offen ist |
| Offene-Posten-Altersstruktur | Wie überfällig jeder offene Posten ist, nach Altersklassen |
| Steuerbericht | Netto- und Steuerbeträge je Steuer, getrennt nach Verkauf und Einkauf |
| Journalprüfung | Jede Zeile der gewählten Journale, mit Steuerübersicht je Journal |
| Buchungssatz | Eine Seite je Buchung, zum Ablegen oder Beilegen |

Alle Berichte lesen Buchungszeilen ausschließlich über das Odoo-ORM. Das Modul schreibt nichts außerhalb seiner eigenen Dialogdatensätze und fügt keinem Standardmodell ein Feld hinzu.

## 2. Installation

1. Kopieren Sie den Ordner `odomate_account_ledger_reports` in Ihren Addons-Pfad.
2. **Apps → App-Liste aktualisieren**.
3. Suchen Sie nach *Accounting Audit Reports* und klicken Sie auf **Aktivieren**.

Die einzigen Abhängigkeiten sind `account` und `analytic`, beide Bestandteil von Odoo Community. Nach der Installation ist keine Konfiguration nötig: Es gibt keine Einstellungsseite, keinen geplanten Job und keine Demodaten.

## 3. Wer es nutzen darf

Drei vorhandene Odoo-Buchhaltungsgruppen dürfen die Dialoge öffnen und drucken:

- `account.group_account_manager` — Abrechnungsadministrator
- `account.group_account_user` — Buchhalter
- `account.group_account_readonly` — Buchhaltungszugriff nur lesend

Das Modul legt keine eigene Gruppe an und gewährt keiner anderen Gruppe etwas. Ein Benutzer außerhalb dieser drei Gruppen erhält beim Druckversuch `Nur Buchhaltungsbenutzer dürfen Buchhaltungsberichte drucken.` und sieht die Menüs gar nicht erst.

Jeder Dialogdatensatz ist ein transienter Assistentendatensatz: Die drei Gruppen erhalten Lesen, Schreiben und Anlegen, niemand erhält Löschen — dafür sorgt Odoos eigene Bereinigung.

## 4. Wo die Berichte zu finden sind

| Bericht | Menüpfad |
|---|---|
| Hauptbuch | Buchhaltung → Berichtswesen → Prüfungsberichte → Hauptbuch |
| Journalprüfung | Buchhaltung → Berichtswesen → Prüfungsberichte → Journalprüfung |
| Partnerkonten | Buchhaltung → Berichtswesen → Partnerberichte → Partnerkonten |
| Offene-Posten-Altersstruktur | Buchhaltung → Berichtswesen → Partnerberichte → Offene-Posten-Altersstruktur |
| Offene Forderungen nach Alter | Buchhaltung → Berichtswesen → Partnerberichte → Offene Forderungen nach Alter |
| Offene Verbindlichkeiten nach Alter | Buchhaltung → Berichtswesen → Partnerberichte → Offene Verbindlichkeiten nach Alter |
| Steuerbericht | Buchhaltung → Berichtswesen → Steuern → Steuerbericht |
| Buchungszeilen nach Konto | Buchhaltung → Berichtswesen → Verwaltung → Buchungszeilen nach Konto |
| Buchungszeilen nach Partner | Buchhaltung → Berichtswesen → Verwaltung → Buchungszeilen nach Partner |

*Offene Forderungen nach Alter* und *Offene Verbindlichkeiten nach Alter* sind derselbe Dialog wie *Offene-Posten-Altersstruktur*, nur mit vorgewähltem und ausgeblendetem Kontotyp.

Der Buchungssatz-Ausdruck hat kein Menü: Markieren Sie eine oder mehrere Buchungen unter **Buchhaltung → Buchhaltung → Buchungen** und nutzen Sie **Drucken → Buchungssatz**.

## 5. Der gemeinsame Filter

Jeder Dialog beginnt mit demselben Satz von vier Feldern.

| Feld | Bedeutung |
|---|---|
| **Buchungen** | *Nur gebuchte Buchungen* (Vorgabe) oder *Alle Buchungen*. Stornierte Buchungen werden in keinem Fall einbezogen. |
| **Startdatum** / **Enddatum** | Begrenzen die Buchungszeilen nach ihrem Buchungsdatum. Lassen Sie beide leer für „alle Daten“, wo der Dialog das erlaubt. |
| **Journale** | Leer lassen, um alle Journale des Unternehmens einzubeziehen. |
| **Unternehmen** | Nur in Mehrfirmen-Datenbanken sichtbar. Standard ist Ihr aktives Unternehmen. |

**Drucken** erzeugt das PDF, **Abbrechen** schließt den Dialog.

Der Dialog verweigert den Druck und erklärt den Grund, wenn:

- das gewählte Unternehmen nicht zu denen gehört, in denen Sie arbeiten dürfen;
- das Startdatum nach dem Enddatum liegt;
- ein gewähltes Journal zu einem anderen Unternehmen gehört.

## 6. Hauptbuch

**Zusatzfelder:** Konten, Partner, Kostenstellen (nur mit *Kostenrechnung*), Sortieren nach, Konten anzeigen, Eröffnungsbilanz einbeziehen.

**Spalten:** Datum · Journal · Partner · Referenz · Buchung · Bezeichnung · Soll · Haben · Saldo, zusätzlich Währung (bei Mehrwährungsbetrieb, nur wenn die Währung der Zeile von der Unternehmenswährung abweicht) und Kostenstelle (bei Kostenrechnung).

**Konten anzeigen**

- *Alle Konten* — jedes Konto des Unternehmens, auch unbewegte.
- *Mit Bewegungen* (Vorgabe) — Konten mit Zeilen im Zeitraum oder mit einer Eröffnung ungleich null.
- *Mit Saldo ungleich null* — blendet Konten aus, deren Eröffnung + Soll − Haben auf null rundet.

**Sortieren nach** ändert die Reihenfolge innerhalb eines Kontos: *Datum* nach Datum, Buchungsnummer, ID; *Journal und Partner* nach Journal, dann Partner, dann Datum.

### Rechenbeispiel — die Eröffnungsbilanz

Unternehmensbücher, Geschäftsjahr = Kalenderjahr, Startdatum **2024-03-01**, **Eröffnungsbilanz einbeziehen** aktiviert.

| Buchung | Datum | Konto 121000 (Forderungen) | Konto 400000 (Erträge) |
|---|---|---|---|
| E1 | 2023-06-15 | Soll 1.000,00 | Haben 1.000,00 |
| E2 | 2024-02-10 | Soll 500,00 | Haben 500,00 |
| E3 | 2024-03-15 | Soll 250,00 | Haben 250,00 |

Gedruckte Eröffnungen:

- **121000** ist ein Bilanzkonto und eröffnet daher mit *allem*, was vor dem Startdatum gebucht wurde: 1.000,00 + 500,00 = **1.500,00**.
- **400000** ist ein Ertragskonto und eröffnet daher nur mit dem laufenden Geschäftsjahr: E1 fällt ins Vorjahr und entfällt, es bleiben **−500,00**.

Der laufende Saldo von 121000 zeigt dann 1.500,00 in der Zeile *Eröffnungsbilanz* und 1.750,00 nach E3; die Kontosummenzeile zeigt Soll 250,00, Haben 0,00, Saldo 1.750,00.

## 7. Partnerkonten

**Zusatzfelder:** Partner, Kontotyp, Ausgeglichene Posten einbeziehen, Betrag in Währung anzeigen (bei Mehrwährungsbetrieb).

**Kontotyp** bildet auf die Odoo-Kontotypen ab: *Forderungskonten* → `asset_receivable`, *Verbindlichkeitskonten* → `liability_payable`, *Forderungs- und Verbindlichkeitskonten* → beide.

**Spalten:** Datum · Journal · Konto · Buchung · Referenz · Bezeichnung · Soll · Haben · Saldo (beginnt je Partner bei null), zusätzlich Währung.

Jeder Partnerblock endet mit Soll, Haben, Schlusssaldo und **Offener Betrag** — der Summe der Restbeträge der Zeilen.

Ein Posten bleibt ausgeblendet, solange **Ausgeglichene Posten einbeziehen** nicht aktiviert ist, nur solange er *vollständig* ausgeglichen ist — das heißt, wenn auch alle Posten auf der Gegenseite seines Ausgleichs zugeordnet sind und nichts mehr offen bleibt. Eine teilweise bezahlte Rechnung druckt weiterhin sowohl ihre eigene Zeile als auch die Zeile ihrer Zahlung, bis das der Fall ist, sodass der Schlusssaldo stets zeigt, was noch offen ist; eine vollständig bezahlte Rechnung und ihre Zahlung verschwinden gemeinsam und erscheinen beim Aktivieren von **Ausgeglichene Posten einbeziehen** wieder gemeinsam. Zeilen ohne Partner werden hier nie gedruckt; sie gehören ins Hauptbuch.

Sie können den Bericht auch direkt aus einem Kontakt drucken: Markieren Sie einen oder mehrere Kontakte unter **Kontakte** und wählen Sie **Drucken → Partnerkonten**. Der Dialog öffnet sich mit diesen Partnern, dem Kontotyp *Forderungs- und Verbindlichkeitskonten* und einbezogenen ausgeglichenen Posten.

### Rechenbeispiel — eine teilweise bezahlte Rechnung behält ihre Zahlung auf einer eigenen Zeile

Eine Kundenrechnung über 1.000,00 wird gebucht und anschließend mit 400,00 teilweise bezahlt. Gedruckt mit deaktiviertem **Ausgeglichene Posten einbeziehen**:

| Zeile | Soll | Haben | Saldo |
|---|---|---|---|
| Rechnung | 1.000,00 | | 1.000,00 |
| Zahlung | | 400,00 | 600,00 |
| **Partnersumme** | **1.000,00** | **400,00** | **600,00** |

**Offener Betrag** zeigt ebenfalls 600,00 — beide Zeilen werden gedruckt, weil auf Rechnungsseite noch 600,00 offen sind, auch wenn die Zahlung selbst nichts mehr zuzuordnen hat. Sobald die Rechnung vollständig bezahlt ist, verschwinden beide Zeilen aus der deaktivierten Ansicht und erscheinen erst beim Aktivieren von **Ausgeglichene Posten einbeziehen** wieder gemeinsam.

## 8. Offene-Posten-Altersstruktur

**Zusatzfelder:** Stichtag (Pflicht, Vorgabe heute), Periodenlänge (Tage) (Pflicht, Vorgabe 30), Kontotyp, Partner. Startdatum und Journale werden in diesem Bericht nicht verwendet und sind ausgeblendet.

Jeder offene Posten wird nach seinem Alter in ganzen Tagen einer von sechs Spalten zugeordnet, wobei Alter = *Stichtag* − (Fälligkeitsdatum, ersatzweise Buchungsdatum):

| Spalte | Alter (P = Periodenlänge) |
|---|---|
| Nicht fällig | Alter ≤ 0 |
| 1 - P | 1 … P |
| P+1 - 2P | P+1 … 2P |
| 2P+1 - 3P | 2P+1 … 3P |
| 3P+1 - 4P | 3P+1 … 4P |
| +4P | Alter > 4P |

Eine Zeile, deren sechs Spalten alle null sind, entfällt. Posten ohne Partner werden in einer Zeile **Unbekannter Partner** zusammengefasst. Alle Beträge stehen in Unternehmenswährung; es wird nirgends umgerechnet.

### Rechenbeispiel — Einordnung bei P = 30, Stichtag 2024-06-30

| Posten | Fälligkeit | Alter | Betrag | Spalte |
|---|---|---|---|---|
| A | 2024-06-30 | 0 | 10,00 | Nicht fällig |
| B | 2024-06-29 | 1 | 20,00 | 1 - 30 |
| C | 2024-05-31 | 30 | 30,00 | 1 - 30 |
| D | 2024-05-30 | 31 | 40,00 | 31 - 60 |
| E | 2024-03-01 | 121 | 50,00 | +120 |

Gedruckte Zeile: Nicht fällig 10,00 · 1-30 50,00 · 31-60 40,00 · 61-90 0,00 · 91-120 0,00 · +120 50,00 · Summe 150,00.

### Rechenbeispiel — der Restbetrag gilt *zum Stichtag*

Eine Rechnung über 1.000,00 wird am 2024-03-10 gebucht und am 2024-05-20 mit 400,00 teilweise bezahlt.

- Zum **2024-04-30** hat die Zahlung noch nicht stattgefunden, der Bericht zeigt also **1.000,00**.
- Zum **2024-06-30** zeigt er **600,00**, und die Zahlungszeile selbst saldiert auf null und verschwindet.

Der Bericht berechnet den Restbetrag aus der Ausgleichshistorie neu, statt den heutigen `amount_residual` zu lesen — genau das macht eine rückdatierte Altersstruktur korrekt.

## 9. Steuerbericht

Es gilt nur der gemeinsame Filter; Startdatum und Enddatum sind Pflicht und stehen standardmäßig auf dem ersten Tag des laufenden Monats und auf heute.

Der Bericht listet alle aktiven Verkaufs- und Einkaufssteuern des Unternehmens in zwei Abschnitten. Eine Steuergruppe wird durch ihre untergeordneten Steuern unter dem Typ der übergeordneten Steuer dargestellt; die Gruppe selbst ist keine Zeile. Je Steuer:

- **Nettobetrag** — die Summe der Salden der Zeilen, die diese Steuer tragen.
- **Steuerbetrag** — die Summe der Salden der von dieser Steuer erzeugten Steuerzeilen.

Im Abschnitt **Verkauf** wird bei beiden Werten das Vorzeichen gedreht, damit Erlöse positiv erscheinen; im Abschnitt **Einkauf** werden sie so gedruckt, wie sie gebucht sind. Es wird nie ein Absolutwert gebildet, sodass Gutschriften die Werte tatsächlich mindern. Zeilen, die bei beiden Werten null sind, entfallen; ein leerer Abschnitt druckt *In diesem Zeitraum gibt es keine Steuerbewegungen.*

### Rechenbeispiel — eine Gutschrift mindert die Verkaufswerte

März 2024, eine Verkaufssteuer von 20 %:

| Beleg | Netto | Steuer |
|---|---|---|
| Kundenrechnung, 1.000,00 + 20 % | 1.000,00 | 200,00 |
| Gutschrift, 400,00 + 20 % | −400,00 | −80,00 |
| **Gedruckte Zeile „Verkauf“** | **600,00** | **120,00** |

## 10. Journalprüfung

**Zusatzfelder:** Journale (Pflicht — Vorgabe sind die Verkaufs- und Einkaufsjournale Ihres Unternehmens), Buchungen sortieren nach, Betrag in Währung anzeigen.

Ein Abschnitt je gewähltem Journal, in der Reihenfolge der Journale. **Spalten:** Buchung · Datum · Konto · Partner · Bezeichnung · Soll · Haben, zusätzlich Währung. Jeder Abschnitt endet mit den Soll- und Haben-Summen des Journals.

Enthält das Journal besteuerte Zeilen, folgt eine kleine Übersicht mit Steuer / Bemessungsgrundlage / Steuerbetrag nach derselben Vorzeichenregel wie im Steuerbericht (Verkaufssteuern negiert). Journale ohne besteuerte Zeilen haben schlicht keine Übersicht.

## 11. Buchungssatz-Ausdruck

Kein Dialog: Buchungen markieren und **Drucken → Buchungssatz** wählen. Eine Seite je Buchung, jeweils mit Briefkopf und Währung des eigenen Unternehmens.

Der Kopf zeigt Buchungsnummer, Journal, Datum, Partner, Referenz und Status. Die Zeilentabelle zeigt Konto · Bezeichnung · Partner · Kostenstelle · Soll · Haben · Währung in der eigenen Zeilenreihenfolge der Buchung, ohne Abschnitts-, Unterabschnitts- und Notizzeilen. Die Summenzeile addiert Soll und Haben in der Unternehmenswährung der Buchung — bei jeder gebuchten Buchung sind sie gleich.

## 12. Buchungszeilen-Ansichten

Zwei gespeicherte Ansichten auf `account.move.line`, beide als Liste / Pivot / Grafik mit Odoos Standard-Suchbereich für Buchungszeilen und beide ohne Abschnitts-, Unterabschnitts- und Notizzeilen:

- **Buchungszeilen nach Konto** — nach Konto gruppiert, nur gebuchte Buchungen.
- **Buchungszeilen nach Partner** — nach Partner gruppiert, gebuchte Buchungen, vorgefiltert auf Forderungen, Verbindlichkeiten und nicht ausgeglichene Posten.

Es sind gewöhnliche Odoo-Listen: Sie können umgruppieren, filtern, exportieren und von dort in eine Buchung springen.

## 13. Bekannte Einschränkungen

- **Nur Unternehmenswährung.** Jede Zahl ist der Betrag in Unternehmenswährung. Die optionale Spalte Währung zeigt den Fremdwährungsbetrag der Zeile zur Information; es wird nichts umgerechnet.
- **Kein Excel-Export.** Die Berichte gibt es nur als PDF. Für Tabellenkalkulation nutzen Sie die beiden Buchungszeilen-Ansichten.
- **Altersstruktur ignoriert Journale.** Bewusst umfasst sie alle Journale des Unternehmens; das Feld Journale ist in diesem Dialog ausgeblendet.
- **Kein Drill-down.** Die PDFs sind statische Dokumente und verlinken nicht zurück nach Odoo.
- **`account.report` unberührt.** Das Modul erweitert Odoos dynamische Berichts-Engine nicht, daher erscheinen diese Berichte nicht in deren Variantenauswahl.
- **Umfang des Steuerberichts.** Aufgeführt werden nur Steuern mit `type_tax_use` gleich `sale` oder `purchase`; Steuern mit *None* erscheinen nie.
- **Spalte „Kostenstelle“.** Die Kostenstelleninformation stammt aus `analytic_distribution`; die gezeigten Prozentwerte sind Verteilungsprozente, keine Beträge.

## 14. Für Entwickler: der stabile Vertrag

Schwestermodule dürfen sich auf Folgendes verlassen; es ändert sich nicht:

**Modell** `odomate.account.report.filter` (konkretes `TransientModel`, Basis für Prototyp-Vererbung) mit den Feldern `company_id`, `date_from`, `date_to`, `journal_ids`, `target_move` und den Methoden:

| Element | Art | Zweck |
|---|---|---|
| `_odomate_journals()` | Datensatz | Gewählte Journale oder alle Journale des Unternehmens |
| `_odomate_state_domain()` | Datensatz | Statusbedingung für das gewählte `target_move` |
| `_odomate_line_domain(date_field='date', date_from=None, date_to=None)` | Datensatz | Die Basisdomäne der Buchungszeilen |
| `_odomate_check_filter()` | Datensatz | Validierung; mit `super()` erweitern |
| `_odomate_report_data()` | Datensatz | Nutzlast ausschließlich aus einfachen Typen |
| `_odomate_print(report_xmlid=None)` | Datensatz | Prüfen und die Berichtsaktion zurückgeben |
| `action_odomate_print()` | Datensatz | Die Schaltfläche „Drucken“ des Dialogs |
| `_odomate_report_xmlid` | Klassenattribut | Standard-XML-ID des Berichts zum Dialog |
| `_odomate_options_from_data(data)` | Modell | Nutzlast zurück in Datensätze und Daten übersetzen |
| `_odomate_check_report_access()` | Modell | Löst `AccessError` außerhalb der drei Buchhaltungsgruppen aus |
| `_odomate_initial_balance_domain(company, date_from, journals=None, target_move='posted')` | Modell | Domäne der Eröffnungsbilanz |

**Ansicht** `odomate_account_ledger_reports.view_odomate_account_report_filter_form` — mit `mode="primary"` erben und eigene Felder nach dem Knoten `journal_ids` oder dem Knoten `target_move` einfügen. Nur diese beiden Stellen werden unterstützt.

**QWeb** `odomate_account_ledger_reports.report_filter_header` — Parameter `company`, `date_from`, `date_to`, `journals`, `target_move_label`.

**Papierformat** `odomate_account_ledger_reports.paperformat_odomate_ledger_landscape` — A4 quer, 10 mm Ränder.

**Menü** `odomate_account_ledger_reports.menu_odomate_account_reports_audit` — der Ordner *Prüfungsberichte*.

Alles Übrige — dialogspezifische Felder, Hilfsmethoden zum Zeilenaufbau, Namen der Berichtsmodelle, Formulierungen der Vorlagen, Reihenfolge der Dictionary-Schlüssel — ist intern und kann sich ändern.

---

© OdoMate · <https://odomate.pro> · <support@odomate.pro>
