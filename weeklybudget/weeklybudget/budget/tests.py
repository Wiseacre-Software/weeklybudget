from datetime import date, datetime

from django.template.defaultfilters import date as _date
from django.test import TestCase, Client

from .views import *


# python manage.py test budget.tests

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

    ba1a = BankAccount.objects.create(
        title='john credit account',
        current_balance=1000,
        account_type='credit',
        account_limit=8000,
        owner=user[0],
    )
    ba1a.save()

    ba1b = BankAccount.objects.create(
        title='john virtual account',
        current_balance=0,
        account_type='virtual',
        owner=user[0],
    )
    ba1b.save()

    ba2 = BankAccount.objects.create(
        title='yoko account',
        current_balance=1000,
        owner=user[1],
    )
    ba2.save()


def test_categories():
    user_john = User.objects.get(username__exact='john')
    user_yoko = User.objects.get(username__exact='yoko')
    pt1 = PaymentType.objects.create(
        name='pt1',
        sort_order='1',
        owner=user_john
    )
    cat1 = Category.objects.create(
        name='cat1',
        payment_type=pt1,
        owner=user_john
    )
    SubCategory.objects.create(
        name='subcat1',
        category=cat1,
        owner=user_john
    )
    pt1a = PaymentType.objects.create(
        name='pt1a',
        sort_order='1',
        owner=user_john
    )
    cat1a = Category.objects.create(
        name='cat1a',
        payment_type=pt1a,
        owner=user_john
    )
    SubCategory.objects.create(
        name='subcat1a',
        category=cat1a,
        owner=user_john
    )
    pt1b = PaymentType.objects.create(
        name='pt1b',
        sort_order='1',
        owner=user_john
    )
    cat1b = Category.objects.create(
        name='cat1b',
        payment_type=pt1b,
        owner=user_john
    )
    SubCategory.objects.create(
        name='subcat1b',
        category=cat1b,
        owner=user_john
    )
    pt2 = PaymentType.objects.create(
        name='pt2',
        sort_order='2',
        owner=user_yoko
    )
    cat2 = Category.objects.create(
        name='cat2',
        payment_type=pt2,
        owner=user_yoko
    )
    SubCategory.objects.create(
        name='subcat2',
        category=cat2,
        owner=user_yoko
    )


def test_payment_schedules():
    PaymentScheduleFrequency.objects.create(name='User Defined', sort_order=6)
    PaymentScheduleFrequency.objects.create(name='Linked to Other Payment', sort_order=5)
    PaymentScheduleFrequency.objects.create(name='Annual', sort_order=4)
    PaymentScheduleFrequency.objects.create(name='Monthly', sort_order=3)
    PaymentScheduleFrequency.objects.create(name='Weekly', sort_order=2)
    PaymentScheduleFrequency.objects.create(name='Once Off', sort_order=1)


def test_payments():
    # Payment 1: Weekly
    user_john = User.objects.get(username__exact='john')
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
        owner=user_john,
        account=BankAccount.objects.get(title__exact='john account'),
    )

    # Credit Payment 1: Monthly
    ps = PaymentSchedule.objects.create(
        next_date=datetime(2016, 7, 1),
        frequency=PaymentScheduleFrequency.objects.get(name__exact='Monthly'),
        monthly_dom=1,
        monthly_frequency=1
    )
    Payment.objects.create(
        title='Credit Payment 1',
        in_out='o',
        amount=40,
        payment_type=PaymentType.objects.get(name__exact='pt1a'),
        category=Category.objects.get(name__exact='cat1a'),
        subcategory=SubCategory.objects.get(name__exact='subcat1a'),
        schedule=ps,
        owner=user_john,
        account=BankAccount.objects.get(title__exact='john credit account'),
    )

    # Virual Payment 1: Monthly
    ps = PaymentSchedule.objects.create(
        next_date=datetime(2016, 6, 15),
        frequency=PaymentScheduleFrequency.objects.get(name__exact='Monthly'),
        monthly_dom=15,
        monthly_frequency=1
    )
    Payment.objects.create(
        title='Virtual Payment 1',
        in_out='o',
        amount=500,
        payment_type=PaymentType.objects.get(name__exact='pt1b'),
        category=Category.objects.get(name__exact='cat1b'),
        subcategory=SubCategory.objects.get(name__exact='subcat1b'),
        schedule=ps,
        owner=user_john,
        account=BankAccount.objects.get(title__exact='john virtual account'),
    )

    # Annual Payment
    ps = PaymentSchedule.objects.create(
        next_date=datetime(2016, 6, 2),
        frequency=PaymentScheduleFrequency.objects.get(name__exact='Annual'),
        annual_dom=2,
        annual_moy=6,
        annual_frequency=5
    )
    Payment.objects.create(
        title='Annual Payment',
        in_out='o',
        amount=115,
        payment_type=PaymentType.objects.get(name__exact='pt2'),
        category=Category.objects.get(name__exact='cat2'),
        subcategory=SubCategory.objects.get(name__exact='subcat2'),
        schedule=ps,
        account=BankAccount.objects.get(title__exact='john account'),
        owner=user_john
    )


# endregion


