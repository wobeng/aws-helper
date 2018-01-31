import os


class Ssm:
    def __init__(self, session):
        self.client = session.client('ssm')

    def parameter(self, name, default=None):
        value = os.environ.get(name, default)
        if not value:
            try:
                value = self.client.get_parameter(Name=name, WithDecryption=True)['Parameter']['Value']
                os.environ[name] = value
            except BaseException:
                pass
        return value
