from django.test import TestCase, Client
from django.core.cache import cache
from .views import get_recipe
from .models import Recipe
from datetime import datetime, timedelta
from .RefreshHandler import clean_cache_task
from pathlib import Path
class TestViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.recipe1 = Recipe.objects.create(name='Pasta', desc='Delicious pasta.', image='pasta.jpg')
        self.recipe2 = Recipe.objects.create(name='Pizza', desc='Delicious pizza.', image='pizza.jpg')
    
    def test_get_recipe_with_filter(self):
        recipes = get_recipe('Pasta')
        self.assertIn(self.recipe1, recipes)
        self.assertNotIn(self.recipe2, recipes)

    def test_get_recipe_without_filter(self):
        recipes = get_recipe()
        self.assertIn(self.recipe1, recipes)
        self.assertIn(self.recipe2, recipes)
    
    def test_home_view(self):
        response = self.client.get('/?recipe=Pasta')
        self.assertEqual(response.status_code, 200)
        # This checks if the recipe's name appears in the rendered HTML
        self.assertContains(response, self.recipe1.name)

    def test_show_view(self):
        response = self.client.get(f'/{self.recipe1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.recipe1.name)


    def test_home_view_cache(self):
        cache.set('Pasta', [self.recipe1])
        response = self.client.get('/?recipe=Pasta')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.recipe1.name)

    def test_show_view_cache(self):
        cache.set(self.recipe1.id, self.recipe1)
        response = self.client.get(f'/{self.recipe1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.recipe1.name)
class CleanCacheTaskTest(TestCase):
    def test_cache_cleanup(self):
        # Add a recipe to cache that has a timestamp older than now
        old_recipe = Recipe.objects.create(name='Old Recipe', desc='Delicious pasta.', image='pasta.jpg', timeStamp=int((datetime.now() - timedelta(minutes=10)).timestamp()))
        cache.set('old_recipe', old_recipe)
        
        # Add a recipe to cache that has a timestamp newer than now
        new_recipe = Recipe.objects.create(name='New Recipe', desc='Delicious pizza.', image='pizza.jpg', timeStamp=int((datetime.now() + timedelta(seconds=30)).timestamp()))
        cache.set('new_recipe', new_recipe)

        # Run the clean_cache_task synchronously
        clean_cache_task.now(1)

        # Assert that the old_recipe was removed from the cache
        self.assertIsNone(cache.get('old_recipe'))

        # Assert that the new_recipe is still in the cache
        self.assertIsNotNone(cache.get('new_recipe'))

class HandlePostTest(TestCase):
    def test_handle_post(self):
        client = Client()
        module_root = '/path/to/module_root'
        fpath = '/path/to/fpath'
        cache_root = '/path/to/cache_root'
        response = client.post('/handle_post/', {
            'module_root': module_root,
            'fpath': fpath,
            'cache_root': cache_root,
        })
        self.assertEqual(response.status_code, 200)

        # Form srcPath by joining module_root and fpath
        src_path = f"{module_root}/{fpath}"
        
        # Check that the data has been added to the cache
        cached_data = cache.get(src_path)
        self.assertIsNotNone(cached_data)

        # Verify the content of cached_data
        self.assertEqual(cached_data['srcPath'], src_path)
        self.assertEqual(cached_data['cachePath'], f"{cache_root}/{fpath}")
        self.assertIsInstance(cached_data['timeStamp'], int)