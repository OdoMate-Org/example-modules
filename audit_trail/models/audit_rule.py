from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError

TRACKED_ACTIONS = ("create", "write", "unlink", "export", "read")

ACTION_SELECTION = [
    ("create", "Created"),
    ("write", "Updated"),
    ("unlink", "Deleted"),
    ("export", "Exported"),
    ("read", "Viewed"),
]

DETAIL_LEVEL_SELECTION = [
    ("full", "Full - old and new values"),
    ("light", "Light - new values only"),
]


class AuditRule(models.Model):
    _name = "audit.rule"
    _description = "Audit Watch Rule"
    _order = "model_name, id"

    name = fields.Char(
        required=True,
        help="Free label for this watch rule, e.g. 'Contacts - full audit'.",
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Watched Model",
        required=True,
        ondelete="cascade",
        index=True,
        help="The kind of record being watched.",
    )
    model_name = fields.Char(
        string="Technical Model",
        related="model_id.model",
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("active", "Active")],
        default="draft",
        required=True,
        copy=False,
        help="Nothing is recorded while the rule is in Draft.",
    )
    detail_level = fields.Selection(
        selection=DETAIL_LEVEL_SELECTION,
        required=True,
        default="full",
        help="Full re-reads the record before every change to capture the old "
             "value. Light skips that extra read and stores new values only.",
    )
    track_create = fields.Boolean(string="Record Creations", default=True)
    track_write = fields.Boolean(string="Record Updates", default=True)
    track_unlink = fields.Boolean(string="Record Deletions", default=True)
    track_export = fields.Boolean(string="Record Exports", default=False)
    track_read = fields.Boolean(
        string="Record Views",
        default=False,
        help="Records one event per row displayed. On list views this can "
             "generate a very large number of events.",
    )
    keep_deleted_snapshot = fields.Boolean(
        string="Keep Deletion Snapshot",
        default=False,
        help="Store the field values of a record at the moment it is deleted. "
             "Only meaningful when deletions are recorded.",
    )
    excluded_user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="audit_rule_excluded_users_rel",
        column1="rule_id",
        column2="user_id",
        string="Excluded Users",
        help="Actions performed by these users produce no event at all.",
    )
    excluded_field_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="audit_rule_excluded_fields_rel",
        column1="rule_id",
        column2="field_id",
        string="Excluded Fields",
        domain="[('model_id', '=', model_id)]",
        help="These fields never appear in recorded values, nor in deletion "
             "snapshots.",
    )
    date_confirmed = fields.Datetime(readonly=True, copy=False)

    _unique_model_company = models.Constraint(
        "UNIQUE(model_id, company_id)",
        "Only one audit rule may watch a given model for a given company.",
    )

    def _check_no_duplicate(self, model_id, company_id, ignore_ids=()):
        """Point at the existing rule before the database constraint fires.

        @api.constrains runs after the INSERT, by which time the UNIQUE index
        has already aborted the transaction, so the friendly message has to be
        produced ahead of super(). The database constraint stays as the
        race-proof backstop.
        """
        if not model_id or not company_id:
            return
        domain = [("model_id", "=", model_id), ("company_id", "=", company_id)]
        if ignore_ids:
            domain.append(("id", "not in", list(ignore_ids)))
        duplicate = self.sudo().search(domain, limit=1)
        if duplicate:
            raise ValidationError(_(
                "%(model)s is already watched for %(company)s by the rule "
                "\"%(rule)s\". Edit that rule instead of adding a second one.",
                model=duplicate.model_id.display_name,
                company=duplicate.company_id.display_name,
                rule=duplicate.name,
            ))

    @api.constrains("model_id", "excluded_field_ids")
    def _check_excluded_fields_model(self):
        for rule in self:
            stray = rule.excluded_field_ids.filtered(
                lambda field, rule=rule: field.model_id != rule.model_id
            )
            if stray:
                raise ValidationError(_(
                    "The excluded fields %(fields)s do not belong to %(model)s.",
                    fields=", ".join(stray.mapped("name")),
                    model=rule.model_id.display_name,
                ))

    @api.onchange("model_id")
    def _onchange_model_id(self):
        self.excluded_field_ids = [fields.Command.clear()]

    @api.model_create_multi
    def create(self, vals_list):
        default_company_id = self.env.company.id
        for vals in vals_list:
            self._check_no_duplicate(
                vals.get("model_id"), vals.get("company_id", default_company_id)
            )
        rules = super().create(vals_list)
        self.env.registry.clear_cache()
        return rules

    def write(self, vals):
        if "model_id" in vals or "company_id" in vals:
            for rule in self:
                self._check_no_duplicate(
                    vals.get("model_id", rule.model_id.id),
                    vals.get("company_id", rule.company_id.id),
                    ignore_ids=self.ids,
                )
        result = super().write(vals)
        self.env.registry.clear_cache()
        return result

    def unlink(self):
        result = super().unlink()
        self.env.registry.clear_cache()
        return result

    def action_confirm(self):
        self.write({"state": "active", "date_confirmed": fields.Datetime.now()})
        return True

    def action_draft(self):
        self.write({"state": "draft"})
        return True

    def action_view_logs(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "audit_trail.action_audit_log"
        )
        action["domain"] = [("rule_id", "=", self.id)]
        action["context"] = {"search_default_group_by_action": 1}
        return action

    @api.model
    @tools.ormcache()
    def _audit_watched_model_names(self):
        rules = self.sudo().search([("state", "=", "active")])
        return frozenset(rules.mapped("model_name"))

    @api.model
    def _audit_rule_config(self, model_name, company_id):
        """Snapshot of the active rule watching ``model_name``.

        Read live rather than registry-cached: exclusions, detail level and the
        tracked-action set are edited by administrators, and serving a stale
        policy would silently record a user who is on the exclusion list. The
        cheap guard that keeps unwatched models off this path entirely is
        ``_audit_watched_model_names``, which is cached.
        """
        rule = self.sudo().search(
            [
                ("model_name", "=", model_name),
                ("state", "=", "active"),
                ("company_id", "=", company_id),
            ],
            limit=1,
        )
        if not rule:
            return None
        return {
            "rule_id": rule.id,
            "detail_level": rule.detail_level,
            "keep_deleted_snapshot": rule.keep_deleted_snapshot,
            "actions": frozenset(
                action for action in TRACKED_ACTIONS if rule["track_%s" % action]
            ),
            # active_test=False: an archived user must stay excluded, otherwise
            # archiving an integration account silently resumes recording it.
            "excluded_user_ids": frozenset(
                rule.with_context(active_test=False).excluded_user_ids.ids
            ),
            "excluded_fields": frozenset(rule.excluded_field_ids.mapped("name")),
        }
