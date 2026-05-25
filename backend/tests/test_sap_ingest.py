from app.workflows.sap_ingest import normalize_sap_row


def test_normalize_sap_row_maps_columns():
    row = normalize_sap_row(
        {
            "Customer Name": "Acme Corp",
            "Customer ID": "C-99",
            "Contact Number": "+15551234567",
            "Outstanding": "1,250.50",
            "Aging Bucket": "90+",
            "E-mail": "billing@acme.com",
        }
    )
    assert row["customer_name"] == "Acme Corp"
    assert row["customer_id"] == "C-99"
    assert row["phone_number"] == "+15551234567"
    assert row["outstanding_amount"] == 1250.5
    assert row["email"] == "billing@acme.com"
    assert row["aging_days"] == 90
