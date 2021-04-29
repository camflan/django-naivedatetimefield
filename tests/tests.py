import datetime
from unittest import skipIf

import pytz
from django import db
from django.db import connection
from django.db.models import functions, Value
from django.test import TestCase, override_settings
from django.utils import timezone

import naivedatetimefield
from naivedatetimefield import AtTimeZone
from .models import (
    NaiveDateTimeTestModel,
    NaiveDateTimeAutoNowAddModel,
    NaiveDateTimeAutoNowModel,
    NullableNaiveDateTimeModel,
)


class NaiveDateTimeFieldTestCase(TestCase):
    """
    main test case for NaiveDateTimeField
    """

    def test_auto_now_add(self):
        obj = NaiveDateTimeAutoNowAddModel.objects.create()

        self.assertTrue(timezone.is_aware(obj.aware))
        self.assertTrue(timezone.is_naive(obj.naive))

    def test_auto_now(self):
        obj = NaiveDateTimeAutoNowModel.objects.create()

        self.assertTrue(timezone.is_aware(obj.aware))
        self.assertTrue(timezone.is_naive(obj.naive))

    def test_timezones_ignored(self):

        naive = datetime.datetime(2018, 4, 1, 18, 0)
        o1 = NaiveDateTimeTestModel.objects.create(
            naive=naive,
            aware=timezone.make_aware(naive),
        )

        with timezone.override("Australia/Melbourne"):
            o2 = NaiveDateTimeTestModel.objects.create(
                naive=naive,
                aware=timezone.make_aware(naive),
            )
            o1.refresh_from_db()
            o2.refresh_from_db()

        self.assertNotEqual(o1.aware, o2.aware)
        self.assertEqual(o1.naive, naive)
        self.assertEqual(o2.naive, naive)

        with timezone.override("Australia/Adelaide"):
            o1.refresh_from_db()
            o2.refresh_from_db()
            self.assertNotEqual(o1.aware, o2.aware)
            self.assertEqual(o1.naive, naive)
            self.assertEqual(o2.naive, naive)

        with override_settings(USE_TZ=False):
            o1.refresh_from_db()
            o2.refresh_from_db()
            self.assertNotEqual(o1.aware, o2.aware)
            self.assertEqual(o1.naive, naive)
            self.assertEqual(o2.naive, naive)

    def test_time_lookup(self):
        """
        This should test that __time lookups work properly on naive datetime fields
        """
        timezone.activate("America/Los_Angeles")

        n = datetime.datetime(2018, 4, 1, 18, 0)
        a = timezone.make_aware(n)

        o = NaiveDateTimeTestModel.objects.create(aware=a, naive=n)

        o.refresh_from_db()

        results = NaiveDateTimeTestModel.objects.filter(naive__time__hour__gte=1)

        self.assertEqual(results.count(), 1)

    def test_date_trunc(self):
        """
        Test that date truncating works regardless of active timezone.
        """
        timezone.activate("Australia/Adelaide")
        n = datetime.datetime(2017, 12, 31, 20, 10, 30, 123456)
        a = timezone.make_aware(n)
        o = NaiveDateTimeTestModel.objects.create(aware=a, naive=n)
        o.refresh_from_db()

        def query_truncations(module):
            return NaiveDateTimeTestModel.objects.annotate(
                year=getattr(module, "TruncYear")("naive"),
                mon=getattr(module, "TruncMonth")("naive"),
                day=getattr(module, "TruncDay")("naive"),
                hour=getattr(module, "TruncHour")("naive"),
                min=getattr(module, "TruncMinute")("naive"),
                sec=getattr(module, "TruncSecond")("naive"),
                date=getattr(module, "TruncDate")("naive"),
                time=getattr(module, "TruncTime")("naive"),
            ).all()[0]

        self.assertEqual(NaiveDateTimeTestModel.objects.count(), 1)

        r = query_truncations(naivedatetimefield)
        self.assertEqual(
            [r.year, r.mon, r.day, r.hour, r.min, r.sec, r.date, r.time],
            [
                datetime.datetime(2017, 1, 1),
                datetime.datetime(2017, 12, 1),
                datetime.datetime(2017, 12, 31),
                datetime.datetime(2017, 12, 31, 20),
                datetime.datetime(2017, 12, 31, 20, 10),
                datetime.datetime(2017, 12, 31, 20, 10, 30),
                datetime.date(2017, 12, 31),
                datetime.time(20, 10, 30, 123456),
            ],
        )

        with self.assertRaisesRegex(
            TypeError, r"Django's \w+ cannot be used with a NaiveDateTimeField"
        ):
            query_truncations(functions)

    def test_date_transforms(self):
        """
        Test that date transforms work regardless of active timezone.
        """
        timezone.activate("utc")

        # Create some borderline datetimes, hard-coded for easier visualisation/verification
        # >>> dt = datetime.datetime(2017, 1, 1, 10, 30)
        # >>> for i in range(12): repr(dt + timedelta(days=121*i, hours=13*i, minutes=4*i, seconds=i))
        datetimes = [
            datetime.datetime(2017, 1, 1, 10, 30, 0),
            datetime.datetime(2017, 5, 2, 23, 34, 1),
            datetime.datetime(2017, 9, 1, 12, 38, 2),
            datetime.datetime(2018, 1, 1, 1, 42, 3),
            datetime.datetime(2018, 5, 2, 14, 46, 4),
            datetime.datetime(2018, 9, 1, 3, 50, 5),
            datetime.datetime(2018, 12, 31, 16, 54, 6),
            datetime.datetime(2019, 5, 2, 5, 58, 7),
            datetime.datetime(2019, 8, 31, 19, 2, 8),
            datetime.datetime(2019, 12, 31, 8, 6, 9),
            datetime.datetime(2020, 4, 30, 21, 10, 10),
            datetime.datetime(2020, 8, 30, 10, 14, 11),
        ]

        NaiveDateTimeTestModel.objects.bulk_create(
            NaiveDateTimeTestModel(aware=timezone.make_aware(dt), naive=dt)
            for dt in datetimes
        )

        def count_filter(**kwargs):
            return NaiveDateTimeTestModel.objects.filter(**kwargs).count()

        def test_in_timezone(tz):
            with timezone.override(tz):
                self.assertEqual(count_filter(naive__year__lt=2018), 3)
                self.assertEqual(count_filter(naive__year__lte=2018), 7)
                self.assertEqual(count_filter(naive__year__gt=2018), 5)
                self.assertEqual(count_filter(naive__year__gte=2018), 9)
                self.assertEqual(count_filter(naive__year=2018), 4)

                self.assertEqual(count_filter(naive__month__lt=5), 3)
                self.assertEqual(count_filter(naive__month__lte=5), 6)
                self.assertEqual(count_filter(naive__month__gt=5), 6)
                self.assertEqual(count_filter(naive__month__gte=5), 9)
                self.assertEqual(count_filter(naive__month=5), 3)

                self.assertEqual(count_filter(naive__day__lt=2), 4)
                self.assertEqual(count_filter(naive__day__lte=2), 7)
                self.assertEqual(count_filter(naive__day__gt=2), 5)
                self.assertEqual(count_filter(naive__day__gte=2), 8)
                self.assertEqual(count_filter(naive__day=2), 3)

                self.assertEqual(count_filter(naive__hour__lt=12), 6)
                self.assertEqual(count_filter(naive__hour__lte=12), 7)
                self.assertEqual(count_filter(naive__hour__gt=12), 5)
                self.assertEqual(count_filter(naive__hour__gte=12), 6)
                self.assertEqual(count_filter(naive__hour=12), 1)

                self.assertEqual(count_filter(naive__minute__lt=30), 4)
                self.assertEqual(count_filter(naive__minute__lte=30), 5)
                self.assertEqual(count_filter(naive__minute__gt=30), 7)
                self.assertEqual(count_filter(naive__minute__gte=30), 8)
                self.assertEqual(count_filter(naive__minute=30), 1)

                self.assertEqual(count_filter(naive__second__lt=6), 6)
                self.assertEqual(count_filter(naive__second__lte=6), 7)
                self.assertEqual(count_filter(naive__second__gt=6), 5)
                self.assertEqual(count_filter(naive__second__gte=6), 6)
                self.assertEqual(count_filter(naive__second=6), 1)

                self.assertEqual(count_filter(naive__week__lt=30), 7)
                self.assertEqual(count_filter(naive__week__lte=30), 7)
                self.assertEqual(count_filter(naive__week__gt=30), 5)
                self.assertEqual(count_filter(naive__week__gte=30), 5)
                self.assertEqual(count_filter(naive__week=30), 0)

                self.assertEqual(count_filter(naive__week_day__lt=4), 6)
                self.assertEqual(count_filter(naive__week_day__lte=4), 7)
                self.assertEqual(count_filter(naive__week_day__gt=4), 5)
                self.assertEqual(count_filter(naive__week_day__gte=4), 6)
                self.assertEqual(count_filter(naive__week_day=4), 1)

                self.assertEqual(
                    count_filter(naive__date__lt=datetime.date(2018, 12, 31)), 6
                )
                self.assertEqual(
                    count_filter(naive__date__lte=datetime.date(2018, 12, 31)), 7
                )
                self.assertEqual(
                    count_filter(naive__date__gt=datetime.date(2018, 12, 31)), 5
                )
                self.assertEqual(
                    count_filter(naive__date__gte=datetime.date(2018, 12, 31)), 6
                )
                self.assertEqual(
                    count_filter(naive__date=datetime.date(2018, 12, 31)), 1
                )

                if (
                    db.connection.vendor != "mysql"
                ):  # known bug in Django's mysql date handling
                    self.assertEqual(
                        count_filter(naive__time__lt=datetime.time(10, 30, 0)), 5
                    )
                    self.assertEqual(
                        count_filter(naive__time__lte=datetime.time(10, 30, 0)), 6
                    )
                    self.assertEqual(
                        count_filter(naive__time__gt=datetime.time(10, 30, 0)), 6
                    )
                    self.assertEqual(
                        count_filter(naive__time__gte=datetime.time(10, 30, 0)), 7
                    )
                    self.assertEqual(
                        count_filter(naive__time=datetime.time(10, 30, 0)), 1
                    )

        # Test in some out-there timezones
        test_in_timezone("utc")
        test_in_timezone("Pacific/Chatham")  # +12:45/+13:45
        test_in_timezone("Pacific/Marquesas")  # -09:30

    def test_date_extract_annotations(self):
        """
        Test that date truncating works regardless of active timezone.
        """
        timezone.activate("Australia/Adelaide")
        n = datetime.datetime(2017, 12, 31, 20, 10, 30, 123456)
        a = timezone.make_aware(n)
        o = NaiveDateTimeTestModel.objects.create(aware=a, naive=n)
        o.refresh_from_db()

        def query_transforms(module):
            return NaiveDateTimeTestModel.objects.annotate(
                year=getattr(module, "ExtractYear")("naive"),
                mon=getattr(module, "ExtractMonth")("naive"),
                day=getattr(module, "ExtractDay")("naive"),
                hour=getattr(module, "ExtractHour")("naive"),
                min=getattr(module, "ExtractMinute")("naive"),
                sec=getattr(module, "ExtractSecond")("naive"),
                week=getattr(module, "ExtractWeek")("naive"),
                dow=getattr(module, "ExtractWeekDay")("naive"),
            )[0]

        r = query_transforms(naivedatetimefield)
        self.assertEqual(
            [r.year, r.mon, r.day, r.hour, r.min, r.sec, r.week, r.dow],
            [2017, 12, 31, 20, 10, 30, 52, 1],
        )

    def test_add_los_angeles_local_timestamp(self):
        """
        activate a timezone that's not the default tz and is also not utc
        """

        timezone.activate("America/Los_Angeles")

        now = timezone.now()
        los_angeles_local_now = timezone.make_naive(now)

        self.assertTrue(timezone.is_aware(now))
        self.assertTrue(timezone.is_naive(los_angeles_local_now))

        self.assertEqual(now, timezone.make_aware(los_angeles_local_now))

        obj = NaiveDateTimeTestModel.objects.create(
            aware=now, naive=los_angeles_local_now
        )

        self.assertTrue(timezone.is_aware(obj.aware))
        self.assertTrue(timezone.is_naive(obj.naive))

        self.assertEqual(timezone.make_naive(obj.aware), obj.naive)

        # deactivate the timezone and make sure we still have our
        # same naive timestamp
        timezone.deactivate()

        self.assertTrue(timezone.is_aware(obj.aware))
        self.assertTrue(timezone.is_naive(obj.naive))

        self.assertEqual(obj.aware, now)
        self.assertEqual(obj.naive, los_angeles_local_now)

        self.assertNotEqual(timezone.make_naive(obj.aware), obj.naive)

    def test_select_by_naive(self):
        timezone.activate("America/Los_Angeles")

        n = datetime.datetime(2018, 4, 1, 18, 0)
        a = timezone.make_aware(n)

        o = NaiveDateTimeTestModel.objects.create(aware=a, naive=n)

        o.refresh_from_db()

        find_with_aware_in_la_timezone = NaiveDateTimeTestModel.objects.filter(
            aware__lt=(
                datetime.datetime(2018, 4, 1, 20, 0).replace(
                    tzinfo=timezone.get_current_timezone()
                )
            )
        ).count()

        self.assertTrue(find_with_aware_in_la_timezone == 1)

        find_with_naive_in_la_timezone = NaiveDateTimeTestModel.objects.filter(
            naive__lt=datetime.datetime(2018, 4, 1, 20, 0)
        ).count()

        self.assertTrue(find_with_naive_in_la_timezone == 1)

        timezone.activate(pytz.utc)

        find_with_aware_in_utc = NaiveDateTimeTestModel.objects.filter(
            aware__lt=(
                datetime.datetime(2018, 4, 1, 20, 0).replace(
                    tzinfo=timezone.get_current_timezone()
                )
            )
        ).count()

        self.assertTrue(find_with_aware_in_utc == 0)

        find_with_naive_in_utc = NaiveDateTimeTestModel.objects.filter(
            naive__lt=datetime.datetime(2018, 4, 1, 20, 0)
        ).count()

        self.assertTrue(find_with_naive_in_utc == 1)

    def test_nullable_naive_datetimefield(self):
        o = NullableNaiveDateTimeModel.objects.create(naive=None)
        o.refresh_from_db()
        self.assertIsNone(o.naive)


