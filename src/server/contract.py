import uuid

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
