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

        self._observers = []

    def progress(self, new_bytes) -> None:
        """Callback function to update newly transferred bytes on download."""
        with self._lock:
            self._bytes_transferred += new_bytes

    def start(self) -> str:
        """Initiates file download."""
        self.client.download_file(Bucket=self.bucket, 
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

class DownloadManager(Boto3Config):
    """Class for keeping track of active downloads.

    Attributes:
        client: An S3.Client object for use in connecting to bucket.
        contract: A Contract object containing file download metadata (bucket, key, etc.).
    """

    def __init__(self) -> None:
        super().__init__()
        self.ready_queue = {}
        self.download_queue = {}
        self.complete_queue = {}
        self.client = boto3.client('s3',
                                   region_name=self.region_name,
                                   endpoint_url=self.endpoint_url,
                                   aws_access_key_id=self.access_key,
                                   aws_secret_access_key=self.secret_key)

    def submit(self, contract: Contract) -> None:
        """Submit new Contract to Download Manager for remote file."""
        self.ready_queue[contract.id] = Download(client=self.client, contract=contract)

    def start(self):
        """Start downloads in ready queue and move to download_queue."""
        for uuid in list(self.ready_queue):
            download = self.ready_queue[uuid]
            download.attach(DownloadCompleteObserver())
            download.start()
            self.download_queue[uuid] = self.ready_queue.pop(uuid)
