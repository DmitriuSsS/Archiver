class Link:
    max_offset = 4 * 1024 - 1
    max_len = 15

    def __init__(self, offset, len_copy):
        self.offset = offset
        self.len_copy = len_copy

    def get_byte_interpretation(self):
        return [self.offset // 16, (self.offset % 16) * 16 + self.len_copy]

    @staticmethod
    def decode_bytes_as_link(two_bytes):
        offset = two_bytes[0] * 16 + two_bytes[1] // 16
        length = two_bytes[1] % 16
        return offset, length

    @staticmethod
    def copy(array, two_bytes):
        offset, length = Link.decode_bytes_as_link(two_bytes)
        pointer = len(array) - offset
        for i in range(length):
            array.append(array[pointer + i])
