import csv
from decimal import Decimal
from re import sub
from time import sleep

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.template.defaultfilters import date as _date
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec  # available since 2.26.0
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0

from budget.models import BankAccount, PaymentType, Category, SubCategory
from .models import Transaction, Extract

# python manage.py test transactions.ui_tests

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


def test_westpac_load():
    user = User.objects.get(username__exact='john')
    r = Extract.objects.create(
        extract_run_id=1,
        has_header_row=True,
        delimiter=',',
        owner=user,
    )
    with open(test_file_path + r'\westpac1.csv', 'r') as f:
        row_number = 1
        for row in f:
            t = Transaction.objects.create(
                run=r,
                raw_text=row,
                row_number=row_number,
                owner=user,
            )
            t.save()
            row_number += 1

def test_virgin_load():
    user = User.objects.get(username__exact='john')
    r = Extract.objects.create(
        extract_run_id=2,
        has_header_row=False,
        delimiter=',',
        owner=user,
    )
    with open(test_file_path + r'\virgin_mc.csv', 'r') as f:
        reader = csv.reader(f)
        row_number = 1
        for row in reader:
            t = Transaction.objects.create(
                run=r,
                raw_text=row,
                row_number=row_number,
                owner=user,
            )
            t.save()
            row_number += 1
# endregion


# region Common Operations
def test_login(self):
    self.selenium.get('%s%s' % (self.live_server_url, '/transactions/'))
    username_input = self.selenium.find_element_by_name("username")
    username_input.send_keys('john')
    password_input = self.selenium.find_element_by_name("password")
    password_input.send_keys('johnpassword')
    self.selenium.find_element_by_xpath('//input[@value="login"]').click()


def print_console_logs(driver):
    print '----------------------------------------'
    print 'Console logs:'
    print
    # console_logs = (entry for entry in driver.get_log('browser') if entry['source'] == 'console-api')
    # for entry in console_logs:
    for entry in driver.get_log('browser'):
        print entry['message']


def chosen_selected_text(self, select_element_parent_xpath):
    chosen_dev_xpath = select_element_parent_xpath + "/div[contains(@class, 'chosen-container')]"
    return self.selenium.find_element_by_xpath(chosen_dev_xpath + "/a/span").text
# endregion


class TestFileUpload(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestFileUpload, cls).setUpClass()

    @classmethod
    def setUp(cls):
        d = DesiredCapabilities.CHROME
        d['loggingPrefs'] = {'browser': 'ALL'}
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        cls.selenium = WebDriver(desired_capabilities=d, chrome_options=chrome_options)
        cls.selenium.implicitly_wait(1)
        test_users()
        test_categories()
        test_bank_accounts()
        test_login(cls)

    @classmethod
    def tearDown(cls):
        cls.selenium.quit()

    @classmethod
    def tearDownClass(cls):
        super(TestFileUpload, cls).tearDownClass()

    def test_file_upload(self):
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, "//div[@id = 'id_account_chosen']")))
        self.assertEqual('john account', chosen_selected_text(self, "//select[@id = 'id_account']/.."))

        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.ID, 'id_file')))\
            .send_keys(test_file_path + r'\westpac1.csv')
        self.selenium.find_element_by_id('btn__upload_file_submit').click()
        sleep(1)

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Upload successful!')
        print_console_logs(self.selenium)

        self.assertEqual('733000731063', self.selenium.find_element_by_xpath('((//table[@id="tbl__upload_table"]//tr[td])[1]/td)[2]').text)

    def test_file_upload_no_header(self):
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located((By.ID, 'id_file')))\
            .send_keys(test_file_path + r'\virgin_mc.csv')
        self.selenium.find_element_by_id('btn__upload_file_submit').click()
        sleep(1)

        element = WebDriverWait(self.selenium, 1) \
            .until(ec.visibility_of_element_located((By.ID, 'div__user_message')))
        self.assertIsNotNone(element)
        self.assertEqual(element.text, 'Upload successful!')
        print_console_logs(self.selenium)

        elements = self.selenium.find_elements_by_xpath('(//table[@id="tbl__upload_table"]//tr[td])[1]/td')
        self.assertEqual('1', elements[0].text)
        self.assertEqual('"01/08/2017"', elements[1].text)


class TestFileUploadOptions(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestFileUploadOptions, cls).setUpClass()

    @classmethod
    def setUp(cls):
        d = DesiredCapabilities.CHROME
        d['loggingPrefs'] = {'browser': 'ALL'}
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        cls.selenium = WebDriver(desired_capabilities=d, chrome_options=chrome_options)
        cls.selenium.implicitly_wait(1)
        test_users()
        test_categories()
        test_bank_accounts()
        test_westpac_load()
        test_login(cls)

    @classmethod
    def tearDown(cls):
        cls.selenium.quit()

    @classmethod
    def tearDownClass(cls):
        super(TestFileUploadOptions, cls).tearDownClass()

    def test_file_upload_options(self):
        WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, "//div[@id = 'id_account_chosen']")))
        self.assertEqual('john account', chosen_selected_text(self, "//select[@id = 'id_account']/.."))

        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, '//label[@for="chk__header_row"]')))
        self.assertEqual('true', self.selenium.find_element_by_id('chk__header_row').get_attribute("checked"))
        self.assertIn("ui-checkboxradio-checked", element.get_attribute("class"))
        self.assertEqual('1', self.selenium.find_element_by_xpath('(//table[@id="tbl__upload_table"]//th)[1]').text)
        self.assertEqual('2', self.selenium.find_element_by_xpath('(//table[@id="tbl__upload_table"]//td)[1]').text)
        element.click()
        sleep(1)

        self.assertEqual('Row Number', self.selenium.find_element_by_xpath('(//table[@id="tbl__upload_table"]//th)[1]').text)
        self.assertEqual('1', self.selenium.find_element_by_xpath('(//table[@id="tbl__upload_table"]//td)[1]').text)
        element.click()
        sleep(1)

        header_row = WebDriverWait(self.selenium, 1).until(ec.presence_of_all_elements_located(
            (By.XPATH, '//table[@id="tbl__upload_table"]//th')))
        self.assertEqual('1', header_row[0].text)
        self.assertEqual('2', self.selenium.find_element_by_xpath('(//table[@id="tbl__upload_table"]//td)[1]').text)

    def test_file_upload_no_header_options(self):
        test_virgin_load()
        self.selenium.refresh()
        sleep(10)

        element = WebDriverWait(self.selenium, 1).until(ec.presence_of_element_located(
            (By.XPATH, '//label[@for="chk__header_row"]')))
        self.assertIsNone(self.selenium.find_element_by_id('chk__header_row').get_attribute("checked"))
        self.assertNotIn("ui-checkboxradio-checked", element.get_attribute("class"))
        self.assertEqual('Row Number', self.selenium.find_element_by_xpath('(//table[@id="tbl__upload_table"]//th)[1]').text)
        self.assertEqual('1', self.selenium.find_element_by_xpath('(//table[@id="tbl__upload_table"]//td)[1]').text)
        element.click()
        sleep(1)

        self.assertEqual('1', self.selenium.find_element_by_xpath('(//table[@id="tbl__upload_table"]//th)[1]').text)
        self.assertEqual('2', self.selenium.find_element_by_xpath('(//table[@id="tbl__upload_table"]//td)[1]').text)
        element.click()
        sleep(1)

        self.assertEqual('Row Number', self.selenium.find_element_by_xpath('(//table[@id="tbl__upload_table"]//th)[1]').text)
        self.assertEqual('1', self.selenium.find_element_by_xpath('(//table[@id="tbl__upload_table"]//td)[1]').text)

