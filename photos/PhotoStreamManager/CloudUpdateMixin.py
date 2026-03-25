from collections.abc import Callable
from typing import TypeVar, Generic

T = TypeVar('T')

class CloudUpdateMixin(Generic[T]):
    def cloud_update(self):
        self._cloud_update(self)

    def set_cloud_update_func(self, update_func: Callable[[T], None]):
        self._cloud_update = update_func