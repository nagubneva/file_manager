import shutil
import os
from enum import Enum
from pathlib import Path

from storage import JSONStorage
from settings import USERS_FOLDERS


def dir_size(path):
    size = 0
    for path, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(path, file)
            size += file_size(file_path)
    return size


def str_size(string):
    return len(string.encode())


def file_size(path):
    return os.path.getsize(path)


class Commands(Enum):
    MAKE_DIR = 'MakeFold'
    MAKE_FILE = 'MakeFile'
    CD = 'CD'
    WRITE_FILE = 'WriteTextFile'
    SHOW_FILE = 'ViewTextFile'
    DEL = 'Delete'
    COPY = 'Copy'
    MOVE = 'Move'
    FREE = 'Memory'
    EXIT = 'Exit'


class Errors(Enum):
    UNDEFINED_COMMAND = 'Команда не найдена.'
    NO_SPACE = 'У Вас нет свободного места.'
    NO_SPACE_LIMIT = 'У Вас нет ограничений по объему.'
    ALREADY_EXIST = 'Такой файл или папка уже есть.'
    FILE_ALREADY_EXIST = 'Такой файл уже есть.'
    DIR_ALREADY_EXIST = 'Такая папка уже есть.'
    NOT_EXIST = 'Такой папки или файла нет.'
    FILE_NOT_EXIST = 'Такого файла нет.'
    DIR_NOT_EXIST = 'Такой папки нет.'
    WRONG_PASSWORD = 'Неправильный пароль.'


class FileManager:

    @staticmethod
    def make_dir(path):
        if path.exists():
            _print_error(Errors.ALREADY_EXIST)
        else:
            path.mkdir(parents=True)

    @staticmethod
    def make_file(path):
        if path.exists():
            _print_error(Errors.NOT_EXIST)
        else:
            path.touch()

    @staticmethod
    def cd(path):
        if path.is_dir():
            os.chdir(path)
        else:
            _print_error(Errors.DIR_NOT_EXIST)

    @staticmethod
    def show_file(path):
        if path.is_file():
            print(path.read_text())
        else:
            _print_error(Errors.FILE_NOT_EXIST)

    @staticmethod
    def delete(path):
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()
        else:
            _print_error(Errors.NOT_EXIST)

    @staticmethod
    def move(src_path, dst_path):
        if src_path.exists():
            shutil.move(src_path, dst_path)
        else:
            _print_error(Errors.NOT_EXIST)

    def __init__(self, root, username='', size=None):
        self._root = Path(root).resolve()
        if not self._root.is_dir():
            self.make_dir(self._root)
        os.chdir(self._root)
        self._username = username
        self._size = size

    @property
    def working_dir(self):
        return Path.cwd().relative_to(self._root)

    @property
    def root_size(self):
        return dir_size(self._root)

    @property
    def invite(self):
        working_dir = str(
            self.working_dir).replace('\\', '/').replace('.', '/')
        if working_dir[0] != '/':
            working_dir = '/' + working_dir
        if self._username:
            return f'{self._username}:{working_dir}$ '
        else:
            f'{working_dir}$ '

    def write_file(self, path):
        if path.is_file():
            text = input()
            if self._size and self._is_no_space(str_size(text)):
                _print_error(Errors.NO_SPACE)
                self.free()
            else:
                with open(path, 'a') as file:
                    file.write(text)
        else:
            _print_error(Errors.FILE_NOT_EXIST)

    def copy(self, src_path, dst_path):
        if src_path.is_file():
            if self._size and self._is_no_space(file_size(src_path)):
                _print_error(Errors.NO_SPACE)
                self.free()
            else:
                shutil.copy(src_path, dst_path)
        elif src_path.is_dir():
            if self._size and self._is_no_space(dir_size(src_path)):
                _print_error(Errors.NO_SPACE)
                self.free()
            else:
                shutil.copytree(src_path, dst_path)
        else:
            _print_error(Errors.NOT_EXIST)

    def free(self):
        if self._size:
            free_size = self._size - self.root_size
            print(f'Доступно {free_size}Б из {self._size}Б.')
        else:
            _print_error(Errors.NO_SPACE_LIMIT)

    def command_line(self):
        while True:
            command, *paths = input(self.invite).split()
            paths = list(map(self._get_path, paths))
            if command == Commands.MAKE_DIR.value:
                self.make_dir(paths[0])
            elif command == Commands.MAKE_FILE.value:
                self.make_file(paths[0])
            elif command == Commands.CD.value:
                self.cd(paths[0])
            elif command == Commands.WRITE_FILE.value:
                self.write_file(paths[0])
            elif command == Commands.SHOW_FILE.value:
                self.show_file(paths[0])
            elif command == Commands.DEL.value:
                self.delete(paths[0])
            elif command == Commands.COPY.value:
                self.copy(paths[0], paths[1])
            elif command == Commands.MOVE.value:
                self.move(paths[0], paths[1])
            elif command == Commands.FREE.value:
                self.free()
            elif command == Commands.EXIT.value:
                break
            else:
                _print_error(Errors.UNDEFINED_COMMAND)

    def _get_path(self, str_path):
        if str_path[0] == '/':
            path = Path(self._root, str_path[1:])
        elif str_path.find('..') != -1:
            path = Path()
            for path_part in Path(str_path).parts:
                resolved_path_part = Path(path_part).resolve()
                if (path_part == '..' and
                        resolved_path_part.is_relative_to(self._root)):
                    path = resolved_path_part
                elif path_part != '..':
                    path = path.joinpath(path_part)
                else:
                    path = self._root
        else:
            resolved_path = Path(str_path).resolve()
            if (resolved_path.is_absolute() and
                    resolved_path.relative_to(self._root)):
                path = Path(str_path).resolve()
            else:
                path = Path.cwd().joinpath(Path(str_path))
        return path

    def _is_no_space(self, extra):
        if self.root_size + extra > self._size:
            return True
        return False


class MultiUserFileManager:

    def __init__(self, users, root=None, size=None):
        self._users = users
        if root is not None:
            self._root = Path(root).resolve()
            self.make_root_dir()
        else:
            self._root = root
        self._size = size
        self._authorized = False
        self._username = None

    def make_root_dir(self):
        if not self._root.is_dir():
            self._root.mkdir(parents=True)

    def auth(self):
        username = input('Логин: ')
        password = input('Пароль: ')
        if self._users.exists(username):
            if password == self._users.get_password(username):
                self._authorized = True
        else:
            self._users.add(username, password)
            self._authorized = True
        self._username = username

    def start(self):
        if self._authorized:
            user_working_dir = Path(self._root, self._username)
            FileManager(
                user_working_dir,
                self._username,
                self._size
            ).command_line()
        else:
            _print_error(Errors.WRONG_PASSWORD)


def _print_error(error):
    print('Ошибка:', error.value)


fm = MultiUserFileManager(
    JSONStorage('users.json'),
    root=USERS_FOLDERS,
    size=12310
)
fm.auth()
fm.start()