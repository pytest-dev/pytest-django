from .app.models import Item


class TestBarePytestClass:
    def setup_method(self, method):
        Item.objects.create(name='unique_name')

    def test_fresh_database(self):
        assert Item.objects.count() == 1

    def test_fresh_database_again(self):
        self.test_fresh_database()
