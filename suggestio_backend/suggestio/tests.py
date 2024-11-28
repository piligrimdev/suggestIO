from django.test import TestCase


class SampleTest(TestCase):
    def setUp(self) -> None:
        print('setUp')

    def tearDown(self) -> None:
        print('tearDown')

    def test_sample(self):
        self.assertTrue(1 == 1)
