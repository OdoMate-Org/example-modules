# User Guide: Apps Dashboard

> A personal "My Apps" home screen: square tiles for every Odoo app you can already open, with favorites pinned on top, admin-curated priority apps shown first, the rest sorted by how often you use them, and drag-to-reorder if you want full control.

---

## Table of Contents

1. [What does this module do](#1-what-does-this-module-do)
2. [Where to find it in Odoo](#2-where-to-find-it-in-odoo)
3. [First-run setup](#3-first-run-setup)
4. [Using the My Apps dashboard](#4-using-the-my-apps-dashboard)
5. [Favorites](#5-favorites)
6. [Priority apps, usage order and reordering tiles](#6-priority-apps-usage-order-and-reordering-tiles)
7. [Making the dashboard a home screen](#7-making-the-dashboard-a-home-screen)
8. [Worked example](#8-worked-example)
9. [Which apps appear on the dashboard](#9-which-apps-appear-on-the-dashboard)
10. [Access roles](#10-access-roles)
11. [Technical reference](#11-technical-reference)
12. [Limitations](#12-limitations)

---

## 1. What does this module do

Apps Dashboard adds a **My Apps** screen that shows every application you can access as a large square tile with its icon and name. You can pin the apps you use most with a star so they always appear first, filter the tiles by typing part of an app name, and optionally make the dashboard the first screen you see after logging in — for yourself, or for everyone in the database if you're an administrator.

Administrators can also curate a database-wide **Priority Apps** list (Settings > General Settings) so the apps the company has already decided are "always available" show up first for every user. Apps that are neither favorited nor on the priority list are sorted by how often each person actually opens them, and anyone can drag tiles to set their own order if they want more control than that.

The dashboard never grants new access: it only shows apps that already appear in your native Odoo app menu.

| Capability | Details |
|---|---|
| App tiles | One tile per top-level app you can open: app icon, app name, a priority pin indicator, and a star in the top-right corner. |
| Favorites | Click the star to pin an app. Pinned apps are shown in a **Favorites** section above everything else. Favorites are personal and stored on your user. |
| Priority apps | Administrators pick apps, in order, that always come first for every user among apps that aren't favorited (Settings > General Settings > My Apps Dashboard > **Manage Priority Apps**). |
| Usage order | Apps you have neither favorited, prioritized nor manually reordered are sorted by how often you personally open them — the ones you use most rise to the top automatically. |
| Drag to reorder | Drag any non-favorite tile to a new spot. Once you've dragged a tile, your own order takes over for that section instead of the automatic usage order. |
| Search | The **Search apps...** box filters tiles by name as you type (case-insensitive, matches any part of the name). |
| Open an app | Clicking a tile opens the app exactly as the native app menu does, and counts toward that app's usage order. |
| Home screen | In **My Preferences**, the **Home Screen** option lets you choose between **Default Menu** and **Apps Dashboard**. Administrators can also set the dashboard as the default home screen for every user at once. |

---

## 2. Where to find it in Odoo

After installation, a new top-level app called **My Apps** appears in the main app menu. It is placed at the end of the app list (sequence 9999), so it never replaces your normal landing app unless the dashboard is chosen (by you or by an administrator) as the Home Screen, and it is visible to all internal users.

- **My Apps** — opens the dashboard. You can also go directly to the URL `/odoo/my-apps`.
- **My Apps → Priority Apps** — administrators only. Manage the database-wide list of apps pinned first for everyone.
- **Avatar menu (top right) → My Preferences → Home Screen** — chooses whether Odoo opens the dashboard after your own login.
- **Settings → General Settings → My Apps Dashboard** — administrators only. Set the dashboard as the default home screen for the whole database, and a shortcut button to **Manage Priority Apps**.

---

## 3. First-run setup

No setup is required for regular use. Every internal user can open **My Apps** immediately after installation. Each user sees only their own apps, their own favorites, and their own usage-based ordering.

> 💡 If the module was installed with demo data, **Employees**, **Project** and **Timesheets** (whichever are installed) are pre-configured as database-wide Priority Apps, and the administrator additionally has these plus, when installed, **Invoicing**, **Time Off**, **Recruitment**, **CRM**, **Sales** and **Purchase** pinned as personal favorites. If none of the priority candidates are installed, no priority apps are pre-configured and favorites fall back to **Settings**.

Administrators who want the dashboard to be everyone's landing screen, or who want to curate the Priority Apps list, do this once from **Settings → General Settings → My Apps Dashboard** — see [section 6](#6-priority-apps-usage-order-and-reordering-tiles) and [section 7](#7-making-the-dashboard-a-home-screen).

---

## 4. Using the My Apps dashboard

**Path:** `My Apps`

The screen has a **My Apps** title and a **Search apps...** box at the top, followed by the tiles.

| Element | What it does |
|---|---|
| Tile (icon + name) | Click anywhere on the tile to open the app. Opening a tile also counts toward that app's usage order. |
| Star (top-right corner of a tile) | Hollow star = not a favorite (tooltip **Add to favorites**). Yellow star = favorite (tooltip **Remove from favorites**). Clicking the star does not open the app. |
| Thumbtack icon (top-left corner of a tile) | Shown when the app is on the database-wide Priority Apps list and you haven't manually moved it. |
| **Favorites** section | Shown only when you have at least one favorite that you can still access. Always first. |
| **All Apps** section | Everything you haven't favorited: priority apps first (in the order an administrator set), then the rest sorted by how often you open them, or by your own drag order once you've reordered anything. The **All Apps** heading appears only when a **Favorites** section is shown above it. |
| Drag and drop | While the search box is empty, drag any tile in **All Apps** to a new position to set your own order for that tile (and everything around it). Dragging is disabled while a search filter is active. |
| **Search apps...** | Filters both sections at once. Clear the box to see all tiles again (and to re-enable drag and drop). |

Messages you may see:

| Message | Meaning |
|---|---|
| **No apps available yet** — "You do not have access to any application. Ask your administrator to grant you access rights." | Your user cannot open any app. Ask an administrator to give you access rights. |
| **No app matches your search.** | No app name contains the text you typed. Change or clear the search. |
| **This app is no longer available to you.** (warning notification) | You clicked a star on an app you have lost access to since the page was loaded. The dashboard reloads and the tile disappears. |

---

## 5. Favorites

**To pin an app:** click the hollow star on its tile. The star turns yellow and the tile moves to the **Favorites** section.

**To unpin an app:** click the yellow star. The tile moves back to **All Apps**, where it is placed according to the priority / usage / drag order described in [section 6](#6-priority-apps-usage-order-and-reordering-tiles).

Rules:

- Favorites are personal. Pinning an app does not affect any other user.
- You can only pin apps you can see on the dashboard. The server refuses to pin an app you are not allowed to open.
- If you later lose access to a pinned app (for example, an administrator removes you from a group), the app simply disappears from your dashboard. The favorite is not deleted: if your access is restored, the app reappears in **Favorites** automatically.

---

## 6. Priority apps, usage order and reordering tiles

Tiles in **All Apps** (everything that isn't a personal favorite) follow this order, from first to last:

1. **Priority apps** — the apps an administrator has pinned for the whole database, in the order they set, for as long as you haven't manually moved that tile yourself.
2. **Your most-used apps** — among the rest, the app you personally open most often comes first, then the next most-used, and so on. An app you have never opened sits behind any app you have opened at least once.
3. **Your own drag order** — as soon as you drag any tile in **All Apps**, that tile (and from then on, any tile you drag) keeps the exact position you gave it, ahead of the automatic priority/usage ordering for that tile. Apps you haven't personally reordered yet still follow rules 1 and 2 around the ones you have.

**Managing the database-wide Priority Apps list** (administrators only):

**Path:** `Settings → General Settings → My Apps Dashboard → Manage Priority Apps`, or `My Apps → Priority Apps`.

1. Open **Manage Priority Apps**. You see a list with a drag handle and the **App** column.
2. Click **New**, pick a root app from **App**, and save. It is added at the end of the list (its sequence is set after the current last row). The **App** dropdown only offers apps that can appear on a dashboard: root apps visible in the normal app menu (outside developer mode), excluding **My Apps** itself. Each saved row is titled with its app's name.
3. Drag rows by their handle to change the order everyone sees priority apps in.
4. Remove a row to stop treating that app as a priority app for everyone (it still shows up in **All Apps**, sorted by usage like any other app).

Priority apps are a database-wide setting: every eligible user sees the same priority apps in the same order (unless they've personally dragged that tile elsewhere on their own dashboard). An app only appears as a priority tile for users who can already see it in their native app menu — the priority list never grants extra access.

**Reordering your own tiles:**

While the search box is empty, drag any tile in **All Apps** to a new spot and drop it. Your browser shows the tile moving as you drag. The new order is saved immediately and is personal to you — it does not change what anyone else sees.

---

## 7. Making the dashboard a home screen

### Per user

**Path:** avatar menu (top right) → `My Preferences` → field **Home Screen** (on the **Preferences** tab, below **Email Signature**; administrators also find it on the **Preferences** tab of **Settings → Users** for any internal user)

| Option | Effect |
|---|---|
| **Default Menu** | Odoo opens as usual after login. If your Home Action was the dashboard, it is cleared. |
| **Apps Dashboard** | Your user's **Home Action** is set to the **My Apps** dashboard, so Odoo opens on the dashboard after login. |

Click **Save**. The new home screen takes effect the next time you log in or reload Odoo.

> ⚠️ If an administrator has given you a different Home Action (for example, the Sales pipeline), choosing **Default Menu** does not remove it. Only the dashboard Home Action set by this option is cleared. Choosing **Apps Dashboard** replaces whatever Home Action you had.

### For the whole database (administrators)

**Path:** `Settings → General Settings → My Apps Dashboard → Apps Dashboard is the default home screen`

Turning this toggle **on** and clicking **Save** immediately sets every active internal user's Home Screen to **Apps Dashboard** (portal and public users are never changed and never get the dashboard as their home action) — it overwrites each user's individual choice at that moment. Turning it **off** and saving sets every active internal user back to **Default Menu**. Anyone can still go to their own **My Preferences** afterward and pick whichever option they personally prefer; the database-wide setting only establishes what happens *at the moment you save it*, it does not lock the choice.

A user who signs up after you've turned this on starts with the database-wide default; a user created while it's off starts with **Default Menu**, as before.

---

## 8. Worked example

Anna is a project manager. Her user can open six apps: **Discuss**, **Calendar**, **Contacts**, **Project**, **Timesheets** and **Employees**. **Settings** is not on her dashboard because she is not an administrator. The administrator has already set **Project** as a database-wide Priority App.

1. Anna clicks **My Apps**. **All Apps** shows **Project** first (it's a priority app), then the other five sorted by her usage so far — all tied at zero, so they keep their native menu order: Discuss, Calendar, Contacts, Timesheets, Employees. She has no favorites yet, so there's no separate **Favorites** section.
2. She clicks the star on **Timesheets**. It moves into a new **Favorites** section above everything else.
3. Over the next few days she opens **Contacts** eight times and **Calendar** twice. The next time she opens the dashboard, **All Apps** now reads: Project (still priority, still first), Contacts (most used), Discuss, Calendar, Employees.
4. She decides she wants **Discuss** right after **Project** regardless of usage, so she drags its tile up by one position. From then on, **Discuss** keeps that position even as her usage of other apps changes, while Contacts/Calendar/Employees continue to reorder automatically around it based on usage.
5. She opens **My Preferences**, sets **Home Screen** to **Apps Dashboard** and clicks **Save**. After her next login, Odoo opens directly on **My Apps**.
6. Later, an administrator removes Anna's Timesheets access. On her next visit, the **Favorites** section disappears (she has no other favorites), and **Timesheets** is no longer on the dashboard at all. When her access is restored, **Timesheets** comes back as a favorite without her having to pin it again.

---

## 9. Which apps appear on the dashboard

An app appears on your dashboard only if it meets all of these conditions:

| Condition | Explanation |
|---|---|
| It is a top-level app menu | Sub-menus (for example, *Sales → Orders*) never appear as tiles. |
| You can see it in the native app menu | The same check Odoo uses for its own app menu: the menu's groups and read access to the menu's action. The dashboard shows exactly the same apps as that menu, including apps that have no action of their own (clicking them opens their first sub-menu, as in the native app menu). |
| It is not **My Apps** itself | The dashboard does not show a tile for itself. |

A priority app that a particular user cannot see in their native app menu simply never appears as a tile for that user — the priority list is never a source of extra access. Portal and public users cannot see the **My Apps** menu. If such a user calls the dashboard anyway, they receive an empty list.

---

## 10. Access roles

The module creates no new security groups. It adds two small internal models — `app_dashboard.priority.app` and `app_dashboard.tile` — with their own access rules.

| Who | Open My Apps | Pin / unpin favorites | Drag to reorder own tiles | Change own Home Screen | Manage Priority Apps / database-wide default |
|---|---|---|---|---|---|
| **Internal user** (`base.group_user`) | ✅ | ✅ Own favorites, only for apps they can access | ✅ Own order only | ✅ Own preference | ❌ Read-only visibility of the priority list |
| **Administrator** (`base.group_system`) | ✅ | ✅ Own favorites | ✅ Own order only | ✅ Own preference; can also edit **Home Action** directly on any user | ✅ |
| **Portal / public user** | ❌ Menu hidden, empty list | ❌ | ❌ | ❌ | ❌ |

What each user sees depends entirely on the rights they already have in other apps. To give someone a new tile, grant them access to that app: `Settings` → `Users & Companies` → `Users` → select user → access rights. Each person's own tile order and usage counts (`app_dashboard.tile`) are private to them — nobody else can read or write another user's rows, enforced by a database access rule, not just by the user interface.

---

## 11. Technical reference

| Model | Purpose |
|---|---|
| `res.users` (extended) | Adds `favorite_app_menu_ids` (Many2many → `ir.ui.menu`) and `home_screen_mode` (Selection: `default_menu` / `apps_dashboard`, defaulting to the database-wide setting). |
| `app_dashboard.priority.app` | One row per database-wide priority app: `menu_id` (Many2one → `ir.ui.menu`) and `sequence`. Managed from Settings or `My Apps → Priority Apps`. |
| `app_dashboard.tile` | One row per user per app they've opened or reordered: `user_id`, `menu_id`, `open_count` (usage counter), `sequence` and `is_manual` (true once the user has dragged that tile). |
| `res.config.settings` (extended) | Adds `app_dashboard_default_home_screen`, a Boolean stored as the `app_dashboard.default_home_screen` system parameter, that bulk-applies the default Home Screen to every active internal (non-portal) user on save. |

| Item | Identifier |
|---|---|
| Client action | `app_dashboard.action_apps_dashboard` (tag `app_dashboard.AppsDashboard`, path `my-apps`) |
| Menu | `app_dashboard.menu_apps_dashboard_root`, `app_dashboard.menu_app_dashboard_priority_app` |
| Priority Apps action/view | `app_dashboard.action_app_dashboard_priority_app`, `app_dashboard.view_app_dashboard_priority_app_list` |
| Preferences view | `app_dashboard.view_users_form_simple_modif_app_dashboard` |
| Settings view | `app_dashboard.res_config_settings_view_form_app_dashboard` |
| Server methods | `res.users.get_app_dashboard_data()`, `res.users.toggle_app_favorite(menu_id)`, `res.users.register_app_open(menu_id)`, `res.users.reorder_apps(ordered_menu_ids)` |

---

## 12. Limitations

| Topic | Limitation |
|---|---|
| Tile content | Tiles show icon, name, a priority indicator and a star. There are no live counters, badges or previews. |
| Drag and drop | Only tiles in **All Apps** can be dragged; **Favorites** keeps its existing star-driven order. Dragging is disabled while a search filter is active. |
| Database-wide default | Turning on the Settings toggle overwrites every active internal user's Home Screen at that moment (portal users are skipped); it is not a continuously-enforced policy, so users can change their own preference afterward. |
| Home Action sync | If an administrator changes a user's **Home Action** directly in the user form, the **Home Screen** selection is not updated to match. |
| When it takes effect | A changed **Home Screen** applies after the next login or page reload, not immediately. |
| Access | The dashboard never grants access. An app missing from the dashboard is also missing from the native app menu or from the Priority Apps list for that user; fix it with access rights, not with this module. |
| Stale favorites | Favorites for apps you can no longer access are hidden, not deleted. They stay stored on your user. |
| Usage counting | Opening an app increments a simple per-user counter; it does not distinguish how long you stayed in the app or what you did there. |
| Integrations | No integration with any specific app; the module works with whatever apps are installed. |
