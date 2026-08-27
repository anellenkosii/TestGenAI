# Re-export the example source from uploads so tests importing
# `from source import ...` work regardless of current working dir.
try:
    from uploads.source import *
except Exception:
    # Fallback minimal implementation
    def is_even(number):
        return number % 2 == 0
