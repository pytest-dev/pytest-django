from app.models import Item
import py

def test_load_fixtures():
    py.test.load_fixture('items') #@UndefinedVariable
    assert Item.objects.count() == 1
    assert Item.objects.all()[0].name == 'Fixture item'

def test_load_fixtures_again():
    """Ensure fixtures are only loaded once."""
    test_load_fixtures()

@py.test.urls('tests.urls_test')
def test_urls(client):
    assert client.get('/test_url/').content == 'Test URL works!'
    
