from ai_assisted_mini_lead_management_system.db.models import Lead


def test_ingest_new_lead_creates_record(client, db_session):
    payload = {
        "name": "Bruce Wayne",
        "email": "bruce.wayne@testdomain.com",
        "phone": "+1 415 555 0199",
        "company": "Wayne Enterprises",
        "country": "United States",
        "message": "Interested in enterprise deployment",
        "form_name": "Demo Request",
        "page_url": "/demo",
    }
    res = client.post("/leads/ingest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["action"] == "created"
    lead = data["lead"]
    assert lead["email"] == "bruce.wayne@testdomain.com"
    assert lead["lead_status"] == "New"
    assert lead["source_channel"] == "Website"
    assert lead["source_detail"] == "Demo Request - /demo"
    assert lead["record_id"] > 0


def test_ingest_duplicate_email_case_insensitive_updates_lead(client, db_session):
    initial_payload = {
        "name": "Diana Prince",
        "email": "diana.prince@testdomain.com",
        "phone": "447911123456",
        "company": "Themyscira Global",
        "country": "United Kingdom",
        "message": "First contact note",
    }
    res1 = client.post("/leads/ingest", json=initial_payload)
    assert res1.status_code == 200
    created_id = res1.json()["lead"]["record_id"]

    duplicate_payload = {
        "name": "Diana Prince",
        "email": "  DIANA.PRINCE@TESTDOMAIN.COM  ",
        "phone": "447911123456",
        "company": "Themyscira Global Corp",
        "country": "United Kingdom",
        "message": "Second inbound request",
    }
    res2 = client.post("/leads/ingest", json=duplicate_payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["action"] == "updated"
    updated_lead = data2["lead"]
    assert updated_lead["record_id"] == created_id
    assert "First contact note" in updated_lead["notes"]
    assert "Second inbound request" in updated_lead["notes"]


def test_ingest_duplicate_phone_digits_fallback_updates_lead(client, db_session):
    initial_payload = {
        "name": "Clark Kent",
        "email": "clark.kent@testdomain.com",
        "phone": "+1 (212) 555-4321",
        "company": "Daily Planet",
        "country": "United States",
        "message": "Met on newsroom floor",
    }
    res1 = client.post("/leads/ingest", json=initial_payload)
    assert res1.status_code == 200
    created_id = res1.json()["lead"]["record_id"]

    duplicate_phone_payload = {
        "name": "Clark Kent",
        "email": "ckent.personal@testdomain.com",
        "phone": "1-212-555-4321",
        "company": "Daily Planet News",
        "country": "United States",
        "message": "Follow up via personal email",
    }
    res2 = client.post("/leads/ingest", json=duplicate_phone_payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["action"] == "updated"
    assert data2["lead"]["record_id"] == created_id
    assert "Follow up via personal email" in data2["lead"]["notes"]


def test_ingest_batch_mixed_new_and_existing(client, db_session):
    seed_payload = {
        "name": "Barry Allen",
        "email": "barry.allen@testdomain.com",
        "phone": "15559876543",
        "company": "STAR Labs",
        "country": "United States",
        "message": "Initial test note",
    }
    res_seed = client.post("/leads/ingest", json=seed_payload)
    assert res_seed.status_code == 200
    existing_id = res_seed.json()["lead"]["record_id"]

    batch_payload = [
        {
            "name": "Hal Jordan",
            "email": "hal.jordan@testdomain.com",
            "phone": "15551112233",
            "company": "Ferris Aircraft",
            "country": "United States",
            "message": "New lead from aviation summit",
        },
        {
            "name": "Barry Allen",
            "email": "barry.allen@testdomain.com",
            "phone": "15559876543",
            "company": "STAR Labs Inc",
            "country": "United States",
            "message": "Second message from Barry",
        },
    ]

    res_batch = client.post("/leads/ingest", json=batch_payload)
    assert res_batch.status_code == 200
    batch_data = res_batch.json()
    assert isinstance(batch_data, list)
    assert len(batch_data) == 2

    assert batch_data[0]["action"] == "created"
    assert batch_data[0]["lead"]["email"] == "hal.jordan@testdomain.com"

    assert batch_data[1]["action"] == "updated"
    assert batch_data[1]["lead"]["record_id"] == existing_id
    assert "Second message from Barry" in batch_data[1]["lead"]["notes"]
