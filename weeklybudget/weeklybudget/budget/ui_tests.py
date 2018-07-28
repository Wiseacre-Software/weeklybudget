from decimal import Decimal
from re import sub
from time import sleep

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.template.defaultfilters import date as _date
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec  # available since 2.26.0
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0

from .models import *

# python manage.py test budget.ui_tests

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
        active=True,
    )
    ba1.save()

    ba1a = BankAccount.objects.create(
        title='john credit account',
        current_balance=500,
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
    SubCategory.objects.create(
        name='subcat1',
        category=cat1,
        owner=user[0]
    )
    pt1a = PaymentType.objects.create(
        name='pt1a',
        sort_order='1',
        owner=user[0]
    )
    cat1a = Category.objects.create(
        name='cat1a',
        payment_type=pt1a,
        owner=user[0]
    )
    SubCategory.objects.create(
        name='subcat1a',
        category=cat1a,
        owner=user[0]
    )
    pt1b = PaymentType.objects.create(
        name='pt1b',
        sort_order='1',
        owner=user[0]
    )
    cat1b = Category.objects.create(
        name='cat1b',
        payment_type=pt1b,
        owner=user[0]
    )
    SubCategory.objects.create(
        name='subcat1b',
        category=cat1b,
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
    SubCategory.objects.create(
        name='subcat2',
        category=cat2,
        owner=user[1]
    )


def test_payment_schedules():
    PaymentScheduleFrequency.objects.create(name='User Specified', sort_order=6)
    PaymentScheduleFrequency.objects.create(name='Linked to Other Payment', sort_order=5)
    PaymentScheduleFrequency.objects.create(name='Annual', sort_order=4)
    PaymentScheduleFrequency.objects.create(name='Monthly', sort_order=3)
    PaymentScheduleFrequency.objects.create(name='Weekly', sort_order=2)
    PaymentScheduleFrequency.objects.create(name='Once Off', sort_order=1)


def test_payments():
    user = User.objects.all()[:2]
    ba1 = BankAccount.objects.filter(title__exact='john account').get()

    # Payment 1 - Weekly
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
        account=ba1,
        owner=user[0]
    )

    # Payment 2 - Monthly
    ps = PaymentSchedule.objects.create(
        next_date=datetime(2016, 5, 30),
        frequency=PaymentScheduleFrequency.objects.get(name__exact='Monthly'),
        monthly_dom=-2,
        monthly_frequency=1
    )
    Payment.objects.create(
        title='Payment 2',
        in_out='o',
        amount=200,
        payment_type=PaymentType.objects.get(name__exact='pt2'),
        category=Category.objects.get(name__exact='cat2'),
        subcategory=SubCategory.objects.get(name__exact='subcat2'),
        schedule=ps,
        account=ba1,
        owner=user[0]
    )

    # Payment 3 - Annual
    ps = PaymentSchedule.objects.create(
        next_date=datetime(2016, 6, 2),
        frequency=PaymentScheduleFrequency.objects.get(name__exact='Annual'),
        annual_dom=2,
        annual_moy=6,
        annual_frequency=5
    )
    Payment.objects.create(
        title='Payment 3',
        in_out='o',
        amount=115,
        payment_type=PaymentType.objects.get(name__exact='pt2'),
        category=Category.objects.get(name__exact='cat2'),
        subcategory=SubCategory.objects.get(name__exact='subcat2'),
        schedule=ps,
        account=ba1,
        owner=user[0]
    )

    # Credit payment
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
        owner=user[0],
        account=BankAccount.objects.get(title__exact='john credit account'),
    )

    # Virtual payment
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
        owner=user[0],
        account=BankAccount.objects.get(title__exact='john virtual account'),
    )


# endregion

# region Common Operations


def update_next_date(self, calendar_date_element_xpath, new_next_date, update_series):
    self.selenium.find_element_by_xpath(calendar_date_element_xpath).click()
    element = WebDriverWait(self.selenium, 10) \
        .until(ec.presence_of_element_located((By.NAME, "next_date")))
    element.clear()
    element.send_keys(new_next_date)
    if update_series:
        self.selenium.find_element_by_xpath("//label[@for = 'rdo__series_choice_series']").click()
    else:
        self.selenium.find_element_by_xpath("//label[@for = 'rdo__series_choice_this']").click()
    self.selenium.find_element_by_id("button__update_payment_date_save_changes").click()


def test_login(self):
    self.selenium.get('%s%s' % (self.live_server_url, '/budget/'))
    username_input = self.selenium.find_element_by_name("username")
    username_input.send_keys('john')
    password_input = self.selenium.find_element_by_name("password")
    password_input.send_keys('johnpassword')
    self.selenium.find_element_by_xpath('//input[@value="login"]').click()


def create_payment(self, payment_name, payment_date):
    elements = WebDriverWait(self.selenium, 1) \
        .until(ec.presence_of_all_elements_located((By.CLASS_NAME, 'button-insert-payment')))
    elements[0].click()

    element = self.selenium.find_element_by_xpath(
        "//table[@id = 'table__payment_detail']//input[@id = 'id_title']")
    element.send_keys(payment_name)
    element = self.selenium.find_element_by_xpath(
        "//table[@id = 'table__payment_detail']//input[@id = 'id_amount']")
    element.send_keys('500')

    select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_payment_type']/..", "id_payment_type",
                  "pt1")
    select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_category']/..", "id_category", "cat1")
    select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_subcategory']/..", "id_subcategory",
                  "subcat1")
    element = self.selenium.find_element_by_xpath(
        "//table[@id = 'table__payment_detail']//input[@id = 'id_next_date']")
    element.clear()
    element.send_keys(payment_date)
    select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_schedule_frequency']/..",
                  "id_schedule_frequency", "Monthly")
    element = self.selenium.find_element_by_xpath(
        "//table[@id = 'table__payment_detail']//button[@id = 'button__update_payment_save_changes']")
    element.click()


def create_payment_exception(self):
    payment_date_xpath = "//tr[@data-row_id='1|2016-06-07']/td[contains(@class,'calendar__payment_date')]"
    element = WebDriverWait(self.selenium, 1) \
        .until(ec.presence_of_element_located((By.XPATH, payment_date_xpath)))
    element.click()
    update_next_date(self, payment_date_xpath, _date(date(2016, 6, 8), 'SHORT_DATE_FORMAT'), False)


def select_chosen_by_id(self, select_element_parent_xpath, select_element_id, visible_text):
    chosen_dev_xpath = select_element_parent_xpath + "/div[@id = '" + select_element_id + "_chosen']"
    element = self.selenium.find_element_by_xpath(chosen_dev_xpath)
    element.click()
    element = self.selenium.find_element_by_xpath(chosen_dev_xpath + "//li[text() = '" + visible_text + "']")
    element.click()


def select_chosen_by_class(self, select_element_parent_xpath, visible_text):
    chosen_dev_xpath = select_element_parent_xpath + "/div[contains(@class, 'chosen-container')]"
    element = self.selenium.find_element_by_xpath(chosen_dev_xpath)
    element.click()
    element = self.selenium.find_element_by_xpath(chosen_dev_xpath + "//li[text() = '" + visible_text + "']")
    element.click()


def print_console_logs(driver):
    print '----------------------------------------'
    print 'Console logs:'
    print
    # console_logs = (entry for entry in driver.get_log('browser') if entry['source'] == 'console-api')
    # for entry in console_logs:
    for entry in driver.get_log('browser'):
        print entry['message']


def payment_search(driver, search_term):
    WebDriverWait(driver, 10).until(ec.presence_of_element_located(
        (By.ID, 'txt__calendar_search'))).send_keys(search_term)
    driver.find_element_by_id('btn__calendar_search_next').click()

# endregion

