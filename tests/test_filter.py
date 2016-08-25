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

    def test_startswith(self):
        self.assertEqual(
            'test2.rst',
            RST_FBO().get(slug__startswith='test2').name,
        )

    def test_endswith(self):
        self.assertEqual(
            'test2.rst',
            RST_FBO().get(name__endswith='test2.rst').name,
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


class TestQ(TestCase):
    """Tests for using Q objects in filtering."""

    def test_simple_filter(self):
        """Single leg Q in filter()"""

        self.assertEquals(
            'test1.rst',
            RST_FBO().filter(
                Q(name='test1.rst'),
            ).get().name,
        )

    def test_simple_exclude(self):
        """Single leg Q in exclude()"""

        self.assertEquals(
            [
                'test1.rst',
                'test2.rst',
            ],
            [
                o.name for o in RST_FBO().exclude(
                    Q(name='test3.rst'),
                )
            ],
        )

    def test_simple_get(self):
        """Single leg Q in get()"""

        self.assertEquals(
            'test1.rst',
            RST_FBO().get(
                Q(name='test1.rst'),
            ).name,
        )

    def test_or(self):
        """Logical or Qs"""

        self.assertEquals(
            [
                'test1.rst',
                'test2.rst',
            ],
            [
                o.name for o in RST_FBO().filter(
                    Q(name='test1.rst') | Q(name='test2.rst'),
                )
            ],
        )

    def test_and(self):
        """Logical and Qs"""

        self.assertEquals(
            'test1.rst',
            RST_FBO().get(
                Q(name='test1.rst') & Q(size='large'),
            ).name
        )

    def test_tree(self):
        """Complex tree of Qs"""

        self.assertEquals(
            'test1.rst',
            RST_FBO().get(
                (
                    Q(name='test1.rst') | Q(name='test2.rst')
                ) & Q(size='large'),
            ).name
        )
