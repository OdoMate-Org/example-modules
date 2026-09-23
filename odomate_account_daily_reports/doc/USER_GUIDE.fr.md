# Rapports comptables quotidiens — guide de l'utilisateur

Impressions PDF du livre journal, du livre de caisse et du livre de banque pour Odoo 19 Community.

## Sommaire

1. [Présentation](#1-présentation)
2. [Installation](#2-installation)
3. [Qui peut l'utiliser](#3-qui-peut-lutiliser)
4. [Livre journal](#4-livre-journal)
5. [Livre de caisse](#5-livre-de-caisse)
6. [Livre de banque](#6-livre-de-banque)
7. [Comment les montants sont calculés](#7-comment-les-montants-sont-calculés)
8. [Multi-sociétés](#8-multi-sociétés)
9. [Limites](#9-limites)
10. [Assistance](#10-assistance)

## 1. Présentation

Le module ajoute trois livres imprimables dans **Comptabilité → Analyse → Audit Reports** :

| Rapport | Contenu | Journaux couverts |
|---|---|---|
| **Livre journal** | Toutes les écritures de la période, regroupées en un bloc par jour calendaire | Tous les types de journaux |
| **Livre de caisse** | Mouvements de caisse par compte, avec solde progressif | journaux de type `cash` |
| **Livre de banque** | Mouvements de banque et de carte de crédit par compte, avec solde progressif | journaux de type `bank` et `credit` |

Les trois rapports sont **en lecture seule**. Ils ne créent, ne modifient et ne suppriment jamais d'enregistrement : ils ne sont donc pas affectés par les dates de verrouillage et peuvent être lancés sans risque par un comptable en lecture seule.

Le module réutilise la fenêtre de filtres partagée, l'en-tête de page et le format paysage de **Accounting Audit Reports** (`odomate_account_ledger_reports`), afin que les six rapports aient la même présentation et le même comportement.

L'en-tête imprimé — société, période, journaux et la sélection **Écritures** (*Écritures comptabilisées uniquement* / *Toutes les écritures*) — s'affiche dans la langue de votre session, grâce aux traductions propres du module (`uk`, `pl`, `de`, `es`, `fr`, `pt_BR`).

## 2. Installation

1. Copiez `odomate_account_daily_reports` dans le répertoire addons de votre Odoo.
2. **Applications → Mettre à jour la liste des applications**.
3. Recherchez *Accounting Daily Reports* et cliquez sur **Installer**.

`account` et `odomate_account_ledger_reports` sont installés automatiquement s'ils ne sont pas déjà présents.

## 3. Qui peut l'utiliser

Les trois menus et les trois fenêtres sont accessibles à :

- `account.group_account_manager` — administrateur comptable
- `account.group_account_user` — fonctionnalités comptables complètes
- `account.group_account_readonly` — comptabilité en lecture seule

Les utilisateurs ne disposant que de `account.group_account_invoice` (Facturation) ne voient aucun menu et n'ont aucun accès : l'impression déclenche le message *« Only accounting users can print accounting reports. »*

Le module **ne crée aucun nouveau groupe de sécurité** et ne modifie aucun utilisateur.

## 4. Livre journal

**Comptabilité → Analyse → Audit Reports → Day Book**

| Champ | Signification |
|---|---|
| **Écritures** | *Écritures comptabilisées uniquement* ou *Toutes les écritures* (ajoute les brouillons). Les écritures annulées n'apparaissent jamais. |
| **Date de début** / **Date de fin** | Les deux sont **obligatoires**. Elles prennent par défaut la date du jour. |
| **Journaux** | Laissez vide pour couvrir tous les journaux de la société. |
| **Société** | Visible dans les configurations multi-sociétés. |

Cliquez sur **Print** pour obtenir le PDF, ou sur **Cancel** pour fermer la fenêtre.

L'impression regroupe les écritures en un bloc par jour. Les colonnes sont *Journal, Écriture, Partenaire, Référence, Libellé, Débit, Crédit, Écart* (plus *Devise* pour les utilisateurs multidevises). Chaque jour se termine par une ligne **Total du jour**, et le rapport par une ligne **Total**.

Les jours sans écriture ne produisent aucun bloc : le rapport n'imprime jamais de journée vide. Si rien ne correspond, le PDF affiche *« No entries in this period. »*

Le livre journal **n'a ni solde d'ouverture ni solde progressif** : c'est un relevé chronologique, pas un grand livre.

## 5. Livre de caisse

**Comptabilité → Analyse → Audit Reports → Cash Book**

Les mêmes filtres que le livre journal, plus :

| Champ | Signification |
|---|---|
| **Trier par** | *Date* ou *Journal et partenaire* — modifie l'ordre des écritures à l'intérieur de chaque compte. |
| **Afficher les comptes** | *Tous les comptes*, *Avec mouvements* (par défaut) ou *Avec solde non nul*. |
| **Inclure le solde d'ouverture** | Imprime une ligne **Solde d'ouverture** par compte. Nécessite une date de début. |
| **Avec devise** | Ajoute la colonne *Devise*. Visible uniquement pour les utilisateurs du groupe **Multi-devises**. |

Le champ **Journaux** n'accepte que les journaux de caisse. Choisir un journal de banque déclenche le message *« This book only covers cash journals. »*

L'impression comporte un bloc par compte, triés par code de compte, avec les colonnes *Date, Journal, Écriture, Partenaire, Référence, Libellé, Débit, Crédit, Solde*. Chaque bloc se termine par une ligne **Total du compte**, et le rapport par une ligne **Total**.

### Quels comptes apparaissent

Le livre de caisse ne se contente pas de lister « tout ce que les journaux de caisse ont touché ». L'ensemble des comptes est déterminé à partir de :

- le **compte par défaut** et le **compte d'attente** de chaque journal,
- les comptes d'**encaissements en attente / décaissements en attente** de chaque journal,
- ainsi que tout compte de type `asset_cash` réellement mouvementé par une écriture de la période.

Les comptes appartenant à une autre société sont écartés. Ainsi, un journal de caisse sans compte par défaut configuré s'imprime malgré tout correctement.

## 6. Livre de banque

**Comptabilité → Analyse → Audit Reports → Bank Book**

Identique au livre de caisse, si ce n'est qu'il couvre les journaux de **banque** et de **carte de crédit**, et que son ensemble de comptes inclut également les comptes de type `liability_credit_card`. Choisir un journal de caisse déclenche le message *« This book only covers bank and credit card journals. »*

## 7. Comment les montants sont calculés

### Solde d'ouverture

Lorsque **Inclure le solde d'ouverture** est coché, la ligne de solde d'ouverture additionne tout ce qui a été comptabilisé sur ce compte **avant la date de début**, selon la même règle respectant l'exercice fiscal que le grand livre de *Accounting Audit Reports*. Pour les comptes de caisse et de carte de crédit, qui reportent toujours leur solde, cela revient simplement à toutes les écritures antérieures.

### Solde progressif

La colonne **Solde** est un véritable solde progressif par compte :

```
solde d'une ligne = solde de la ligne précédente + débit de cette ligne − crédit de cette ligne
```

La première ligne part du solde d'ouverture, ou de zéro lorsque celui-ci n'est pas imprimé.

### Solde de clôture

```
Total du compte = Solde d'ouverture + Σ débit − Σ crédit
```

Il est additionné à partir des écritures, jamais lu sur la dernière ligne.

### Exemple chiffré

Compte **101100 Cash A**, période du 01/03/2024 au 31/03/2024, solde d'ouverture activé.

| Ligne | Débit | Crédit | Solde |
|---|---:|---:|---:|
| Solde d'ouverture | 1 000,00 | 0,00 | **1 000,00** |
| 05/03/2024 CASH-IN | 200,00 | 0,00 | **1 200,00** |
| 10/03/2024 CASH-OUT | 0,00 | 50,00 | **1 150,00** |
| **Total du compte** | **200,00** | **50,00** | **1 150,00** |

Vérification : `1 000,00 + 200,00 − 50,00 = 1 150,00`.

La même période dans le livre journal, pour le 05/03/2024 — un encaissement en espèces de 200,00 et un encaissement bancaire de 300,00 :

| | Débit | Crédit | Écart |
|---|---:|---:|---:|
| **Total du jour** | 500,00 | 500,00 | **0,00** |

Dans une comptabilité équilibrée, la colonne **Écart** vaut toujours 0,00 ; une valeur non nulle signale une écriture déséquilibrée.

### Devise

Tous les montants sont imprimés dans la **devise de la société** — rien n'est converti. La colonne facultative *Devise* affiche le montant de l'écriture dans sa propre devise dès que celle-ci diffère de la devise de la société, montants négatifs compris.

## 8. Multi-sociétés

Chaque impression couvre exactement une société : celle choisie dans la fenêtre. Les écritures des autres sociétés n'apparaissent jamais. Choisir une société dans laquelle vous n'êtes pas autorisé à travailler déclenche le message *« You cannot print a report for a company you are not allowed to work in. »*

Les quatre modèles de fenêtres sont transitoires et ne détiennent aucune donnée de société propre : aucune règle d'enregistrement n'est donc nécessaire, le filtre par société se trouvant dans l'étape de validation et dans chaque domaine.

## 9. Limites

- **PDF et HTML uniquement.** Il n'y a ni export XLSX ou CSV, ni version interactive à l'écran.
- **Pas d'exploration détaillée.** Le PDF est une impression ; cliquer sur un montant n'ouvre pas l'écriture correspondante.
- **Une société par impression.** Les livres consolidés multi-sociétés ne sont pas pris en charge.
- **Pas de conversion de devise.** Les écritures en devise étrangère sont présentées à leur valeur comptabilisée en devise de la société ; le rapport ne les reconvertit pas à un taux choisi.
- **Pas de colonnes analytiques.** Si vous avez besoin de la répartition analytique, utilisez le grand livre de *Accounting Audit Reports*.
- **Le livre journal n'a pas de soldes**, par conception ; pour les soldes progressifs et de clôture, utilisez le livre de caisse ou de banque.
- **Pas de données de démonstration.** Ces rapports impriment ce que votre base contient déjà.

## 10. Assistance

- Auteur : OdoMate — <https://odomate.pro>
- Assistance : <support@odomate.pro>

Version anglaise de ce guide : `USER_GUIDE.md`.