class TestLogin(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestLogin, cls).setUpClass()
        test_users()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(1)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(TestLogin, cls).tearDownClass()

    def test_login(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/budget/'))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys('john')
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys('johnpassword')
        self.selenium.find_element_by_xpath('//input[@value="login"]').click()
        self.assertEqual(self.live_server_url + '/budget/', self.selenium.current_url)


class TestCalendarView(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestCalendarView, cls).setUpClass()

    @classmethod
    def setUp(cls):
        d = DesiredCapabilities.CHROME
        d['loggingPrefs'] = {'browser': 'ALL'}
        cls.selenium = WebDriver(desired_capabilities=d)
        cls.selenium.implicitly_wait(1)
        test_users()
        test_categories()
        test_bank_accounts()
        test_payment_schedules()
        test_payments()
        test_login(cls)

    @classmethod
    def tearDown(cls):
        cls.selenium.quit()

    @classmethod
    def tearDownClass(cls):
        super(TestCalendarView, cls).tearDownClass()

    def test_initial_view(self):
        p = Payment.objects.filter(title__exact='Payment 2').get()
        p_row_id = str(p.id) + '|' + str(p.schedule.next_date)
        tr_xpath = '//tr[@data-row_id = "' + p_row_id + '"]'
        element = WebDriverWait(self.selenium, 1).until(
            ec.presence_of_element_located((By.XPATH, tr_xpath + '/td[contains(@class, "calendar__payment_date")]')))
        self.assertEqual('30/05/2016', element.text)
        self.assertEqual('$800.00', self.selenium.find_element_by_xpath(
            '(//div[contains(@class, "calendar__curr_balance")])').text)
        self.assertEqual('$800.00', self.selenium.find_element_by_xpath(
            '(//div[contains(@class, "calendar__curr_budget_balance")])').text)


class TestScheduleUpdate(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestScheduleUpdate, cls).setUpClass()

    @classmethod
    def setUp(cls):
        d = DesiredCapabilities.CHROME
        d['loggingPrefs'] = {'browser': 'ALL'}
        cls.selenium = WebDriver(desired_capabilities=d)
        cls.selenium.implicitly_wait(1)
        test_users()
        test_categories()
        test_bank_accounts()
        test_payment_schedules()
        test_payments()
        test_login(cls)

    @classmethod
    def tearDown(cls):
        cls.selenium.quit()

    @classmethod
    def tearDownClass(cls):
        super(TestScheduleUpdate, cls).tearDownClass()

    def test_ui_payment_update_initialise_weekly(self):
        payment_1_title = Payment.objects.get(title__exact='Payment 1').title
        payment_1_next_date = Payment.objects.get(title__exact='Payment 1').schedule.next_date.strftime('%d/%m/%Y')
        payment_1_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = '" + \
                                    payment_1_title + "']]" + "/td[contains(@class,'calendar__payment_date')]"
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_1_next_date_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(elements[0].text, payment_1_next_date)
        self.selenium.find_element_by_xpath(payment_1_next_date_xpath).click()
        element = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_element_located((By.NAME, "next_date")))
        self.selenium.find_element_by_xpath("//label[@for = 'rdo__series_choice_series']").click()
        self.assertEqual(element.get_property("value"), payment_1_next_date)
        self.assertEqual(Select(self.selenium.find_element_by_name('schedule_frequency'))
                         .first_selected_option.get_property('text'), 'Weekly')
        self.assertTrue(self.selenium.find_element_by_name('weekly_dow_tue').is_selected)
        self.assertEqual(self.selenium.find_element_by_id('input__weekly_dow_frequency').get_property('value'), '2')

    def test_ui_payment_update_initialise_monthly_dom(self):
        p = Payment.objects.get(title__exact='Payment 2')
        p.schedule.monthly_frequency = 3
        p.schedule.save()
        p.save()
        payment_next_date = p.schedule.next_date.strftime('%d/%m/%Y')
        payment_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = '" + \
                                  p.title + "']]" + "/td[contains(@class,'calendar__payment_date')]"
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_next_date_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(elements[0].text, payment_next_date)
        self.selenium.find_element_by_xpath(payment_next_date_xpath).click()
        element = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_element_located((By.NAME, "next_date")))
        self.selenium.find_element_by_xpath("//label[@for = 'rdo__series_choice_series']").click()
        self.assertEqual(element.get_property("value"), payment_next_date)
        self.assertEqual(self.selenium.find_element_by_id('id_schedule_frequency_chosen').text, 'Monthly')
        self.assertTrue(self.selenium.find_element_by_id('radio__monthly_style_dom').is_selected)
        self.assertEqual(self.selenium.find_element_by_id('select__monthly_dom_day_chosen').text, '2nd')
        self.assertEqual(self.selenium.find_element_by_id('select__monthly_dom_last_chosen').text, 'last')
        self.assertEqual(self.selenium.find_element_by_id('input__monthly_dom_frequency').get_property('value'), '3')

    def test_ui_payment_update_initialise_monthly_dow(self):
        p = Payment.objects.get(title__exact='Payment 2')
        p.schedule.monthly_dom = 0
        p.schedule.monthly_frequency = 3
        p.schedule.monthly_wom = 2
        p.schedule.monthly_dow = 4
        p.schedule.save()
        p.save()
        self.selenium.refresh()

        rr = rrule(MONTHLY, dtstart=p.schedule.next_date, count=1,
                   byweekday=weekdays[p.schedule.monthly_dow](p.schedule.monthly_wom),
                   interval=p.schedule.monthly_frequency)
        payment_next_date = rr[0].date().strftime('%d/%m/%Y')
        # p.schedule.next_date = rr[0].date()
        payment_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = '" + \
                                  p.title + "']]" + "/td[contains(@class,'calendar__payment_date')]"

        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_next_date_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(elements[0].text, payment_next_date)
        self.selenium.find_element_by_xpath(payment_next_date_xpath).click()
        sleep(1)
        element = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_element_located((By.NAME, "next_date")))
        self.selenium.find_element_by_xpath("//label[@for = 'rdo__series_choice_series']"
                                            "/span[contains(@class, 'ui-checkboxradio-icon')]").click()
        self.assertEqual(element.get_property("value"), payment_next_date)
        self.assertEqual(self.selenium.find_element_by_id('id_schedule_frequency_chosen').text, 'Monthly')
        self.assertTrue(self.selenium.find_element_by_id('radio__monthly_style_dow').is_selected)
        self.assertEqual(self.selenium.find_element_by_id('select__monthly_wom_nth_chosen').text, '2nd')
        self.assertEqual(self.selenium.find_element_by_id('select__monthly_wom_last_chosen').text, '')
        self.assertEqual(self.selenium.find_element_by_id('select__monthly_wom_day_chosen').text, 'Friday')
        self.assertEqual(self.selenium.find_element_by_id('input__monthly_wom_frequency').get_property('value'), '3')

    def test_ui_payment_update_initialise_annual(self):
        p = Payment.objects.get(title__exact='Payment 3')
        payment_next_date = p.schedule.next_date.strftime('%d/%m/%Y')
        payment_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = '" + \
                                  p.title + "']]" + "/td[contains(@class,'calendar__payment_date')]"

        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_next_date_xpath)))
        self.assertGreaterEqual(len(elements), 1)
        self.assertEqual(elements[0].text, payment_next_date)
        self.selenium.find_element_by_xpath(payment_next_date_xpath).click()
        element = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_element_located((By.NAME, "next_date")))
        self.selenium.find_element_by_xpath("//label[@for = 'rdo__series_choice_series']").click()
        self.assertEqual(element.get_property("value"), payment_next_date)
        self.assertEqual(self.selenium.find_element_by_id('id_schedule_frequency_chosen').text, 'Annual')
        self.assertEqual(self.selenium.find_element_by_id('id_annual_dom_chosen').text, '2nd')
        self.assertEqual(self.selenium.find_element_by_id('id_annual_moy_chosen').text, 'June')
        self.assertEqual(self.selenium.find_element_by_id('id_annual_frequency').get_property('value'), '5')

    def test_ui_set_new_first_payment_date(self):
        payment_1_title = Payment.objects.get(title__exact='Payment 1').title
        payment_1_next_date = Payment.objects.get(title__exact='Payment 1').schedule.next_date.strftime('%d/%m/%Y')
        payment_1_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = '" + \
                                    payment_1_title + "']]" + "/td[contains(@class,'calendar__payment_date')]"
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_1_next_date_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(elements[0].text, payment_1_next_date)
        update_next_date(self, payment_1_next_date_xpath, _date(date(2017, 5, 16), 'SHORT_DATE_FORMAT'), True)
        element = WebDriverWait(self.selenium, 10) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')

        elements = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_1_next_date_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(elements[0].text, _date(date(2017, 5, 16), 'SHORT_DATE_FORMAT'))

        # element = WebDriverWait(self.selenium, 100) \
        #     .until(EC.presence_of_element_located((By.NAME, 'lager')))

    def test_ui_update_weekly_schedule(self):
        payment_1_title = Payment.objects.get(title__exact='Payment 1').title
        payment_1_next_date = Payment.objects.get(title__exact='Payment 1').schedule.next_date.strftime('%d/%m/%Y')
        payment_1_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = '" + \
                                    payment_1_title + "']]/td[contains(@class,'calendar__payment_date')]"
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_1_next_date_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(elements[0].text, payment_1_next_date)
        self.selenium.find_element_by_xpath(payment_1_next_date_xpath).click()
        element = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_element_located((By.NAME, "next_date")))
        element.clear()
        element.send_keys('2/6/2016')
        self.selenium.find_element_by_xpath("//label[@for = 'rdo__series_choice_series']").click()
        sleep(1)

        WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'tr__payment_schedule__weekly')))
        self.assertTrue(self.selenium.find_element_by_name('weekly_dow_thu').is_selected)
        self.selenium.find_element_by_xpath('//label[@for = "id_weekly_dow_wed"]'
                                            '/span[contains(@class, "ui-checkboxradio-icon")]').click()
        element = self.selenium.find_element_by_id('input__weekly_dow_frequency')
        element.clear()
        element.send_keys('1')
        self.selenium.find_element_by_id("button__update_payment_date_save_changes").click()
        sleep(1)

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')

        elements = self.selenium.find_elements_by_xpath(payment_1_next_date_xpath)
        self.assertGreater(len(elements), 1)
        self.assertEqual(elements[0].text, _date(date(2016, 6, 2), 'SHORT_DATE_FORMAT'))
        self.assertEqual(elements[1].text, _date(date(2016, 6, 8), 'SHORT_DATE_FORMAT'))
        self.assertEqual(elements[2].text, _date(date(2016, 6, 9), 'SHORT_DATE_FORMAT'))
        self.assertEqual(elements[3].text, _date(date(2016, 6, 15), 'SHORT_DATE_FORMAT'))

    def test_ui_update_monthly_schedule_dom(self):
        payment_title = Payment.objects.get(title__exact='Payment 2').title
        payment_next_date = Payment.objects.get(title__exact='Payment 2').schedule.next_date.strftime('%d/%m/%Y')
        payment_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = '" + \
                                    payment_title + "']]" + "/td[contains(@class,'calendar__payment_date')]"
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_next_date_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(elements[0].text, payment_next_date)
        self.selenium.find_element_by_xpath(payment_next_date_xpath).click()
        element = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.NAME, "next_date")))
        element.clear()
        element.send_keys('1/6/2016')
        self.selenium.find_element_by_xpath("//label[@for = 'rdo__series_choice_series']").click()
        sleep(1)

        element = WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located(
            (By.XPATH, '//div[@id = "select__monthly_dom_day_chosen"]/a[@class = "chosen-single"]')))
        self.assertEqual('1st', element.text)
        element = self.selenium.find_element_by_id('input__monthly_dom_frequency')
        element.clear()
        element.send_keys('2')
        self.selenium.find_element_by_id("button__update_payment_date_save_changes").click()
        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')
        sleep(1)

        self.assertEqual(WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, payment_next_date_xpath))).text, _date(date(2016, 6, 1), 'SHORT_DATE_FORMAT'))

        payment_search(self.selenium, 'Payment 2')
        sleep(1)
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual(WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, "//td[contains(@class,'calendar__payment_date')][contains(@class,'highlight')]")))
                         .text, _date(date(2016, 8, 1), 'SHORT_DATE_FORMAT'))

    def test_ui_update_monthly_schedule_wom(self):
        payment_title = Payment.objects.get(title__exact='Payment 2').title
        payment_next_date = Payment.objects.get(title__exact='Payment 2').schedule.next_date.strftime('%d/%m/%Y')
        payment_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = '" + \
                                  payment_title + "']]" + "/td[contains(@class,'calendar__payment_date')]"
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_next_date_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(elements[0].text, payment_next_date)
        self.selenium.find_element_by_xpath(payment_next_date_xpath).click()
        element = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_element_located((By.NAME, "next_date")))
        element.clear()
        element.send_keys('1/6/2016')
        self.selenium.find_element_by_xpath("//label[@for = 'rdo__series_choice_series']").click()
        sleep(1)

        WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located(
            (By.XPATH, '//label[@for = "radio__monthly_style_dow"]/span[contains(@class, "ui-checkboxradio-icon")]')))\
            .click()
        select_chosen_by_id(self, '//select[@id = "select__monthly_wom_nth"]/..', 'select__monthly_wom_nth', '2nd')
        select_chosen_by_id(self, '//select[@id = "select__monthly_wom_last"]/..', 'select__monthly_wom_last', 'last')
        select_chosen_by_id(self, '//select[@id = "select__monthly_wom_day"]/..', 'select__monthly_wom_day', 'Monday')
        element = self.selenium.find_element_by_id('input__monthly_wom_frequency')
        element.clear()
        element.send_keys('2')

        self.selenium.find_element_by_id("button__update_payment_date_save_changes").click()
        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')
        sleep(1)

        payment_search(self.selenium, 'Payment 2')
        sleep(1)
        self.assertEqual(WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, "//td[contains(@class,'calendar__payment_date')][contains(@class,'highlight')]")))
                         .text, _date(date(2016, 6, 20), 'SHORT_DATE_FORMAT'))

        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual(WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, "//td[contains(@class,'calendar__payment_date')][contains(@class,'highlight')]")))
                         .text, _date(date(2016, 8, 22), 'SHORT_DATE_FORMAT'))

    def test_ui_update_annual_schedule(self):
        payment_title = Payment.objects.get(title__exact='Payment 3').title
        payment_next_date = Payment.objects.get(title__exact='Payment 3').schedule.next_date.strftime('%d/%m/%Y')
        payment_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = '" + \
                                  payment_title + "']]" + "/td[contains(@class,'calendar__payment_date')]"
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_next_date_xpath)))
        self.selenium.find_element_by_xpath(payment_next_date_xpath).click()
        element = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_element_located((By.NAME, "next_date")))
        element.clear()
        element.send_keys('2/7/2016')
        self.selenium.find_element_by_xpath("//label[@for = 'rdo__series_choice_series']").click()
        sleep(1)

        self.assertEqual('2nd', WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located(
            (By.XPATH, '//div[@id = "id_annual_dom_chosen"]/a[@class = "chosen-single"]'))).text)
        self.assertEqual('July', WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located(
            (By.XPATH, '//div[@id = "id_annual_moy_chosen"]/a[@class = "chosen-single"]'))).text)
        element = self.selenium.find_element_by_id('id_annual_frequency')
        element.clear()
        element.send_keys('2')

        self.selenium.find_element_by_id("button__update_payment_date_save_changes").click()
        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')
        sleep(1)

        payment_search(self.selenium, 'Payment 3')
        sleep(1)
        self.assertEqual(WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, "//td[contains(@class,'calendar__payment_date')][contains(@class,'highlight')]")))
                         .text, _date(date(2016, 7, 2), 'SHORT_DATE_FORMAT'))

        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual(WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, "//td[contains(@class,'calendar__payment_date')][contains(@class,'highlight')]")))
                         .text, _date(date(2018, 7, 2), 'SHORT_DATE_FORMAT'))

    def test_ui_update_monthly_schedule_dom_with_occurrence(self):
        payment_title = Payment.objects.get(title__exact='Payment 2').title
        payment_next_date = Payment.objects.get(title__exact='Payment 2').schedule.next_date.strftime('%d/%m/%Y')
        payment_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = '" + \
                                  payment_title + "']]" + "/td[contains(@class,'calendar__payment_date')]"
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_next_date_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(elements[0].text, payment_next_date)
        self.selenium.find_element_by_xpath(payment_next_date_xpath).click()
        element = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.NAME, "next_date")))
        element.clear()
        element.send_keys('1/6/2016')
        self.selenium.find_element_by_xpath("//label[@for = 'rdo__series_choice_series']").click()
        sleep(1)

        element = WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located(
            (By.XPATH, '//div[@id = "select__monthly_dom_day_chosen"]/a[@class = "chosen-single"]')))
        self.assertEqual('1st', element.text)
        element = self.selenium.find_element_by_id('input__monthly_dom_frequency')
        element.clear()
        element.send_keys('2')
        # Select occurrence
        self.selenium.find_element_by_xpath('//label[@for = "radio__until_occurrences"]'
                                            '/span[contains(@class, "ui-checkboxradio-icon")]').click()
        element = self.selenium.find_element_by_id('id_occurrences')
        element.send_keys('3')
        # Save changes
        self.selenium.find_element_by_id("button__update_payment_date_save_changes").click()
        sleep(1)
        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')
        sleep(1)

        self.assertEqual('01/06/2016', self.selenium.find_element_by_xpath(payment_next_date_xpath).text)
        payment_search(self.selenium, 'Payment 2')
        sleep(1)
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual('01/08/2016', WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, "//td[contains(@class,'calendar__payment_date')][contains(@class,'highlight')]"))).text)
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual('01/10/2016', WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, "//td[contains(@class,'calendar__payment_date')][contains(@class,'highlight')]"))).text)
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual(self.selenium.find_element_by_id('div__user_message').text, 'Error: No more occurrences found')

    def test_ui_update_monthly_schedule_wom_with_end_date(self):
        payment_title = Payment.objects.get(title__exact='Payment 2').title
        payment_next_date = Payment.objects.get(title__exact='Payment 2').schedule.next_date.strftime('%d/%m/%Y')
        payment_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = '" + \
                                  payment_title + "']]" + "/td[contains(@class,'calendar__payment_date')]"
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_next_date_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(elements[0].text, payment_next_date)
        self.selenium.find_element_by_xpath(payment_next_date_xpath).click()
        element = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_element_located((By.NAME, "next_date")))
        element.clear()
        element.send_keys('1/6/2016')
        self.selenium.find_element_by_xpath("//label[@for = 'rdo__series_choice_series']").click()
        sleep(1)

        WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located(
            (By.XPATH, '//label[@for = "radio__monthly_style_dow"]/span[contains(@class, "ui-checkboxradio-icon")]')))\
            .click()
        select_chosen_by_id(self, '//select[@id = "select__monthly_wom_nth"]/..', 'select__monthly_wom_nth', '2nd')
        select_chosen_by_id(self, '//select[@id = "select__monthly_wom_last"]/..', 'select__monthly_wom_last', 'last')
        select_chosen_by_id(self, '//select[@id = "select__monthly_wom_day"]/..', 'select__monthly_wom_day', 'Monday')
        element = self.selenium.find_element_by_id('input__monthly_wom_frequency')
        element.clear()
        element.send_keys('2')
        # Select end_date
        self.selenium.find_element_by_xpath('//label[@for = "radio__until_end_date"]'
                                            '/span[contains(@class, "ui-checkboxradio-icon")]').click()
        element = self.selenium.find_element_by_id('id_end_date')
        element.send_keys('23/08/2016')
        # Save changes
        self.selenium.find_element_by_id("button__update_payment_date_save_changes").click()
        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')
        sleep(1)

        payment_search(self.selenium, 'Payment 2')
        sleep(1)
        self.assertEqual('20/06/2016', WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, "//td[contains(@class,'calendar__payment_date')][contains(@class,'highlight')]"))).text)
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual('22/08/2016', WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, "//td[contains(@class,'calendar__payment_date')][contains(@class,'highlight')]"))).text)
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual('Error: No more occurrences found', self.selenium.find_element_by_id('div__user_message').text)

    def test_ui_update_schedule_end_date_before_next_date(self):
        payment_title = Payment.objects.get(title__exact='Payment 2').title
        payment_next_date = Payment.objects.get(title__exact='Payment 2').schedule.next_date.strftime('%d/%m/%Y')
        payment_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = '" + \
                                  payment_title + "']]" + "/td[contains(@class,'calendar__payment_date')]"
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_next_date_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(elements[0].text, payment_next_date)
        self.selenium.find_element_by_xpath(payment_next_date_xpath).click()
        self.selenium.find_element_by_xpath("//label[@for = 'rdo__series_choice_series']").click()
        sleep(1)

        # Select end_date
        self.selenium.find_element_by_xpath('//label[@for = "radio__until_end_date"]'
                                            '/span[contains(@class, "ui-checkboxradio-icon")]').click()
        element = self.selenium.find_element_by_id('id_end_date')
        element.send_keys('23/08/2015')
        # Save changes
        self.selenium.find_element_by_id("button__update_payment_date_save_changes").click()
        sleep(1)
        self.assertEqual('Error: Until date must be after Next Payment date',
                         self.selenium.find_element_by_id('div__user_message').text)

    def test_ui_update_linked__payment_schedule_with_month_offset(self):
        payment_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')]" \
                                  "[text() = 'Payment 1']]/td[contains(@class,'calendar__payment_date')]"
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_next_date_xpath)))
        self.selenium.find_element_by_xpath(payment_next_date_xpath).click()
        element = self.selenium.find_element_by_name("next_date")
        element.clear()
        element.send_keys('1/6/2016')
        self.selenium.find_element_by_xpath("//label[@for = 'rdo__series_choice_series']").click()
        sleep(1)

        select_chosen_by_class(self, "//select[@id = 'id_schedule_frequency']/..", "Linked to Other Payment")
        sleep(1)
        select_chosen_by_class(self, "//select[@id = 'id_linked_to']/..", "Payment 1")
        element = self.selenium.find_element_by_xpath("//input[@id = 'id_offset']")
        element.clear()
        element.send_keys('1')
        select_chosen_by_class(self, '//select[@id = "id_offset_type"]/..', 'Months')
        # Select end_date
        self.selenium.find_element_by_xpath('//label[@for = "radio__until_end_date"]'
                                            '/span[contains(@class, "ui-checkboxradio-icon")]').click()
        element = self.selenium.find_element_by_id('id_end_date')
        element.send_keys('23/08/2022')
        # Save changes
        self.selenium.find_element_by_id("button__update_payment_date_save_changes").click()
        sleep(1)
        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Error: Payment cannot be linked to itself')

        select_chosen_by_class(self, "//select[@id = 'id_linked_to']/..", "Payment 3")
        # Save changes
        self.selenium.find_element_by_id("button__update_payment_date_save_changes").click()
        sleep(1)
        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')

        #
        # payment_search(self.selenium, 'Payment 1')
        # sleep(1)
        # self.assertEqual('02/07/2016', WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
        #     (By.XPATH, "//td[contains(@class,'calendar__payment_date')][contains(@class,'highlight')]"))).text)
        # self.selenium.find_element_by_id('btn__calendar_search_next').click()
        # sleep(1)
        # self.assertEqual('02/07/2021', WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
        #     (By.XPATH, "//td[contains(@class,'calendar__payment_date')][contains(@class,'highlight')]"))).text)
        # self.selenium.find_element_by_id('btn__calendar_search_next').click()
        # sleep(1)
        # self.assertEqual('Error: No more occurrences found', self.selenium.find_element_by_id('div__user_message').text)

    def test_ui_create_payment_exception(self):
        payment_date_xpath = "//tr[@data-row_id='1|2016-06-07']/td[contains(@class,'calendar__payment_date')]"
        exception_payment_date_xpath = "//tr[td[contains(., 'Payment 1')]]/td[text() = '08/06/2016']"

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.XPATH, payment_date_xpath)))
        element.click()
        update_next_date(self, payment_date_xpath, _date(date(2016, 6, 8), 'SHORT_DATE_FORMAT'), False)

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')

        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, exception_payment_date_xpath)))
        self.assertEqual(1, len(elements))
        self.assertEqual(_date(date(2016, 6, 8), 'SHORT_DATE_FORMAT'), elements[0].text)

    # TODO Make one payment dependant on another (shared schedules?)


