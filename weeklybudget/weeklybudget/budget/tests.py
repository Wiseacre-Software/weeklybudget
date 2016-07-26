import locale

from dateutil.relativedelta import relativedelta
from dateutil.rrule import *
from django.contrib.auth.models import User
from django.template.defaultfilters import date as _date
from django.test import TestCase, Client
from datetime import date, datetime

from .models import *
from .views import *

import re
import time


# region Reference objects
def test_users():
    User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    User.objects.create_user('yoko', 'yoko@shavedfish.com', 'yokopassword')


def test_bank_accounts():
    user = User.objects.all()[:2]
    ba1 = BankAccount.objects.create(
        title='john account',
        current_balance=1000,
        owner=user[0],
    )
    ba1.save()

    ba2 = BankAccount.objects.create(
        title='yoko account',
        current_balance=1000,
        owner=user[1],
    )
    ba2.save()


def test_categories():
    user = User.objects.all()[:2]
    pt1 = PaymentType.objects.create(
        name='pt1',
        sort_order='1',
        owner=user[0]
    )
    cat1 = Category.objects.create(
        name='cat1',
        payment_type=pt1,
        owner=user[0]
    )
    subcat1 = SubCategory.objects.create(
        name='subcat1',
        category=cat1,
        owner=user[0]
    )
    pt2 = PaymentType.objects.create(
        name='pt2',
        sort_order='2',
        owner=user[1]
    )
    cat2 = Category.objects.create(
        name='cat2',
        payment_type=pt2,
        owner=user[1]
    )
    subcat2 = SubCategory.objects.create(
        name='subcat2',
        category=cat2,
        owner=user[1]
    )


def test_payment_schedules():
    PaymentScheduleFrequency.objects.create(name='User Specified', sort_order=5)
    PaymentScheduleFrequency.objects.create(name='Annual', sort_order=4)
    PaymentScheduleFrequency.objects.create(name='Monthly', sort_order=3)
    PaymentScheduleFrequency.objects.create(name='Weekly', sort_order=2)
    PaymentScheduleFrequency.objects.create(name='Once Off', sort_order=1)


def test_payments():
    user = User.objects.all()[:2]
    ps = PaymentSchedule.objects.create(
        next_date=datetime(2016, 6, 7),
        frequency=PaymentScheduleFrequency.objects.get(name__exact='Weekly'),
        weekly_dow_tue=True,
        weekly_frequency=2
    )
    Payment.objects.create(
        title='Payment 1',
        in_out='i',
        amount=1000,
        payment_type=PaymentType.objects.get(name__exact='pt1'),
        category=Category.objects.get(name__exact='cat1'),
        subcategory=SubCategory.objects.get(name__exact='subcat1'),
        schedule=ps,
        owner=user[0]
    )
# endregion


