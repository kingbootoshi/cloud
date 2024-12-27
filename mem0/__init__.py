import importlib.metadata

try:
    __version__ = importlib.metadata.version("mem0ai")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.1.0"  # Default version if not installed

from mem0.client.main import MemoryClient, AsyncMemoryClient  # noqa
from mem0.memory.main import Memory  # noqa
