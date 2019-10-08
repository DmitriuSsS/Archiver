from Parser.NotArchiveException import NotArchiveException
from zlib import crc32


def get_hash_file(fd, length):
    count_read = 256 * 1024 * 1024
    hash_list = []
    pointer = 0
    delta = min(count_read, length - pointer)
    content = fd.read(delta)
    while pointer < length and content:
        hash_list.append(crc32(content))
        delta = min(count_read, length - pointer)
        pointer += delta
        content = fd.read(delta)
    hash_str = ''
    for h in hash_list:
        hash_str += str(h)
    return hash_str.encode()


class File:
    def __init__(self, fd, start_position):
        fd.seek(start_position)
        length_name_file = fd.read(1)[0]
        name = fd.read(length_name_file).decode('utf-8')
        self.name = name

        length_hash = fd.read(1)[0] * 256 + fd.read(1)[0]
        hash_file = fd.read(length_hash)
        self.hash = hash_file

        bytes_length_file = fd.read(5)
        length_file = 0
        pow_n = 1
        for i in range(1, 6):
            length_file += pow_n * bytes_length_file[-i]
            pow_n <<= 8
        self.length = length_file

        self.start = start_position + length_name_file + length_hash + 8
        self.fd = fd

        if not self.check_internal_file():
            raise NotArchiveException

    def check_internal_file(self):
        self.fd.seek(self.start)
        actually_hash_file = get_hash_file(self.fd, self.length)
        return self.hash == actually_hash_file