class GenerateCalendarViewTest(TestCase):
    payload = {'start_date': '2016-08-01', 'end_date': '2017-08-01'}

    def setUp(self):
        test_users()
        test_bank_accounts()
        test_categories()
        test_payment_schedules()
        test_payments()
        p = Payment.objects.all()[0]
        p.weekly_dow_tue = False
        p.weekly_frequency = 0

    def test_calendar_view_setup(self):
        c = Client()
        c.login(username='john', password='johnpassword')
        response = c.post('/budget/calendar_view/', self.payload)
        self.assertEqual(response.resolver_match.func, generate_calendar_view)

    def test_monthly_specific_dom_payment_monthly_frequency(self):
        expected_next_date = rrule(MONTHLY, dtstart=datetime.strptime(self.payload['start_date'], '%Y-%m-%d'),
                                   count=1, bymonthday=15)[0].date()
        self.assertEqual(expected_next_date, date(2016, 8, 15))

        p = Payment.objects.all()[0]
        p.schedule.frequency = PaymentScheduleFrequency.objects.get(name__exact='Monthly')
        p.schedule.monthly_dom = 15
        p.schedule.monthly_frequency = 2
        p.schedule.next_date = expected_next_date
        p.schedule.save()
        p.save()

        c = Client()
        c.login(username='john', password='johnpassword')
        response = c.post('/budget/calendar_view/', self.payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        pc = response_data["data"]
        self.assertEqual(pc[0]['payment_date'], str(expected_next_date),
                         "pc[0]['payment_date']: found %s (%s), expected %s (%s)" %
                         (pc[0]['payment_date'], str(type(pc[0]['payment_date'])),
                          str(expected_next_date), str(type(str(expected_next_date)))))
        self.assertEqual(pc[1]['payment_date'], str(expected_next_date + relativedelta(months=+2)),
                         "pc[1]['payment_date']: found %s, expected %s" %
                         (pc[1]['payment_date'], str(expected_next_date + relativedelta(months=+2))))

    def test_monthly_specific_dom_payment_second_last_day(self):
        expected_next_dates = rrule(MONTHLY, dtstart=datetime.strptime(self.payload['start_date'], '%Y-%m-%d'),
                                    count=6, bymonthday=-2)
        self.assertEqual(expected_next_dates[0].date(), date(2016, 8, 30))

        p = Payment.objects.all()[0]
        p.schedule.frequency = PaymentScheduleFrequency.objects.get(name__exact='Monthly')
        p.schedule.monthly_dom = -2
        p.schedule.monthly_frequency = 1
        p.schedule.next_date = expected_next_dates[0].date()
        p.schedule.save()
        p.save()

        c = Client()
        c.login(username='john', password='johnpassword')
        response = c.post('/budget/calendar_view/', self.payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        pc = response_data["data"]
        self.assertEqual(pc[0]['payment_date'], str(expected_next_dates[0].date()),
                         "pc[0]['payment_date']: found %s (%s), expected %s (%s)" %
                         (pc[0]['payment_date'], str(type(pc[0]['payment_date'])),
                          str(expected_next_dates[0].date()), str(type(str(expected_next_dates[0].date())))))
        self.assertEqual(pc[1]['payment_date'], str(expected_next_dates[1].date()),
                         "pc[1]['payment_date']: found %s, expected %s" %
                         (pc[1]['payment_date'], str(expected_next_dates[1].date())))

    def test_monthly_wom_payment_first_monday(self):
        expected_next_dates = rrule(MONTHLY, dtstart=datetime.strptime(self.payload['start_date'], '%Y-%m-%d'),
                                    count=6, byweekday=MO(+1))
        self.assertEqual(expected_next_dates[0].date(), date(2016, 8, 1))

        p = Payment.objects.all()[0]
        p.schedule.frequency = PaymentScheduleFrequency.objects.get(name__exact='Monthly')
        p.schedule.monthly_wom = 1
        p.schedule.monthly_dow = 0
        p.schedule.monthly_frequency = 1
        p.schedule.next_date = expected_next_dates[0].date()
        p.schedule.save()
        p.save()

        c = Client()
        c.login(username='john', password='johnpassword')
        response = c.post('/budget/calendar_view/', self.payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        pc = response_data["data"]
        self.assertEqual(pc[0]['payment_date'], str(expected_next_dates[0].date()),
                         "pc[0]['payment_date']: found %s (%s), expected %s (%s)" %
                         (pc[0]['payment_date'], str(type(pc[0]['payment_date'])),
                          str(expected_next_dates[0].date()), str(type(str(expected_next_dates[0].date())))))
        self.assertEqual(pc[1]['payment_date'], str(expected_next_dates[1].date()),
                         "pc[1]['payment_date']: found %s, expected %s" %
                         (pc[1]['payment_date'], str(expected_next_dates[1].date())))

    def test_monthly_wom_payment_second_last_wed_of_every_4_months(self):
        expected_next_dates = rrule(MONTHLY, dtstart=datetime.strptime(self.payload['start_date'], '%Y-%m-%d'), count=6,
                                    byweekday=WE(-2), interval=4)
        self.assertEqual(expected_next_dates[0].date(), date(2016, 8, 24))

        p = Payment.objects.all()[0]
        p.schedule.frequency = PaymentScheduleFrequency.objects.get(name__exact='Monthly')
        p.schedule.monthly_wom = -2
        p.schedule.monthly_dow = 2
        p.schedule.monthly_frequency = 4
        p.schedule.next_date = expected_next_dates[0].date()
        p.schedule.save()
        p.save()

        c = Client()
        c.login(username='john', password='johnpassword')
        response = c.post('/budget/calendar_view/', self.payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        pc = response_data["data"]
        self.assertEqual(pc[0]['payment_date'], str(expected_next_dates[0].date()),
                         "pc[0]['payment_date']: found %s (%s), expected %s (%s)" %
                         (pc[0]['payment_date'], str(type(pc[0]['payment_date'])),
                          str(expected_next_dates[0].date()), str(type(str(expected_next_dates[0].date())))))
        self.assertEqual(pc[1]['payment_date'], str(expected_next_dates[1].date()),
                         "pc[1]['payment_date']: found %s, expected %s" %
                         (pc[1]['payment_date'], str(expected_next_dates[1].date())))

    def test_annual_payment_every_second_year(self):
        expected_next_dates = rrule(YEARLY, dtstart=datetime.strptime(self.payload['start_date'], '%Y-%m-%d'),
                                    count=2, bymonth=8, bymonthday=15, interval=2)
        self.assertEqual(expected_next_dates[0].date(), date(2016, 8, 15))

        p = Payment.objects.all()[0]
        p.schedule.frequency = PaymentScheduleFrequency.objects.get(name__exact='Annual')
        p.schedule.annual_dom = 15
        p.schedule.annual_moy = 8
        p.schedule.annual_frequency = 2
        p.schedule.next_date = expected_next_dates[0].date()
        p.schedule.save()
        p.save()

        self.payload['end_date'] = '2018-08-15'

        c = Client()
        c.login(username='john', password='johnpassword')
        response = c.post('/budget/calendar_view/', self.payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("exception", response_data, 'Exception occurred: %s' % response_data)
        pc = response_data["data"]
        self.assertEqual(pc[0]['payment_date'], str(expected_next_dates[0].date()),
                         "pc[0]['payment_date']: found %s (%s), expected %s (%s)" %
                         (pc[0]['payment_date'], str(type(pc[0]['payment_date'])),
                          str(expected_next_dates[0].date()), str(type(str(expected_next_dates[0].date())))))
        self.assertEqual(pc[1]['payment_date'], str(expected_next_dates[1].date()),
                         "pc[1]['payment_date']: found %s, expected %s" %
                         (pc[1]['payment_date'], str(expected_next_dates[1].date())))


class AuthenticationTest(TestCase):
    def setUp(self):
        user1 = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
        user2 = User.objects.create_user('yoko', 'yoko@shavedfish.com', 'yokopassword')
        p = Payment.objects.create(
            title='test',
            amount=1000,
            owner=user1,
        )
        p.save()
        pt = PaymentType.objects.create(name="type1", owner=user1)
        cat = Category.objects.create(name="cat1", payment_type=pt, owner=user1)
        subcat = SubCategory.objects.create(name="subcat1", category=cat, owner=user1)

    def test_login_invalid_user(self):
        c = Client()
        self.assertFalse(c.login(username='fred', password='secret'))

    def test_login_valid_user(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))

    def test_user_cant_see_other_user_payment(self):
        c = Client()
        self.assertTrue(c.login(username='yoko', password='yokopassword'))
        response = c.get('/budget/')
        self.assertEqual(len(response.context['payments']), 0, "context['payments']: found %i, expected %i" %
                         (len(response.context['payments']), 0))
        self.assertEqual(len(response.context['manage_payment_types']), 0,
                         "context['manage_payment_types']: found %i, expected %i" %
                         (len(response.context['manage_payment_types']), 0))
        self.assertEqual(len(response.context['manage_categories']), 0,
                         "context['manage_categories']: found %i, expected %i" %
                         (len(response.context['manage_categories']), 0))
        self.assertEqual(len(response.context['manage_subcategories']), 0,
                         "context['manage_subcategories']: found %i, expected %i" %
                         (len(response.context['manage_subcategories']), 0))
        self.assertEqual(response.context['categorymap'], '[]',
                         "context['categorymap']: found %s, expected %s" %
                         (response.context['categorymap'], '[]'))

    def test_user_can_see_their_own_payment(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        response = c.get('/budget/')
        self.assertEqual(len(response.context['payments']), 1, "context['payments']: found %i, expected %i" %
                         (len(response.context['payments']), 1))
        self.assertEqual(len(response.context['manage_payment_types']), 1,
                         "context['manage_payment_types']: found %i, expected %i" %
                         (len(response.context['manage_payment_types']), 1))
        self.assertEqual(len(response.context['manage_categories']), 1,
                         "context['manage_categories']: found %i, expected %i" %
                         (len(response.context['manage_categories']), 1))
        self.assertEqual(len(response.context['manage_subcategories']), 1,
                         "context['manage_subcategories']: found %i, expected %i" %
                         (len(response.context['manage_subcategories']), 1))
        self.assertEqual(response.context['categorymap'], '[[1], [1, 1], [1, 1, 1]]',
                         "context['categorymap']: found %s, expected %s" %
                         (response.context['categorymap'], '[[1], [1, 1], [1, 1, 1]]'))


class BankAccountTest(TestCase):
    def setUp(self):
        test_users()
        test_bank_accounts()

    def test_cant_see_other_user_bank_account(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        response = c.get('/budget/bank_account/')
        self.assertIsNotNone(response.context, response.content)
        ba = response.context["bank_accounts"]
        self.assertEqual(len(ba), 1, "context['bank_accounts']: found %i, expected %i" %
                         (len(ba), 1))

    def test_invalid_user_cant_see_squat(self):
        c = Client()
        self.assertFalse(c.login(username='not_john', password='not_johnpassword'))

    def test_create_bank_account(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'update',
            'bank_account_id': '',
            'title': 'new account',
            'current_balance': 7000,
            'owner': c,
        }
        response = c.post('/budget/bank_account/', payload)
        self.assertIsNotNone(response.context, response.content)
        self.assertEqual(len(response.context["bank_accounts"]), 2,
                         "context['bank_accounts']: found %i, expected %i" %
                         (len(response.context["bank_accounts"]), 2))
        self.assertEqual(response.context["result_success"], "pass",
                         "context['bank_accounts']: found %s, expected %s" %
                         (response.context["result_success"], "pass"))

    def test_update_bank_account(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        ba = BankAccount.objects.get(title__exact='john account')
        payload = {
            'action': 'update',
            'bank_account_id': ba.pk,
            'title': 'john account - updated!',
            'current_balance': 7000,
            'owner': c,
        }
        response = c.post('/budget/bank_account/', payload)
        self.assertIsNotNone(response.context, 'response.context is None. response.content: %s' % response.content)
        self.assertEqual(len(response.context['bank_accounts']), 1,
                         "context['bank_accounts']: found %i, expected %i" %
                         (len(response.context['bank_accounts']), 1))
        res = response.context['bank_accounts'][0]
        self.assertEqual(res.title, 'john account - updated!',
                         "title: found %s, expected %s" %
                         (res.title, 'john account - updated!'))
        self.assertEqual(res.current_balance, 7000,
                         "current_balance: found %i, expected %i" %
                         (res.current_balance, 7000))
        self.assertEqual(response.context["result_success"], "pass",
                         "result: found %s, expected %s" %
                         (response.context["result_success"], "pass"))

    def test_delete_bank_account(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        ba = BankAccount.objects.get(title__exact='john account')
        payload = {
            'action': 'delete',
            'bank_account_id': ba.pk,
        }
        response = c.post('/budget/bank_account/', payload)
        self.assertIsNotNone(response.context, 'response.context is None. response.content: %s' % response.content)
        self.assertEqual(len(response.context['bank_accounts']), 0,
                         "context['bank_accounts']: found %i, expected %i" %
                         (len(response.context['bank_accounts']), 0))
        self.assertEqual(response.context["result_success"], "pass",
                         "result: found %s, expected %s" %
                         (response.context["result_success"], "pass"))

    def test_cannot_create_bank_account_with_same_name(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'update',
            'bank_account_id': '',
            'title': 'john account',
            'current_balance': 7000,
            'owner': c,
        }
        response = c.post('/budget/bank_account/', payload)
        self.assertIsNotNone(response.context, response.content)
        self.assertEqual(len(response.context["bank_accounts"]), 1,
                         "context['bank_accounts']: found %i, expected %i" %
                         (len(response.context["bank_accounts"]), 1))
        self.assertEqual(response.context["result_success"], "fail",
                         "result: found %s, expected %s" %
                         (response.context["result_success"], "fail"))


class UpdatePaymentTest(TestCase):
    def setUp(self):
        test_users()
        test_categories()
        test_payment_schedules()
        test_payments()

    # def test_cant_see_other_user_bank_account(self):
        # todo write test case

    def test_create_payment(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'update',
            'title': 'payment 2',
            'amount': 1000,
            'in_out': 'i',
            'payment_type': PaymentType.objects.get(name__exact='pt1').id,
            'category': Category.objects.get(name__exact='cat1').id,
            'subcategory': SubCategory.objects.get(name__exact='subcat1').id,
            'schedule_frequency': PaymentScheduleFrequency.objects.get(name__exact='Weekly').id,
            'next_date': '20/06/2016',
            'weekly_dow_tue': 'true',
            'weekly_frequency': 2
        }
        response = c.post('/budget/update_payment/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass", "found %s, expected %s" %
                         (response_data["result_success"], "pass"))
        self.assertEqual(response_data["form_data"]['title'], "payment 2", "found %s, expected %s" %
                         (response_data["form_data"]['title'], "payment 2"))
        p = Payment.objects.get(title__iexact='payment 1')
        self.assertTrue(p.schedule.weekly_dow_tue, "found false, expected true")

    def test_create_payment_with_duplicate_name(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'update',
            'title': 'payment 1',
            'amount': 1000,
            'in_out': 'i',
            'payment_type': PaymentType.objects.get(name__exact='pt1').id,
            'category': Category.objects.get(name__exact='cat1').id,
            'subcategory': SubCategory.objects.get(name__exact='subcat1').id,
            'schedule_frequency': PaymentScheduleFrequency.objects.get(name__exact='Weekly').id,
            'next_date': '20/06/2016',
            'weekly_dow_tue': 'true',
            'weekly_frequency': 2
        }
        response = c.post('/budget/update_payment/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["Exception"], "Payment of that name already exists", "found %s, expected %s" %
                         (response_data["Exception"], "Payment of that name already exists"))

    def test_update_payment(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'update',
            'payment_id': Payment.objects.all()[0].id,
            'title': 'payment 1 updated',
            'amount': 2000,
            'in_out': 'o',
            'payment_type': PaymentType.objects.get(name__exact='pt1').id,
            'category': Category.objects.get(name__exact='cat1').id,
            'subcategory': SubCategory.objects.get(name__exact='subcat1').id,
            'schedule_frequency': PaymentScheduleFrequency.objects.get(name__exact='Weekly').id,
            'next_date': '21/06/2016',
            'weekly_dow_tue': 'false',
            'weekly_dow_wed': 'true',
            'weekly_frequency': 1
        }
        response = c.post('/budget/update_payment/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass", "found %s, expected %s" %
                         (response_data["result_success"], "pass"))
        self.assertEqual(response_data["result_message"], "Payment Saved!", "found %s, expected %s" %
                         (response_data["result_message"], "Payment Saved!"))
        self.assertEqual(response_data["form_data"]['title'], "payment 1 updated", "found %s, expected %s" %
                         (response_data["form_data"]['title'], "payment 1 updated"))

    def test_delete_payment(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payment_id = Payment.objects.all()[0].id
        payload = {
            'action': 'delete',
            'payment_id': payment_id,
        }
        response = c.post('/budget/update_payment/', payload)
        self.assertNotEqual(response.content, '', 'response.content is empty. response.content: %s' % response.content)
        response_data = jsonpickle.decode(response.content)
        self.assertEqual(response_data["result_success"], "pass", "found %s, expected %s" %
                         (response_data["result_success"], "pass"))
        self.assertEqual(response_data["result_message"], "Payment deleted!", "found %s, expected %s" %
                         (response_data["result_message"], "Payment deleted!"))
        self.assertEqual(Payment.objects.filter(pk=payment_id).count(), 0, "found %i, expected %i" %
                         (Payment.objects.filter(pk=payment_id).count(), 0))

    def test_payment_request_via_get(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {}
        response = c.get('/budget/update_payment/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertIn("Exception", response_data, 'Exception occurred: %s' % response_data)

    def test_payment_with_no_payment_category(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'update',
            'title': 'payment no category',
            'amount': 2000,
            'in_out': 'o',
            'payment_type': PaymentType.objects.get(name__exact='pt1').id,
            'schedule_frequency': PaymentScheduleFrequency.objects.get(name__exact='Weekly').id,
            'next_date': '21/06/2016',
            'weekly_dow_tue': 'true',
            'weekly_dow_wed': 'false',
            'weekly_frequency': 1
        }
        response = c.post('/budget/update_payment/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass", "found %s, expected %s" %
                         (response_data["result_success"], "pass"))
        self.assertEqual(response_data["form_data"]['title'], "payment no category", "found %s, expected %s" %
                         (response_data["form_data"]['title'], "payment no category"))
        p = Payment.objects.get(title__iexact='payment no category')
        self.assertIsNone(p.category, "found a category, expected none")
        self.assertIsNone(p.category, "found a subcategory, expected none")

    def test_create_annual_payment(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'update',
            'title': 'payment 2',
            'amount': 1000,
            'in_out': 'i',
            'payment_type': PaymentType.objects.get(name__exact='pt1').id,
            'category': Category.objects.get(name__exact='cat1').id,
            'subcategory': SubCategory.objects.get(name__exact='subcat1').id,
            'schedule_frequency': PaymentScheduleFrequency.objects.get(name__exact='Annual').id,
            'next_date': '20/07/2016',
            'annual_dom': 20,
            'annual_moy': 7,
            'annual_frequency': 1
        }
        response = c.post('/budget/update_payment/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass", "found %s, expected %s" %
                         (response_data["result_success"], "pass"))
        self.assertEqual(response_data["form_data"]['title'], "payment 2", "found %s, expected %s" %
                         (response_data["form_data"]['title'], "payment 2"))



class UpdatePaymentDateTest(TestCase):
    def setUp(self):
        test_users()
        test_categories()
        test_payment_schedules()
        test_payments()
        test_bank_accounts()

    def test_update_existing_payment_date(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'series_choice': 'series',
            'payment_id': Payment.objects.get(title__exact='Payment 1').id,
            'schedule_frequency': PaymentScheduleFrequency.objects.get(name__exact='Monthly').id,
            'next_date': '21/06/2016',
            'monthly_dom': 21,
            'monthly_frequency': 1,
        }
        response = c.post('/budget/update_payment_date/', payload)
        # print response.content
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass", "found %s, expected %s" %
                         (response_data["result_success"], "pass"))
        p = Payment.objects.get(title__iexact='payment 1')
        self.assertFalse(p.schedule.weekly_dow_tue, "found false, expected true")
        self.assertEqual(p.schedule.weekly_frequency, 0, "found %i, expected %i" %
                         (p.schedule.weekly_frequency, 0))
        self.assertEqual(p.schedule.monthly_dom, 21, "found %i, expected %i" %
                         (p.schedule.monthly_dom, 21))
        self.assertEqual(p.schedule.monthly_frequency, 1, "found %i, expected %i" %
                         (p.schedule.monthly_frequency, 1))

    def test_create_custom_payment_date(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'series_choice': 'this',
            'payment_id': Payment.objects.get(title__exact='Payment 1').id,
            'next_date': '23/06/2016',
            'original_date': '2016-06-21'
        }
        response = c.post('/budget/update_payment_date/', payload)
        # print response.content
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass", "found %s, expected %s" %
                         (response_data["result_success"], "pass"))
        new_p = Payment.objects.get(title__iexact='Payment 1' + ' - ' +
                                                  _date(date(2016, 6, 23), 'SHORT_DATE_FORMAT'))
        self.assertEqual(new_p.schedule.frequency.name, 'Once Off', "found %s, expected %s" %
                         (new_p.schedule.frequency.name, 'Once Off'))
        orig_p = Payment.objects.get(title__iexact='Payment 1')
        self.assertEqual(orig_p.schedule.frequency.name, 'Weekly', "found %s, expected %s" %
                         (orig_p.schedule.frequency.name, 'Weekly'))
        orig_p_exclusions = PaymentScheduleExclusion.objects.get(main_payment=orig_p)
        self.assertEqual(orig_p_exclusions.main_payment.schedule.frequency.name, 'Weekly', "found %s, expected %s" %
                         (orig_p_exclusions.main_payment.schedule.frequency.name, 'Weekly'))
        self.assertEqual(orig_p_exclusions.exclusion_date, date(2016, 6, 21), "found %s, expected %s" %
                         (_date(orig_p_exclusions.exclusion_date, 'SHORT_DATE_FORMAT'),
                          _date(date(2016, 6, 21), 'SHORT_DATE_FORMAT')))

    def test_create_custom_payment_date_new_payment_in_calendar(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'series_choice': 'this',
            'payment_id': Payment.objects.get(title__exact='Payment 1').id,
            'next_date': '23/06/2016',
            'original_date': '2016-06-21'
        }
        c.post('/budget/update_payment_date/', payload)
        response = c.post('/budget/calendar_view/', {'start_date': '2016-05-01', 'end_date': '2016-08-01'})
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertIn('data', response_data, 'Error in response_data: %s' % response_data)
        pc = response_data["data"]
        self.assertEqual(pc[1]['payment_date'], '2016-06-23', "found %s, expected %s" %
                         (pc[1]['payment_date'], '2016-06-23'))
        self.assertEqual(pc[1]['title'], 'Payment 1 - 23/06/2016', "found %s, expected %s" %
                         (pc[1]['title'], 'Payment 1 - 23/06/2016'))
        self.assertEqual(pc[2]['payment_date'], '2016-07-05', "found %s, expected %s" %
                         (pc[2]['payment_date'], '2016-07-05'))
        self.assertEqual(pc[2]['title'], 'Payment 1', "found %s, expected %s" %
                         (pc[2]['title'], 'Payment 1'))

    def test_revert_custom_payment_date_to_original_schedule(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))

        # create exclusion
        payload = {
            'series_choice': 'this',
            'payment_id': Payment.objects.get(title__exact='Payment 1').id,
            'next_date': '23/06/2016',
            'original_date': '2016-06-21'
        }
        response = c.post('/budget/update_payment_date/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass", "found %s, expected %s" %
                         (response_data["result_success"], "pass"))
        new_payment_id = response_data['form_data']['payment_id']
        self.assertTrue(PaymentScheduleExclusion.objects.filter(exclusion_payment__pk=new_payment_id).exists(),
                        'new_payment_id: %i' % new_payment_id)

        # now revert
        response = c.post('/budget/update_payment_date/',
                          {'action': 'revert', 'payment_id': new_payment_id})
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass", "found %s, expected %s" %
                         (response_data["result_success"], "pass"))

        # check that PaymentExclusion removed as well
        self.assertFalse(PaymentScheduleExclusion.objects.filter(exclusion_payment__pk=new_payment_id).exists())


class UpdatePaymentClassificationTest(TestCase):
    def setUp(self):
        test_users()
        test_categories()
        test_payment_schedules()
        test_payments()
        test_bank_accounts()

        user = User.objects.get(username='john')
        pt1a = PaymentType.objects.create(
            name='pt1a',
            sort_order='2',
            owner=user
        )
        cat1a = Category.objects.create(
            name='cat1a',
            payment_type=pt1a,
            owner=user
        )
        subcat1a = SubCategory.objects.create(
            name='subcat1a',
            category=cat1a,
            owner=user
        )

    def test_update_existing_payment_classification(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'payment_id': Payment.objects.get(title__exact='Payment 1').id,
            'payment_type': PaymentType.objects.get(name__exact='pt1a').id,
            'category': Category.objects.get(name__exact='cat1a').id,
            'subcategory': SubCategory.objects.get(name__exact='subcat1a').id,
        }
        response = c.post('/budget/update_payment_classification/', payload)
        # print response.content
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass", "found %s, expected %s" %
                         (response_data["result_success"], "pass"))
        p = Payment.objects.get(title__iexact='payment 1')
        self.assertEqual(p.payment_type.name, 'pt1a', "found %s, expected %s" %
                         (p.payment_type.name, 'pt1a'))
        self.assertEqual(p.category.name, 'cat1a', "found %s, expected %s" %
                         (p.category.name, 'cat1a'))
        self.assertEqual(p.subcategory.name, 'subcat1a', "found %s, expected %s" %
                         (p.subcategory.name, 'subcat1a'))


class ManageCategoriesTest(TestCase):
    def setUp(self):
        test_users()
        test_categories()
        test_payment_schedules()
        test_payments()

    def test_new_payment_type(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {'new_payment_type': 'pt2'}
        response = c.get('/budget/manage_categories/', payload)
        self.assertNotIn("Exception", response.content, 'Exception occurred: %s' % response.content)
        self.assertEqual(response.context["result_success"], "pass", "found %s, expected %s" %
                         (response.context["result_success"], "pass"))
        self.assertIn('pt2', response.context["manage_payment_types"], "pt2 not found: %s" %
                      response.context["manage_payment_types"])

    def test_new_payment_type_with_duplicate_name(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {'new_payment_type': 'pt1'}
        response = c.get('/budget/manage_categories/', payload)
        self.assertIn("Exception", response.content, 'Exception occurred: %s' % response.content)

    def test_new_category_with_duplicate_name(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {'new_category': 'cat1', 'payment_type': PaymentType.objects.get(name__exact='pt1').id}
        response = c.get('/budget/manage_categories/', payload)
        self.assertIn("Exception", response.content, 'Exception occurred: %s' % response.content)

    def test_delete_category(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {'delete_category': Category.objects.get(name__exact='cat1').id}
        response = c.get('/budget/manage_categories/', payload)
        self.assertNotIn("Exception", response.content, 'Exception occurred: %s' % response.content)
        self.assertEqual(response.context["result_success"], "pass", "found %s, expected %s" %
                         (response.context["result_success"], "pass"))

    def test_edit_subcategory_with_duplicate_name(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        Category.objects.create(
            name='cat2',
            payment_type=PaymentType.objects.get(name__exact='pt1'),
            owner=User.objects.get(username__iexact='john')
        )
        payload = {'edit_category_name': 'cat1', 'edit_category_id': Category.objects.get(name__exact='cat1').id}
        response = c.get('/budget/manage_categories/', payload)
        self.assertIn("Exception", response.content, 'Exception occurred: %s' % response.content)


class PaymentViewTest(TestCase):
    def setUp(self):
        test_users()
        test_categories()
        test_payment_schedules()
        test_payments()

    def test_get_payments(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        response = c.post('/budget/payments/')
        self.assertNotIn("Exception", response.content, 'Exception occurred: %s' % response.content)


class PaymentModelsTest(TestCase):
    def setUp(self):
        test_users()
        test_categories()
        test_payment_schedules()
        test_payments()

    def test_weekly_missing_frequency(self):
        ps = PaymentSchedule.objects.create(
            next_date=datetime(2016, 6, 10),
            frequency=PaymentScheduleFrequency.objects.get(name__exact='Weekly'),
            weekly_dow_tue=True
        )
        with self.assertRaises(ValidationError):
            ps.full_clean()
        ps.save()


class MarkPaidReceivedTest(TestCase):
    # python manage.py test budget.tests.MarkPaidReceivedTest
    def setUp(self):
        test_users()
        test_categories()
        test_payment_schedules()
        test_payments()

    def test_mark_paid(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'update',
            'payment_id': Payment.objects.get(title__exact='Payment 1').id,
            'payment_date': '2016-06-07',
            'start_date': '2000-01-01',
            'end_date': '2017-01-01',
        }
        response = c.post('/budget/calendar_view/', payload)
        # print response.content
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        p = Payment.objects.get(title__iexact='payment 1')
        self.assertEqual(p.schedule.next_date, date(2016, 6, 21), "found %s, expected %s" %
                         (str(p.schedule.next_date), str(datetime(2016, 6, 21))))
