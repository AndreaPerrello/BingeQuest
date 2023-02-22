import base64
import json

import cryptography.fernet
import quart

from iotech.configurator import Config

_fernet = cryptography.fernet.Fernet(Config(str, 'FERNET', 'key').get().encode('utf-8'))


def encrypt(data: str) -> str:
    encrypted_data = _fernet.encrypt(data.encode())
    b64_hash = base64.urlsafe_b64encode(encrypted_data)
    return b64_hash.decode('ascii')


def encrypt_dict(**data) -> str:
    return encrypt(json.dumps(data))


def decrypt(hash_: str) -> str:
    b64_hash = hash_.encode('ascii')
    encrypted_data = base64.urlsafe_b64decode(b64_hash)
    return _fernet.decrypt(encrypted_data).decode()


def decrypt_dict(hash_: str) -> dict:
    if not hash_:
        return {}
    return json.loads(decrypt(hash_))


def url_for(view_name: str, q: str = None, **kwargs) -> str:
    return quart.url_for(view_name, q=q, d=encrypt_dict(**kwargs))
