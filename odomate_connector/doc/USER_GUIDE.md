# OdoMate Connector — user guide

## What this module does

It produces one file: `odomate_context.json`, a **redacted structural description of your
Odoo database**. OdoMate reads that file so the modules it generates for you fit the system
they will actually be installed on — your installed apps, your custom fields, the views you
have already modified, the settings you have switched on.

Nothing is sent anywhere. The module has no network access at all: you press a button, you
get a file, and you decide what happens to it.

## Installing

1. Copy the `odomate_connector` folder into your Odoo addons path (or install it from the
   Odoo Apps Store).
2. In Odoo: **Apps → Update Apps List**, then search for *OdoMate Connector* and install it.

Requires Odoo 19 — Community or Enterprise. No extra Python packages.

## Exporting a snapshot

1. Enable the developer/technical menus if they are not visible
   (**Settings → General Settings → Developer Tools → Activate the developer mode**).
2. Go to **Settings → Technical → Export OdoMate Context**.
3. Press **Generate snapshot**.
4. You will see a summary — Odoo version and edition, how many modules, models, fields,
   customized views, settings and security groups were found.
5. Click the `odomate_context.json` link to download the file.

You need the *Settings* administration group to see the menu or run the export.

## Reading the file before you share it

The file is pretty-printed JSON, meant to be opened and read. The top-level keys are:

| Key | What it holds |
|---|---|
| `instance` | Odoo version, edition, installed languages, multi-company flag, and a SHA-256 **hash** of the database UUID |
| `modules` | Every installed module, with a `source` of `core`, `enterprise`, `oca`, `thirdparty` or `custom` |
| `models` | Models and their fields — type, selection values, relation target, and whether the field is a customization |
| `views` | Only views you created or edited, with their XML |
| `settings` | Boolean and selection configuration toggles |
| `config_params` | An allowlisted handful of system parameters |
| `groups` | Security groups and **how many** users hold each |
| `automations` | Names and models of automated actions — never their code |
| `record_counts` | Approximate row counts per model |
| `truncated` | Anything dropped to stay under the size cap (usually empty) |

If you want to satisfy yourself that no business data is present, searching the file for a
customer name, an employee name, or an email address is a fair test — none will be there.

Note that field *names* such as `password` or `totp_secret` do appear under `models`: those
are part of Odoo's public schema, and only the names are present. No values of any kind are
exported.

## What OdoMate can do with it

The snapshot describes your database accurately whatever is installed on it.
What OdoMate can currently *do* with each part of it differs:

- **Odoo Community** is what OdoMate generates for today. An Enterprise installation is
  still described accurately in the snapshot, but generation is not aimed at it.
- **Commercial third-party modules** are recorded by name, version and public schema —
  never their code. Whether that is enough for OdoMate to reliably account for such a
  module's behaviour while generating is **not yet verified**; treat it as unconfirmed
  rather than supported.
- The **test replica cannot install commercial modules**, so a generated module is never
  automatically tested against them. Anything depending on a paid module needs your own
  testing before you rely on it.

## How often to re-export

Whenever your environment changes in a way that matters — you install or remove apps, add
custom fields, or change configuration. A snapshot is a point-in-time picture; an old one
simply describes an older version of your system.

## Removing it

Uninstall the module. It stores nothing, so there is nothing left behind. Any file you
already downloaded is yours and is unaffected.

## Support

support@odomate.pro — https://www.odomate.pro
