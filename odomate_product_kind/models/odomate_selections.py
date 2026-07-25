# Mirror of odomate.product.kind.route_type. Declared as a plain module-level
# constant (not a related Selection) so it can be reused verbatim wherever a
# route-type Selection field is needed outside the source model — a related
# Selection is dropped from fields_get during registry setup in Odoo 19,
# which makes any view referencing it crash the OWL parser with "field is
# undefined".
ROUTE_TYPE_SELECTION = [
    ('sold', "Sold (Finished Good)"),
    ('manufactured', "Manufactured"),
    ('semi_finished', "Semi-Finished"),
    ('component', "Component"),
    ('service', "Service"),
    ('transport', "Transport"),
    ('other', "Other"),
]
