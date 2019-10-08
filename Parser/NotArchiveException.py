class NotArchiveException(Exception):
    def __str__(self):
        return "File isn't archive"
