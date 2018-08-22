import datetime
import pytz

from django.test import TestCase

from django.db.models import F
from django.contrib.auth.models import User
from django.utils import timezone

from .models import (
    NaiveDateTimeTestModel,
    NaiveDateTimeAutoNowAddModel,
    NaiveDateTimeAutoNowModel,
)


class NaiveDateTimeFieldTestCase(TestCase):
    """
    main test case for NaiveDateTimeField
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="supertester", email="super@test.com", password="testing12345"
        )

    def test_auto_now_add(self):
        obj = NaiveDateTimeAutoNowAddModel.objects.create()

        self.assertTrue(timezone.is_aware(obj.aware))
        self.assertTrue(timezone.is_naive(obj.naive))

    def test_auto_now(self):
        obj = NaiveDateTimeAutoNowModel.objects.create()

        self.assertTrue(timezone.is_aware(obj.aware))
        self.assertTrue(timezone.is_naive(obj.naive))

    def xtest_time_lookup(self):
        """
        This should test that __time lookups work properly on naive datetime fields
        """
        timezone.activate("America/Los_Angeles")

        n = datetime.datetime(2018, 4, 1, 18, 0)
        a = timezone.make_aware(n)

        o = NaiveDateTimeTestModel.objects.create(aware=a, naive=n)

        o.refresh_from_db()

        results = NaiveDateTimeTestModel.objects.annotate(
            hour=F("naive__time__hour")
        ).filter(naive__time__hour__gte=1)

        for ndt in NaiveDateTimeTestModel.objects.all():
            print(ndt.id, ndt.naive)

        print(results, results.query)

        self.assertTrue(results == 1)

    def xtest_date_lookup(self):
        """
        This should test that __date lookups work properly on naive datetime fields
        """
        pass

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
