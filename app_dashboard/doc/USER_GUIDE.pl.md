# Podręcznik użytkownika: Pulpit aplikacji (Apps Dashboard)

> Osobisty ekran startowy „My Apps”: kwadratowe kafelki dla każdej aplikacji Odoo, którą już możesz otworzyć, z ulubionymi na górze, aplikacjami priorytetowymi wskazanymi przez administratora jako pierwsze dla wszystkich, resztą uporządkowaną według częstości użycia i możliwością przeciągania kafelków, jeśli chcesz mieć pełną kontrolę.

---

## Spis treści

1. [Co robi ten moduł](#1-co-robi-ten-moduł)
2. [Gdzie go znaleźć w Odoo](#2-gdzie-go-znaleźć-w-odoo)
3. [Konfiguracja początkowa](#3-konfiguracja-początkowa)
4. [Korzystanie z pulpitu My Apps](#4-korzystanie-z-pulpitu-my-apps)
5. [Ulubione](#5-ulubione)
6. [Aplikacje priorytetowe, kolejność według użycia i przeciąganie kafelków](#6-aplikacje-priorytetowe-kolejność-według-użycia-i-przeciąganie-kafelków)
7. [Pulpit jako ekran startowy](#7-pulpit-jako-ekran-startowy)
8. [Przykład](#8-przykład)
9. [Które aplikacje pojawiają się na pulpicie](#9-które-aplikacje-pojawiają-się-na-pulpicie)
10. [Role dostępu](#10-role-dostępu)
11. [Informacje techniczne](#11-informacje-techniczne)
12. [Ograniczenia](#12-ograniczenia)

---

## 1. Co robi ten moduł

Moduł Apps Dashboard dodaje ekran **My Apps**, na którym każda dostępna dla Ciebie aplikacja jest pokazana jako duży kwadratowy kafelek z ikoną i nazwą. Najczęściej używane aplikacje możesz przypiąć gwiazdką, aby zawsze były pierwsze, kafelki możesz filtrować, wpisując fragment nazwy, a pulpit możesz ustawić jako pierwszy ekran po zalogowaniu — dla siebie albo, jeśli jesteś administratorem, dla wszystkich w bazie danych.

Administratorzy mogą także skonfigurować ogólnobazodanową listę **Priority Apps** (Settings → General Settings), aby aplikacje, które firma już uznała za „zawsze dostępne”, pojawiały się jako pierwsze u każdego użytkownika. Aplikacje, które nie są ani ulubione, ani priorytetowe, są sortowane według tego, jak często dana osoba faktycznie je otwiera, a każdy może przeciągać kafelki, aby ustawić własną kolejność, jeśli potrzebuje większej kontroli.

Pulpit nigdy nie nadaje nowych uprawnień: pokazuje wyłącznie aplikacje, które już widzisz w standardowym menu aplikacji Odoo.

| Funkcja | Szczegóły |
|---|---|
| Kafelki aplikacji | Jeden kafelek dla każdej aplikacji najwyższego poziomu, którą możesz otworzyć: ikona, nazwa, wskaźnik priorytetu i gwiazdka w prawym górnym rogu. |
| Ulubione | Kliknij gwiazdkę, aby przypiąć aplikację. Przypięte aplikacje są pokazywane w sekcji **Favorites** nad wszystkim innym. Ulubione są osobiste i zapisywane w Twoim użytkowniku. |
| Aplikacje priorytetowe | Administratorzy wybierają aplikacje, w określonej kolejności, które zawsze są pierwsze dla każdego użytkownika wśród aplikacji nieoznaczonych jako ulubione (Settings → General Settings → My Apps Dashboard → **Manage Priority Apps**). |
| Kolejność według użycia | Aplikacje, których nie oznaczyłeś jako ulubione, priorytetowe ani nie przeciągnąłeś ręcznie, są sortowane według tego, jak często osobiście je otwierasz — te używane najczęściej automatycznie przesuwają się na górę. |
| Przeciąganie | Przeciągnij dowolny nieulubiony kafelek na nowe miejsce. Tę pozycję zachowuje tylko przeciągnięty kafelek; kafelki, których nie przestawiałeś, zachowują wokół niego automatyczną kolejność według priorytetu i użycia. |
| Wyszukiwanie | Pole **Search apps...** filtruje kafelki po nazwie podczas pisania (bez rozróżniania wielkości liter, dopasowanie do dowolnej części nazwy). |
| Otwieranie aplikacji | Kliknięcie kafelka otwiera aplikację dokładnie tak jak standardowe menu aplikacji i jest liczone do kolejności użycia tej aplikacji. |
| Ekran startowy | W **My Preferences** opcja **Home Screen** pozwala wybrać między **Default Menu** a **Apps Dashboard**. Administratorzy mogą też ustawić pulpit jako domyślny ekran startowy dla wszystkich użytkowników jednocześnie. |

---

## 2. Gdzie go znaleźć w Odoo

Po instalacji w głównym menu aplikacji pojawia się nowa aplikacja najwyższego poziomu **My Apps**. Jest umieszczona na końcu listy aplikacji (sekwencja 9999), więc nie zastępuje Twojej zwykłej aplikacji startowej, dopóki pulpit nie zostanie wybrany (przez Ciebie lub administratora) jako ekran startowy, i jest widoczna dla wszystkich użytkowników wewnętrznych.

- **My Apps** — otwiera pulpit. Można też przejść bezpośrednio pod adres `/odoo/my-apps`.
- **My Apps → Priority Apps** — tylko dla administratorów. Zarządzanie ogólnobazodanową listą aplikacji przypiętych jako pierwsze dla wszystkich.
- **Menu awatara (prawy górny róg) → My Preferences → Home Screen** — określa, czy Odoo otwiera pulpit po Twoim własnym zalogowaniu.
- **Settings → General Settings → My Apps Dashboard** — tylko dla administratorów. Ustawienie pulpitu jako domyślnego ekranu startowego dla całej bazy danych oraz przycisk-skrót **Manage Priority Apps**.

---

## 3. Konfiguracja początkowa

Do zwykłego korzystania konfiguracja nie jest wymagana. Każdy użytkownik wewnętrzny może otworzyć **My Apps** zaraz po instalacji. Każdy użytkownik widzi tylko swoje aplikacje, swoje ulubione i własną kolejność według użycia.

> 💡 Jeśli moduł zainstalowano z danymi demonstracyjnymi, **Employees**, **Project** i **Timesheets** (te, które są zainstalowane) są już skonfigurowane jako ogólnobazodanowe Priority Apps, a administrator ma dodatkowo przypięte jako osobiste ulubione te same aplikacje plus, jeśli zainstalowane, **Invoicing**, **Time Off**, **Recruitment**, **CRM**, **Sales** i **Purchase**. Jeśli żaden z kandydatów na priorytet nie jest zainstalowany, aplikacje priorytetowe nie są konfigurowane, a ulubione domyślnie przypinają **Settings**.

Administratorzy, którzy chcą, aby pulpit był ekranem startowym dla wszystkich, lub chcą skonfigurować listę Priority Apps, robią to raz w **Settings → General Settings → My Apps Dashboard** — zobacz [punkt 6](#6-aplikacje-priorytetowe-kolejność-według-użycia-i-przeciąganie-kafelków) i [punkt 7](#7-pulpit-jako-ekran-startowy).

---

## 4. Korzystanie z pulpitu My Apps

**Ścieżka:** `My Apps`

U góry ekranu znajdują się tytuł **My Apps** i pole **Search apps...**, a pod nimi kafelki.

| Element | Działanie |
|---|---|
| Kafelek (ikona + nazwa) | Kliknij w dowolnym miejscu kafelka, aby otworzyć aplikację. Otwarcie kafelka jest także liczone do kolejności użycia tej aplikacji. |
| Gwiazdka (prawy górny róg kafelka) | Pusta gwiazdka = nie w ulubionych (podpowiedź **Add to favorites**). Żółta gwiazdka = w ulubionych (podpowiedź **Remove from favorites**). Kliknięcie gwiazdki nie otwiera aplikacji. |
| Ikona pinezki (lewy górny róg kafelka) | Pojawia się, gdy aplikacja znajduje się na ogólnobazodanowej liście Priority Apps i nie została przez Ciebie ręcznie przesunięta. |
| Sekcja **Favorites** | Wyświetlana tylko wtedy, gdy masz co najmniej jedną ulubioną aplikację, do której nadal masz dostęp. Zawsze pierwsza. |
| Sekcja **All Apps** | Wszystko, co nie jest ulubione: najpierw aplikacje priorytetowe (w kolejności ustalonej przez administratora), potem reszta uporządkowana według częstości użycia. Każdy przeciągnięty przez Ciebie kafelek zostaje tam, gdzie go upuściłeś, a pozostałe układają się wokół niego. Nagłówek **All Apps** pojawia się tylko wtedy, gdy nad nim jest wyświetlana sekcja **Favorites**. |
| Przeciąganie | Gdy pole wyszukiwania jest puste, przeciągnij dowolny kafelek w **All Apps** na nowe miejsce. Przypinany jest tylko przeciągnięty kafelek; sąsiednie zachowują automatyczną kolejność. Podczas aktywnego filtra wyszukiwania przeciąganie jest wyłączone. |
| **Search apps...** | Filtruje obie sekcje jednocześnie. Wyczyść pole, aby znów zobaczyć wszystkie kafelki (i ponownie włączyć przeciąganie). |

Komunikaty, które możesz zobaczyć:

| Komunikat | Znaczenie |
|---|---|
| **No apps available yet** — „You do not have access to any application. Ask your administrator to grant you access rights.” | Twój użytkownik nie może otworzyć żadnej aplikacji. Poproś administratora o nadanie uprawnień. |
| **No app matches your search.** | Żadna nazwa aplikacji nie zawiera wpisanego tekstu. Zmień lub wyczyść wyszukiwanie. |
| **This app is no longer available to you.** (ostrzeżenie) | Kliknięto gwiazdkę aplikacji, do której utracono dostęp po załadowaniu strony. Pulpit przeładowuje się, a kafelek znika. |

---

## 5. Ulubione

**Aby przypiąć aplikację:** kliknij pustą gwiazdkę na jej kafelku. Gwiazdka zmieni kolor na żółty, a kafelek przeniesie się do sekcji **Favorites**.

**Aby odpiąć aplikację:** kliknij żółtą gwiazdkę. Kafelek wróci do **All Apps**, gdzie jego pozycja jest ustalana według kolejności priorytet / użycie / przeciąganie, opisanej w [punkcie 6](#6-aplikacje-priorytetowe-kolejność-według-użycia-i-przeciąganie-kafelków).

Zasady:

- Ulubione są osobiste. Przypięcie aplikacji nie wpływa na innych użytkowników.
- Możesz przypinać tylko aplikacje widoczne na Twoim pulpicie. Serwer odmawia przypięcia aplikacji, której nie wolno Ci otwierać.
- Jeśli później utracisz dostęp do przypiętej aplikacji (na przykład administrator usunie Cię z grupy), aplikacja po prostu zniknie z Twojego pulpitu. Ulubiony wpis nie jest usuwany: jeśli dostęp zostanie przywrócony, aplikacja automatycznie znów pojawi się w **Favorites**.

---

## 6. Aplikacje priorytetowe, kolejność według użycia i przeciąganie kafelków

Kafelki w **All Apps** (wszystko, co nie jest osobistym ulubionym) są uporządkowane w następujący sposób, od pierwszego do ostatniego:

1. **Aplikacje priorytetowe** — aplikacje przypięte przez administratora dla całej bazy danych, w ustalonej przez niego kolejności, o ile sam nie przesunąłeś ręcznie tego kafelka.
2. **Twoje najczęściej używane aplikacje** — wśród pozostałych pierwsza jest aplikacja, którą osobiście otwierasz najczęściej, potem następna pod względem częstości i tak dalej. Aplikacja, której nigdy nie otworzyłeś, znajduje się za każdą aplikacją otwartą przynajmniej raz.
3. **Twoja własna kolejność przeciągania** — gdy tylko przeciągniesz dowolny kafelek w **All Apps**, ten kafelek (a od tej chwili każdy przeciągnięty przez Ciebie kafelek) zachowuje dokładną pozycję, którą mu nadałeś, przed automatycznym porządkiem priorytet/użycie dla tego kafelka. Aplikacje, których jeszcze osobiście nie przestawiłeś, wciąż podlegają zasadom 1 i 2 wokół tych, które przestawiłeś.

**Zarządzanie ogólnobazodanową listą Priority Apps** (tylko administratorzy):

**Ścieżka:** `Settings → General Settings → My Apps Dashboard → Manage Priority Apps` albo `My Apps → Priority Apps`.

1. Otwórz **Manage Priority Apps**. Zobaczysz listę z uchwytem do przeciągania i kolumną **App**.
2. Kliknij **New**, wybierz aplikację główną w polu **App** i zapisz. Zostanie dodana na końcu listy (jej kolejność ustawia się za bieżącym ostatnim wierszem). Lista **App** proponuje tylko aplikacje, które mogą pojawić się na pulpicie: aplikacje główne widoczne w zwykłym menu aplikacji (poza trybem deweloperskim), z wyjątkiem samego **My Apps**. Każdy zapisany wiersz ma tytuł z nazwą swojej aplikacji.
3. Przeciągaj wiersze za uchwyt, aby zmienić kolejność, w jakiej wszyscy widzą aplikacje priorytetowe.
4. Usuń wiersz, aby przestać traktować tę aplikację jako priorytetową dla wszystkich (wciąż pojawia się w **All Apps**, sortowana według użycia jak każda inna aplikacja).

Aplikacje priorytetowe są ustawieniem ogólnobazodanowym: każdy uprawniony użytkownik widzi te same aplikacje priorytetowe w tej samej kolejności (o ile osobiście nie przeciągnął tego kafelka gdzie indziej na swoim własnym pulpicie). Aplikacja priorytetowa pojawia się jako kafelek tylko u użytkowników, którzy już widzą ją w swoim standardowym menu aplikacji — lista priorytetowa nigdy nie nadaje dodatkowego dostępu.

**Przestawianie własnych kafelków:**

Gdy pole wyszukiwania jest puste, przeciągnij dowolny kafelek w **All Apps** na nowe miejsce i upuść. Przeglądarka pokazuje przesuwanie się kafelka w trakcie przeciągania. Nowa kolejność zapisywana jest natychmiast i jest osobista dla Ciebie — nie zmienia tego, co widzą inni.

---

## 7. Pulpit jako ekran startowy

### Dla jednego użytkownika

**Ścieżka:** menu awatara (prawy górny róg) → `My Preferences` → pole **Home Screen** (na karcie **Preferences**, pod **Email Signature**; administratorzy widzą to pole także na karcie **Preferences** w **Settings → Users** dla każdego użytkownika wewnętrznego)

| Opcja | Efekt |
|---|---|
| **Default Menu** | Po zalogowaniu Odoo otwiera się jak zwykle. Jeśli Twoją akcją startową (Home Action) był pulpit, zostanie ona wyczyszczona. |
| **Apps Dashboard** | Akcja startowa (**Home Action**) Twojego użytkownika zostaje ustawiona na pulpit **My Apps**, więc po zalogowaniu Odoo otwiera się na pulpicie. |

Kliknij **Save**. Nowy ekran startowy zacznie obowiązywać po następnym zalogowaniu lub przeładowaniu Odoo.

> ⚠️ Jeśli administrator przypisał Ci inną akcję startową (na przykład lejek sprzedaży), wybór **Default Menu** jej nie usuwa. Czyszczona jest tylko akcja startowa pulpitu ustawiona tą opcją. Wybór **Apps Dashboard** zastępuje dowolną wcześniejszą akcję startową.

### Dla całej bazy danych (administratorzy)

**Ścieżka:** `Settings → General Settings → My Apps Dashboard → Apps Dashboard is the default home screen`

Włączenie tego przełącznika i kliknięcie **Save** natychmiast ustawia **Home Screen** każdego aktywnego użytkownika wewnętrznego na **Apps Dashboard** (użytkownicy portalu i publiczni nigdy nie są zmieniani i nigdy nie dostają pulpitu jako akcji startowej) — nadpisując indywidualny wybór każdego z nich w tym momencie. Wyłączenie i zapisanie przywraca wszystkich aktywnych użytkowników wewnętrznych do **Default Menu**. Każdy może potem wejść do swoich **My Preferences** i wybrać opcję, którą osobiście preferuje; ustawienie ogólnobazodanowe określa jedynie to, co dzieje się *w momencie zapisu*, a nie trwale wymuszony wybór.

Użytkownik zarejestrowany po włączeniu tej opcji zaczyna z ustawieniem domyślnym dla bazy danych; użytkownik utworzony, gdy jest ona wyłączona, zaczyna z **Default Menu**, jak wcześniej.

---

## 8. Przykład

Anna jest kierowniczką projektów. Jej użytkownik może otworzyć sześć aplikacji: **Discuss**, **Calendar**, **Contacts**, **Project**, **Timesheets** i **Employees**. **Settings** nie ma na jej pulpicie, ponieważ nie jest administratorką. Administrator już ustawił **Project** jako ogólnobazodanową Priority App.

1. Anna klika **My Apps**. **All Apps** pokazuje najpierw **Project** (to aplikacja priorytetowa), a potem pozostałe pięć uporządkowane według jej użycia — wszystkie na równi z zerem, więc zachowują standardową kolejność menu: Discuss, Calendar, Contacts, Timesheets, Employees. Nie ma jeszcze ulubionych, więc nie ma osobnej sekcji **Favorites**.
2. Klika gwiazdkę na **Timesheets**. Przenosi się do nowej sekcji **Favorites** nad wszystkim innym.
3. W ciągu kolejnych kilku dni otwiera **Contacts** osiem razy, a **Calendar** dwa razy. Następnym razem, gdy otwiera pulpit, **All Apps** wyświetla teraz: Project (wciąż priorytetowa, wciąż pierwsza), Contacts (najczęściej używana), Discuss, Calendar, Employees.
4. Decyduje, że chce mieć **Discuss** zaraz po **Project**, niezależnie od użycia, więc przeciąga jego kafelek o jedną pozycję wyżej. Od tej chwili **Discuss** zachowuje tę pozycję, nawet gdy zmienia się jej użycie innych aplikacji, a Contacts/Calendar/Employees nadal automatycznie przestawiają się wokół niego na podstawie użycia.
5. Otwiera **My Preferences**, ustawia **Home Screen** na **Apps Dashboard** i klika **Save**. Po następnym zalogowaniu Odoo otwiera się od razu na **My Apps**.
6. Później administrator odbiera Annie dostęp do Timesheets. Przy następnej wizycie sekcja **Favorites** znika (nie ma innych ulubionych), a **Timesheets** w ogóle nie ma już na pulpicie. Gdy dostęp zostaje przywrócony, **Timesheets** wraca do ulubionych bez ponownego przypinania.

---

## 9. Które aplikacje pojawiają się na pulpicie

Aplikacja pojawia się na Twoim pulpicie tylko wtedy, gdy spełnia wszystkie te warunki:

| Warunek | Wyjaśnienie |
|---|---|
| Jest menu aplikacji najwyższego poziomu | Podmenu (na przykład *Sales → Orders*) nigdy nie są pokazywane jako kafelki. |
| Widzisz ją w standardowym menu aplikacji | To samo sprawdzenie, którego Odoo używa dla własnego menu aplikacji: grupy menu i prawo odczytu akcji menu. Pulpit pokazuje dokładnie te same aplikacje co to menu, w tym aplikacje bez własnej akcji (kliknięcie otwiera ich pierwsze podmenu, tak jak w standardowym menu aplikacji). |
| Nie jest samym **My Apps** | Pulpit nie pokazuje kafelka samego siebie. |

Aplikacja priorytetowa, której konkretny użytkownik nie widzi w swoim standardowym menu aplikacji, po prostu nigdy nie pojawia się jako kafelek dla tego użytkownika — lista priorytetowa nigdy nie jest źródłem dodatkowego dostępu. Użytkownicy portalu i użytkownicy publiczni nie widzą menu **My Apps**. Jeśli taki użytkownik mimo to odwoła się do pulpitu, otrzyma pustą listę.

---

## 10. Role dostępu

Moduł nie tworzy nowych grup bezpieczeństwa. Dodaje dwa niewielkie wewnętrzne modele — `app_dashboard.priority.app` i `app_dashboard.tile` — z własnymi regułami dostępu.

| Kto | Otwieranie My Apps | Przypinanie / odpinanie ulubionych | Przeciąganie własnych kafelków | Zmiana własnego Home Screen | Zarządzanie Priority Apps / ustawieniem domyślnym dla bazy danych |
|---|---|---|---|---|---|
| **Użytkownik wewnętrzny** (`base.group_user`) | ✅ | ✅ Własne ulubione, tylko dla dostępnych aplikacji | ✅ Tylko własna kolejność | ✅ Własne ustawienie | ❌ Tylko podgląd listy priorytetowej |
| **Administrator** (`base.group_system`) | ✅ | ✅ Własne ulubione | ✅ Tylko własna kolejność | ✅ Własne ustawienie; może też bezpośrednio zmieniać **Home Action** dowolnego użytkownika | ✅ |
| **Użytkownik portalu / publiczny** | ❌ Menu ukryte, pusta lista | ❌ | ❌ | ❌ | ❌ |

To, co widzi każdy użytkownik, zależy wyłącznie od uprawnień, które już ma w innych aplikacjach. Aby dać komuś nowy kafelek, nadaj mu dostęp do danej aplikacji: `Settings` → `Users & Companies` → `Users` → wybierz użytkownika → prawa dostępu. Własna kolejność kafelków i liczniki użycia każdej osoby (`app_dashboard.tile`) są prywatne — nikt inny nie może odczytać ani zmienić wierszy innego użytkownika, co jest zagwarantowane regułą dostępu na poziomie bazy danych, a nie tylko interfejsem.

---

## 11. Informacje techniczne

| Model | Przeznaczenie |
|---|---|
| `res.users` (rozszerzony) | Dodaje `favorite_app_menu_ids` (Many2many → `ir.ui.menu`) i `home_screen_mode` (Selection: `default_menu` / `apps_dashboard`, domyślnie ustawienie ogólnobazodanowe). |
| `app_dashboard.priority.app` | Jeden wiersz na każdą ogólnobazodanową aplikację priorytetową: `menu_id` (Many2one → `ir.ui.menu`) i `sequence`. Zarządzane z Settings lub `My Apps → Priority Apps`. |
| `app_dashboard.tile` | Jeden wiersz na użytkownika i aplikację, którą otworzył lub przestawił: `user_id`, `menu_id`, `open_count` (licznik użycia), `sequence` i `is_manual` (true, gdy użytkownik przeciągnął ten kafelek). |
| `res.config.settings` (rozszerzony) | Dodaje `app_dashboard_default_home_screen` — pole logiczne zapisywane jako parametr systemowy `app_dashboard.default_home_screen`, które masowo stosuje domyślny Home Screen do każdego aktywnego użytkownika wewnętrznego (nie portalowego) przy zapisie. |

| Element | Identyfikator |
|---|---|
| Akcja klienta | `app_dashboard.action_apps_dashboard` (tag `app_dashboard.AppsDashboard`, ścieżka `my-apps`) |
| Menu | `app_dashboard.menu_apps_dashboard_root`, `app_dashboard.menu_app_dashboard_priority_app` |
| Akcja/widok Priority Apps | `app_dashboard.action_app_dashboard_priority_app`, `app_dashboard.view_app_dashboard_priority_app_list` |
| Widok preferencji | `app_dashboard.view_users_form_simple_modif_app_dashboard` |
| Widok Settings | `app_dashboard.res_config_settings_view_form_app_dashboard` |
| Metody serwera | `res.users.get_app_dashboard_data()`, `res.users.toggle_app_favorite(menu_id)`, `res.users.register_app_open(menu_id)`, `res.users.reorder_apps(ordered_menu_ids, moved_menu_id)` |

---

## 12. Ograniczenia

| Temat | Ograniczenie |
|---|---|
| Zawartość kafelka | Kafelki pokazują ikonę, nazwę, wskaźnik priorytetu i gwiazdkę. Brak liczników na żywo, odznak i podglądów. |
| Przeciąganie | Przeciągać można tylko kafelki w **All Apps**; **Favorites** zachowuje swoją kolejność ustaloną gwiazdką. Podczas aktywnego filtra wyszukiwania przeciąganie jest wyłączone. |
| Ustawienie domyślne dla bazy danych | Włączenie przełącznika w Settings nadpisuje Home Screen każdego aktywnego użytkownika wewnętrznego w tym momencie (użytkownicy portalu są pomijani); nie jest to trwale wymuszona polityka, więc użytkownicy mogą później zmienić własne ustawienie. |
| Synchronizacja Home Action | Jeśli administrator zmieni **Home Action** użytkownika bezpośrednio w formularzu użytkownika, wybór **Home Screen** nie zostanie odpowiednio zaktualizowany. |
| Kiedy zaczyna działać | Zmieniony **Home Screen** obowiązuje po następnym zalogowaniu lub przeładowaniu strony, a nie natychmiast. |
| Dostęp | Pulpit nigdy nie nadaje uprawnień. Aplikacji, której brakuje na pulpicie, brakuje też w standardowym menu aplikacji lub na liście Priority Apps dla tego użytkownika; należy to naprawić uprawnieniami, a nie tym modułem. |
| Nieaktualne ulubione | Ulubione dla aplikacji, do których nie masz już dostępu, są ukrywane, a nie usuwane. Pozostają zapisane w Twoim użytkowniku. |
| Liczenie użycia | Otwarcie aplikacji zwiększa prosty licznik na użytkownika; nie uwzględnia, jak długo w niej przebywałeś ani co w niej robiłeś. |
| Integracje | Brak integracji z jakąkolwiek konkretną aplikacją; moduł działa z dowolnymi zainstalowanymi aplikacjami. |