def identity(v):
    return v


@skipIf(connection.vendor != "postgresql", "AtTimeZone is only supported in PostgreSQL")
class AtTimeZoneTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.now = datetime.datetime(2019, 1, 15, 10)
        cls.perth_tz = pytz.timezone("Australia/Perth")
        cls.sydney_tz = pytz.timezone("Australia/Sydney")
        cls.adelaide_tz = pytz.timezone("Australia/Adelaide")

        cls.perth = NaiveDateTimeTestModel.objects.create(
            naive=cls.now,
            aware=timezone.make_aware(cls.now, cls.perth_tz),
            timezone="Australia/Perth",
        )

        cls.sydney = NaiveDateTimeTestModel.objects.create(
            naive=cls.now,
            aware=timezone.make_aware(cls.now, cls.sydney_tz),
            timezone="Australia/Sydney",
        )

    def test_annotate(self):
        self.assertQuerysetEqual(
            NaiveDateTimeTestModel.objects.annotate(
                naive_converted=AtTimeZone("aware", "timezone"),
                aware_converted=AtTimeZone("naive", "timezone"),
            ).values_list("naive_converted", "aware_converted"),
            [
                (self.now, timezone.make_aware(self.now, self.perth_tz)),
                (self.now, timezone.make_aware(self.now, self.sydney_tz)),
            ],
            transform=identity,
        )

    def test_db_aware_db_timezone(self):
        self.assertQuerysetEqual(
            NaiveDateTimeTestModel.objects.filter(
                naive=AtTimeZone(
                    "aware",
                    "timezone",
                )
            ),
            [self.perth, self.sydney],
            transform=identity,
        )

    def test_db_aware_value_timezone(self):
        self.assertQuerysetEqual(
            NaiveDateTimeTestModel.objects.filter(
                naive__lt=AtTimeZone(
                    "aware",
                    Value("Australia/Adelaide"),
                )
            ),
            [self.perth],
            transform=identity,
        )

    def test_db_naive_db_timezone(self):
        self.assertQuerysetEqual(
            NaiveDateTimeTestModel.objects.filter(
                aware=AtTimeZone(
                    "naive",
                    "timezone",
                )
            ),
            [self.perth, self.sydney],
            transform=identity,
        )

    def test_db_naive_value_timezone(self):
        self.assertQuerysetEqual(
            NaiveDateTimeTestModel.objects.filter(
                aware__lt=AtTimeZone(
                    "naive",
                    Value("Australia/Adelaide"),
                )
            ),
            [self.sydney],
            transform=identity,
        )

    def test_value_aware_db_timezone(self):
        self.assertQuerysetEqual(
            NaiveDateTimeTestModel.objects.filter(
                naive__lt=AtTimeZone(
                    Value(timezone.make_aware(self.now, self.adelaide_tz)),
                    "timezone",
                )
            ),
            [self.sydney],
            transform=identity,
        )

    def test_raw_aware_db_timezone(self):
        self.assertQuerysetEqual(
            NaiveDateTimeTestModel.objects.filter(
                naive__lt=AtTimeZone(
                    timezone.make_aware(self.now, self.adelaide_tz),
                    "timezone",
                )
            ),
            [self.sydney],
            transform=identity,
        )

    def test_value_aware_value_timezone(self):
        self.assertQuerysetEqual(
            NaiveDateTimeTestModel.objects.filter(
                naive=AtTimeZone(
                    Value(timezone.make_aware(self.now, self.adelaide_tz)),
                    Value("Australia/Adelaide"),
                )
            ),
            [self.perth, self.sydney],
            transform=identity,
        )

    def test_raw_aware_value_timezone(self):
        self.assertQuerysetEqual(
            NaiveDateTimeTestModel.objects.filter(
                naive=AtTimeZone(
                    timezone.make_aware(self.now, self.adelaide_tz),
                    Value("Australia/Adelaide"),
                )
            ),
            [self.perth, self.sydney],
            transform=identity,
        )

    def test_value_naive_db_timezone(self):
        self.assertQuerysetEqual(
            NaiveDateTimeTestModel.objects.filter(
                aware=AtTimeZone(
                    Value(self.now),
                    "timezone",
                )
            ),
            [self.perth, self.sydney],
            transform=identity,
        )

    def test_raw_naive_db_timezone(self):
        self.assertQuerysetEqual(
            NaiveDateTimeTestModel.objects.filter(
                aware=AtTimeZone(
                    self.now,
                    "timezone",
                )
            ),
            [self.perth, self.sydney],
            transform=identity,
        )

    def test_value_naive_value_timezone(self):
        self.assertQuerysetEqual(
            NaiveDateTimeTestModel.objects.filter(
                aware__lt=AtTimeZone(
                    Value(self.now),
                    Value("Australia/Adelaide"),
                )
            ),
            [self.sydney],
            transform=identity,
        )

    def test_raw_naive_value_timezone(self):
        self.assertQuerysetEqual(
            NaiveDateTimeTestModel.objects.filter(
                aware__lt=AtTimeZone(
                    self.now,
                    Value("Australia/Adelaide"),
                )
            ),
            [self.sydney],
            transform=identity,
        )
