from django_micro import configure
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_HOSTS = [os.environ.get('ALLOWED_HOST') or 'localhost']
DEBUG = bool(os.environ.get('DJANGO_DEBUG', 0))

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
from django.shortcuts import get_object_or_404, render, redirect
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.urls import reverse
from django.views import View
from django.db import models
from django import forms

from .utils import ShardedUpload, confirm, short_uuid
from .tasks import run_async


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

    @run_async
    def update_last_access(self):
        self.last_access = timezone.now()
        self.save()

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


@route(r'^$', name='upload')
class UploadView(View):
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

        return redirect('file_info', asset.slug)


@route(r'^([\w\d\-]+)$', name='download')
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


@route(r'^([\w\d\-]+)/meta/?$', name='file_info')
def file_info(request, asset_slug):
    asset = get_object_or_404(Asset, slug=asset_slug)
    base_url = 'http://' + request.META['HTTP_HOST']

    return JsonResponse(asset.as_json(base_url),
        json_dumps_params={'ensure_ascii': False, 'indent': 2})


@command('cleanup')
class CleanupCommand(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-f', '--force', action='store_true', default=False, dest='force')
        parser.add_argument('-d', '--days', type=int, default=180, dest='days')

    def validate_options(self, options):
        if options['days'] < 1:
            raise CommandError('Days option should be large that 0')

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
