from decimal import Decimal
from operator import itemgetter

import jsonpickle
import json
from django.core.serializers.json import DjangoJSONEncoder
from dateutil.rrule import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Max
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.defaultfilters import date as _date
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.decorators import method_decorator
from django.utils.translation import get_language
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import ListView

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
        return Payment.objects.filter(owner=self.request.user, active=True)

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
        context["manage_payment_types"] = jsonpickle.encode(
            dict(zip(list(o.pk for o in PaymentType.objects.filter(owner=self.request.user, active=True).all())
                     , list(o.name for o in PaymentType.objects.filter(owner=self.request.user, active=True).all()))))
        context["manage_categories"] = jsonpickle.encode(
            dict(zip(list(o.pk for o in Category.objects.filter(owner=self.request.user, active=True).all())
                     , list(o.name for o in Category.objects.filter(owner=self.request.user, active=True).all()))))
        context["manage_subcategories"] = jsonpickle.encode(
            dict(zip(list(o.pk for o in SubCategory.objects.filter(owner=self.request.user, active=True).all())
                     , list(o.name for o in SubCategory.objects.filter(owner=self.request.user, active=True).all()))))
        context["categorymap"] = jsonpickle.encode(generate_categorymap(self.request.user))
        context["userLanguage"] = get_language()
        context["calendar_search_terms"] = generate_calendar_search_terms(self.request.user)
        return context


