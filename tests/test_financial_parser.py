from app.services.financial_parser import merge_financial_rows, parse_financial_rows_from_text


def test_parse_financial_rows_from_text_extracts_values():
    text = """
    [PAGE 2] Highlights for Q2FY26 include:
    Revenue at 29,795 million; growth of 15.8% YoY
    EBITDA margin at 13.4%
    Net profit at 3,287 million
    """
    rows = parse_financial_rows_from_text(text)
    assert rows
    first = rows[0]
    assert first["period"] == "Q2FY26"
    assert first["revenue"] == "29795"
    assert first["pat"] == "3287"
    assert first["ebitda_margin"] == "13.4"


def test_merge_financial_rows_parser_precedence_and_fill():
    parser_rows = [{"period": "Q2FY26", "revenue": "29795", "ebitda": "", "pat": "3287", "ebitda_margin": "", "source": "parser", "source_page": "PAGE 2"}]
    llm_rows = [{"period": "Q2FY26", "revenue": "", "ebitda": "4908", "pat": "", "ebitda_margin": "16.5", "source": "llm", "source_page": "PAGE 2"}]
    merged = merge_financial_rows(parser_rows, llm_rows)
    assert len(merged) == 1
    row = merged[0]
    assert row["revenue"] == "29795"
    assert row["ebitda"] == "4908"
    assert row["pat"] == "3287"
    assert row["ebitda_margin"] == "16.5"
    assert row["source"] == "parser"
