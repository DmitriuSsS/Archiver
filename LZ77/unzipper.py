from LZ77.Link import Link


def unzip_file(name_archive, file, name_out_file):
    with open(name_archive, 'br') as input_file:
        input_file.seek(file.start)
        with open(name_out_file, 'bw') as output_file:
            count_read = 1024 * 1024
            context = bytearray()
            pointer = 0
            residue_string = b''
            while pointer < file.length:
                delta = min(count_read, file.length - pointer)
                pointer += delta
                content = residue_string + input_file.read(delta)
                unzip_str, residue_string, context = unzip_string(content, context)
                output_file.write(unzip_str)


def _get_flag(byte):
    res = []
    while len(res) != 8:
        res.append(byte % 2)
        byte >>= 1
    return res[::-1]


def _get_list_flags(string):
    pointer = 0
    result = []
    while pointer < len(string):
        result.append(pointer)
        pointer += 9 + _get_flag(string[pointer]).count(1)
    return result


def unzip_string(string, context):
    result = context.copy()
    flags = _get_list_flags(string)
    last_ = len(string) < 1024 * 1024
    if last_:
        max_ind = len(flags)
    else:
        max_ind = len(flags) - 1
    for i in range(max_ind):
        f = flags[i]
        flag = _get_flag(string[f])
        pointer = f + 1
        for j in flag:
            if pointer >= len(string):
                break
            if j:
                Link.copy(result, [string[pointer], string[pointer + 1]])
                pointer += 2
            else:
                result.append(string[pointer])
                pointer += 1

    if last_:
        return result[len(context)::], b'', b''

    if len(result) >= Link.max_offset:
        next_context = result[-Link.max_offset::]
    else:
        next_context = result
    next_residue_string = string[flags[-1]::]
    return result[len(context)::], next_residue_string, next_context
