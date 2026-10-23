# SPEC.md — the specification this module was generated from

This is the specification the module in this folder was generated from. It was written by
the OdoMate team in Ukrainian; the English translation comes first, the Ukrainian original
follows it.

Everything in `models/`, `views/`, `security/`, `static/src/`, `demo/` and `tests/` was
produced by OdoMate from it.

**Two generated versions, and no hand correction to the code.** Version 1 was generated from
this document. Version 2 came from one enhancement round: the Launchpad menu no longer becomes
every user's first screen after installation (the specification says nothing changes until a
user chooses it), an app with no icon of its own now shows Odoo's default icon instead of a
broken image, and the demo-data test is skipped on a database without demo data. Nothing in the
module was written or corrected by hand. The publication changes are the store listing page,
the banner, the icon, the user-guide PDFs, this file, and the manifest metadata that points at
them (`summary`, `website`, `images`).

**What was verified before publication.** On freshly created Odoo 20 Community databases:
with demo data and Project, Timesheets, Employees, Expenses and Recruitment installed, the
module installs with no errors and its 17 tests pass, the two pinned apps come first and the
rest follow by use; without demo data, it installs with no errors and the demo-data test is
skipped. Pinning, search and the startup-screen button were checked in a browser, on a desktop
and at phone width.

---

## English translation

**Module:** `odomate_launchpad`

A separate start screen with square icons for every app available to the user (standard and
custom), sorted by the user's own frequency of use over the last 30 days, with the option to
pin favourite apps at the top.

### Models

`odomate.launchpad.usage`: `user_id` (Many2one → `res.users`, required, `ondelete=cascade`),
`menu_id` (Many2one → `ir.ui.menu`, required, `ondelete=cascade`), `used_on` (Datetime,
required, default = now).
Purpose: a log of every app opened by a given user. An app's 30-day "weight" is computed live
from it (`read_group` over `used_on >= now - 30 days`), with no stored counter — so the data is
always current and needs no cron recalculation.

`odomate.launchpad.pin`: `user_id` (Many2one → `res.users`, required, `ondelete=cascade`),
`menu_id` (Many2one → `ir.ui.menu`, required, `ondelete=cascade`), `sequence` (Integer,
default = 10).
Constraint: the pair (`user_id`, `menu_id`) is unique — a `models.Constraint`.
Purpose: manual pinning of apps, personal to each user.

No new model is created for the "list of apps" itself — the icon, name and action are taken
directly from the existing root `ir.ui.menu` records (`web_icon`, `name`, `action`), the same way
Odoo's standard app switcher already builds them — so custom `odomate_hr_*` modules appear on
the screen automatically.

### Business rules

Opening an icon: a `odomate.launchpad.usage` row is created for the current user and that app
menu, and then the same action runs that a click on that app in the standard side menu would
open.

Tile order, per user:

1. Pinned apps (`odomate.launchpad.pin`), by `sequence`.
2. All other apps — by number of opens in the last 30 days, descending.
3. Apps with no history (new employees, a freshly installed app) or with an equal count — by
   name, alphabetically.

Pin / unpin: a button on the tile creates or deletes the current user's own
`odomate.launchpad.pin` row — it does not affect anyone else's pins.

"Set as startup screen" button: writes this action as the home action (the standard Odoo field
that decides what opens after login) for the current user only — each user turns it on for
themselves; by default nothing changes.

Visibility: the screen shows only the root apps the user already has access to — a natural
consequence of reading `ir.ui.menu` as the user (without `sudo`); no extra access check is
needed.

Deleting a user or removing an app (deleting its root menu) automatically removes the related
log and pin rows (`ondelete=cascade`) — no orphaned records are left behind.

### Views & UX

A full-screen client action (a grid of square icons: app icon + name); tile layout and size as
in Odoo's standard app switcher, so it looks native and works correctly on mobile.

A search / filter field above the grid — narrows the tiles by name instantly.

On each tile — a small pin / unpin toggle button.

A "Set as startup screen" button in the screen's top bar.

A separate top-level menu item that opens this screen manually at any time (available to all
internal users).

The technical models `odomate.launchpad.usage` and `odomate.launchpad.pin` have no lists or
forms of their own; they only serve data to the grid, and the user does not manage them
directly.

OWL complexity: a custom client component of medium complexity (grid + search + on-the-fly
sorting), with no server-side reports or dashboard.

### Security

Access on `odomate.launchpad.usage` and `odomate.launchpad.pin`: group `base.group_user` — full
CRUD.

Record rule on both models: domain `[('user_id', '=', user.id)]` for `base.group_user` — each
user sees and changes only their own log and their own pins, with no company restriction
(sufficient, since the list of apps is already filtered through `ir.ui.menu`).

The menu that opens the screen is available to `base.group_user` (which every internal user
already holds), with no need for a manager group or a new group hierarchy.

### Demo data

Since the amount of demo data was not specified separately, a default is proposed: ~25
`odomate.launchpad.usage` rows for the demo admin, spread over the last 30 days across 5–6
installed apps (Projects, HR, Timesheets, Expenses, Recruitment), with noticeably more opens in
2 of them, so the "most used" sorting is visible from the first login.

2 pinned apps for the demo admin (for example, Projects and Timesheets), to show that pinned
tiles always come first.

### Constraints & notes

