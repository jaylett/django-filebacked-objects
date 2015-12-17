import os.path
from django.test import SimpleTestCase as TestCase

from django_FBO import FBO, Q

from .utils import RST_FBO, TEST_FILES_ROOT


class TestAll(TestCase):
    """
    Can we read all objects correctly?
    """

    def test_everything(self):
        """Just find all file objects."""

        qs = FBO(
            path=TEST_FILES_ROOT,
        ).exclude(
            name__glob='*~',
        ).exclude(
            name__glob='*.meta',
        )

        self.assertEqual(
            5,
            qs.count(),
        )
        self.assertEqual(
            {
                'test1.md',
                'test2.md',
                'test1.rst',
                'test2.rst',
                'test3.rst',
            },
            { o.name for o in qs },
        )

    def test_glob_restriction(self):
        """With globbing."""

        qs = FBO(
            path=TEST_FILES_ROOT,
            glob='*.md',
        ).all()

        self.assertEqual(
            2,
            qs.count(),
        )
        self.assertEqual(
            {
                'test1.md',
                'test2.md',
            },
            { o.name for o in qs },
        )


class TestGet(TestCase):
    """
    Can we read a single object correctly?
    """

    def test_get(self):
        """Fetch a single file instance."""

        qs = FBO(
            path=TEST_FILES_ROOT,
        ).all()

        obj = qs.get(
            name='test1.md',
        )

        self.assertEqual(
            'test1.md',
            obj.name,
        )

    def test_get_honours_glob(self):
        """Cannot get not matching the glob."""

        with self.assertRaises(FBO.DoesNotExist):
            qs = FBO(
                path=TEST_FILES_ROOT,
                glob='*.md',
            ).all().get(
                name='test1.rst',
            )

    def test_missing(self):
        with self.assertRaises(FBO.DoesNotExist):
            FBO(
                path=TEST_FILES_ROOT,
            ).all().get(
                name='missing.txt',
            )


class TestOrdering(TestCase):
    """
    Can we order objects based on metadata?
    """

    def test_intrinsic_metadata(self):
        """Intrinsic metadata."""

        qs = FBO(
            path=TEST_FILES_ROOT,
            glob='*.md',
            metadata='.meta',
        ).all()

        self.assertEqual(
            2,
            qs.count(),
        )
        # Have to test this both ways so that however it
        # comes out of the filesystem "by default" (ie
        # intrinsically, probably inode ordering) we'll get
        # a failure if our explicit ordering isn't applied.
        self.assertEqual(
            'test1.md',
            qs.order_by('name')[0].name,
        )
        self.assertEqual(
            'test2.md',
            qs.order_by('-name')[0].name,
        )

    def test_extrinsic_metadata(self):
        """Various format front matter."""

        qs = FBO(
            path=TEST_FILES_ROOT,
            glob='*.rst',
            metadata=FBO.MetadataInFileHead,
        ).all()

        self.assertEqual(
            3,
            qs.count(),
        )
        # Have to test this both ways so that however it
        # comes out of the filesystem "by default" (ie
        # intrinsically, probably inode ordering) we'll get
        # a failure if our explicit ordering isn't applied.
        self.assertEqual(
            'test1.rst',
            qs.order_by('title')[0].name,
        )
        self.assertEqual(
            'test3.rst',
            qs.order_by('-title')[0].name,
        )


