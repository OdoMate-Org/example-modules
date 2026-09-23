# Buchhaltung Tagesberichte — Benutzerhandbuch

PDF-Ausdrucke von Tagebuch, Kassenbuch und Bankbuch für Odoo 19 Community.

## Inhaltsverzeichnis

1. [Überblick](#1-überblick)
2. [Installation](#2-installation)
3. [Wer es nutzen darf](#3-wer-es-nutzen-darf)
4. [Tagebuch](#4-tagebuch)
5. [Kassenbuch](#5-kassenbuch)
6. [Bankbuch](#6-bankbuch)
7. [Wie die Beträge berechnet werden](#7-wie-die-beträge-berechnet-werden)
8. [Mehrere Unternehmen](#8-mehrere-unternehmen)
9. [Einschränkungen](#9-einschränkungen)
10. [Support](#10-support)

## 1. Überblick

Das Modul fügt unter **Buchhaltung → Berichtswesen → Audit Reports** drei druckbare Bücher hinzu:

| Bericht | Inhalt | Erfasste Journale |
|---|---|---|
| **Tagebuch** | Alle Buchungszeilen des Zeitraums, gruppiert in einen Block je Kalendertag | Alle Journaltypen |
| **Kassenbuch** | Kassenbewegungen je Konto, mit laufendem Saldo | Journale vom Typ `cash` |
| **Bankbuch** | Bank- und Kreditkartenbewegungen je Konto, mit laufendem Saldo | Journale vom Typ `bank` und `credit` |

Alle drei Berichte arbeiten **ausschließlich lesend**. Sie erstellen, ändern oder löschen niemals einen Datensatz, sind daher von Sperrdaten unabhängig und können gefahrlos von einer Buchhaltungskraft mit reinem Leserecht ausgeführt werden.

Das Modul verwendet den gemeinsamen Filterdialog, die Seitenkopfzeile und das Querformat von **Accounting Audit Reports** (`odomate_account_ledger_reports`) wieder, sodass alle sechs Berichte einheitlich aussehen und sich einheitlich verhalten.

Die gedruckte Kopfzeile — Unternehmen, Zeitraum, Journale und die Auswahl **Buchungen** (*Nur gebuchte Buchungen* / *Alle Buchungen*) — erscheint in der Sprache Ihrer Sitzung, dank der eigenen Übersetzungen des Moduls (`uk`, `pl`, `de`, `es`, `fr`, `pt_BR`).

## 2. Installation

1. Kopieren Sie `odomate_account_daily_reports` in Ihren Odoo-Addons-Pfad.
2. **Apps → App-Liste aktualisieren**.
3. Suchen Sie nach *Accounting Daily Reports* und klicken Sie auf **Installieren**.

`account` und `odomate_account_ledger_reports` werden automatisch installiert, falls sie noch nicht vorhanden sind.

## 3. Wer es nutzen darf

Die drei Menüpunkte und die drei Dialoge stehen zur Verfügung für:

- `account.group_account_manager` — Buchhaltungsadministrator
- `account.group_account_user` — vollständige Buchhaltungsfunktionen
- `account.group_account_readonly` — Buchhaltung nur lesend

Benutzer, die nur `account.group_account_invoice` (Rechnungsstellung) besitzen, sehen kein Menü und erhalten keinen Zugriff: Das Drucken löst die Meldung *„Only accounting users can print accounting reports.“* aus.

Das Modul erstellt **keine neue Berechtigungsgruppe** und ändert keinen Benutzer.

## 4. Tagebuch

**Buchhaltung → Berichtswesen → Audit Reports → Day Book**

| Feld | Bedeutung |
|---|---|
| **Buchungen** | *Nur gebuchte Buchungen* oder *Alle Buchungen* (ergänzt Entwürfe). Stornierte Buchungen erscheinen nie. |
| **Startdatum** / **Enddatum** | Beide sind **Pflichtfelder**. Voreingestellt ist das heutige Datum. |
| **Journale** | Leer lassen, um alle Journale des Unternehmens einzubeziehen. |
| **Unternehmen** | In Mehrfirmen-Konfigurationen sichtbar. |

Klicken Sie auf **Print** für das PDF oder auf **Cancel**, um den Dialog zu schließen.

Der Ausdruck gruppiert die Zeilen in einen Block je Tag. Die Spalten sind *Journal, Buchung, Partner, Referenz, Bezeichnung, Soll, Haben, Differenz* (sowie *Währung* für Benutzer mit Mehrwährungsfähigkeit). Jeder Tag schließt mit einer **Tagessumme**-Zeile ab, der Bericht mit einer **Gesamt**-Zeile.

Tage ohne Zeilen erzeugen keinen Block — der Bericht druckt niemals einen leeren Tag. Passt nichts, steht im PDF *„No entries in this period.“*

Das Tagebuch hat **weder Anfangssaldo noch laufenden Saldo**: Es ist eine chronologische Übersicht, kein Kontoauszug.

## 5. Kassenbuch

**Buchhaltung → Berichtswesen → Audit Reports → Cash Book**

Dieselben Filter wie beim Tagebuch, zusätzlich:

| Feld | Bedeutung |
|---|---|
| **Sortieren nach** | *Datum* oder *Journal und Partner* — ändert die Reihenfolge der Zeilen innerhalb jedes Kontos. |
| **Konten anzeigen** | *Alle Konten*, *Mit Bewegungen* (Standard) oder *Mit Saldo ungleich null*. |
| **Anfangssaldo einbeziehen** | Druckt je Konto eine **Anfangssaldo**-Zeile. Erfordert ein Startdatum. |
| **Mit Währung** | Ergänzt die Spalte *Währung*. Nur für Benutzer der Gruppe **Mehrere Währungen** sichtbar. |

Das Feld **Journale** akzeptiert nur Kassenjournale. Die Auswahl eines Bankjournals löst die Meldung *„This book only covers cash journals.“* aus.

Der Ausdruck enthält je Konto einen Block, sortiert nach Kontonummer, mit den Spalten *Datum, Journal, Buchung, Partner, Referenz, Bezeichnung, Soll, Haben, Saldo*. Jeder Block schließt mit einer **Kontosumme**-Zeile ab, der Bericht mit einer **Gesamt**-Zeile.

### Welche Konten erscheinen

Das Kassenbuch listet nicht einfach „alles, was die Kassenjournale berührt haben“. Die Kontenmenge wird ermittelt aus:

- dem **Standardkonto** und dem **Zwischenkonto** jedes Journals,
- den Konten für **offene Einzahlungen / offene Auszahlungen** jedes Journals,
- sowie jedem Konto vom Typ `asset_cash`, das im Zeitraum tatsächlich von einer Zeile berührt wurde.

Konten eines anderen Unternehmens werden verworfen. Dadurch wird ein Kassenjournal ohne konfiguriertes Standardkonto dennoch korrekt gedruckt.

## 6. Bankbuch

**Buchhaltung → Berichtswesen → Audit Reports → Bank Book**

Identisch zum Kassenbuch, umfasst jedoch **Bank-** und **Kreditkartenjournale**, und die Kontenmenge enthält zusätzlich Konten vom Typ `liability_credit_card`. Die Auswahl eines Kassenjournals löst die Meldung *„This book only covers bank and credit card journals.“* aus.

## 7. Wie die Beträge berechnet werden

### Anfangssaldo

Ist **Anfangssaldo einbeziehen** aktiviert, summiert die Anfangssaldo-Zeile alles, was auf diesem Konto **vor dem Startdatum** gebucht wurde, nach derselben geschäftsjahrgerechten Regel wie das Hauptbuch von *Accounting Audit Reports*. Für Kassen- und Kreditkartenkonten, die ihren Saldo stets vortragen, sind das schlicht alle früheren Zeilen.

### Laufender Saldo

Die Spalte **Saldo** ist ein echter laufender Saldo je Konto:

```
Saldo einer Zeile = Saldo der vorherigen Zeile + Soll dieser Zeile − Haben dieser Zeile
```

Die erste Zeile beginnt beim Anfangssaldo oder bei null, wenn der Anfangssaldo nicht gedruckt wird.

### Endsaldo

```
Kontosumme = Anfangssaldo + Σ Soll − Σ Haben
```

Sie wird aus den Zeilen aufsummiert und nicht aus der letzten Zeile abgelesen.

### Rechenbeispiel

Konto **101100 Cash A**, Zeitraum 01.03.2024 → 31.03.2024, Anfangssaldo aktiviert.

| Zeile | Soll | Haben | Saldo |
|---|---:|---:|---:|
| Anfangssaldo | 1.000,00 | 0,00 | **1.000,00** |
| 05.03.2024 CASH-IN | 200,00 | 0,00 | **1.200,00** |
| 10.03.2024 CASH-OUT | 0,00 | 50,00 | **1.150,00** |
| **Kontosumme** | **200,00** | **50,00** | **1.150,00** |

Probe: `1.000,00 + 200,00 − 50,00 = 1.150,00`.

Derselbe Zeitraum im Tagebuch, für den 05.03.2024 — eine Bareinnahme von 200,00 und ein Bankeingang von 300,00:

| | Soll | Haben | Differenz |
|---|---:|---:|---:|
| **Tagessumme** | 500,00 | 500,00 | **0,00** |

In einer ausgeglichenen Buchhaltung beträgt die Spalte **Differenz** immer 0,00; ein abweichender Wert weist auf eine unausgeglichene Buchung hin.

### Währung

Alle Beträge werden in der **Unternehmenswährung** gedruckt — es wird nichts umgerechnet. Die optionale Spalte *Währung* zeigt den Betrag der Zeile in ihrer eigenen Währung, sobald sich diese von der Unternehmenswährung unterscheidet, negative Beträge eingeschlossen.

## 8. Mehrere Unternehmen

Jeder Ausdruck umfasst genau ein Unternehmen — das im Dialog gewählte. Zeilen anderer Unternehmen erscheinen nie. Die Wahl eines Unternehmens, in dem Sie nicht arbeiten dürfen, löst die Meldung *„You cannot print a report for a company you are not allowed to work in.“* aus.

Die vier Dialogmodelle sind transient und halten keine eigenen Unternehmensdaten, daher ist keine Datensatzregel nötig: Der Unternehmensfilter liegt im Validierungsschritt und in jeder Domain.

## 9. Einschränkungen

- **Nur PDF und HTML.** Es gibt keinen XLSX- oder CSV-Export und keine interaktive Bildschirmversion.
- **Kein Drill-down.** Das PDF ist ein Ausdruck; ein Klick auf einen Betrag öffnet die zugrunde liegende Buchung nicht.
- **Ein Unternehmen je Ausdruck.** Konsolidierte Bücher über mehrere Unternehmen werden nicht unterstützt.
- **Keine Währungsumrechnung.** Fremdwährungszeilen werden mit ihrem gebuchten Wert in Unternehmenswährung ausgewiesen; der Bericht rechnet sie nicht zu einem gewählten Kurs um.
- **Keine Kostenstellenspalten.** Wenn Sie die analytische Verteilung benötigen, nutzen Sie das Hauptbuch von *Accounting Audit Reports*.
- **Das Tagebuch hat keine Salden** — das ist beabsichtigt; für laufende und End-Salden nutzen Sie das Kassen- oder Bankbuch.
- **Keine Demodaten.** Diese Berichte drucken das, was Ihre Datenbank bereits enthält.

## 10. Support

- Autor: OdoMate — <https://odomate.pro>
- Support: <support@odomate.pro>

Englische Fassung dieses Handbuchs: `USER_GUIDE.md`.
