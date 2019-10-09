import os

# Для запуска тестов через консоль
# import sys
# sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir))

import archiver
import tempfile
import argparse
import unittest.mock
import LZ77.unzipper as unzipper
import LZ77.zipper as zipper
from LZ77.Link import Link
from Parser import parser_archive
from Parser.File import get_hash_file
from shutil import rmtree
from parameterized import parameterized

test_file = os.path.join('tests', 'test_log.txt')


def create_file(name):
    dir_of_file = os.path.dirname(name)
    if not os.path.exists(dir_of_file) and dir_of_file != '':
        os.makedirs(dir_of_file)
    open(name, 'wb+').close()


def create_dir(name):
    if not os.path.exists(name):
        os.makedirs(name)


def create_tree():
    create_dir(os.path.join('Test', 'Test0', 'Test00'))
    create_dir(os.path.join('Test', 'Test2'))
    create_file(os.path.join('Test', 'Test1', 'Test10', 'file.txt'))
    create_file(os.path.join('Test', 'Test1', 'file1.txt'))


class TestLink(unittest.TestCase):
    @parameterized.expand([[5, 4],
                           [1, 3],
                           [6, 3]
                           ])
    def test_creator(self, offset, len_copy):
        link = Link(offset, len_copy)
        self.assertEqual(offset, link.offset)
        self.assertEqual(len_copy, link.len_copy)

    @parameterized.expand([[0, 39, Link(2, 7)],
                           [0, 16, Link(1, 0)],
                           [2, 15, Link(32, 15)],
                           [255, 255, Link(Link.max_offset, Link.max_len)]
                           ])
    def test_byte_interpretation(self, first_byte, second_byte, link):
        self.assertEqual([first_byte, second_byte], link.get_byte_interpretation())

    @parameterized.expand([[9, 15, (9 * 16, 15)],
                           [0, 0, (0, 0)],
                           [255, 255, (Link.max_offset, Link.max_len)],
                           [35, 78, (35 * 16 + 4, 14)]
                           ])
    def test_decode__bytes_as_link(self, first_byte, second_byte, result):
        self.assertEqual(result, Link.decode_bytes_as_link([first_byte, second_byte]))

    @parameterized.expand([[Link(25, 10)],
                           [Link(1, 0)],
                           [Link(2341, 14)],
                           [Link(Link.max_offset, Link.max_len)]
                           ])
    def test_complex_code_decode(self, link):
        self.assertEqual((link.offset, link.len_copy), Link.decode_bytes_as_link(link.get_byte_interpretation()))

    def test_copy(self):
        array = [1, 2, 3]
        Link.copy(array, Link(3, 5).get_byte_interpretation())
        self.assertEqual([1, 2, 3, 1, 2, 3, 1, 2], array)
        Link.copy(array, Link(6, 2).get_byte_interpretation())
        self.assertEqual([1, 2, 3, 1, 2, 3, 1, 2, 3, 1], array)
        Link.copy(array, Link(1, 4).get_byte_interpretation())
        self.assertEqual([1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 1, 1, 1, 1], array)


class TestArchive(unittest.TestCase):
    @parameterized.expand([[b''],
                           [b'compression decompression'],
                           [b'qwertyuiopasdfghjklzxcvbnm']
                           ])
    def test_extract_links(self, string):
        self.assertTrue(self.check_links(string, zipper.extract_links(string)))

    @staticmethod
    def check_links(string, links):
        for link in links:
            if string[link:links[link].len_copy:] != string[link - links[link].offset:links[link].len_copy:]:
                return False
        return True

    def test_processing_sequence(self):
        links = {1: Link(1, 4),
                 7: Link(3, 2)}
        completed, new_pointer, res = \
            zipper.processing_sequence(0, links, b'aaaaabaabcdehgheh')
        a, b, c, d, e = ord('a'), ord('b'), ord('c'), ord('d'), ord('e')
        self.assertEqual([72, a, 0, 20, b, a, 0, 50, c, d, e], res)
        self.assertEqual(12, new_pointer)
        self.assertTrue(completed)

        completed = zipper.processing_sequence(0, links, b'aaaaabaab')[0]
        self.assertFalse(completed)

        completed = zipper.processing_sequence(8, links, b'abaabasdfghj')[0]
        self.assertFalse(completed)

    def test_processing_last_flag(self):
        a = ord('a')
        expected = bytearray([0, a, a, a])
        self.assertEqual(expected, zipper.processing_last_flag(b'aaa'))

        expected = bytes([0] + [a] * 8 + [0] + [a])
        self.assertEqual(expected, zipper.processing_last_flag(b'aaaaaaaaa'))

    def test_coding_string(self):
        links = {1: Link(1, 4),
                 7: Link(3, 2)}
        string = b'aaaaabaabasdfghj'
        res = zipper.coding_string(string, links)
        self.assertEqual(bytearray(b'\x48a\x00\x14ba\x00\x32asd'), res[0])
        self.assertEqual(string[12::], res[1])

    @parameterized.expand([[[1, 0], 256, 2],
                           [[0, 0, 0], 0, 3],
                           [[0, 0, 255, 255], 65535, 4],
                           [[18, 178], 4786, 2]
                           ])
    def test_get_bytes_interpretation_num(self, res, num, count_byte):
        self.assertEqual(bytes(res), zipper.get_bytes_interpretation_num(num, count_byte))

    def test_work_with_files_and_dirs(self):
        create_tree()

        files = [file[1] for file in zipper.get_files('Test')]
        empty_dirs = zipper.get_empty_dirs('Test')

        rmtree('Test')

        self.assertEqual(len(files), 2)
        self.assertTrue(os.path.join('Test', 'Test1', 'Test10', 'file.txt') in files)
        self.assertTrue(os.path.join('Test', 'Test1', 'file1.txt') in files)

        self.assertEqual(len(empty_dirs), 2)
        self.assertTrue(os.path.join('Test', 'Test0', 'Test00') in empty_dirs)
        self.assertTrue(os.path.join('Test', 'Test2') in empty_dirs)


