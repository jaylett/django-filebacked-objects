import os.path
from django.core.exceptions import (
    ObjectDoesNotExist,
    MultipleObjectsReturned,
)
from django.test import SimpleTestCase as TestCase
from itertools import combinations

from django_FBO import FBO, FileObject

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
            7,
            qs.count(),
        )
        self.assertEqual(
            {
                'index.md',
                'subdir/index.md',
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
            4,
            qs.count(),
        )
        self.assertEqual(
            {
                'index.md',
                'subdir/index.md',
                'test1.md',
                'test2.md',
            },
            { o.name for o in qs },
        )


class TestClone(TestCase):
    """Does clone do so properly?"""

    def test_filters_are_clones_not_references(self):
        """_filter must be cloned"""
        # Everything else is considered immutable
        qs = FBO(
            path=TEST_FILES_ROOT,
            glob='*.rst',
        )
        self.assertEqual(
            3,
            qs.count(),
        )
        qs2 = qs.filter(name='test1.rst')
        self.assertEqual(
            3,
            qs.count(),
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

        with self.assertRaises(ObjectDoesNotExist):
            qs = FBO(
                path=TEST_FILES_ROOT,
                glob='*.md',
            ).all().get(
                name='test1.rst',
            )

    def test_get_by_index(self):
        """Can fetch a single instance by subscript."""

        qs = FBO(
            path=TEST_FILES_ROOT,
        ).exclude(
            name__glob='*~',
        ).exclude(
            name__glob='*.meta',
        ).order_by('name')

        obj = qs[0]
        self.assertEqual(
            'index.md',
            obj.name,
        )

    def test_get_by_indexerror(self):
        """Get an IndexError if we go off the end."""

        qs = FBO(
            path=TEST_FILES_ROOT,
        ).exclude(
            name__glob='*~',
        ).exclude(
            name__glob='*.meta',
        ).order_by('name')

        with self.assertRaises(IndexError):
            obj = qs[10]

    def test_multiple(self):
        """Can't get if we resolve multiple objects."""

        with self.assertRaises(MultipleObjectsReturned):
            _ = RST_FBO().get()

    def test_missing(self):
        with self.assertRaises(ObjectDoesNotExist):
            FBO(
                path=TEST_FILES_ROOT,
            ).all().get(
                name='missing.txt',
            )


class TestEquality(TestCase):
    """
    Are different FileObjects different, are the same ones
    the same?
    """

    def test_equal(self):
        """Two FileObjects with the same path are the same."""

        qs = FBO(path=TEST_FILES_ROOT, glob='*.md').order_by('name')
        qs2 = FBO(path=TEST_FILES_ROOT, glob='*.md').order_by('name')
        self.assertEqual(
            qs[0],
            qs2[0],
        )

    def test_unequal(self):
        """FileObjects with different paths are all different."""

        qs = FBO(path=TEST_FILES_ROOT, glob='*.md').order_by('name')
        # There are four of these.
        for a, b in combinations(qs.all(), 2):
            self.assertNotEqual(a, b)

    def test_none(self):
        """FileObjects are never equal to None."""

        qs = FBO(path=TEST_FILES_ROOT, glob='*.md').order_by('name')
        self.assertNotEqual(None, qs[0])
        self.assertNotEqual(qs[0], None)

    def test_other_types(self):
        """FileObjects are never equal to non-FileObject."""

        qs = FBO(path=TEST_FILES_ROOT, glob='*.md').order_by('name')
        self.assertNotEqual(1, qs[0])
        self.assertNotEqual(NotImplementedError, qs[0])
        class MockFileObject:
            path = qs[0].path
        self.assertNotEqual(MockFileObject(), qs[0])


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
            4,
            qs.count(),
        )
        # Have to test this both ways so that however it
        # comes out of the filesystem "by default" (ie
        # intrinsically, probably inode ordering) we'll get
        # a failure if our explicit ordering isn't applied.
        self.assertEqual(
            'index.md',
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
            metadata=FileObject.MetadataInFileHead,
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
            metadata=FileObject.MetadataInFileHead,
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
            metadata=FileObject.MetadataInFileHead,
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
            metadata=FileObject.MetadataInFileHead,
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
            metadata=FileObject.MetadataInFileHead,
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

        self.assertIsNone(obj.title)
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
            metadata=FileObject.MetadataInFileHead,
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
            metadata = FileObject.MetadataInFileHead
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

    def test_override_model(self):
        """Change the FileObject model."""

        class MyModel(FileObject):
            def render(self):
                return self.content

        class MyFBO(FBO):
            path = TEST_FILES_ROOT
            metadata = FileObject.MetadataInFileHead
            model = MyModel

        self.assertEqual(
            'My little explicit YAML test.\n',
            MyFBO().objects.get(name='test2.rst').render(),
        )


class TestSlice(TestCase):
    """Can we slice FBO?"""

    def setUp(self):
        self.qs = FBO(
            path=TEST_FILES_ROOT,
        ).exclude(
            name__glob='*~',
        ).exclude(
            name__glob='*.meta',
        ).order_by(
            'name'
        )

    def test_sliced_filter(self):
        # We want to test that the slice is applied last.
        # However we prefetch at the start of the iterator,
        # so we need to cause that prefetch to happen before
        # the filter is applied, so that the filter will be
        # applied within the iterator rather than in the
        # prefetch.
        #
        # This incidentally also showed that our prefetch
        # cache wasn't being propagated down to sub querysets,
        # so it acts as a regression test against that also.
        qs = self.qs.clone()
        _ = iter(qs)
        qs = qs.filter(
            name__glob='*.rst'
        )[2:]

        self.assertEqual(
            [
                'test3.rst',
            ],
            [ o.name for o in qs ],
        )

    def test_open_both(self):
        qs = self.qs[:]

        self.assertEqual(
            [
                'index.md',
                'subdir/index.md',
                'test1.md',
                'test1.rst',
                'test2.md',
                'test2.rst',
                'test3.rst',
            ],
            [ o.name for o in qs ],
        )

    def test_open_start(self):
        qs = self.qs[:4]

        self.assertEqual(
            [
                'index.md',
                'subdir/index.md',
                'test1.md',
                'test1.rst',
            ],
            [ o.name for o in qs ],
        )

    def test_open_end(self):
        qs = self.qs[1:]

        self.assertEqual(
            [
                'subdir/index.md',
                'test1.md',
                'test1.rst',
                'test2.md',
                'test2.rst',
                'test3.rst',
            ],
            [ o.name for o in qs ],
        )

    def test_closed(self):
        qs = self.qs[1:3]

        self.assertEqual(
            [
                'subdir/index.md',
                'test1.md',
            ],
            [ o.name for o in qs ],
        )

    def test_sliced_slice1(self):
        qs = self.qs[1:4][:2]

        self.assertEqual(
            [
                'subdir/index.md',
                'test1.md',
            ],
            [ o.name for o in qs ],
        )

    def test_sliced_slice2(self):
        qs = self.qs[1:3][:4]

        self.assertEqual(
            [
                'subdir/index.md',
                'test1.md',
            ],
            [ o.name for o in qs ],
        )

    def test_sliced_slice3(self):
        qs = self.qs[:2][1:4]

        self.assertEqual(
            [
                'subdir/index.md',
                'test1.md',
            ],
            [ o.name for o in qs ],
        )

    def test_sliced_slice4(self):
        qs = self.qs[1:4][1:3]

        self.assertEqual(
            [
                'test1.md',
                'test1.rst',
            ],
            [ o.name for o in qs ],
        )

    def test_step(self):
        qs = self.qs[1::2]

        self.assertEqual(
            [
                'subdir/index.md',
                'test1.rst',
                'test2.rst',
            ],
            [ o.name for o in qs ],
        )

    def test_sliced_step1(self):
        qs = self.qs[1::2][:1]

        self.assertEqual(
            [
                'subdir/index.md',
            ],
            [ o.name for o in qs ],
        )

    def test_sliced_step2(self):
        qs = self.qs[1::2][::]

        self.assertEqual(
            [
                'subdir/index.md',
                'test1.rst',
                'test2.rst',
            ],
            [ o.name for o in qs ],
        )

    def test_sliced_step3(self):
        qs = self.qs[1:][::2]

        self.assertEqual(
            [
                'subdir/index.md',
                'test1.rst',
                'test2.rst',
            ],
            [ o.name for o in qs ],
        )


class TestSlugStripping(TestCase):
    """Can we use the slug stripping controls?"""

    def test_slug_suffices(self):
        """Can we support optional suffices on the slug within the filename?"""

        qs = FBO(
            path=TEST_FILES_ROOT,
            slug_suffices=['.md'],
        ).exclude(
            name__glob='*~',
        ).filter(
            name__glob='*.md',
        ).order_by(
            'name'
        )

        self.assertEqual(
            {
                'index',
                'subdir/index',
                'test1',
                'test2',
            },
            {
                o.slug for o in qs
            },
        )

    def test_slug_index_stripping(self):
        """Can we strip 'index'?"""

        qs = FBO(
            path=TEST_FILES_ROOT,
            slug_suffices=['.md'],
            slug_strip_index=True,
        ).exclude(
            name__glob='*~',
        ).filter(
            name__glob='*.md',
        ).order_by(
            'name'
        )

        self.assertEqual(
            {
                '',
                'subdir/',
                'test1',
                'test2',
            },
            {
                o.slug for o in qs
            },
        )
