import datetime

from django import forms
from django.core import exceptions, checks

from django.db import models

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.translation import gettext_lazy as _


class NaiveDateTimeField(models.DateField):
    description = _("Naive Date (with time)")

    def get_internal_type(self):
        return "NaiveDateTime"

    def db_type(self, connection):
        if (connection.settings_dict['ENGINE'] in [
                'django.db.backends.postgresql',
                'django.db.backends.postgresql_psycopg2']):
            return "timestamp without time zone"

        return "datetime"

    def _check_fix_default_value(self):
        """
        Warn that using an actual date or datetime value is probably wrong;
        it's only evaluated on server startup.
        """
        if not self.has_default():
            return []

        now = timezone.now()
        if not timezone.is_naive(now):
            now = timezone.make_naive(now, timezone.utc)
        value = self.default
        if isinstance(value, datetime.datetime):
            second_offset = datetime.timedelta(seconds=10)
            lower = now - second_offset
            upper = now + second_offset
            if timezone.is_aware(value):
                value = timezone.make_naive(value, timezone.utc)
        elif isinstance(value, datetime.date):
            second_offset = datetime.timedelta(seconds=10)
            lower = now - second_offset
            lower = datetime.datetime(lower.year, lower.month, lower.day)
            upper = now + second_offset
            upper = datetime.datetime(upper.year, upper.month, upper.day)
            value = datetime.datetime(value.year, value.month, value.day)
        else:
            # No explicit date / datetime value -- no checks necessary
            return []
        if lower <= value <= upper:
            return [
                checks.Warning(
                    'Fixed default value provided.',
                    hint='It seems you set a fixed date / time / datetime '
                         'value as default for this field. This may not be '
                         'what you want. If you want to have the current date '
                         'as default, use `django.utils.timezone.now`',
                    obj=self,
                    id='fields.W161',
                )
            ]

        return []

    def to_python(self, value):
        '''
        This method was lifted from django's DateTimeField and then
        all TZ handling was removed

        It attempts to convert the value to python from least complex
        to most complex/slowest
        '''
        if value is None:
            return value
        if isinstance(value, datetime.datetime):
            return value.replace(tzinfo=None)
        if isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day)

        try:
            parsed = parse_datetime(value)
            if parsed is not None:
                return parsed
        except ValueError:
            raise exceptions.ValidationError(
                self.error_messages['invalid_datetime'],
                code='invalid_datetime',
                params={'value': value},
            )

        try:
            parsed = parse_date(value)
            if parsed is not None:
                return datetime.datetime(parsed.year, parsed.month, parsed.day)
        except ValueError:
            raise exceptions.ValidationError(
                self.error_messages['invalid_date'],
                code='invalid_date',
                params={'value': value},
            )

        raise exceptions.ValidationError(
            self.error_messages['invalid'],
            code='invalid',
            params={'value': value},
        )

    def get_prep_value(self, value):
        '''
        Ensure we have a naive datetime ready for insertion
        '''
        value = super(NaiveDateTimeField, self).get_prep_value(value)
        value = self.to_python(value)

        if value is not None and timezone.is_aware(value):
            # We were given an aware datetime, strip off tzinfo
            value = value.replace(tzinfo=None)

        return value

    def get_db_prep_value(self, value, connection, prepared=False):
        if not prepared:
            value = self.get_prep_value(value)

        if value is None:
            return None

        if hasattr(value, 'resolve_expression'):
            return value

        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return str(value)

        elif connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3':
            return str(value)

        elif connection.settings_dict['ENGINE'] == 'django.db.backends.oracle':
            from django.db.backends.oracle.utils import Oracle_datetime
            return Oracle_datetime.from_datetime(value)

        return value

    def pre_save(self, model_instance, add):
        if self.auto_now or (self.auto_now_add and add):
            value = timezone.now().replace(tzinfo=None)
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(NaiveDateTimeField, self).pre_save(model_instance, add)

    def value_to_string(self, obj):
        val = self.value_from_object(obj)
        return '' if val is None else val.isoformat()

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.DateTimeField}
        defaults.update(kwargs)
        return super(NaiveDateTimeField, self).formfield(**defaults)
