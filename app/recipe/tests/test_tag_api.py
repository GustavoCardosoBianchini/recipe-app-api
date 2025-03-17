"""
Tests for tag api
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (Tag, Recipe)

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

def detail_url(tag_id):
    '''create and return a tag detail url.'''
    return reverse('recipe:tag-detail', args=[tag_id])

def create_user(email='user@example.com', password='testpass123'):
    '''Create and return a user'''
    return get_user_model().objects.create_user(email=email, password=password)

class PublicTagsAPITest(TestCase):
    """Test unauthenticated API requests"""

    # função para iniciar o APICLient
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''test auth is required on retrieving Tags'''
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateTagsAPITest(TestCase):
    """test authenticated API"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        '''test retrieving list of tags'''
        Tag.objects.create(user=self.user, name="vegan")
        Tag.objects.create(user=self.user, name="meat")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        '''test tags limited to authenticated user'''
        user2= create_user(email='user2@example.com')
        Tag.objects.create(user=user2, name="Fruity")
        tag = Tag.objects.create(user=self.user, name="Confort Food")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        '''test updating a tag.'''
        tag= Tag.objects.create(user=self.user, name='After Dinner')

        payload = {'name': 'Dessert'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        '''test deleting a tag'''
        tag = Tag.objects.create(user=self.user, name='Salt')

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user = self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipes(self):
        '''Test listing tags to those assigned to recipes'''
        tag1 = Tag.objects.create(user=self.user, name="breakfast")
        tag2 = Tag.objects.create(user=self.user, name="lunch")
        recipe = Recipe.objects.create(
            title='Green Eggs',
            time_minutes='15',
            price=Decimal('2.50'),
            user=self.user,
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only':1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_tags_unique(self):
        '''test filtered tags return unique list'''
        tag = Tag.objects.create(user=self.user, name="dinner")
        Tag.objects.create(user=self.user, name="breakfast")
        recipe1 = Recipe.objects.create(
            title='arroz e feijao',
            time_minutes='40',
            price=Decimal('25.00'),
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title='macarronada',
            time_minutes='30',
            price=Decimal('20.00'),
            user=self.user,
        )
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only':1})

        self.assertEqual(len(res.data), 1)




