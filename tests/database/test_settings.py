from sqlalchemy.engine import make_url

from wapang.database.settings import DatabaseSettings


def test_shared_db_url_preserves_special_characters_in_credentials():
    settings = DatabaseSettings(
        _env_file=None, dialect="mysql", driver="pymysql", host="db.example.test",
        port=3306, user="user@example", password="p@ss:/?#%word", database="wapang",
    )
    parsed = make_url(settings.url)
    assert parsed.username == settings.user
    assert parsed.password == settings.password
    assert parsed.host == settings.host