class TestPaymentSearch(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestPaymentSearch, cls).setUpClass()

    @classmethod
    def setUp(cls):
        d = DesiredCapabilities.CHROME
        d['loggingPrefs'] = {'browser': 'ALL'}
        cls.selenium = WebDriver(desired_capabilities=d)
        cls.selenium.implicitly_wait(1)
        test_users()
        test_categories()
        test_bank_accounts()
        test_payment_schedules()
        test_payments()
        test_login(cls)

    @classmethod
    def tearDown(cls):
        cls.selenium.quit()

    @classmethod
    def tearDownClass(cls):
        super(TestPaymentSearch, cls).tearDownClass()

    def test_ui_calendar_search_in_list(self):
        payment_title_xpath = "//tr[@data-payment_id]/td[contains(@class,'calendar__title')][text() = 'Payment 1']"

        search_box = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_element_located((By.ID, 'txt__calendar_search')))
        search_box.send_keys('Payment 1')
        find_next = self.selenium.find_element_by_id('btn__calendar_search_next')
        find_next.click()

        elements = WebDriverWait(self.selenium, 100) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_title_xpath)))
        self.assertGreaterEqual(len(elements), 1)
        self.assertIn('highlight', elements[0].get_attribute('class'))

    def test_ui_calendar_search_not_in_list(self):
        p = Payment.objects.get(title__exact='Payment 3')
        p.schedule.next_date = datetime(2018, 6, 2)
        p.schedule.save()
        p.save()
        self.selenium.refresh()

        payment_title_xpath = "//tr[@data-payment_id]/td[contains(@class,'calendar__title')][text() = 'Payment 3']"
        payment_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = 'Payment " \
                                  "3']]/td[contains(@class,'calendar__payment_date')] "

        search_box = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_element_located((By.ID, 'txt__calendar_search')))
        self.assertEqual(0, len(self.selenium.find_elements_by_xpath(payment_title_xpath)))
        search_box.send_keys('Payment 3')
        find_next = self.selenium.find_element_by_id('btn__calendar_search_next')
        find_next.click()

        elements = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_title_xpath)))
        self.assertGreaterEqual(len(elements), 1)
        self.assertIn('highlight', elements[0].get_attribute('class'))
        self.assertEqual(self.selenium.find_element_by_xpath(payment_next_date_xpath).text,
                         _date(date(2018, 6, 2), 'SHORT_DATE_FORMAT'))

    def test_ui_calendar_search_first_payment(self):
        payment_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = 'Payment " \
                                  "2']]/td[contains(@class,'calendar__payment_date')][text() = '" \
                                  + _date(date(2016, 5, 30), 'SHORT_DATE_FORMAT') + "']"

        search_box = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_element_located((By.ID, 'txt__calendar_search')))
        search_box.send_keys('Payment 2')
        find_next = self.selenium.find_element_by_id('btn__calendar_search_next')
        find_next.click()

        elements = WebDriverWait(self.selenium, 100) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_next_date_xpath)))
        self.assertGreaterEqual(len(elements), 1)
        self.assertEqual(elements[0].text, _date(date(2016, 5, 30), 'SHORT_DATE_FORMAT'))
        self.assertIn('highlight', elements[0].get_attribute('class'))

    def test_ui_search_new_payment(self):
        create_payment(self, 'New Payment', '15/05/2016')

        WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_all_elements_located((By.XPATH, "//td[text() = 'New Payment']")))

        search_box = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.ID, 'txt__calendar_search')))
        search_box.send_keys('New Payment')

        find_next = self.selenium.find_element_by_id('btn__calendar_search_next')
        find_next.click()

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.XPATH, "//td[text() = 'New Payment']")))
        self.assertIn('highlight', element.get_attribute('class'))

    def test_ui_calendar_search_second_match_in_list(self):
        payment_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')]" \
                                  "[text() = 'Virtual Payment 1']]/td[contains(@class,'calendar__payment_date')]" \
                                  "[text() = '" + _date(date(2016, 6, 15), 'SHORT_DATE_FORMAT') + "']"

        self.test_ui_calendar_search_in_list()
        sleep(1)
        find_next = self.selenium.find_element_by_id('btn__calendar_search_next')
        find_next.click()

        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_next_date_xpath)))
        self.assertGreaterEqual(len(elements), 1)
        self.assertEqual(self.selenium.find_element_by_xpath(payment_next_date_xpath).text,
                         _date(date(2016, 6, 15), 'SHORT_DATE_FORMAT'))
        self.assertIn('highlight', elements[0].get_attribute('class'))

    def test_ui_calendar_search_second_match_not_in_list(self):
        payment_next_date_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = 'Payment " \
                                  "3']]/td[contains(@class,'calendar__payment_date')][text() = '" \
                                  + _date(date(2022, 6, 2), 'SHORT_DATE_FORMAT') + "']"

        search_box = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_element_located((By.ID, 'txt__calendar_search')))
        search_box.send_keys('Payment 3')
        find_next = self.selenium.find_element_by_id('btn__calendar_search_next')
        find_next.click()
        sleep(1)
        find_next.click()

        elements = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_next_date_xpath)))
        self.assertGreaterEqual(len(elements), 1)
        self.assertIn('highlight', elements[0].get_attribute('class'))

    def test_ui_calendar_search_first_and_second_match_not_in_list(self):
        user = User.objects.all()[:2]

        ps = PaymentSchedule.objects.create(
            next_date=datetime(2017, 11, 2),
            frequency=PaymentScheduleFrequency.objects.get(name__exact='Annual'),
            annual_dom=2,
            annual_moy=11,
            annual_frequency=1
        )
        Payment.objects.create(
            title='New Payment 1',
            in_out='o',
            amount=115,
            payment_type=PaymentType.objects.get(name__exact='pt2'),
            category=Category.objects.get(name__exact='cat2'),
            subcategory=SubCategory.objects.get(name__exact='subcat2'),
            schedule=ps,
            account=BankAccount.objects.get(title__exact='john account'),
            owner=user[0]
        )

        ps = PaymentSchedule.objects.create(
            next_date=datetime(2018, 2, 2),
            frequency=PaymentScheduleFrequency.objects.get(name__exact='Annual'),
            annual_dom=2,
            annual_moy=2,
            annual_frequency=1
        )
        Payment.objects.create(
            title='New Payment 2',
            in_out='o',
            amount=120,
            payment_type=PaymentType.objects.get(name__exact='pt2'),
            category=Category.objects.get(name__exact='cat2'),
            subcategory=SubCategory.objects.get(name__exact='subcat2'),
            schedule=ps,
            account=BankAccount.objects.get(title__exact='john account'),
            owner=user[0]
        )
        self.selenium.refresh()

        sleep(5)
        new_payment_1_xpath = "//tr[td[text() = 'New Payment 1']]/td[text() = '02/11/2017']"
        new_payment_2_xpath = "//tr[td[text() = 'New Payment 2']]/td[text() = '02/02/2018']"

        search_box = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_element_located((By.ID, 'txt__calendar_search')))
        search_box.send_keys('New Payment')
        find_next = self.selenium.find_element_by_id('btn__calendar_search_next')
        find_next.click()

        elements = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_all_elements_located((By.XPATH, new_payment_1_xpath)))
        self.assertGreaterEqual(len(elements), 1)
        self.assertIn('highlight', elements[0].get_attribute('class'))

        find_next.click()
        elements = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_all_elements_located((By.XPATH, new_payment_2_xpath)))
        self.assertGreaterEqual(len(elements), 1)
        self.assertIn('highlight', elements[0].get_attribute('class'))

    def test_ui_calendar_search_previous(self):
        payment_title_xpath = "//tr[@data-row_id='1|2016-06-07']/td[contains(@class,'calendar__title')]"

        payment_search(self.selenium, 'Payment 1')
        sleep(1)
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)

        find_prev = self.selenium.find_element_by_id('btn__calendar_search_prev')
        find_prev.click()

        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_title_xpath)))
        self.assertEqual(len(elements), 1)
        self.assertIn('highlight', elements[0].get_attribute('class'))

    def test_ui_calendar_search_return_key(self):
        payment_title_xpath = "//tr[@data-payment_id]/td[contains(@class,'calendar__title')][text() = 'Payment 1']"

        search_box = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.ID, 'txt__calendar_search')))
        search_box.send_keys('Payment 1' + Keys.RETURN)

        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_title_xpath)))
        self.assertGreaterEqual(len(elements), 1)
        self.assertIn('highlight', elements[0].get_attribute('class'))

    # TODO Jump to highlighted row
    # TODO Clear search
    # TODO Wildcard searching


