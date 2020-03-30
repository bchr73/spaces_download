from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from download import Download

class Observer(ABC):
    """The Obvserver interface declares the update method, used by downloads.
    """

    @abstractmethod
    def __init__(self, callback) -> None:
        pass

    @abstractmethod
    def update(self, download: Download) -> None:
        """Receive update from download.
        """
        pass

class DownloadCompleteObserver(Observer):
    """Observer, reacts to download transferred bytes == total bytes.
    """

    def __init__(self, callback) -> None:
        self.callback = callback

    def update(self, download: Download) -> None:
        if download._bytes_transferred == download._size:
            self.callback(download)
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

