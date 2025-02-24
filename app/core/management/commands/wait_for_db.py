"""
comando django para esperar o banco ligar
"""

import time

from psycopg2 import OperationalError as Psycopg2Error

from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    '''Django comand to wait for database'''

    def handle(self, *args, **options):
        # Mensagem do momento de espera
        self.stdout.write('Waiting for database')
        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True

            # captura os erros para a gente
            except (Psycopg2Error, OperationalError):
                self.stdout.write('Database Unavilable, wait a second')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database Available'))