class TestObjects(TestCase):
    """
    Can we access object attributes?
    """

    def test_content(self):
        """Access the primary content."""

        obj = FBO(
            path=TEST_FILES_ROOT,
        ).all().get(
            name='test1.md',
        )

        self.assertEqual(
            'A short work by me, for you to read.\n',
            obj.content,
        )

    def test_intrinsic(self):
        """Intrinsic (name and path)."""

        obj = FBO(
            path=TEST_FILES_ROOT,
        ).all().get(
            name='test1.rst',
        )

        self.assertEqual(
            'test1.rst',
            obj.name,
        )
        self.assertEqual(
            os.path.join(TEST_FILES_ROOT, 'test1.rst'),
            obj.path,
        )

    def test_extrinsic(self):
        """Extrinsic (metadata)."""

        obj = FBO(
            path=TEST_FILES_ROOT,
            metadata=FBO.MetadataInFileHead,
        ).all().get(
            name='test3.rst',
        )

        self.assertEqual(
            'Me',
            obj.author,
        )
        self.assertEqual(
            'little',
            obj.size,
        )
        # And access ones directly that don't work as attributes
        self.assertEqual(
            'JSON',
            obj.metadata.get('metadata-format'),
        )
        self.assertEqual(
            {
                'title',
                'author',
                'size',
                'tags',
                'metadata-format',
            },
            set(
                obj.metadata.keys()
            ),
        )


class TestMetadataFormats(TestCase):
    """
    Can we process YAML and JSON metadata properly and automatically?
    """

    def test_json(self):
        """Explicit JSON."""

        obj = FBO(
            path=TEST_FILES_ROOT,
            glob='*.rst',
            metadata=FBO.MetadataInFileHead,
        ).all().get(
            name='test3.rst',
        )

        self.assertEqual(
            'This one is third in the alphabet',
            obj.title,
        )
        self.assertEqual(
            'My little explicit JSON test.\n',
            obj.content,
        )

    def test_implicit_yaml(self):
        """Implicit YAML."""

        obj = FBO(
            path=TEST_FILES_ROOT,
            glob='*.rst',
            metadata=FBO.MetadataInFileHead,
        ).all().get(
            name='test1.rst',
        )

        self.assertEqual(
            'At the start of the alphabet',
            obj.title,
        )
        self.assertEqual(
            'My little implicit YAML test.\n',
            obj.content,
        )

    def test_explicit_yaml(self):
        """Explicit YAML."""

        obj = FBO(
            path=TEST_FILES_ROOT,
            glob='*.rst',
            metadata=FBO.MetadataInFileHead,
        ).all().get(
            name='test2.rst',
        )

        self.assertEqual(
            'Second in the alphabet',
            obj.title,
        )
        self.assertEqual(
            'My little explicit YAML test.\n',
            obj.content,
        )

    def test_no_metadata(self):
        """Ignore front matter."""

        obj = FBO(
            path=TEST_FILES_ROOT,
            glob='*.rst',
        ).all().get(
            name='test2.rst',
        )

        with self.assertRaises(KeyError):
            _ = obj.title
        self.assertEqual(
            '---\ntitle: Second in the alphabet\nsize: middling\ntags:\n - tag2\n - tag_all\n---\nMy little explicit YAML test.\n',
            obj.content,
        )


class TestConvenience(TestCase):
    """Test some convenience shims and wrappers."""

    def test_objects(self):
        """FBO.objects, kind of like the ORM."""

        obj = FBO(
            path=TEST_FILES_ROOT,
            metadata=FBO.MetadataInFileHead,
        ).objects.all().filter(
            name__glob='*.rst',
        ).get(
            name='test2.rst',
        )

        self.assertEqual(
            'Second in the alphabet',
            obj.title,
        )


class TestSubclassing(TestCase):
    """Can we subclass FBO to set defaults?"""

    def test_simple_defaults(self):
        """Set new defaults and accept them."""

        qs = RST_FBO().objects.all()
        self.assertEqual(
            3,
            qs.count(),
        )
        self.assertEqual(
            'Second in the alphabet',
            qs.get(name='test2.rst').title,
        )

    def test_override_defaults(self):
        """Set new defaults and override some on instantiation."""

        class MyFBO(FBO):
            path = '/tmp/'
            metadata = FBO.MetadataInFileHead
            glob='*.rst'

        qs = MyFBO(
            path=TEST_FILES_ROOT,
        ).objects.all()
        self.assertEqual(
            3,
            qs.count(),
        )
        self.assertEqual(
            'Second in the alphabet',
            qs.get(name='test2.rst').title,
        )


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
