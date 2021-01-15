"""
MonkeyPatch to allow TenantFileSystemStorage to return the url of the files according to the tenant.
"""

from django.utils.encoding import filepath_to_uri
from django.utils.six.moves.urllib.parse import urljoin
from django.db import connection
from tenant_schemas.storage import TenantFileSystemStorage


def url(self, name):
    """Permite guardar según tenants."""

    if self.base_url is None:
        raise ValueError("This file is not accessible via a URL.")

    base_url = "{0}{1}/".format(self.base_url, connection.tenant.domain_url)
    return urljoin(base_url, filepath_to_uri(name))


TenantFileSystemStorage.url = url
