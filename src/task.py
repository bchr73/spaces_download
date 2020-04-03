from __future__ import annotations
import os
import sys
import queue
import time
import threading
from abc import abstractmethod
from typing import TYPE_CHECKING, Type, List, Dict

import boto3

from config import Boto3Config
from observer import DownloadCompleteObserver, ProgressObserver, Observable
from contract import Contract
from worker import ConnectionPool

if TYPE_CHECKING:
    import Observer
    import botocore

class Task(Observable):
    """Interface declaring methods for managing subscribers.                                                                                                                  
    """                   

    @abstractmethod
    def start(self, client: botocore.client) -> None:
        raise NotImplementedError

class Download(Task):
    """Class for keeping track of active downloads.

    Attributes:
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
        super().__init__()
        self.id = contract.id
        self.bucket = contract.bucket
        self.key = contract.key
        self.filename = contract.filename
        self.extra_args = contract.extra_args

        self._bytes_transferred = 0
        self._lock = threading.Lock()

    def progress(self, new_bytes) -> None:
        """Callback function to update newly transferred bytes on download."""
        with self._lock:
            self._bytes_transferred += new_bytes
            self.notify()

    def start(self, client: botocore.client) -> None:
        """Fetches object size and initiates download."""
        try:
            self._size = client.head_object(Bucket=self.bucket, Key=self.filename).get('ContentLength')
        except Exception as e:
            print(f'Failed to retrieve object size: {self.bucket} {self.filename}')
            print(e)
        self._started = time.time()
        client.download_file(Bucket=self.bucket,
                       Key=self.key,
                       Filename=self.filename,
                       ExtraArgs=self.extra_args,
                       Callback=self.progress)

class ProgressTracker(threading.Thread):
    """Simple class that accepts a dict and displays formatted output
       of contents.

    Attributes:
        to_track: Object of type dict containing information for active downloads
    """

    def __init__(self, to_track: Dict) -> None:
        super().__init__()
        self.running = False
        self.to_track = to_track

    def run(self):
        self.running = True
        while self.running:
            print('Progress:')
            for uuid, progress in self.to_track.items():
                print(f'{uuid}: {progress}', flush=True)
            time.sleep(2)
            os.system('clear')
            
    def stop(self,timeout=None):
        self.running = False
        super().join(timeout)
        print(f'ProgressTracker {self.name} joined')

class DownloadManager:
    """Class for keeping track of active downloads.

    Attributes:
        client: An botocore.client object for use in connecting to bucket.
        contract: A Contract object containing file download metadata (bucket, key, etc.).
    """

    def __init__(self, max_workers: int=1) -> None:
        self.download_queue: queue.Queue = queue.Queue()
        self.ready_queue: queue.Queue = queue.Queue()
        self.complete_queue: queue.Queue = queue.Queue()
        self.progress_map: Dict = {}

        self.connection_pool = ConnectionPool(self.ready_queue, max_workers)

    def submit(self, contract: Contract) -> None:
        """Submit new Contract to Download Manager for remote file."""
        self.download_queue.put(Download(contract=contract))

    def move_to_complete_queue(self, task: Type[Task]):
        self.complete_queue.put(task)
        print(f'Download {task.id} complete.')

    def update_progress_map(self, task: Type[Task]):
        percentage = round((task._bytes_transferred / task._size) * 100, 2)
        transfer_rate = round((task._bytes_transferred / (time.time() - task._started)) / 1000000, 2)
        self.progress_map[task.id] = f'transferred {percentage}%  {transfer_rate}Mb/s'

    def attach_observers(self, task: Type[Task]):
        observers = [
            DownloadCompleteObserver(self.move_to_complete_queue),
            ProgressObserver(self.update_progress_map)
        ]
        for ob in observers:
            task.attach(ob)
        return task

    def start(self):
        """Initiates download process.
        """
        for _ in range(self.download_queue.qsize()):
            download = self.download_queue.get()
            # attach observers to download
            self.attach_observers(download)
            self.ready_queue.put(download)

        # start progress tracker thread
        self.progress_tracker = ProgressTracker(self.progress_map)
        self.progress_tracker.start()

        # start connection pool
        self.connection_pool.start()

    def stop(self,sig,frame):
            print("Joining threads")
            try:
                # join threads
                self.connection_pool.stop()
                self.progress_tracker.stop()
            except Exception as e:
                print(e)
            print("Exiting")

