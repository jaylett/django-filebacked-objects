class DoesNotExist(Exception):
    pass


class FBO:
    MetadataInFileHead = True
    DoesNotExist = DoesNotExist

    def __init__(self, **kwargs):
        pass

    @property
    def objects(self):
        return self

    def all(self):
        return self

    def order_by(self, args):
        return self
    
    def get(self, **kwargs):
        raise DoesNotExist
    
    def count(self):
        return 0
