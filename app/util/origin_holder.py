# Equivalent of OriginHolder.java
# A simple singleton-like holder for the upstream origin URL,
# set once at startup and used throughout the app.

class OriginHolder:
    def __init__(self):
        self._origin: str | None = None

    def get_origin(self) -> str | None:
        return self._origin

    def set_origin(self, origin: str):
        self._origin = origin


# Single shared instance (mimics Spring @Component singleton)
origin_holder = OriginHolder()
