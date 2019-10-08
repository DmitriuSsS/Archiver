from LZ77.Link import Link
from Parser.File import get_hash_file
import tempfile
import os


def finding_empty_files(path_dir):
    list_dir = os.listdir(path_dir)
    if not list_dir:
        yield path_dir
    else:
        for d in list_dir:
            new_path = os.path.join(path_dir, d)
            if os.path.isdir(new_path):
                for directory in finding_empty_files(new_path):
                    yield directory


def get_empty_dirs(path):
    res_empty_dirs = []
    for d in finding_empty_files(path):
        res_empty_dirs.append(d)
    name_root_dir = os.path.basename(path)
    remove = len(path) - len(name_root_dir)
    return [name_dir[remove::] for name_dir in res_empty_dirs]


def get_files(path):
    files_from_folder = []
    name_root_dir = os.path.basename(path)
    remove = len(path) - len(name_root_dir)
    for top, dirs, files in os.walk(path):
        for nm in files:
            name_file = os.path.join(top, nm)
            files_from_folder.append((name_file, name_file[remove::]))
    return files_from_folder


def zip_dirs_and_files(files_and_dirs, name_output_file):
    files = []
    empty_dirs = []
    for e in files_and_dirs:
        if os.path.isfile(e):
            files.append((e, os.path.basename(e)))
        elif os.path.isdir(e):
            files += get_files(e)
            empty_dirs += get_empty_dirs(e)

    if os.path.exists(name_output_file):
        os.remove(name_output_file)

    with open(name_output_file, 'wb') as output_fd:
        output_fd.write(get_bytes_interpretation_num(len(files), 1))
        output_fd.write(get_bytes_interpretation_num(len(empty_dirs), 1))
        for file in files:
            with open(file[0], 'rb') as input_fd:
                zip_file(input_fd, file[1], output_fd)

        for empty_dir in empty_dirs:
            output_fd.write(get_bytes_interpretation_num(len(empty_dir), 1))
            output_fd.write(empty_dir.encode())


def zip_file(input_fd, name_input_file, output_fd):
    # Вид архивированного файла: [len_name][name][len_hash][hash][len_file][file]
    t = tempfile.NamedTemporaryFile('wb+')
    length_archive = 0
    with t.file as tpf:

        # region archive file
        input_fd.seek(0)
        name_input_file = name_input_file.encode()
        name = bytes([len(name_input_file)]) + name_input_file
        count_read = 4 * 1024 * 1024
        content = input_fd.read(count_read)
        remained = b''
        while content:
            result, remained = zip_string(content, remained)
            length_archive += len(result)
            tpf.write(result)
            content = input_fd.read(count_read)
        last = processing_last_flag(remained)
        length_archive += len(last)
        tpf.write(last)
        # endregion

        # region copy archived file
        tpf.seek(0)
        hash_file = get_hash_file(t.file, length_archive)
        output_fd.write(name)
        output_fd.write(get_bytes_interpretation_num(len(hash_file), 2))
        output_fd.write(hash_file)
        output_fd.write(get_bytes_interpretation_num(length_archive, 5))
        tpf.seek(0)
        count_read_for_copy = 128 * 1024 * 1024
        content = tpf.read(count_read_for_copy)
        while content:
            output_fd.write(content)
            content = tpf.read(count_read_for_copy)
        # endregion


def get_bytes_interpretation_num(num, len_interpretation):
    res = []
    while len(res) != len_interpretation:
        res.append(num % 256)
        num >>= 8
    return bytearray(res[::-1])


def coding_string(string, links):
    pointer = 0
    result = []
    while pointer < len(string):
        completed, new_pointer, res = processing_sequence(pointer, links, string)
        if completed:
            pointer = new_pointer
            result += res
        else:
            break

    return bytearray(result), string[pointer::]


def processing_sequence(pointer, links, string):
    res = [0]
    link_detected = 0
    completed_flag = True

    for i in range(8):
        if pointer >= len(string):
            completed_flag = False
            break
        if pointer in links:
            link_detected = link_detected * 2 + 1
            res += links[pointer].get_byte_interpretation()
            pointer += links[pointer].len_copy
        else:
            res.append(string[pointer])
            pointer += 1
            link_detected *= 2

    res[0] = link_detected

    return completed_flag, pointer, res


def processing_last_flag(string):
    result = []
    for pointer in range(len(string)):
        if pointer % 8 == 0:
            result.append(0)
        result.append(string[pointer])

    return bytearray(result)


def zip_string(string, remainder):
    string = remainder + string
    links = extract_links(string)
    return coding_string(string, links)


def extract_links(string):
    max_len_phrase = Link.max_len
    len_buffer = Link.max_offset
    links = {}
    buffer = {}
    pos = 0
    while pos < len(string):
        flag = False
        i = 1
        while string[pos:pos + i:] in buffer and i < max_len_phrase and pos + i < len(string):
            i += 1
        if i - 3 >= 0 and pos - buffer[string[pos:pos + i - 1:]] <= len_buffer:
            links[pos] = Link(pos - buffer[string[pos:pos + i - 1:]], i - 1)
            flag = True
        buffer[string[pos:pos + i - 1:]] = pos
        buffer[string[pos:pos + i:]] = pos
        pos += i - 1 if flag else 1
    return links
