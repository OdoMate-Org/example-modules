# Rapports d'audit comptable — Guide de l'utilisateur

Module : `odomate_account_ledger_reports` · Odoo 19.0 · Version 19.0.1.0.1 · Licence LGPL-3

## Sommaire

1. [Ce que fait ce module](#1-ce-que-fait-ce-module)
2. [Installation](#2-installation)
3. [Qui peut l'utiliser](#3-qui-peut-lutiliser)
4. [Où trouver les rapports](#4-où-trouver-les-rapports)
5. [Le filtre commun](#5-le-filtre-commun)
6. [Grand livre](#6-grand-livre)
7. [Grand livre des partenaires](#7-grand-livre-des-partenaires)
8. [Balance âgée des partenaires](#8-balance-âgée-des-partenaires)
9. [Rapport de taxes](#9-rapport-de-taxes)
10. [Audit des journaux](#10-audit-des-journaux)
11. [Impression de la pièce comptable](#11-impression-de-la-pièce-comptable)
12. [Écrans des écritures comptables](#12-écrans-des-écritures-comptables)
13. [Limites connues](#13-limites-connues)
14. [Pour les développeurs : le contrat stable](#14-pour-les-développeurs--le-contrat-stable)

---

## 1. Ce que fait ce module

Il ajoute les six impressions d'audit comptable classiques que réclament commissaires aux comptes et comptables, sous forme de simples documents PDF, ainsi que deux écrans d'écritures comptables prêts à l'emploi.

| Rapport | Répond à |
|---|---|
| Grand livre | Quels mouvements sur chaque compte, avec un solde cumulé |
| Grand livre des partenaires | Quels mouvements sur les comptes clients/fournisseurs et ce qui reste dû |
| Balance âgée des partenaires | Depuis combien de temps chaque écriture ouverte est échue, par tranches |
| Rapport de taxes | Montants HT et de taxe par taxe, séparés en Ventes et Achats |
| Audit des journaux | Toutes les écritures des journaux sélectionnés, avec un récapitulatif de taxes |
| Pièce comptable | Une page par pièce, à classer ou à joindre à un justificatif |

Tous les rapports lisent les écritures comptables uniquement via l'ORM d'Odoo. Le module n'écrit rien en dehors de ses propres enregistrements de fenêtre et n'ajoute aucun champ à un modèle standard.

## 2. Installation

1. Copiez le dossier `odomate_account_ledger_reports` dans votre chemin d'addons.
2. **Applications → Mettre à jour la liste des applications**.
3. Recherchez *Accounting Audit Reports* et cliquez sur **Activer**.

Les seules dépendances sont `account` et `analytic`, toutes deux livrées avec Odoo Community. Aucune configuration n'est nécessaire après l'installation : pas de page de paramètres, pas de tâche planifiée, pas de données de démonstration.

## 3. Qui peut l'utiliser

Trois groupes comptables Odoo existants peuvent ouvrir les fenêtres et imprimer :

- `account.group_account_manager` — administrateur de facturation
- `account.group_account_user` — comptable
- `account.group_account_readonly` — accès comptable en lecture seule

Le module ne crée aucun groupe propre et n'accorde rien à un autre groupe. Un utilisateur hors de ces trois groupes obtient `Seuls les utilisateurs de la comptabilité peuvent imprimer les rapports comptables.` s'il tente d'imprimer, et ne voit pas les menus.

Chaque enregistrement de fenêtre est transitoire (assistant) : les trois groupes obtiennent lecture, écriture et création, personne n'obtient la suppression — le nettoyage automatique d'Odoo s'en charge.

## 4. Où trouver les rapports

| Rapport | Chemin de menu |
|---|---|
| Grand livre | Comptabilité → Analyse → Rapports d'audit → Grand livre |
| Audit des journaux | Comptabilité → Analyse → Rapports d'audit → Audit des journaux |
| Grand livre des partenaires | Comptabilité → Analyse → Rapports partenaires → Grand livre des partenaires |
| Balance âgée des partenaires | Comptabilité → Analyse → Rapports partenaires → Balance âgée des partenaires |
| Balance âgée clients | Comptabilité → Analyse → Rapports partenaires → Balance âgée clients |
| Balance âgée fournisseurs | Comptabilité → Analyse → Rapports partenaires → Balance âgée fournisseurs |
| Rapport de taxes | Comptabilité → Analyse → Taxes → Rapport de taxes |
| Écritures comptables par compte | Comptabilité → Analyse → Gestion → Écritures comptables par compte |
| Écritures comptables par partenaire | Comptabilité → Analyse → Gestion → Écritures comptables par partenaire |

*Balance âgée clients* et *Balance âgée fournisseurs* sont la même fenêtre que *Balance âgée des partenaires*, avec le type de compte présélectionné et masqué.

L'impression de pièce n'a pas de menu : sélectionnez une ou plusieurs pièces dans **Comptabilité → Comptabilité → Pièces comptables** puis **Imprimer → Pièce comptable**.

## 5. Le filtre commun

Chaque fenêtre part du même ensemble de quatre champs.

| Champ | Signification |
|---|---|
| **Écritures** | *Écritures comptabilisées uniquement* (défaut) ou *Toutes les écritures*. Les pièces annulées ne sont jamais incluses. |
| **Date de début** / **Date de fin** | Bornent les écritures selon leur date comptable. Laissez les deux vides pour « toutes les dates » lorsque la fenêtre le permet. |
| **Journaux** | Laissez vide pour couvrir tous les journaux de la société. |
| **Société** | Visible uniquement dans les bases multi-sociétés. Par défaut votre société active. |

**Imprimer** produit le PDF, **Annuler** ferme la fenêtre.

La fenêtre refuse d'imprimer et en explique la raison lorsque :

- la société choisie ne fait pas partie de celles où vous êtes autorisé à travailler ;
- la date de début est postérieure à la date de fin ;
- un journal sélectionné appartient à une autre société.

## 6. Grand livre

**Champs supplémentaires :** Comptes, Partenaires, Comptes analytiques (uniquement avec la *Comptabilité analytique*), Trier par, Afficher les comptes, Inclure le solde d'ouverture.

**Colonnes :** Date · Journal · Partenaire · Référence · Écriture · Libellé · Débit · Crédit · Solde, plus Devise (utilisateurs multidevises, seulement quand la devise de la ligne diffère de celle de la société) et Analytique (utilisateurs de la comptabilité analytique).

**Afficher les comptes**

- *Tous les comptes* — tous les comptes de la société, même sans mouvement.
- *Avec mouvements* (défaut) — comptes ayant des écritures sur la période, ou un solde d'ouverture non nul.
- *Avec un solde non nul* — écarte les comptes dont ouverture + débit − crédit arrondit à zéro.

**Trier par** change l'ordre à l'intérieur d'un compte : *Date* trie par date, numéro d'écriture, id ; *Journal et partenaire* trie par journal, puis partenaire, puis date.

### Exemple chiffré — le solde d'ouverture

Comptabilité de la société, exercice = année civile, date de début **2024-03-01**, **Inclure le solde d'ouverture** coché.

| Écriture | Date | Compte 121000 (Clients) | Compte 400000 (Produits) |
|---|---|---|---|
| E1 | 2023-06-15 | débit 1 000,00 | crédit 1 000,00 |
| E2 | 2024-02-10 | débit 500,00 | crédit 500,00 |
| E3 | 2024-03-15 | débit 250,00 | crédit 250,00 |

Ouvertures imprimées :

- **121000** est un compte de bilan : il s'ouvre avec *tout* ce qui est comptabilisé avant la date de début, soit 1 000,00 + 500,00 = **1 500,00**.
- **400000** est un compte de résultat : il ne s'ouvre qu'avec l'exercice en cours ; E1 tombe sur l'exercice précédent et est exclu, il reste **−500,00**.

Le solde cumulé de 121000 affiche alors 1 500,00 sur la ligne *Solde d'ouverture* et 1 750,00 après E3 ; la ligne de total du compte affiche Débit 250,00, Crédit 0,00, Solde 1 750,00.

## 7. Grand livre des partenaires

**Champs supplémentaires :** Partenaires, Type de compte, Inclure les écritures lettrées, Afficher le montant en devise (utilisateurs multidevises).

**Type de compte** correspond aux types de compte Odoo : *Comptes clients* → `asset_receivable`, *Comptes fournisseurs* → `liability_payable`, *Comptes clients et fournisseurs* → les deux.

**Colonnes :** Date · Journal · Compte · Écriture · Référence · Libellé · Débit · Crédit · Solde (repartant de zéro pour chaque partenaire), plus Devise.

Chaque bloc partenaire se termine par Débit, Crédit, solde de clôture et **Montant dû** — la somme des montants résiduels des écritures.

Une écriture reste masquée tant que **Inclure les écritures lettrées** n'est pas coché uniquement lorsqu'elle est lettrée *entièrement* — c'est-à-dire lorsque toutes les écritures de l'autre côté de son lettrage sont elles aussi rapprochées et qu'il ne reste rien dû. Une facture partiellement réglée continue d'imprimer à la fois sa propre ligne et celle de son règlement tant que ce n'est pas le cas, de sorte que le solde de clôture indique toujours ce qui reste dû ; une facture entièrement réglée et son règlement disparaissent ensemble, et réapparaissent ensemble lorsque **Inclure les écritures lettrées** est coché. Les écritures sans partenaire ne sont jamais imprimées ici ; leur place est dans le Grand livre.

Vous pouvez aussi l'imprimer directement depuis un contact : sélectionnez un ou plusieurs contacts dans **Contacts**, puis **Imprimer → Grand livre des partenaires**. La fenêtre s'ouvre avec ces partenaires, le type de compte *Comptes clients et fournisseurs* et les écritures lettrées incluses.

### Exemple chiffré — une facture partiellement réglée garde son règlement sur sa propre ligne

Une facture client de 1 000,00 est comptabilisée, puis partiellement réglée de 400,00. Imprimée avec **Inclure les écritures lettrées** décoché :

| Ligne | Débit | Crédit | Solde |
|---|---|---|---|
| Facture | 1 000,00 | | 1 000,00 |
| Règlement | | 400,00 | 600,00 |
| **Total du partenaire** | **1 000,00** | **400,00** | **600,00** |

**Montant dû** affiche lui aussi 600,00 — les deux lignes s'impriment car 600,00 restent dus côté facture, même si le règlement lui-même n'a plus rien à rapprocher. Une fois la facture entièrement réglée, les deux lignes disparaissent de la vue décochée et ne réapparaissent ensemble qu'en cochant **Inclure les écritures lettrées**.

## 8. Balance âgée des partenaires

**Champs supplémentaires :** À la date du (obligatoire, aujourd'hui par défaut), Durée de la période (jours) (obligatoire, 30 par défaut), Type de compte, Partenaires. Date de début et Journaux ne sont pas utilisés par ce rapport et sont masqués.

Chaque écriture ouverte est placée dans l'une des six colonnes selon son antériorité en jours entiers, où antériorité = *À la date du* − (date d'échéance, ou date comptable en l'absence d'échéance) :

| Colonne | Antériorité (P = Durée de la période) |
|---|---|
| Non échu | antériorité ≤ 0 |
| 1 - P | 1 … P |
| P+1 - 2P | P+1 … 2P |
| 2P+1 - 3P | 2P+1 … 3P |
| 3P+1 - 4P | 3P+1 … 4P |
| +4P | antériorité > 4P |

Une ligne dont les six colonnes sont nulles est supprimée. Les écritures sans partenaire sont regroupées dans une ligne **Partenaire inconnu**. Tous les montants sont en devise de la société ; aucune conversion n'est appliquée.

### Exemple chiffré — répartition avec P = 30, au 2024-06-30

| Écriture | Échéance | Antériorité | Montant | Colonne |
|---|---|---|---|---|
| A | 2024-06-30 | 0 | 10,00 | Non échu |
| B | 2024-06-29 | 1 | 20,00 | 1 - 30 |
| C | 2024-05-31 | 30 | 30,00 | 1 - 30 |
| D | 2024-05-30 | 31 | 40,00 | 31 - 60 |
| E | 2024-03-01 | 121 | 50,00 | +120 |

Ligne imprimée : Non échu 10,00 · 1-30 50,00 · 31-60 40,00 · 61-90 0,00 · 91-120 0,00 · +120 50,00 · Total 150,00.

### Exemple chiffré — le résiduel est mesuré *à la date*

Une facture de 1 000,00 est comptabilisée le 2024-03-10 et partiellement réglée de 400,00 le 2024-05-20.

- Au **2024-04-30**, le règlement n'a pas encore eu lieu : le rapport affiche **1 000,00**.
- Au **2024-06-30**, il affiche **600,00**, et la ligne de règlement elle-même se solde à zéro et disparaît.

Le rapport recalcule le résiduel à partir de l'historique de lettrage au lieu de lire le `amount_residual` du jour : c'est ce qui rend correcte une balance âgée antidatée.

## 9. Rapport de taxes

Seul le filtre commun s'applique ; Date de début et Date de fin sont obligatoires et valent par défaut le premier jour du mois en cours et aujourd'hui.

Le rapport liste toutes les taxes de vente et d'achat actives de la société en deux sections. Un groupe de taxes est représenté par ses taxes filles sous le type de la taxe mère ; le groupe lui-même n'est pas une ligne. Pour chaque taxe :

- **Montant HT** — la somme des soldes des écritures qui portent la taxe.
- **Montant de la taxe** — la somme des soldes des lignes de taxe générées par la taxe.

Dans la section **Ventes**, les deux montants changent de signe pour que le chiffre d'affaires soit positif ; dans **Achats**, ils sont imprimés tels que comptabilisés. Aucune valeur absolue n'est jamais prise, si bien que les avoirs réduisent réellement les montants. Les lignes nulles sur les deux montants sont omises, et une section vide imprime *Aucun mouvement de taxe sur cette période.*

### Exemple chiffré — un avoir réduit les montants de vente

Mars 2024, une taxe de vente à 20 % :

| Document | HT | Taxe |
|---|---|---|
| Facture client, 1 000,00 + 20 % | 1 000,00 | 200,00 |
| Avoir, 400,00 + 20 % | −400,00 | −80,00 |
| **Ligne « Ventes » imprimée** | **600,00** | **120,00** |

## 10. Audit des journaux

**Champs supplémentaires :** Journaux (obligatoire — par défaut les journaux de vente et d'achat de votre société), Trier les écritures par, Afficher le montant en devise.

Une section par journal sélectionné, dans l'ordre propre des journaux. **Colonnes :** Écriture · Date · Compte · Partenaire · Libellé · Débit · Crédit, plus Devise. Chaque section se termine par les totaux Débit et Crédit du journal.

Lorsque le journal comporte des écritures taxées, un petit tableau récapitulatif Taxe / Base imposable / Montant de la taxe suit, avec la même règle de signe que le Rapport de taxes (taxes de vente inversées). Les journaux sans écriture taxée n'ont tout simplement pas ce tableau.

## 11. Impression de la pièce comptable

Pas de fenêtre : sélectionnez des pièces et utilisez **Imprimer → Pièce comptable**. Une page par pièce, chacune imprimée avec l'en-tête et la devise de sa propre société.

L'en-tête indique le numéro de pièce, le journal, la date, le partenaire, la référence et le statut. Le tableau des écritures affiche Compte · Libellé · Partenaire · Analytique · Débit · Crédit · Devise, dans l'ordre des lignes de la pièce, hors lignes de section, de sous-section et de note. La ligne de total additionne débit et crédit dans la devise de la société de la pièce — égaux pour toute pièce comptabilisée.

## 12. Écrans des écritures comptables

Deux vues enregistrées sur `account.move.line`, toutes deux en liste / tableau croisé / graphique avec le panneau de recherche standard d'Odoo, et toutes deux sans les lignes de section, de sous-section et de note :

- **Écritures comptables par compte** — groupées par compte, écritures comptabilisées uniquement.
- **Écritures comptables par partenaire** — groupées par partenaire, écritures comptabilisées, pré-filtrées sur les comptes clients, les comptes fournisseurs et les écritures non lettrées.

Ce sont des listes Odoo ordinaires : vous pouvez regrouper, filtrer, exporter et ouvrir une pièce depuis là.

## 13. Limites connues

- **Devise de la société uniquement.** Chaque montant est exprimé en devise de la société. La colonne facultative Devise affiche le montant en devise étrangère de l'écriture à titre indicatif ; rien n'est converti.
- **Pas d'export Excel.** Les rapports sont uniquement en PDF. Utilisez les deux écrans d'écritures pour un tableur.
- **La balance âgée ignore les journaux.** Par conception elle couvre tous les journaux de la société ; le champ Journaux est masqué dans cette fenêtre.
- **Pas de navigation détaillée.** Les PDF sont des documents statiques et ne renvoient pas vers Odoo.
- **`account.report` intact.** Le module n'étend pas le moteur de rapports dynamiques d'Odoo : ces rapports n'apparaissent donc pas dans son sélecteur de variantes.
- **Périmètre du rapport de taxes.** Seules les taxes dont `type_tax_use` vaut `sale` ou `purchase` sont listées ; les taxes *None* n'apparaissent jamais.
- **Colonne « Analytique ».** L'information analytique est lue depuis `analytic_distribution` ; les pourcentages affichés sont ceux de la répartition, pas des montants.

## 14. Pour les développeurs : le contrat stable

Les modules frères peuvent s'appuyer sur ce qui suit, qui ne changera pas :

**Modèle** `odomate.account.report.filter` (`TransientModel` concret, base d'héritage par prototype) avec les champs `company_id`, `date_from`, `date_to`, `journal_ids`, `target_move` et les méthodes :

| Élément | Nature | Rôle |
|---|---|---|
| `_odomate_journals()` | enregistrement | Journaux sélectionnés, ou tous les journaux de la société |
| `_odomate_state_domain()` | enregistrement | Condition d'état pour le `target_move` choisi |
| `_odomate_line_domain(date_field='date', date_from=None, date_to=None)` | enregistrement | Le domaine de base des écritures |
| `_odomate_check_filter()` | enregistrement | Validation ; à étendre avec `super()` |
| `_odomate_report_data()` | enregistrement | La charge utile, composée uniquement de types simples |
| `_odomate_print(report_xmlid=None)` | enregistrement | Valider puis renvoyer l'action de rapport |
| `action_odomate_print()` | enregistrement | Le bouton Imprimer de la fenêtre |
| `_odomate_report_xmlid` | attribut de classe | XML ID de rapport par défaut de la fenêtre |
| `_odomate_options_from_data(data)` | modèle | Retransforme la charge utile en enregistrements et dates |
| `_odomate_check_report_access()` | modèle | Lève `AccessError` hors des trois groupes comptables |
| `_odomate_initial_balance_domain(company, date_from, journals=None, target_move='posted')` | modèle | Domaine du solde d'ouverture |

**Vue** `odomate_account_ledger_reports.view_odomate_account_report_filter_form` — héritez avec `mode="primary"` et ajoutez vos champs après le nœud `journal_ids` ou le nœud `target_move`. Ce sont les deux seuls points d'ancrage pris en charge.

**QWeb** `odomate_account_ledger_reports.report_filter_header` — paramètres `company`, `date_from`, `date_to`, `journals`, `target_move_label`.

**Format de papier** `odomate_account_ledger_reports.paperformat_odomate_ledger_landscape` — A4 paysage, marges de 10 mm.

**Menu** `odomate_account_ledger_reports.menu_odomate_account_reports_audit` — le dossier *Rapports d'audit*.

Tout le reste — champs propres à chaque fenêtre, méthodes utilitaires de construction des lignes, noms des modèles de rapport, formulation des modèles QWeb, ordre des clés des dictionnaires — est interne et peut changer.

---

© OdoMate · <https://odomate.pro> · <support@odomate.pro>
