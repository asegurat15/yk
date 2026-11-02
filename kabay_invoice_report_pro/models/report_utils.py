# -*- coding: utf-8 -*-


def split_product_description(raw_name):
    """Split a report line without removing user-entered description lines.

    In Odoo the line ``name`` can contain the product display name on the first
    line and an editable sales/invoice description on the following lines.
    Those following lines are business content, even when their text is very
    similar to the product name, so the report must preserve them verbatim
    instead of trying to de-duplicate them.
    """
    normalized = (raw_name or "").replace("\r\n", "\n").replace("\r", "\n")
    parts = [part.strip() for part in normalized.split("\n") if part.strip()]

    return {
        "primary": parts[0] if parts else "",
        "detail": "\n".join(parts[1:]) if len(parts) > 1 else "",
    }
