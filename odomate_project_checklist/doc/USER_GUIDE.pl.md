# Podręcznik użytkownika: Project Task Checklists (Listy kontrolne zadań projektowych)

> Wielokrotnego użytku listy kontrolne krok po kroku dla zadań Odoo Project: przyciski statusu dla każdego kroku, pasek postępu na żywo oraz automatyczne daty rozpoczęcia i zakończenia.

---

## Spis treści

1. [Co robi ten moduł](#1-co-robi-ten-moduł)
2. [Gdzie znaleźć go w Odoo](#2-gdzie-znaleźć-go-w-odoo)
3. [Konfiguracja początkowa: tworzenie szablonu listy kontrolnej](#3-konfiguracja-początkowa-tworzenie-szablonu-listy-kontrolnej)
4. [Stosowanie listy kontrolnej do zadania](#4-stosowanie-listy-kontrolnej-do-zadania)
5. [Praca z krokami](#5-praca-z-krokami)
6. [Jak obliczany jest postęp](#6-jak-obliczany-jest-postęp)
7. [Start Date i End Date](#7-start-date-i-end-date)
8. [Zastępowanie listy kontrolnej, nad którą trwają już prace](#8-zastępowanie-listy-kontrolnej-nad-którą-trwają-już-prace)
9. [Lista zadań i wyszukiwanie](#9-lista-zadań-i-wyszukiwanie)
10. [Role dostępu](#10-role-dostępu)
11. [Ograniczenia](#11-ograniczenia)

---

## 1. Co robi ten moduł

Wiele zadań przebiega za każdym razem według tego samego schematu: wdrożenie klienta, uruchomienie strony internetowej, odejście pracownika. Moduł pozwala administratorowi projektów raz zdefiniować taki schemat jako **szablon listy kontrolnej**. Osoba pracująca nad zadaniem wybiera listę, a jej kroki są kopiowane do zadania. Każdy krok ma status, zadanie pokazuje pasek postępu, a daty rozpoczęcia i zakończenia wypełniają się same.

| Funkcja | Szczegóły |
|---|---|
| Szablony wielokrotnego użytku | **Project → Configuration → Checklists** (Projekt → Konfiguracja → Listy kontrolne): nazwa, opis i uporządkowana lista kroków. Każdy krok ma nazwę i opcjonalną notatkę. |
| Zastosowanie jednym kliknięciem | Wybór szablonu w polu **Checklist** (Lista kontrolna) zadania kopiuje do niego wszystkie kroki. |
| Niezależna kopia w każdym zadaniu | Kroki zadania można edytować, przestawiać, dodawać i usuwać. Późniejsze zmiany szablonu **nigdy** nie zmieniają list już zastosowanych w zadaniach. |
| Statusy kroków | **To Do → In Progress → Done** (Do zrobienia → W toku → Zrobione) lub **Cancelled** (Anulowane). W każdym wierszu są przyciski **Start**, **Done**, **Cancel**. |
| Pasek postępu | Zrobione kroki ÷ (wszystkie kroki − anulowane) × 100. Widoczny w formularzu zadania i jako kolumna na liście zadań. |
| Automatyczne daty | **Start Date** (Data rozpoczęcia) jest ustawiana, gdy pierwszy krok zostanie rozpoczęty lub zrobiony. **End Date** (Data zakończenia) jest ustawiana, gdy lista osiągnie 100%, i czyszczona, gdy postęp spadnie. |
| Bezpieczna zamiana | Gdy prace już trwają, zmiana listy odbywa się przez okno potwierdzenia, które pokazuje, co dokładnie zostanie utracone. |

---

## 2. Gdzie znaleźć go w Odoo

Moduł nie ma własnego menu głównego. Rozszerza standardową aplikację **Project** (Projekt):

- **Project → Configuration → Checklists**: tworzenie i utrzymywanie szablonów list kontrolnych.
- **Formularz zadania**:
  - pole **Checklist** zaraz po **Tags** (Tagi)
  - pola **Start Date** i **End Date** zaraz po **Deadline** (Termin)
  - zakładka **Checklist** w notatniku (pojawia się, gdy zadanie ma co najmniej jeden krok)
- **Lista zadań**: kolumna **Checklist Progress** (Postęp listy kontrolnej) z paskiem postępu.
- **Wyszukiwanie zadań**: filtr **With Checklist** (Z listą kontrolną) oraz wyszukiwanie po polu **Checklist**.

> 💡 W standardowym Odoo menu **Project → Configuration** widzą tylko administratorzy projektów. Pozostali użytkownicy nadal mogą przeglądać szablony i wybierać je w zadaniach, ale nie widzą menu konfiguracji.

---

## 3. Konfiguracja początkowa: tworzenie szablonu listy kontrolnej

**Ścieżka:** `Project` → `Configuration` → `Checklists` → `New` (Nowy)

| Pole | Co wpisać | Przykład |
|---|---|---|
| **Name** (Nazwa, wymagane) | Nazwa, którą użytkownicy wybiorą w zadaniu | `New Client Onboarding` |
| **Description** (Opis) | Do czego służy lista (notatka wewnętrzna) | `Standardowe kroki wdrożenia nowego klienta` |
| **Steps Count** (Liczba kroków) | Tylko do odczytu. Liczba kroków w szablonie | `5` |
| Zakładka **Steps** (Kroki) | Jeden wiersz na krok: **Name** (wymagane) i opcjonalna **Note** (Notatka). Aby zmienić kolejność, przeciągnij uchwyt (⋮⋮) po lewej. | `Create Account`, `Send Welcome Email`, `Schedule Kick-off Call`, `Set Up Shared Folder`, `Confirm First Invoice` |

Lista **Checklists** pokazuje **Name** i **Steps Count** każdego szablonu. Szablony można wyszukiwać po nazwie lub po polu **Step** (Krok), aby znaleźć wszystkie szablony zawierające dany krok, np. „Invoice”.

Aby przestać oferować szablon bez jego usuwania, **zarchiwizuj** go (menu akcji ⚙ → **Archive**). Zarchiwizowane szablony znikają z listy wyboru pola **Checklist**. Zadania, które już ich używają, zachowują swoje kroki. Zarchiwizowane szablony znajdziesz filtrem **Archived**.

> 💡 Jeśli załadowano dane demonstracyjne, dostępne są trzy przykładowe szablony: *New Client Onboarding* (5 kroków), *Website Launch Checklist* (4 kroki) i *Employee Offboarding* (4 kroki).

---

## 4. Stosowanie listy kontrolnej do zadania

1. Otwórz dowolne zadanie (**Project → Projects → *twój projekt* → *zadanie***).
2. W polu **Checklist** (obok **Tags**) wybierz szablon, np. `New Client Onboarding`.
3. Zapisz. Wszystkie kroki szablonu zostają skopiowane do zadania ze statusem **To Do** i pojawia się zakładka **Checklist**.

Co można zrobić z kopią w zadaniu:

- **Edytować** nazwę lub notatkę kroku, aby pasowała do tego zadania.
- **Zmieniać kolejność** kroków przez przeciąganie.
- **Dodawać** kroki przez *Add a line* (Dodaj wiersz) na dole listy.
- **Usuwać** kroki, które nie dotyczą zadania.

Żadna z tych zmian nie wpływa na szablon. Działa to też w drugą stronę: jeśli administrator później zmieni nazwy, doda lub usunie kroki w szablonie, zadania, które już go używają, zachowają swoje kroki bez zmian. Nową wersję dostaną tylko zadania, do których szablon zostanie zastosowany później.

> 💡 Dopóki żaden krok nie został rozpoczęty, zrobiony ani anulowany, można po prostu wybrać inny szablon w polu **Checklist**. Kroki zostaną zastąpione bez okna dialogowego, bo prace jeszcze się nie zaczęły. Gdy prace już trwają, zobacz [sekcję 8](#8-zastępowanie-listy-kontrolnej-nad-którą-trwają-już-prace).

---

## 5. Praca z krokami

Otwórz zakładkę **Checklist** zadania. Na górze widać pasek **Checklist Progress**, pod nim listę kroków:

| Kolumna | Znaczenie |
|---|---|
| ⋮⋮ (uchwyt) | Przeciągnij, aby zmienić kolejność |
| **Name** | Krok |
| **Note** | Opcjonalne instrukcje skopiowane z szablonu |
| **Status** | Kolorowy pogrubiony tekst: **To Do**, pomarańczowy **In Progress**, zielony **Done**, czerwony **Cancelled**. Kliknij, aby wybrać status ręcznie (w celu poprawienia pomyłki). |
| Przyciski | **Start** (▶ Rozpocznij), **Done** (✓ Zrobione), **Cancel** (✕ Anuluj). Widoczne są tylko przyciski odpowiednie dla bieżącego statusu. |

**Przejścia statusów:**

| Bieżący status | Widoczne przyciski | Wynik |
|---|---|---|
| To Do | **Start**, **Done**, **Cancel** | In Progress / Done / Cancelled |
| In Progress | **Done**, **Cancel** | Done / Cancelled |
| Done | brak | aby otworzyć ponownie, zmień **Status** ręcznie |
| Cancelled | brak | aby otworzyć ponownie, zmień **Status** ręcznie |

Aby cofnąć przypadkowe kliknięcie (np. krok omyłkowo oznaczony jako **Done**), kliknij komórkę **Status** i wybierz właściwą wartość, np. **To Do**. Postęp i End Date przeliczają się od razu.

Całe wiersze też są kolorowane: **zielony** dla zrobionych, **czerwony** dla anulowanych, **pomarańczowy** dla kroków w toku.

Każdy krok zapisuje też, kiedy został po raz pierwszy rozpoczęty (**Started On**) i kiedy zrobiony (**Done On**). Te dane są przechowywane informacyjnie i nie są pokazywane w formularzu zadania.

---

## 6. Jak obliczany jest postęp

```
Checklist Progress = Zrobione kroki ÷ (Wszystkie kroki − Anulowane kroki) × 100
```

Anulowane kroki są całkowicie pomijane, więc anulowanie nieistotnego kroku nie obniża wyniku. Jeśli nie ma kroków kwalifikujących się do obliczenia (brak kroków lub wszystkie anulowane), postęp wynosi **0%**.

**Przykłady obliczeń**

| Kroki | Zrobione | W toku | Do zrobienia | Anulowane | Obliczenie | Postęp |
|---|---|---|---|---|---|---|
| 5 | 2 | 1 | 2 | 0 | 2 ÷ 5 | **40%** |
| 5 | 2 | 0 | 2 | 1 | 2 ÷ (5 − 1) = 2 ÷ 4 | **50%** |
| 4 | 2 | 0 | 1 | 1 | 2 ÷ (4 − 1) = 2 ÷ 3 | **67%** |
| 3 | 2 | 0 | 0 | 1 | 2 ÷ (3 − 1) = 2 ÷ 2 | **100%** |
| 3 | 0 | 0 | 0 | 3 | brak kwalifikujących się kroków | **0%** |

Kroki „W toku” nie są jeszcze liczone jako zrobione. Wliczają się do postępu dopiero po oznaczeniu jako **Done**.

---

## 7. Start Date i End Date

Moduł dodaje do zadania dwa **nowe** pola dat, widoczne jako **Start Date** (Data rozpoczęcia) i **End Date** (Data zakończenia) zaraz po **Deadline** (nazwy techniczne `checklist_date_start` i `checklist_date_end`).

> ℹ️ **Dlaczego nowe pola?** Standardowy model `project.task` ma już techniczne pole `date_end` (data i godzina), którym zarządza rdzeń Odoo. Aby nie ingerować w standardowe działanie, moduł nie zapisuje do niego, tylko prowadzi własne daty listy kontrolnej.

| Pole | Ustawiane automatycznie, gdy… | Czyszczone automatycznie, gdy… | Edycja ręczna |
|---|---|---|---|
| **Start Date** | krok po raz pierwszy przechodzi w **In Progress** lub **Done** **i** pole jest puste. Ustawiana jest dzisiejsza data. | nigdy. Po ustawieniu nie zmienia się automatycznie. | ✅ Zawsze |
| **End Date** | postęp osiąga **100%** (jest co najmniej jeden nieanulowany krok) **i** pole jest puste. Ustawiana jest dzisiejsza data. | postęp spada poniżej 100% (np. dodano nowy krok lub krok wrócił do stanu niezrobionego), **lub** lista została zastąpiona przez okno **Replace Checklist** | ✅ Zawsze |

**Przykładowa oś czasu** (szablon z 4 krokami):

| Data | Akcja | Postęp | Start Date | End Date |
|---|---|---|---|---|
| 2 mar | Zastosowano listę | 0% | – | – |
| 3 mar | Krok 1 → **Start** | 0% | **3 mar** | – |
| 5 mar | Krok 1 → **Done**, krok 3 → **Cancel** | 1 ÷ 3 = 33% | 3 mar | – |
| 9 mar | Kroki 2 i 4 → **Done** | 3 ÷ 3 = 100% | 3 mar | **9 mar** |
| 10 mar | Dodano nowy krok „Client sign-off” | 3 ÷ 4 = 75% | 3 mar | *wyczyszczona* |
| 12 mar | „Client sign-off” → **Done** | 100% | 3 mar | **12 mar** |

Uwagi:
- Jeśli wpiszesz Start Date lub End Date ręcznie, automatyka nie nadpisze jej dzisiejszą datą. Wyjątek: End Date jest i tak czyszczona, gdy dowolny krok zmieni status, a postęp jest poniżej 100%.
- Zastąpienie listy **nie** czyści Start Date, ponieważ prace nad zadaniem już się rozpoczęły.

---

## 8. Zastępowanie listy kontrolnej, nad którą trwają już prace

Gdy **dowolny** krok ma status In Progress, Done lub Cancelled, pole **Checklist** staje się tylko do odczytu, a pod nim pojawia się przycisk **Replace Checklist** (⇄ Zastąp listę kontrolną). Chroni to wykonaną pracę przed przypadkową zmianą w liście wyboru.

1. Kliknij **Replace Checklist**. Otworzy się okno z polami **Task** (Zadanie) i **Current Checklist** (Bieżąca lista).
2. Wybierz **New Checklist** (Nowa lista). Bieżący szablon nie jest proponowany.
3. Przeczytaj ostrzeżenie. Pokazuje ono, co dokładnie zostanie utracone, np.: *"5 current step(s) (2 done, 1 in progress, 1 cancelled) will be deleted and replaced by the steps of "Website Launch Checklist". The End Date will be cleared."* (5 bieżących kroków (2 zrobione, 1 w toku, 1 anulowany) zostanie usuniętych i zastąpionych krokami „Website Launch Checklist”. End Date zostanie wyczyszczona.)
4. Kliknij **Replace Checklist**, aby potwierdzić. Wszystkie bieżące kroki zostają usunięte, kroki nowego szablonu są kopiowane ze statusem **To Do**, a **End Date** jest czyszczona. **Start Date** pozostaje bez zmian.
   Albo kliknij **Discard** (Odrzuć), aby zamknąć okno. Nic się nie zmieni.

> ℹ️ **Dlaczego przycisk, a nie okno przy zmianie pola?** W Odoo zmiana pola w formularzu (tzw. onchange) nie może otworzyć okna potwierdzenia bez własnego kodu JavaScript, a ten moduł celowo zbudowano bez własnego JavaScriptu. Dlatego pole jest blokowane, gdy prace się rozpoczną, a zamiana odbywa się przez to wyraźne okno dialogowe. Próba zmiany listy w inny sposób (np. przez import) zostanie odrzucona komunikatem: *"The checklist of task … is already in progress. Use the Replace Checklist button to switch to another checklist."*

---

## 9. Lista zadań i wyszukiwanie

- **Kolumna Checklist Progress**: widok listy zadań (np. **Project → Projects → *projekt*** w trybie listy) pokazuje pasek postępu dla każdego zadania. Kolumna jest opcjonalna, więc można ją pokazać lub ukryć w selektorze kolumn. Przy grupowaniu wiersz grupy pokazuje **średni** postęp.
- **Filtr With Checklist** (w sekcji Filters panelu wyszukiwania): tylko zadania z co najmniej jednym krokiem listy.
- **Wyszukiwanie po Checklist**: wpisz nazwę szablonu w pasku wyszukiwania i wybierz *Search Checklist for: …*, aby znaleźć wszystkie zadania korzystające z tego szablonu.

---

## 10. Role dostępu

| Rola | Szablony list kontrolnych (i ich kroki) | Kroki list w zadaniach | Okno Replace Checklist |
|---|---|---|---|
| **Użytkownik wewnętrzny** (`base.group_user`) | ✅ Tylko odczyt (może wybierać szablony w zadaniach) | ✅ Odczyt / tworzenie / edycja / usuwanie, **tylko w zadaniach, które widzi** (patrz niżej), w ramach dozwolonych firm | ✅ Może używać |
| **Administrator projektów** (`project.group_project_manager`) | ✅ Odczyt / tworzenie / edycja / usuwanie | ✅ Odczyt / tworzenie / edycja / usuwanie we **wszystkich** zadaniach dozwolonych firm | ✅ Może używać |

**Które kroki widzi i edytuje użytkownik wewnętrzny.** Kroki podlegają widoczności projektu zadania. Użytkownik może zarządzać krokami zadania, jeśli spełniony jest **dowolny** z warunków:
- projekt zadania jest widoczny dla wszystkich pracowników wewnętrznych (lub także dla portalu),
- użytkownik obserwuje projekt zadania,
- użytkownik obserwuje zadanie,
- użytkownik jest przypisany do zadania.

Dodatkowo zadanie musi należeć do jednej z dozwolonych firm użytkownika (lub nie mieć firmy).

**Szablony są globalne.** Nie mają pola firmy, więc wszystkie firmy w bazie wielofirmowej widzą te same szablony.

Aby przypisać rolę: `Settings` → `Users & Companies` → `Users` → wybierz użytkownika → poziom dostępu **Project** (**User** lub **Administrator**).

---

## 11. Ograniczenia

| Temat | Ograniczenie |
|---|---|
| Powiadomienia | Przy zmianie statusu kroku nie są wysyłane e-maile, wiadomości w czacie, aktywności ani przypomnienia. |
| Przypisanie | Kroki nie mają osobnego wykonawcy ani terminu. Za całą listę odpowiadają osoby przypisane do zadania. |
| Ponowne otwieranie kroków | Nie ma przycisku, który przywraca krok **Done** lub **Cancelled**; zamiast tego zmień komórkę **Status** ręcznie. |
| Raportowanie | Brak dedykowanych raportów, pulpitów i PDF. Można korzystać z kolumny **Checklist Progress**, średniej w grupowaniu i filtra **With Checklist**. |
| Czas kroków | **Started On** / **Done On** są zapisywane dla każdego kroku, ale nie są wyświetlane w standardowych widokach. |
| Wiele firm | Szablony nie są przypisane do firmy. Wszystkie firmy współdzielą jedną listę szablonów. |
| Zmiana szablonu | Gdy dowolny krok zostanie rozpoczęty, zrobiony lub anulowany, nie można zmienić szablonu przez ponowny wybór w polu. Użyj przycisku **Replace Checklist**. Zamiana usuwa bieżące kroki wraz ze statusami i nie można jej cofnąć. |
| Aktualizacje szablonów | Zmiany szablonu nie są przenoszone do zadań, które już go używają. Tak to zaprojektowano. |
| Czyszczenie pola Checklist | Wyczyszczenie pola **Checklist** (w zadaniu bez postępu) nie usuwa już skopiowanych kroków. W razie potrzeby usuń je w zakładce **Checklist**. |
| Widoczność menu | **Project → Configuration → Checklists** znajduje się w standardowym menu konfiguracji, które Odoo pokazuje tylko administratorom projektów. |
