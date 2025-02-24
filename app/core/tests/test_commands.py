'''
test custom django management commands
'''

from unittest.mock import patch  # patch sobrescreve o codigo de teste

from psycopg2 import OperationalError as Psycopg2Error

# helper comand function from python, that allow to call comands by the name
from django.core.management import call_command


# outro tipo gerador de erro, dependendo do ponto de conexão do banco de dados
from django.db.utils import OperationalError

# teste simples sem conexão do banco de dados.
from django.test import SimpleTestCase


# para fazer o mock, do teste precisamos adicionar o @patch() antes
# da classe para substituir a funcionalidade de conexão do banco por exemplo


# Command.check, é referente a biblioteca BasecCommand
# importada do arquivo wait_for_db
@patch('core.management.commands.wait_for_db.Command.check')
class CommandTests(SimpleTestCase):
    """Test commands"""

    def test_wait_for_db_ready(self, patched_check):
        """testa se o banco ja esta rodando"""
        patched_check.return_value = True

        call_command('wait_for_db')

        # assert_called_once_with, garante que o patched
        # esteja sendo chamado com os dados do database=['default']
        # chama o banco apenas uma vez
        patched_check.assert_called_once_with(databases=['default'])

    @patch('time.sleep')
    def test_wait_for_db_delay(self, patched_spleep, patched_check):
        '''espera pelo atraso do banco'''
        patched_check.side_effect = [Psycopg2Error] * 2 + \
            [OperationalError] * 3 + [True]

        call_command('wait_for_db')

        self.assertEqual(patched_check.call_count, 6)
        # pode chamar o banco varias vezes
        patched_check.assert_called_with(databases=['default'])
