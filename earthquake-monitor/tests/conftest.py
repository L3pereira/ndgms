"""Root pytest configuration for all tests."""

import os

# Set testing environment at the earliest possible point
os.environ["TESTING"] = "true"
