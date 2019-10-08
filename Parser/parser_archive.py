from Parser.NotArchiveException import NotArchiveException
from Parser.File import File


def check_file(file_name):
    try:
        ListingFiles(file_name)
        return True
    except (NotArchiveException, UnicodeDecodeError, IndexError):
        return False


class ListingFiles:
    def __init__(self, name_archive):
        try:
            self.files = []
            self.empty_dirs = []
            with open(name_archive, 'rb') as archive_fd:
                count_files = archive_fd.read(1)[0]
                count_dirs = archive_fd.read(1)[0]

                pointer = 2
                for _ in range(count_files):
                    file = File(archive_fd, pointer)
                    pointer = file.start + file.length
                    self.files.append(file)

                archive_fd.seek(pointer)
                for _ in range(count_dirs):
                    len_name_dir = archive_fd.read(1)[0]
                    name_dir = archive_fd.read(len_name_dir)
                    if len(name_dir) != len_name_dir:
                        raise NotArchiveException
                    self.empty_dirs.append(name_dir.decode('utf-8'))
        except (IndexError, NotArchiveException):
            raise NotArchiveException

    def __str__(self):
        return '\n'.join([file.name for file in self.files])
