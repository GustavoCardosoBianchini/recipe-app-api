'''
sample testes
'''

from django.test import SimpleTestCase

from app import calc


class CalcTest(SimpleTestCase):
    '''classe para testar o modulo de Calculo'''

    def test_calc_add(self):
        '''função de teste de add'''

        res = calc.add(5, 6)

        self.assertEqual(res, 11)

    def test_calc_subtract(self):
        '''função para testar subtração'''

        res = calc.subtract(10, 15)

        self.assertEqual(res, -5)