class TestPaymentUpdate(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestPaymentUpdate, cls).setUpClass()

    @classmethod
    def setUp(cls):
        d = DesiredCapabilities.CHROME
        d['loggingPrefs'] = {'browser': 'ALL'}
        cls.selenium = WebDriver(desired_capabilities=d)
        cls.selenium.implicitly_wait(1)
        test_users()
        test_categories()
        test_bank_accounts()
        test_payment_schedules()
        test_payments()
        test_login(cls)

    @classmethod
    def tearDown(cls):
        cls.selenium.quit()

    @classmethod
    def tearDownClass(cls):
        super(TestPaymentUpdate, cls).tearDownClass()

    def test_ui_delete_payment(self):
        payment_delete_xpath = "//tr[@data-row_id='1|2016-06-07']//button[contains(@class,'button__delete_payment')]"
        delete_dialog_ok_xpath = \
            "//div[contains(@class,'ui-dialog-buttonset')]/button[contains(@class,'ui-button')][text() = 'OK']"
        payment_1_xpath = "//tr[@data-payment_id='1']"

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.XPATH, payment_delete_xpath)))
        element.click()
        element = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.XPATH, delete_dialog_ok_xpath)))
        self.assertTrue(element.is_displayed())
        element.click()

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment deleted!')

        self.assertEqual(0, len(self.selenium.find_elements_by_xpath(payment_1_xpath)))

        # Ensure payment doesn't show in autocomplete search terms
        self.assertNotIn('Payment 1', self.selenium.execute_script('return calendar_search_terms;'))

    def test_ui_delete_payment_exception_does_not_delete_series(self):
        payment_delete_xpath = "//tr[td[text() = '08/06/2016']]//button[contains(@class,'button__delete_payment')]"
        delete_dialog_ok_xpath = \
            "//div[contains(@class,'ui-dialog-buttonset')]/button[contains(@class,'ui-button')][text() = 'OK']"
        payment_1_xpath = "//tr[@data-payment_id='1']"
        user_message_xpath = "//div[@id='div__user_message']//*[text() = 'Payment deleted!']"

        create_payment_exception(self)
        element = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.XPATH, payment_delete_xpath)))
        element.click()
        sleep(1)
        element = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.XPATH, delete_dialog_ok_xpath)))
        self.assertTrue(element.is_displayed())
        element.click()

        WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.XPATH, user_message_xpath)))
        self.assertGreater(len(self.selenium.find_elements_by_xpath(payment_1_xpath)), 0)

    def test_ui_create_weekly_payment(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.CLASS_NAME, 'button-insert-payment'))).click()

        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_title']") \
            .send_keys('New Payment')
        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_amount']") \
            .send_keys('500')

        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_payment_type']/..",
                            "id_payment_type", "pt1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_category']/..",
                            "id_category",
                            "cat1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_subcategory']/..",
                            "id_subcategory", "subcat1")
        element = self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//input[@id = 'id_next_date']")
        element.clear()
        element.send_keys('15/05/2016')
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_schedule_frequency']/..",
                            "id_schedule_frequency", "Weekly")
        self.selenium.find_element_by_xpath('//label[@for = "id_weekly_dow_fri"]'
                                            '/span[contains(@class, "ui-checkboxradio-icon")]').click()
        self.selenium.find_element_by_xpath('//label[@for = "id_weekly_dow_sun"]'
                                            '/span[contains(@class, "ui-checkboxradio-icon")]').click()
        element = self.selenium.find_element_by_id('input__weekly_dow_frequency')
        element.clear()
        element.send_keys('3')
        self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//button[@id = 'button__update_payment_save_changes']").click()

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')
        payment_search(self.selenium, 'New Payment')
        sleep(1)
        self.assertEqual(self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text
            , _date(date(2016, 5, 20), 'SHORT_DATE_FORMAT'))
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        self.assertEqual(self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text
            , _date(date(2016, 6, 10), 'SHORT_DATE_FORMAT'))

        # Ensure payment in autocomplete search terms
        self.assertIn('New Payment', self.selenium.execute_script('return calendar_search_terms;'))

    def test_ui_create_monthly_dom_payment(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.CLASS_NAME, 'button-insert-payment'))).click()

        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_title']")\
            .send_keys('New Payment')
        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_amount']")\
            .send_keys('500')

        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_payment_type']/..",
                      "id_payment_type", "pt1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_category']/..", "id_category",
                      "cat1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_subcategory']/..",
                      "id_subcategory", "subcat1")
        element = self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//input[@id = 'id_next_date']")
        element.clear()
        element.send_keys('15/05/2016')
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_schedule_frequency']/..",
                      "id_schedule_frequency", "Monthly")
        element = WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located(
            (By.XPATH, '//div[@id = "select__monthly_dom_day_chosen"]/a[@class = "chosen-single"]')))
        select_chosen_by_class(self, '//select[@id = "select__monthly_dom_day"]/..', "1st")
        element = self.selenium.find_element_by_id('input__monthly_dom_frequency')
        element.clear()
        element.send_keys('2')
        self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//button[@id = 'button__update_payment_save_changes']").click()

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')

        payment_search(self.selenium, 'New Payment')
        sleep(1)
        self.assertEqual(self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text
                         , _date(date(2016, 6, 1), 'SHORT_DATE_FORMAT'))
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        self.assertEqual(self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text
                         , _date(date(2016, 8, 1), 'SHORT_DATE_FORMAT'))

        # Ensure payment in autocomplete search terms
        self.assertIn('New Payment', self.selenium.execute_script('return calendar_search_terms;'))

    def test_ui_create_monthly_dow_payment(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.CLASS_NAME, 'button-insert-payment'))).click()

        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_title']") \
            .send_keys('New Payment')
        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_amount']") \
            .send_keys('500')

        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_payment_type']/..",
                            "id_payment_type", "pt1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_category']/..",
                            "id_category",
                            "cat1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_subcategory']/..",
                            "id_subcategory", "subcat1")
        element = self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//input[@id = 'id_next_date']")
        element.clear()
        element.send_keys('15/05/2016')
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_schedule_frequency']/..",
                            "id_schedule_frequency", "Monthly")
        WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located(
            (By.XPATH, '//label[@for = "radio__monthly_style_dow"]/span[contains(@class, "ui-checkboxradio-icon")]'))) \
            .click()
        select_chosen_by_id(self, '//select[@id = "select__monthly_wom_nth"]/..', 'select__monthly_wom_nth', '1st')
        select_chosen_by_id(self, '//select[@id = "select__monthly_wom_last"]/..', 'select__monthly_wom_last', 'last')
        select_chosen_by_id(self, '//select[@id = "select__monthly_wom_day"]/..', 'select__monthly_wom_day', 'Saturday')
        element = self.selenium.find_element_by_id('input__monthly_wom_frequency')
        element.clear()
        element.send_keys('3')
        self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//button[@id = 'button__update_payment_save_changes']").click()

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')

        payment_search(self.selenium, 'New Payment')
        sleep(1)
        self.assertEqual(self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text
                         , _date(date(2016, 5, 28), 'SHORT_DATE_FORMAT'))
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        self.assertEqual(self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text
                         , _date(date(2016, 8, 27), 'SHORT_DATE_FORMAT'))

        # Ensure payment in autocomplete search terms
        self.assertIn('New Payment', self.selenium.execute_script('return calendar_search_terms;'))

    def test_ui_create_annual_payment(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.CLASS_NAME, 'button-insert-payment'))).click()

        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_title']") \
            .send_keys('New Payment')
        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_amount']") \
            .send_keys('500')

        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_payment_type']/..",
                            "id_payment_type", "pt1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_category']/..",
                            "id_category",
                            "cat1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_subcategory']/..",
                            "id_subcategory", "subcat1")
        element = self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//input[@id = 'id_next_date']")
        element.clear()
        element.send_keys('15/05/2016')
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_schedule_frequency']/..",
                            "id_schedule_frequency", "Annual")
        WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located(
            (By.XPATH, '//div[@id = "id_annual_dom_chosen"]/a[@class = "chosen-single"]')))
        select_chosen_by_id(self, '//select[@id = "id_annual_dom"]/..', 'id_annual_dom', '14th')
        select_chosen_by_id(self, '//select[@id = "id_annual_moy"]/..', 'id_annual_moy', 'May')
        element = self.selenium.find_element_by_id('id_annual_frequency')
        element.clear()
        element.send_keys('2')
        self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//button[@id = 'button__update_payment_save_changes']").click()

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')

        payment_search(self.selenium, 'New Payment')
        sleep(1)
        self.assertEqual(self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text
                         , _date(date(2017, 5, 14), 'SHORT_DATE_FORMAT'))
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        self.assertEqual(self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text
                         , _date(date(2019, 5, 14), 'SHORT_DATE_FORMAT'))

        # Ensure payment in autocomplete search terms
        self.assertIn('New Payment', self.selenium.execute_script('return calendar_search_terms;'))

    def test_ui_create_payment_from_search(self):
        search_box = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.ID, 'txt__calendar_search')))
        search_box.send_keys('New Payment')
        find_new = self.selenium.find_element_by_id('btn__calendar_new_payment_from_search')
        find_new.click()

        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, "//table[@id = 'table__payment_detail']//input[@id = 'id_title']")))
        self.assertEqual(element.get_property('value'), 'New Payment')

    def test_ui_create_weekly_payment_with_occurrence(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.CLASS_NAME, 'button-insert-payment'))).click()

        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_title']") \
            .send_keys('New Payment')
        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_amount']") \
            .send_keys('500')

        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_payment_type']/..",
                            "id_payment_type", "pt1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_category']/..",
                            "id_category",
                            "cat1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_subcategory']/..",
                            "id_subcategory", "subcat1")
        element = self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//input[@id = 'id_next_date']")
        element.clear()
        element.send_keys('15/05/2016')
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_schedule_frequency']/..",
                            "id_schedule_frequency", "Weekly")
        self.selenium.find_element_by_xpath('//label[@for = "id_weekly_dow_fri"]'
                                            '/span[contains(@class, "ui-checkboxradio-icon")]').click()
        self.selenium.find_element_by_xpath('//label[@for = "id_weekly_dow_sun"]'
                                            '/span[contains(@class, "ui-checkboxradio-icon")]').click()
        element = self.selenium.find_element_by_id('input__weekly_dow_frequency')
        element.clear()
        element.send_keys('3')
        # Select occurrence
        self.selenium.find_element_by_xpath('//label[@for = "radio__until_occurrences"]'
                                            '/span[contains(@class, "ui-checkboxradio-icon")]').click()
        element = self.selenium.find_element_by_id('id_occurrences')
        element.clear()
        element.send_keys('3')
        # Save changes
        self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//button[@id = 'button__update_payment_save_changes']").click()

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')
        payment_search(self.selenium, 'New Payment')
        sleep(1)
        self.assertEqual('20/05/2016', self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text)
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual('10/06/2016', self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text)
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual('01/07/2016', self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text)
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual(self.selenium.find_element_by_id('div__user_message').text, 'Error: No more occurrences found')

    def test_ui_create_annual_payment_with_end_date(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.CLASS_NAME, 'button-insert-payment'))).click()

        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_title']") \
            .send_keys('New Payment')
        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_amount']") \
            .send_keys('500')

        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_payment_type']/..",
                            "id_payment_type", "pt1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_category']/..",
                            "id_category",
                            "cat1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_subcategory']/..",
                            "id_subcategory", "subcat1")
        element = self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//input[@id = 'id_next_date']")
        element.clear()
        element.send_keys('15/05/2016')
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_schedule_frequency']/..",
                            "id_schedule_frequency", "Annual")
        WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located(
            (By.XPATH, '//div[@id = "id_annual_dom_chosen"]/a[@class = "chosen-single"]')))
        select_chosen_by_id(self, '//select[@id = "id_annual_dom"]/..', 'id_annual_dom', '14th')
        select_chosen_by_id(self, '//select[@id = "id_annual_moy"]/..', 'id_annual_moy', 'May')
        element = self.selenium.find_element_by_id('id_annual_frequency')
        element.clear()
        element.send_keys('2')
        # Select end_date
        self.selenium.find_element_by_xpath('//label[@for = "radio__until_end_date"]'
                                            '/span[contains(@class, "ui-checkboxradio-icon")]').click()
        element = self.selenium.find_element_by_id('id_end_date')
        element.send_keys('20/05/2017')
        # Save changes
        self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//button[@id = 'button__update_payment_save_changes']").click()

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')

        payment_search(self.selenium, 'New Payment')
        sleep(1)
        self.assertEqual('14/05/2017', self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text)
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual(self.selenium.find_element_by_id('div__user_message').text, 'Error: No more occurrences found')

    def test_ui_create_payment_linked_with_no_offset(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.CLASS_NAME, 'button-insert-payment'))).click()
        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_title']") \
            .send_keys('New Payment')
        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_amount']") \
            .send_keys('500')
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_payment_type']/..",
                            "id_payment_type", "pt1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_category']/..",
                            "id_category",
                            "cat1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_subcategory']/..",
                            "id_subcategory", "subcat1")
        element = self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//input[@id = 'id_next_date']")
        element.clear()
        element.send_keys('15/05/2016')
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_schedule_frequency']/..",
                            "id_schedule_frequency", "Linked to Other Payment")
        WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located(
            (By.XPATH, '//div[@id = "id_linked_to_chosen"]/a[@class = "chosen-single"]')))
        select_chosen_by_class(self, '//select[@id = "id_linked_to"]/..', 'Payment 1')
        # Save changes
        self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//button[@id = 'button__update_payment_save_changes']").click()
        sleep(1)

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')

        payment_search(self.selenium, 'New Payment')
        sleep(1)
        self.assertEqual('07/06/2016', self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text)
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual('21/06/2016', self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text)

    def test_ui_create_payment_linked_with_days_offset(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.CLASS_NAME, 'button-insert-payment'))).click()
        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_title']") \
            .send_keys('New Payment')
        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_amount']") \
            .send_keys('500')
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_payment_type']/..",
                            "id_payment_type", "pt1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_category']/..",
                            "id_category",
                            "cat1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_subcategory']/..",
                            "id_subcategory", "subcat1")
        element = self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//input[@id = 'id_next_date']")
        element.clear()
        element.send_keys('15/05/2016')
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_schedule_frequency']/..",
                            "id_schedule_frequency", "Linked to Other Payment")
        WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located(
            (By.XPATH, '//div[@id = "id_linked_to_chosen"]/a[@class = "chosen-single"]')))
        select_chosen_by_class(self, '//select[@id = "id_linked_to"]/..', 'Payment 2')
        # Select offset
        element = self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//input[@id = 'id_offset']")
        element.clear()
        element.send_keys('-1')
        select_chosen_by_class(self, '//select[@id = "id_offset_type"]/..', 'Days')
        # Select occurrence
        self.selenium.find_element_by_xpath('//label[@for = "radio__until_occurrences"]'
                                            '/span[contains(@class, "ui-checkboxradio-icon")]').click()
        element = self.selenium.find_element_by_id('id_occurrences')
        element.clear()
        element.send_keys('2')
        # Save changes
        self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//button[@id = 'button__update_payment_save_changes']").click()
        sleep(1)

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')

        payment_search(self.selenium, 'New Payment')
        sleep(1)
        self.assertEqual('29/05/2016', self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text)
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual('28/06/2016', self.selenium.find_element_by_xpath(
            '//td[contains(@class,"calendar__payment_date")][contains(@class,"highlight")]').text)
        self.selenium.find_element_by_id('btn__calendar_search_next').click()
        sleep(1)
        self.assertEqual(self.selenium.find_element_by_id('div__user_message').text, 'Error: No more occurrences found')

    def test_ui_create_schedule_end_date_before_next_date(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.CLASS_NAME, 'button-insert-payment'))).click()

        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_title']") \
            .send_keys('New Payment')
        self.selenium.find_element_by_xpath("//table[@id = 'table__payment_detail']//input[@id = 'id_amount']") \
            .send_keys('500')

        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_payment_type']/..",
                            "id_payment_type", "pt1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_category']/..",
                            "id_category",
                            "cat1")
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_subcategory']/..",
                            "id_subcategory", "subcat1")
        element = self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//input[@id = 'id_next_date']")
        element.clear()
        element.send_keys('15/05/2016')
        select_chosen_by_id(self, "//table[@id = 'table__payment_detail']//select[@id = 'id_schedule_frequency']/..",
                            "id_schedule_frequency", "Annual")
        WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located(
            (By.XPATH, '//div[@id = "id_annual_dom_chosen"]/a[@class = "chosen-single"]')))
        select_chosen_by_id(self, '//select[@id = "id_annual_dom"]/..', 'id_annual_dom', '14th')
        select_chosen_by_id(self, '//select[@id = "id_annual_moy"]/..', 'id_annual_moy', 'May')
        element = self.selenium.find_element_by_id('id_annual_frequency')
        element.send_keys('2')
        # Select end_date
        self.selenium.find_element_by_xpath('//label[@for = "radio__until_end_date"]'
                                            '/span[contains(@class, "ui-checkboxradio-icon")]').click()
        element = self.selenium.find_element_by_id('id_end_date')
        element.send_keys('20/05/2010')
        # Save changes
        self.selenium.find_element_by_xpath(
            "//table[@id = 'table__payment_detail']//button[@id = 'button__update_payment_save_changes']").click()

        sleep(1)
        self.assertEqual('Error: Until date must be after Next Payment date',
                         self.selenium.find_element_by_id('div__user_message').text)

    def test_ui_update_bank_account(self):
        p = Payment.objects.get(title="Payment 1")
        row_id = '%d|%s' % (p.id, str(p.schedule.next_date))
        account_xpath = '//tr[@data-row_id = "%s"]' % row_id

        # Update series
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
            account_xpath + '//td[contains(@class,"calendar__account")]'))).click()
        sleep(1)
        select_chosen_by_class(self, account_xpath + '//td[contains(@class,"calendar__account")]//select/..',
                               "john credit account")
        sleep(1)
        self.selenium.find_element_by_xpath(account_xpath +
            '//button[contains(@class, "button-update-account-save-series")]').click()
        sleep(1)

        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, account_xpath + '/td[contains(@class,"calendar__account")]')))
        self.assertEqual('john credit account', element.text)

        # Update this
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
            account_xpath + '//td[contains(@class,"calendar__account")]'))).click()
        sleep(1)
        select_chosen_by_class(self, account_xpath + '//td[contains(@class,"calendar__account")]//select/..',
                               "john virtual account")
        sleep(1)
        self.selenium.find_element_by_xpath(account_xpath +
                                            '//button[contains(@class, "button-update-account-save-single")]').click()
        sleep(1)

        pe = PaymentScheduleExclusion.objects.get(main_payment=p)
        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, '//tr[@data-payment_id = "' + str(pe.exclusion_payment.id) + '"]/td[contains(@class,"calendar__account")]')))
        self.assertEqual('john virtual account', element.text)
        self.assertEqual('john credit account', self.selenium.find_element_by_xpath('//tr[@data-payment_id = "'
            + str(p.id) + '"]/td[contains(@class,"calendar__account")]').text)

    def test_ui_update_payment_title(self):
        p = Payment.objects.get(title="Payment 1")
        row_id = '%d|%s' % (p.id, str(p.schedule.next_date))
        row_xpath = '//tr[@data-row_id = "%s"]' % row_id

        # Update series
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, row_xpath + '//td[contains(@class,"calendar__title")]'))).click()
        sleep(1)
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, row_xpath + '//td[contains(@class,"calendar__title")]//input')))\
            .send_keys('Payment 1 - updated')
        self.selenium.find_element_by_xpath(
            row_xpath + '//button[contains(@class, "button-update-detail-save-series")]').click()
        sleep(1)

        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, row_xpath + '/td[contains(@class,"calendar__title")]')))
        self.assertEqual('Payment 1 - updated', element.text)
        self.assertIn('Payment 1 - updated', self.selenium.execute_script('return calendar_search_terms;'))

        # Update this instance (not the whole series)
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, row_xpath + '//td[contains(@class,"calendar__title")]'))).click()
        sleep(1)
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, row_xpath + '//td[contains(@class,"calendar__title")]//input'))) \
            .send_keys('Payment 1 - updated again')
        self.selenium.find_element_by_xpath(
            row_xpath + '//button[contains(@class, "button-update-detail-save-single")]').click()
        sleep(1)

        pe = PaymentScheduleExclusion.objects.get(main_payment=p)
        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, '//tr[@data-payment_id = "' + str(
                pe.exclusion_payment.id) + '"]/td[contains(@class,"calendar__title")]')))
        self.assertEqual('Payment 1 - updated again', element.text)
        self.assertEqual('Payment 1 - updated', self.selenium.find_element_by_xpath(
            '//tr[@data-payment_id = "' + str(p.id) + '"]/td[contains(@class,"calendar__title")]').text)
        self.assertIn('Payment 1 - updated again', self.selenium.execute_script('return calendar_search_terms;'))

    def test_ui_update_outgoing(self):
        p = Payment.objects.get(title="Payment 2")
        row_id = '%d|%s' % (p.id, str(p.schedule.next_date))
        row_xpath = '//tr[@data-row_id = "%s"]' % row_id

        # Update series
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, row_xpath + '//td[contains(@class,"calendar__outgoing")]'))).click()
        sleep(1)
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, row_xpath + '//td[contains(@class,"calendar__outgoing")]//input'))) \
            .send_keys('100')
        self.selenium.find_element_by_xpath(
            row_xpath + '//button[contains(@class, "button-update-detail-save-series")]').click()
        sleep(1)

        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, row_xpath + '/td[contains(@class,"calendar__outgoing")]')))
        self.assertEqual('$100.00', element.text)

        # Update this
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, row_xpath + '//td[contains(@class,"calendar__outgoing")]'))).click()
        sleep(1)
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, row_xpath + '//td[contains(@class,"calendar__outgoing")]//input'))) \
            .send_keys('300')
        self.selenium.find_element_by_xpath(
            row_xpath + '//button[contains(@class, "button-update-detail-save-single")]').click()
        sleep(1)

        pe = PaymentScheduleExclusion.objects.get(main_payment=p)
        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, '//tr[@data-payment_id = "' + str(
                pe.exclusion_payment.id) + '"]/td[contains(@class,"calendar__outgoing")]')))
        self.assertEqual('$300.00', element.text)
        self.assertEqual('$100.00', self.selenium.find_element_by_xpath(
            '//tr[@data-payment_id = "' + str(p.id) + '"]/td[contains(@class,"calendar__outgoing")]').text)

    def test_ui_update_incoming_amount_series(self):
        payment_1_title = Payment.objects.get(title__exact='Payment 1').title
        payment_1_amount = Payment.objects.get(title__exact='Payment 1').amount
        payment_1_amount_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = 'Payment " \
                                 "1']]/td[contains(@class,'calendar__incoming')][not(input)] "
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_1_amount_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(Decimal(sub(r'[^\d.]', '', elements[0].text)), payment_1_amount)

        elements[0].click()
        element = WebDriverWait(self.selenium, 10).until(ec.presence_of_element_located(
            (By.XPATH, "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = '" +
             payment_1_title + "']]" + "/td[contains(@class,'calendar__incoming')]/input")))
        self.assertEqual(Decimal(sub(r'[^\d.]', '', element.get_property("value"))), payment_1_amount)
        element.send_keys('2000')

        elements = self.selenium.find_elements_by_class_name('button-update-detail-save-series')
        self.assertEqual(len(elements), 1)
        elements[0].click()

        element = WebDriverWait(self.selenium, 10) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')

        WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_all_elements_located((By.XPATH, "//tr[@data-row_id='1|2016-06-07']/td[contains("
                                                                  "@class,'calendar__incoming')][not(input)] ")))
        elements = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_1_amount_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(Decimal(sub(r'[^\d.]', '', elements[0].text)), 2000.0)
        self.assertEqual(Decimal(sub(r'[^\d.]', '', elements[1].text)), 2000.0)

    def test_ui_update_incoming_amount_single(self):
        payment_1_amount = Payment.objects.get(title__exact='Payment 1').amount
        payment_1_date = Payment.objects.get(title__exact='Payment 1').schedule.next_date.strftime('%d/%m/%Y')
        payment_1_amount_xpath = "//tr[@data-payment_id][td[contains(@class,'calendar__title')]" \
                                 "[text() = 'Payment 1']]/td[contains(@class,'calendar__incoming')]"
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_1_amount_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(Decimal(sub(r'[^\d.]', '', elements[0].text)), payment_1_amount)

        elements[0].click()
        element = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located(
            (By.XPATH, "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = 'Payment 1']]"
                       "/td[contains(@class,'calendar__incoming')]/input")))
        self.assertEqual(Decimal(sub(r'[^\d.]', '', element.get_property("value"))), payment_1_amount)
        element.send_keys('2000')

        elements = self.selenium.find_elements_by_class_name('button-update-detail-save-single')
        self.assertEqual(len(elements), 1)
        elements[0].click()
        sleep(1)

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')

        self.assertEqual(self.selenium.find_element_by_xpath(
            "//tr[@data-payment_id][td[contains(@class,'calendar__title')]"
            "[text() = 'Payment 1 - " + payment_1_date + "']]/td[contains(@class,'calendar__incoming')]").text,
                         "$2,000.00")
        self.assertEqual(self.selenium.find_element_by_xpath(
            "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = 'Payment 1']]"
            "/td[contains(@class,'calendar__incoming')]").text, "$1,000.00")

    def test_ui_update_second_incoming_amount_single(self):
        payment_1_title = Payment.objects.get(title__exact='Payment 1').title
        payment_1_amount = Payment.objects.get(title__exact='Payment 1').amount
        payment_1_amount_xpath = "//tr[td[contains(@class,'calendar__title')]" \
                                 "[text() = 'Payment 1']]/td[contains(@class,'calendar__incoming')]"
        payment_1_exception_amount_xpath = "//tr[td[contains(@class,'calendar__title')]" \
                                 "[contains(text(), 'Payment 1 - ')]]/td[contains(@class,'calendar__incoming')]"
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.XPATH, payment_1_amount_xpath)))
        self.assertGreater(len(elements), 1)
        self.assertEqual(Decimal(sub(r'[^\d.]', '', elements[0].text)), payment_1_amount)

        elements[1].click()
        element = WebDriverWait(self.selenium, 10) \
            .until(ec.presence_of_element_located(
            (By.XPATH, "//tr[@data-payment_id][td[contains(@class,'calendar__title')][text() = '" + \
             payment_1_title + "']]" + "/td[contains(@class,'calendar__incoming')]/input")))
        self.assertEqual(Decimal(sub(r'[^\d.]', '', element.get_property("value"))), payment_1_amount)
        element.send_keys('2000')

        elements = self.selenium.find_elements_by_class_name('button-update-detail-save-single')
        self.assertEqual(len(elements), 1)
        elements[0].click()
        sleep(1)

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Payment Saved!')

        elements = self.selenium.find_elements_by_xpath(payment_1_amount_xpath)
        self.assertGreater(len(elements), 1)
        self.assertEqual(elements[0].text, '$1,000.00')
        self.assertEqual(elements[1].text, '$1,000.00')
        self.assertEqual(self.selenium.find_element_by_xpath(payment_1_exception_amount_xpath).text, '$2,000.00')

    def test_ui_only_edit_one_field_at_a_time(self):
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, '//td[contains(@class, "calendar__payment_date")]'))).click()
        self.assertEqual(1, len(WebDriverWait(self.selenium, 1).until(ec.visibility_of_all_elements_located(
            (By.ID, 'id_next_date')))))

        self.selenium.find_element_by_xpath('//div[contains(@class, "calendar__payment_classification")]').click()
        sleep(1)
        self.assertEqual(0, len(self.selenium.find_elements_by_class_name('tr__calendar_inline_edit_row')))

        self.selenium.find_element_by_xpath('//td[contains(@class, "calendar__title")]').click()
        sleep(1)
        self.assertEqual(0, len(self.selenium.find_elements_by_class_name('button__calendar_edit__classification_update')))

        self.selenium.find_element_by_xpath('//td[contains(@class, "calendar__account")]').click()
        sleep(1)
        self.assertEqual(0, len(self.selenium.find_elements_by_xpath(
            '//td[contains(@class, "calendar__title")]'
            '//button[contains(@class, "button-update-detail-save-series")]')))

        self.selenium.find_element_by_xpath('//td[contains(@class, "calendar__outgoing")]').click()
        sleep(1)
        self.assertEqual(0, len(self.selenium.find_elements_by_xpath(
            '//td[contains(@class, "calendar__account")]'
            '//button[contains(@class, "button-update-account-save-series")]')))

        self.selenium.find_element_by_xpath('//td[contains(@class, "calendar__incoming")]').click()
        sleep(1)
        self.assertEqual(0, len(self.selenium.find_elements_by_xpath(
            '//td[contains(@class, "calendar__outgoing")]'
            '//button[contains(@class, "button-update-detail-save-series")]')))

        self.selenium.find_element_by_xpath('//td[contains(@class, "calendar__payment_date")]').click()
        sleep(1)
        self.assertEqual(0, len(self.selenium.find_elements_by_xpath(
            '//td[contains(@class, "calendar__incoming")]'
            '//button[contains(@class, "button-update-detail-save-series")]')))


