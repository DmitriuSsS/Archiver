import time
import sys
import os
import argparse

from LZ77.zipper import zip_dirs_and_files
from LZ77.unzipper import unzip_file
from Parser.parser_archive import check_file, ListingFiles


def existent_file(name):
    if not (os.path.exists(name) and os.path.isfile(name)):
        raise argparse.ArgumentTypeError(f'File {name} does not exist')
    return name


def existent_files_or_dirs(name):
    if not os.path.exists(name):
        raise argparse.ArgumentTypeError(f'{name} does not exist')
    return name


def check_that_file_is_archive(arguments):
    name = arguments.file
    if check_file(name):
        print(f"File {name} is archive")
    else:
        print(f"File {name} isn't archive")


def archive_files(arguments):
    names_files_and_dirs = arguments.files_and_dirs
    name_output_dir = os.path.dirname(arguments.file_archive)
    if not os.path.exists(name_output_dir) and name_output_dir != '':
        os.makedirs(name_output_dir)
    t = time.time()
    print('Start compressing')
    zip_dirs_and_files(names_files_and_dirs, arguments.file_archive)
    print('Finish compressing')
    print('Time compressing: ' + str(time.time() - t))


def unzip_files(arguments):
    if check_file(arguments.file_archive):
        listing_files = ListingFiles(arguments.file_archive)
        print('Start decompressing')
        files = listing_files.files
        for file in files:
            unzip_one_file(arguments.file_archive, file, arguments.directory)
        dirs = listing_files.empty_dirs
        for empty_dir in dirs:
            if not os.path.exists(empty_dir):
                os.makedirs(empty_dir)
        print('Finish decompressing')
    else:
        print(f"File {arguments.file_archive} isn't archive")


def listing_archive(arguments):
    name_archive = arguments.file_archive
    if not check_file(name_archive):
        print(f"File {name_archive} isn't archive")
    else:
        files = ListingFiles(name_archive)
        print(files)


def extract_file(arguments):
    file_archive = arguments.file_archive
    removable_file = arguments.file
    directory = arguments.directory
    if check_file(file_archive):
        list_files = ListingFiles(file_archive).files
        for file in list_files:
            if file.name == removable_file:
                unzip_one_file(file_archive, file, directory)
                return
        print(f"File {removable_file} does not exist in {file_archive}")
    else:
        print(f"File {file_archive} isn't archive")


def unzip_one_file(name_archive, file, directory):
    file.name = os.path.join(directory, file.name)
    dir_of_file = os.path.dirname(file.name)
    if not os.path.exists(dir_of_file) and dir_of_file != '':
        os.makedirs(dir_of_file)
    primary_file_name = os.path.basename(file.name)
    while os.path.exists(os.path.join(dir_of_file, primary_file_name)):
        print('File exist in directory')
        while True:
            act = input('What would you like to do? replace/rename/cancel: ')
            if act in ['rename', 'cancel', 'replace']:
                break
            print('unidentified command')
        if act == 'rename':
            primary_file_name = input('Please, rename file: ')
        elif act == 'cancel':
            return
    unzip_file(name_archive, file, os.path.join(dir_of_file,
                                                primary_file_name))


def get_parser():
    parser_ = argparse.ArgumentParser(description='File Archive Utility')
    subparsers = parser_.add_subparsers()

    # region check
    parser_check = subparsers.add_parser('check', help='Check if the file is archived')
    parser_check.add_argument('file', type=existent_file, help='File to check')
    parser_check.set_defaults(function=check_that_file_is_archive)
    # endregion

    # region zip
    parse_archive = subparsers.add_parser('zip',
                                          help='Zipping this files and dirs')
    parse_archive.add_argument('file_archive',
                               help='File which will be archive')
    parse_archive.add_argument('files_and_dirs', type=existent_files_or_dirs,
                               nargs='+',
                               help='Files and folders for zipping')
    parse_archive.set_defaults(function=archive_files)
    # endregion

    # region unzip
    parse_unzip = subparsers.add_parser('unzip', help='Unzipping this file')
    parse_unzip.add_argument('file_archive', type=existent_file,
                             help='File to archive')
    parse_unzip.add_argument('directory',
                             help='Directory to write the zipped file')
    parse_unzip.set_defaults(function=unzip_files)
    # endregion

    # region listing
    parse_listing = subparsers.add_parser('listing', help='Output of all file names of this archive')
    parse_listing.add_argument('file_archive', type=existent_file, help='Archive for which to output files')
    parse_listing.set_defaults(function=listing_archive)
    # endregion

    # region extract_file
    parse_extract_file = subparsers.add_parser('extract_file',
                                               help='Unzip the specified file from the archive to the desired folder')
    parse_extract_file.add_argument('file_archive', type=existent_file, help='Archive file')
    parse_extract_file.add_argument('file', help='The file you want to unzip')
    parse_extract_file.add_argument('directory', help='Unpacking directory')
    parse_extract_file.set_defaults(function=extract_file)
    # endregion

    return parser_


if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.parse_args(['-h']).function()
    else:
        args = parser.parse_args()
        args.function(args)
