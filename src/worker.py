from __future__ import annotations
import threading
from typing import TYPE_CHECKING
import boto3
from config import Boto3Config

if TYPE_CHECKING:
    import queue
    import botocore

class Worker(threading.Thread):
    """Base class for boto3.client threads.
    """
    def __init__(self):
        super().__init__()
        self.daemon = True

    def stop(self,timeout=None):
        super().join(timeout)
        print(f'Worker {self.name} joined')

class Connection(Worker):
    """boto3.client connection object.
    """

    def __init__(self, client: botocore.client, from_queue: queue.Queue, terminate_on: bool) -> None:
        super().__init__()
        self.client = client
        self.from_queue = from_queue
        self.running = terminate_on

    def run(self):
        while self.running and self.from_queue.qsize() > 0:
            download = self.from_queue.get()
            download.start(self.client)
        self.stop()

class ConnectionPool(Boto3Config):
    """Thread-pool like object for storing workers.
    """

    def __init__(self, task_queue: queue.Queue, max_workers: int=1) -> None:
        super().__init__()
        self.running = True
        self.worker_pool = [Connection(client=self.new_client(), from_queue=task_queue, terminate_on=self.running) for _ in range(max_workers)]

    def new_client(self):
        return boto3.client('s3',
                            region_name=self.region_name,
                            endpoint_url=self.endpoint_url,
                            aws_access_key_id=self.access_key,
                            aws_secret_access_key=self.secret_key)

    def start(self):
        self.running = True
        for worker in self.worker_pool:
            worker.start()

    def stop(self):
        self.running = False