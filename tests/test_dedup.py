def test_dedupe_candidates_structure(client):
    res = client.post("/leads/dedupe-candidates?threshold=0.5&limit=10")
    assert res.status_code == 200
    clusters = res.json()
    assert isinstance(clusters, list)
    assert len(clusters) > 0

    for cluster in clusters:
        assert "cluster_id" in cluster
        assert "lead_count" in cluster
        assert cluster["lead_count"] >= 2
        assert "confidence" in cluster
        assert 0.0 <= cluster["confidence"] <= 1.0
        assert "leads" in cluster
        assert len(cluster["leads"]) == cluster["lead_count"]

        # Verify lead fields inside cluster
        for lead in cluster["leads"]:
            assert "record_id" in lead
            assert "full_name" in lead
            assert "email" in lead
            assert "phone_digits" in lead


def test_dedupe_candidates_limit(client):
    limit = 3
    res = client.post(f"/leads/dedupe-candidates?threshold=0.5&limit={limit}")
    assert res.status_code == 200
    clusters = res.json()
    assert isinstance(clusters, list)
    assert len(clusters) <= limit


def test_dedupe_candidates_threshold_filtering(client):
    threshold = 0.98
    res = client.post(f"/leads/dedupe-candidates?threshold={threshold}&limit=20")
    assert res.status_code == 200
    clusters = res.json()
    assert isinstance(clusters, list)

    for cluster in clusters:
        assert cluster["confidence"] >= threshold


def test_dedupe_clusters_contain_distinct_record_ids(client):
    res = client.post("/leads/dedupe-candidates?threshold=0.5&limit=10")
    assert res.status_code == 200
    clusters = res.json()

    for cluster in clusters:
        record_ids = [lead["record_id"] for lead in cluster["leads"]]
        # No duplicate record IDs inside the same cluster
        assert len(record_ids) == len(set(record_ids))
