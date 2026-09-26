# Audit Trail — Podręcznik użytkownika

Audit Trail rejestruje, **kto, co, z którym obserwowanym rekordem i kiedy zrobił**, wraz z wartościami pól przed zmianą i po niej. Sam wybierasz, jakie rodzaje rekordów obserwować w każdej firmie, i świadomie włączasz obserwację. Po włączeniu zaplanowane czyszczenie może usuwać starą historię.

## Spis treści

1. [Przegląd](#1-przegląd)
2. [Instalacja](#2-instalacja)
3. [Role i dostęp](#3-role-i-dostęp)
4. [Konfiguracja](#4-konfiguracja)
5. [Codzienna praca](#5-codzienna-praca)
6. [Opis pól](#6-opis-pól)
7. [Zaplanowane czyszczenie](#7-zaplanowane-czyszczenie)
8. [Dane demonstracyjne](#8-dane-demonstracyjne)
9. [Ograniczenia](#9-ograniczenia)

## 1. Przegląd

| Ekran | Menu | Przeznaczenie |
|---|---|---|
| Reguły obserwacji (`audit.rule`) | Audyt → Konfiguracja → Reguły | Jaki rodzaj rekordu jest obserwowany, w której firmie, jakie działania i z jaką szczegółowością |
| Zarejestrowane zdarzenia (`audit.log`) | Audyt → Dzienniki | Jeden wiersz na utworzenie / zmianę / usunięcie / eksport / otwarcie listy |
| Zmiany pól (`audit.log.line`) | Audyt → Pozycje dziennika | Jeden wiersz na każde zmienione pole, wyszukiwanie we wszystkich obserwowanych rodzajach rekordów |
| Sesje robocze (`audit.session`) | Audyt → Sesje | Czas logowania, przeglądarka i adres sieciowy wizyty, w której powstały zdarzenia |

## 2. Instalacja

1. Otwórz **Aplikacje**, wyszukaj **Audit Trail** i kliknij **Aktywuj**.
2. Moduł zależy od `base`, `web`, `base_setup` i `product` (cenniki). Żadne inne aplikacje nie są instalowane.
3. Po instalacji administrator widzi menu **Audyt**. Administratorzy systemu automatycznie otrzymują rolę **Administrator audytu**.

## 3. Role i dostęp

| Rola | Reguły obserwacji | Zarejestrowane zdarzenia / Zmiany pól / Sesje |
|---|---|---|
| **Audytor** (`audit_trail.group_audit_user`) | Odczyt | Odczyt |
| **Administrator audytu** (`audit_trail.group_audit_manager`, obejmuje Audytora) | Odczyt, tworzenie, edycja, usuwanie | Odczyt i usuwanie (bez edycji) |

- Każdy rekord jest ograniczony do firm, w których użytkownik może pracować.
- Przycisk **Dzienniki** (View Logs) na formularzach kontaktów, kont bankowych i cenników widzą tylko audytorzy i administratorzy audytu.
- Menu **Reguły** wymaga roli administratora audytu, menu **Ustawienia** — roli administratora systemu Odoo.

## 4. Konfiguracja

### 4.1 Tworzenie reguły obserwacji

1. Przejdź do **Audyt → Konfiguracja → Reguły** i kliknij **Nowy**.
2. Wypełnij **Nazwa** (np. „Kontakty”) i **Rodzaj rekordu** (np. *Kontakt*). **Firma** domyślnie to Twoja bieżąca firma.
3. Wybierz **Poziom szczegółowości**:
   - **Pełny** — zachowuje stare i nowe wartości. Wolniejszy: cały rekord jest odczytywany ponownie przed każdą zmianą i po niej.
   - **Lekki** — zachowuje tylko nową wartość każdego zmienionego pola. Szybszy, ale stara wartość przepada.
4. Na karcie **Działania do rejestrowania** zaznacz: **Rejestruj tworzenie**, **Rejestruj zmiany**, **Rejestruj usuwanie**, **Rejestruj eksporty**, **Rejestruj otwarcia list**.
   - **Rejestruj otwarcia list** jest domyślnie wyłączone. Każda lista z więcej niż jednym obserwowanym rekordem tworzy zdarzenie, co może oznaczać tysiące wierszy dziennie. Pojedynczy rekord otwarty osobno nigdy nie jest rejestrowany.
5. **Zachowaj kopię przy usunięciu** zapisuje pełną zawartość każdego usuniętego rekordu (dodatkowe miejsce w bazie danych).
6. Na karcie **Wykluczenia** wskaż **Wykluczone osoby** i **Wykluczone pola**.
7. Kliknij **Potwierdź**. Reguła staje się **Aktywna** i rejestrowanie się rozpoczyna.

Dla jednego rodzaju rekordu w jednej firmie dozwolona jest tylko jedna reguła. Druga zostanie odrzucona z komunikatem wskazującym istniejącą regułę.

### 4.2 Zmiana reguły

Gdy reguła jest **Aktywna**, jej ustawienia obserwacji są zablokowane (informuje o tym niebieski baner). Kliknij **Przywróć do projektu**, zmień ustawienia i ponownie kliknij **Potwierdź**. W stanie projektu nic nie jest rejestrowane. Aktywnej reguły nie można usunąć — najpierw przywróć ją do projektu.

## 5. Codzienna praca

### 5.1 Zarejestrowane zdarzenia

**Audyt → Dzienniki** pokazuje zdarzenia z datą, rekordem, rodzajem rekordu, działaniem i użytkownikiem. Grupuj według użytkownika, rodzaju rekordu, działania, daty lub sesji roboczej i korzystaj z filtrów **Utworzenia, Zmiany, Usunięcia, Eksporty, Otwarcia list**.

Formularz zdarzenia pokazuje, kto, kiedy, z którym rekordem i jakie działanie wykonał, poziom szczegółowości oraz tabelę **Zmiany pól** (pole, stara wartość, nowa wartość). Przyciski:

- **Otwórz rekord** — otwiera obserwowany rekord (ukryty dla usunięć, eksportów i otwarć list). Jeśli rekord został w międzyczasie usunięty, zamiast tego pojawia się powiadomienie z ostrzeżeniem.
- **Pokaż wyeksportowane rekordy** — tylko dla zdarzeń eksportu; otwiera dokładnie te rekordy, które wyeksportowano.
- Karta **Zawartość usuniętego rekordu** pojawia się przy zdarzeniach usunięcia, jeśli zachowano kopię.

### 5.2 Przykład

Reguła „Kontakty”, pełna szczegółowość, aktywna. Użytkownik zmienia telefon *Deco Addict* z `(603)-996-3829` na `(603)-996-4100`:

| Pole | Stara wartość | Nowa wartość |
|---|---|---|
| Telefon | (603)-996-3829 | (603)-996-4100 |

Przy szczegółowości **Lekki** ta sama zmiana zapisuje pustą **Starą wartość** i **Nową wartość** `(603)-996-4100`. Jeśli użytkownik zapisze rekord bez zmian, zdarzenie nie jest tworzone.

### 5.3 Zmiany pól

**Audyt → Pozycje dziennika** to płaska lista wszystkich zmienionych pól we wszystkich obserwowanych rodzajach rekordów. Szukaj według rekordu, etykiety pola, starej lub nowej wartości, rodzaju rekordu albo użytkownika.

### 5.4 Z obserwowanego rekordu

Na formularzu kontaktu, konta bankowego lub cennika kliknij **Dzienniki**, aby zobaczyć historię tylko tego rekordu.

### 5.5 Sesje robocze

**Audyt → Sesje** pokazuje użytkownika, czas logowania, ostatnią aktywność, przeglądarkę, adres sieciowy i liczbę zarejestrowanych zdarzeń. Otwórz sesję, aby zobaczyć jej zdarzenia. Sesja powstaje, gdy zalogowana osoba po raz pierwszy wywoła rejestrowane zdarzenie, więc **Czas logowania** to czas pierwszego zdarzenia, a nie faktycznego logowania.

## 6. Opis pól

### Reguła obserwacji (`audit.rule`)

| Pole | Znaczenie |
|---|---|
| `name` | Nazwa reguły |
| `model_id` | Obserwowany rodzaj rekordu |
| `company_id` | Firma, której zmiany użytkowników są rejestrowane |
| `state` | Projekt / Aktywna |
| `detail_level` | Pełny / Lekki |
| `track_create`, `track_write`, `track_unlink`, `track_export`, `track_read` | Rejestrowane działania |
| `keep_deleted_copy` | Zapis zawartości usuniętego rekordu |
| `excluded_user_ids`, `excluded_field_ids` | Osoby i pola nigdy nierejestrowane |

### Zarejestrowane zdarzenie (`audit.log`)

`rule_id`, `res_model`, `res_id`, `record_name`, `action`, `user_id`, `date`, `detail_level`, `company_id`, `deleted_data`, `exported_res_ids`, `session_id`, `source_action`, `line_ids`.

### Zmiana pola (`audit.log.line`)

`log_id`, `field_id`, `field_description`, `old_value`, `new_value` oraz kopie tylko do odczytu do wyszukiwania: `date`, `user_id`, `record_name`, `res_model`, `res_id`, `action`, `company_id`, `session_id`.

## 7. Zaplanowane czyszczenie

1. Przejdź do **Audyt → Konfiguracja → Ustawienia** (lub **Ustawienia → Audit Trail**).
2. Zaznacz **Usuwaj starą historię** i ustaw **Przechowuj historię przez … miesięcy** (domyślnie 6).
3. Codzienne zadanie **Ścieżka audytu: usuwanie przeterminowanej historii** w jednym przebiegu usuwa do 1000 najstarszych zdarzeń firm, które włączyły czyszczenie, i prosi harmonogram o ponowne uruchomienie, aż wszystko zostanie przetworzone.

Przykład: czyszczenie włączone z wiekiem 6 miesięcy 26 września 2026 → zdarzenia sprzed 26 marca 2026 są usuwane tylko dla tej firmy. Pozostałe firmy zachowują wszystko.

Administratorzy audytu mogą też usuwać zdarzenia ręcznie w **Audyt → Dzienniki** (zaznacz → Akcje → Usuń).

## 8. Dane demonstracyjne

Baza demonstracyjna zawiera trzy reguły w stanie **projektu** (Kontakty, Konta bankowe, Cenniki), trzy sesje robocze i dziesięć przykładowych zdarzeń (zmiany telefonu i e-maila kontaktów, zmiana i usunięcie konta bankowego, zmiany cenników, eksporty). Nic nie jest rejestrowane, dopóki nie potwierdzisz reguły.

## 9. Ograniczenia

- Rejestrowane są zmiany wykonane przez ORM Odoo (ekrany, import, API). Bezpośrednie zmiany w SQL nie są widoczne.
- Firma zdarzenia to **bieżąca firma** użytkownika w chwili zmiany, a nie własna firma rekordu.
- Porównywane są tylko pola przechowywane; pola binarne, obrazy i pola jeden-do-wielu nie są rejestrowane (ich rekordy podrzędne można obserwować osobną regułą).
- **Ekran źródłowy** jest ustalany w miarę możliwości na podstawie adresu w przeglądarce; dla wywołań API może być pusty.
- Brak zatwierdzania, blokowania, powiadomień i zabezpieczenia przed modyfikacją: administratorzy audytu mogą usuwać historię.
- Jeśli rejestracja z jakiegoś powodu się nie powiedzie, działanie użytkownika i tak zostaje wykonane, a błąd trafia do dziennika serwera.