@login_required
@ensure_csrf_cookie
def get_payments(request):
    try:
        if request.method == 'POST':
            payments = Payment.objects.filter(owner=request.user, active=True)
            response_data = {'data': []}

            for payment in payments:
                response_data['data'].append(
                    {
                        'payment_id': payment.pk,
                        'payment_type_id': payment.payment_type.id if payment.payment_type else -1,
                        'payment_type': payment.payment_type.name if payment.payment_type else '',
                        'category_id': payment.category.id if payment.category else -1,
                        'category': payment.category.name if payment.category else '',
                        'subcategory_id': payment.subcategory.id if payment.subcategory else -1,
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
    response_data = {}
    try:
        if request.method != 'POST':
            raise RuntimeError('Invalid request')

        if 'action' not in request.POST:
            raise RuntimeError('No action specified')

        action = request.POST['action']
        snippet = 'budget/' + (request.POST['snippet'] if 'snippet' in request.POST else 'snippet__update_payment.html')
        logger.debug('update_payment:- entering with action: %s, snippet: %s, content: %s'
                     % (action, snippet, request.POST))

        # if this is the initial viewing of the form
        if action == 'blank':
            logger.debug('update_payment:- initial viewing')
            form_data = {}

            # look for defaults
            if 'title' in request.POST:
                form_data = {'title': request.POST['title']}
            form_data['offset'] = 0

            form = PaymentForm(request.user, form_data)
            return render_to_response(
                snippet, {'form': form, 'categorymap': jsonpickle.encode(generate_categorymap(request.user))})

        # Save the updated payment details
        result_message = 'Payment Saved!'
        result_success = 'pass'
        form = PaymentForm(request.user, request.POST)

        if action == 'update':
            # check whether it's valid:
            if not form.is_valid():
                raise ValidationError(form.errors.as_json())

            category = Category.objects.get(pk=form.cleaned_data['category']) \
                if 'category' in form.cleaned_data and form.cleaned_data['category'] else None
            subcategory = SubCategory.objects.get(pk=form.cleaned_data['subcategory']) \
                if 'subcategory' in form.cleaned_data and form.cleaned_data['subcategory'] else None

            # new payment
            if form.cleaned_data['payment_id'] == '':
                logger.debug('update_payment:- new payment: %s' % form.cleaned_data["title"])
                if Payment.objects.filter(owner=request.user, active=True,
                                          title__iexact=form.cleaned_data['title']).count() > 0:
                    # title must be unique for user
                    raise ValidationError('Payment of that name already exists')

                p = Payment(
                    title=form.cleaned_data["title"],
                    amount=form.cleaned_data["amount"],
                    in_out=form.cleaned_data["in_out"],
                    payment_type=PaymentType.objects.get(pk=form.cleaned_data['payment_type']),
                    category=category,
                    subcategory=subcategory,
                    schedule=build_payment_frequency('', form.cleaned_data),
                    owner=request.user,
                    account=BankAccount.objects.get(pk=form.cleaned_data['account']),
                )

                # linked payments
                if int(form.cleaned_data['schedule_frequency']) == PaymentScheduleFrequency.objects.get(name__exact='Linked to Other Payment').id:
                    if 'linked_to' not in request.POST:
                        raise ValidationError('Linked to payment not specified')

                    mp = Payment.objects.get(owner=request.user, active=True, pk=int(form.cleaned_data['linked_to']))
                    if mp is None:
                        raise ValidationError('Linked to payment does not exist')
                    if mp.id == p.id:
                        raise ValidationError('Payment cannot be linked to itself')

                    p.parent_payment=mp
                    p.offset=int(form.cleaned_data['offset'])
                    p.offset_type=form.cleaned_data['offset_type']
                    # Update next_date
                    kwargs = {}
                    kwargs[p.offset_type] = p.offset
                    payment_date = schedule_rrule(p).after(datetime(year=p.schedule.next_date.year,
                                                                    month=p.schedule.next_date.month,
                                                                    day=p.schedule.next_date.day), True).date()
                    p.schedule.next_date = payment_date + relativedelta(**kwargs)
                    p.schedule.save()

                p.save()

            # existing payment
            else:
                if Payment.objects.filter(owner=request.user, active=True, title__iexact=form.cleaned_data['title']) \
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
                p.account = BankAccount.objects.get(pk=form.cleaned_data['account'])
                build_payment_frequency(p.schedule, form.cleaned_data)
                p.save()

            response_data['result_message'] = result_message
            response_data['result_success'] = result_success
            response_data['search_terms'] = generate_calendar_search_terms(request.user)
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

        p = Payment.objects.filter(owner=request.user, active=True).get(pk=request.POST['payment_id'])
        if p is None:
            # specified payment not found
            raise RuntimeError('Specified payment not found')

        if action == 'delete':
            logger.debug('update_payment:- deleting %d' % p.id)
            p.active = False
            p.save()
            response_data['result_message'] = 'Payment deleted!'
            response_data['result_success'] = 'pass'
            response_data['search_terms'] = generate_calendar_search_terms(request.user)
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
                'is_exclusion': PaymentScheduleExclusion.objects.filter(owner=request.user,
                                                                        exclusion_payment=p).exists(),

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
        error_message = '{ "Exception": "%s" }' % \
                        (e.messages if hasattr(e, 'messages') else e.message)
        logger.error(error_message)
        response_data['result_success'] = 'fail'
        response_data['result_message'] = error_message
        return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")


@login_required
@ensure_csrf_cookie
def update_payment_date(request):
    try:
        response_data = {}

        if request.method != 'POST':
            raise RuntimeError('Invalid request')

        # Check for revert action
        if 'action' in request.POST and request.POST['action'] == 'revert':
            pid = request.POST['payment_id']
            logger.debug('update_payment_date:- reverting payment id %s' % (pid))
            pe = PaymentScheduleExclusion.objects.filter(owner=request.user, active=True,
                                                         exclusion_payment__pk=pid).get()
            if pe is None:
                raise RuntimeError('Specified excluded payment not found')
            pe.active = False
            pe.save()

            p = Payment.objects.filter(owner=request.user, active=True)\
                .exclude(exclusion_payment__isnull=True)\
                .get(pk=request.POST['payment_id'])
            if p is None:
                raise RuntimeError('Specified payment not found')
            p.active = False
            p.save()

            response_data['result_message'] = 'Payment reverted successfully!'
            response_data['result_success'] = 'pass'
            return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")

        result_message = 'Payment Saved!'
        result_success = 'pass'
        form = PaymentDateForm(request.user, request.POST)

        # check whether it's valid:
        if not form.is_valid():
            logger.error('update_payment_date:- form invalid, form.errors: %s' % form.errors.as_json())
            raise ValidationError(form.errors.as_json())

        p = Payment.objects.filter(owner=request.user, active=True).get(pk=form.cleaned_data['payment_id'])
        if p is None:
            # specified payment not found
            raise RuntimeError('Specified payment not found')
        logger.debug('update_payment_date:- updating payment: %s' % request.POST)

        response_data['result_message'] = result_message
        response_data['result_success'] = result_success
        response_data['form_data'] = form.cleaned_data

        # if only updating single instance, then add to exclusions and create one-off
        if request.POST['series_choice'] == 'this':
            logger.info('update_payment_date:- updating single instance')
            new_schedule = PaymentSchedule(
                next_date=form.cleaned_data['next_date'],
                frequency=PaymentScheduleFrequency.objects.get(name__exact='Once Off'),
            )
            new_schedule.save()
            new_payment = Payment(
                title=p.title + ' - ' + _date(form.cleaned_data['next_date'], 'SHORT_DATE_FORMAT'),
                in_out=p.in_out,
                amount=p.amount,
                payment_type=p.payment_type,
                category=p.category,
                subcategory=p.subcategory,
                account=p.account,
                schedule=new_schedule,
                owner=request.user
            )
            new_payment.save()
            new_exclusion = PaymentScheduleExclusion(
                main_payment=p,
                exclusion_payment=new_payment,
                exclusion_date=parse_date(request.POST['original_date']),
                owner=request.user
            )
            logger.info('update_payment_date:- raw date: %s, exclusion_date: %s'
                        % (request.POST['original_date'], str(new_exclusion.exclusion_date)))
            new_exclusion.save()
            response_data['form_data']['schedule_frequency'] = new_payment.schedule.frequency.name
            response_data['form_data']['payment_id'] = new_payment.pk
            response_data['form_data']['next_date'] = new_payment.schedule.next_date.strftime('%d/%m/%Y')

        # otherwise, update existing schedule
        else:
            logger.info('update_payment_date:- existing schedule: id %s' % (p.schedule.id))

            # linked payments
            if int(form.cleaned_data['schedule_frequency']) == PaymentScheduleFrequency.objects.get(
                    name__exact='Linked to Other Payment').id:
                if 'linked_to' not in request.POST:
                    raise ValidationError('Linked to payment not specified')

                mp = Payment.objects.get(owner=request.user, active=True, pk=int(form.cleaned_data['linked_to']))
                if mp is None:
                    raise ValidationError('Linked to payment does not exist')
                if mp.id == p.id:
                    raise ValidationError('Payment cannot be linked to itself')

                p.parent_payment = mp
                p.schedule.frequency = PaymentScheduleFrequency.objects.\
                    get(pk=int(form.cleaned_data['schedule_frequency']))
                p.offset = int(form.cleaned_data['offset'])
                p.offset_type = form.cleaned_data['offset_type']
                # Update next_date
                kwargs = {}
                kwargs[p.offset_type] = p.offset
                next_date =  form.cleaned_data['next_date']
                payment_date = schedule_rrule(p).after(datetime(year=next_date.year, month=next_date.month,
                                                                day=next_date.day), inc=True).date()
                p.schedule.next_date = payment_date + relativedelta(**kwargs)
                p.schedule.save()

            else:
                build_payment_frequency(p.schedule, form.cleaned_data)

            p.save()
            response_data['form_data']['schedule_frequency'] = p.schedule.frequency.name
            response_data['form_data']['payment_id'] = p.pk
            response_data['form_data']['next_date'] = p.schedule.next_date.strftime('%d/%m/%Y')

        return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")

    except Exception as e:
        error_message = '{ "Exception": "%s" }' % \
                        (e.messages if hasattr(e, 'messages') else e.message)
        logger.error('update_payment_date:- Exception: %s' % error_message)
        response_data['result_success'] = 'fail'
        response_data['result_message'] = error_message
        return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")


@login_required
@ensure_csrf_cookie
def update_payment_classification(request):
    logger.debug('update_payment_classification:- entering with: %s' % (request.POST))
    try:
        response_data = {}

        if request.method != 'POST':
            raise RuntimeError('Invalid request')

        # Save the updated payment details
        response_data['result_message'] = 'Payment Saved!'
        response_data['result_success'] = 'pass'
        form = PaymentClassificationForm(request.user, request.POST)

        # check whether it's valid:
        if not form.is_valid():
            raise ValidationError(form.errors.as_json())

        category = Category.objects.get(pk=form.cleaned_data['category']) \
            if 'category' in form.cleaned_data and form.cleaned_data['category'] else None
        subcategory = SubCategory.objects.get(pk=form.cleaned_data['subcategory']) \
            if 'subcategory' in form.cleaned_data and form.cleaned_data['subcategory'] else None

        p = Payment.objects.filter(owner=request.user, active=True).get(pk=form.cleaned_data['payment_id'])
        if p is None:
            # specified payment not found
            raise RuntimeError('Specified payment not found')

        p.payment_type = PaymentType.objects.get(pk=form.cleaned_data['payment_type'])
        p.category = category
        p.subcategory = subcategory
        p.save()
        logger.debug('update_payment_classification:- returning: %s' % (jsonpickle.encode(response_data)))

        return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")

    except Exception as e:
        error_message = '{ "Exception type": "%s", "Exception": "%s" }' % \
                        (str(type(e)), e.messages if 'messages' in e else e.message)
        logger.error(error_message)
        return HttpResponse(error_message, content_type="application/json")


@login_required
@ensure_csrf_cookie
def update_payment_partial(request):
    # if this is a POST request we need to process the form data
    response_data = {}
    try:
        if request.method != 'POST':
            raise RuntimeError('Invalid request')

        logger.debug('update_payment_partial:- entering with content: %s' % request.POST)

        # Save the updated payment details
        result_message = 'Payment Saved!'
        result_success = 'pass'
        if 'field' not in request.POST:
            raise RuntimeError('Missing field directive')
        if 'value' not in request.POST:
            raise RuntimeError('Missing value directive')
        if 'single_series' not in request.POST:
            raise RuntimeError('Missing single/series directive')
        if 'single_series' in request.POST and request.POST['single_series'] == 'single' \
                and 'payment_date' not in request.POST:
            raise RuntimeError('Single payment updates required payment_date')
        if 'payment_id' not in request.POST:
            raise RuntimeError('Missing payment_id')

        p = Payment.objects.filter(owner=request.user, active=True).get(pk=request.POST['payment_id'])
        if p is None:
            # specified payment not found
            raise RuntimeError('Specified payment not found')

        if request.POST['single_series'] == 'series':
            logger.debug('update_payment_partial:- updating series for %s to %s'
                         % (request.POST['field'], request.POST['value']))
            if request.POST['field'] == 'title':
                p.title = request.POST['value']
            elif request.POST['field'] == 'outgoing':
                p.in_out = 'o'
                p.amount = request.POST['value']
            elif request.POST['field'] == 'incoming':
                p.in_out = 'i'
                p.amount = request.POST['value']
            elif request.POST['field'] == 'account_id':
                p.account = BankAccount.objects.filter(owner=request.user, active=True).get(pk=request.POST['value'])
            p.save()

        elif request.POST['single_series'] == 'single':
            logger.debug('update_payment_partial:- updating single payment for %s to %s on %s'
                         % (request.POST['field'], request.POST['value'], request.POST['payment_date']))
            new_schedule = PaymentSchedule(
                next_date=parse_date(request.POST['payment_date']),
                frequency=PaymentScheduleFrequency.objects.get(name__exact='Once Off'),
            )
            new_schedule.save()
            new_payment = Payment.objects.filter(owner=request.user, active=True).get(pk=request.POST['payment_id'])
            new_payment.pk = None
            new_payment.title = p.title + ' - ' + _date(parse_date(request.POST['payment_date']), 'SHORT_DATE_FORMAT')
            new_payment.schedule=new_schedule
            if request.POST['field'] == 'title':
                new_payment.title = request.POST['value']
            elif request.POST['field'] == 'outgoing':
                new_payment.in_out = 'o'
                new_payment.amount = request.POST['value']
            elif request.POST['field'] == 'incoming':
                new_payment.in_out = 'i'
                new_payment.amount = request.POST['value']
            elif request.POST['field'] == 'account_id':
                new_payment.account = BankAccount.objects.filter(owner=request.user, active=True).get(
                    pk=request.POST['value'])
            new_payment.save()
            new_exclusion = PaymentScheduleExclusion(
                main_payment=p,
                exclusion_payment=new_payment,
                exclusion_date=parse_date(request.POST['payment_date']),
                owner=request.user
            )
            new_exclusion.save()

        response_data['result_message'] = result_message
        response_data['result_success'] = result_success
        response_data['search_terms'] = generate_calendar_search_terms(request.user)
        return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")

    except Exception as e:
        error_message = '{ "Exception type": "%s", "Exception": "%s" }' % \
                        (str(type(e)), e.messages if hasattr(e, 'messages') else e.message)
        logger.error(error_message)
        response_data['result_message'] = 'update_payment_partial: ' + error_message
        response_data['result_success'] = 'fail'
        return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")


@login_required
@ensure_csrf_cookie
def manage_categories(request):
    logger.info('manage_categories:- entering: %s' % request.POST)
    try:
        if request.method != 'POST':
            raise RuntimeError('Invalid request')

        context = dict()
        context['result_success'] = 'pass'
        context['result_message'] = 'Categories updated!'
        form_data = {}

        if 'new_payment_type' in request.POST:
            if PaymentType.objects.filter(owner=request.user, name__iexact=request.POST['new_payment_type'],
                                          active=True).count() > 0:
                raise ValidationError('Payment Type of that name already exists')
            pt = PaymentType(name=request.POST['new_payment_type'], owner=request.user)
            pt.save()
            form_data["updated_payment_type"] = request.POST['new_payment_type']

        elif 'new_category' in request.POST:
            if Category.objects.filter(owner=request.user, name__iexact=request.POST['new_category'],
                                       active=True).count() > 0:
                raise ValidationError('Category of that name already exists')
            if 'payment_type' not in request.POST:
                raise ValidationError('Payment Type not specified')
            pt = PaymentType.objects.get(pk=request.POST['payment_type'], owner=request.user)
            c = Category(name=request.POST['new_category'], payment_type=pt, owner=request.user)
            c.save()
            form_data['selected_payment_type'] = pt.name
            form_data['updated_category'] = request.POST['new_category']

        elif 'new_subcategory' in request.POST:
            if SubCategory.objects.filter(owner=request.user, name__iexact=request.POST['new_subcategory'],
                                          active=True).count() > 0:
                # name must be unique for user
                raise RuntimeError('Subcategory of that name already exists')
            if 'category' not in request.POST:
                raise ValidationError('Category not specified')
            c = Category.objects.get(pk=request.POST['category'], owner=request.user)
            sc = SubCategory(name=request.POST['new_subcategory'], category=c, owner=request.user)
            sc.save()
            form_data['selected_payment_type'] = c.payment_type.name
            form_data['selected_category'] = c.name
            form_data['updated_subcategory'] = request.POST['new_subcategory']

        elif 'delete_payment_type' in request.POST:
            pt = PaymentType.objects.get(pk=request.POST['delete_payment_type'], owner=request.user)
            pt.active = False
            pt.save()

        elif 'delete_category' in request.POST:
            c = Category.objects.get(pk=request.POST['delete_category'], owner=request.user)
            c.active = False
            c.save()

        elif 'delete_subcategory' in request.POST:
            sc = SubCategory.objects.get(pk=request.POST['delete_subcategory'], owner=request.user)
            sc.active = False
            sc.save()

        elif 'edit_payment_type_id' in request.POST:
            if PaymentType.objects.filter(owner=request.user) \
                    .filter(name__iexact=request.POST['edit_payment_type_name']).count() > 0:
                # name must be unique for user
                raise RuntimeError('Payment Type of that name already exists')

            pt = PaymentType.objects.get(pk=request.POST['edit_payment_type_id'], owner=request.user)
            pt.name = request.POST['edit_payment_type_name']
            pt.save()
            form_data['updated_payment_type'] = request.POST['edit_payment_type_name']

        elif 'edit_category_id' in request.POST:
            if Category.objects.filter(owner=request.user).filter(name__iexact=request.POST['edit_category_name']) \
                    .count() > 0:
                # name must be unique for user
                raise RuntimeError('Category of that name already exists')

            c = Category.objects.get(pk=request.POST['edit_category_id'], owner=request.user)
            c.name = request.POST['edit_category_name']
            c.save()
            form_data['updated_category'] = request.POST['edit_category_name']

        elif 'edit_subcategory_id' in request.POST:
            if SubCategory.objects.filter(owner=request.user) \
                    .filter(name__iexact=request.POST['edit_subcategory_name']).count() > 0:
                # name must be unique for user
                raise RuntimeError('Subcategory of that name already exists')

            sc = SubCategory.objects.get(pk=request.POST['edit_subcategory_id'], owner=request.user)
            sc.name = request.POST['edit_subcategory_name']
            sc.save()
            form_data['updated_subcategory'] = request.POST['edit_subcategory_name']

        elif 'new_payment_type_for_category' in request.POST:
            pt = PaymentType.objects.get(pk=request.POST['new_payment_type_for_category'], owner=request.user)
            c = Category.objects.get(pk=request.POST['category_id'], owner=request.user)
            c.payment_type = pt
            c.save()
            form_data["updated_category"] = c.name
            form_data['selected_payment_type'] = pt.name
            Payment.objects.filter(category=c).update(payment_type=pt)

        elif 'new_category_for_subcategory' in request.POST:
            c = Category.objects.get(pk=request.POST['new_category_for_subcategory'], owner=request.user)
            sc = SubCategory.objects.get(pk=request.POST['subcategory_id'], owner=request.user)
            sc.category = c
            sc.save()
            form_data["updated_subcategory"] = sc.name
            form_data['selected_category'] = c.name
            Payment.objects.filter(subcategory=sc).update(category=c, payment_type=c.payment_type)

        if 'curr_payment_type' in request.POST:
            form_data['selected_payment_type'] = request.POST['curr_payment_type']
        if 'curr_category' in request.POST:
            form_data['selected_category'] = request.POST['curr_category']
        if 'curr_subcategory' in request.POST:
            form_data['selected_subcategory'] = request.POST['curr_subcategory']

        updated_payments = []
        for p in Payment.objects.filter(owner=request.user, active=True):
            updated_payments.append(
                {
                    'payment_id': p.pk,
                    'payment_type_id': p.payment_type.id if p.payment_type else -1,
                    'payment_type': p.payment_type.name if p.payment_type else '',
                    'category_id': p.category.id if p.category else -1,
                    'category': p.category.name if p.category else '',
                    'subcategory_id': p.subcategory.id if p.subcategory else -1,
                    'subcategory': p.subcategory.name if p.subcategory else '',
                }
            )

        context['form'] = CategoriesForm(request.user, form_data)
        context["categorymap"] = jsonpickle.encode(generate_categorymap(request.user))
        context["manage_payment_types"] = dict(zip(list(o.pk for o in PaymentType.objects.filter(owner=request.user, active=True).all())
                                               , list(o.name for o in PaymentType.objects.filter(owner=request.user, active=True).all())))
        context["manage_categories"] = dict(zip(list(o.pk for o in Category.objects.filter(owner=request.user, active=True).all())
                                               , list(o.name for o in Category.objects.filter(owner=request.user, active=True).all())))
        context["manage_subcategories"] = dict(zip(list(o.pk for o in SubCategory.objects.filter(owner=request.user, active=True).all())
                                               , list(o.name for o in SubCategory.objects.filter(owner=request.user, active=True).all())))
        context['payments'] = jsonpickle.encode(updated_payments)
        return render_to_response('budget/snippet__manage_categories.html', context)

    except Exception as e:
        error_message = 'manage_categories:- buzz! %s' % (e.messages if hasattr(e, 'messages') else e.message)
        logger.error(error_message)
        context['result_message'] = error_message
        context['result_success'] = 'fail'
        return render_to_response('budget/snippet__manage_categories.html', context)


@login_required
@ensure_csrf_cookie
def generate_calendar_view(request):
    logger.info('generate_calendar_view: entering with %s' % request.POST)
    response_data = dict()
    try:
        if request.method != 'POST':
            raise RuntimeError('Invalid request')

        # start and end date required
        if 'start_date' not in request.POST or 'end_date' not in request.POST:
            raise RuntimeError('Missing start and/or end date: %s' % request.POST)
        start_date = parse_date(request.POST['start_date'])
        end_date = parse_date(request.POST['end_date'])

        # Check to see if we're marking a calendar entry as paid or received
        if 'action' in request.POST and request.POST['action'] == 'update':
            p = Payment.objects.filter(owner=request.user, active=True).get(pk=request.POST['payment_id'])

            # logger.debug('generate_calendar_view: marking "%s" paid, occurrences: %d, next_date: %s, end_date: %s'
            #              % (p.title, p.schedule.occurrences, p.schedule.next_date, p.schedule.end_date))

            # If this is an exclusion payment
            if PaymentScheduleExclusion.objects.filter(owner=request.user, exclusion_payment=p).exists():
                p.active = False
                p.save()
            elif (p.schedule.end_date is not None or p.schedule.occurrences > 0) \
                    and p.schedule.next_date != parse_date(request.POST['payment_date']):
                new_next_date = schedule_rrule(p).after(parse_datetime(request.POST['payment_date'] + ' 00:00:00'))
                # logger.debug('generate_calendar_view: new_next_date: %s' % (new_next_date))

                # If not the last payment, create an exclusion and mark it as inactive
                if new_next_date is not None:
                    new_schedule = PaymentSchedule(
                        next_date=parse_date(request.POST['payment_date']),
                        frequency=PaymentScheduleFrequency.objects.get(name__exact='Once Off'),
                    )
                    new_schedule.save()
                    new_payment = Payment.objects.get(pk=p.pk)
                    new_payment.pk = None
                    new_payment.title = p.title + ' - ' + _date(request.POST['payment_date'], 'SHORT_DATE_FORMAT')
                    new_payment.schedule = new_schedule
                    new_payment.active = False
                    new_payment.save()
                    new_exclusion = PaymentScheduleExclusion(
                        main_payment=p,
                        exclusion_payment=new_payment,
                        exclusion_date=parse_date(request.POST['payment_date']),
                        owner=request.user
                    )
                    new_exclusion.save()

                # Last payment for end-dated schedules
                elif p.schedule.end_date is not None:
                    new_end_date = schedule_rrule(p).before(parse_datetime(request.POST['payment_date'] + ' 00:00:00'))
                    # logger.debug('generate_calendar_view: new_end_date: %s' % (new_end_date))
                    # If there is a penultimate payment, set it as the last payment
                    if new_end_date is not None:
                        p.schedule.end_date = new_end_date
                        p.schedule.save()
                    # There are no other payments, so make the payment inactive
                    else:
                        p.active = False
                        p.save()

                # Last payment for occurrence schedules
                else:
                    new_end_date = schedule_rrule(p).before(parse_datetime(request.POST['payment_date'] + ' 00:00:00'))
                    # logger.debug('generate_calendar_view: new_end_date for occurrence payment: %s' % (new_end_date))
                    # If there is a penultimate payment, set it as the last payment
                    if p.schedule.occurrences > 1:
                        p.schedule.occurrences -= 1
                        p.schedule.save()
                    # There are no other payments, so make the payment inactive
                    else:
                        p.active = False
                        p.save()
            else:
                new_next_date = schedule_rrule(p).after(parse_datetime(request.POST['payment_date'] + ' 00:00:00'))
                # logger.debug('generate_calendar_view: new_next_date for first payment: %s' % (new_next_date))
                if new_next_date is None:
                    p.active = False
                    p.save()
                else:
                    p.schedule.next_date = new_next_date
                    p.schedule.save()

        # Check to see if we're searching for a payment
        if 'action' in request.POST and request.POST['action'] == 'search':
            search_term = request.POST['search_term']
            logger.debug('generate_calendar_view:- Searching for: %s in %s' % (search_term, request.POST))
            if not Payment.objects.filter(owner=request.user, active=True, title__icontains=search_term).exists():
                raise RuntimeError('Cannot find "%s"' % request.POST['search_term'])

            # For each matching payment, work out the first chronological match
            p_first = (-1, date.max)
            for p in Payment.objects.filter(owner=request.user, active=True, title__icontains=search_term).order_by(
                    'title').all():
                p_next_date = schedule_rrule(p)\
                    .after(datetime(year=start_date.year, month=start_date.month, day=start_date.day), inc=True)
                if p_next_date is None:
                    raise RuntimeError('No more occurrences found')
                p_next_date = date(year=p_next_date.year, month=p_next_date.month, day=p_next_date.day)
                if p_next_date < p_first[1]:
                    p_first = (p.id, p_next_date)

            p = Payment.objects.get(pk=p_first[0])
            end_date = p_first[1]
            response_data['selected_row'] = str(p.pk) + '|' + str(end_date)

        # for each payment
        payment_calendar = []
        logger.debug('generate_calendar_view: found %i payments' % Payment.objects.filter(owner=request.user,
                                                                                          active=True).count())
        for p in Payment.objects.filter(owner=request.user, active=True):
            # logger.debug('generate_calendar_view: processing payment "%s", amount: %f, start_date: %s, end_date: %s'
            #              % (p.title, p.amount, str(start_date), str(end_date)))
            # logger.debug('generate_calendar_view: processing payment "%s", occurrences: %d, next_date: %s'
            #              % (p.title, p.schedule.occurrences, p.schedule.next_date))

            rr = schedule_rrule(p)\
                .between(datetime(year=start_date.year, month=start_date.month, day=start_date.day),
                         datetime(year=end_date.year, month=end_date.month, day=end_date.day), inc=True)
            exclusions = [e.exclusion_date for e in
                          PaymentScheduleExclusion.objects.filter(owner=request.user, main_payment=p)]

            if rr:
                for i in range(0, len(rr)):
                    payment_date = rr[i].date()
                    if payment_date in exclusions:
                        continue
                    if p.schedule.frequency.name == 'Linked to Other Payment':
                        kwargs = {}
                        kwargs[p.offset_type] = p.offset
                        payment_date += relativedelta(**kwargs)
                        if p.schedule.next_date > payment_date \
                                or (p.schedule.end_date is not None and payment_date > p.schedule.end_date) \
                                or (p.schedule.occurrences != 0 and i >= p.schedule.occurrences):
                            continue

                    # logger.debug('generate_calendar_view: payment_calendar.append %i of %i: %s, date: %s, amount: %d'
                    #   % (i + 1, len(rr), p.title, str(payment_date), p.amount))
                    payment_calendar.append({
                        'row_id': str(p.pk) + '|' + str(payment_date),
                        'payment_date': str(payment_date),
                        'payment_type_id': p.payment_type.id if p.payment_type else -1,
                        'payment_type': p.payment_type.name if p.payment_type else '',
                        'category_id': p.category.id if p.category else -1,
                        'category': p.category.name if p.category else '',
                        'subcategory_id': p.subcategory.id if p.subcategory else -1,
                        'subcategory': p.subcategory.name if p.subcategory else '',
                        'account': p.account.title,
                        'account_type': p.account.account_type,
                        'amount_value': p.amount,
                        'amount': str(p.amount),
                        'title': p.title,
                        'in_out': p.in_out,
                        'payment_id': p.pk
                    })


        # Current balance (actual balance) = balance of debit accounts
        # - credit and virtual accounts ignored as they only impact budget balance
        # logger.debug('generate_calendar_view: about to calculate curr_balance: %s' % (
        #     'not there' if 'final_balance' not in request.POST else 'is there'))
        if 'final_balance' not in request.POST:
            curr_balance = \
            BankAccount.objects.filter(owner=request.user, active=True, account_type__exact='debit').aggregate(
                Sum('current_balance'))['current_balance__sum'] \
                if BankAccount.objects.filter(owner=request.user, active=True, account_type__exact='debit').exists() \
                else 0
            curr_balance -= \
                BankAccount.objects.filter(owner=request.user, active=True, account_type__exact='virtual').aggregate(
                    Sum('current_balance'))['current_balance__sum'] \
                    if BankAccount.objects.filter(owner=request.user, active=True, account_type__exact='virtual').exists() \
                    else 0
        else:
            curr_balance = Decimal(request.POST['final_balance'])
        if 'final_budget_balance' not in request.POST:
            curr_budget_balance = curr_balance - \
                (BankAccount.objects.filter(owner=request.user, active=True, account_type__exact='virtual').aggregate(
                Sum('current_balance'))['current_balance__sum'] \
                if BankAccount.objects.filter(owner=request.user, active=True, account_type__exact='virtual').exists() \
                else 0)
        else:
            curr_budget_balance = Decimal(request.POST['final_budget_balance'])
        # logger.debug('generate_calendar_view: curr_balance: %f, curr_budget_balance: %f' % (curr_balance, curr_budget_balance))

        # Initialise account balances
        bank_balance = {}
        for ba in BankAccount.objects.filter(owner=request.user, active=True):
            bank_balance[ba.title] = ba.current_balance

        sorted_payment_calendar = sorted(payment_calendar, key=itemgetter('payment_date'))
        for pc in sorted_payment_calendar:
            if 'amount' not in pc or pc['amount_value'] is None:
                logger.error('generate_calendar_view:- no amount: %s' % pc)
            # logger.debug('generate_calendar_view: curr_budget_balance: %s, curr_balance: %s, amount_value: %s'
            #              % (curr_budget_balance, curr_balance, pc['amount_value']))

            curr_budget_balance += pc['amount_value'] * (1 if pc['in_out'] == 'i' else -1)
            if pc['account_type'] == 'debit':
                curr_balance += pc['amount_value'] * (1 if pc['in_out'] == 'i' else -1)
            bank_balance[pc['account']] += pc['amount_value'] * (1 if pc['in_out'] == 'i' else -1)

            pc['curr_balance'] = str(curr_balance)
            pc['curr_budget_balance'] = str(curr_budget_balance)
            if 'bank_balance' not in pc:
                pc['bank_balance'] = {}
            pc['bank_balance'][pc['account']] = bank_balance[pc['account']]

        if len(sorted_payment_calendar):
            response_data['final_balance'] = sorted_payment_calendar[-1]['curr_balance']
            response_data['final_budget_balance'] = sorted_payment_calendar[-1]['curr_budget_balance']
            # Min account balances & dates
            bank_balance_obj = {}
            accs = list(set(item['account'] for item in sorted_payment_calendar))
            for acc in accs:
                bank_balance_obj[acc] = {}
                bank_balance_obj[acc]['amount'] = min(
                    item['bank_balance'][acc] for item in sorted_payment_calendar if item['account'] == acc)
                bank_balance_obj[acc]['payment_date'] = \
                    (item['payment_date'] for item in sorted_payment_calendar if
                     item['account'] == acc and
                     item['bank_balance'][acc] == bank_balance_obj[acc]['amount']).next()
                # logger.debug('generate_calendar_view: response_data[bank_balance]: %s: %s'
                #              % (acc, response_data['bank_balance'][acc]))
                response_data['bank_balance__min'] = json.dumps(bank_balance_obj, cls=DjangoJSONEncoder)

        else:
            response_data['final_balance'] = str(curr_balance)
            response_data['final_budget_balance'] = str(curr_budget_balance)

        response_data['result_success'] = 'pass'
        response_data['calendar_end_date'] = str(end_date)
        response_data['data'] = sorted_payment_calendar
        return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")

    except Exception as e:
        error_message = e.messages if hasattr(e, 'messages') else e.message
        logger.error(error_message)
        response_data['result_message'] = error_message
        response_data['result_success'] = 'fail'
        return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")


@login_required
@ensure_csrf_cookie
def bank_account_view(request):
    logger.info('bank_account_view:- entering...')
    response_data = dict()

    if request.method != 'POST':
        bank_accounts = BankAccount.objects.filter(owner=request.user, active=True).order_by('display_order')
        return render_to_response('budget/snippet__bank_accounts.html', {'bank_accounts': bank_accounts})

    try:
        if 'action' not in request.POST:
            raise RuntimeError('Invalid request: missing action')

        logger.debug('bank_account_view:- request.POST: %s' % request.POST)
        result_message = 'Account Saved!'
        result_success = 'pass'

        action = request.POST["action"]
        if action == 'new':
            # create a new dummy account
            acc_count = 1
            acc_type = 'debit' if 'account_type' not in request.POST else request.POST['account_type']
            acc_title = acc_type.title() + ' Account #1'
            while BankAccount.objects.filter(owner=request.user, active=True, title__iexact=acc_title).exists():
                acc_count += 1
                acc_title = acc_type.title() + ' Account #%d' % acc_count
            BankAccount.objects.create(
                title=acc_title,
                account_type=acc_type,
                current_balance=0,
                display_order=BankAccount.objects.filter(owner=request.user, active=True, account_type__exact=acc_type)
                    .aggregate(Max('display_order'))['display_order__max'] + 1,
                owner=request.user,
                active=True,
            )

        elif action == 'update':
            if 'bank_account_id' not in request.POST:
                raise RuntimeError("bank_account_view:- bank_account_id not specified")

            ba = BankAccount.objects.get(pk=request.POST['bank_account_id'])

            if 'title' in request.POST:
                if BankAccount.objects.filter(owner=request.user, active=True) \
                        .filter(title__iexact=request.POST['title']).count() > 0:
                    raise ValidationError("Account of that name already exists")
                else:
                    ba.title = request.POST['title']

            if 'current_balance' in request.POST:
                ba.current_balance = request.POST['current_balance']

            if 'account_type' in request.POST:
                ba.account_type = request.POST['account_type']

            if 'display_order' in request.POST:
                display_order_min = min(ba.display_order, int(request.POST['display_order']))
                display_order_max = max(ba.display_order, int(request.POST['display_order']))
                shift_down = ba.display_order < int(request.POST['display_order'])
                ba.display_order = int(request.POST['display_order'])
                for ba_iter in BankAccount.objects.filter(owner=request.user, active=True).order_by('display_order'):
                    if ba_iter.display_order >= display_order_min and ba_iter.display_order <= display_order_max \
                            and ba_iter.pk != ba.pk:
                        if shift_down:
                            ba_iter.display_order -= 1
                        else:
                            ba_iter.display_order += 1
                        ba_iter.save()

            ba.save()

        elif action == 'delete':
            ba = BankAccount.objects.get(pk=request.POST['bank_account_id'])
            # Can't delete if there are active payments from/to this account
            if Payment.objects.filter(owner=request.user, active=True, account=ba).exists():
                raise ValidationError("Cannot delete an account with active payments")

            ba.active = False
            ba.save()
            result_message = 'Account deleted!'

        # logger.info('update_account_from_calendar_view:- saved new account')
        bank_accounts = BankAccount.objects.filter(owner=request.user, active=True).order_by('display_order')
        return render_to_response('budget/snippet__bank_accounts.html', {'bank_accounts': bank_accounts,
                                                                         'result_message': result_message,
                                                                         'result_success': result_success})

    except Exception as e:
        error_message = e.messages if hasattr(e, 'messages') else e.message
        logger.error(error_message)
        response_data['result_message'] = error_message
        response_data['result_success'] = 'fail'
        return HttpResponse(jsonpickle.encode(response_data), content_type="application/json")


@login_required
@ensure_csrf_cookie
def get_accounts_json(request):
    if request.method != 'GET':
        raise RuntimeError("get_accounts_json: GET request expected")

    try:
        # logger.info('get_accounts_json:- ')
        accounts = BankAccount.objects.filter(owner=request.user, active=True).order_by('display_order').all()
        accounts_json = []
        for a in accounts:
            accounts_json.append({'id': a.id, 'title': a.title, 'type': a.account_type})

        return HttpResponse(jsonpickle.encode(accounts_json), content_type="application/json")

    except Exception as e:
        return HttpResponse(jsonpickle.encode('{ "Exception": "%s"}' % e.message), content_type="application/json")


# region Helper functions


def generate_categorymap(owner):
    # Category Map
    categorymap = []
    for pt in PaymentType.objects.filter(owner=owner, active=True).order_by('name'):
        categorymap.append([pt.id])
        for c in pt.category_set.filter(owner=owner, active=True).order_by('name'):
            categorymap.append([pt.id, c.id])
            for sc in c.subcategory_set.filter(owner=owner, active=True).order_by('name'):
                categorymap.append([pt.id, c.id, sc.id])
    return categorymap


def generate_calendar_search_terms(owner):
    calendar_search_terms = []
    for searchstr in Payment.objects.filter(owner=owner, active=True).values_list('title', flat=True):
        if searchstr not in calendar_search_terms:
            calendar_search_terms.append(searchstr)
    for p in Payment.objects.filter(owner=owner, active=True).all():
        if p.payment_type.name not in calendar_search_terms:
            calendar_search_terms.append(p.payment_type.name)
        if p.category is not None and p.category.name not in calendar_search_terms:
            calendar_search_terms.append(p.category.name)
        if p.subcategory is not None and p.subcategory.name not in calendar_search_terms:
            calendar_search_terms.append(p.subcategory.name)
    return sorted(calendar_search_terms, key=unicode.lower)


def build_payment_frequency(schedule, cleaned_data):
    if schedule == '':
        ps = PaymentSchedule()
        logger.info('build_payment_frequency:- new schedule')
    else:
        ps = schedule
        logger.info('build_payment_frequency:- existing schedule')

    ps.next_date = cleaned_data['next_date']
    ps.frequency = PaymentScheduleFrequency.objects.get(pk=cleaned_data['schedule_frequency'])

    if cleaned_data['until_type'] == 'until_forever':
        ps.end_date = None
        ps.occurrences = 0
    elif cleaned_data['until_type'] == 'until_occurrences':
        logger.debug('build_payment_frequency:- cleaned_data[occurrences]: %s' % cleaned_data['occurrences'])
        ps.end_date = None
        ps.occurrences = cleaned_data['occurrences']
    elif cleaned_data['until_type'] == 'until_end_date':
        ps.end_date = cleaned_data['end_date']
        ps.occurrences = 0

    # Weekly fields
    ps.weekly_dow_mon = cleaned_data['weekly_dow_mon']
    ps.weekly_dow_tue = cleaned_data['weekly_dow_tue']
    ps.weekly_dow_wed = cleaned_data['weekly_dow_wed']
    ps.weekly_dow_thu = cleaned_data['weekly_dow_thu']
    ps.weekly_dow_fri = cleaned_data['weekly_dow_fri']
    ps.weekly_dow_sat = cleaned_data['weekly_dow_sat']
    ps.weekly_dow_sun = cleaned_data['weekly_dow_sun']
    ps.weekly_frequency = int(cleaned_data['weekly_frequency']) if cleaned_data['weekly_frequency'] else 0
    if ps.weekly_frequency != 0:
        # "Round" up next_date to the very next occurrence, as rrule will use frequency and skip it
        ps.weekly_frequency = int(cleaned_data['weekly_frequency'])
        dow = []
        if ps.weekly_dow_mon:
            dow.append(0)
        if ps.weekly_dow_tue:
            dow.append(1)
        if ps.weekly_dow_wed:
            dow.append(2)
        if ps.weekly_dow_thu:
            dow.append(3)
        if ps.weekly_dow_fri:
            dow.append(4)
        if ps.weekly_dow_sat:
            dow.append(5)
        if ps.weekly_dow_sun:
            dow.append(6)
        ps.next_date = rrule(WEEKLY, dtstart=ps.next_date, byweekday=dow)\
            .after(datetime(year=ps.next_date.year, month=ps.next_date.month, day=ps.next_date.day), inc=True)
    else:
        ps.weekly_frequency = 0

    # Monthly fields
    ps.monthly_frequency = int(cleaned_data['monthly_frequency']) if cleaned_data['monthly_frequency'] else 0
    ps.monthly_dom = int(cleaned_data['monthly_dom']) if cleaned_data['monthly_dom'] else 0
    if ps.monthly_frequency != 0 and ps.monthly_dom != 0:
        ps.monthly_dom = int(cleaned_data['monthly_dom'])
        # "Round" up next_date to the very next occurrence, as rrule will use frequency and skip it
        ps.next_date = rrule(MONTHLY, dtstart=ps.next_date, bymonthday=ps.monthly_dom) \
            .after(datetime(year=ps.next_date.year, month=ps.next_date.month, day=ps.next_date.day), inc=True)

    ps.monthly_wom = int(cleaned_data['monthly_wom']) if cleaned_data['monthly_wom'] else 0
    ps.monthly_dow = int(cleaned_data['monthly_dow']) if cleaned_data['monthly_dow'] else 0
    if ps.monthly_frequency != 0 and ps.monthly_wom != 0:
        # "Round" up next_date to the very next occurrence, as rrule will use frequency and skip it
        ps.next_date = rrule(MONTHLY, dtstart=ps.next_date, byweekday=weekdays[ps.monthly_dow](ps.monthly_wom)) \
            .after(datetime(year=ps.next_date.year, month=ps.next_date.month, day=ps.next_date.day), inc=True)

    # Annual fields
    ps.annual_frequency = int(cleaned_data['annual_frequency']) if cleaned_data['annual_frequency'] else 0
    ps.annual_dom = int(cleaned_data['annual_dom']) if cleaned_data['annual_dom'] else 0
    ps.annual_moy = int(cleaned_data['annual_moy']) if cleaned_data['annual_moy'] else 0
    if ps.annual_frequency != 0:
        ps.next_date = rrule(YEARLY, dtstart=ps.next_date, bymonth=ps.annual_moy, bymonthday=ps.annual_dom)\
            .after(datetime(year=ps.next_date.year, month=ps.next_date.month, day=ps.next_date.day), inc=True)

    ps.full_clean()
    recalculate_next_payment(ps)
    ps.save()

    return ps


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
    rr = {}
    # Check params
    if (recalc_type == 'count' or recalc_type == 'months') and num == 0:
        raise RuntimeError("recalculate_payments: num must be specified")
    if recalc_type == 'from_to' and (start_date is None or end_date is None):
        raise RuntimeError("recalculate_payments: start_date and end_date must be specified")
    if recalc_type == 'until' and end_date is None:
        raise RuntimeError("recalculate_payments: end_date must be specified")
    if recalc_type == 'after' and start_date is None:
        raise RuntimeError("recalculate_payments: start_date must be specified for recalc_type: after")

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
            elif recalc_type == 'after':
                rr = rrule(MONTHLY, dtstart=max(start_date, schedule.next_date), count=num,
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
            elif recalc_type == 'after':
                rr = rrule(MONTHLY, dtstart=max(start_date, schedule.next_date), count=num,
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
        elif recalc_type == 'after':
            rr = rrule(WEEKLY, dtstart=max(start_date, schedule.next_date), count=num,
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
            logger.debug('recalculate_next_n_m:- recalc_type: %s, start_date: %s, next_date: %s, annual_dom: %d, annual_frequency: %d'
                         % (recalc_type, str(start_date), str(schedule.next_date), schedule.annual_dom, schedule.annual_frequency))
            rr = rrule(YEARLY, dtstart=max(start_date, schedule.next_date), until=end_date, bymonth=schedule.annual_moy,
                       bymonthday=schedule.annual_dom, interval=schedule.annual_frequency)
        elif recalc_type == 'until':
            rr = rrule(YEARLY, dtstart=schedule.next_date, until=end_date, bymonth=schedule.annual_moy,
                       bymonthday=schedule.annual_dom, interval=schedule.annual_frequency)
        elif recalc_type == 'after':
            start_date_datetime = datetime(year=start_date.year, month=start_date.month, day=start_date.day)
            logger.debug('recalculate_next_n_m:- recalc_type: %s, start_date_datetime: %s, next_date: %s, annual_dom: %d, annual_frequency: %d'
                         % (recalc_type, str(start_date_datetime), str(schedule.next_date), schedule.annual_dom, schedule.annual_frequency))
            rr = rrule(YEARLY, dtstart=schedule.next_date, count=num, bymonth=schedule.annual_moy,
                       bymonthday=schedule.annual_dom, interval=schedule.annual_frequency).after(start_date_datetime, inc=True)
            logger.debug('recalculate_next_n_m: success')

    elif schedule.frequency.name == 'Once Off':
        rr = rrule(DAILY, count=1, dtstart=schedule.next_date)

    # elif schedule.frequency.name == 'Linked to Other Payment':
    #     kwargs = {}
    #     kwargs[p.offset_type] = p.offset
    #     payment_date += relativedelta(**kwargs)

    return list(rr)


def schedule_rrule(payment):
    kwargs = {}

    if payment.schedule.occurrences > 0:
        kwargs['count'] = payment.schedule.occurrences
    elif payment.schedule.end_date is not None:
        kwargs['until'] = payment.schedule.end_date

    schedule = payment.schedule if payment.schedule.frequency.name != 'Linked to Other Payment' \
        else payment.parent_payment.schedule
    if schedule.frequency.name == 'Monthly':
        kwargs['freq'] = MONTHLY
        kwargs['dtstart'] = schedule.next_date
        kwargs['interval'] = schedule.monthly_frequency
        # Specific day of month
        if schedule.monthly_dom != 0:
            kwargs['bymonthday'] = schedule.monthly_dom
        # day of week
        elif schedule.monthly_wom != 0:
            kwargs['byweekday'] = weekdays[schedule.monthly_dow](schedule.monthly_wom)

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
        kwargs['freq'] = WEEKLY
        kwargs['dtstart'] = schedule.next_date
        kwargs['byweekday'] = dow
        kwargs['interval'] = schedule.weekly_frequency

    elif schedule.frequency.name == 'Annual':
        kwargs['freq'] = YEARLY
        kwargs['dtstart'] = schedule.next_date
        kwargs['bymonth'] = schedule.annual_moy
        kwargs['bymonthday'] = schedule.annual_dom
        kwargs['interval'] = schedule.annual_frequency

    elif schedule.frequency.name == 'Once Off':
        kwargs['freq'] = YEARLY
        kwargs['dtstart'] = schedule.next_date
        kwargs['count'] = 1

    logger.debug('schedule_rrule:- calling rrule with kwargs: %s' % kwargs)
    rset = rruleset()
    rset.rrule(rrule(**kwargs))

    # add exclusions
    for ex in PaymentScheduleExclusion.objects.filter(main_payment=payment).all():
        rset.exdate(datetime(year=ex.exclusion_date.year, month=ex.exclusion_date.month, day=ex.exclusion_date.day))

    return rset

# endregion

# region Deprecated functions


def build_payment_frequency__textual(cleaned_data):
    nth = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh", 8: "eighth",
           9: "ninth", 10: "tenth", 11: "eleventh", 12: "twelfth", 13: "thirteenth", 14: "fourteenth", 15: "fifteenth",
           16: "sixteenth", 17: "seventeenth", 18: "eighteenth", 19: "nineteenth", 20: "twentieth", 21: "twentyfirst",
           22: "twentysecond", 23: "twentythird", 24: "twentyfourth", 25: "twentyfifth", 26: "twentysixth",
           27: "twentyseventh", 28: "twentyeight", 29: "twentyninth", 30: "thirtieth", 31: "thirtyfirst"}
    weekdays_full = ("sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday")
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
            if periodicity_words[0].lower() in list(weekdays_full) + list(weekdays_abbrev1) + list(weekdays_abbrev2):
                ps.monthly_wom = -1
                if periodicity_words[0].lower() in weekdays_full:
                    ps.monthly_dow = weekdays_full.index(periodicity_words[0].lower())
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
                if periodicity_words[2].lower() in list(weekdays_full) + list(weekdays_abbrev1) + list(
                        weekdays_abbrev2):
                    ps.monthly_wom = int(dom.match(periodicity_words[0]).group(1)) * -1
                else:
                    ps.monthly_dom = int(dom.match(periodicity_words[0]).group(1)) * -1
            else:
                if periodicity_words[2].lower() in list(weekdays_full) + list(weekdays_abbrev1) + list(
                        weekdays_abbrev2):
                    ps.monthly_wom = nth.keys()[nth.values().index(periodicity_words[0])] * -1
                else:
                    ps.monthly_dom = nth.keys()[nth.values().index(periodicity_words[0])] * -1
            periodicity_words.pop(0)
            periodicity_words.pop(0)

        elif periodicity_words[0].lower() == 'first':
            ps.monthly_wom = 1
            periodicity_words.pop(0)
            if periodicity_words[0].lower() in weekdays_full:
                ps.monthly_dow = weekdays_full.index(periodicity_words[0].lower())
                periodicity_words.pop(0)
            elif periodicity_words[0].lower() in weekdays_abbrev1:
                ps.monthly_dow = weekdays_abbrev1.index(periodicity_words[0].lower())
                periodicity_words.pop(0)
            elif periodicity_words[0].lower() in weekdays_abbrev2:
                ps.monthly_dow = weekdays_abbrev2.index(periodicity_words[0].lower())
                periodicity_words.pop(0)

        else:
            if dom.match(periodicity_words[0]):
                if periodicity_words[1].lower() in list(weekdays_full) + list(weekdays_abbrev1) + list(
                        weekdays_abbrev2):
                    ps.monthly_wom = int(dom.match(periodicity_words[0]).group(1))
                else:
                    ps.monthly_dom = int(dom.match(periodicity_words[0]).group(1))
            else:
                if periodicity_words[1].lower() in list(weekdays_full) + list(weekdays_abbrev1) + list(
                        weekdays_abbrev2):
                    ps.monthly_wom = nth.keys()[nth.values().index(periodicity_words[0])]
                else:
                    ps.monthly_dom = nth.keys()[nth.values().index(periodicity_words[0])]
            periodicity_words.pop(0)

        if periodicity_words[0].lower() == 'day':
            periodicity_words.pop(0)
        elif periodicity_words[0].lower() in weekdays_full:
            ps.monthly_dow = weekdays_full.index(periodicity_words[0].lower())
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