class TestGenerateCalendarView(TestCase):
    payload = {'start_date': '1900-01-01', 'end_date': '2017-09-01'}

    def setUp(self):
        test_users()
        test_bank_accounts()
        test_categories()
        test_payment_schedules()
        test_payments()
        # p = Payment.objects.all()[0]
        # p.weekly_dow_tue = False
        # p.weekly_frequency = 0

    def test_calendar_view_setup(self):
        c = Client()
        c.login(username='john', password='johnpassword')
        response = c.post('/budget/calendar_view/', self.payload)
        response_data = jsonpickle.decode(response.content)
        pc = [p for p in response_data['data'] if p['title'] == 'Payment 1']
        self.assertEqual(pc[0]['payment_date'], str(date(2016, 6, 7)))
        self.assertEqual(float(pc[0]['curr_balance']), 1885)

        pc1 = (p_item for p_item in response_data['data'] if p_item["title"] == "Virtual Payment 1").next()
        self.assertEqual(pc1['title'], 'Virtual Payment 1', pc1)
        self.assertEqual(pc1['payment_date'], str(date(2016, 6, 15)), pc1)
        self.assertEqual(float(pc1['curr_balance']), 1885, pc1)
        self.assertEqual(float(pc1['curr_budget_balance']), 1385, pc1)

        pc1 = (p_item for p_item in response_data['data'] if p_item["title"] == "Credit Payment 1").next()
        self.assertEqual(pc1['title'], 'Credit Payment 1', pc1)
        self.assertEqual(pc1['payment_date'], str(date(2016, 7, 1)), pc1)
        self.assertEqual(float(pc1['curr_balance']), 2885, pc1)
        self.assertEqual(float(pc1['curr_budget_balance']), 2345, pc1)

        pc1 = (p_item for p_item in response_data['data'] if p_item["title"] == "Annual Payment").next()
        self.assertEqual(pc1['title'], 'Annual Payment', pc1)
        self.assertEqual(pc1['payment_date'], str(date(2016, 6, 2)), pc1)
        self.assertEqual(float(pc1['curr_balance']), 885, pc1)
        self.assertEqual(float(pc1['curr_budget_balance']), 885, pc1)

    def test_blank_calendar_view(self):
        Payment.objects.all().delete()
        BankAccount.objects.all().delete()
        c = Client()
        c.login(username='john', password='johnpassword')
        response = c.post('/budget/calendar_view/', self.payload)
        response_data = jsonpickle.decode(response.content)
        pc = response_data["data"]
        self.assertEqual(0, len(pc), pc)

    def test_calendar_view_no_payments(self):
        Payment.objects.all().delete()
        c = Client()
        c.login(username='john', password='johnpassword')
        response = c.post('/budget/calendar_view/', self.payload)
        response_data = jsonpickle.decode(response.content)
        pc = response_data["data"]
        self.assertEqual(0, len(pc), pc)

    def test_calendar_view_with_final_balance_provided(self):
        self.payload['final_balance'] = 50
        self.payload['final_budget_balance'] = 100

        c = Client()
        c.login(username='john', password='johnpassword')
        response = c.post('/budget/calendar_view/', self.payload)
        response_data = jsonpickle.decode(response.content)

        pc = [p for p in response_data['data'] if p['title'] == 'Payment 1']
        self.assertEqual(pc[0]['payment_date'], str(date(2016, 6, 7)))
        self.assertEqual(pc[0]['title'], 'Payment 1', pc[0])
        self.assertEqual(pc[0]['payment_date'], str(date(2016, 6, 7)))
        self.assertEqual(float(pc[0]['curr_balance']), 50 - 115 + 1000)
        self.assertEqual(float(pc[0]['curr_budget_balance']), 100 - 115 + 1000)

        pc1 = (p_item for p_item in response_data['data'] if p_item["title"] == "Virtual Payment 1").next()
        self.assertEqual(pc1['title'], 'Virtual Payment 1', pc1)
        self.assertEqual(pc1['payment_date'], str(date(2016, 6, 15)), pc1)
        self.assertEqual(float(pc1['curr_balance']), 50 - 115 + 1000)
        self.assertEqual(float(pc1['curr_budget_balance']), 100 - 115 + 1000 - 500)

        pc1 = (p_item for p_item in response_data['data'] if p_item["title"] == "Credit Payment 1").next()
        self.assertEqual(pc1['title'], 'Credit Payment 1', pc1)
        self.assertEqual(pc1['payment_date'], str(date(2016, 7, 1)), pc1)
        self.assertEqual(float(pc1['curr_balance']), 50 - 115 + 1000 + 1000)
        self.assertEqual(float(pc1['curr_budget_balance']), 100 - 115 + 1000 - 500 + 1000 - 40)

        pc1 = (p_item for p_item in response_data['data'] if p_item["title"] == "Annual Payment").next()
        self.assertEqual(pc1['title'], 'Annual Payment', pc1)
        self.assertEqual(pc1['payment_date'], str(date(2016, 6, 2)), pc1)
        self.assertEqual(float(pc1['curr_balance']), 50 - 115)
        self.assertEqual(float(pc1['curr_budget_balance']), 100 - 115)

    def test_monthly_specific_dom_payment_monthly_frequency(self):
        expected_next_date = date(2016, 8, 15)

        p = Payment.objects.get(title__exact='Payment 1')
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
        pc = [pc for pc in response_data["data"] if pc['title'] == 'Payment 1']
        self.assertEqual(pc[0]['payment_date'], str(expected_next_date),
                         "pc[0]['payment_date']: found %s (%s), expected %s (%s)" %
                         (pc[0]['payment_date'], str(type(pc[0]['payment_date'])),
                          str(expected_next_date), str(type(str(expected_next_date)))))
        self.assertEqual(pc[1]['payment_date'], str(expected_next_date + relativedelta(months=+2)),
                         "pc[1]['payment_date']: found %s, expected %s" %
                         (pc[1]['payment_date'], str(expected_next_date + relativedelta(months=+2))))

    def test_monthly_specific_dom_payment_second_last_day(self):
        expected_next_dates = rrule(MONTHLY, dtstart=datetime(2016, 8, 30), count=6, bymonthday=-2)

        p = Payment.objects.get(title__exact='Payment 1')
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
        pc = [pc for pc in response_data["data"] if pc['title'] == 'Payment 1']
        self.assertEqual(pc[0]['payment_date'], str(expected_next_dates[0].date()),
                         "pc[0]['payment_date']: found %s (%s), expected %s (%s)" %
                         (pc[0]['payment_date'], str(type(pc[0]['payment_date'])),
                          str(expected_next_dates[0].date()), str(type(str(expected_next_dates[0].date())))))
        self.assertEqual(pc[1]['payment_date'], str(expected_next_dates[1].date()),
                         "pc[1]['payment_date']: found %s, expected %s" %
                         (pc[1]['payment_date'], str(expected_next_dates[1].date())))

    def test_monthly_wom_payment_first_monday(self):
        expected_next_dates = rrule(MONTHLY, dtstart=datetime(2016, 8, 1), count=6, byweekday=MO(+1))

        p = Payment.objects.get(title__exact='Payment 1')
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
        pc = [pc for pc in response_data["data"] if pc['title'] == 'Payment 1']
        self.assertEqual(pc[0]['payment_date'], str(expected_next_dates[0].date()),
                         "pc[0]['payment_date']: found %s (%s), expected %s (%s)" %
                         (pc[0]['payment_date'], str(type(pc[0]['payment_date'])),
                          str(expected_next_dates[0].date()), str(type(str(expected_next_dates[0].date())))))
        self.assertEqual(pc[1]['payment_date'], str(expected_next_dates[1].date()),
                         "pc[1]['payment_date']: found %s, expected %s" %
                         (pc[1]['payment_date'], str(expected_next_dates[1].date())))

    def test_monthly_wom_payment_second_last_wed_of_every_4_months(self):
        expected_next_dates = rrule(MONTHLY, dtstart=datetime(2016, 8, 24), count=6,
                                    byweekday=WE(-2), interval=4)

        p = Payment.objects.get(title__exact='Payment 1')
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
        pc = [pc for pc in response_data["data"] if pc['title'] == 'Payment 1']
        self.assertEqual(pc[0]['payment_date'], str(expected_next_dates[0].date()),
                         "pc[0]['payment_date']: found %s (%s), expected %s (%s)" %
                         (pc[0]['payment_date'], str(type(pc[0]['payment_date'])),
                          str(expected_next_dates[0].date()), str(type(str(expected_next_dates[0].date())))))
        self.assertEqual(pc[1]['payment_date'], str(expected_next_dates[1].date()),
                         "pc[1]['payment_date']: found %s, expected %s" %
                         (pc[1]['payment_date'], str(expected_next_dates[1].date())))

    def test_annual_payment_every_second_year(self):
        expected_next_dates = rrule(YEARLY, dtstart=datetime(2016, 8, 15),
                                    count=2, bymonth=8, bymonthday=15, interval=2)
        self.assertEqual(expected_next_dates[0].date(), date(2016, 8, 15))

        p = Payment.objects.get(title__exact='Payment 1')
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
        pc = [pc for pc in response_data["data"] if pc['title'] == 'Payment 1']
        self.assertEqual(pc[0]['payment_date'], str(expected_next_dates[0].date()),
                         "pc[0]['payment_date']: found %s (%s), expected %s (%s)" %
                         (pc[0]['payment_date'], str(type(pc[0]['payment_date'])),
                          str(expected_next_dates[0].date()), str(type(str(expected_next_dates[0].date())))))
        self.assertEqual(pc[1]['payment_date'], str(expected_next_dates[1].date()),
                         "pc[1]['payment_date']: found %s, expected %s" %
                         (pc[1]['payment_date'], str(expected_next_dates[1].date())))

    def test_weekly_payment_with_occurrences(self):
        user_john = User.objects.get(username__exact='john')
        ps = PaymentSchedule.objects.create(
            next_date=datetime(2016, 6, 20),
            frequency=PaymentScheduleFrequency.objects.get(name__exact='Weekly'),
            weekly_dow_mon=True,
            weekly_frequency=2,
            occurrences=2,
        )
        Payment.objects.create(
            title='Payment 2',
            in_out='o',
            amount=200,
            payment_type=PaymentType.objects.get(name__exact='pt1'),
            category=Category.objects.get(name__exact='cat1'),
            subcategory=SubCategory.objects.get(name__exact='subcat1'),
            schedule=ps,
            owner=user_john,
            account=BankAccount.objects.get(title__exact='john account'),
        )

        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        response = c.post('/budget/calendar_view/', {'start_date': '1900-01-01', 'end_date': '2017-09-01'})
        response_data = jsonpickle.decode(response.content)
        pc = [p for p in response_data['data'] if p['title'] == 'Payment 2']
        self.assertEqual(2, len(pc))
        self.assertEqual(pc[0]['payment_date'], str(date(2016, 6, 20)))
        self.assertEqual(pc[1]['payment_date'], str(date(2016, 7, 4)))

    def test_monthly_payment_with_end_date(self):
        user_john = User.objects.get(username__exact='john')
        ps = PaymentSchedule.objects.create(
            next_date=datetime(2016, 6, 25),
            frequency=PaymentScheduleFrequency.objects.get(name__exact='Monthly'),
            monthly_dom=25,
            monthly_frequency=1,
            end_date=datetime(2017, 9, 9),
        )
        Payment.objects.create(
            title='Payment 2',
            in_out='o',
            amount=200,
            payment_type=PaymentType.objects.get(name__exact='pt1'),
            category=Category.objects.get(name__exact='cat1'),
            subcategory=SubCategory.objects.get(name__exact='subcat1'),
            schedule=ps,
            owner=user_john,
            account=BankAccount.objects.get(title__exact='john account'),
        )

        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        response = c.post('/budget/calendar_view/', {'start_date': '1900-01-01', 'end_date': '2017-09-01'})
        response_data = jsonpickle.decode(response.content)
        pc = [p for p in response_data['data'] if p['title'] == 'Payment 2']
        self.assertEqual(15, len(pc))
        self.assertEqual(pc[0]['payment_date'], str(date(2016, 6, 25)))
        self.assertEqual(pc[14]['payment_date'], str(date(2017, 8, 25)))

    def test_annual_payment_with_occurrences(self):
        user_john = User.objects.get(username__exact='john')
        ps = PaymentSchedule.objects.create(
            next_date=datetime(2016, 6, 20),
            frequency=PaymentScheduleFrequency.objects.get(name__exact='Annual'),
            annual_dom=20,
            annual_moy=6,
            annual_frequency=3,
            occurrences=3,
        )
        Payment.objects.create(
            title='Payment 2',
            in_out='o',
            amount=200,
            payment_type=PaymentType.objects.get(name__exact='pt1'),
            category=Category.objects.get(name__exact='cat1'),
            subcategory=SubCategory.objects.get(name__exact='subcat1'),
            schedule=ps,
            owner=user_john,
            account=BankAccount.objects.get(title__exact='john account'),
        )

        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        response = c.post('/budget/calendar_view/', {'start_date': '1900-01-01', 'end_date': '2025-09-01'})
        response_data = jsonpickle.decode(response.content)
        pc = [p for p in response_data['data'] if p['title'] == 'Payment 2']
        self.assertEqual(3, len(pc))
        self.assertEqual(pc[0]['payment_date'], str(date(2016, 6, 20)))
        self.assertEqual(pc[1]['payment_date'], str(date(2019, 6, 20)))
        self.assertEqual(pc[2]['payment_date'], str(date(2022, 6, 20)))

    def test_linked_payment_with_offset_type_days(self):
        user_john = User.objects.get(username__exact='john')
        ps = PaymentSchedule.objects.create(
            next_date=datetime(2016, 6, 20),
            frequency=PaymentScheduleFrequency.objects.get(name__exact='Linked to Other Payment'),
        )
        Payment.objects.create(
            title='Linked Payment',
            in_out='o',
            amount=200,
            payment_type=PaymentType.objects.get(name__exact='pt1'),
            category=Category.objects.get(name__exact='cat1'),
            subcategory=SubCategory.objects.get(name__exact='subcat1'),
            schedule=ps,
            parent_payment=Payment.objects.get(title__exact='Payment 1'),
            offset=-1,
            offset_type='days',
            owner=user_john,
            account=BankAccount.objects.get(title__exact='john account'),
        )

        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        response = c.post('/budget/calendar_view/', {'start_date': '1900-01-01', 'end_date': '2017-09-01'})
        response_data = jsonpickle.decode(response.content)
        pc = [p for p in response_data['data'] if p['title'] == 'Linked Payment']
        self.assertEqual(pc[0]['payment_date'], str(date(2016, 6, 20)))
        self.assertEqual(pc[1]['payment_date'], str(date(2016, 7, 4)))
        self.assertEqual(pc[2]['payment_date'], str(date(2016, 7, 18)))

    def test_linked_payment_with_offset_type_weeks_with_occurrence(self):
        user_john = User.objects.get(username__exact='john')
        ps = PaymentSchedule.objects.create(
            next_date=datetime(2016, 5, 20),
            frequency=PaymentScheduleFrequency.objects.get(name__exact='Linked to Other Payment'),
            occurrences=2
        )
        Payment.objects.create(
            title='Linked Payment',
            in_out='o',
            amount=200,
            payment_type=PaymentType.objects.get(name__exact='pt1'),
            category=Category.objects.get(name__exact='cat1'),
            subcategory=SubCategory.objects.get(name__exact='subcat1'),
            schedule=ps,
            parent_payment=Payment.objects.get(title__exact='Payment 1'),
            offset=1,
            offset_type='weeks',
            owner=user_john,
            account=BankAccount.objects.get(title__exact='john account'),
        )

        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        response = c.post('/budget/calendar_view/', {'start_date': '1900-01-01', 'end_date': '2017-09-01'})
        response_data = jsonpickle.decode(response.content)
        pc = [p for p in response_data['data'] if p['title'] == 'Linked Payment']
        self.assertEqual(2, len(pc))
        self.assertEqual(str(date(2016, 6, 14)), pc[0]['payment_date'])
        self.assertEqual(str(date(2016, 6, 28)), pc[1]['payment_date'])

    def test_linked_payment_with_offset_type_months_with_end_date(self):
        user_john = User.objects.get(username__exact='john')
        ps = PaymentSchedule.objects.create(
            next_date=datetime(2016, 5, 20),
            frequency=PaymentScheduleFrequency.objects.get(name__exact='Linked to Other Payment'),
            end_date=datetime(2016, 10, 20),
        )
        Payment.objects.create(
            title='Linked Payment',
            in_out='o',
            amount=200,
            payment_type=PaymentType.objects.get(name__exact='pt1'),
            category=Category.objects.get(name__exact='cat1'),
            subcategory=SubCategory.objects.get(name__exact='subcat1'),
            schedule=ps,
            parent_payment=Payment.objects.get(title__exact='Payment 1'),
            offset=3,
            offset_type='months',
            owner=user_john,
            account=BankAccount.objects.get(title__exact='john account'),
        )

        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        response = c.post('/budget/calendar_view/', {'start_date': '1900-01-01', 'end_date': '2017-09-01'})
        response_data = jsonpickle.decode(response.content)
        pc = [p for p in response_data['data'] if p['title'] == 'Linked Payment']
        self.assertEqual(4, len(pc))
        self.assertEqual(str(date(2016, 9, 7)), pc[0]['payment_date'])
        self.assertEqual(str(date(2016, 9, 21)), pc[1]['payment_date'])
        self.assertEqual(str(date(2016, 10, 5)), pc[2]['payment_date'])
        self.assertEqual(str(date(2016, 10, 19)), pc[3]['payment_date'])

