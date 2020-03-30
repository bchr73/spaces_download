import threading
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import queue
    import botocore

class Worker(threading.Thread):
    """Base class for boto3.client threads.
    """
    pass

class Connection(Worker):
    """boto3.client connection object.
    """

    def __init__(self, client: botocore.client, from_queue: queue.Queue) -> None:
        self.client = client
        self.from_queue = from_queue

    def run(self):
        while True:
            download = self.from_queue.get()
            download.start(self.client)