from threading import Thread
from queue import Queue

tasks = {}


def task_consumer(queue):
    while True:
        try:
            task, args, kwargs = queue.get()
        except KeyboardInterrupt:
            return

        tasks[task](*args, **kwargs)


def run_async(fn=None, name=None):
    def wrapper(fn):
        task_name = name or fn.__name__
        tasks[task_name] = fn

        def decorator(*args, **kwargs):
            task_queue.put((task_name, args, kwargs))
        return decorator

    return wrapper(fn) if fn else wrapper


def start_workers(queue, concurrency=1):
    for _ in range(concurrency):
        worker = Thread(target=task_consumer, args=(queue,))
        worker.daemon = True
        worker.start()


task_queue = Queue()
start_workers(task_queue)
