import logging
from operator import itemgetter
from django.template.defaultfilters import date as _date
from datetime import datetime, timedelta

from dateutil.rrule import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, render_to_response
from django.utils.decorators import method_decorator
from django.utils.dateparse import parse_date
from django.utils.translation import get_language
from django.views.generic import ListView
from django.views.decorators.csrf import ensure_csrf_cookie

import jsonpickle
import re

from .forms import *
from .models import *

logger = logging.getLogger(__name__)


class PaymentList(LoginRequiredMixin, ListView):
    model = Payment
    context_object_name = "payments"
    login_url = '/login/'
    redirect_field_name = 'budget'

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, request, *args, **kwargs):
        self.request = request  # So get_context_data can access it.
        return super(PaymentList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Payment.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        # The current context.
        context = super(PaymentList, self).get_context_data(**kwargs)

        """
        Business Rules for list view
        """
        # payments = context["payments"]
        # for payment in payments:
        #         payment.recalculate_next_payment()

        """
        Add items to the context:
        """
        context["manage_payment_types"] = list(PaymentType.objects.filter(owner=self.request.user))
        context["manage_categories"] = list(Category.objects.filter(owner=self.request.user))
        context["manage_subcategories"] = list(SubCategory.objects.filter(owner=self.request.user))
        context["categorymap"] = jsonpickle.encode(generate_categorymap(self.request.user))
        context["userLanguage"] = get_language()
        return context


@login_required
@ensure_csrf_cookie
def get_payments(request):
    try:
        if request.method == 'POST':
            payments = Payment.objects.filter(owner=request.user)
            response_data = {'data': []}

            for payment in payments:
                response_data['data'].append(
                    {
                        'payment_id': payment.pk,
                        'payment_type': payment.payment_type.name if payment.payment_type else '',
                        'category': payment.category.name if payment.category else '',
                        'subcategory': payment.subcategory.name if payment.subcategory else '',
                        'title': payment.title,
                        'amount': str(payment.amount),
                        'in_out': 'Incoming' if payment.in_out == 'i' else 'Outgoing',
                        'frequency': payment.schedule.frequency.name,
                        'next_date': str(payment.schedule.next_date)
                    }
                )
            # logger.info(jsonpickle.encode(response_data))
            return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")

    except Exception as e:
        e_message = '{ "Exception": "%s" }' % e.message
        logger.error(e_message)
        return HttpResponse(e_message, content_type="application/json")


@login_required
@ensure_csrf_cookie
def update_payment(request):
    # if this is a POST request we need to process the form data
    try:
        response_data = {}

        if request.method != 'POST':
            raise RuntimeError('Invalid request')

        if 'action' not in request.POST:
            raise RuntimeError('No action specified')

        action = request.POST['action']
        snippet = 'budget/' + (request.POST['snippet'] if 'snippet' in request.POST else 'snippet__update_payment.html')

        # if this is the initial viewing of the form
        if action == 'blank':
            logger.debug('update_payment:- initial viewing')
            form = PaymentForm(request.user)
            return render_to_response(snippet, {'form': form,
                                       'categorymap': jsonpickle.encode(generate_categorymap(request.user))})

        # Save the updated payment details
        result_message = 'Payment Saved!'
        result_success = 'pass'
        form = PaymentForm(request.user, request.POST)

        if action == 'update':
            # check whether it's valid:
            if not form.is_valid():
                return HttpResponse(form.errors.as_json(), content_type="application/json")

            category = Category.objects.get(pk=form.cleaned_data['category']) \
                if 'category' in form.cleaned_data and form.cleaned_data['category'] else None
            subcategory = SubCategory.objects.get(pk=form.cleaned_data['subcategory']) \
                if 'subcategory' in form.cleaned_data and form.cleaned_data['subcategory'] else None

            if form.cleaned_data['payment_id'] == '':
                logger.debug('update_payment:- new payment')
                # new payment
                if Payment.objects.filter(owner=request.user) \
                        .filter(title__iexact=form.cleaned_data['title']).count() > 0:
                    # title must be unique for user
                    raise RuntimeError('Payment of that name already exists')

                p = Payment(
                    title=form.cleaned_data["title"],
                    amount=form.cleaned_data["amount"],
                    in_out=form.cleaned_data["in_out"],
                    payment_type=PaymentType.objects.get(pk=form.cleaned_data['payment_type']),
                    category=category,
                    subcategory=subcategory,
                    owner=request.user
                )
                build_payment_frequency(p, form.cleaned_data)
                # p.save()

            else:
                # updated payment submission
                if Payment.objects.filter(owner=request.user) \
                        .filter(title__iexact=form.cleaned_data['title']) \
                        .exclude(pk=int(form.cleaned_data['payment_id'])).count() > 0:
                    # title must be unique for user
                    raise RuntimeError('Payment of that name already exists')

                p = Payment.objects.filter(owner=request.user).get(pk=form.cleaned_data['payment_id'])
                logger.debug('update_payment:- existing payment: %s' % p.title)

                if p is None:
                    # specified payment not found
                    raise RuntimeError('Specified payment not found')

                p.title = form.cleaned_data["title"]
                p.amount = form.cleaned_data["amount"]
                p.in_out = form.cleaned_data["in_out"]
                p.payment_type = PaymentType.objects.get(pk=form.cleaned_data['payment_type'])
                p.category = category
                p.subcategory = subcategory
                build_payment_frequency(p, form.cleaned_data)
                # p.save()

            response_data['result_message'] = result_message
            response_data['result_success'] = result_success
            response_data['form_data'] = form.cleaned_data
            if p:
                if p.subcategory:
                    response_data['form_data']['subcategory_name'] = p.subcategory.name
                if p.category:
                    response_data['form_data']['category_name'] = p.category.name
                response_data['form_data']['payment_type_name'] = p.payment_type.name
                response_data['form_data']['schedule_frequency'] = p.schedule.frequency.name
                response_data['form_data']['payment_id'] = p.pk
                response_data['form_data']['next_date'] = p.schedule.next_date.strftime('%d/%m/%Y')

            return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")

        p = Payment.objects.filter(owner=request.user).get(pk=request.POST['payment_id'])
        if p is None:
            # specified payment not found
            raise RuntimeError('Specified payment not found')

        if action == 'delete':
            p.delete()
            response_data['result_message'] = 'Payment deleted!'
            response_data['result_success'] = 'pass'
            return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")

        # Render the Update Payment form
        if p.schedule is None:
            form_data = {
                'payment_id': p.pk,
                'title': p.title,
                'amount': p.amount,
                'in_out': p.in_out,
                'subcategory': p.subcategory.id if p.subcategory else 0,
                'category': p.category.id if p.category else 0,
                'payment_type': p.payment_type.id if p.payment_type else 0,
            }
        else:
            form_data = {
                'payment_id': p.pk,
                'title': p.title,
                'amount': p.amount,
                'in_out': p.in_out,
                'subcategory': p.subcategory.id if p.subcategory else 0,
                'category': p.category.id if p.category else 0,
                'payment_type': p.payment_type.id if p.payment_type else 0,
                'schedule_frequency': p.schedule.frequency.id,
                'next_date': p.schedule.next_date,
                'is_exclusion': PaymentScheduleExclusion.objects.filter(exclusion_payment=p).exists(),

                # Weekly fields
                'weekly_dow_mon': p.schedule.weekly_dow_mon,
                'weekly_dow_tue': p.schedule.weekly_dow_tue,
                'weekly_dow_wed': p.schedule.weekly_dow_wed,
                'weekly_dow_thu': p.schedule.weekly_dow_thu,
                'weekly_dow_fri': p.schedule.weekly_dow_fri,
                'weekly_dow_sat': p.schedule.weekly_dow_sat,
                'weekly_dow_sun': p.schedule.weekly_dow_sun,
                'weekly_frequency': p.schedule.weekly_frequency,

                # Monthly fields
                'monthly_dom': p.schedule.monthly_dom,
                'monthly_frequency': p.schedule.monthly_frequency,
                'monthly_wom': p.schedule.monthly_wom,
                'monthly_dow': p.schedule.monthly_dow,

                # Annual fields
                'annual_dom': p.schedule.annual_dom,
                'annual_moy': p.schedule.annual_moy,
                'annual_frequency': p.schedule.annual_frequency,
            }

        form = PaymentForm(request.user, form_data)
        return render_to_response(snippet,
                                  {'form': form, 'categorymap': jsonpickle.encode(generate_categorymap(request.user))})

    except Exception as e:
        error_message = '{ "Exception type": "%s", "Exception": "%s" }' % \
                        (str(type(e)), e.messages if hasattr(e, 'messages') else e.message)
        logger.error(error_message)
        return HttpResponse(error_message, content_type="application/json")


@login_required
@ensure_csrf_cookie
def update_payment_date(request):
    try:
        response_data = {}

        if request.method != 'POST':
            raise RuntimeError('Invalid request')

        # Check for revert action
        if 'action' in request.POST and request.POST['action'] == 'revert':
            p = Payment.objects.filter(owner=request.user)\
                .exclude(exclusion_payment__isnull=True)\
                .get(pk=request.POST['payment_id'])
            if p is None:
                raise RuntimeError('Specified payment not found')

            p.delete()
            response_data['result_message'] = 'Payment reverted successfully!'
            response_data['result_success'] = 'pass'
            return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")

        # Save the updated payment details
        result_message = 'Payment Saved!'
        result_success = 'pass'
        form = PaymentDateForm(request.POST)

        # check whether it's valid:
        if not form.is_valid():
            logger.error('update_payment_date:- form invalid, next_date: %s' % form.fields['next_date'].value())
            return HttpResponse(form.errors.as_json(), content_type="application/json")

        p = Payment.objects.filter(owner=request.user).get(pk=form.cleaned_data['payment_id'])
        logger.info('update_payment:- updating payment %s' % p.title)

        if p is None:
            # specified payment not found
            raise RuntimeError('Specified payment not found')

        response_data['result_message'] = result_message
        response_data['result_success'] = result_success
        response_data['form_data'] = form.cleaned_data

        # if only updating single instance, then add to exclusions and create one-off
        if request.POST['series_choice'] == 'this':
            logger.info('update_payment:- updating single instance')
            # new_schedule = PaymentSchedule(
            #     next_date=form.cleaned_data['next_date'],
            #     frequency=PaymentScheduleFrequency.objects.get(name__exact='Once Off'),
            # )
            # new_schedule.save()
            # new_payment = Payment(
            #     title=p.title + ' - ' + _date(form.cleaned_data['next_date'], 'SHORT_DATE_FORMAT'),
            #     in_out=p.in_out,
            #     amount=p.amount,
            #     payment_type=p.payment_type,
            #     category=p.category,
            #     subcategory=p.subcategory,
            #     schedule=new_schedule,
            #     owner=request.user
            # )
            # new_payment.save()
            # new_exclusion = PaymentScheduleExclusion(
            #     main_payment=p,
            #     exclusion_payment=new_payment,
            #     exclusion_date=parse_date(request.POST['original_date'])
            # )
            # logger.info('update_payment_date:- raw date: %s, exclusion_date: %s'
            #             % (request.POST['original_date'], str(new_exclusion.exclusion_date)))
            # new_exclusion.save()
            # response_data['form_data']['schedule_frequency'] = new_payment.schedule.frequency.name
            # response_data['form_data']['payment_id'] = new_payment.pk
            # response_data['form_data']['next_date'] = new_payment.schedule.next_date.strftime('%d/%m/%Y')

        # otherwise, update existing schedule
        else:
            logger.info('update_payment:- existing schedule: %s' % p.schedule.id)
            build_payment_frequency(p, form.cleaned_data)
            # p.save()
            # response_data['form_data']['schedule_frequency'] = p.schedule.frequency.name
            # response_data['form_data']['payment_id'] = p.pk
            # response_data['form_data']['next_date'] = p.schedule.next_date.strftime('%d/%m/%Y')

        # return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")

    except Exception as e:
        error_message = '{ "Exception type": "%s", "Exception": "%s" }' % \
                        (str(type(e)), e.messages if 'messages' in e else e.message)
        logger.error(error_message)
        return HttpResponse(error_message, content_type="application/json")


@login_required
@ensure_csrf_cookie
def update_payment_classification(request):
    try:
        response_data = {}

        if request.method != 'POST':
            raise RuntimeError('Invalid request')

        # Save the updated payment details
        response_data['result_message'] = 'Payment Saved!'
        response_data['result_success'] = 'pass'
        form = PaymentClassificationForm(request.user, request.POST)
        response_data['form_data'] = form

        # check whether it's valid:
        if not form.is_valid():
            raise ValidationError(form.errors.as_json())

        category = Category.objects.get(pk=form.cleaned_data['category']) \
            if 'category' in form.cleaned_data and form.cleaned_data['category'] else None
        subcategory = SubCategory.objects.get(pk=form.cleaned_data['subcategory']) \
            if 'subcategory' in form.cleaned_data and form.cleaned_data['subcategory'] else None

        p = Payment.objects.filter(owner=request.user).get(pk=form.cleaned_data['payment_id'])
        if p is None:
            # specified payment not found
            raise RuntimeError('Specified payment not found')

        p.payment_type = PaymentType.objects.get(pk=form.cleaned_data['payment_type'])
        p.category = category
        p.subcategory = subcategory
        p.save()

        return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")

    except Exception as e:
        error_message = '{ "Exception type": "%s", "Exception": "%s" }' % \
                        (str(type(e)), e.messages if 'messages' in e else e.message)
        logger.error(error_message)
        return HttpResponse(error_message, content_type="application/json")


@login_required
@ensure_csrf_cookie
def manage_categories(request):
    logger.info('manage_categories:- entering')
    try:
        context = dict()
        context['result_success'] = 'pass'
        context['result_message'] = 'Categories updated!'

        if 'new_payment_type' in request.POST:
            if PaymentType.objects.filter(owner=request.user).filter(name__iexact=request.POST['new_payment_type']) \
                    .count() > 0:
                # name must be unique for user
                raise RuntimeError('Payment Type of that name already exists')

            pt = PaymentType(name=request.POST['new_payment_type'], owner=request.user)
            pt.save()

        elif 'new_category' in request.POST:
            if Category.objects.filter(owner=request.user).filter(name__iexact=request.POST['new_category']).count() > 0:
                # name must be unique for user
                raise RuntimeError('Category of that name already exists')

            pt = PaymentType.objects.get(pk=request.POST['payment_type'], owner=request.user)
            c = Category(name=request.POST['new_category'], payment_type=pt, owner=request.user)
            c.save()

        elif 'new_subcategory' in request.POST:
            if SubCategory.objects.filter(owner=request.user).filter(name__iexact=request.POST['new_subcategory']) \
                    .count() > 0:
                # name must be unique for user
                raise RuntimeError('Subcategory of that name already exists')

            c = Category.objects.get(pk=request.POST['category'], owner=request.user)
            sc = SubCategory(name=request.POST['new_subcategory'], category=c, owner=request.user)
            sc.save()

        elif 'delete_payment_type' in request.POST:
            PaymentType.objects.get(pk=request.POST['delete_payment_type'], owner=request.user).delete()

        elif 'delete_category' in request.POST:
            Category.objects.get(pk=request.POST['delete_category'], owner=request.user).delete()

        elif 'delete_subcategory' in request.POST:
            SubCategory.objects.get(pk=request.POST['delete_subcategory'], owner=request.user).delete()

        elif 'edit_payment_type_id' in request.POST:
            if PaymentType.objects.filter(owner=request.user) \
                    .filter(name__iexact=request.POST['edit_payment_type_name']).count() > 0:
                # name must be unique for user
                raise RuntimeError('Payment Type of that name already exists')

            pt = PaymentType.objects.get(pk=request.POST['edit_payment_type_id'], owner=request.user)
            pt.name = request.POST['edit_payment_type_name']
            pt.save()

        elif 'edit_category_id' in request.POST:
            if Category.objects.filter(owner=request.user).filter(name__iexact=request.POST['edit_category_name']) \
                    .count() > 0:
                # name must be unique for user
                raise RuntimeError('Category of that name already exists')

            c = Category.objects.get(pk=request.POST['edit_category_id'], owner=request.user)
            c.name = request.POST['edit_category_name']
            c.save()

        elif 'edit_subcategory_id' in request.POST:
            if SubCategory.objects.filter(owner=request.user) \
                    .filter(name__iexact=request.POST['edit_subcategory_name']).count() > 0:
                # name must be unique for user
                raise RuntimeError('Subcategory of that name already exists')

            sc = SubCategory.objects.get(pk=request.POST['edit_subcategory_id'], owner=request.user)
            sc.name = request.POST['edit_subcategory_name']
            sc.save()

        context['form'] = CategoriesForm(request.user)

        pt_dict = dict()
        for pt in PaymentType.objects.filter(owner=request.user):
            pt_dict[pt.id] = pt.name
        context["manage_payment_types"] = jsonpickle.encode(pt_dict)
        cat_dict = dict()
        for c in Category.objects.filter(owner=request.user):
            cat_dict[c.id] = c.name
        context["manage_categories"] = jsonpickle.encode(cat_dict)
        sc_dict = dict()
        for sc in SubCategory.objects.filter(owner=request.user):
            sc_dict[sc.id] = sc.name
        context["manage_subcategories"] = jsonpickle.encode(sc_dict)
        context["categorymap"] = jsonpickle.encode(generate_categorymap(request.user))

        return render_to_response('budget/snippet__manage_categories.html', context)

    except Exception as e:
        return HttpResponse('{ "Exception": "' + e.message + '"}', content_type="application/json")


@login_required
@ensure_csrf_cookie
def generate_calendar_view(request):
    # logger.info('generate_calendar_view: entering...')
    try:
        if request.method != 'POST':
            raise RuntimeError('Invalid request')

        # start and end date required
        if 'start_date' not in request.POST or 'end_date' not in request.POST:
            raise RuntimeError('Missing start and/or end date: %s' % request.POST)

        # Check to see if we're marking a calendar entry as paid or received
        if 'action' in request.POST:
            p = Payment.objects.get(pk=request.POST['payment_id'])
            # logger.info('generate_calendar_view:- Payment: %s, mark paid date: %s' %
            #             (p.title, str(request.POST['payment_date'])))
            p.schedule.next_date = parse_date(request.POST['payment_date']) + relativedelta(days=1)
            p.save()
            recalculate_next_payment(p.schedule)
            # logger.info('generate_calendar_view:- Payment: %s, new date: %s' %
            #             (p.title, str(p.schedule.next_date)))

        # for each payment
        payment_calendar = []
        # logger.info('generate_calendar_view: found %i payments' % Payment.objects.filter(owner=request.user).count())
        for p in Payment.objects.filter(owner=request.user):
            # logger.info('generate_calendar_view: processing payment "%s"' % p.title)

            rr = recalculate_from_to(p.schedule, start_date=parse_date(request.POST['start_date']),
                                     end_date=parse_date(request.POST['end_date']))
            exclusions = [e.exclusion_date for e in PaymentScheduleExclusion.objects.filter(main_payment=p)]

            if rr:
                for i in range(0, len(rr)):
                    if rr[i].date() in exclusions:
                        # logger.info(
                        #     'generate_calendar_view: payment_calendar.skipping %i of %i: %s, date: %s, amount: %d' %
                        #     (i + 1, len(rr), p.title, str(rr[i].date()), p.amount))
                        continue

                    # logger.info('generate_calendar_view: payment_calendar.append %i of %i: %s, date: %s, amount: %d' %
                    #             (i + 1, len(rr), p.title, str(rr[i].date()), p.amount))
                    payment_calendar.append({
                        'payment_date': str(rr[i].date()),
                        'payment_type': p.payment_type.name if p.payment_type else '',
                        'category': p.category.name if p.category else '',
                        'subcategory': p.subcategory.name if p.subcategory else '',
                        'amount_value': p.amount,
                        'amount': str(p.amount),
                        'title': p.title,
                        'in_out': p.in_out,
                        'payment_id': p.pk
                    })

        curr_balance = BankAccount.objects.filter(owner=request.user).aggregate(Sum('current_balance'))[
            'current_balance__sum']
        # logger.info('generate_calendar_view: curr_balance...')

        sorted_payment_calendar = sorted(payment_calendar, key=itemgetter('payment_date'))
        for pc in sorted_payment_calendar:
            if 'amount' not in pc or pc['amount_value'] is None:
                logger.error('generate_calendar_view:- no amount: %s' % pc)
            if pc['in_out'] == 'i':
                curr_balance += pc['amount_value']
            else:
                curr_balance -= pc['amount_value']
            pc['curr_balance'] = str(curr_balance)

        # return render_to_response('budget/snippet__calendar_view.html', {'payment_calendar': sorted_payment_calendar})
        response_data = dict()
        response_data['data'] = sorted_payment_calendar
        return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")

    except Exception as e:
        error_message = '{ "source": "generate_calendar_view", "exception type": "%s", "exception": "%s" }' % \
                        (str(type(e)), e.message_dict if 'message_dict' in e else e.message)
        logger.error(error_message)
        return HttpResponse(error_message, content_type="application/json")


@login_required
@ensure_csrf_cookie
def bank_account_view(request):
    if request.method != 'POST':
        bank_accounts = BankAccount.objects.filter(owner=request.user)
        return render_to_response('budget/snippet__bank_accounts.html', {'bank_accounts': bank_accounts})

    try:
        if 'action' in request.POST:
            action = request.POST["action"]
            if action == 'blank':
                # send blank form
                form = AccountForm()
                return render_to_response('budget/snippet__update_account_from_calendar_view.html',
                                          {'form': form, 'result': 'blank form'})

            else:
                result_message = 'Account Saved!'
                result_success = 'pass'
                if action == 'update':
                    # add new or update existing bank account
                    form = AccountForm(request.POST)

                    if not form.is_valid():
                        return HttpResponse(form.errors.as_json())

                    if form.cleaned_data['bank_account_id'] == '':
                        # new bank account
                        if BankAccount.objects.filter(owner=request.user) \
                                .filter(title__iexact=form.cleaned_data['title']).count() > 0:
                            # title must be unique for user
                            result_message = 'Account of that name already exists'
                            result_success = 'fail'

                        else:
                            ba = BankAccount(
                                title=form.cleaned_data['title'],
                                current_balance=form.cleaned_data['current_balance'],
                                owner=request.user
                            )
                            ba.save()
                    else:
                        ba = BankAccount.objects.get(pk=form.cleaned_data['bank_account_id'])
                        ba.title = form.cleaned_data['title']
                        ba.current_balance = form.cleaned_data['current_balance']
                        ba.save()

                elif action == 'delete':
                    ba = BankAccount.objects.get(pk=request.POST['bank_account_id'])
                    ba.delete()
                    result_message = 'Account deleted!'

                # logger.info('update_account_from_calendar_view:- saved new account')
                bank_accounts = BankAccount.objects.filter(owner=request.user)
                return render_to_response('budget/snippet__bank_accounts.html', {'bank_accounts': bank_accounts,
                                                                                 'result_message': result_message,
                                                                                 'result_success': result_success})

        return HttpResponse(jsonpickle.encode('{ "error": "No action" }'), content_type="application/json")

    except Exception as e:
        return HttpResponse(jsonpickle.encode('{ "Exception": "%s"}' % e.message), content_type="application/json")


# region Helper functions


def generate_categorymap(owner):
    # Category Map
    categorymap = []
    for pt in PaymentType.objects.filter(owner=owner).order_by('name'):
        categorymap.append([pt.id])
        for c in pt.category_set.filter(owner=owner).order_by('name'):
            categorymap.append([pt.id, c.id])
            for sc in c.subcategory_set.filter(owner=owner).order_by('name'):
                categorymap.append([pt.id, c.id, sc.id])
    return categorymap


def build_payment_frequency(p, cleaned_data):
    if p.schedule is None:
        ps = PaymentSchedule()
        logger.info('build_payment_frequency:- new schedule')
    else:
        ps = p.schedule
        logger.info('build_payment_frequency:- existing schedule')

    ps.next_date = cleaned_data['next_date']
    ps.frequency = PaymentScheduleFrequency.objects.get(pk=cleaned_data['schedule_frequency'])
    logger.info('build_payment_frequency:- frequency: %s' % ps.frequency.name)

    # Weekly fields
    ps.weekly_dow_mon = cleaned_data['weekly_dow_mon']
    ps.weekly_dow_tue = cleaned_data['weekly_dow_tue']
    ps.weekly_dow_wed = cleaned_data['weekly_dow_wed']
    ps.weekly_dow_thu = cleaned_data['weekly_dow_thu']
    ps.weekly_dow_fri = cleaned_data['weekly_dow_fri']
    ps.weekly_dow_sat = cleaned_data['weekly_dow_sat']
    ps.weekly_dow_sun = cleaned_data['weekly_dow_sun']
    ps.weekly_frequency = int(cleaned_data['weekly_frequency']) if cleaned_data['weekly_frequency'] else 0

    # Monthly fields
    ps.monthly_dom = int(cleaned_data['monthly_dom']) if cleaned_data['monthly_dom'] else 0
    ps.monthly_frequency = int(cleaned_data['monthly_frequency']) if cleaned_data['monthly_frequency'] else 0
    ps.monthly_wom = int(cleaned_data['monthly_wom']) if cleaned_data['monthly_wom'] else 0
    ps.monthly_dow = int(cleaned_data['monthly_dow']) if cleaned_data['monthly_dow'] else 0
    # ps.last_payment_date = date.max

    # Annual fields
    ps.annual_dom = int(cleaned_data['annual_dom']) if cleaned_data['annual_dom'] else 0
    ps.annual_moy = int(cleaned_data['annual_moy']) if cleaned_data['annual_moy'] else 0
    ps.annual_frequency = int(cleaned_data['annual_frequency']) if cleaned_data['annual_frequency'] else 0

    logger.info('build_payment_frequency:- about to full_clean')
    ps.full_clean()
    logger.info('build_payment_frequency:- full_clean complete')
    ps.save()

    if not p.schedule:
        p.schedule = ps
    logger.info('build_payment_frequency:- leaving')


def recalculate_next_payment(schedule):
    rr = recalculate_next_n_payments(schedule, 1)
    if rr:
        schedule.next_date = rr[0].date()
        schedule.save()


def recalculate_next_n_payments(schedule, n):
    return recalculate_next_n_m(schedule, 'count', num=n)


def recalculate_next_n_months(schedule, n):
    return recalculate_next_n_m(schedule, 'months', num=n)


def recalculate_from_to(schedule, start_date, end_date):
    return recalculate_next_n_m(schedule, 'from_to', start_date=start_date, end_date=end_date)


def recalculate_until(schedule, end_date):
    return recalculate_next_n_m(schedule, 'until', end_date=end_date)


def recalculate_next_n_m(schedule, recalc_type, num=0, start_date=None, end_date=None):
    # Check params
    if (recalc_type == 'count' or recalc_type == 'months') and num == 0:
        raise RuntimeError("recalculate_payments: num must be specified")
    if recalc_type == 'from_to' and (start_date is None or end_date is None):
        raise RuntimeError("recalculate_payments: start_date and end_date must be specified")
    if recalc_type == 'until' and end_date is None:
        raise RuntimeError("recalculate_payments: end_date must be specified")

    if schedule.frequency.name == 'Monthly':
        # Specific day of month
        if schedule.monthly_dom != 0:
            if recalc_type == 'count':
                rr = rrule(MONTHLY, dtstart=schedule.next_date, count=num,
                           bymonthday=schedule.monthly_dom, interval=schedule.monthly_frequency)
            elif recalc_type == 'months':
                rr = rrule(MONTHLY, dtstart=schedule.next_date,
                           until=schedule.next_date + relativedelta(months=num),
                           bymonthday=schedule.monthly_dom, interval=schedule.monthly_frequency)
            elif recalc_type == 'from_to':
                rr = rrule(MONTHLY, dtstart=max(start_date, schedule.next_date), until=end_date,
                           bymonthday=schedule.monthly_dom, interval=schedule.monthly_frequency)
            elif recalc_type == 'until':
                rr = rrule(MONTHLY, dtstart=schedule.next_date, until=end_date,
                           bymonthday=schedule.monthly_dom, interval=schedule.monthly_frequency)

        # day of week
        elif schedule.monthly_wom != 0:
            if recalc_type == 'count':
                rr = rrule(MONTHLY, dtstart=schedule.next_date, count=num,
                           byweekday=weekdays[schedule.monthly_dow](schedule.monthly_wom),
                           interval=schedule.monthly_frequency)
            elif recalc_type == 'months':
                rr = rrule(MONTHLY, dtstart=schedule.next_date,
                           until=schedule.next_date + relativedelta(months=num),
                           byweekday=weekdays[schedule.monthly_dow](schedule.monthly_wom),
                           interval=schedule.monthly_frequency)
            elif recalc_type == 'from_to':
                rr = rrule(MONTHLY, dtstart=max(start_date, schedule.next_date), until=end_date,
                           byweekday=weekdays[schedule.monthly_dow](schedule.monthly_wom),
                           interval=schedule.monthly_frequency)
            elif recalc_type == 'until':
                rr = rrule(MONTHLY, dtstart=schedule.next_date, until=end_date,
                           byweekday=weekdays[schedule.monthly_dow](schedule.monthly_wom),
                           interval=schedule.monthly_frequency)

    elif schedule.frequency.name == 'Weekly':
        dow = []
        if schedule.weekly_dow_mon:
            dow.append(0)
        if schedule.weekly_dow_tue:
            dow.append(1)
        if schedule.weekly_dow_wed:
            dow.append(2)
        if schedule.weekly_dow_thu:
            dow.append(3)
        if schedule.weekly_dow_fri:
            dow.append(4)
        if schedule.weekly_dow_sat:
            dow.append(5)
        if schedule.weekly_dow_sun:
            dow.append(6)
        if recalc_type == 'count':
            rr = rrule(WEEKLY, dtstart=schedule.next_date, count=num,
                       byweekday=dow, interval=schedule.weekly_frequency)
        elif recalc_type == 'months':
            rr = rrule(WEEKLY, dtstart=schedule.next_date,
                       until=schedule.next_date + relativedelta(months=num),
                       byweekday=dow, interval=schedule.weekly_frequency)
        elif recalc_type == 'from_to':
            rr = rrule(WEEKLY, dtstart=max(start_date, schedule.next_date), until=end_date,
                       byweekday=dow, interval=schedule.weekly_frequency)
        elif recalc_type == 'until':
            rr = rrule(WEEKLY, dtstart=schedule.next_date, until=end_date,
                       byweekday=dow, interval=schedule.weekly_frequency)

    elif schedule.frequency.name == 'Annual':
        if recalc_type == 'count':
            rr = rrule(YEARLY, dtstart=schedule.next_date, count=num, bymonth=schedule.annual_moy,
                       bymonthday=schedule.annual_dom, interval=schedule.annual_frequency)
        elif recalc_type == 'months':
            rr = rrule(YEARLY, dtstart=schedule.next_date,
                       until=schedule.next_date + relativedelta(months=num), bymonth=schedule.annual_moy,
                       bymonthday=schedule.annual_dom, interval=schedule.annual_frequency)
        elif recalc_type == 'from_to':
            rr = rrule(YEARLY, dtstart=max(start_date, schedule.next_date), until=end_date, bymonth=schedule.annual_moy,
                       bymonthday=schedule.annual_dom, interval=schedule.annual_frequency)
        elif recalc_type == 'until':
            rr = rrule(YEARLY, dtstart=schedule.next_date, until=end_date, bymonth=schedule.annual_moy,
                       bymonthday=schedule.annual_dom, interval=schedule.annual_frequency)

    elif schedule.frequency.name == 'Once Off':
        rr = rrule(DAILY, count=1, dtstart=schedule.next_date)

    return list(rr)

# endregion

# region Deprecated functions


def build_payment_frequency__textual(cleaned_data):
    nth = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh", 8: "eighth",
           9: "ninth", 10: "tenth", 11: "eleventh", 12: "twelfth", 13: "thirteenth", 14: "fourteenth", 15: "fifteenth",
           16: "sixteenth", 17: "seventeenth", 18: "eighteenth", 19: "nineteenth", 20: "twentieth", 21: "twentyfirst",
           22: "twentysecond", 23: "twentythird", 24: "twentyfourth", 25: "twentyfifth", 26: "twentysixth",
           27: "twentyseventh", 28: "twentyeight", 29: "twentyninth", 30: "thirtieth", 31: "thirtyfirst"}
    weekdays = ("sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday")
    weekdays_abbrev1 = ("sun", "mon", "tue", "wed", "thu", "fri", "sat")
    weekdays_abbrev2 = ("sun", "mon", "tues", "wed", "thur", "fri", "sat")

    ps = PaymentSchedule(
        next_date=cleaned_data['next_date'],
        frequency=PaymentScheduleFrequency.objects.get(pk=cleaned_data['schedule_frequency']),
    )

    if ps.frequency.name == 'Monthly':
        periodicity_words = re.split(r'\W+', cleaned_data['periodicity'])

        dom = re.compile(r'^([0-9]+)[a-z]*$')
        if periodicity_words[0].lower() == 'the':
            periodicity_words.pop(0)

        if periodicity_words[0].lower() == 'last':
            periodicity_words.pop(0)
            if periodicity_words[0].lower() in list(weekdays) + list(weekdays_abbrev1) + list(weekdays_abbrev2):
                ps.monthly_wom = -1
                if periodicity_words[0].lower() in weekdays:
                    ps.monthly_dow = weekdays.index(periodicity_words[0].lower())
                    periodicity_words.pop(0)
                elif periodicity_words[0].lower() in weekdays_abbrev1:
                    ps.monthly_dow = weekdays_abbrev1.index(periodicity_words[0].lower())
                    periodicity_words.pop(0)
                elif periodicity_words[0].lower() in weekdays_abbrev2:
                    ps.monthly_dow = weekdays_abbrev2.index(periodicity_words[0].lower())
                    periodicity_words.pop(0)
            else:
                ps.monthly_dom = -1

        elif periodicity_words[1].lower() == 'last':
            if dom.match(periodicity_words[0]):
                if periodicity_words[2].lower() in list(weekdays) + list(weekdays_abbrev1) + list(weekdays_abbrev2):
                    ps.monthly_wom = int(dom.match(periodicity_words[0]).group(1)) * -1
                else:
                    ps.monthly_dom = int(dom.match(periodicity_words[0]).group(1)) * -1
            else:
                if periodicity_words[2].lower() in list(weekdays) + list(weekdays_abbrev1) + list(weekdays_abbrev2):
                    ps.monthly_wom = nth.keys()[nth.values().index(periodicity_words[0])] * -1
                else:
                    ps.monthly_dom = nth.keys()[nth.values().index(periodicity_words[0])] * -1
            periodicity_words.pop(0)
            periodicity_words.pop(0)

        elif periodicity_words[0].lower() == 'first':
            ps.monthly_wom = 1
            periodicity_words.pop(0)
            if periodicity_words[0].lower() in weekdays:
                ps.monthly_dow = weekdays.index(periodicity_words[0].lower())
                periodicity_words.pop(0)
            elif periodicity_words[0].lower() in weekdays_abbrev1:
                ps.monthly_dow = weekdays_abbrev1.index(periodicity_words[0].lower())
                periodicity_words.pop(0)
            elif periodicity_words[0].lower() in weekdays_abbrev2:
                ps.monthly_dow = weekdays_abbrev2.index(periodicity_words[0].lower())
                periodicity_words.pop(0)

        else:
            if dom.match(periodicity_words[0]):
                if periodicity_words[1].lower() in list(weekdays) + list(weekdays_abbrev1) + list(weekdays_abbrev2):
                    ps.monthly_wom = int(dom.match(periodicity_words[0]).group(1))
                else:
                    ps.monthly_dom = int(dom.match(periodicity_words[0]).group(1))
            else:
                if periodicity_words[1].lower() in list(weekdays) + list(weekdays_abbrev1) + list(weekdays_abbrev2):
                    ps.monthly_wom = nth.keys()[nth.values().index(periodicity_words[0])]
                else:
                    ps.monthly_dom = nth.keys()[nth.values().index(periodicity_words[0])]
            periodicity_words.pop(0)

        if periodicity_words[0].lower() == 'day':
            periodicity_words.pop(0)
        elif periodicity_words[0].lower() in weekdays:
            ps.monthly_dow = weekdays.index(periodicity_words[0].lower())
            periodicity_words.pop(0)
        elif periodicity_words[0].lower() in weekdays_abbrev1:
            ps.monthly_dow = weekdays_abbrev1.index(periodicity_words[0].lower())
            periodicity_words.pop(0)
        elif periodicity_words[0].lower() in weekdays_abbrev2:
            ps.monthly_dow = weekdays_abbrev2.index(periodicity_words[0].lower())
            periodicity_words.pop(0)

        if periodicity_words[0].lower() == 'of' \
                and (periodicity_words[1].lower() in ('each', 'every', 'the')):
            periodicity_words.pop(0)
            periodicity_words.pop(0)

        if periodicity_words[0].lower() != 'month':
            if dom.match(periodicity_words[0]):
                ps.monthly_frequency = int(dom.match(periodicity_words[0]).group(1))
            else:
                ps.monthly_frequency = nth.keys()[nth.values().index(periodicity_words[0])]

    return ps

# endregion
