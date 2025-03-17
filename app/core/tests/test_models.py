"""
Tests for models
"""
from unittest.mock import patch
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models

def create_user(email='user@example.com', password='testpass123'):
    '''Create and return a new user for testing'''
    return get_user_model().objects.create_user(email, password)

class ModelTests(TestCase):
    '''test models'''

    def test_create_user_with_email_successful(self):
        """teste criando usuario com email correto"""
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email = email,
            password = password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        ''' test if its a valid email '''
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """test de validação se usuario foi criado sem email, gere um erro"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', '123')

    def test_create_superuser(self):
        """teste de função para criação de um usper usuario"""
        user = get_user_model().objects.create_superuser(
            'teste@example.com', 'test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        '''Test creating a recipe is successfull'''
        user = get_user_model().objects.create_user(
            'test@example.com',
            'test@123'
        )
        recipe = models.Recipe.objects.create(
            user = user,
            title = "Sample recipe Name",
            time_minutes= 5,
            price= Decimal('5.50'),
            description="Sample recipe Description"
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        '''test creating a tag is successfull'''
        user = create_user()
        tag = models.Tag.objects.create(user=user, name="Tag1")

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        '''teste4 creating a ingredient is successfull'''
        user = create_user()
        ingredient = models.Ingredient.objects.create(user=user, name="ingredient1")

        self.assertEqual(str(ingredient), ingredient.name)

    # patch the uuid, unit test identifier
    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        '''Test generating image path'''
        # if we don't mock this uuid, the code will generate a
        # new one each time we test and it can be quite difficult
        # to retrieve it's value each time, so mocking it to a
        # fixed value will make it easier to test

        # mock the uuid, to a fixed value
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid

        # this is the function that will receive the image pathfile
        file_path =models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')