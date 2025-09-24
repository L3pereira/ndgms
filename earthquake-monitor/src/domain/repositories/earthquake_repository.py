"""Composite earthquake repository interface."""

from .earthquake_query import EarthquakeQuery
from .earthquake_reader import EarthquakeReader
from .earthquake_search import EarthquakeSearch
from .earthquake_writer import EarthquakeWriter


class EarthquakeRepository(
    EarthquakeWriter, EarthquakeReader, EarthquakeQuery, EarthquakeSearch
):
    """
    Composite interface combining all earthquake repository capabilities.

    This interface follows the Interface Segregation Principle by composing
    focused interfaces, while maintaining backward compatibility.

    Clients can depend on the specific interfaces they need:
    - EarthquakeWriter: For save operations
    - EarthquakeReader: For basic read operations
    - EarthquakeQuery: For filtered queries
    - EarthquakeSearch: For advanced search with pagination
    """

    pass
