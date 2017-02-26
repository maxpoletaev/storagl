from concurrent.futures import ThreadPoolExecutor
from functools import wraps
import string
import random
import os

from django.core.exceptions import ObjectDoesNotExist
from django.utils.deconstruct import deconstructible

executor = ThreadPoolExecutor(max_workers=1)


@deconstructible
class ShardedUpload:
    def __init__(self, upload_path='', files_per_dir=1000, suffix_field=None):
        self.files_per_dir = files_per_dir
        self.suffix_field = suffix_field
        self.upload_path = upload_path

    def __call__(self, instance, filename):
        _, ext = os.path.splitext(filename)
        suffix = self.get_suffix(instance)
        file_id = instance.pk or self.get_next_id(instance)
        dir_name = str(int(file_id / self.files_per_dir) * self.files_per_dir).rjust(len(str(self.files_per_dir)), '0')
        filename = '{}_{}{}'.format(str(file_id).rjust(len(str(self.files_per_dir)), '0'), suffix, ext)
        return os.path.join(self.upload_path, dir_name, filename)

    def __eq__(self, other):
        return self.upload_path == other.upload_path\
           and self.files_per_dir == other.files_per_dir  # noqa

    def get_suffix(self, instance):
        if self.suffix_field:
            return getattr(instance, self.suffix_field)
        return ''.join(random.choice(string.ascii_lowercase) for _ in range(4))

    def get_next_id(self, instance):
        try:
            next_id = type(instance).objects.latest('id').id + 1
        except ObjectDoesNotExist:
            next_id = 1
        return next_id


def confirm(message, default='n'):
    choices = 'Y/n' if default.lower() in ('y', 'yes') else 'y/N'
    choice = input('{} ({}) '.format(message, choices))
    values = ('y', 'yes', '') if choices == 'Y/n' else ('y', 'yes')
    return choice.strip().lower() in values


def short_uuid():
    symbols = string.ascii_lowercase + string.digits
    return ''.join(random.choice(symbols) for _ in range(8))


def base_url(request, path):
    return 'http://{}{}'.format(request.META['HTTP_HOST'], path)


def run_in_executor(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        return executor.submit(func, *args, **kwargs)
    return decorator