class TestCategoryManagement(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestCategoryManagement, cls).setUpClass()

    @classmethod
    def setUp(cls):
        d = DesiredCapabilities.CHROME
        d['loggingPrefs'] = {'browser': 'ALL'}
        cls.selenium = WebDriver(desired_capabilities=d)
        cls.selenium.implicitly_wait(1)
        test_users()
        test_categories()
        test_bank_accounts()
        test_payment_schedules()
        test_payments()
        test_login(cls)

    @classmethod
    def tearDown(cls):
        cls.selenium.quit()

    @classmethod
    def tearDownClass(cls):
        super(TestCategoryManagement, cls).tearDownClass()

    def test_default_management_selections(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.ID, 'txt__calendar_search'))).send_keys('New Payment')
        self.selenium.find_element_by_id('btn__calendar_new_payment_from_search').click()

        select_chosen_by_id(self, "//select[@id = 'id_payment_type']/..", "id_payment_type", "pt1")
        select_chosen_by_id(self, "//select[@id = 'id_category']/..", "id_category", "cat1")
        select_chosen_by_id(self, "//select[@id = 'id_subcategory']/..", "id_subcategory", "subcat1")

        self.selenium.find_element_by_id('button__manage_categories').click()

        sleep(1)
        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
                    '//table[@id = "id__manage_categories_payment_types"]//td[text() = "pt1"]')))
        self.assertIn('highlighted', element.get_attribute('class'))
        element = self.selenium.find_element_by_xpath(
                    '//table[@id = "id__manage_categories_categories"]//td[text() = "cat1"]')
        self.assertIn('highlighted', element.get_attribute('class'))
        element = self.selenium.find_element_by_xpath(
                    '//table[@id = "id__manage_categories_subcategories"]//td[text() = "subcat1"]')
        self.assertIn('highlighted', element.get_attribute('class'))

        self.selenium.find_element_by_id('button__payment_type_add').click()
        sleep(1)  # allow changes to be saved
        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
                    '//table[@id = "id__manage_categories_payment_types"]//td[text() = "Payment Type #1"]')))
        self.assertIn('selected', element.get_attribute('class'))
        self.assertEqual("Payment Type #1", self.selenium.find_element_by_id('txt__payment_type_update')
                         .get_attribute('value'))
        self.assertEqual(self.selenium.find_element_by_id('id_payment_type_chosen').text, 'Payment Type #1')

        self.selenium.find_element_by_id('button__category_add').click()
        sleep(1)
        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
            '//table[@id = "id__manage_categories_categories"]//td[text() = "Category #1"]')))
        self.assertIn('selected', element.get_attribute('class'))
        self.assertEqual("Category #1", self.selenium.find_element_by_id('txt__category_update').get_attribute('value'))
        elements = self.selenium.find_elements_by_xpath('//table[@id = "id__manage_categories_payment_types"]'
            '//tr[td[contains(@class, "highlighted")]]')
        self.assertEqual(1, len(elements))
        self.assertEqual('Payment Type #1', elements[0].text)
        self.assertEqual(self.selenium.find_element_by_id('id_payment_type_chosen').text, 'Payment Type #1')
        self.assertEqual(self.selenium.find_element_by_id('id_category_chosen').text, 'Category #1')

        self.selenium.find_element_by_id('button__subcategory_add').click()
        sleep(1)
        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
                    '//table[@id = "id__manage_categories_subcategories"]//td[text() = "Subcategory #1"]')))
        self.assertIn('selected', element.get_attribute('class'))
        self.assertEqual("Subcategory #1", self.selenium.find_element_by_id('txt__subcategory_update')
                         .get_attribute('value'))
        elements = self.selenium.find_elements_by_xpath('//table[@id = "id__manage_categories_payment_types"]'
                                                        '//tr[td[contains(@class, "highlighted")]]')
        self.assertEqual(1, len(elements))
        self.assertEqual('Payment Type #1', elements[0].text)
        elements = self.selenium.find_elements_by_xpath('//table[@id = "id__manage_categories_categories"]'
                                                        '//tr[td[contains(@class, "highlighted")]]')
        self.assertEqual(1, len(elements))
        self.assertEqual('Category #1', elements[0].text)

        self.selenium.find_element_by_id('button__manage_categories_done').click()

        self.assertEqual(self.selenium.find_element_by_id('id_payment_type_chosen').text, 'Payment Type #1')
        self.assertEqual(self.selenium.find_element_by_id('id_category_chosen').text, 'Category #1')
        self.assertEqual(self.selenium.find_element_by_id('id_subcategory_chosen').text, 'Subcategory #1')

    def test_default_management_selections_no_subcategory(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.ID, 'txt__calendar_search'))).send_keys('New Payment')
        self.selenium.find_element_by_id('btn__calendar_new_payment_from_search').click()

        select_chosen_by_id(self, "//select[@id = 'id_payment_type']/..", "id_payment_type", "pt1")
        select_chosen_by_id(self, "//select[@id = 'id_category']/..", "id_category", "cat1")

        self.selenium.find_element_by_id('button__manage_categories').click()

        sleep(1)
        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
            '//table[@id = "id__manage_categories_payment_types"]//td[text() = "pt1"]')))
        self.assertIn('highlighted', element.get_attribute('class'))
        element = self.selenium.find_element_by_xpath(
            '//table[@id = "id__manage_categories_categories"]//td[text() = "cat1"]')
        self.assertIn('highlighted', element.get_attribute('class'))
        element = self.selenium.find_element_by_xpath(
            '//table[@id = "id__manage_categories_subcategories"]//td[text() = "subcat1"]')
        self.assertNotIn('highlighted', element.get_attribute('class'))

    def test_update_payment_type(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.ID, 'txt__calendar_search'))).send_keys('New Payment')
        self.selenium.find_element_by_id('btn__calendar_new_payment_from_search').click()

        select_chosen_by_id(self, "//select[@id = 'id_payment_type']/..", "id_payment_type", "pt1")
        select_chosen_by_id(self, "//select[@id = 'id_category']/..", "id_category", "cat1")
        select_chosen_by_id(self, "//select[@id = 'id_subcategory']/..", "id_subcategory", "subcat1")

        self.selenium.find_element_by_id('button__manage_categories').click()

        sleep(1)
        element =  WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
            '//table[@id = "id__manage_categories_payment_types"]//td[text() = "pt1"]')))
        element.click()
        sleep(1)
        self.assertIn('selected', element.get_attribute('class'))
        self.assertEqual('pt1', self.selenium.find_element_by_id('txt__payment_type_update').get_attribute('value'))
        self.selenium.find_element_by_id('txt__payment_type_update').send_keys('pt1a')
        self.selenium.find_element_by_id('button__payment_type_update').click()
        sleep(1)
        self.assertIn('result-message-box-failure',
                      self.selenium.find_element_by_id('div__user_message').get_attribute('class'))

        element = self.selenium.find_element_by_id('txt__payment_type_update')
        sleep(1)
        element.send_keys(Keys.ESCAPE)
        self.assertTrue(element.is_displayed())
        self.assertEqual('', element.get_attribute('value'))

        element.send_keys('pt1 - updated' + Keys.RETURN)
        sleep(1)

        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
            '//table[@id = "id__manage_categories_payment_types"]//td[text() = "pt1 - updated"]')))
        self.assertIn('selected', element.get_attribute('class'))
        self.assertEqual("pt1 - updated", self.selenium.find_element_by_id('txt__payment_type_update')
                         .get_attribute('value'))

        self.assertEqual(self.selenium.find_element_by_id('id_payment_type_chosen').text, 'pt1 - updated')
        p = Payment.objects.get(title="Payment 1")
        row_id = '%d|%s' % (p.id, str(p.schedule.next_date))
        self.assertEqual('pt1 - updated -\ncat1 -\nsubcat1', self.selenium.find_element_by_xpath(
            '//tr[@data-row_id = "' + row_id + '"]//div[contains(@class, "calendar__payment_classification")]').text)

    def test_update_category(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.ID, 'txt__calendar_search'))).send_keys('New Payment')
        self.selenium.find_element_by_id('btn__calendar_new_payment_from_search').click()

        select_chosen_by_id(self, "//select[@id = 'id_payment_type']/..", "id_payment_type", "pt1")
        select_chosen_by_id(self, "//select[@id = 'id_category']/..", "id_category", "cat1")
        select_chosen_by_id(self, "//select[@id = 'id_subcategory']/..", "id_subcategory", "subcat1")

        self.selenium.find_element_by_id('button__manage_categories').click()

        sleep(1)
        element = self.selenium.find_element_by_xpath(
            '//table[@id = "id__manage_categories_categories"]//td[text() = "cat1"]')
        element.click()
        sleep(1)
        self.assertIn('selected', element.get_attribute('class'))
        self.assertEqual('cat1', self.selenium.find_element_by_id('txt__category_update').get_attribute('value'))
        self.selenium.find_element_by_id('txt__category_update').send_keys('cat1a')
        self.selenium.find_element_by_id('button__category_update').click()
        sleep(1)
        self.assertIn('result-message-box-failure',
                      self.selenium.find_element_by_id('div__user_message').get_attribute('class'))

        element = self.selenium.find_element_by_id('txt__category_update')
        element.send_keys(Keys.ESCAPE)
        self.assertTrue(element.is_displayed())
        self.assertEqual('', element.get_attribute('value'))

        element.send_keys('cat1 - updated' + Keys.RETURN)
        sleep(1)
        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
            '//table[@id = "id__manage_categories_categories"]//td[text() = "cat1 - updated"]')))
        self.assertIn('selected', element.get_attribute('class'))
        self.assertEqual("cat1 - updated", self.selenium.find_element_by_id('txt__category_update')
                         .get_attribute('value'))

        self.assertEqual(self.selenium.find_element_by_id('id_category_chosen').text, 'cat1 - updated')
        p = Payment.objects.get(title="Payment 1")
        row_id = '%d|%s' % (p.id, str(p.schedule.next_date))
        self.assertEqual('pt1 -\ncat1 - updated -\nsubcat1', self.selenium.find_element_by_xpath(
            '//tr[@data-row_id = "' + row_id + '"]//div[contains(@class, "calendar__payment_classification")]').text)

    def test_update_subcategory(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.ID, 'txt__calendar_search'))).send_keys('New Payment')
        self.selenium.find_element_by_id('btn__calendar_new_payment_from_search').click()

        select_chosen_by_id(self, "//select[@id = 'id_payment_type']/..", "id_payment_type", "pt1")
        select_chosen_by_id(self, "//select[@id = 'id_category']/..", "id_category", "cat1")
        select_chosen_by_id(self, "//select[@id = 'id_subcategory']/..", "id_subcategory", "subcat1")

        self.selenium.find_element_by_id('button__manage_categories').click()

        sleep(1)
        element = self.selenium.find_element_by_xpath(
            '//table[@id = "id__manage_categories_subcategories"]//td[text() = "subcat1"]')
        element.click()
        sleep(1)
        self.assertIn('selected', element.get_attribute('class'))
        self.assertEqual('subcat1', self.selenium.find_element_by_id('txt__subcategory_update').get_attribute('value'))
        self.selenium.find_element_by_id('txt__subcategory_update').send_keys('subcat1a')
        self.selenium.find_element_by_id('button__subcategory_update').click()
        sleep(1)
        self.assertIn('result-message-box-failure',
                      self.selenium.find_element_by_id('div__user_message').get_attribute('class'))

        element = self.selenium.find_element_by_id('txt__subcategory_update')
        element.send_keys(Keys.ESCAPE)
        self.assertTrue(element.is_displayed())
        self.assertEqual('', element.get_attribute('value'))

        element.send_keys('subcat1 - updated' + Keys.RETURN)
        sleep(1)
        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
                                                                                        '//table[@id = "id__manage_categories_subcategories"]//td[text() = "subcat1 - updated"]')))
        self.assertIn('selected', element.get_attribute('class'))
        self.assertEqual("subcat1 - updated", self.selenium.find_element_by_id('txt__subcategory_update')
                         .get_attribute('value'))

        self.assertEqual(self.selenium.find_element_by_id('id_subcategory_chosen').text, 'subcat1 - updated')
        p = Payment.objects.get(title="Payment 1")
        row_id = '%d|%s' % (p.id, str(p.schedule.next_date))
        self.assertEqual('pt1 -\ncat1 -\nsubcat1 - updated', self.selenium.find_element_by_xpath(
            '//tr[@data-row_id = "' + row_id + '"]//div[contains(@class, "calendar__payment_classification")]').text)

    def test_update_relationships(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.ID, 'txt__calendar_search'))).send_keys('New Payment')
        self.selenium.find_element_by_id('btn__calendar_new_payment_from_search').click()
        select_chosen_by_id(self, "//select[@id = 'id_payment_type']/..", "id_payment_type", "pt1")
        select_chosen_by_id(self, "//select[@id = 'id_category']/..", "id_category", "cat1")
        select_chosen_by_id(self, "//select[@id = 'id_subcategory']/..", "id_subcategory", "subcat1")
        self.selenium.find_element_by_id('button__manage_categories').click()
        sleep(1)

        # New payment type for category
        self.selenium.find_element_by_xpath(
            '//table[@id = "id__manage_categories_categories"]//td[text() = "cat1"]').click()
        self.selenium.find_element_by_xpath(
            '//table[@id = "id__manage_categories_payment_types"]//td[text() = "pt1a"]').click()
        sleep(1)

        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, '//div[@role = "dialog"][contains(@style, "display: block")]//button[text() = "OK"]'))).click()
        sleep(1)

        self.assertEqual('pt1a', WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.ID, 'id_payment_type_chosen'))).text)
        p = Payment.objects.get(title="Payment 1")
        row_id = '%d|%s' % (p.id, str(p.schedule.next_date))
        self.assertEqual('pt1a -\ncat1 -\nsubcat1', self.selenium.find_element_by_xpath(
            '//tr[@data-row_id = "' + row_id + '"]//div[contains(@class, "calendar__payment_classification")]').text)

        # New category for subcategory
        p = Payment.objects.get(title="Payment 1")
        row_id = '%d|%s' % (p.id, str(p.schedule.next_date))
        self.assertEqual('pt1a -\ncat1 -\nsubcat1', self.selenium.find_element_by_xpath(
            '//tr[@data-row_id = "' + row_id + '"]//div[contains(@class, "calendar__payment_classification")]').text)

        self.selenium.find_element_by_xpath(
            '//table[@id = "id__manage_categories_subcategories"]//td[text() = "subcat1"]').click()
        self.selenium.find_element_by_xpath(
            '//table[@id = "id__manage_categories_categories"]//td[text() = "cat1a"]').click()
        sleep(1)

        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, '//div[@role = "dialog"][contains(@style, "display: block")]//button[text() = "OK"]'))).click()
        sleep(1)

        self.assertEqual('cat1a', WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.ID, 'id_category_chosen'))).text)
        self.assertEqual('pt1a -\ncat1a -\nsubcat1', self.selenium.find_element_by_xpath(
            '//tr[@data-row_id = "' + row_id + '"]//div[contains(@class, "calendar__payment_classification")]').text)

    # TODO Allow user to update payment with inactive Payment Type/Category/Subcategory to active ones

    def test_delete_category(self):
        # Delete payment type
        WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located((By.XPATH,
            '//div[contains(@class, "calendar__payment_classification")]'))).click()
        sleep(1)
        WebDriverWait(self.selenium, 1).until(ec.visibility_of_element_located((By.CLASS_NAME,
            'button__calendar_edit__classification_edit'))).click()
        sleep(1)
        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
            '//table[@id = "id__manage_categories_payment_types"]//tr[td[text() = "pt1a"]]'
            '//button[contains(@class, "button__manage_categories_payment_types_delete")]')))
        ActionChains(self.selenium).move_to_element(element).click(element).perform()
        sleep(1)
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, '//div[@role = "dialog"][contains(@style, "display: block")]//button[text() = "OK"]'))).click()
        sleep(1)
        elements = self.selenium.find_elements_by_xpath(
            '//table[@id = "id__manage_categories_payment_types"]//tr[td[text() = "pt1a"]]')
        self.assertEqual(0, len(elements))

        # Delete category
        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
            '//table[@id = "id__manage_categories_categories"]//tr[td[text() = "cat1a"]]'
            '//button[contains(@class, "button__manage_categories_categories_delete")]')))
        ActionChains(self.selenium).move_to_element(element).click(element).perform()
        sleep(1)
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, '//div[@role = "dialog"][contains(@style, "display: block")]//button[text() = "OK"]'))).click()
        sleep(1)
        elements = self.selenium.find_elements_by_xpath(
            '//table[@id = "id__manage_categories_categories"]//tr[td[text() = "cat1a"]]')
        self.assertEqual(0, len(elements))

        # Delete subcategory
        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
            '//table[@id = "id__manage_categories_subcategories"]//tr[td[text() = "subcat1a"]]'
            '//button[contains(@class, "button__manage_categories_subcategories_delete")]')))
        ActionChains(self.selenium).move_to_element(element).click(element).perform()
        sleep(1)
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, '//div[@role = "dialog"][contains(@style, "display: block")]//button[text() = "OK"]'))).click()
        sleep(1)
        elements = self.selenium.find_elements_by_xpath(
            '//table[@id = "id__manage_categories_subcategories"]//tr[td[text() = "subcat1a"]]')
        self.assertEqual(0, len(elements))

    # TODO Allow user to update payment with inactive Payment Type/Category/Subcategory to active ones


