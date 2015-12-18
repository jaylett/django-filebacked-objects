from django.test import SimpleTestCase as TestCase

from django_FBO import Q

from .utils import RST_FBO


class TestOperators(TestCase):
    """Test various operators."""

    def test_equals(self):
        self.assertEqual(
            'test2.rst',
            RST_FBO().objects.get(name__equals='test2.rst').name,
        )

    def test_implicit_equals(self):
        self.assertEqual(
            'test2.rst',
            RST_FBO().objects.get(name='test2.rst').name,
        )

    def test_lte(self):
        self.assertEqual(
            [
                'test1.rst',
                'test2.rst',
            ],
            [
                o.name for o in RST_FBO(
                ).objects.filter(
                    name__lte='test2.rst',
                ).order_by('name')
            ],
        )

    def test_gte(self):
        self.assertEqual(
            [
                'test2.rst',
                'test3.rst',
            ],
            [
                o.name for o in RST_FBO(
                ).objects.filter(
                    name__gte='test2.rst',
                ).order_by('name')
            ],
        )

    def test_contains(self):
        self.assertEqual(
            'test2.rst',
            RST_FBO().get(tags__contains='tag2').name,
        )

    def test_in(self):
        self.assertEqual(
            [
                'test2.rst',
                'test3.rst',
            ],
            [
                o.name for o in RST_FBO().filter(
                    size__in=[
                        'little',
                        'middling',
                    ],
                )
            ],
        )

    def test_no_such_operator(self):
        with self.assertRaises(ValueError):
            RST_FBO().filter(name__sort_of='test1').get()
