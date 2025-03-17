'''
user api, unit test
'''

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
CREATE_TOKEN = reverse('user:token')
ME_URL = reverse('user:me')

def create_user(**params):
    '''helper function to return new user'''
    return get_user_model().objects.create_user(**params)

class PublicUserApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create_user_succes(self):
        ''' Test creating a password'''
        payload = {
            'email': 'jorge@example.com',
            'password': 'testpass123',
            'name': 'Jorge'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])

        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password',res.data)

    def test_user_with_email_exists_error(self):
        '''test error, email already exists'''
        payload = {
            'email': 'test@example.com',
            'password': 'test@1234',
            'name': 'TestUser'
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        '''Test if password is too short'''
        payload = {
            'email': 'caio@example.com',
            'password': 'pw',
            'name': 'Name'
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        '''test generates token for valid credentials'''
        user_details = {
            'name': 'Cleber',
            'email': 'cleber@example.com',
            'password': 'supercleber123',
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }

        res = self.client.post(CREATE_TOKEN, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        '''teste erro for invalid credentials'''
        create_user(email='test@example.com', password='goodpass123', name='Ricardo')

        payload = {
            'email': 'test@example.com',
            'password': 'badpass123'
        }

        res = self.client.post(CREATE_TOKEN, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blak_password(self):
        """test if token return with blank password"""
        payload= {'email': 'test@example', 'password': ''}

        res = self.client.post(CREATE_TOKEN, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

# vamos lidar com a autenticação no metodo de configuração, chamado automaticamente.
# antes de cada teste, assim não precisarei duplicar código de autenticação, ou simular uma autenticação.
# para cada teste da api
class PrivateUserApiTests(TestCase):
    """Test Api requests that require authentication"""

    def setUp(self):
        self.user = create_user(
            email='keila@example.com',
            password='testpas123',
            name= 'Keila'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        '''test retrieve profile  for loggerd user'''
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email':self.user.email
        })

    def test_post_me_not_allowed(self):
        """test Post is not allowed for the ME endpoint"""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        '''test updating user profile for the authenticated user'''
        payload = {'name': 'Keila', 'password': 'newpassword123'}

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)