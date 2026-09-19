# Księgowe raporty audytowe — Podręcznik użytkownika

Moduł: `odomate_account_ledger_reports` · Odoo 19.0 · Wersja 19.0.1.0.1 · Licencja LGPL-3

## Spis treści

1. [Co robi ten moduł](#1-co-robi-ten-moduł)
2. [Instalacja](#2-instalacja)
3. [Kto może korzystać](#3-kto-może-korzystać)
4. [Gdzie znaleźć raporty](#4-gdzie-znaleźć-raporty)
5. [Wspólny filtr](#5-wspólny-filtr)
6. [Księga główna](#6-księga-główna)
7. [Księga kontrahentów](#7-księga-kontrahentów)
8. [Wiekowanie należności i zobowiązań](#8-wiekowanie-należności-i-zobowiązań)
9. [Raport podatkowy](#9-raport-podatkowy)
10. [Audyt dzienników](#10-audyt-dzienników)
11. [Wydruk zapisu księgowego](#11-wydruk-zapisu-księgowego)
12. [Ekrany pozycji dziennika](#12-ekrany-pozycji-dziennika)
13. [Znane ograniczenia](#13-znane-ograniczenia)
14. [Dla programistów: stabilny kontrakt](#14-dla-programistów-stabilny-kontrakt)

---

## 1. Co robi ten moduł

Moduł dodaje sześć klasycznych księgowych wydruków audytowych, o które proszą audytorzy i księgowi, w postaci zwykłych dokumentów PDF, a także dwa gotowe ekrany pozycji dziennika.

| Raport | Na co odpowiada |
|---|---|
| Księga główna | Jakie były obroty na każdym koncie, z saldem narastającym |
| Księga kontrahentów | Jakie były obroty na kontach klientów i dostawców i ile jeszcze są winni |
| Wiekowanie należności i zobowiązań | Jak bardzo przeterminowana jest każda otwarta pozycja, w przedziałach wiekowych |
| Raport podatkowy | Kwoty netto i podatku dla każdego podatku, w podziale na Sprzedaż i Zakupy |
| Audyt dzienników | Każda pozycja wybranych dzienników wraz z podsumowaniem podatków |
| Zapis księgowy | Jedna strona na zapis, do podpięcia pod dokument |

Wszystkie raporty czytają pozycje dziennika wyłącznie przez ORM Odoo. Moduł nie zapisuje niczego poza własnymi rekordami okien dialogowych i nie dodaje żadnego pola do modeli standardowych.

## 2. Instalacja

1. Skopiuj katalog `odomate_account_ledger_reports` do swojej ścieżki addons.
2. **Aplikacje → Aktualizuj listę aplikacji**.
3. Wyszukaj *Accounting Audit Reports* i kliknij **Aktywuj**.

Jedyne zależności to `account` i `analytic` — oba są częścią Odoo Community. Po instalacji nie trzeba nic konfigurować: nie ma strony ustawień, zadania cyklicznego ani danych demonstracyjnych.

## 3. Kto może korzystać

Okna dialogowe mogą otwierać i drukować trzy istniejące grupy księgowe Odoo:

- `account.group_account_manager` — administrator fakturowania
- `account.group_account_user` — księgowy
- `account.group_account_readonly` — dostęp do księgowości tylko do odczytu

Moduł nie tworzy własnych grup i nie przyznaje niczego innym grupom. Użytkownik spoza tych trzech grup przy próbie wydruku otrzyma komunikat `Tylko użytkownicy księgowości mogą drukować raporty księgowe.` i w ogóle nie zobaczy menu.

Każdy rekord okna dialogowego jest rekordem przejściowym (kreatorem): trzy grupy dostają odczyt, zapis i tworzenie, nikt nie dostaje usuwania — sprzątaniem zajmuje się własny mechanizm Odoo.

## 4. Gdzie znaleźć raporty

| Raport | Ścieżka w menu |
|---|---|
| Księga główna | Księgowość → Raportowanie → Raporty audytowe → Księga główna |
| Audyt dzienników | Księgowość → Raportowanie → Raporty audytowe → Audyt dzienników |
| Księga kontrahentów | Księgowość → Raportowanie → Raporty kontrahentów → Księga kontrahentów |
| Wiekowanie należności i zobowiązań | Księgowość → Raportowanie → Raporty kontrahentów → Wiekowanie należności i zobowiązań |
| Wiekowanie należności | Księgowość → Raportowanie → Raporty kontrahentów → Wiekowanie należności |
| Wiekowanie zobowiązań | Księgowość → Raportowanie → Raporty kontrahentów → Wiekowanie zobowiązań |
| Raport podatkowy | Księgowość → Raportowanie → Podatki → Raport podatkowy |
| Pozycje dziennika wg konta | Księgowość → Raportowanie → Zarządzanie → Pozycje dziennika wg konta |
| Pozycje dziennika wg kontrahenta | Księgowość → Raportowanie → Zarządzanie → Pozycje dziennika wg kontrahenta |

*Wiekowanie należności* i *Wiekowanie zobowiązań* to to samo okno co *Wiekowanie należności i zobowiązań*, tylko z wybranym z góry i ukrytym typem konta.

Wydruk zapisu nie ma pozycji w menu: zaznacz jeden lub więcej zapisów w **Księgowość → Księgowość → Zapisy księgowe** i użyj **Drukuj → Zapis księgowy**.

## 5. Wspólny filtr

Każde okno zaczyna się od tego samego zestawu czterech pól.

| Pole | Znaczenie |
|---|---|
| **Zapisy** | *Tylko zaksięgowane zapisy* (domyślnie) lub *Wszystkie zapisy*. Zapisy anulowane nigdy nie są uwzględniane. |
| **Data początkowa** / **Data końcowa** | Ograniczają pozycje dziennika według ich daty księgowania. Zostaw oba puste dla „wszystkich dat”, jeśli okno na to pozwala. |
| **Dzienniki** | Zostaw puste, aby objąć wszystkie dzienniki firmy. |
| **Firma** | Widoczne tylko w bazach wielofirmowych. Domyślnie Twoja aktywna firma. |

Naciśnij **Drukuj**, aby utworzyć PDF, lub **Anuluj**, aby zamknąć.

Okno odmówi wydruku i wyjaśni dlaczego, gdy:

- wybrana firma nie należy do tych, w których wolno Ci pracować;
- data początkowa jest późniejsza niż końcowa;
- wybrany dziennik należy do innej firmy.

## 6. Księga główna

**Pola dodatkowe:** Konta, Kontrahenci, Konta analityczne (tylko z *Księgowością analityczną*), Sortuj według, Pokaż konta, Uwzględnij bilans otwarcia.

**Kolumny:** Data · Dziennik · Kontrahent · Odnośnik · Zapis · Opis · Winien · Ma · Saldo, a także Waluta (dla użytkowników wielowalutowych, tylko gdy waluta pozycji różni się od waluty firmy) i Analityka (dla użytkowników księgowości analitycznej).

**Pokaż konta**

- *Wszystkie konta* — każde konto firmy, nawet bez obrotów.
- *Z obrotami* (domyślnie) — konta z pozycjami w okresie lub z niezerowym bilansem otwarcia.
- *Z saldem różnym od zera* — pomija konta, w których otwarcie + Winien − Ma zaokrągla się do zera.

**Sortuj według** zmienia kolejność wewnątrz konta: *Data* — według daty, numeru zapisu, id; *Dziennik i kontrahent* — według dziennika, potem kontrahenta, potem daty.

### Przykład liczbowy — bilans otwarcia

Księgi firmy, rok obrotowy = kalendarzowy, data początkowa **2024-03-01**, zaznaczone **Uwzględnij bilans otwarcia**.

| Zapis | Data | Konto 121000 (Należności) | Konto 400000 (Przychody) |
|---|---|---|---|
| E1 | 2023-06-15 | Winien 1 000,00 | Ma 1 000,00 |
| E2 | 2024-02-10 | Winien 500,00 | Ma 500,00 |
| E3 | 2024-03-15 | Winien 250,00 | Ma 250,00 |

Wydrukowane otwarcia:

- **121000** to konto bilansowe, więc otwiera się *wszystkim*, co zaksięgowano przed datą początkową: 1 000,00 + 500,00 = **1 500,00**.
- **400000** to konto wynikowe, więc otwiera się tylko bieżącym rokiem obrotowym: E1 przypada na poprzedni rok i zostaje pominięty, zostaje **−500,00**.

Saldo narastające konta 121000 pokaże 1 500,00 w wierszu *Bilans otwarcia* i 1 750,00 po E3; wiersz podsumowania konta: Winien 250,00, Ma 0,00, Saldo 1 750,00.

## 7. Księga kontrahentów

**Pola dodatkowe:** Kontrahenci, Typ konta, Uwzględnij rozliczone pozycje, Pokaż kwotę w walucie (dla użytkowników wielowalutowych).

**Typ konta** odpowiada typom kont Odoo: *Konta należności* → `asset_receivable`, *Konta zobowiązań* → `liability_payable`, *Konta należności i zobowiązań* → oba.

**Kolumny:** Data · Dziennik · Konto · Zapis · Odnośnik · Opis · Winien · Ma · Saldo (liczone od zera dla każdego kontrahenta), a także Waluta.

Każdy blok kontrahenta kończy się sumami Winien, Ma, saldem końcowym oraz **Kwotą do zapłaty** — sumą kwot pozostających do rozliczenia.

Pozycja jest ukryta, dopóki nie zaznaczysz **Uwzględnij rozliczone pozycje**, tylko wtedy, gdy jest rozliczona *w całości* — czyli gdy wszystkie pozycje po drugiej stronie jej rozliczenia również zostały dopasowane i nic nie pozostaje do zapłaty. Częściowo opłacona faktura nadal drukuje zarówno swój własny wiersz, jak i wiersz swojej płatności, dopóki to nie nastąpi, dzięki czemu saldo końcowe zawsze pokazuje kwotę wciąż pozostającą do zapłaty; w pełni opłacona faktura i jej płatność znikają razem i pojawiają się razem ponownie po zaznaczeniu **Uwzględnij rozliczone pozycje**. Pozycje bez kontrahenta nigdy nie są tu drukowane — ich miejsce jest w Księdze głównej.

Raport można też wydrukować prosto z kontaktu: zaznacz jeden lub więcej kontaktów w **Kontaktach**, następnie **Drukuj → Księga kontrahentów**. Okno otworzy się z tymi kontrahentami, typem konta *Konta należności i zobowiązań* oraz włączonymi pozycjami rozliczonymi.

### Przykład liczbowy — częściowo opłacona faktura zachowuje płatność w osobnym wierszu

Faktura sprzedaży na 1 000,00 zostaje zaksięgowana, a następnie częściowo opłacona kwotą 400,00. Wydrukowana z odznaczonym **Uwzględnij rozliczone pozycje**:

| Wiersz | Winien | Ma | Saldo |
|---|---|---|---|
| Faktura | 1 000,00 | | 1 000,00 |
| Płatność | | 400,00 | 600,00 |
| **Suma kontrahenta** | **1 000,00** | **400,00** | **600,00** |

**Kwota do zapłaty** również pokazuje 600,00 — oba wiersze są drukowane, ponieważ 600,00 wciąż pozostaje do zapłaty po stronie faktury, mimo że sama płatność nie ma już nic do dopasowania. Gdy faktura zostanie opłacona w całości, oba wiersze znikną z widoku bez zaznaczenia i pojawią się razem ponownie dopiero po zaznaczeniu **Uwzględnij rozliczone pozycje**.

## 8. Wiekowanie należności i zobowiązań

**Pola dodatkowe:** Na dzień (wymagane, domyślnie dziś), Długość okresu (dni) (wymagane, domyślnie 30), Typ konta, Kontrahenci. Data początkowa i Dzienniki nie są używane w tym raporcie i są ukryte.

Każda otwarta pozycja trafia do jednej z sześciu kolumn według swojego wieku w pełnych dniach, gdzie wiek = *Na dzień* − (termin płatności lub data księgowania, gdy terminu brak):

| Kolumna | Wiek (P = Długość okresu) |
|---|---|
| Nieprzeterminowane | wiek ≤ 0 |
| 1 - P | 1 … P |
| P+1 - 2P | P+1 … 2P |
| 2P+1 - 3P | 2P+1 … 3P |
| 3P+1 - 4P | 3P+1 … 4P |
| +4P | wiek > 4P |

Wiersz, w którym wszystkie sześć kolumn jest zerowych, zostaje pominięty. Pozycje bez kontrahenta są grupowane w wierszu **Nieznany kontrahent**. Wszystkie kwoty są w walucie firmy; nie stosuje się żadnego przeliczenia.

### Przykład liczbowy — przedziały przy P = 30, na dzień 2024-06-30

| Pozycja | Termin płatności | Wiek | Kwota | Kolumna |
|---|---|---|---|---|
| A | 2024-06-30 | 0 | 10,00 | Nieprzeterminowane |
| B | 2024-06-29 | 1 | 20,00 | 1 - 30 |
| C | 2024-05-31 | 30 | 30,00 | 1 - 30 |
| D | 2024-05-30 | 31 | 40,00 | 31 - 60 |
| E | 2024-03-01 | 121 | 50,00 | +120 |

Wydrukowany wiersz: Nieprzeterminowane 10,00 · 1-30 50,00 · 31-60 40,00 · 61-90 0,00 · 91-120 0,00 · +120 50,00 · Razem 150,00.

### Przykład liczbowy — kwota pozostała liczona *na dany dzień*

Faktura na 1 000,00 zaksięgowana 2024-03-10, częściowo opłacona kwotą 400,00 dnia 2024-05-20.

- Na dzień **2024-04-30** płatności jeszcze nie było, więc raport pokazuje **1 000,00**.
- Na dzień **2024-06-30** pokazuje **600,00**, a sam wiersz płatności zeruje się i znika.

Raport przelicza kwotę pozostałą z historii rozliczeń zamiast czytać dzisiejszą wartość `amount_residual` — właśnie to sprawia, że wiekowanie wstecz jest poprawne.

## 9. Raport podatkowy

Stosuje się tylko wspólny filtr; Data początkowa i Data końcowa są wymagane i domyślnie wskazują pierwszy dzień bieżącego miesiąca oraz dzisiaj.

Raport wymienia wszystkie aktywne podatki sprzedaży i zakupu firmy w dwóch sekcjach. Grupa podatków jest reprezentowana przez swoje podatki podrzędne pod typem podatku nadrzędnego; sama grupa nie jest wierszem. Dla każdego podatku:

- **Kwota netto** — suma sald pozycji objętych tym podatkiem.
- **Kwota podatku** — suma sald wierszy podatkowych wygenerowanych przez ten podatek.

W sekcji **Sprzedaż** obie wartości zmieniają znak, aby przychód był dodatni; w sekcji **Zakupy** są drukowane tak, jak zaksięgowano. Moduł nigdy nie bierze wartości bezwzględnej, więc korekty faktycznie zmniejszają wartości. Wiersze zerowe w obu wartościach są pomijane, a pusta sekcja drukuje *Brak obrotów podatkowych w tym okresie.*

### Przykład liczbowy — korekta zmniejsza wartości sprzedaży

Marzec 2024, jeden podatek sprzedaży 20 %:

| Dokument | Netto | Podatek |
|---|---|---|
| Faktura sprzedaży, 1 000,00 + 20 % | 1 000,00 | 200,00 |
| Korekta, 400,00 + 20 % | −400,00 | −80,00 |
| **Wydrukowany wiersz „Sprzedaż”** | **600,00** | **120,00** |

## 10. Audyt dzienników

**Pola dodatkowe:** Dzienniki (wymagane — domyślnie dzienniki sprzedaży i zakupu Twojej firmy), Sortuj zapisy według, Pokaż kwotę w walucie.

Jedna sekcja na każdy wybrany dziennik, we własnej kolejności dzienników. **Kolumny:** Zapis · Data · Konto · Kontrahent · Opis · Winien · Ma, a także Waluta. Każda sekcja kończy się sumami Winien i Ma dziennika.

Gdy dziennik zawiera pozycje z podatkiem, poniżej pojawia się mała tabela Podatek / Podstawa opodatkowania / Kwota podatku z tą samą regułą znaków co w Raporcie podatkowym (podatki sprzedaży ze zmienionym znakiem). Dzienniki bez pozycji opodatkowanych takiej tabeli nie mają.

## 11. Wydruk zapisu księgowego

Brak okna dialogowego: zaznacz zapisy i użyj **Drukuj → Zapis księgowy**. Jedna strona na zapis, każdy drukowany z papierem firmowym i walutą własnej firmy.

Nagłówek pokazuje numer zapisu, dziennik, datę, kontrahenta, odnośnik i status. Tabela pozycji pokazuje Konto · Opis · Kontrahent · Analityka · Winien · Ma · Waluta, we własnej kolejności wierszy zapisu, z pominięciem wierszy sekcji, podsekcji i notatek. Wiersz sumy sumuje Winien i Ma w walucie firmy zapisu — dla każdego zaksięgowanego zapisu są równe.

## 12. Ekrany pozycji dziennika

Dwa zapisane widoki na `account.move.line`, oba w trybie lista / tabela przestawna / wykres ze standardowym panelem wyszukiwania pozycji dziennika Odoo, oba bez wierszy sekcji, podsekcji i notatek:

- **Pozycje dziennika wg konta** — pogrupowane według konta, tylko zapisy zaksięgowane.
- **Pozycje dziennika wg kontrahenta** — pogrupowane według kontrahenta, zapisy zaksięgowane, z filtrami należności handlowych, zobowiązań handlowych i pozycji nierozliczonych.

To zwykłe listy Odoo: można je przegrupować, filtrować, eksportować i przechodzić stamtąd do zapisu.

## 13. Znane ograniczenia

- **Tylko waluta firmy.** Każda liczba to kwota w walucie firmy. Opcjonalna kolumna Waluta pokazuje własną kwotę obcą pozycji informacyjnie; nic nie jest przeliczane.
- **Brak eksportu do Excela.** Raporty są tylko w PDF. Do pracy w arkuszu użyj dwóch ekranów pozycji dziennika.
- **Wiekowanie ignoruje dzienniki.** Z założenia obejmuje wszystkie dzienniki firmy; pole Dzienniki jest w tym oknie ukryte.
- **Brak przejścia do danych.** PDF to dokumenty statyczne, nie linkują z powrotem do Odoo.
- **`account.report` bez zmian.** Moduł nie rozszerza dynamicznego silnika raportów Odoo, więc te raporty nie pojawiają się w jego przełączniku wariantów.
- **Zakres raportu podatkowego.** Wymieniane są tylko podatki z `type_tax_use` równym `sale` lub `purchase`; podatki *None* nigdy się nie pojawiają.
- **Kolumna „Analityka”.** Informacja analityczna czytana jest z `analytic_distribution`; pokazane procenty to procenty rozdziału, a nie kwoty.

## 14. Dla programistów: stabilny kontrakt

Moduły pokrewne mogą polegać na poniższym — to się nie zmieni:

**Model** `odomate.account.report.filter` (konkretny `TransientModel`, baza dla dziedziczenia prototypowego) z polami `company_id`, `date_from`, `date_to`, `journal_ids`, `target_move` i metodami:

| Element | Rodzaj | Przeznaczenie |
|---|---|---|
| `_odomate_journals()` | rekord | Wybrane dzienniki albo wszystkie dzienniki firmy |
| `_odomate_state_domain()` | rekord | Warunek stanu dla wybranego `target_move` |
| `_odomate_line_domain(date_field='date', date_from=None, date_to=None)` | rekord | Bazowa domena pozycji dziennika |
| `_odomate_check_filter()` | rekord | Walidacja; rozszerzaj przez `super()` |
| `_odomate_report_data()` | rekord | Ładunek zawierający wyłącznie typy proste |
| `_odomate_print(report_xmlid=None)` | rekord | Sprawdź i zwróć akcję raportu |
| `action_odomate_print()` | rekord | Przycisk „Drukuj” w oknie |
| `_odomate_report_xmlid` | atrybut klasy | Domyślny XML ID raportu okna |
| `_odomate_options_from_data(data)` | model | Parsowanie ładunku z powrotem na rekordy i daty |
| `_odomate_check_report_access()` | model | Zgłasza `AccessError` poza trzema grupami księgowymi |
| `_odomate_initial_balance_domain(company, date_from, journals=None, target_move='posted')` | model | Domena bilansu otwarcia |

**Widok** `odomate_account_ledger_reports.view_odomate_account_report_filter_form` — dziedzicz z `mode="primary"` i dodawaj własne pola po węźle `journal_ids` lub po węźle `target_move`. To jedyne dwa obsługiwane miejsca.

**QWeb** `odomate_account_ledger_reports.report_filter_header` — parametry `company`, `date_from`, `date_to`, `journals`, `target_move_label`.

**Format papieru** `odomate_account_ledger_reports.paperformat_odomate_ledger_landscape` — A4 poziomo, marginesy 10 mm.

**Menu** `odomate_account_ledger_reports.menu_odomate_account_reports_audit` — folder *Raporty audytowe*.

Wszystko pozostałe — pola poszczególnych okien, metody pomocnicze budujące wiersze, nazwy modeli raportów, brzmienie szablonów, kolejność kluczy w słownikach — jest wewnętrzne i może się zmienić.

---

© OdoMate · <https://odomate.pro> · <support@odomate.pro>
