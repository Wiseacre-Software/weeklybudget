from django.conf.urls import url
from . import views as budget_views

app_name = 'budget'
urlpatterns = [
    url(r"^$", budget_views.PaymentList.as_view()),
    url(r"^payments/", budget_views.get_payments, name='get_payments'),
    url(r"^update_payment/", budget_views.update_payment, name='update_payment'),
    url(r"^update_payment_date/", budget_views.update_payment_date, name='update_payment_date'),
    url(r"^update_payment_classification/", budget_views.update_payment_classification, name='update_payment_classification'),
    url(r"^manage_categories/", budget_views.manage_categories, name='manage_categories'),
    url(r"^calendar_view/", budget_views.generate_calendar_view, name='generate_calendar_view'),
    url(r"^bank_account/", budget_views.bank_account_view, name='bank_account_view'),
]
