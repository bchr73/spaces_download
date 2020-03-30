import queue
import time
import threading
from typing import TYPE_CHECKING, List, Dict

import boto3

from config import Boto3Config
from observer import DownloadCompleteObserver, Observable
from contract import Contract

if TYPE_CHECKING:
    import Observer
    import botocore

class Download(Observable):
    """Class for keeping track of active downloads.

    Attributes:
        client: An S3.Client object for use in connecting to bucket.
        id: String object, contains a unique 8 character sequence.
        bucket: String containing Digital Ocean Spaces bucket name.
        key: String containing where the remote file is located inside bucket.
        filename: Path like string object containing where to store download.
        extra_args: Dict containing any extra arguments to supply 'download_file' method.

        _size: Integer count representing remote file size, in bytes.
        _bytes_transferred: Integer count representing number of bytes transferred from remote.
        _lock: Threading.Lock object to protect access to _bytes_transferred.

        _observers: List object containing all subscribed observers.
    """

    def __init__(self, contract: Contract) -> None:
        self.id = contract.id
        self.bucket = contract.bucket
        self.key = contract.key
        self.filename = contract.filename
        self.extra_args = contract.extra_args

        self._size = self.client.head_object(Bucket=self.bucket, Key=self.filename).get('ContentLength')
        self._bytes_transferred = 0
        self._lock = threading.Lock()

        self._observers: List = []

    def progress(self, new_bytes) -> None:
        """Callback function to update newly transferred bytes on download."""
        with self._lock:
            self._bytes_transferred += new_bytes
            self.notify()

    def start(self, client: botocore.client) -> None:
        """Initiates file download."""
        client.download_file(Bucket=self.bucket,
                       Key=self.key,
                       Filename=self.filename,
                       ExtraArgs=self.extra_args,
                       Callback=self.progress)

    def attach(self, observer: Observer) -> None:
        """Attaches an observer to the current object."""
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """Detaches an observer to the current object."""
        self._observers.remove(observer)

    def notify(self) -> None:
        """Trigger an update in each subscriber."""
        for observer in self._observers:
            observer.update(self)

class ProgressTracker(threading.Thread):
    """Simple class that accepts a dict and displays formatted output
       of contents.

    Attributes:
        to_track: Object of type dict containing information for active downloads
    """

    def __init__(self, to_track: Dict) -> None:
        self.to_track = to_track

    def run(self):
        while True:
            time.sleep(2)
            for uuid, progress in self.to_track.items():
                print(f'{uuid}: {progress}')

class DownloadManager(Boto3Config):
    """Class for keeping track of active downloads.

    Attributes:
        client: An S3.Client object for use in connecting to bucket.
        contract: A Contract object containing file download metadata (bucket, key, etc.).
    """

    def __init__(self) -> None:
        super().__init__()
        self.download_queue: queue.Queue = queue.Queue()
        self.ready_queue: queue.Queue = queue.Queue()
        self.complete_queue: queue.Queue = queue.Queue()

        self.progress_map: Dict = {}

        self.client = boto3.client('s3',
                                   region_name=self.region_name,
                                   endpoint_url=self.endpoint_url,
                                   aws_access_key_id=self.access_key,
                                   aws_secret_access_key=self.secret_key)

    def submit(self, contract: Contract) -> None:
        """Submit new Contract to Download Manager for remote file."""
        self.download_queue.put(Download(contract=contract))

    def attach_observers(self, download: Download):
        observers = [
            DownloadCompleteObserver(self.move_to_complete_queue)
        ]
        for ob in observers:
            download.attach(ob)
        return download

    def move_to_complete_queue(self, download: Download):
        self.complete_queue.put(download)

    def start(self):
        """Initiates download process by:
            1. Dequeing downloads from download_queue.
            2. Attaching downloads with observers.
            3. Moving downloads to ready_queue.
            4. Starting 'progress' thread.
            4. Starting Connection-Pool.
        """
        for _ in range(self.download_queue.qsize()):
            download = self.download_queue.get()
            self.attach_observers(download)
            self.ready_queue.put(download)

        # start progress tracker thread
        progress_tracker = ProgressTracker(self.progress_map)
        progress_tracker.start()

        #TODO: start connection-pool

        # join threads
        #TODO: join connection-pool
        progress_tracker.join()