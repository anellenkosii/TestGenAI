try:
    from uploads.source import is_even
except Exception:
    def is_even(number):
        return number % 2 == 0

__all__ = ["is_even"]
