import dejaview.crawler, dejaview.parser, dejaview.index, dejaview.ranking, dejaview.api


def test_packages_import():
    assert dejaview.__name__ == 'dejaview'
