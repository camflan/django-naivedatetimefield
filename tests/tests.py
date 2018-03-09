from django.test import TestCase

from django.contrib.auth.models import User
from django.utils import timezone

from .models import (NaiveDateTimeTestModel,
                     NaiveDateTimeAutoNowAddModel,
                     NaiveDateTimeAutoNowModel)


class NaiveDateTimeFieldTestCase(TestCase):
    '''
    main test case for NaiveDateTimeField
    '''

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username='supertester',
            email='super@test.com',
            password='testing12345'
        )

    def test_auto_now_add(self):
        obj = NaiveDateTimeAutoNowAddModel.objects.create()

        self.assertTrue(timezone.is_aware(obj.aware))
        self.assertTrue(timezone.is_naive(obj.naive))

    def test_auto_now(self):
        obj = NaiveDateTimeAutoNowModel.objects.create()

        self.assertTrue(timezone.is_aware(obj.aware))
        self.assertTrue(timezone.is_naive(obj.naive))

    def test_add_los_angeles_local_timestamp(self):
        '''
        activate a timezone that's not the default tz and is also not utc
        '''

        timezone.activate("America/Los_Angeles")

        now = timezone.now()
        los_angeles_local_now = timezone.make_naive(now)

        self.assertTrue(timezone.is_aware(now))
        self.assertTrue(timezone.is_naive(los_angeles_local_now))

        self.assertEqual(now, timezone.make_aware(los_angeles_local_now))

        obj = NaiveDateTimeTestModel.objects.create(
            aware=now,
            naive=los_angeles_local_now
        )

        self.assertTrue(timezone.is_aware(obj.aware))
        self.assertTrue(timezone.is_naive(obj.naive))

        self.assertEqual(timezone.make_naive(obj.aware), obj.naive)

        # deactivate the timezone and make sure we still have our same naive timestamp
        timezone.deactivate()

        self.assertTrue(timezone.is_aware(obj.aware))
        self.assertTrue(timezone.is_naive(obj.naive))

        self.assertEqual(obj.aware, now)
        self.assertEqual(obj.naive, los_angeles_local_now)

        self.assertNotEqual(timezone.make_naive(obj.aware), obj.naive)
