#!/usr/bin/env python3
import boto3
import threading
import os
import sys
import time
import uuid
from abc import ABC, abstractmethod
import dataclasses
from typing import AnyStr, Callable

class SpacesConfig:
    """DigitalOcean Spaces configuration object/loader.

    Attributes:
        bucket: String containing Digital Ocean Spaces bucket name.
    """

    def __init__(self):
        config = self.load_config()
        self.bucket_name = config.get('SPACES_NAME')
        self.access_key = config.get('ACCESS_KEY')
        self.secret_key = config.get('SECRET_KEY')
        self.region_name = config.get('REGION_NAME')
        self.endpoint_url = config.get('ENDPOINT')

        #self.root_folder = config.get('ROOT_FOLDER')
        #self.dest_folder = config.get('DEST_FOLDER')
        print(self.__dict__)

    def load_config(self):
        try:
            with open('config', 'r') as f:
                env = []
                lines = f.read().splitlines()
                for line in lines:
                    env += line.split('=')
                env = iter(env)
                return dict(zip(env,env))
        except FileNotFoundException:
            print('Config file missing')

class Contract:
    """File metadata for Download Manager request object.

    Attributes:
        id: String object, contains a unique 8 character sequence.
        bucket: String containing Digital Ocean Spaces bucket name.
        key: String containing where the remote file is located inside bucket.
        filename: Path like string object containing where to store download.
        extra_args: Dict containing any extra arguments to supply 'download_file' method.
    """

    def __init__(self, bucket: str, key: str, filename: str, extra_args: dict) -> None:
        self.id = str(uuid.uuid4())[:8]
        self.bucket = bucket
        self.key = key
        self.filename = filename
        self.extra_args = extra_args

class ContractFactory:
    """Factory class for creating contracts.

    Attributes:
        bucket: String containing Digital Ocean Spaces bucket name.
    """

    def __init__(self, bucket: str) -> None:
        self.bucket = bucket

    def new(self, key: str, filename: str, extra_args: dict=None) -> Contract:
        """Returns a new Contract object."""
        return Contract(self.bucket,
                        key,
                        filename,
                        extra_args)

class Observer(ABC):
    """The Obvserver interface declares the update method, used by downloads.
    """

    @abstractmethod
    def update(self, download: 'Download') -> None:
        """Receive update from download.
        """
        pass

class DownloadCompleteObserver(Observer):
    """Observer, reacts to download transferred bytes == total bytes.
    """

    def update(self, download: 'Download') -> None:
        if download._bytes_transferred == download._size:
            print(f'Download {download.id} complete.')

class Observable(ABC):
    """Interface declaring methods for managing subscribers.
    """

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        """Attach an observer to the subscriber.
        """
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        """Detach an observer from the subscriber.
        """
        pass

    @abstractmethod
    def notify(self) -> None:
        """Notify all observers about an event.
        """
        pass

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

    def __init__(self, client: 'botocore.client.S3', contract: Contract) -> None:
        self.client = client
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
            self.notify()

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

class DownloadManager(SpacesConfig):
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
        session = boto3.session.Session()
        self.client = session.client('s3',
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


if __name__ == '__main__':

    filenames = [
            'The.Mandalorian.S01E01.INTERNAL.1080p.WEB.H264-DEFLATE.mkv',
            'The.Mandalorian.S01E02.1080p.WEBRip.DDP5.1.x264-CUSTOM.mkv',
            'The.Mandalorian.S01E03.1080p.WEB.H264-PETRiFiED.mkv',
            'The.Mandalorian.S01E04.1080p.WEBRiP.x264-PETRiFiED.mkv',
            'The.Mandalorian.S01E05.1080p.WEBRiP.x264-PETRiFiED.mkv',
            'The.Mandalorian.S01E06.REPACK.1080p.WEBRiP.x264-PETRiFiED.mkv',
            'The.Mandalorian.S01E07.1080p.WEBRiP.x264-PETRiFiED.mkv',
            'The.Mandalorian.S01E08.1080p.WEBRiP.x264-PETRiFiED.mkv'
        ]
    sam_cham = 'samurai_champloo_ep1.mkv'

    dm = DownloadManager()
    cf = ContractFactory('karim-storage')

    contract = cf.new(sam_cham, sam_cham)

    dm.submit(contract)
    dm.start()
