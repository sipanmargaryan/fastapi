from urllib.parse import urlparse

from app.helpers.exceptions import PermissionDeniedError


def split_domain(url):
    url_str = str(url)
    netloc = urlparse(url_str).netloc
    components = netloc.split(".")
    if len(components) > 2:
        return ".".join(components[:-2])
    else:
        raise PermissionDeniedError