The 30-day window is computed live each time the screen opens (no stored counter) — a
deliberate choice, to avoid stale data and to need no cron recalculation or recalculation when
settings are saved.

Ranking and pins are strictly personal, per user — not shared across the company and not
cross-company.

---

## Original (Ukrainian)

Module: odomate_launchpad
Окремий стартовий екран із квадратними іконками всіх доступних користувачу програм (рідних і кастомних), відсортованими за особистою частотою використання за останні 30 днів, із можливістю закріплювати улюблені програми нагорі.

Models
odomate.launchpad.usage: user_id (Many2one -> res.users, required, ondelete=cascade), menu_id (Many2one -> ir.ui.menu, required, ondelete=cascade), used_on (Datetime, required, default=now)
Призначення: журнал кожного відкриття програми конкретним користувачем; на його основі "вага" програми за 30 днів рахується наживо (read_group за used_on >= now - 30 days), без збереження лічильника — тому дані завжди актуальні і не потребують cron-перерахунку.
odomate.launchpad.pin: user_id (Many2one -> res.users, required, ondelete=cascade), menu_id (Many2one -> ir.ui.menu, required, ondelete=cascade), sequence (Integer, default=10)
Constraint: унікальність пари (user_id, menu_id) — модель models.Constraint.
Призначення: ручне закріплення програм, персонально для кожного користувача.
Жодна нова модель для самого "списку програм" не створюється — іконка, назва й дія беруться напряму з існуючих кореневих записів ir.ui.menu (web_icon, name, action), так само як їх уже будує стандартний перемикач програм Odoo — тож кастомні odomate_hr_* модулі потраплять на екран автоматично.

Business Rules
Відкриття іконки: створюється рядок odomate.launchpad.usage для поточного користувача й цього меню-програми, після чого виконується та сама дія, яку відкрив би клік по цій програмі в стандартному бічному меню.
Порядок тайлів для кожного користувача:
1. Закріплені програми (odomate.launchpad.pin), за sequence.
2. Решта програм — за кількістю відкриттів за останні 30 днів, за спаданням.
3. Програми без історії (нові співробітники, щойно встановлений додаток) або з однаковою кількістю — за алфавітом назви.

Закріплення/відкріплення: кнопка на тайлі створює або видаляє власний рядок odomate.launchpad.pin поточного користувача — на чужі закріплення не впливає.
Кнопка "Встановити стартовою": записує цю дію як домашню дію (стандартне поле Odoo, що визначає, що відкривається після входу) лише для поточного користувача — кожен вмикає собі самостійно, за замовчуванням нічого не змінюється.
Видимість: екран показує лише ті кореневі програми, до яких у користувача вже є доступ — це природний наслідок читання ir.ui.menu від імені користувача (без sudo), додаткової перевірки прав не потрібно.
Видалення користувача або вимкнення програми (видалення її кореневого меню) автоматично прибирає пов'язані рядки журналу й закріплень (ondelete=cascade) — не залишає "сирітських" записів.

Views & UX
Повноекранна клієнтська дія (грід квадратних іконок: значок програми + назва), верстка й розміри тайлів — як у стандартному перемикачі програм Odoo, щоб виглядало "рідно" і коректно на мобільному.
Поле пошуку/фільтра над гріддю — миттєво звужує список тайлів за назвою.
На кожному тайлі — невелика кнопка-прапорець "закріпити/відкріпити".
Кнопка "Встановити стартовою" у верхній панелі екрана.
Окремий пункт верхнього меню, що відкриває цей екран вручну в будь-який момент (доступний усім внутрішнім користувачам).
Технічні моделі odomate.launchpad.usage і odomate.launchpad.pin — без власних списків/форм, це лише служать дані для гріда, користувач ними не керує напряму.
OWL-складність: власний клієнтський компонент середньої складності (грід + пошук + сортування на льоту), без серверних звітів/дошборду.

Security
Доступ на odomate.launchpad.usage і odomate.launchpad.pin: група base.group_user — повний CRUD.
Record rule на обох моделях: домен [('user_id', '=', user.id)] для base.group_user — кожен бачить і змінює лише власний журнал і власні закріплення, без обмеження за компанією (достатньо, оскільки сам список програм уже відфільтрований через ir.ui.menu).
Меню для відкриття екрана — доступне групі base.group_user (нею вже володіє кожен внутрішній користувач), без потреби в менеджерській групі чи новій ієрархії груп.

Demo Data
Оскільки обсяг демоданих не був заданий окремо — пропоную дефолт: ~25 рядків odomate.launchpad.usage для демо-адміна, розподілених за останні 30 днів по 5–6 встановлених програмах (Проєкти, HR, Табелі, Витрати, Рекрутинг), з помітно більшою кількістю відкриттів у 2 з них, щоб одразу на першому вході було видно ефект сортування "найчастіше використовувані".
2 закріплені програми для демо-адміна (наприклад, Проєкти та Табелі), щоб продемонструвати, що закріплені тайли завжди першими.

Constraints & Notes
30-денне вікно рахується наживо при кожному відкритті екрана (без збереження лічильника) — свідоме рішення, щоб уникнути застарілих даних і не потребувати cron-перерахунку чи перерахунку при збереженні налаштувань.
Рейтинг і закріплення — строго персональні per-user, не спільні для компанії та не крос-компанійні.
