from iotech.microservice.web import db

from ..security import encrypt_dict, decrypt_dict


class CacheEntries(db.Model):

    name = db.Column(db.String(64), primary_key=True)
    id = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text)

    @classmethod
    def get(cls, name: str, id_: str) -> dict:
        entry = cls.query.filter_by(name=name, id=id_).first()
        if entry:
            return decrypt_dict(entry.value)

    @classmethod
    def set(cls, name: str, id_: str, value: dict):
        item = cls(name=name, id=id_, value=encrypt_dict(**value))
        db.session.add(item)
        db.session.commit()
