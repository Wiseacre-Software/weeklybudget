from django import forms
from django.db.models import Q

from budget.models import BankAccount

class UploadFileForm(forms.Form):
    file = forms.FileField()
    account = forms.ChoiceField()

    def __init__(self, user, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)

        # bank_accounts = [(a.id, a.title, a.account_type) for a in BankAccount.objects.filter(owner=user, active=True)
        #         .filter(Q(account_type='debit') | Q(account_type='credit')).order_by('display_order')]

        account_choices = [('Debit', [(a.id, a.title) for a in BankAccount.objects.filter(
            owner=user, active=True, account_type='debit').order_by('display_order')])]
        account_choices += [('Credit', [(a.id, a.title) for a in BankAccount.objects.filter(
            owner=user, active=True, account_type='credit').order_by('display_order')])]

        self.fields['account'].choices = account_choices
