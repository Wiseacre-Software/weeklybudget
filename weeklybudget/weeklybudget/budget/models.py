import logging

from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY, weekdays, WEEKLY
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

# region Reference
from django.db.models import SET_NULL
from django.utils.datetime_safe import date, datetime
from simple_history.models import HistoricalRecords

logger = logging.getLogger(__name__)


class PaymentType(models.Model):
    name = models.CharField(max_length=200)
    sort_order = models.SmallIntegerField(null=True)
    owner = models.ForeignKey(User)
    active = models.BooleanField(default=True)
    history = HistoricalRecords()

    def __unicode__(self):
        return unicode(self.name)


class Category(models.Model):
    name = models.CharField(max_length=200)
    payment_type = models.ForeignKey(PaymentType)
    payment_type.default = 0
    owner = models.ForeignKey(User)
    active = models.BooleanField(default=True)
    history = HistoricalRecords()

    def __unicode__(self):
        return unicode(self.name)


class SubCategory(models.Model):
    category = models.ForeignKey(Category)
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User)
    active = models.BooleanField(default=True)
    history = HistoricalRecords()

    def __unicode__(self):
        return unicode(self.name)


# endregion

# region Accounts


class BankAccount(models.Model):
    title = models.CharField(max_length=200)
    # current_balance represents amount available for credit accounts
    current_balance = models.DecimalField(max_digits=18, decimal_places=4)
    owner = models.ForeignKey(User)
    account_type = models.CharField(max_length=20, default='debit')  # debit/credit/virtual
    account_limit = models.DecimalField(max_digits=18, decimal_places=4, null=True, default=0)
    display_order = models.SmallIntegerField(default=0)
    active = models.BooleanField(default=True)
    history = HistoricalRecords()

    def clean(self):
        if self.account_type == 'credit' and self.account_limit is None:
            raise ValidationError('Credit accounts require account limit to be specified')

    def __unicode__(self):
        return unicode(self.title)


# endregion

# region Scheduling


class PaymentScheduleFrequency(models.Model):
    name = models.CharField(max_length=200)
    sort_order = models.SmallIntegerField(null=True)
    list_display = ('name', 'sort_order')
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return unicode(self.name)


class PaymentSchedule(models.Model):
    next_date = models.DateField('Next Payment Date', null=True)
    frequency = models.ForeignKey(PaymentScheduleFrequency)
    end_date = models.DateField('Last Payment Date', null=True, blank=True)
    occurrences = models.SmallIntegerField(default=0)  # 0 = infinite
    history = HistoricalRecords()

    # Weekly fields
    weekly_dow_mon = models.BooleanField(default=False)  # day of week
    weekly_dow_tue = models.BooleanField(default=False)
    weekly_dow_wed = models.BooleanField(default=False)
    weekly_dow_thu = models.BooleanField(default=False)
    weekly_dow_fri = models.BooleanField(default=False)
    weekly_dow_sat = models.BooleanField(default=False)
    weekly_dow_sun = models.BooleanField(default=False)
    weekly_frequency = models.SmallIntegerField(default=0, null=True)  # every 'x' weeks

    # Monthly fields
    monthly_dom = models.SmallIntegerField(default=0, null=True)  # day of month: -1 = last, -2 second last, etc
    monthly_frequency = models.SmallIntegerField(default=0, null=True)  # every 'x' months
    monthly_wom = models.SmallIntegerField(default=0, null=True)  # week of month: -1 = last, -2 second last, etc
    monthly_dow = models.SmallIntegerField(default=0, null=True)  # 0 = Monday

    # Annual fields
    annual_dom = models.SmallIntegerField(default=0, null=True)  # day of month
    annual_moy = models.SmallIntegerField(default=0, null=True)  # month of year
    annual_frequency = models.SmallIntegerField(default=0, null=True)  # every 'x' years

    def clean(self):
        if self.frequency.name == 'Weekly':
            if self.weekly_frequency == 0:
                raise ValidationError('Weekly payments must have a frequency specified')
            if not self.weekly_dow_mon and not self.weekly_dow_tue and not self.weekly_dow_wed \
                    and not self.weekly_dow_thu and not self.weekly_dow_fri and not self.weekly_dow_sat \
                    and not self.weekly_dow_sun:
                raise ValidationError('Weekly payments must have a at least one day of the week specified')

        if self.frequency.name == 'Monthly':
            if self.monthly_frequency == 0:
                raise ValidationError('Monthly payments must have a frequency specified')
            if self.monthly_dom == 0 and self.monthly_wom == 0:
                raise ValidationError('Monthly payments must have a day of month or week of month specified')

        if self.frequency.name == 'Annual':
            if self.annual_frequency == 0:
                raise ValidationError('Annual payments must have a frequency specified')
            if self.annual_dom == 0 or self.annual_moy == 0:
                raise ValidationError('Annual payments must have a day and month specified')

# endregion

# region Payments and associated


class Payment(models.Model):
    title = models.CharField(max_length=200)
    in_out = models.CharField(max_length=1, default='o')  # i: incoming; o: outgoing
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    payment_type = models.ForeignKey(PaymentType)
    category = models.ForeignKey(Category, null=True, blank=True)
    subcategory = models.ForeignKey(SubCategory, null=True, blank=True)
    schedule = models.ForeignKey(PaymentSchedule)
    account = models.ForeignKey(BankAccount)

    # linked payments
    parent_payment = models.ForeignKey('self', null=True, blank=True, related_name='children')
    offset = models.SmallIntegerField(default=0, null=True, blank=True)  # positive or negative number of offset_type away from parent
    offset_type = models.CharField(max_length=40, null=True, blank=True) # 'days', 'weeks', 'months', 'years'

    create_date = models.DateTimeField('create date', auto_now_add=True)
    owner = models.ForeignKey(User)
    active = models.BooleanField(default=True)
    history = HistoricalRecords()

    def __unicode__(self):
        return unicode(self.title)


class PaymentScheduleExclusion(models.Model):
    main_payment = models.ForeignKey(Payment, null=True, on_delete=models.CASCADE, related_name='exclusion')
    exclusion_payment = models.ForeignKey(Payment, null=True, on_delete=models.CASCADE, related_name='exclusion_payment')
    exclusion_date = models.DateField()
    owner = models.ForeignKey(User)
    active = models.BooleanField(default=True)
    history = HistoricalRecords()

    def __unicode__(self):
        return unicode(self.main_payment.title + ' - ' + unicode(self.exclusion_date))

# endregion

