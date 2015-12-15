from django.test import TestCase

from django_FBO import FBO, Q


TEST_FILES_ROOT=os.path.join(
    os.path.dirname(__file__),
    'files',
)


class TestAll(TestCase):
    """
    Can we read all objects correctly?
    """

    def test_everything(self):
        """Just find all file objects."""

        qs = FBO(
            path=TEST_FILES_ROOT,
        ).all()

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
            }
            set(
                [ o.name for o in qs ]
            ),
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
            }
            set(
                [ o.name for o in qs ]
            ),
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
            ).all.get(
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
    Can we read objects from files correctly?
    """

    def test_extrinsic_metadata(self):
        """Extrinsic metadata."""

        qs = FBO(
            path=TEST_FILES_ROOT,
            glob='*.md',
            metadata='.meta',
        ).all()

        self.assertEqual(
            2,
            qs.count(),
        )
        self.assertEqual(
            'test1.md',
            qs.order_by('title')[0].name,
        )

    def test_intrinsic_metadata(self):
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
        self.assertEqual(
            'test1.rst',
            qs.order_by('title')[0].title,
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
            name='test3.rst',
        )

        self.assertEqual(
            'My little explicit JSON test.',
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
        # And transformed keys
        self.assertEqual(
            'JSON',
            obj.metadata_format,
        )
        # And access it directly
        self.assertEqual(
            'JSON',
            obj.metadata.get('metadata-format'),
        )
        self.assertEqual(
            {
                'title',
                'author',
                'size',
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
            obj.name,
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
            'A the start of the alphabet',
            obj.name,
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
            obj.name,
        )
