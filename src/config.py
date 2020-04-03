from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List

class Boto3Config:
    """Boto3 Client configuration object/loader.

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

    def load_config(self):
        try:
            with open('boto3.conf', 'r') as f:
                env: List[str] = []
                lines = f.read().splitlines()
                for line in lines:
                    env += line.split('=')
                env = iter(env)
                return dict(zip(env,env))
        except FileNotFoundError:
            print('Config file missing')
