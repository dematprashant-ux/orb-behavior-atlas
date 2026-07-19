"""Provider-neutral adapter framework for canonical Data Engine sources."""

from src.engines.data.providers._base import BaseProviderAdapter
from src.engines.data.providers._config import ProviderConfig
from src.engines.data.providers._protocol import ProviderAdapter

__all__ = ["BaseProviderAdapter", "ProviderAdapter", "ProviderConfig"]
