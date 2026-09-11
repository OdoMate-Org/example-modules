import logging

_logger = logging.getLogger(__name__)

DEDUCTION_CATEGORY_CODE = "DED"
DEDUCTION_RULE_XMLID = "odomate_hr_salary_advance.hr_salary_rule_advance_deduction"


def post_init_hook(env):
    """Bind the shipped ``ADV_DEDUCT`` salary rule to the deduction category.

    ``payroll.DED`` is only defined by the payroll module's *demo* data, so a
    production database frequently has no such xmlid while still owning a
    perfectly good category with code ``DED``. Resolving it here — searching
    first, creating only when genuinely absent — keeps the install working on
    both kinds of database.
    """
    category = env["hr.salary.rule.category"].sudo().search(
        [("code", "=", DEDUCTION_CATEGORY_CODE)], limit=1
    )
    if not category:
        category = env["hr.salary.rule.category"].sudo().create({
            "name": "Deduction",
            "code": DEDUCTION_CATEGORY_CODE,
        })
        _logger.info(
            "odomate_hr_salary_advance: created salary rule category %s",
            DEDUCTION_CATEGORY_CODE,
        )

    rule = env.ref(DEDUCTION_RULE_XMLID, raise_if_not_found=False)
    if rule and not rule.category_id:
        rule.sudo().category_id = category.id
