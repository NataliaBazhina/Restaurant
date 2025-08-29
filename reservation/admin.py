from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Hall, Table, Reservation


@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    list_display = ['name', 'width', 'height', 'description_short']
    list_filter = ['width', 'height']
    search_fields = ['name', 'description']

    def description_short(self, obj):
        return obj.description[:50] + '...' if obj.description else ''

    description_short.short_description = 'Описание'


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'hall', 'capacity', 'x_position', 'y_position', 'is_active']
    list_editable = ['is_active', 'capacity', 'x_position', 'y_position']
    list_filter = ['is_active', 'hall', 'capacity']
    search_fields = ['number', 'hall__name']
    list_per_page = 20

    actions = ['activate_tables', 'deactivate_tables']

    def activate_tables(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} столиков активировано', messages.SUCCESS)

    activate_tables.short_description = 'Активировать выбранные столики'

    def deactivate_tables(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} столиков деактивировано', messages.SUCCESS)

    deactivate_tables.short_description = 'Деактивировать выбранные столики'


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'table',
        'user',
        'date',
        'start_time',
        'end_time_display',
        'guests_count',
        'status',
        'source',
        'extended_by_admin',
        'created_at_short'
    ]

    list_filter = [
        'status',
        'source',
        'date',
        'table__hall',
        'extended_by_admin'
    ]

    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'table__number',
        'table__hall__name',
        'event'
    ]

    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at', 'end_time_display']
    date_hierarchy = 'date'
    list_per_page = 30

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'table', 'date', 'start_time', 'duration', 'guests_count')
        }),
        ('Статус и детали', {
            'fields': ('status', 'event', 'extended_by_admin', 'source', 'staff_user')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_confirmed', 'mark_completed', 'mark_canceled']

    def end_time_display(self, obj):
        return obj.end_time.strftime('%H:%M') if obj.end_time else '-'

    end_time_display.short_description = 'Окончание'

    def created_at_short(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')

    created_at_short.short_description = 'Создано'

    def mark_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} броней подтверждено', messages.SUCCESS)

    mark_confirmed.short_description = 'Подтвердить выбранные брони'

    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} броней завершено', messages.SUCCESS)

    mark_completed.short_description = 'Завершить выбранные брони'

    def mark_canceled(self, request, queryset):
        updated = queryset.update(status='canceled')
        self.message_user(request, f'{updated} броней отменено', messages.SUCCESS)

    mark_canceled.short_description = 'Отменить выбранные брони'

    def save_model(self, request, obj, form, change):
        """Автоматически заполняем staff_user если админ меняет бронь"""
        if change and request.user.is_staff and not obj.staff_user:
            obj.staff_user = request.user
        super().save_model(request, obj, form, change)