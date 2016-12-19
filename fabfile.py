import os

from fabric.api import env, task
from fabric.operations import run
from fabric.context_managers import prefix
from fabric.contrib.project import rsync_project


env.user = 'static'
env.hosts = ['zenwalker.ru']

EXCLUDE_FILES = [
    '__pycache__', '.DS_Store', '.hg',
    '*.sqlite3', '*.orig', '*.pyc', 'uploads']


def deploy_project(remote_dir, touch_file):
    manage_py = 'python ' + os.path.join(remote_dir, 'storage/app.py')

    rsync_project(local_dir='./', remote_dir=remote_dir,
                  exclude=EXCLUDE_FILES, delete=True)

    with prefix('source ~/venv/bin/activate'):
        run('pip install -r ' + os.path.join(remote_dir, 'requirements.txt'))
        run(manage_py + ' migrate')

    run('touch ' + os.path.join(remote_dir, touch_file))


@task
def deploy():
    deploy_project('~/www', touch_file='etc/uwsgi.ini')