class TestUnzipper(unittest.TestCase):
    def test_get_flag(self):
        self.assertEqual([0, 0, 0, 0, 0, 0, 0, 0], unzipper._get_flag(0))
        self.assertEqual([1, 1, 1, 1, 1, 1, 1, 1], unzipper._get_flag(255))
        self.assertEqual([1, 0, 0, 1, 1, 0, 0, 0], unzipper._get_flag(152))

    def test_get_list_flags(self):
        test_list = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        test_list += [1, 10, 11, 12, 13, 14, 15, 16, 17, 18]
        test_list += [248, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
        test_list += [128, 34]

        self.assertEqual([0, 9, 19, 33], unzipper._get_list_flags(test_list))

    @parameterized.expand([[b'', b'', bytearray()],
                           [b'aaaaaabb', b'\x40a\x00\x15bb', bytearray()],
                           [b'Good', b'\x00Good', bytearray()],
                           [b'Hello, World!', b'\x80\x00\x77World!', bytearray(b'Hello, ')]
                           ])
    def test_unzip_string(self, res, string, context):
        actual = unzipper.unzip_string(string, context)[0]
        self.assertEqual(res, actual)


class TestParse(unittest.TestCase):
    def test_hash_from_duplicate_files(self):
        text = b'Python is the best programming language!'
        with tempfile.NamedTemporaryFile('wb+').file as tf1:
            with tempfile.NamedTemporaryFile('wb+').file as tf2:
                tf1.write(text)
                tf2.write(text)
                tf1.seek(0)
                tf2.seek(0)

                self.assertEqual(get_hash_file(tf1, len(text)),
                                 get_hash_file(tf2, len(text)))


class ComplexTest(unittest.TestCase):
    def zip_unzip_file_test(self, input_file, compress_file, decompress_file):
        with open(input_file, 'rb') as input_fd:
            with open(compress_file, 'w+b') as compress_fd:
                zipper.zip_file(input_fd, input_file, compress_fd)
                file = parser_archive.File(compress_fd, 0)
                unzipper.unzip_file(compress_file, file, decompress_file)
        with open(input_file, 'br') as file1:
            with open(decompress_file, 'br') as file2:
                str1 = file1.read()
                str2 = file2.read()
        os.remove(decompress_file)
        os.remove(compress_file)
        self.assertEqual(str1, str2)

    def test_zip_unzip_file(self):
        create_file('test_empty_file.txt')
        self.zip_unzip_file_test('test_empty_file.txt', 'test_empty_file.dim', 'unzip_test_empty_file.txt')
        os.remove('test_empty_file.txt')

        self.zip_unzip_file_test(test_file, 'test_file.dim', 'unzip_test_file.txt')

    def zip_check_file(self, input_file, output_file):
        with open(input_file, 'rb') as input_fd:
            with open(output_file, 'w+b') as compress_fd:
                zipper.zip_file(input_fd, input_file, compress_fd)
                file = parser_archive.File(compress_fd, 0)
                self.assertTrue(file.check_internal_file())

        os.remove(output_file)
        self.assertFalse(os.path.exists(output_file))

    def test_zip_check_file(self):
        create_file('test_empty_file.txt')
        self.zip_check_file('test_empty_file.txt', 'test_empty_file.dim')
        os.remove('test_empty_file.txt')
        self.assertFalse(os.path.exists('test_empty_file.txt'))

        self.zip_check_file(test_file, 'test_file.dim')

    def test_zip_check_listing_dir(self):
        create_tree()

        zipper.zip_dirs_and_files(['Test'], 'test.dim')
        files_and_dirs = parser_archive.ListingFiles('test.dim')

        rmtree('Test')

        files = [file.name for file in files_and_dirs.files]
        empty_dirs = files_and_dirs.empty_dirs
        self.assertEqual(len(files), 2)
        self.assertTrue(os.path.join('Test', 'Test1', 'Test10', 'file.txt') in files)
        self.assertTrue(os.path.join('Test', 'Test1', 'file1.txt') in files)

        self.assertEqual(len(empty_dirs), 2)
        self.assertTrue(os.path.join('Test', 'Test0', 'Test00') in empty_dirs)
        self.assertTrue(os.path.join('Test', 'Test2') in empty_dirs)

        self.assertTrue(parser_archive.check_file('test.dim'))
        self.assertFalse(parser_archive.check_file(test_file))

        os.remove('test.dim')
        self.assertFalse(os.path.exists('test.dim'))


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.parser = archiver.get_parser()

    def test_existent_file(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            archiver.existent_file('qwedfghjkl.asfw')
        self.assertEqual(test_file, archiver.existent_file(test_file))

    def test_existent_file_or_dir(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            archiver.existent_files_or_dirs('qwedfghjkl.asfw')
        name = '.'
        self.assertEqual(name, archiver.existent_files_or_dirs(name))
        self.assertEqual(test_file, archiver.existent_files_or_dirs(test_file))

    def test_called_check(self):
        args = self.parser.parse_args(['check', test_file])
        self.assertEqual(archiver.check_that_file_is_archive, args.function)

    def test_called_archive(self):
        args = self.parser.parse_args(['zip', test_file, test_file])
        self.assertEqual(archiver.archive_files, args.function)

    def test_called_unzip(self):
        args = self.parser.parse_args(['unzip', test_file, '.'])
        self.assertEqual(archiver.unzip_files, args.function)

    def test_called_listing(self):
        args = self.parser.parse_args(['listing', test_file])
        self.assertEqual(archiver.listing_archive, args.function)

    def test_called_extract_file(self):
        args = self.parser.parse_args(['extract_file', test_file, test_file, '.'])
        self.assertEqual(archiver.extract_file, args.function)

    @unittest.mock.patch('archiver.zip_dirs_and_files')
    def test_called_zip(self, magic_mock):
        mock = unittest.mock.Mock(files_and_dirs=[test_file], file_archive='test.txt')
        archiver.archive_files(mock)
        self.assertTrue(magic_mock.called)

    @unittest.mock.patch('archiver.check_file')
    def test_called_check_file_when_checking(self, magic_mock):
        mock = unittest.mock.Mock(name=test_file)
        archiver.check_that_file_is_archive(mock)
        self.assertTrue(magic_mock.call_count == 1)

    @unittest.mock.patch('archiver.ListingFiles')
    def test_called_listing_1(self, magic_mock):
        create_file('test.txtx')
        zipper.zip_dirs_and_files(['test.txtx'], 'test.dim')
        mock = unittest.mock.Mock(file_archive='test.dim')
        archiver.listing_archive(mock)
        os.remove('test.txtx')
        os.remove('test.dim')
        self.assertTrue(magic_mock.called)

    def test_called_unzip_one_file(self):
        create_tree()

        zipper.zip_dirs_and_files(['Test'], 'test_archive.txt')

        with unittest.mock.patch('archiver.unzip_one_file') as magic_mock:
            mock = unittest.mock.Mock(file_archive='test_archive.txt',
                                      file=os.path.join('Test', 'Test1', 'Test10', 'file.txt'))
            archiver.extract_file(mock)
            self.assertTrue(magic_mock.call_count == 1)

        with unittest.mock.patch('archiver.unzip_one_file') as magic_mock:
            mock = unittest.mock.Mock(file_archive='test_archive.txt')
            archiver.unzip_files(mock)
            self.assertTrue(magic_mock.call_count == 2)

        rmtree('Test')

        with unittest.mock.patch('archiver.unzip_file') as magic_mock:
            list_file = parser_archive.ListingFiles('test_archive.txt').files
            archiver.unzip_one_file('test_archive.txt', list_file[0], '.')
            self.assertTrue(magic_mock.called)

        rmtree('Test')
        os.remove('test_archive.txt')

        self.assertFalse(os.path.exists('Test'))
        self.assertFalse(os.path.exists('test_archive.txt'))


if __name__ == '__main__':
    unittest.main()
