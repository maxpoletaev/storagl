from django_micro import configure
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG = bool(os.environ.get('DJANGO_DEBUG', 0))
ALLOWED_HOSTS = ['*']

FILE_UPLOAD_PERMISSIONS = 0o644
FILE_OWNER = os.environ.get('FILE_OWNER')
UPLOADS_DIR = os.path.join(BASE_DIR, 'data')
UPLOADS_URL = '/data/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(UPLOADS_DIR, 'db.sqlite3'),
        'OPTIONS': {'check_same_thread': False},
    },
}

configure(locals())

from collections import OrderedDict
from datetime import timedelta

from django_micro import command, get_app_label, route, run
from django.core.management.base import BaseCommand, CommandError
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.core.files.storage import FileSystemStorage
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.deconstruct import deconstructible
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.urls import reverse
from django.views import View
from django.db import models
from django import forms

from .utils import ShardedUpload, confirm, short_uuid, run_in_executor


@deconstructible
class UploadStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(UPLOADS_DIR, UPLOADS_URL)


class Asset(models.Model):
    slug = models.SlugField(unique=True, default=short_uuid)
    file = models.FileField(upload_to=ShardedUpload(suffix_field='slug'), storage=UploadStorage())
    file_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    last_access = models.DateTimeField(blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assets'
        app_label = get_app_label()

    @run_in_executor
    def update_last_access(self):
        self.last_access = timezone.now()
        self.save(update_fields=['last_access'])

    def as_json(self, base_url=''):
        upload_date = self.upload_date.isoformat()
        last_access = self.last_access.isoformat() \
                      if self.last_access else None  # noqa

        return OrderedDict([
            ('slug', self.slug),
            ('file_name', self.file_name),
            ('content_type', self.content_type),
            ('upload_date', upload_date),
            ('last_access', last_access),
            ('url', base_url + self.get_absolute_url()),
        ])

    def get_absolute_url(self):
        return reverse('download', args=[self.slug])


@receiver(pre_delete, sender=Asset)
def cleanup_file(sender, instance, **kwargs):
    instance.file.delete()


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ('file',)


@route('', name='upload')
class UploadView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        return render(request, 'upload.html')

    def post(self, request):
        form = AssetForm(request.POST, request.FILES)
        content_type = request.FILES['file'].content_type
        file_name = request.FILES['file'].name

        if not form.is_valid():
            return JsonResponse({'errors': form.errors}, status=400)

        asset = form.save(commit=False)
        asset.content_type = content_type
        asset.file_name = file_name
        asset.save()

        if FILE_OWNER:
            uid, gid = (int(x) for x in FILE_OWNER.split(':'))
            os.chown(asset.file.path, uid, gid)

        base_url = 'http://' + request.META['HTTP_HOST']
        accept_content_type = request.META.get('HTTP_ACCEPT')

        if 'application/json' not in accept_content_type:
            return HttpResponse(base_url + asset.get_absolute_url() + '\n')

        return JsonResponse(
            asset.as_json(base_url),
            json_dumps_params={'ensure_ascii': False, 'indent': 2},
        )


@route('<slug:asset_slug>', name='download')
def download(request, asset_slug):
    force_download = bool(request.GET.get('download', False))
    asset = get_object_or_404(Asset, slug=asset_slug)
    asset.update_last_access()

    if not DEBUG:
        response = HttpResponse()
        response['X-Accel-Redirect'] = asset.file.url
        response['Content-Type'] = ''  # let nginx guess the mimetype
    else:
        response = FileResponse(asset.file,
            content_type=asset.content_type)

    if asset.file_name:
        disposition = 'attachment' if force_download else 'inline'
        response['Content-Disposition'] = '{}; filename="{}"'.format(disposition, asset.file_name)

    return response


@route('<slug:asset_slug>/meta/', name='file_info')
def file_info(request, asset_slug):
    asset = get_object_or_404(Asset, slug=asset_slug)
    base_url = 'http://' + request.META['HTTP_HOST']

    return JsonResponse(asset.as_json(base_url),
        json_dumps_params={'ensure_ascii': False, 'indent': 2})


@command('remove_file')
class RemoveFileCommand(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('file_id', type=int)

    def handle(self, file_id, *args, **options):
        try:
            asset = Asset.objects.get(id=file_id)
        except Asset.DoesNotExist:
            raise CommandError('File with id "{}" does not exist'.format(str(file_id)))
        asset.delete()


@command('cleanup')
class CleanupCommand(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-f', '--force', action='store_true', default=False, dest='force')
        parser.add_argument('-d', '--days', type=int, default=180, dest='days')

    def validate_options(self, options):
        if options['days'] < 1:
            raise CommandError('Days option should be great that 0')

    def handle(self, *args, **options):
        self.validate_options(options)
        max_age = timezone.now() - timedelta(days=options['days'])

        assets = Asset.objects.filter(
            models.Q(last_access__lte=max_age) |
            models.Q(last_access=None, upload_date__lte=max_age))

        assets_count = assets.count()

        if not assets_count:
            self.stdout.write('Nothing to cleanup')
            return

        if options['force'] or confirm('Remove {} unused assets?'.format(assets_count)):
            assets.delete()


application = run()
