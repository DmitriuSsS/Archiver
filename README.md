# Archiver

## Описание
Данная программа создана для сжатия и распаковки файлов, интерфейс консольный

## Режимы работы программы
Справка по запуску: `archiver.py` без аргументов или `archiver.py -h` или `archiver.py --help`

### Сжатие файла
Запуск: `achiver.py zip output_file input_files_and_dirs`

Пример запуска: `archiver.py zip example.z file.txt`
                `archiver.py zip example.z file1.txt file2.js directory`

### Распаковка файла
Запуск: `archiver.py unzip input_file output_dir`

Пример запуска: `archiver.py unzip archive.dim ./`

Если файл с именем архивированного файла существует, то Вам будет предложен выбор:
* перезаписать файл -> replace
* изменить имя -> rename
* отменить разархивацию -> cancel

### Проверка файла на целостность
Запуск: `archiver.py check input_archived_file`

Пример запуска: `archiver.py check example_archive.z`

### Листинг файлов
Запуск: `archiver.py listing input_archived_file`

Пример запуска: `archiver.py listing example_archive.z`

### Распаковка отдельного файла из архива
Запуск: `archiver.py extract_file file_archive name_file outrut_dir`

Пример запуска: `archiver.py extract_file example_archive.z file.txt ./`
