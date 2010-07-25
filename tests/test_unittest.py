from django.test import TestCase
from app.models import Item

class TestFixtures(TestCase):
    fixtures = ['items']
    
    def test_fixtures(self):
        assert Item.objects.count() == 1
        assert Item.objects.all()[0].name == 'Fixture item'
    
    def test_fixtures_again(self):
        """Ensure fixtures are only loaded once."""
        self.test_fixtures()

class TestSetup(TestCase):
    def setUp(self):
        """setUp should be called after starting a transaction"""
        assert Item.objects.count() == 0
        Item.objects.create(name='Some item')
        Item.objects.create(name='Some item again')
        
    def test_count(self):
        self.assertEqual(Item.objects.count(), 2)
        assert Item.objects.count() == 2
        Item.objects.create(name='Foo')
        self.assertEqual(Item.objects.count(), 3)
    
    def test_count_again(self):
        self.test_count()

    def tearDown(self):
        """tearDown should be called before rolling back the database"""
        assert Item.objects.count() == 3


class TestFixturesWithSetup(TestCase):
    fixtures = ['items']
    
    def setUp(self):
        assert Item.objects.count() == 1
        Item.objects.create(name='Some item')
    
    def test_count(self):
        assert Item.objects.count() == 2
        Item.objects.create(name='Some item again')
    
    def test_count_again(self):
        self.test_count()
    
    def tearDown(self):
        assert Item.objects.count() == 3

    
class TestUrls(TestCase):
    urls = 'tests.urls_test'
    
    def test_urls(self):
        self.assertTrue(self.client.get('/test_url/').content == 'Test URL works!')
