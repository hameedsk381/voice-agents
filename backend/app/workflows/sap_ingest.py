"""
SAP AR report field normalization for workflow ingestion.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Canonical keys used in workflow context / decision engine
SAP_FIELD_ALIASES = {
    "customer_name": ["customer_name", "customer name", "name", "customer"],
    "customer_id": ["customer_id", "customer id", "customerid", "account", "account_id"],
    "branch_code": ["branch_code", "branch", "branch code"],
    "profit_center": ["profit_center", "profit center", "profitcenter"],
    "outstanding_amount": ["outstanding_amount", "outstanding", "amount", "balance", "open_amount"],
    "invoice_number": ["invoice_number", "invoice", "invoice no", "invoice #"],
    "due_date": ["due_date", "due date", "duedate"],
    "aging_bucket": ["aging_bucket", "aging", "aging bucket", "bucket"],
    "email": ["email", "e-mail", "email_address"],
    "contact_number": ["contact_number", "phone", "phone_number", "mobile", "telephone"],
    "payment_history": ["payment_history", "payment history"],
    "status": ["status", "account_status"],
    "remarks": ["remarks", "notes", "comment"],
}


def _norm_key(key: str) -> str:
    return key.strip().lower().replace(" ", "_")


def normalize_sap_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map a CSV/JSON row to canonical workflow context fields."""
    lowered = {_norm_key(k): v for k, v in row.items() if v is not None and str(v).strip() != ""}
    out: Dict[str, Any] = {}
    for canonical, aliases in SAP_FIELD_ALIASES.items():
        for alias in aliases:
            nk = _norm_key(alias)
            if nk in lowered:
                out[canonical] = lowered[nk]
                break

    phone = out.get("contact_number")
    if phone:
        out["phone_number"] = str(phone).strip()

    # Derive aging_days from bucket if missing
    if "aging_days" not in out and out.get("aging_bucket"):
        bucket = str(out["aging_bucket"])
        if "120" in bucket:
            out["aging_days"] = 120
        elif "90" in bucket:
            out["aging_days"] = 90
        elif "60" in bucket:
            out["aging_days"] = 60
        elif "30" in bucket:
            out["aging_days"] = 30
        else:
            out["aging_days"] = 15

    try:
        if out.get("outstanding_amount"):
            out["outstanding_amount"] = float(str(out["outstanding_amount"]).replace(",", ""))
    except (TypeError, ValueError):
        pass

    return out


def rows_from_csv_dicts(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [normalize_sap_row(r) for r in rows if r.get("phone_number") or r.get("contact_number")]
