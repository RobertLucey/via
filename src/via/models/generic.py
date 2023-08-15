import uuid
from typing import Any, Iterable, Mapping


class GenericObjects:
    def __init__(self, *args, **kwargs):
        """

        :kwarg data:
        :kwarg child_class:
        """
        self._uuid = kwargs.get("uuid", None)
        self.child_class = kwargs.get("child_class", GenericObject)
        self._data = [self.child_class.parse(d) for d in kwargs.get("data", [])]

    @property
    def uuid(self):
        if self._uuid is None:
            self._uuid = uuid.uuid4()
        return self._uuid

    def __getitem__(self, i):
        return self._data[i]

    def __iter__(self):
        return (i for i in self._data)

    def __len__(self):
        return len(self._data)

    def append(self, obj: Any) -> None:
        """

        :param obj:
        """
        if not isinstance(obj, self.child_class):
            obj = self.child_class.parse(obj)
        self._data.append(obj)

    def extend(self, objs: Iterable[Any]) -> None:
        """

        :param objs:
        """
        for obj in objs:
            self.append(obj)

    def serialize(self) -> Iterable[Mapping[str, Any]]:
        return [obj.serialize() for obj in self._data]

    @staticmethod
    def parse(objs):  # pragma: nocover
        raise NotImplementedError()


class GenericObject:
    def __init__(self, *args, **kwargs):
        """

        :kwarg data:
        """
        self._uuid = kwargs.get("uuid", None)

    @property
    def uuid(self):
        if self._uuid is None:
            self._uuid = uuid.uuid4()
        return self._uuid

    def __repr__(self):
        return str("%s(%s)" % (type(self).__name__, self.uuid))

    @staticmethod
    def parse(obj):  # pragma: nocover
        raise NotImplementedError()

    def serialize(self):  # pragma: nocover
        raise NotImplementedError()
