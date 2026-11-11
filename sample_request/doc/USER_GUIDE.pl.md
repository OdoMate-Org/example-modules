# Podręcznik użytkownika: Product Sample Requests (Wnioski o próbki produktów)

> Handlowcy wnioskują o próbki produktów dla klientów, kierownicy je zatwierdzają i wysyłają, a Odoo przypomina handlowcowi o kontakcie z klientem i mierzy, ile próbek zamienia się w zamówienia.

---

## Spis treści

1. [Co robi ten moduł](#1-co-robi-ten-moduł)
2. [Gdzie znaleźć moduł w Odoo](#2-gdzie-znaleźć-moduł-w-odoo)
3. [Konfiguracja początkowa](#3-konfiguracja-początkowa)
4. [Tworzenie wniosku o próbki](#4-tworzenie-wniosku-o-próbki)
5. [Główny przebieg pracy](#5-główny-przebieg-pracy)
6. [Przypomnienie i wynik kontaktu](#6-przypomnienie-i-wynik-kontaktu)
7. [Raporty i współczynnik konwersji](#7-raporty-i-współczynnik-konwersji)
8. [Role i uprawnienia](#8-role-i-uprawnienia)
9. [Ograniczenia](#9-ograniczenia)

---

## 1. Co robi ten moduł

Moduł zastępuje e-maile i arkusze kalkulacyjne używane do obsługi próbek. Handlowiec tworzy **Sample Request** (`sample.request`, wniosek o próbki) dla klienta z co najmniej jednym produktem i ilością, a następnie go wysyła. Kierownik sprzedaży zatwierdza lub odrzuca wniosek. Po wysłaniu próbek kierownik klika **Mark as Sent** (Oznacz jako wysłane), a Odoo planuje dla handlowca zadanie To-Do za 14 dni. Handlowiec zapisuje, czy klient złożył zamówienie, a menu Reporting pokazuje konwersję próbka → zamówienie dla każdego handlowca.

| Funkcja | Szczegóły |
|---|---|
| Wnioski z pozycjami produktów | Customer (Klient), Sales Rep (Handlowiec), Reason (Powód), Reason Details (Szczegóły powodu) oraz zakładka **Products** (Produkty: Product, Quantity). Każdy wniosek dostaje numer, np. `SR/2026/0001`. |
| Proces zatwierdzania | Draft → Submitted → Approved → Sent → Followed Up, a także Rejected i Cancelled. Każda zmiana statusu jest zapisywana w czacie (chatter). |
| Obowiązkowy powód odrzucenia | Przycisk **Reject** (Odrzuć) otwiera okno, w którym trzeba podać powód. Powód jest widoczny we wniosku. |
| Automatyczne zadanie kontaktu | **Mark as Sent** tworzy dla handlowca aktywność To-Do „Follow up on sample request” z terminem Sent Date + 14 dni. |
| Zapis wyniku | Okno **Log Outcome** (Zapisz wynik): Ordered / Still Thinking / Not Interested, z możliwością powiązania Sales Order (zamówienia sprzedaży). |
| Raport konwersji | Tabela przestawna i wykres według Sales Rep i Status, z miarami **Converted** i **Conversion Rate (%)**. |
| Widoczność rekordów | Handlowcy widzą tylko własne wnioski, kierownicy widzą wszystkie. |

---

## 2. Gdzie znaleźć moduł w Odoo

Po instalacji w menu głównym pojawia się aplikacja **Sample Requests** z następującymi pozycjami:

- **My Requests** (Moje wnioski): Twoje wnioski (filtr „My Requests” jest domyślnie włączony). Otwiera się widok kanban pogrupowany według statusu. Dostępne są też lista, formularz, tabela przestawna i wykres.
- **Approvals** (Zatwierdzenia, tylko kierownicy): wszystkie wnioski w statusie **Submitted**, które czekają na decyzję. Z tego menu nie można tworzyć wniosków.
- **All Requests** (Wszystkie wnioski, tylko kierownicy): wszystkie wnioski wszystkich handlowców.
- **Reporting** (Raporty): tabela przestawna i wykres *Sample Request Analysis*, otwierane z włączonym już filtrem **Sent or Followed Up**.

---

## 3. Konfiguracja początkowa

Poza uprawnieniami użytkowników nie trzeba niczego konfigurować. Moduł nie ma strony ustawień.

1. Przejdź do **Settings → Users & Companies → Users** (Ustawienia → Użytkownicy i firmy → Użytkownicy) i otwórz użytkownika.
2. W sekcji uprawnień ustaw **Sample Request** na **User** (handlowcy) lub **Manager** (osoby, które zatwierdzają i wysyłają próbki).
3. Zapisz. Aplikacja **Sample Requests** pojawi się w menu tego użytkownika.

| Kto | Grupa do przypisania |
|---|---|
| Handlowiec, który wnioskuje o próbki | `Sample Request / User` |
| Kierownik sprzedaży lub logistyk, który zatwierdza i wysyła | `Sample Request / Manager` |

> Wskazówka: konto administratora otrzymuje **Sample Request / Manager** automatycznie przy instalacji, więc aplikacja jest od razu widoczna.
>
> Wskazówka: `Sample Request / User` nadaje też **Sales / User: Own Documents Only** (Sprzedaż / Użytkownik: tylko własne dokumenty), dzięki czemu handlowcy mogą wybrać zamówienie sprzedaży przy zapisie wyniku.

---

## 4. Tworzenie wniosku o próbki

**Ścieżka:** `Sample Requests` → `My Requests` → `New` (Nowy)

| Pole | Opis |
|---|---|
| **Reference** (Numer) | Nadawany automatycznie przy zapisie (np. `SR/2026/0007`). Tylko do odczytu. |
| **Customer** (Klient) | Wymagane. Firma lub kontakt, który otrzymuje próbki. |
| **Sales Rep** (Handlowiec) | Wymagane. Domyślnie Ty. Zmienić może je tylko kierownik i tylko dopóki wniosek jest w statusie Draft. |
| **Reason** (Powód) | Opcjonalne: Deal in Progress (transakcja w toku), New Prospect (nowy potencjalny klient), Existing Customer (obecny klient), Trade Show (targi), Other (inne). |
| **Reason Details** (Szczegóły powodu) | Dowolny tekst dla zatwierdzającego, np. „Partia pilotażowa do przetargu Q3, 2 kolory”. |
| Zakładka **Products** (Produkty) | Jedna pozycja na produkt: **Product** i **Quantity**. Ilość musi być większa od zera. |

**Przepływ statusów:**

```
Draft ──Submit──▶ Submitted ──Approve──▶ Approved ──Mark as Sent──▶ Sent ──Log Outcome──▶ Followed Up
  │                  │
  │                  ├──Reject (wymagany powód)──▶ Rejected
  │                  │
  └──Cancel──────────┴──Cancel──▶ Cancelled
```

Draft = Szkic, Submitted = Złożony, Approved = Zatwierdzony, Rejected = Odrzucony, Sent = Wysłany, Followed Up = Zakończony kontaktem, Cancelled = Anulowany.

> Uwaga: Rejected i Cancelled to statusy końcowe. Aby spróbować ponownie, otwórz wniosek i użyj **Actions → Duplicate** (Akcje → Duplikuj). Kopia powstaje jako nowy szkic z tym samym klientem, powodem i pozycjami produktów.

---

## 5. Główny przebieg pracy

### Scenariusz 1: handlowiec wnioskuje o próbki

**Krok 1: wypełnij wniosek.** Wybierz **Customer**, opcjonalnie **Reason** i **Reason Details**, i dodaj co najmniej jedną pozycję w zakładce **Products**.

**Krok 2: kliknij Submit (Złóż).**
- Jeśli zakładka **Products** jest pusta, Odoo zatrzyma Cię komunikatem „Add at least one product to … before submitting it.” (Dodaj co najmniej jeden produkt przed złożeniem).
- Status zmieni się na **Submitted**, a wniosek pojawi się w menu **Approvals** u wszystkich kierowników.

> Uwaga: po złożeniu nie możesz już zmieniać klienta, powodu, handlowca ani produktów. Jeśli coś się nie zgadza, kliknij **Cancel** (Anuluj; możliwe w statusach Draft i Submitted), a następnie zduplikuj wniosek i popraw kopię.

### Scenariusz 2: kierownik podejmuje decyzję

Otwórz **Sample Requests → Approvals** i otwórz wniosek.

- **Approve** (Zatwierdź): status zmieni się na **Approved**, a w polu **Decided By** (Decyzję podjął) pojawi się Twoje nazwisko.
- **Reject** (Odrzuć): otworzy się okno z wymaganym polem **Rejection Reason** (Powód odrzucenia). Kliknij **Reject** w oknie. Status zmieni się na **Rejected**, pojawi się czerwona wstęga „Rejected”, a powód i **Decided By** będą widoczne w formularzu.

Decyzję w sprawie dowolnego wniosku może podjąć każdy użytkownik z grupą **Sample Request / Manager**. Zatwierdzanie nie jest powiązane z bezpośrednim przełożonym handlowca.

### Scenariusz 3: kierownik wysyła próbki

Gdy paczka zostanie nadana, otwórz zatwierdzony wniosek i kliknij **Mark as Sent**:

- **Sent Date** (Data wysyłki) zostaje ustawiona na dziś. Jeśli kierownik wcześniej wpisał datę, zostaje ona zachowana.
- Status zmienia się na **Sent**.
- Dla handlowca planowane jest zadanie To-Do (zob. [sekcja 6](#6-przypomnienie-i-wynik-kontaktu)).

Dopóki wniosek ma status **Sent**, kierownik może poprawić **Sent Date** w formularzu. Ta zmiana **nie** przesuwa już utworzonego zadania, więc w razie potrzeby zmień jego termin ręcznie.

### Usuwanie

Usunąć można tylko wnioski w statusie **Draft** lub **Cancelled**. Przy innych statusach pojawi się „Only draft or cancelled sample requests can be deleted.” Zamiast usuwać, anuluj wniosek, aby zachować historię.

---

## 6. Przypomnienie i wynik kontaktu

### Przypomnienie

**Mark as Sent** tworzy we wniosku dokładnie jedną aktywność:

| Właściwość | Wartość |
|---|---|
| Typ | To-Do |
| Podsumowanie | Follow up on sample request |
| Przypisane do | **Sales Rep** wniosku |
| Termin | **Sent Date** + 14 dni |

Przykład: Sent Date = **3 marca 2026**, więc termin zadania to **17 marca 2026**. Handlowiec widzi je w menu aktywności (ikona zegara) i w czacie wniosku.

### Zapis wyniku

We wniosku w statusie **Sent** handlowiec-właściciel (lub dowolny kierownik) klika **Log Outcome**. Otwiera się okno *Log Follow-up Outcome*:

| Pole | Opis |
|---|---|
| **Outcome** (Wynik) | Wymagane: **Ordered** (Zamówił), **Still Thinking** (Jeszcze się zastanawia) lub **Not Interested** (Niezainteresowany). |
| **Sales Order** (Zamówienie sprzedaży) | Widoczne tylko dla **Ordered**, opcjonalne. Można wybrać tylko zamówienia, w których klientem jest klient wniosku lub jeden z jego kontaktów. Nie można tu utworzyć nowego zamówienia. |

Kliknij **Log Outcome**. Odoo:
- ustawia status **Followed Up** i zapisuje **Follow-up Outcome**,
- oznacza zadanie jako wykonane z komentarzem „Outcome: Ordered” (lub wybranym wynikiem),
- pokazuje zieloną wstęgę „Ordered”, jeśli wynik to Ordered.

> Wskazówka: jeśli zamówienia nie ma jeszcze w Odoo, zapisz **Ordered** bez zamówienia. Później otwórz wniosek i uzupełnij **Sales Order** w formularzu. Dla wniosków z wynikiem Ordered to pole pozostaje edytowalne.
>
> Uwaga: **Still Thinking** również zamyka wniosek i jego zadanie. Drugie przypomnienie nie jest planowane. Jeśli chcesz kolejne przypomnienie, zaplanuj nową aktywność w czacie samodzielnie.

---

## 7. Raporty i współczynnik konwersji

**Ścieżka:** `Sample Requests` → `Reporting`

Tabela przestawna *Sample Request Analysis* otwiera się z ustawieniami:
- **Wiersze:** Sales Rep
- **Kolumny:** Status
- **Miary:** **Count** (Liczba), **Converted** (Skonwertowane), **Conversion Rate (%)** (Współczynnik konwersji)
- **Filtr:** **Sent or Followed Up** (już włączony)

Każdy wniosek przechowuje dwie wartości:

| Miara | Wartość dla jednego wniosku | Agregacja w tabeli przestawnej |
|---|---|---|
| **Converted** | 1, jeśli Followed Up z wynikiem Ordered, w przeciwnym razie 0 | Suma |
| **Conversion Rate (%)** | 100, jeśli Followed Up z wynikiem Ordered, w przeciwnym razie 0 | Średnia |

Zatem przy domyślnie włączonym filtrze:

```
Conversion Rate = wnioski zakończone zamówieniem ÷ (wysłane + zakończone kontaktem) × 100
```

**Przykład obliczenia.** Anna ma 10 wniosków w statusie Sent lub Followed Up: 2 są nadal **Sent**, 8 jest **Followed Up** (3 Ordered, 4 Still Thinking, 1 Not Interested).

| Sales Rep | Count | Converted | Conversion Rate (%) |
|---|---|---|---|
| Anna | 10 | 3 | (3 × 100 + 7 × 0) ÷ 10 = **30,00** |

> Uwaga: po usunięciu filtra **Sent or Followed Up** szkice, wnioski odrzucone i anulowane liczą się jako 0 i zaniżają współczynnik. W przykładzie dodanie 5 szkiców i 1 odrzuconego wniosku dałoby 3 ÷ 16 = **18,75 %**. Odczytując współczynnik, trzymaj filtr włączony albo patrz tylko na kolumny **Sent** i **Followed Up**.

Inne przydatne filtry i grupowania w panelu wyszukiwania: **Pending Approval** (Oczekujące na zatwierdzenie), **Awaiting Follow-up** (Oczekujące na kontakt), **Converted to Order** (Zamienione na zamówienie), **Sent Date** (według okresu) oraz grupowanie według **Outcome**, **Reason** lub **Customer**. Wykres pokazuje skumulowany wykres słupkowy wniosków według Sales Rep i Status.

---

## 8. Role i uprawnienia

| Czynność | Sample Request / User (handlowiec) | Sample Request / Manager |
|---|---|---|
| Podgląd wniosków | Tylko własne (Sales Rep = ja) | Wszystkie |
| Tworzenie wniosku | Tak, dla siebie | Tak, dla dowolnego handlowca |
| Edycja wniosku / produktów | Tylko w statusie Draft | Tak, w dowolnym statusie (po Draft formularz blokuje większość pól) |
| Submit | Własne szkice | Dowolne szkice |
| Cancel (Draft / Submitted) | Własne | Dowolne |
| Approve / Reject / Mark as Sent | Nie | Tak |
| Zmiana Sent Date w statusie Sent | Nie | Tak |
| Log Outcome (w statusie Sent) | Własne | Dowolne |
| Powiązanie Sales Order z wnioskiem Ordered | Własne | Dowolne |
| Usuwanie | Własne Draft / Cancelled | Dowolne Draft / Cancelled |
| Menu | My Requests, Reporting | My Requests, Approvals, All Requests, Reporting |

`Sample Request / Manager` obejmuje wszystkie uprawnienia `Sample Request / User`. `Sample Request / User` obejmuje **Sales / User: Own Documents Only**. W menu Reporting handlowiec widzi statystyki tylko własnych wniosków.

Jak przypisać role: **Settings → Users & Companies → Users** → wybierz użytkownika → pole uprawnień **Sample Request**.

---

## 9. Ograniczenia

| Temat | Ograniczenie |
|---|---|
| Wiele firm | Wnioski nie mają pola Company ani reguły dostępu według firmy. W bazie z wieloma firmami kierownicy widzą wnioski wszystkich firm. Numeracja jest wspólna dla wszystkich firm. |
| Współczynnik konwersji | Ma sens tylko z włączonym filtrem **Sent or Followed Up** (w Reporting jest on domyślnie włączony). Bez niego szkice, wnioski odrzucone i anulowane liczą się jako 0. |
| Powiązane zamówienie | Nie jest sprawdzane pod kątem produktów, ilości ani kwot próbek. Można powiązać dowolne zamówienie klienta lub jego kontaktów, w tym szkic oferty lub anulowane zamówienie. |
| Wybór zamówienia | Tylko zamówienia, w których klientem jest klient wniosku lub jeden z jego kontaktów podrzędnych. Zamówienia złożonego na firmę nadrzędną lub niepowiązanego partnera nie można wybrać. Nie można utworzyć zamówienia z wniosku. |
| Magazyn / dostawa | Mark as Sent nie tworzy dostawy i nie zmienia stanów magazynowych. Wysyłka odbywa się poza tym modułem. |
| Ścieżka zatwierdzania | Każdy kierownik może zatwierdzić każdy wniosek. Brak poziomów zatwierdzania, limitów kwot czy zatwierdzających według zespołów. Kierownicy nie dostają e-maila po złożeniu wniosku (korzystaj z menu **Approvals** lub obserwuj wniosek). |
| Termin przypomnienia | Opóźnienie 14 dni jest zapisane w kodzie. Zmiana Sent Date po Mark as Sent nie przesuwa istniejącego zadania. **Still Thinking** zamyka wniosek bez drugiego przypomnienia. |
| Statusy końcowe | Rejected, Cancelled i Followed Up nie mogą zostać ponownie otwarte. Aby zacząć od nowa, użyj **Duplicate**. |
| Koszt próbek | Koszt ani wartość próbek nie są śledzone ani raportowane. |
