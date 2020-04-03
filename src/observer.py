from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from task import Task, Download
    from typing import Type, List

class Observer:
    """The Obvserver interface declares the update method, used by downloads.
    """

    def __init__(self, callback=None) -> None:
        self._callback = callback

    def update(self, task: Type[Task]) -> None:
        """Receive update from task.
        """
        raise NotImplementedError

class Observable:
    """Interface declaring methods for managing subscribers.                                                                                                                  
    """                   

    def __init__(self):
        self._observers: List = []

    def attach(self, observer: Observer) -> None:
        """Attach an observer to the subscriber.                                                                                                                              
        """
        if not observer in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """Detach an observer from the subscriber.                                                                                                                            
        """
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self) -> None:
        """Notify all observers about an event.                                                                                                                               
        """
        for observer in self._observers:
            observer.update(self)

class DownloadCompleteObserver(Observer):
    """Moves Download to complete_queue when fully transferred.
    """

    def update(self, download: Type[Download]) -> None:
        if download._bytes_transferred == download._size:
            return self._callback()

class ProgressObserver(Observer):
    """Updates progress_map with progress information.
    """
    pass