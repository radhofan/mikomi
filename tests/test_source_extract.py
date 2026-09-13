from api.schemas import SourceChannel


def test_extract_event_note(client):
    payload = {"text": "Met him at the SFF booth, scanned our QR code"}
    res = client.post("/leads/source-extract", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["channel"] == SourceChannel.EVENT.value
    assert isinstance(data["detail"], str)
    assert len(data["detail"]) > 0


def test_extract_empty_notes_fallback(client):
    payload = {"text": "   "}
    res = client.post("/leads/source-extract", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["channel"] == SourceChannel.OTHER.value
    assert "Empty notes" in data["detail"]


def test_extract_referral_note(client):
    payload = {"text": "Sarah from Acme referred John to us"}
    res = client.post("/leads/source-extract", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["channel"] == SourceChannel.REFERRAL.value
    assert isinstance(data["detail"], str)
    assert len(data["detail"]) > 0


def test_extract_channel_strictly_in_enum(client):
    allowed_channels = {c.value for c in SourceChannel}
    payload = {"text": "Found us through organic google search then booked a demo"}
    res = client.post("/leads/source-extract", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["channel"] in allowed_channels
