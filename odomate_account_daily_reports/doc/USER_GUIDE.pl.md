# Księgowe raporty dzienne — przewodnik użytkownika

Wydruki PDF dziennika operacji, księgi kasowej i księgi bankowej dla Odoo 19 Community.

## Spis treści

1. [Przegląd](#1-przegląd)
2. [Instalacja](#2-instalacja)
3. [Kto może korzystać](#3-kto-może-korzystać)
4. [Dziennik operacji](#4-dziennik-operacji)
5. [Księga kasowa](#5-księga-kasowa)
6. [Księga bankowa](#6-księga-bankowa)
7. [Jak obliczane są kwoty](#7-jak-obliczane-są-kwoty)
8. [Wielofirmowość](#8-wielofirmowość)
9. [Ograniczenia](#9-ograniczenia)
10. [Wsparcie](#10-wsparcie)

## 1. Przegląd

Moduł dodaje trzy księgi do wydruku w menu **Księgowość → Raportowanie → Audit Reports**:

| Raport | Co zawiera | Objęte dzienniki |
|---|---|---|
| **Dziennik operacji** | Wszystkie zapisy księgowe okresu, pogrupowane w bloki po jednym na dzień kalendarzowy | Wszystkie typy dzienników |
| **Księga kasowa** | Obroty kasowe według kont, z saldem narastającym | dzienniki typu `cash` |
| **Księga bankowa** | Obroty bankowe i kart kredytowych według kont, z saldem narastającym | dzienniki typu `bank` i `credit` |

Wszystkie trzy raporty działają **wyłącznie w trybie odczytu**. Nigdy nie tworzą, nie zmieniają ani nie usuwają rekordów, więc nie zależą od dat blokady i mogą być bezpiecznie uruchamiane przez księgowego z prawem tylko do odczytu.

Moduł ponownie wykorzystuje wspólne okno filtrów, nagłówek strony i poziomy format papieru z modułu **Accounting Audit Reports** (`odomate_account_ledger_reports`), dzięki czemu wszystkie sześć raportów wygląda i działa spójnie.

Drukowany nagłówek — firma, okres, dzienniki oraz wybór **Zapisy** (*Tylko zaksięgowane zapisy* / *Wszystkie zapisy*) — wyświetla się w języku Twojej sesji, dzięki własnym tłumaczeniom modułu (`uk`, `pl`, `de`, `es`, `fr`, `pt_BR`).

## 2. Instalacja

1. Skopiuj `odomate_account_daily_reports` do katalogu addons swojego Odoo.
2. **Aplikacje → Aktualizuj listę aplikacji**.
3. Wyszukaj *Accounting Daily Reports* i kliknij **Instaluj**.

Moduły `account` i `odomate_account_ledger_reports` zostaną zainstalowane automatycznie, jeśli ich jeszcze nie ma.

## 3. Kto może korzystać

Trzy pozycje menu i trzy okna dialogowe są dostępne dla:

- `account.group_account_manager` — administrator księgowości
- `account.group_account_user` — pełne funkcje księgowe
- `account.group_account_readonly` — księgowość tylko do odczytu

Użytkownicy mający wyłącznie `account.group_account_invoice` (Fakturowanie) nie widzą menu i nie mają dostępu: wydruk zgłasza komunikat *„Only accounting users can print accounting reports.”*

Moduł **nie tworzy żadnej nowej grupy uprawnień** i nie modyfikuje żadnego użytkownika.

## 4. Dziennik operacji

**Księgowość → Raportowanie → Audit Reports → Day Book**

| Pole | Znaczenie |
|---|---|
| **Zapisy** | *Tylko zaksięgowane zapisy* lub *Wszystkie zapisy* (dodaje projekty). Zapisy anulowane nigdy się nie pojawiają. |
| **Data początkowa** / **Data końcowa** | Obie są **wymagane**. Domyślnie ustawiona jest data dzisiejsza. |
| **Dzienniki** | Pozostaw puste, aby objąć wszystkie dzienniki firmy. |
| **Firma** | Widoczne w konfiguracjach wielofirmowych. |

Kliknij **Print**, aby otrzymać PDF, albo **Cancel**, aby zamknąć okno.

Wydruk grupuje pozycje w bloki po jednym na dzień. Kolumny to *Dziennik, Zapis, Kontrahent, Odnośnik, Opis, Winien, Ma, Różnica* (oraz *Waluta* dla użytkowników wielowalutowych). Każdy dzień kończy się wierszem **Razem za dzień**, a raport wierszem **Razem**.

Dni bez pozycji nie tworzą bloku — raport nigdy nie drukuje pustego dnia. Jeśli nic nie pasuje, w PDF pojawi się napis *„No entries in this period.”*

Dziennik operacji **nie ma salda początkowego ani salda narastającego**: to chronologiczne zestawienie, a nie rejestr.

## 5. Księga kasowa

**Księgowość → Raportowanie → Audit Reports → Cash Book**

Te same filtry co w dzienniku operacji, a ponadto:

| Pole | Znaczenie |
|---|---|
| **Sortuj według** | *Data* albo *Dziennik i kontrahent* — zmienia kolejność pozycji wewnątrz każdego konta. |
| **Wyświetlane konta** | *Wszystkie konta*, *Z obrotami* (domyślnie) albo *Z saldem różnym od zera*. |
| **Uwzględnij saldo początkowe** | Drukuje wiersz **Saldo początkowe** dla każdego konta. Wymaga daty początkowej. |
| **Z walutą** | Dodaje kolumnę *Waluta*. Widoczne tylko dla użytkowników grupy **Wielowalutowość**. |

Pole **Dzienniki** przyjmuje wyłącznie dzienniki kasowe. Wybranie dziennika bankowego zgłasza komunikat *„This book only covers cash journals.”*

Wydruk zawiera jeden blok na konto, uporządkowane według kodu konta, z kolumnami *Data, Dziennik, Zapis, Kontrahent, Odnośnik, Opis, Winien, Ma, Saldo*. Każdy blok kończy się wierszem **Razem za konto**, a raport wierszem **Razem**.

### Które konta się pojawiają

Księga kasowa nie wymienia po prostu „wszystkiego, czego dotknęły dzienniki kasowe”. Zbiór kont jest ustalany na podstawie:

- **konta domyślnego** i **konta przejściowego** każdego dziennika,
- kont **należności nierozliczonych / płatności nierozliczonych** każdego dziennika,
- oraz każdego konta typu `asset_cash`, którego faktycznie dotknęła pozycja w danym okresie.

Konta należące do innej firmy są pomijane. Dzięki temu dziennik kasowy bez skonfigurowanego konta domyślnego nadal drukuje się poprawnie.

## 6. Księga bankowa

**Księgowość → Raportowanie → Audit Reports → Bank Book**

Identyczna jak księga kasowa, z tą różnicą, że obejmuje dzienniki **bankowe** i **kart kredytowych**, a jej zbiór kont zawiera dodatkowo konta typu `liability_credit_card`. Wybranie dziennika kasowego zgłasza komunikat *„This book only covers bank and credit card journals.”*

## 7. Jak obliczane są kwoty

### Saldo początkowe

Przy zaznaczonej opcji **Uwzględnij saldo początkowe** wiersz salda początkowego sumuje wszystko, co zaksięgowano na danym koncie **przed datą początkową**, według tej samej reguły uwzględniającej rok obrotowy, co księga główna modułu *Accounting Audit Reports*. Dla kont kasowych i kont kart kredytowych, które zawsze przenoszą saldo, są to po prostu wszystkie wcześniejsze pozycje.

### Saldo narastające

Kolumna **Saldo** to rzeczywiste saldo narastające dla każdego konta:

```
saldo wiersza = saldo poprzedniego wiersza + winien tego wiersza − ma tego wiersza
```

Pierwszy wiersz zaczyna się od salda początkowego lub od zera, gdy saldo początkowe nie jest drukowane.

### Saldo końcowe

```
Razem za konto = Saldo początkowe + Σ winien − Σ ma
```

Jest sumowane z pozycji, a nie odczytywane z ostatniego wiersza.

### Przykład liczbowy

Konto **101100 Cash A**, okres 01.03.2024 → 31.03.2024, saldo początkowe włączone.

| Wiersz | Winien | Ma | Saldo |
|---|---:|---:|---:|
| Saldo początkowe | 1 000,00 | 0,00 | **1 000,00** |
| 05.03.2024 CASH-IN | 200,00 | 0,00 | **1 200,00** |
| 10.03.2024 CASH-OUT | 0,00 | 50,00 | **1 150,00** |
| **Razem za konto** | **200,00** | **50,00** | **1 150,00** |

Sprawdzenie: `1 000,00 + 200,00 − 50,00 = 1 150,00`.

Ten sam okres w dzienniku operacji, dla 05.03.2024 — wpływ gotówki 200,00 i wpływ na rachunek bankowy 300,00:

| | Winien | Ma | Różnica |
|---|---:|---:|---:|
| **Razem za dzień** | 500,00 | 500,00 | **0,00** |

W zbilansowanej księdze kolumna **Różnica** zawsze wynosi 0,00; wartość różna od zera wskazuje na niezbilansowany zapis.

### Waluta

Wszystkie kwoty są drukowane w **walucie firmy** — nic nie jest przeliczane. Opcjonalna kolumna *Waluta* pokazuje kwotę pozycji w jej własnej walucie za każdym razem, gdy waluta ta różni się od waluty firmy, w tym również kwoty ujemne.

## 8. Wielofirmowość

Każdy wydruk obejmuje dokładnie jedną firmę — tę wybraną w oknie dialogowym. Pozycje innych firm nigdy się nie pojawiają. Wybranie firmy, w której nie masz uprawnień do pracy, zgłasza komunikat *„You cannot print a report for a company you are not allowed to work in.”*

Cztery modele okien dialogowych są przejściowe i nie przechowują własnych danych firmy, więc reguła rekordu nie jest potrzebna: filtr firmy działa na etapie walidacji oraz w każdej domenie.

## 9. Ograniczenia

- **Tylko PDF i HTML.** Nie ma eksportu do XLSX ani CSV, ani interaktywnej wersji ekranowej.
- **Brak drążenia danych.** PDF to wydruk; kliknięcie kwoty nie otwiera powiązanego zapisu.
- **Jedna firma na wydruk.** Skonsolidowane księgi wielofirmowe nie są obsługiwane.
- **Brak przeliczania walut.** Pozycje w walucie obcej są pokazywane w zaksięgowanej wartości w walucie firmy; raport nie przelicza ich po wybranym kursie.
- **Brak kolumn analitycznych.** Jeśli potrzebujesz podziału analitycznego, użyj księgi głównej modułu *Accounting Audit Reports*.
- **Dziennik operacji nie ma sald** — tak zaprojektowano; do salda narastającego i końcowego użyj księgi kasowej lub bankowej.
- **Brak danych demonstracyjnych.** Te raporty drukują to, co już znajduje się w Twojej bazie danych.

## 10. Wsparcie

- Autor: OdoMate — <https://odomate.pro>
- Wsparcie: <support@odomate.pro>

Wersja angielska tego przewodnika: `USER_GUIDE.md`.
