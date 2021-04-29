import datetime
import sys

import pytz

import django
from django.core import exceptions, checks
from django.db.models import DateTimeField, Func, Value
from django.db.models.functions.datetime import TruncBase, Extract, ExtractYear
from django.db.models.lookups import (
    Exact,
    GreaterThan,
    GreaterThanOrEqual,
    LessThan,
    LessThanOrEqual,
)
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.translation import gettext_lazy as _


def _conn_tz(connection):
    """
    Before Django 3.1, connection.timezone is always None when using PostgreSQL.
    """
    if django.VERSION < (3, 1):
        return pytz.timezone(connection.timezone_name)
    else:
        return connection.timezone


class NaiveDateTimeField(DateTimeField):
    description = _("Naive Date (with time)")

    default_error_messages = {
        "tzaware": _("TZ-aware datetimes cannot be coerced to naive datetimes"),
    }

    def get_internal_type(self):
        return "DateTimeField"

    def db_type(self, connection):
        if connection.vendor == "postgresql":
            return "timestamp without time zone"
        return super(NaiveDateTimeField, self).db_type(connection)

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
                    "Fixed default value provided.",
                    hint="It seems you set a fixed date / time / datetime "
                    "value as default for this field. This may not be "
                    "what you want. If you want to have the current date "
                    "as default, use `django.utils.timezone.now`",
                    obj=self,
                    id="fields.W161",
                )
            ]

        return []

    def to_python(self, value):
        """
        This method was lifted from django's DateTimeField and then
        all TZ handling was removed

        It attempts to convert the value to python from least complex
        to most complex/slowest
        """
        if value is None:
            return value
        if isinstance(value, datetime.datetime):
            if timezone.is_aware(value):
                raise exceptions.ValidationError(self.error_messages["tzaware"])
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day)

        try:
            parsed = parse_datetime(value)
            if parsed is not None:
                if timezone.is_aware(parsed):
                    raise exceptions.ValidationError(self.error_messages["tzaware"])
                return parsed
        except ValueError:
            raise exceptions.ValidationError(
                self.error_messages["invalid_datetime"],
                code="invalid_datetime",
                params={"value": value},
            )

        try:
            parsed = parse_date(value)
            if parsed is not None:
                return datetime.datetime(parsed.year, parsed.month, parsed.day)
        except ValueError:
            raise exceptions.ValidationError(
                self.error_messages["invalid_date"],
                code="invalid_date",
                params={"value": value},
            )

        raise exceptions.ValidationError(
            self.error_messages["invalid"], code="invalid", params={"value": value}
        )

    def get_prep_value(self, value):
        return super(DateTimeField, self).get_prep_value(value)

    def from_db_value(self, value, expr, connection):
        if value is None:
            return None

        if isinstance(expr, TruncBase) and not isinstance(expr, NaiveAsSQLMixin):
            raise TypeError(
                "Django's %s cannot be used with a NaiveDateTimeField"
                % expr.__class__.__name__
            )

        if timezone.is_aware(value):
            return timezone.make_naive(value, _conn_tz(connection))
        return value

    def pre_save(self, model_instance, add):
        if self.auto_now or (self.auto_now_add and add):
            value = timezone.make_naive(timezone.now())
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(NaiveDateTimeField, self).pre_save(model_instance, add)


class NaiveConvertValueMixin(object):
    def convert_value(self, value, expression, connection):
        if isinstance(self.output_field, NaiveDateTimeField):
            if timezone.is_aware(value):
                return timezone.make_naive(value, _conn_tz(connection))
        return super(NaiveConvertValueMixin, self).convert_value(
            value, expression, connection
        )


class NaiveAsSQLMixin(object):
    """
    The purpose of this mixin is to override the active timezone when
    generating SQL for truncate and extract operations, to effectively
    nullify the timezone conversion that Django unconditionally applies
    to datetime values.
    """

    def as_sql(self, compiler, connection):
        if isinstance(self.lhs.output_field, NaiveDateTimeField):
            if self.tzinfo is not None:
                raise ValueError("tzinfo can only be used with DateTimeField.")
            # Account for https://github.com/django/django/commit/cef3f2d3
            tz_override = pytz.utc if django.VERSION < (3,) else _conn_tz(connection)
            with timezone.override(tz_override):
                return super(NaiveAsSQLMixin, self).as_sql(compiler, connection)
        return super(NaiveAsSQLMixin, self).as_sql(compiler, connection)


class AtTimeZone(Func):
    """
    This implements PostgreSQL's AT TIME ZONE construct, which returns a naive
    datetime if used with a timezone-aware datetime, and vice versa.

    See https://www.postgresql.org/docs/9.6/functions-datetime.html#FUNCTIONS-DATETIME-ZONECONVERT # noqa
    """

    def __init__(self, value, tz):
        super(AtTimeZone, self).__init__(
            value,
            tz,
            template="(%(expressions)s)",
            arg_joiner=" AT TIME ZONE ",
        )

    @staticmethod
    def _fix_value(v):
        if isinstance(v.value, datetime.datetime) and timezone.is_naive(v.value):
            if "output_field" not in v.__dict__:
                v.output_field = NaiveDateTimeField()
            elif not isinstance(v.output_field, NaiveDateTimeField):
                raise TypeError(
                    "Naive Value passed to AtTimeZone has output_field type DateTimeField - must be None or NaiveDateTimeField"
                )
        return v

    def _parse_expressions(self, *expressions):
        return [
            self._fix_value(v) if isinstance(v, Value) else v
            for v in super()._parse_expressions(*expressions)
        ]

    def _resolve_output_field(self):
        if getattr(self, "_output_field", None) is None:
            value_field, _ = super(AtTimeZone, self).get_source_fields()
            if isinstance(value_field, NaiveDateTimeField):
                self._output_field = DateTimeField()
            elif isinstance(value_field, DateTimeField):
                self._output_field = NaiveDateTimeField()
            elif value_field is None:
                value_expr = self.get_source_expressions()[0]
                if isinstance(value_expr, Value):
                    if timezone.is_naive(value_expr.value):
                        self._output_field = DateTimeField()
                    else:
                        self._output_field = NaiveDateTimeField()
        return getattr(self, "_output_field", None)


_monkeypatching = False


_this_module = sys.modules[__name__]
_db_functions = sys.modules["django.db.models.functions"]
_lookups = set(DateTimeField.get_lookups().values())
_patch_classes = [
    (Extract, [NaiveAsSQLMixin]),
    (TruncBase, [NaiveAsSQLMixin, NaiveConvertValueMixin]),
]
for original, mixins in _patch_classes:
    for cls in original.__subclasses__():

        bases = tuple(mixins) + (cls,)
        naive_cls = type(cls.__name__, bases, {})

        if _monkeypatching:
            setattr(_db_functions, cls.__name__, naive_cls)

        if cls in _lookups:
            NaiveDateTimeField.register_lookup(naive_cls)

            # Year lookups don't need special handling with naive fields
            if cls is ExtractYear:
                naive_cls.register_lookup(Exact)
                naive_cls.register_lookup(GreaterThan)
                naive_cls.register_lookup(GreaterThanOrEqual)
                naive_cls.register_lookup(LessThan)
                naive_cls.register_lookup(LessThanOrEqual)

        # Add an attribute to this module so these functions can be imported
        setattr(_this_module, cls.__name__, naive_cls)
