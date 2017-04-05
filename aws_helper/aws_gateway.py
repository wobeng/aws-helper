import requests
import traceback
from requests_aws4auth import AWS4Auth


class Gateway:
    def __init__(self, session):
        cred = session.get_credentials()
        self.auth = AWS4Auth(
            cred.access_key,
            cred.secret_key,
            session.region_name,
            "execute-api", session_token=cred.token
        )
        print(cred.access_key)
        print(cred.secret_key)
        print(cred.token)
        print(session.region_name)
        print(traceback.print_stack())
    def invoke(self, method, endpoint, data=None, json=None, params=None):
        method = getattr(requests, method)
        response = method(endpoint, data=data, params=params, json=json, auth=self.auth)
        response.raise_for_status()
        return response
