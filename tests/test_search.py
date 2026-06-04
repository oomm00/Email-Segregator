from src.common.search.es_client import INDEX_EMAILS


def test_es_index_name():
    assert INDEX_EMAILS == "shipping_emails"


def test_es_client_imports():
    from src.common.search.es_client import es_client, index_email, search_emails
    assert es_client is not None
    assert callable(index_email)
    assert callable(search_emails)
