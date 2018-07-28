from django import forms
import re

from .models import *


class PaymentForm(forms.Form):
    payment_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    action = forms.CharField(widget=forms.HiddenInput(), required=False)
    title = forms.CharField(label='Title', max_length=100)
    amount = forms.CharField(label='Amount', max_length=100, widget=forms.TextInput(attrs={'class': 'money'}))
    in_out = forms.ChoiceField(
        choices=(
            ('i', 'Incoming'),
            ('o', 'Outgoing')
        ),
        initial='o'
    )

    payment_type = forms.ChoiceField()
    category = forms.ChoiceField(required=False)
    subcategory = forms.ChoiceField(required=False)

    schedule_frequency = forms.ChoiceField(widget=forms.Select(attrs={'class': 'select__schedule_frequency'}))
    next_date = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
        input_formats=['%d/%m/%Y', '%d/%m/%y'],
    )
    account = forms.ChoiceField(required=True)
    is_exclusion = forms.CharField(widget=forms.HiddenInput(), required=False)
    until_type = forms.CharField(widget=forms.HiddenInput(), required=True) # 'forever', 'occurrences', 'end_date'
    occurrences = forms.CharField(required=False)
    end_date = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
        input_formats=['%d/%m/%Y', '%d/%m/%y'],
        required=False,
    )

    # Weekly fields
    weekly_dow_mon = forms.BooleanField(required=False)
    weekly_dow_tue = forms.BooleanField(required=False)
    weekly_dow_wed = forms.BooleanField(required=False)
    weekly_dow_thu = forms.BooleanField(required=False)
    weekly_dow_fri = forms.BooleanField(required=False)
    weekly_dow_sat = forms.BooleanField(required=False)
    weekly_dow_sun = forms.BooleanField(required=False)
    weekly_frequency = forms.CharField(widget=forms.HiddenInput(), required=False)

    # Monthly fields
    monthly_dom = forms.CharField(widget=forms.HiddenInput(), required=False)
    monthly_frequency = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    monthly_wom = forms.CharField(widget=forms.HiddenInput(), required=False)
    monthly_dow = forms.CharField(widget=forms.HiddenInput(), required=False)

    # Annual fields
    annual_dom = forms.ChoiceField(
        required=False,
        choices=[(1, '1st'), (2, '2nd'), (3, '3rd'), (4, '4th'), (5, '5th'),
                 (6, '6th'), (7, '7th'), (8, '8th'), (9, '9th'), (10, '10th'),
                 (11, '11th'), (12, '12th'), (13, '13th'), (14, '14th'), (15, '15th'),
                 (16, '16th'), (17, '17th'), (18, '18th'), (19, '19th'), (20, '20th'),
                 (21, '21th'), (22, '22th'), (23, '23th'), (24, '24th'), (25, '25th'),
                 (26, '26th'), (27, '27th'), (28, '28th'), (29, '29th'), (30, '30th'), (31, '31st')]
    )
    annual_moy = forms.ChoiceField(
        required=False,
        choices=[(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'),
                 (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]
    )
    annual_frequency = forms.IntegerField(min_value=0, required=False)

    # Linking fields
    linked_to = forms.ChoiceField(required=False)
    offset = forms.CharField(initial=0)
    offset_type = forms.ChoiceField(
        choices=(
            ('days', 'Days'),
            ('weeks', 'Weeks'),
            ('months', 'Months'),
            ('years', 'Years'),
        ),
        initial='days',
        required=False,
    )

    def __init__(self, user, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        self.fields['payment_type'].choices = \
            ([(0, '')] + [(pt.id, pt.name) for pt in PaymentType.objects.filter(owner=user, active=True).order_by('name')])
        self.fields['category'].choices = \
            ([(0, '')] + [(c.id, c.name) for c in Category.objects.filter(owner=user, active=True).order_by('name')])
        self.fields['subcategory'].choices = \
            ([(0, '')] + [(sc.id, sc.name) for sc in SubCategory.objects.filter(owner=user, active=True).order_by('name')])
        self.fields['schedule_frequency'].choices = \
            ([(sf.id, sf.name) for sf in PaymentScheduleFrequency.objects.filter(active=True).order_by('sort_order')])
        self.fields['account'].choices = \
            ([(a.id, a.title) for a in BankAccount.objects.filter(owner=user, active=True).order_by('title')])
        self.fields['linked_to'].choices = \
            ([(p.id, p.title) for p in Payment.objects.filter(owner=user, active=True).order_by('title')])

    def clean_amount(self):
        data = re.sub(r'[^0-9.]', r'', self.cleaned_data['amount'])
        return data


class PaymentDateForm(forms.Form):
    payment_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    schedule_frequency = forms.ChoiceField(widget=forms.Select(attrs={'class': 'select__schedule_frequency'}),
                                           required=False)
    next_date = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
        input_formats=['%d/%m/%Y', '%d/%m/%y'],
    )
    until_type = forms.CharField(widget=forms.HiddenInput(), required=True) # 'forever', 'occurrences', 'end_date'
    occurrences = forms.CharField(required=False)
    end_date = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y'),
        input_formats=['%d/%m/%Y', '%d/%m/%y'],
        required=False,
    )

    # Weekly fields
    weekly_dow_mon = forms.BooleanField(required=False)
    weekly_dow_tue = forms.BooleanField(required=False)
    weekly_dow_wed = forms.BooleanField(required=False)
    weekly_dow_thu = forms.BooleanField(required=False)
    weekly_dow_fri = forms.BooleanField(required=False)
    weekly_dow_sat = forms.BooleanField(required=False)
    weekly_dow_sun = forms.BooleanField(required=False)
    weekly_frequency = forms.CharField(widget=forms.HiddenInput(), required=False)

    # Monthly fields
    monthly_dom = forms.CharField(widget=forms.HiddenInput(), required=False)
    monthly_frequency = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    monthly_wom = forms.CharField(widget=forms.HiddenInput(), required=False)
    monthly_dow = forms.CharField(widget=forms.HiddenInput(), required=False)

    # Annual fields
    annual_dom = forms.ChoiceField(
        required=False,
        choices=[(1, '1st'), (2, '2nd'), (3, '3rd'), (4, '4th'), (5, '5th'),
                 (6, '6th'), (7, '7th'), (8, '8th'), (9, '9th'), (10, '10th'),
                 (11, '11th'), (12, '12th'), (13, '13th'), (14, '14th'), (15, '15th'),
                 (16, '16th'), (17, '17th'), (18, '18th'), (19, '19th'), (20, '20th'),
                 (21, '21th'), (22, '22th'), (23, '23th'), (24, '24th'), (25, '25th'),
                 (26, '26th'), (27, '27th'), (28, '28th'), (29, '29th'), (30, '30th'), (31, '31st')]
    )
    annual_moy = forms.ChoiceField(
        required=False,
        choices=[(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'),
                 (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]
    )
    annual_frequency = forms.IntegerField(min_value=0, required=False)

    # Linking fields
    linked_to = forms.ChoiceField(required=False)
    offset = forms.CharField(initial=0)
    offset_type = forms.ChoiceField(
        choices=(
            ('days', 'Days'),
            ('weeks', 'Weeks'),
            ('months', 'Months'),
            ('years', 'Years'),
        ),
        initial='days',
        required=False,
    )

    def __init__(self, user, *args, **kwargs):
        super(PaymentDateForm, self).__init__(*args, **kwargs)
        self.fields['schedule_frequency'].choices = \
            ([(sf.id, sf.name) for sf in PaymentScheduleFrequency.objects.order_by('sort_order')])
        self.fields['linked_to'].choices = \
            ([(p.id, p.title) for p in Payment.objects.filter(owner=user, active=True).order_by('title')])
        # p = Payment.objects.filter(pk=self.payment_id)


class PaymentClassificationForm(forms.Form):
    payment_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    payment_type = forms.ChoiceField()
    category = forms.ChoiceField(required=False)
    subcategory = forms.ChoiceField(required=False)

    def __init__(self, user, *args, **kwargs):
        super(PaymentClassificationForm, self).__init__(*args, **kwargs)
        self.fields['payment_type'].choices = \
            ([(0, '')] + [(pt.id, pt.name) for pt in PaymentType.objects.filter(owner=user, active=True).order_by('name')])
        self.fields['category'].choices = \
            ([(0, '')] + [(c.id, c.name) for c in Category.objects.filter(owner=user, active=True).order_by('name')])
        self.fields['subcategory'].choices = \
            ([(0, '')] + [(sc.id, sc.name) for sc in SubCategory.objects.filter(owner=user, active=True).order_by('name')])


class CategoriesForm(forms.Form):
    manage_payment_type = forms.MultipleChoiceField(
        widget=forms.SelectMultiple(attrs={'size': '10', 'class': 'mc_payment_type'})
    )
    selected_payment_type = forms.CharField(widget=forms.HiddenInput(), required=False)
    updated_payment_type = forms.CharField(widget=forms.HiddenInput(), required=False)
    manage_category = forms.MultipleChoiceField(
        widget=forms.SelectMultiple(attrs={'size': '10', 'class': 'mc_category'})
    )
    selected_category = forms.CharField(widget=forms.HiddenInput(), required=False)
    updated_category = forms.CharField(widget=forms.HiddenInput(), required=False)
    manage_subcategory = forms.MultipleChoiceField(
        widget=forms.SelectMultiple(attrs={'size': '10', 'class': 'mc_subcategory'})
    )
    selected_subcategory = forms.CharField(widget=forms.HiddenInput(), required=False)
    updated_subcategory = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, user, *args, **kwargs):
        super(CategoriesForm, self).__init__(*args, **kwargs)
        self.fields['manage_payment_type'].choices = \
            ([(pt.id, pt.name) for pt in PaymentType.objects.filter(owner=user, active=True).order_by('name')])
        self.fields['manage_category'].choices = \
            ([(c.id, c.name) for c in Category.objects.filter(owner=user, active=True).order_by('name')])
        self.fields['manage_subcategory'].choices = \
            ([(sc.id, sc.name) for sc in SubCategory.objects.filter(owner=user, active=True).order_by('name')])


class AccountForm(forms.Form):
    bank_account_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    title = forms.CharField(label='Title', max_length=100,
                            widget=forms.TextInput(attrs={'class': 'bank_account_title'}))
    current_balance = forms.CharField(label='Balance', max_length=100,
                                      widget=forms.TextInput(attrs={'class': 'bank_account_balance money'}))
    account_type = forms.ChoiceField(
        choices=(
            ('debit', 'Debit'),
            ('credit', 'Credit'),
            ('virtual', 'Virtual'),
        ),
        initial='credit'
    )
