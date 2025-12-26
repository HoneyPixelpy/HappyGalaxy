from typing import Dict, Optional, Union


class RaisesResponse(Exception):
    def __init__(
        self, data: Optional[Union[Dict, int]] = None, status: Optional[int] = None
    ):
        self.data = data
        self.status = status
