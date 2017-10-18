# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase, Client

from budget.models import BankAccount
from .models import Transaction
from .views import *

# python manage.py test transactions.tests

# region Reference objects
test_file_path=r'D:\Dev\PycharmProjects\weeklybudget\weeklybudget\transactions\test_files'
def test_users():
    User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    User.objects.create_user('yoko', 'yoko@shavedfish.com', 'yokopassword')


def test_bank_accounts():
    user = User.objects.all()[:2]
    ba1 = BankAccount.objects.create(
        title='john account',
        current_balance=1000,
        display_order=1,
        owner=user[0],
        active=True,
    )
    ba1.save()

    ba1a = BankAccount.objects.create(
        title='john credit account',
        current_balance=500,
        account_type='credit',
        account_limit=8000,
        display_order=2,
        owner=user[0],
    )
    ba1a.save()

    ba1b = BankAccount.objects.create(
        title='john virtual account',
        current_balance=0,
        account_type='virtual',
        display_order=3,
        owner=user[0],
    )
    ba1b.save()

    ba2 = BankAccount.objects.create(
        title='yoko account',
        current_balance=1000,
        display_order=1,
        owner=user[1],
    )
    ba2.save()


# endregion

class TestFileUpload(TestCase):

    def setUp(self):
        test_users()
        test_bank_accounts()

    def test_file_upload_header(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        with open(test_file_path + r'\westpac1.csv') as fp:
            payload = {
                'file': fp,
                'account': BankAccount.objects.get(title='john credit account').id
            }
            response = c.post('/transactions/upload_file/', payload)
            response_data = json.loads(response.content)
            qs = Transaction.objects.filter(owner=User.objects.get(username__exact='john'))
            self.assertEqual('pass', response_data['result_success'], response)
            self.assertNotEqual(0, qs.count())
            self.assertEqual(70, len(response_data['transactions_rows']))
            self.assertEqual(8, len(response_data['transactions_rows'][0]))
            self.assertEqual(1, response_data['transactions_rows'][0][0])
            self.assertEqual(70, response_data['transactions_rows'][69][0])
            self.assertTrue(response_data['has_header'])
            self.assertEqual('733000731063', response_data['transactions_rows'][1][1])

            e = qs.first().run
            self.assertIsNotNone(e)
            self.assertEqual(2, e.fields_payment_date)
            self.assertEqual(5, e.fields_incoming)
            self.assertEqual(4, e.fields_outgoing)
            self.assertEqual(3, e.fields_description)
            self.assertEqual(BankAccount.objects.get(title='john credit account'), e.account)

    def test_file_upload_no_header(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        with open(test_file_path + r'\virgin_mc.csv') as fp:
            payload = {
                'file': fp,
                'account': BankAccount.objects.get(title='john credit account').id
            }
            response = c.post('/transactions/upload_file/', payload)
            response_data = json.loads(response.content)
            qs = Transaction.objects.filter(owner=User.objects.get(username__exact='john'))
            self.assertEqual('pass', response_data['result_success'], response)
            self.assertNotEqual(0, qs.count())
            self.assertEqual(2, len(response_data['transactions_rows']))
            self.assertEqual(6, len(response_data['transactions_rows'][0]))
            self.assertEqual(1, response_data['transactions_rows'][0][0])
            self.assertEqual(2, response_data['transactions_rows'][1][0])
            self.assertFalse(response_data['has_header'])
            self.assertEqual('"01/08/2017"', response_data['transactions_rows'][1][1])

            e = qs.first().run
            self.assertIsNotNone(e)
            self.assertEqual(1, e.fields_payment_date)
            self.assertEqual(-1, e.fields_incoming)
            self.assertEqual(3, e.fields_outgoing)
            self.assertEqual(2, e.fields_description)
            self.assertEqual(BankAccount.objects.get(title='john credit account'), e.account)

    def test_file_upload_header_no_guessing(self):
        # TODO test that we're using the latest run as template
        a = BankAccount.objects.get(title='john credit account')
        Extract.objects.create(
            account=a,
            extract_run_id=1,
            has_header_row=True,
            delimiter=',',
            fields_payment_date=11,
            fields_description=12,
            fields_incoming=13,
            fields_incoming_sign='-',
            fields_outgoing=14,
            fields_outgoing_sign='-',
            owner=User.objects.get(username='john'),
        )
        Extract.objects.create(
            account=a,
            extract_run_id=2,
            has_header_row=True,
            delimiter=',',
            fields_payment_date=7,
            fields_description=8,
            fields_incoming=9,
            fields_incoming_sign='-',
            fields_outgoing=10,
            fields_outgoing_sign='-',
            owner=User.objects.get(username='john'),
        )

        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        with open(test_file_path + r'\westpac1.csv') as fp:
            payload = {
                'file': fp,
                'account': a.id
            }
            response = c.post('/transactions/upload_file/', payload)
            response_data = json.loads(response.content)
            self.assertEqual('pass', response_data['result_success'], response)
            e = Transaction.objects.filter(owner=User.objects.get(username__exact='john')).first().run
            self.assertIsNotNone(e)
            self.assertEqual(3, e.extract_run_id)
            self.assertEqual(7, e.fields_payment_date)
            self.assertEqual(9, e.fields_incoming)
            self.assertEqual(10, e.fields_outgoing)
            self.assertEqual(8, e.fields_description)
            self.assertEqual('-', e.fields_incoming_sign)
            self.assertEqual('-', e.fields_outgoing_sign)