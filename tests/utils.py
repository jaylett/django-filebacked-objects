import os.path

from django_FBO import FBO, Q


TEST_FILES_ROOT=os.path.join(
    os.path.dirname(__file__),
    'files',
)


class RST_FBO(FBO):
    path = TEST_FILES_ROOT
    metadata = FBO.MetadataInFileHead
    glob='*.rst'


