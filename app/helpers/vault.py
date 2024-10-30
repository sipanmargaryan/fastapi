import json

import boto3

from app.settings import AWS_ACCESS_KEY_ID, AWS_DEFAULT_REGION, AWS_SECRET_ACCESS_KEY


def lazy_property(fn):
    """
    Decorator that makes a property lazy-evaluated.
    """
    attr_name = "_lazy_" + fn.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    return _lazy_property


class SSMParameterStoreClient:
    @lazy_property
    def client(self):
        return boto3.client(
            "ssm",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_DEFAULT_REGION,
        )

    def set_parameter(
        self, key: str, value: dict, parameter_type: str = "SecureString"
    ):
        input_data = json.dumps(value)
        return self.client.put_parameter(
            Name=key, Value=input_data, Type=parameter_type, Overwrite=True
        )

    def delete_parameter(self, key: str):
        return self.client.delete_parameter(Name=key)

    def get_parameter(self, key: str, encryption: bool = True):
        value = self.client.get_parameter(Name=key, WithDecryption=encryption)[
            "Parameter"
        ]["Value"]
        return json.loads(value)