class TestBankAccountManagement(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestBankAccountManagement, cls).setUpClass()

    @classmethod
    def setUp(cls):
        d = DesiredCapabilities.CHROME
        d['loggingPrefs'] = {'browser': 'ALL'}
        cls.selenium = WebDriver(desired_capabilities=d)
        cls.selenium.implicitly_wait(1)
        test_users()
        test_categories()
        test_bank_accounts()
        test_payment_schedules()
        test_payments()
        test_login(cls)

    @classmethod
    def tearDown(cls):
        cls.selenium.quit()

    @classmethod
    def tearDownClass(cls):
        super(TestBankAccountManagement, cls).tearDownClass()

    def test_create_bank_account(self):
        WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_element_located((By.ID, 'href__add_account'))).click()
        sleep(2)
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.CLASS_NAME, 'td__bank_account_title')))
        self.assertEqual(1, len(list(ba for ba in elements if ba.text == 'Bank Account #1')))

    def test_only_1_account_editable(self):
        elements = WebDriverWait(self.selenium, 1) \
            .until(ec.presence_of_all_elements_located((By.CLASS_NAME, 'td__bank_account_title')))
        account_name = elements[0].text
        next_account_name = elements[1].text
        elements[0].click()
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, '//td[contains(@class,"td__bank_account_title")]/input[@value = "' + account_name + '"]')))

        sleep(1)
        elements[1].click()
        elements = self.selenium.find_elements_by_xpath(
            '//td[contains(@class,"td__bank_account_title")][text() = "' + next_account_name + '"]/input')
        self.assertEqual(0, len(elements))

    def test_account_update(self):
        account_id_xpath = '//tr[@data-bank_account_id = "%d"]' % BankAccount.objects.filter(
            title__iexact="john account").get().pk

        # Update title
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, '//td[contains(@class,"td__bank_account_title")][text() = "john account"]'))).click()
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, '//td[contains(@class,"td__bank_account_title")]/input[@value = "john account"]')))\
            .send_keys('john account updated' + Keys.RETURN)
        sleep(1)

        elements = WebDriverWait(self.selenium, 1).until(ec.presence_of_all_elements_located(
            (By.XPATH, '//td[contains(@class,"td__bank_account_title")][text() = "john account updated"]')))
        self.assertEqual(1, len(elements))
        elements = self.selenium.find_elements_by_xpath(
            '//td[contains(@class,"td__bank_account_title")][text() = "john account updated"]/input')
        self.assertEqual(0, len(elements))

        self.assertNotEqual(0, len(self.selenium.find_elements_by_xpath(
            '//td[contains(@class, "calendar__account")][text() = "john account updated"]')))

        # Update balance
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
            account_id_xpath + '/td[contains(@class,"td__bank_account_balance")]'))).click()
        sleep(1)
        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, account_id_xpath + '/td[contains(@class,"td__bank_account_balance")]/input')))
        element.send_keys('2000' + Keys.RETURN)
        sleep(1)

        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
            account_id_xpath + '/td[contains(@class,"td__bank_account_balance")]')))
        self.assertEqual('$2,000.00', element.text)
        elements = self.selenium.find_elements_by_xpath(
            account_id_xpath + '/td[contains(@class,"td__bank_account_balance")]/input')
        self.assertEqual(0, len(elements))
        element = self.selenium.find_element_by_xpath('//div[contains(@class, "calendar__curr_budget_balance")]')
        self.assertEqual('$1,800.00', element.text)

        # Update account type
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
            account_id_xpath + '/td[contains(@class,"td__bank_account_type")]'))).click()
        sleep(1)
        select_chosen_by_class(self, account_id_xpath + '/td[contains(@class,"td__bank_account_type")]//select/..',
                               "Credit")
        sleep(2)
        self.selenium.find_element_by_xpath(account_id_xpath +
            '//button[contains(@class, "cbo__edit_bank_account_type_ok")]').click()
        sleep(1)

        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.XPATH,
            account_id_xpath + '/td[contains(@class,"td__bank_account_type")]')))
        self.assertEqual('Credit', element.text)
        elements = self.selenium.find_elements_by_xpath(account_id_xpath +
            '//button[contains(@class, "cbo__edit_bank_account_type_ok")]')
        self.assertEqual(0, len(elements))
        element = self.selenium.find_element_by_xpath('//div[contains(@class, "calendar__curr_budget_balance")]')
        self.assertEqual('$0.00', element.text)