class TestAuthentication(TestCase):
    def setUp(self):
        test_users()
        test_bank_accounts()
        test_categories()
        test_payment_schedules()
        ps = PaymentSchedule.objects.create(
            next_date=datetime(2016, 6, 7),
            frequency=PaymentScheduleFrequency.objects.get(name__exact='Weekly'),
            weekly_dow_tue=True,
            weekly_frequency=2
        )
        p = Payment.objects.create(
            title='test',
            amount=1000,
            payment_type=PaymentType.objects.get(name__exact='pt1'),
            category=Category.objects.get(name__exact='cat1'),
            subcategory=SubCategory.objects.get(name__exact='subcat1'),
            schedule=ps,
            owner=User.objects.get(username__exact='john'),
            account=BankAccount.objects.get(title__exact='john account'),
        )
        p.save()

    def test_login_invalid_user(self):
        c = Client()
        self.assertFalse(c.login(username='fred', password='secret'))

    def test_login_valid_user(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))

    def test_user_cant_see_other_user_payment(self):
        c = Client()
        self.assertTrue(c.login(username='yoko', password='yokopassword'))
        u = User.objects.get(username__exact='yoko')
        response = c.get('/budget/')
        self.assertEqual(len(response.context['payments']), 0)
        self.assertEqual(len(jsonpickle.decode(response.context['manage_payment_types'])),
                         len(PaymentType.objects.filter(owner=u, active=True).all()))
        self.assertEqual(len(jsonpickle.decode(response.context['manage_categories'])),
                         len(Category.objects.filter(owner=u, active=True).all()))
        self.assertEqual(len(jsonpickle.decode(response.context['manage_subcategories'])),
                         len(SubCategory.objects.filter(owner=u, active=True).all()))

    def test_user_can_see_their_own_payment(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        u = User.objects.get(username__exact='john')
        response = c.get('/budget/')
        self.assertEqual(len(response.context['payments']), 1)
        self.assertEqual(len(jsonpickle.decode(response.context['manage_payment_types'])),
                         len(PaymentType.objects.filter(owner=u, active=True).all()))
        self.assertEqual(len(jsonpickle.decode(response.context['manage_categories'])),
                         len(Category.objects.filter(owner=u, active=True).all()))
        self.assertEqual(len(jsonpickle.decode(response.context['manage_subcategories'])),
                         len(SubCategory.objects.filter(owner=u, active=True).all()))


class TestBankAccount(TestCase):
    def setUp(self):
        test_users()
        test_bank_accounts()

    def test_cant_see_other_user_bank_account(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        response = c.get('/budget/bank_account/')
        self.assertIsNotNone(response.context, response.content)
        ba = response.context["bank_accounts"]
        self.assertEqual(len(ba), 3)

    def test_invalid_user_cant_see_squat(self):
        c = Client()
        self.assertFalse(c.login(username='not_john', password='not_johnpassword'))

    def test_create_bank_account(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {'action': 'new'}
        response = c.post('/budget/bank_account/', payload)
        self.assertEqual(len(response.context["bank_accounts"]), 4, response.context["bank_accounts"])
        self.assertEqual(response.context["result_success"], "pass", response.content)
        bas = list(ba for ba in response.context["bank_accounts"] if ba.title == 'Bank Account #1')
        self.assertEqual(1, len(bas))

        response = c.post('/budget/bank_account/', payload)
        self.assertEqual(len(response.context["bank_accounts"]), 5, response.context["bank_accounts"])
        self.assertEqual(response.context["result_success"], "pass", response.content)
        self.assertEqual(1, len(list(ba for ba in response.context["bank_accounts"] if ba.title == 'Bank Account #2')))

    def test_update_bank_account(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        ba = BankAccount.objects.get(title__exact='john account')
        payload = {
            'action': 'update',
            'bank_account_id': ba.pk,
            'title': 'john account - updated!',
        }
        response = c.post('/budget/bank_account/', payload)
        self.assertIsNotNone(response.context, 'response.context is None. response.content: %s' % response.content)
        self.assertEqual(response.context["result_success"], "pass", response.context['result_message'])
        self.assertEqual(len(response.context['bank_accounts']), 3)
        for res in response.context['bank_accounts']:
            if res.pk == ba.pk:
                break
        self.assertEqual(res.title, 'john account - updated!', res.title)

        payload = {
            'action': 'update',
            'bank_account_id': ba.pk,
            'current_balance': 7000,
        }
        response = c.post('/budget/bank_account/', payload)
        for res in response.context['bank_accounts']:
            if res.pk == ba.pk:
                break
        self.assertEqual(res.current_balance, 7000, res.current_balance)

        payload = {
            'action': 'update',
            'bank_account_id': ba.pk,
            'account_type': 'virtual',
        }
        response = c.post('/budget/bank_account/', payload)
        for res in response.context['bank_accounts']:
            if res.pk == ba.pk:
                break
        self.assertEqual(res.account_type, 'virtual', res.account_type)

    def test_delete_bank_account(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        ba = BankAccount.objects.get(title__exact='john account', active=True)
        payload = {
            'action': 'delete',
            'bank_account_id': ba.pk,
        }
        response = c.post('/budget/bank_account/', payload)
        self.assertIsNotNone(response.context, 'response.context is None. response.content: %s' % response.content)
        self.assertEqual(len(response.context['bank_accounts']), 2,
                         "context['bank_accounts']: found %i, expected %i, response.context: %s" %
                         (len(response.context['bank_accounts']), 2, response.context))
        self.assertEqual(response.context["result_success"], "pass",
                         "result: found %s, expected %s" %
                         (response.context["result_success"], "pass"))

    def test_cannot_have_bank_account_with_same_name(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        ba = BankAccount.objects.get(title__exact='john account')
        payload = {
            'action': 'update',
            'bank_account_id': ba.pk,
            'title': 'john account',
        }
        response = c.post('/budget/bank_account/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertEqual(response_data["result_success"], "fail", "found %s, expected %s" %
                         (response_data["result_success"], "fail"))


class TestUpdatePayment(TestCase):
    def setUp(self):
        test_users()
        test_categories()
        test_payment_schedules()
        test_bank_accounts()
        test_payments()

    def test_create_weekly_payment(self):
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
            'account': BankAccount.objects.get(title__exact='john account').id,
            'schedule_frequency': PaymentScheduleFrequency.objects.get(name__exact='Weekly').id,
            'next_date': '20/06/2016',
            'weekly_dow_tue': 'true',
            'weekly_frequency': 2,
            'until_type': 'forever'
        }
        response = c.post('/budget/update_payment/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass")
        self.assertEqual(response_data["form_data"]['title'], "payment 2")
        p = Payment.objects.get(title__iexact='payment 2')
        self.assertTrue(p.schedule.weekly_dow_tue)
        self.assertIsNone(p.schedule.end_date)
        self.assertEqual(0, p.schedule.occurrences)

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
            'account': BankAccount.objects.get(title__exact='john account').id,
            'schedule_frequency': PaymentScheduleFrequency.objects.get(name__exact='Weekly').id,
            'next_date': '20/06/2016',
            'weekly_dow_tue': 'true',
            'weekly_frequency': 2
        }
        response = c.post('/budget/update_payment/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertEqual(response_data["result_success"], "fail", "found %s, expected %s" %
                         (response_data["result_success"], "fail"))

    def test_create_weekly_payment_with_occurrences(self):
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
            'account': BankAccount.objects.get(title__exact='john account').id,
            'schedule_frequency': PaymentScheduleFrequency.objects.get(name__exact='Weekly').id,
            'next_date': '20/06/2016',
            'weekly_dow_tue': 'true',
            'weekly_frequency': 2,
            'until_type': 'occurrences',
            'occurrences': 2,
        }
        response = c.post('/budget/update_payment/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass")
        self.assertEqual(response_data["form_data"]['title'], "payment 2")
        p = Payment.objects.get(title__iexact='payment 2')
        self.assertTrue(p.schedule.weekly_dow_tue)
        self.assertIsNone(p.schedule.end_date)
        self.assertEqual(2, p.schedule.occurrences)

    def test_create_monthly_payment_with_end_date(self):
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
            'account': BankAccount.objects.get(title__exact='john account').id,
            'schedule_frequency': PaymentScheduleFrequency.objects.get(name__exact='Monthly').id,
            'next_date': '20/06/2016',
            'monthly_dom': 20,
            'monthly_frequency': 2,
            'until_type': 'end_date',
            'end_date': '20/06/2017',
        }
        response = c.post('/budget/update_payment/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass")
        self.assertEqual(response_data["form_data"]['title'], "payment 2")
        p = Payment.objects.get(title__iexact='payment 2')
        self.assertEqual(20, p.schedule.monthly_dom)
        self.assertEqual(2, p.schedule.monthly_frequency)
        self.assertEqual(str(date(2017, 6, 20)), str(p.schedule.end_date))
        self.assertEqual(0, p.schedule.occurrences)

    def test_create_linked_payment(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'update',
            'title': 'Linked payment',
            'amount': 1000,
            'in_out': 'o',
            'payment_type': PaymentType.objects.get(name__exact='pt1').id,
            'category': Category.objects.get(name__exact='cat1').id,
            'subcategory': SubCategory.objects.get(name__exact='subcat1').id,
            'account': BankAccount.objects.get(title__exact='john account').id,
            'schedule_frequency': PaymentScheduleFrequency.objects.get(name__exact='Linked to Other Payment').id,
            'next_date': '20/06/2016',
            'linked_to': Payment.objects.get(title__exact='Payment 1').id,
            'offset': -1,
            'offset_type': 'days',
            'until_type': 'forever',
        }
        response = c.post('/budget/update_payment/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass")
        self.assertEqual(response_data["form_data"]['title'], "Linked payment")
        self.assertTrue(Payment.objects.filter(title__iexact='Linked payment').exists())
        self.assertTrue(Payment.objects.exclude(parent_payment__isnull=True).exists())

        p = Payment.objects.get(title__iexact='Linked payment')
        self.assertIsNotNone(p.parent_payment)
        self.assertEqual('Payment 1', p.parent_payment.title)
        self.assertEqual(-1, p.offset)
        self.assertEqual('days', p.offset_type)
        self.assertEqual(PaymentScheduleFrequency.objects.get(name__exact='Linked to Other Payment').id, p.schedule.frequency.id)
        self.assertEqual('2016-06-20', str(p.schedule.next_date))
        self.assertIsNone(p.schedule.end_date)
        self.assertEqual(0, p.schedule.occurrences)

    # TODO need to create test for linked payment out of update_payment_date

    # TODO Do not allow payments with children to be deleted
    # TODO User specified schedule, i.e. user maintains a list of dates (saves on having to create multiple payments...)

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
            'account': BankAccount.objects.get(title__exact='john account').id,
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
        self.assertIn('cat1', response_data["search_terms"])

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
        self.assertEqual(Payment.objects.filter(pk=payment_id, active=True).count(), 0, "found %i, expected %i" %
                         (Payment.objects.filter(pk=payment_id, active=True).count(), 0))

    def test_payment_request_via_get(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {}
        response = c.get('/budget/update_payment/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertEqual(response_data["result_success"], "fail", "found %s, expected %s" %
                         (response_data["result_success"], "fail"))

    def test_payment_with_no_payment_subcategory(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'update',
            'title': 'payment no category',
            'amount': 2000,
            'in_out': 'o',
            'payment_type': PaymentType.objects.get(name__exact='pt1').id,
            'category': Category.objects.get(name__exact='cat1').id,
            'account': BankAccount.objects.get(title__exact='john account').id,
            'schedule_frequency': PaymentScheduleFrequency.objects.get(name__exact='Weekly').id,
            'next_date': '21/06/2016',
            'weekly_dow_tue': 'true',
            'weekly_dow_wed': 'false',
            'weekly_frequency': 1
        }
        response = c.post('/budget/update_payment/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass", "found %s, expected %s, response_data: %s" %
                         (response_data["result_success"], "pass", response_data))
        self.assertEqual(response_data["form_data"]['title'], "payment no category", "found %s, expected %s" %
                         (response_data["form_data"]['title'], "payment no category"))
        # p = Payment.objects.get(title__iexact='payment no category')
        # self.assertIsNone(p.category, "found a category, expected none")
        # self.assertIsNone(p.category, "found a subcategory, expected none")

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
            'account': BankAccount.objects.get(title__exact='john account').id,
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

    def test_new_payment(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'blank',
        }
        response = c.post('/budget/update_payment/', payload)
        self.assertRegexpMatches(response.content, '<input .*id="id_title"')

    def test_default_payment_title(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'blank',
            'title': 'New Payment',
        }
        response = c.post('/budget/update_payment/', payload)
        self.assertRegexpMatches(response.content,
                                 '<input .*[id="id_title".*value="New Payment"|value="New Payment".*id="id_title"]')


class TestUpdatePaymentDate(TestCase):
    def setUp(self):
        test_users()
        test_categories()
        test_payment_schedules()
        test_bank_accounts()
        test_payments()

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
        pc = [pc for pc in response_data["data"] if pc['title'] == 'Payment 1']
        self.assertEqual(pc[1]['payment_date'], '2016-06-23', pc)
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
        self.assertFalse(
            PaymentScheduleExclusion.objects.filter(exclusion_payment__pk=new_payment_id, active=True).exists())
        self.assertFalse(Payment.objects.filter(pk=new_payment_id, active=True).exists())

    def test_update_start_date(self):
        p = Payment.objects.get(title__iexact='payment 1')
        p.schedule.frequency = PaymentScheduleFrequency.objects.get(name__exact='Monthly')
        p.schedule.next_date = datetime(2016, 10, 1)
        p.schedule.monthly_dom = 1
        p.schedule.monthly_frequency = 1

        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'series_choice': 'series',
            'payment_id': Payment.objects.get(title__exact='Payment 1').id,
            'schedule_frequency': PaymentScheduleFrequency.objects.get(name__exact='Monthly').id,
            'next_date': '19/02/2017',
            'monthly_dom': 1,
            'monthly_frequency': 1,
        }
        response = c.post('/budget/update_payment_date/', payload)
        # print response.content
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass", "found %s, expected %s" %
                         (response_data["result_success"], "pass"))
        p = Payment.objects.get(title__iexact='payment 1')
        self.assertEqual(p.schedule.monthly_dom, 1, "found %i, expected %i" %
                         (p.schedule.monthly_dom, 1))
        self.assertEqual(p.schedule.monthly_frequency, 1, "found %i, expected %i" %
                         (p.schedule.monthly_frequency, 1))
        self.assertEqual(p.schedule.next_date.strftime("%x %X"), datetime(2017, 3, 1).strftime("%x %X"),
                         "found %s (%s), expected %s (%s)" % (
                             p.schedule.next_date.strftime("%x %X"), type(p.schedule.next_date),
                             datetime(2017, 3, 1).strftime("%x %X"), type(datetime(2017, 3, 1))))
        self.assertFalse(PaymentScheduleExclusion.objects.all().exists())

        # expected_next_date = rrule(MONTHLY, dtstart=datetime(2017, 2, 1),count=1, bymonthday=1)[0].date()
        response = c.post('/budget/calendar_view/', {'start_date': '2016-08-01', 'end_date': '2017-08-01'})
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        pc = [pc for pc in response_data["data"] if pc['title'] == 'Payment 1']
        self.assertEqual(pc[0]['payment_date'], '2017-03-01',
                         "pc[0]['payment_date']: found %s (%s), expected %s" %
                         (pc[0]['payment_date'], str(type(pc[0]['payment_date'])),
                          '2017-03-01'))
        self.assertEqual(pc[1]['payment_date'], '2017-04-01',
                         "pc[1]['payment_date']: found %s, expected %s" %
                         (pc[1]['payment_date'], '2017-04-01'))

    def test_update_to_linked_payment(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'series_choice': 'series',
            'payment_id': Payment.objects.get(title__exact='Payment 1').id,
            'schedule_frequency': PaymentScheduleFrequency.objects.get(name__exact='Linked to Other Payment').id,
            'next_date': '19/02/2017',
            'linked_to': 1,
            'monthly_frequency': 1,
        }
        response = c.post('/budget/update_payment_date/', payload)
        # print response.content
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual(response_data["result_success"], "pass", "found %s, expected %s" %
                         (response_data["result_success"], "pass"))
        p = Payment.objects.get(title__iexact='payment 1')
        self.assertEqual(p.schedule.monthly_dom, 1, "found %i, expected %i" %
                         (p.schedule.monthly_dom, 1))
        self.assertEqual(p.schedule.monthly_frequency, 1, "found %i, expected %i" %
                         (p.schedule.monthly_frequency, 1))
        self.assertEqual(p.schedule.next_date.strftime("%x %X"), datetime(2017, 3, 1).strftime("%x %X"),
                         "found %s (%s), expected %s (%s)" % (
                             p.schedule.next_date.strftime("%x %X"), type(p.schedule.next_date),
                             datetime(2017, 3, 1).strftime("%x %X"), type(datetime(2017, 3, 1))))
        self.assertFalse(PaymentScheduleExclusion.objects.all().exists())

        # expected_next_date = rrule(MONTHLY, dtstart=datetime(2017, 2, 1),count=1, bymonthday=1)[0].date()
        response = c.post('/budget/calendar_view/', {'start_date': '2016-08-01', 'end_date': '2017-08-01'})
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("Exception", response_data, 'Exception occurred: %s' % response_data)
        pc = [pc for pc in response_data["data"] if pc['title'] == 'Payment 1']
        self.assertEqual(pc[0]['payment_date'], '2017-03-01',
                         "pc[0]['payment_date']: found %s (%s), expected %s" %
                         (pc[0]['payment_date'], str(type(pc[0]['payment_date'])),
                          '2017-03-01'))
        self.assertEqual(pc[1]['payment_date'], '2017-04-01',
                         "pc[1]['payment_date']: found %s, expected %s" %
                         (pc[1]['payment_date'], '2017-04-01'))


class TestUpdatePartialPayment(TestCase):
    def setUp(self):
        test_users()
        test_categories()
        test_payment_schedules()
        test_bank_accounts()
        test_payments()

    def test_update_single_payment_amount(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'payment_id': Payment.objects.get(title__exact='Payment 1').id,
            'field': 'incoming',
            'single_series': 'single',
            'value': '2000',
            'payment_date': '2016-06-21',
        }
        response = c.post('/budget/update_payment_partial/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertEqual(response_data["result_success"], "pass", 'response_data: %s' % response_data)
        p = Payment.objects.get(title__iexact='payment 1')
        self.assertEqual(p.schedule.next_date, date(2016, 6, 7))
        self.assertEqual(p.amount, 1000)
        pe = PaymentScheduleExclusion.objects.get(main_payment=p.id)
        self.assertEqual(pe.exclusion_payment.schedule.next_date, date(2016, 6, 21))
        self.assertEqual(pe.exclusion_payment.amount, 2000)

    def test_update_series_payment_amount(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'payment_id': Payment.objects.get(title__exact='Payment 1').id,
            'field': 'incoming',
            'single_series': 'series',
            'value': '2000',
        }
        response = c.post('/budget/update_payment_partial/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertEqual(response_data["result_success"], "pass", 'response_data: %s' % response_data)
        p = Payment.objects.get(title__iexact='payment 1')
        self.assertEqual(p.schedule.next_date, date(2016, 6, 7))
        self.assertEqual(p.amount, 2000)

    def test_update_payment_bank_account(self):
        ba3 = BankAccount.objects.create(
            title='john account #2',
            current_balance=1000,
            owner=User.objects.get(username__exact='john'),
        )

        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'payment_id': Payment.objects.get(title__exact='Payment 1').id,
            'field': 'account_id',
            'single_series': 'series',
            'value': ba3.id,
        }
        response = c.post('/budget/update_payment_partial/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertEqual(response_data["result_success"], "pass", 'response_data: %s' % response_data)
        p = Payment.objects.get(title__iexact='payment 1')
        self.assertEqual(p.account.title, 'john account #2')

        ba4 = BankAccount.objects.create(
            title='john account #4',
            current_balance=10000,
            owner=User.objects.get(username__exact='john'),
        )
        payload = {
            'payment_id': Payment.objects.get(title__exact='Payment 1').id,
            'field': 'account_id',
            'single_series': 'single',
            'value': ba4.id,
            'payment_date': '2016-06-21',
        }
        response = c.post('/budget/update_payment_partial/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertEqual(response_data["result_success"], "pass", 'response_data: %s' % response_data)
        p = Payment.objects.get(title__iexact='payment 1')
        self.assertEqual(p.schedule.next_date, date(2016, 6, 7))
        self.assertEqual(p.account.title, 'john account #2')
        pe = PaymentScheduleExclusion.objects.get(main_payment=p.id)
        self.assertEqual(pe.exclusion_payment.schedule.next_date, date(2016, 6, 21))
        self.assertEqual(pe.exclusion_payment.account.title, 'john account #4')

    def test_update_payment_title(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payment_id = Payment.objects.get(title__exact='Payment 1').id
        payload = {
            'payment_id': payment_id,
            'field': 'title',
            'single_series': 'series',
            'value': 'Payment 1 - updated',
        }
        response = c.post('/budget/update_payment_partial/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertEqual(response_data["result_success"], "pass", 'response_data: %s' % response_data)
        p = Payment.objects.get(pk=payment_id)
        self.assertEqual(p.title, 'Payment 1 - updated')

        payload = {
            'payment_id': payment_id,
            'field': 'title',
            'single_series': 'single',
            'value': 'Payment 1 - updated again',
            'payment_date': '2016-06-21',
        }
        response = c.post('/budget/update_payment_partial/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertEqual(response_data["result_success"], "pass", 'response_data: %s' % response_data)
        p = Payment.objects.get(pk=payment_id)
        self.assertEqual(p.schedule.next_date, date(2016, 6, 7))
        self.assertEqual(p.title, 'Payment 1 - updated')
        pe = PaymentScheduleExclusion.objects.get(main_payment=p.id)
        self.assertEqual(pe.exclusion_payment.schedule.next_date, date(2016, 6, 21))
        self.assertEqual(pe.exclusion_payment.title, 'Payment 1 - updated again')


class UpdatePaymentClassificationTest(TestCase):
    def setUp(self):
        test_users()
        test_categories()
        test_payment_schedules()
        test_bank_accounts()
        test_payments()

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
        # logger.debug("test_update_existing_payment_classification:- response.content: %s" % response.content)
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
        test_bank_accounts()
        test_payments()

    def test_initialise_manage_form(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {'curr_payment_type': 'pt1', 'curr_category': 'cat1', 'curr_subcategory': 'subcat1'}
        response = c.post('/budget/manage_categories/', payload)
        self.assertNotIn("Exception", response.content, 'Exception occurred: %s' % response.content)
        self.assertEqual(response.context["result_success"], "pass", "found %s, expected %s" %
                         (response.context["result_success"], "pass"))
        self.assertRegexpMatches(response.content,
                                 '<input .*[value="pt1".*id="id_selected_payment_type"|id="id_selected_payment_type".*value="pt1"]')
        self.assertRegexpMatches(response.content,
                                 '<input .*[value="cat1".*id="id_selected_category"|id="id_selected_category".*value="cat1"]')
        self.assertRegexpMatches(response.content,
                                 '<input .*[value="subcat1".*id="id_selected_subcategory"|id="id_selected_subcategory".*value="subcat1"]')

    def test_new_payment_type(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {'new_payment_type': 'pt2'}
        response = c.post('/budget/manage_categories/', payload)
        self.assertNotIn("Exception", response.content, 'Exception occurred: %s' % response.content)
        self.assertEqual(response.context["result_success"], "pass", "found %s, expected %s" %
                         (response.context["result_success"], "pass"))
        self.assertRegexpMatches(response.content, '<td [^>]*>pt2</td>')
        self.assertRegexpMatches(response.content, '<input [^>]*pt2[^>]*/>')

    def test_new_payment_type_with_duplicate_name(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {'new_payment_type': 'pt1'}
        response = c.post('/budget/manage_categories/', payload)
        self.assertEqual("fail", response.context['result_success'])

    def test_new_category_with_duplicate_name(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {'new_category': 'cat1', 'payment_type': PaymentType.objects.get(name__exact='pt1').id}
        response = c.post('/budget/manage_categories/', payload)
        self.assertEqual("fail", response.context['result_success'])

    def test_delete_category(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {'delete_category': Category.objects.get(name__exact='cat1').id}
        response = c.post('/budget/manage_categories/', payload)
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
        response = c.post('/budget/manage_categories/', payload)
        self.assertEqual("fail", response.context['result_success'])

    def test_new_payment_type_for_category(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        pt_id = PaymentType.objects.get(name__exact='pt1a').id
        cat_id = Category.objects.get(name__exact='cat1').id
        payload = {'new_payment_type_for_category': pt_id,
                   'category_id': cat_id}
        response = c.post('/budget/manage_categories/', payload)
        self.assertEqual(response.context["result_success"], "pass", "found %s, expected %s: %s" %
                         (response.context["result_success"], "pass", response.context["result_message"]))
        self.assertIn(jsonpickle.encode([pt_id, cat_id]), response.context['categorymap'])
        p = Payment.objects.get(title='Payment 1')
        self.assertEqual('pt1a', p.payment_type.name)

    def test_new_category_for_subcategory(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        pt_id = PaymentType.objects.get(name__exact='pt1a').id
        cat_id = Category.objects.get(name__exact='cat1a').id
        subcat_id = SubCategory.objects.get(name__exact='subcat1').id
        payload = {'new_category_for_subcategory': cat_id,
                   'subcategory_id': subcat_id}
        response = c.post('/budget/manage_categories/', payload)
        self.assertEqual(response.context["result_success"], "pass", "found %s, expected %s: %s" %
                         (response.context["result_success"], "pass", response.context["result_message"]))
        self.assertIn(jsonpickle.encode([pt_id, cat_id, subcat_id]), response.context['categorymap'])
        self.assertEqual('cat1a', Payment.objects.get(title='Payment 1').category.name)
        self.assertEqual('pt1a', Payment.objects.get(title='Payment 1').payment_type.name)


class PaymentViewTest(TestCase):
    def setUp(self):
        test_users()
        test_categories()
        test_payment_schedules()
        test_bank_accounts()
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
        test_bank_accounts()
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
        test_bank_accounts()
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


class PaymentSearchTest(TestCase):
    def setUp(self):
        test_users()
        test_categories()
        test_payment_schedules()
        test_bank_accounts()
        test_payments()

    def test_search_term_exists(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'search',
            'search_term': 'Payment 1',
            'start_date': '2015-06-07',
            'end_date': '2015-07-07',
        }
        response = c.post('/budget/calendar_view/', payload)
        # print response.content
        response_data = jsonpickle.decode(response.content)
        pc = [p for p in response_data['data'] if p['title'] == 'Payment 1']
        self.assertNotIn("exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual("2016-06-07", pc[0]['payment_date'])

    def test_search_term_does_not_exist(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'search',
            'search_term': 'Payment 12',
            'start_date': '2015-06-07',
            'end_date': '2015-07-07',
        }
        response = c.post('/budget/calendar_view/', payload)
        # print response.content
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("exception", response_data, 'Exception occurred: %s' % response_data)
        self.assertEqual("fail", response_data['result_success'],
                         'Incorrect result_success: %s' % response_data['result_success'])
        self.assertEqual('Cannot find "Payment 12"', response_data['result_message'],
                         'Incorrect message: %s' % response_data['result_message'])

    def test_search_term_exists_in_future(self):
        c = Client()
        self.assertTrue(c.login(username='john', password='johnpassword'))
        payload = {
            'action': 'search',
            'search_term': 'Annual Payment',
            'start_date': '2017-08-10',
            'end_date': '2017-08-10',
        }
        response = c.post('/budget/calendar_view/', payload)
        response_data = jsonpickle.decode(response.content)
        self.assertNotIn("exception", response_data, 'Exception occurred: %s' % response_data)
        p = [p for p in response_data['data'] if p['title'] == 'Annual Payment']
        self.assertEqual("2021-06-02", p[0]['payment_date'], p[0])
