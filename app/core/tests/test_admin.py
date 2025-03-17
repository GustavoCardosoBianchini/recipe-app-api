"""
test de funções de admin, para pagina web admin na web
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client

class AdminSiteTests(TestCase):
    """testes para o Django Admin"""

    def setUp(self):
        """Create user and client"""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='testpass123'
        )

        self.client.force_login(self.admin_user)
        self.user  = get_user_model().objects.create_user(
            email ='user@example.com',
            password = 'testpass123',
            name='Teste User'
        )

    def test_users_list(self):
        """test that users are listed on page"""
        url = reverse('admin:core_user_changelist')  # define qual url, vamos puxar do caminho
        res = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_edit_user_page(self):
        '''teste the edit user page works.'''

        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        '''teste para criar a pagina de criar usuario.'''

        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

