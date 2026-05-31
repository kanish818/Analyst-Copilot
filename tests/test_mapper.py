from app.services.mapper import map_payload_to_report


def test_map_payload_defaults():
    payload = {
        "headline": "Test headline",
        "key_metrics": [
            {
                "name": "Revenue",
                "value": "7167",
                "confidence": 0.91,
                "source_excerpt": "revenue rose",
                "source_page": "PAGE 1",
            }
        ],
    }

    report = map_payload_to_report("DemoCo", payload)

    assert report.company_name == "DemoCo"
    assert report.recommendation == "Neutral"
    assert report.headline == "Test headline"
    assert len(report.key_metrics) == 1
    assert report.key_metrics[0].name == "Revenue"
    assert report.key_metrics[0].confidence == 0.91
