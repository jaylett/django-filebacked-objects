import os.path

from django_FBO import FBO, FileObject


TEST_FILES_ROOT=os.path.join(
    os.path.dirname(__file__),
    'files',
)


class RST_FBO(FBO):
    path = TEST_FILES_ROOT
    metadata = FileObject.MetadataInFileHead
    glob='*.rst'
