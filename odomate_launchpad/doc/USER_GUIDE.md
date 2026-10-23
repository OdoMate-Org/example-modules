# User Guide: Launchpad

> A personal, full-screen app launcher that puts the apps you pin and the apps you use most at the top.

---

## Table of Contents

1. [What does this module do](#1-what-does-this-module-do)
2. [Where to find it in Odoo](#2-where-to-find-it-in-odoo)
3. [First-run setup](#3-first-run-setup)
4. [Using the Launchpad](#4-using-the-launchpad)
5. [How tiles are ordered](#5-how-tiles-are-ordered)
6. [Startup Screen](#6-startup-screen)
7. [Demo data](#7-demo-data)
8. [Access and privacy](#8-access-and-privacy)
9. [Limitations](#9-limitations)

---

## 1. What does this module do

Launchpad adds a **Launchpad** app to the main menu. It opens a full-screen page with one square tile for every app you can open. Your pinned apps come first. After them come the apps you opened most in the last 30 days, then everything else in alphabetical order. Each user gets their own ordering, so the screen fits how that person works.

| Capability | Details |
|---|---|
| App tiles | One square tile for each root app you can access. It is the same list as Odoo's standard app switcher, without the Launchpad itself. |
| Usage-based ranking | Each time you click a tile, a usage row (`odomate.launchpad.usage`) is logged. The tile order uses the number of opens in the last 30 days, counted again each time the screen loads. |
| Pinning | The pin button (push-pin icon) on a tile pins or unpins that app for you only (`odomate.launchpad.pin`). Pinned apps always stay at the top. |
| Instant search | The **Search apps...** box filters tiles by name as you type. **Enter** opens the first match and **Escape** clears the box. |
| Startup Screen | **Set as Startup Screen** makes the Launchpad your own Home Action, so it is the first screen after login. |
| Usage tooltip | Hover over a tile to see "Opens in the last 30 days: *N*". |

---

## 2. Where to find it in Odoo

After installation, every internal user (`base.group_user`) sees a new top-level app called **Launchpad**, alongside your other apps in the app switcher — installing the module does not move it to the front of that list or change anyone's startup screen. Clicking it opens the Launchpad screen. You can also go straight to it at:

```
https://<your-odoo>/odoo/launchpad
```

The Launchpad has no submenus, list views or form views. The whole module is this one screen.

---

## 3. First-run setup

You don't have to configure anything. Once the module is installed:

1. Open **Launchpad**. Every app you can access shows as a tile. On a fresh install with no history, the tiles are in alphabetical order.
2. (Optional) Click the pin button on your two or three most important apps to pin them.
3. (Optional) Click **Set as Startup Screen** if you want the Launchpad to open after each login.

There are no settings, company options or scheduled jobs. The ranking updates as you use the screen.

---

## 4. Using the Launchpad

### Opening an app

Click a tile. The Launchpad logs one usage row for you and that app, then opens the app the same way the standard menu does: same default action, same breadcrumbs. If logging fails, the app still opens. Logging is best-effort and never blocks you.

> 💡 Only opens made **from the Launchpad tiles** count. Opening an app from the standard app switcher, a link or a bookmark does not create a usage row.

### Pinning and unpinning

| Action | Result |
|---|---|
| Click the pin button on an unpinned tile | The app is pinned **for you only**. A notification "*App* pinned to the top" appears and the tile moves into the pinned group. |
| Click the pin button on a pinned tile | The pin is removed. A notification "*App* unpinned" appears and the tile goes back to its usage-based position. |

Each user can pin each app only once. A database constraint enforces this (`UNIQUE(user_id, menu_id)`).

### Searching

| Key or action | Result |
|---|---|
| Type in **Search apps...** | Tiles are filtered right away, case-insensitive, matching anywhere in the app name. For example, `time` matches *Timesheets* and *Time Off*. |
| **Enter** | Opens the first tile in the filtered list (and logs the open). |
| **Escape** | Clears the search and shows all tiles again. |

If nothing matches, the screen shows "No app matches your search."

---

## 5. How tiles are ordered

The order is calculated each time the Launchpad screen loads:

1. **Pinned apps** come first, in the order you pinned them. The first app you pinned is first.
2. **Other apps** follow, sorted by how many times you opened them from the Launchpad in the **last 30 days**, highest first.
3. **Ties and apps with no recent opens** are sorted **alphabetically** by name.

There is no stored counter and no cron job. The 30-day count is calculated live from the usage log for the current user on every load. When an open becomes older than 30 days, it simply stops counting.

### Worked example

Suppose the admin pinned **Projects** first and **Timesheets** second. Over the last 30 days they opened apps from the Launchpad this many times:

| App | Opens in last 30 days | Notes |
|---|---|---|
| Projects | 8 | pinned (1st) |
| Timesheets | 6 | pinned (2nd) |
| Employees | 5 | |
| Discuss | 4 | |
| Expenses | 3 | |
| Recruitment | 2 | |
| Settings | 1 | A second Settings open from 45 days ago is **not** counted. |
| Calendar, Contacts, Sales | 0 | no recent history |

Resulting tile order:

| Position | App | Why |
|---|---|---|
| 1 | Projects | pinned first |
| 2 | Timesheets | pinned second |
| 3 | Employees | 5 opens |
| 4 | Discuss | 4 opens |
| 5 | Expenses | 3 opens |
| 6 | Recruitment | 2 opens |
| 7 | Settings | 1 open (the 45-day-old open is ignored, so it's 1, not 2) |
| 8 | Calendar | 0 opens, alphabetical |
| 9 | Contacts | 0 opens, alphabetical |
| 10 | Sales | 0 opens, alphabetical |

Pinned apps ignore usage counts. Timesheets stays second even if it gets 20 opens, because pin order wins. If the admin unpins Timesheets, its 6 opens put it in position 2 of the unpinned group, right after Projects and before Employees.

---

## 6. Startup Screen

The button in the top bar works as a toggle:

| Button shown | What clicking does |
|---|---|
| **Set as Startup Screen** (blue) | Sets **your own** Home Action (`res.users.action_id`) to the Launchpad. A notification says "Launchpad will open after your next login." The button then changes to **Startup Screen**. |
| **Startup Screen** (grey, with a check mark) | Clears your Home Action (only if it currently points to the Launchpad), so Odoo's default start page is used again. A notification says "Launchpad is no longer your startup screen." |

This changes only the current user. Other users are not affected. An administrator can still set or change any user's **Home Action** in **Settings → Users**.

---

## 7. Demo data

If the database was created with demo data, the module adds history for the **Administrator** (`base.user_admin`):

| App | Usage rows | Pinned |
|---|---|---|
| Discuss | 4 (1, 4, 11 and 19 days ago) | only if neither Projects nor Timesheets is installed |
| Settings | 2 (6 days ago and **45 days ago**) | no |
| Projects | 8 (if installed) | yes, 1st |
| Timesheets | 6 (if installed) | yes, 2nd |
| Employees | 5 (if installed) | no |
| Expenses | 3 (if installed) | no |
| Recruitment | 2 (if installed) | no |

The 45-day-old Settings open is there on purpose to show the 30-day window: Settings ranks with **1** open, not 2. The Projects, Timesheets, Employees, Expenses and Recruitment rows (24 opens in total, all within the last 29 days) are created only for apps that are installed. If neither Projects nor Timesheets is installed, **Discuss** is pinned instead, so the demo still shows a pinned tile.

---

## 8. Access and privacy

The module adds no security groups. Every internal user gets the same rights, limited to **their own rows**:

| Model | Who | Read | Create / Edit | Delete | Scope |
|---|---|---|---|---|---|
| `odomate.launchpad.usage` | Internal User (`base.group_user`) | ✅ | ✅ | ✅ | own rows only: `[('user_id', '=', user.id)]` |
| `odomate.launchpad.pin` | Internal User (`base.group_user`) | ✅ | ✅ | ✅ | own rows only: `[('user_id', '=', user.id)]` |

- Users can't see other users' usage or pins, so nobody can tell which apps a colleague opens.
- **Ownership is automatic:** a usage or pin row is always saved for the user who creates it. A `user_id` sent for another user is replaced with the current user (only superuser/system code, such as demo data, can create rows for someone else).
- There is no company restriction. The ranking is per user across all companies.
- **Cascade deletes:** deleting a user removes their usage and pin rows. Uninstalling an app (which deletes its root menu) removes every usage and pin row for that app.
- The Launchpad only lists apps the user can already open. It uses the same visibility as the standard app switcher, and the server checks each logged open or pin against the user's visible root menus.

---

## 9. Limitations

| Topic | Limitation |
|---|---|
| Per-user ranking only | Each user's order is based on their own history. There is no team-wide or company-wide "most popular apps" view, and an admin can't push a default order to other users. |
| Usage log growth | Each tile click adds a row. Rows older than 30 days are **ignored** by the ranking but **never deleted automatically**. There is no purge job. On very busy databases an administrator may want to clean up old rows from time to time. |
| Only Launchpad opens count | Opening an app from the standard app switcher, a URL or a bookmark is not logged and does not affect the ranking. |
| Icons | Tiles use each app's own web icon (image or font icon). If an app has no icon, the tile shows the first letter of the app name. |
| Standard app switcher unchanged | The Launchpad does not reorder Odoo's standard app switcher or the home menu. They keep Odoo's default order. |
| Pin order | Pins appear in the order you created them. There is no drag-and-drop reordering. To change the order, unpin and re-pin apps in the order you want. |
| No admin views | `odomate.launchpad.usage` and `odomate.launchpad.pin` have no list or form views. The data can only be managed through the Launchpad screen (or technical tools). |
| Live calculation | The order is recalculated when the screen loads, not while it's open. Click **Launchpad** again to see a refreshed order (pinning and unpinning reload it immediately). |
