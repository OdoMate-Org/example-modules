# Podręcznik użytkownika: Audit Log (dziennik audytu)

> Rejestruje, kto utworzył, zmienił, usunął, odczytał lub wyeksportował które rekordy w Odoo, wraz ze starą i nową wartością każdego zmienionego pola.

---

## Spis treści

1. [Co robi ten moduł](#1-co-robi-ten-moduł)
2. [Gdzie znaleźć moduł w Odoo](#2-gdzie-znaleźć-moduł-w-odoo)
3. [Pierwsza konfiguracja: tworzenie reguły audytu](#3-pierwsza-konfiguracja-tworzenie-reguły-audytu)
4. [Przeglądanie dzienników](#4-przeglądanie-dzienników)
5. [Główne scenariusze](#5-główne-scenariusze)
6. [Pełny dziennik a szybki dziennik](#6-pełny-dziennik-a-szybki-dziennik)
7. [Polityka błędów, wiele firm i retencja](#7-polityka-błędów-wiele-firm-i-retencja)
8. [Dane demonstracyjne](#8-dane-demonstracyjne)
9. [Role dostępu](#9-role-dostępu)
10. [Ograniczenia](#10-ograniczenia)

---

## 1. Co robi ten moduł

Audit Log prowadzi historię operacji na wybranych przez Ciebie modelach Odoo. Tworzysz jedną **regułę** na model (np. *Contact* — Kontakt), wybierasz operacje do śledzenia i zatwierdzasz regułę. Od tej chwili każda śledzona operacja tworzy **dziennik** (kto, kiedy, który rekord, jaka operacja) z jednym **wierszem dziennika** na każde zmienione pole, pokazującym starą i nową wartość. Audytorzy, administratorzy i działy compliance używają go, aby odpowiedzieć na pytanie „kto to zmienił i jak było wcześniej?”.

| Funkcja | Szczegóły |
|---|---|
| Reguły audytu dla modeli | Jedna reguła na model (`auditlog.rule`); druga reguła dla tego samego modelu jest odrzucana komunikatem „There is already a rule defined on this model.” |
| Śledzone operacje | Tworzenie, zapis, usuwanie, odczyt i eksport — każdą można włączyć osobno |
| Historia na poziomie pól | Każdy wiersz dziennika przechowuje etykietę pola, nazwę techniczną oraz surową i czytelną starą/nową wartość |
| Czytelne wartości relacji | Wartości Many2one oraz many2many/one2many są pokazywane jako nazwy rekordów; nieistniejący już rekord pokazywany jest jako `<id> (DELETED)` |
| Migawka usuniętego rekordu | Z opcją **Capture Record** dziennik usunięcia zachowuje wszystkie wartości pól rekordu tuż przed usunięciem |
| Śledzenie eksportu | Jeden dziennik na eksport z listą identyfikatorów wyeksportowanych rekordów i inteligentnym przyciskiem **Exported Records**, który ponownie je otwiera |
| Wykluczenia | Dla każdej reguły: wykluczeni użytkownicy (np. integracyjni) i wykluczone pola (np. notatki) |
| Ślad sesji i żądań | Każdy dziennik jest powiązany z sesją użytkownika i żądaniem HTTP (ścieżka URL), które go wywołały |
| Izolacja między firmami | Dziennik otrzymuje firmę audytowanego rekordu; użytkownicy widzą tylko dzienniki dozwolonych firm |
| Retencja | Opcjonalna zaplanowana akcja usuwa dane audytu starsze niż 180 dni |
| Skrót „View logs” | Zatwierdzenie reguły dodaje akcję **View logs** (Pokaż dzienniki) do formularza audytowanego modelu (menu Akcje) |

---

## 2. Gdzie znaleźć moduł w Odoo

Moduł znajduje się w ustawieniach technicznych, więc **tryb deweloperski musi być włączony** (Settings → Activate the developer mode). Menu nadrzędne **Audit** widzą tylko administratorzy ustawień (`base.group_system`).

**Ścieżka:** `Settings` → `Technical` → `Audit` (Ustawienia → Techniczne → Audyt)

| Menu | Przeznaczenie | Kto widzi |
|---|---|---|
| **Rules** (Reguły) | Tworzenie, zatwierdzanie i przywracanie do wersji roboczej reguł audytu | Auditlog User (odczyt), Auditlog Manager (edycja) |
| **Logs** (Dzienniki) | Jeden wiersz na każdą audytowaną operację; otwórz, aby zobaczyć zmiany pól | Auditlog User i wyżej |
| **Log Lines** (Wiersze dziennika) | Płaska lista wszystkich zmian pól ze wszystkich dzienników, wyszukiwanie po starej/nowej wartości | Tylko **Access Rights** (`base.group_erp_manager`) |
| **User sessions** (Sesje użytkowników) | Sesje logowania, które utworzyły dzienniki, wraz z ich żądaniami HTTP | Auditlog User i wyżej |
| **HTTP Requests** (Żądania HTTP) | Pojedyncze żądania (ścieżka URL + główny URL) i utworzone przez nie dzienniki | Auditlog User i wyżej |
| **Delete Old Logs** (Usuń stare logi) | Okno, które od razu usuwa stare dane audytu (patrz sekcja 7, Retencja) | Auditlog Manager |

Dodatkowo w formularzu każdego audytowanego modelu (np. kontaktu) pozycja **Actions (koło zębate) → View logs** pokazuje dzienniki tylko tego rekordu.

W formularzu reguły inteligentny przycisk **Logs** (Logi; w prawym górnym rogu, np. **29 Logi**) otwiera wszystkie dzienniki modelu tej reguły.

---

## 3. Pierwsza konfiguracja: tworzenie reguły audytu

> ⚠️ Nic nie jest rejestrowane, dopóki co najmniej jedna reguła nie ma stanu **Confirmed** (Zatwierdzona).

**Ścieżka:** `Settings` → `Technical` → `Audit` → `Rules` → `New`

| Pole | Co wpisać | Przykład |
|---|---|---|
| **Name** (Nazwa) | Dowolna etykieta reguły | `Partner audit trail` |
| **Model** | Model do audytu. Modeli przejściowych (transient) ani samych modeli `auditlog.*` nie można wybrać | `Contact` (`res.partner`) |
| **Type** (Typ) | **Full log** (Pełny dziennik, domyślnie) lub **Fast log** (Szybki dziennik) — zob. [sekcja 6](#6-pełny-dziennik-a-szybki-dziennik) | Full log |
| **On Logging Failure** (W razie błędu zapisu dziennika) | **Block the operation** (Zablokuj operację, domyślnie) lub **Skip the log** (Pomiń wpis) — zob. [sekcja 7](#7-polityka-błędów-wiele-firm-i-retencja) | Block the operation |
| **Log Creates** | Śledź tworzenie rekordów (domyślnie włączone) | ✅ |
| **Log Writes** | Śledź modyfikacje (domyślnie włączone) | ✅ |
| **Log Deletes** | Śledź usuwanie (domyślnie włączone) | ✅ |
| **Log Reads** | Śledź każdy odczyt/otwarcie rekordu (domyślnie wyłączone — kosztowne) | ❌ |
| **Log Exports** | Śledź eksporty (domyślnie włączone) | ✅ |
| **Capture Record** | Przy usuwaniu zachowaj pełną migawkę wartości usuwanego rekordu | ✅ |
| **Users to Exclude** (zakładka, Wykluczeni użytkownicy) | Użytkownicy, których operacje nigdy nie są rejestrowane | `OdooBot`, użytkownik integracji API |
| **Fields to Exclude** (zakładka, Wykluczone pola) | Pola wybranego modelu, które nigdy nie tworzą wiersza dziennika | `Notes` (`comment`) |

Następnie kliknij **Confirm** (Zatwierdź). Pasek statusu przechodzi z **Draft** (Wersja robocza) do **Confirmed**, utworzona akcja „View logs” zostaje podpięta do formularza modelu (jej rekord techniczny pole **Action** pokazuje tylko w trybie deweloperskim), a audyt zaczyna się natychmiast. Przycisk **Logs** prowadzi do dzienników reguły.

**Przepływ statusów:** Draft → Confirmed (→ Set to Draft → Draft)

> 💡 Po zatwierdzeniu reguły wszystkie jej pola konfiguracyjne są tylko do odczytu. Aby zmienić operacje, typ lub wykluczenia, kliknij **Set to Draft** (Przywróć do wersji roboczej), wprowadź zmiany i ponownie kliknij **Confirm**. Gdy reguła jest w wersji roboczej, dla tego modelu nic nie jest rejestrowane, a akcja „View logs” znika z formularza modelu; ponowne zatwierdzenie używa tej samej akcji.

---

## 4. Przeglądanie dzienników

**Ścieżka:** `Settings` → `Technical` → `Audit` → `Logs`

Lista pokazuje **Date** (Data), **Resource Name** (Nazwa zasobu), **Model**, **Method** (Metoda: `create`, `write`, `unlink`, `read`, `export_data`) i **User** (Użytkownik). Kolumny opcjonalne: Resource ID, Type oraz (dla użytkowników wielofirmowych) Company.

Filtry: **Create**, **Write**, **Delete**, **Read**, **Export**. Grupowanie: **User**, **Model**, **Method**, **Company**, **Date**.

Otwarty dziennik zawiera:

| Obszar | Zawartość |
|---|---|
| Grupa **Log** | Data, użytkownik, metoda, typ, firma (tylko w trybie wielofirmowym) |
| Grupa **Resource** | Nazwa zasobu, model, techniczna nazwa modelu, ID zasobu, Resource IDs (tylko eksporty) |
| Zakładka **Fields updated** (Zaktualizowane pola) | Jeden wiersz na pole: Description (Opis), Old value Text (Stara wartość), New value Text (Nowa wartość); surowe wartości i nazwa techniczna dostępne jako kolumny opcjonalne |
| Zakładka **Technical** (Techniczne) | Sesja i żądanie HTTP, które utworzyły dziennik |
| Inteligentny przycisk **Exported Records** | Tylko w dziennikach eksportu: otwiera wyeksportowane rekordy (czytelny komunikat błędu, jeśli model został odinstalowany) |

Dzienniki, sesje i żądania są w interfejsie tylko do odczytu (brak przycisków tworzenia/edycji).

**Log Lines** (`Settings` → `Technical` → `Audit` → `Log Lines`) to płaski widok wszystkich zmian pól tylko do odczytu, przydatny przy pytaniach typu „kto kiedykolwiek ustawił ten adres e-mail?”. Szukaj po **Old value Text** / **New value Text**, filtruj po Create/Write/Delete i grupuj po User, Model, **Field** (Pole) lub Company.

---

## 5. Główne scenariusze

### Scenariusz 1: Sprawdź, kto zmienił nazwę klienta (przykład)

Konfiguracja: reguła *Partner audit trail* dla `Contact`, Full log, włączone Log Writes, stan Confirmed.

1. Handlowiec otwiera kontakt **Azure Interior**, zmienia **Name** na `Azure Interior SA` i zapisuje.
2. Powstaje dokładnie **jeden** dziennik `write`:

   | Pole dziennika | Wartość |
   |---|---|
   | Resource Name | Azure Interior SA |
   | Model | Contact |
   | Method | write |
   | User | handlowiec |
   | Type | Full log |

3. Zakładka **Fields updated** zawiera jeden wiersz na każde zmienione pole — tu jest to pole edytowane przez użytkownika:

   | Description | Old value Text | New value Text |
   |---|---|---|
   | Name | Azure Interior | Azure Interior SA |

   Ponieważ pełny dziennik porównuje wszystkie zapisane pola, zapisane pole obliczane, które zmienia się w konsekwencji (w kontaktach zwykle **Complete Name** — Pełna nazwa), dostaje własny wiersz z tymi samymi starymi/nowymi tekstami. Nic więcej nie jest wyświetlane.

4. Audytor znajduje dziennik przez **Logs** → filtr **Write** → wyszukiwanie `Azure` albo bezpośrednio z formularza kontaktu: **Actions → View logs**.

Pola, których wartość się nie zmieniła, nie tworzą wierszy; `create_date`, `write_date`, `create_uid`, `write_uid` i `display_name` nigdy nie są rejestrowane.

### Scenariusz 2: Zbadaj usunięty rekord

Przy włączonych **Log Deletes** i **Capture Record** usunięcie kontaktu tworzy dziennik `unlink`, którego zakładka **Fields updated** wymienia wszystkie zapisane pola z ich ostatnią wartością w **Old value Text**. Bez Capture Record dziennik `unlink` nadal rejestruje, kto usunął rekord o jakim ID, ale bez wierszy.

### Scenariusz 3: Sprawdź, co zostało wyeksportowane

Przy włączonym **Log Exports** każdy eksport (lista → zaznacz → Actions → Export) tworzy jeden dziennik `export_data`. Pole **Resource IDs** zawiera listę JSON wyeksportowanych ID; inteligentny przycisk **Exported Records** (np. „12 Exported Records”) ponownie otwiera dokładnie te rekordy. Wewnętrzne odczyty wykonywane przez eksport nie są rejestrowane osobno, więc eksport nie zalewa dziennika wpisami odczytu.

### Scenariusz 4: Wyklucz „hałaśliwego” użytkownika lub pole

Przywróć regułę do wersji roboczej, dodaj użytkownika w **Users to Exclude** lub pole w **Fields to Exclude** i kliknij Confirm. Od następnej operacji działania wykluczonego użytkownika nie są w ogóle rejestrowane, a wykluczone pole nigdy nie tworzy wiersza (inne pola zmienione w tym samym zapisie nadal są rejestrowane).

---

## 6. Pełny dziennik a szybki dziennik

| | **Full log** (Pełny, domyślnie) | **Fast log** (Szybki) |
|---|---|---|
| Co jest odczytywane | Wszystkie zapisane, niebinarne pola rekordu **przed i po** operacji | Nic dodatkowo — tylko wartości przekazane do create/write |
| Stare wartości przy zapisie | Rzeczywiste poprzednie wartości | Zawsze pokazywane jako `False` |
| Zmiany uboczne (zapisane pola obliczane) | Rejestrowane | Nierejestrowane |
| Koszt | Dwa dodatkowe odczyty na każdy zapis | Minimalny |
| Najlepsze dla | Compliance, modeli o małym/średnim wolumenie | Modeli o dużym wolumenie, gdy wystarczy wiedzieć „co zostało wysłane” |

**Przykład — ta sama zmiana nazwy z Fast log:** wiersz pokazuje **Old value Text** `False`, **New value Text** `Azure Interior SA`. Wiesz, co zapisano, ale nie wiesz, co zostało zastąpione.

Wspólne dla obu typów:
- Przy **tworzeniu** pola z pustymi wartościami początkowymi (pusty tekst, `False`, puste listy) są pomijane, więc nowy kontakt z samym Name i Email daje dwa wiersze, a nie czterdzieści.
- Pola binarne (obrazy, załączniki) nigdy nie są rejestrowane.
- Wartości relacji są pokazywane nazwami, np. Tags `VIP, Wholesale`; nieistniejący już tag pokazywany jest jako `7 (DELETED)`.

---

## 7. Polityka błędów, wiele firm i retencja

### On Logging Failure (W razie błędu zapisu dziennika)

| Ustawienie | Jeśli zapis rekordu audytu się nie powiedzie… | Kiedy używać |
|---|---|---|
| **Block the operation** (domyślnie) | Operacja użytkownika jest wycofywana, a użytkownik widzi błąd. Żadnej zmiany bez śladu. | Compliance wymaga gwarantowanego śladu |
| **Skip the log** | Operacja użytkownika zostaje wykonana; błąd trafia do logu serwera; **brak rekordu audytu** dla tej operacji | Ciągłość działania jest ważniejsza niż kompletność |

### Konfiguracja „na żywo”

Typ reguły, wykluczenia, Capture Record i polityka błędów są odczytywane z bazy danych przy **każdej** rejestrowanej operacji, więc zmiana działa natychmiast we wszystkich procesach roboczych serwera — restart nie jest potrzebny.

### Wiele firm

- Każdy dziennik przechowuje **firmę audytowanego rekordu** (jeśli model ma pole `company_id`); eksport otrzymuje firmę tylko wtedy, gdy wszystkie wyeksportowane rekordy należą do jednej firmy.
- Dzienniki, wiersze dziennika, widok Log Lines, sesje użytkowników i żądania HTTP są widoczne tylko wtedy, gdy ich firma należy do **dozwolonych firm** użytkownika lub gdy nie mają firmy (np. dzienniki modeli bez pola firmy).
- Same reguły są globalne: jedna reguła dla `Contact` audytuje kontakty wszystkich firm.
- Kolumna/filtr/grupowanie **Company** są ukryte dla użytkowników jednofirmowych i pojawiają się w trybie wielofirmowym.

**Przykład:** edytowany jest kontakt firmy *Auditlog Demo Company B*. Użytkownik, któremu dozwolona jest tylko firma główna, nie widzi tego dziennika w **Logs** ani **Log Lines**; użytkownik z dostępem do obu firm — widzi.

### Retencja (automatyczne czyszczenie)

**Ścieżka:** `Settings` → `Technical` → `Automation` → `Scheduled Actions` → **Auto-vacuum audit logs**

| Właściwość | Wartość |
|---|---|
| Stan po instalacji | **Nieaktywna** — nic nie jest usuwane, dopóki jej nie włączysz |
| Częstotliwość | Codziennie |
| Kod | `model.autovacuum(180)` — przechowuje 180 dni |
| Co jest usuwane | Dzienniki (z wierszami), żądania HTTP i sesje użytkowników starsze niż okres retencji, od najstarszych |

Aby przechowywać dane przez rok, zmień kod na `model.autovacuum(365)` i zaznacz **Active**. Czyszczenie mogą uruchamiać tylko Auditlog Manager.

**Uruchomienie od razu:** `Settings` → `Technical` → `Audit` → **Delete Old Logs** (Usuń stare logi) otwiera okno z polami **Keep Last (Days)** (Zachowaj ostatnie (dni), domyślnie `180`) i **Chunk Size** (Rozmiar partii, `0` = bez limitu; w innym przypadku maksymalna liczba rekordów usuwanych na model w tym uruchomieniu). Kliknij **Delete Old Logs**: powiadomienie potwierdza „Dane audytu starsze niż 180 dni zostały usunięte.” Przykład: przy wartości `90` w dniu 25.09.2026 usuwane są wszystkie dzienniki utworzone do 27.06.2026 włącznie (wraz z wierszami), a dzienniki od lipca pozostają.

### Sesje i żądania

- **User sessions**: **Session ID** to odcisk SHA-256 identyfikatora sesji HTTP, a nie sam identyfikator, więc nie da się go użyć do przejęcia sesji. Nazwa wyświetlana: `<użytkownik> (<data>)`.
- **HTTP Requests**: przechowuje **Path** (Ścieżka, np. `/web/dataset/call_kw/res.partner/web_save`), **Root URL**, użytkownika, sesję i powiązane dzienniki. Kontekst użytkownika nie jest przechowywany.
- Operacje wykonywane poza żądaniem HTTP (akcje zaplanowane, skrypty w powłoce) tworzą dzienniki bez sesji/żądania.

---

## 8. Dane demonstracyjne

Po instalacji z danymi demonstracyjnymi moduł udostępnia:

| Rekord | Szczegóły |
|---|---|
| Reguła **Partner audit trail** | Dla `Contact`, stan Confirmed, wyklucza pole **Notes** (`comment`) |
| Firma **Auditlog Demo Company B** | Druga firma do sprawdzenia widoczności między firmami |
| Użytkownik **audit_viewer** (hasło `audit_viewer`) | Auditlog User ograniczony do firmy głównej — zaloguj się, aby sprawdzić, że dzienniki Company B są ukryte |
| ~20 przykładowych dzienników | Mieszanka wpisów create/write/unlink do przetestowania filtrów i grupowania |

> ⚠️ Zmień hasło lub dezaktywuj użytkownika `audit_viewer` w każdej bazie dostępnej z zewnątrz.

---

## 9. Role dostępu

| Rola | Reguły | Dzienniki / wiersze / sesje / żądania | Menu Log Lines | Automatyczne czyszczenie |
|---|---|---|---|---|
| **Auditlog User** | ✅ Odczyt | ✅ Odczyt (dozwolone firmy) | ❌ (chyba że ma też Access Rights) | ❌ |
| **Auditlog Manager** (obejmuje User) | ✅ Odczyt, tworzenie, edycja, usuwanie, Confirm / Set to Draft | ✅ Pełny dostęp (dozwolone firmy) | ❌ (chyba że ma też Access Rights) | ✅ |
| **Access Rights** (`base.group_erp_manager`) | — | — | ✅ Odczyt | — |
| **Settings** (`base.group_system`) | Automatycznie Auditlog Manager | Automatycznie Auditlog Manager | ✅ (Settings obejmuje Access Rights) | ✅ |

Użytkownik admin otrzymuje rolę Auditlog Manager podczas instalacji. Ponieważ menu **Audit** znajduje się w **Settings → Technical**, aby dotrzeć do niego przez menu, potrzebne są rola Settings i tryb deweloperski.

Jak przypisać: `Settings` → `Users & Companies` → `Users` → wybierz użytkownika → pole **Auditlog Rights** na zakładce Access Rights.

---

## 10. Ograniczenia

| Temat | Ograniczenie |
|---|---|
| Technika implementacji | Moduł podmienia metody ORM (`create`, `write`, `unlink`, `read`, `export_data`) klas audytowanych modeli na poziomie rejestru — ta sama technika co w `base_automation` Odoo. W obrębie jednego wydania jest to niezawodne, ale przy każdej dużej aktualizacji Odoo zaplanuj przegląd/przepisanie. |
| Rejestrowanie odczytów | **Log Reads** tworzy jeden dziennik na każdy odczytany rekord przy każdym odczycie, w tym w widokach list i odczytach automatycznych. Na obciążonych modelach (kontakty, produkty) szybko powiększa to bazę i spowalnia interfejs. Włączaj tylko dla wrażliwych modeli o małym wolumenie. |
| Fast log | Nie pokazuje starych wartości (zawsze `False`) i nie rejestruje zmian ubocznych. |
| Widok Log Lines | Widok SQL tylko do odczytu; nie można go edytować ani z niego usuwać — czyszczony jest wyłącznie przez odpowiadające mu dzienniki. |
| Transakcje tylko do odczytu | Dzienniki powstałe podczas żądań tylko do odczytu (np. rejestrowanie odczytów) są zapisywane przez osobny kursor bazy danych, więc zostają zachowane, nawet jeśli samo żądanie później zakończy się błędem. |
| Bezpośredni SQL | Zmiany wykonane surowym SQL lub kodem omijającym metody ORM nie są rejestrowane. |
| Pola binarne | Obrazy i pliki nigdy nie są rejestrowane. |
| Zakres reguły | Jedna reguła na model; reguły nie można ograniczyć do firmy ani domeny rekordów; modeli `auditlog.*` i modeli przejściowych nie można audytować. |
| Edycja zatwierdzonej reguły | W stanie Confirmed konfiguracja jest tylko do odczytu; użyj Set to Draft → edycja → Confirm (w wersji roboczej nic nie jest rejestrowane). |
| Odporność na manipulacje | Auditlog Manager (a więc i administratorzy Settings) mogą usuwać dzienniki. Moduł to ślad audytowy, a nie kryptograficznie zabezpieczony rejestr. |
| Retencja | Automatyczne czyszczenie jest dostarczane jako nieaktywne; bez jego włączenia dzienniki rosną bez końca. |
| Integracje | Brak eksportu do SIEM lub zewnętrznych systemów logowania; brak raportów (PDF). |
