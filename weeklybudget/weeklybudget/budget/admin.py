from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import *


class CategoryInline(admin.StackedInline):
    model = Category


class SubCategoryInline(admin.StackedInline):
    model = SubCategory


class SubCategoryAdmin(admin.ModelAdmin):
    model = SubCategory


class CategoryAdmin(admin.ModelAdmin):
    inlines = [SubCategoryInline]


class PaymentTypeAdmin(admin.ModelAdmin):
    inlines = [CategoryInline]


class PaymentScheduleAdmin(admin.ModelAdmin):
    model = PaymentSchedule


class PaymentScheduleFrequencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sort_order')


class PaymentAdmin(admin.ModelAdmin):
    model = Payment


class BankAccountAdmin(admin.ModelAdmin):
    model = BankAccount


class PaymentScheduleExclusionsAdmin(admin.ModelAdmin):
    model = PaymentScheduleExclusion


admin.site.register(PaymentType, PaymentTypeAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Payment, SimpleHistoryAdmin)
admin.site.register(PaymentSchedule, PaymentScheduleAdmin)
admin.site.register(PaymentScheduleFrequency, PaymentScheduleFrequencyAdmin)
admin.site.register(BankAccount, BankAccountAdmin)
admin.site.register(PaymentScheduleExclusion, PaymentScheduleExclusionsAdmin)
