'''
Tests for recipe API
'''

from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (Recipe, Tag, Ingredient)

from recipe.serializers import (RecipeSerializer, RecipeDetailSerializer)


RECIPE_URL = reverse('recipe:recipe-list')

def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

def detail_url(recipe_id):
    '''Create and return a recipe detail URL'''
    return reverse('recipe:recipe-detail', args=[recipe_id])

# função helper para não ter que fica criando recipe toda hora.
# agiliza processo de teste
def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title':'Sample Recipe Title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf'
    }
    # caso tenhamos recebido algum valor no params, podemos substituir no valor default
    # e caso não tenha vindo algum dado, a função assume os dados do default
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe

def create_user(**params):
    '''helper function to create new users'''
    return get_user_model().objects.create_user(**params)

class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''teste se autenticação é necessaria para chamar a API'''
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeAPITests(TestCase):
    ''' testa API que precisam estar autenticadas'''

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='testpass123')

        self.client.force_authenticate(self.user)

    def test_retrive_recipe_list(self):
        '''test to recover recipe as list'''
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # serializer.data, dicionario de informações passado pele serializer
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """test list of recipes is limited to authenticated user"""
        other_user = create_user(
           email= 'other@example.com',
            password = 'password123'
        )

        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        # focus on filter for the user we're authenticated
        # can't bring recipe from other user
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many = True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


    def test_get_recipe_detail(self):
        '''Get recipe detail'''
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """create recipe through api using payload"""
        payload= {'title': 'Sample test Title',
                  'time_minutes': 22,
                  'price': Decimal ('5.50')}

        res = self.client.post(RECIPE_URL, payload)  # /api/recipes/recipe

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """test part of recipe, PATCH request"""

        orignal_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title="Sample Title",
            link = orignal_link
        )

        payload = {'title': "Sample Recipe Title"}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.user, self.user)
        self.assertEqual(recipe.link, orignal_link)

    def test_full_update(self):
        """test full put of recipe"""
        new_link = 'https://example.com/recipe1.pdf'

        recipe = create_recipe(
            user=self.user,
            title= 'Sample title',
            link = 'https://example.com/recipe.pdf',
            description = 'Sample description'
        )

        payload = {
            'title': 'Sample title 2',
            'link': new_link,
            'description': 'new description',
            'time_minutes': 10,
            'price' : Decimal('2.50')
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)


    def test_update_user_error(self):
        '''não deixe trocar o usuario que criou o usuario'''
        new_user = create_user(email='user2@example.com', password='test@pass123')
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        '''test the delete recipe successfull'''
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_recipe_other_users_recipe_error(self):
        '''test trying to detele another users recipe gives error'''
        new_user = create_user(email='user2@example.com', password='test@pass123')
        recipe = create_recipe(user= new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)  # quem vai tentar deletar é self.user

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_tags(self):
        '''test creating a recipe with new tags. '''
        payload = {
            'title': 'thai prawn curry',
            'time_minutes':30,
            'price': Decimal('2.50'),
            'tags': [{'name':'Thai'}, {'name':'Dinner'}]
        }
        res = self.client.post(RECIPE_URL,payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)  # verificamos a quantidade de receitas que deve ser 1
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(),2)  # verificamos a quantidade de tags, que deve ser 2
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        '''test creating a recipe with existing tag'''
        tag_india = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'pongal',
            'time_minutes':80,
            'price': Decimal('4.50'),
            'tags': [{'name':'Indian'}, {'name':'Breakfast'}],
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)  # verificamos a quantidade de receitas que deve ser 1
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_india, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        '''test creating tag when updating a  recipe'''
        recipe = create_recipe(user=self.user)
        payload = {'tags':[{'name':'Lunch'}]}
        url =detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assing_tag(self):
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name="Lunch")
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        '''test clearing recipe tags'''
        tag =Tag.objects.create(user=self.user, name="Desert")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags':[]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        '''test creating a recipe with new ingredients'''
        payload = {
            'title': 'Tacos',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name': 'mexican'}],
            'ingredients': [{'name':'rice'}, {'name':'beans'}, {'name':'meat'}],

        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code,  status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                user=self.user,
                name=ingredient['name']
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        '''test create recipe with existing ingredient'''
        ingredient = Ingredient.objects.create(user=self.user, name='Lemon')
        payload = {
            'title': 'Vietnamese Soup',
            'time_minutes': 25,
            'price': '2.55',
            'ingredients': [{'name':'Lemon'}, {'name':'Fish Soup'}],
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name = ingredient['name'],
                user = self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        '''test create ingredient when updating a recipe'''
        recipe = create_recipe(user=self.user)
        payload = {'ingredients': [{'name':'beans'}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='beans')
        self.assertIn(new_ingredient, recipe.ingredients.all())


    def test_update_recipe_assing_new_ingredient(self):
        '''test for assing new ingredients when updating recipe'''
        ingredient1 = Ingredient.objects.create(user=self.user, name='beans')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='rice')
        payload = {'ingredients': [{'name':'rice'}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_ingredients(self):
        '''test clearing a recepi ingredients'''
        ingredient = Ingredient.objects.create(user=self.user, name='beans')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {'ingredients': []}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        '''test filtering recipes by tags.'''
        r1 = create_recipe(user=self.user, title='Thai Vegetable curry')
        r2 = create_recipe(user=self.user, title='Aubergine')
        tag1 = Tag.objects.create(user=self.user, name='vegan')
        tag2 = Tag.objects.create(user=self.user, name='vegetarian')
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title='Fish and chips')

        params = {'tags': f'{tag1.id}, {tag2.id}'}
        res = self.client.get(RECIPE_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        # we expect s1 an s2 in the response but not s3
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        '''test filtering recipes by ingredients'''
        r1 = create_recipe(user=self.user,  title="Posh beans on Toast")
        r2 = create_recipe(user=self.user,  title="Chicken Caccitore")
        ing1 = Ingredient.objects.create(user=self.user, name='Feta Cheese')
        ing2 = Ingredient.objects.create(user=self.user, name='Chicken')
        r1.ingredients.add(ing1)
        r2.ingredients.add(ing2)
        r3 = create_recipe(user=self.user, title="Arroz e feijao")

        params= {'ingredients' : f'{ing1.id},{ing2.id}'}

        res = self.client.get(RECIPE_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

class ImageUploadTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user =get_user_model().objects.create_user(
            'user@example.com',
            'teste123',
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    # tearDown executa depois que teste termina
    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        '''test uploading an image to a recipe'''
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_bad_request(self):
        '''test uploading invalid image'''
        url = image_upload_url(self.recipe.id)
        payload = {'image':'notimage'}

        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)




















