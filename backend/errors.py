class ApiError(Exception):
    """Raise anywhere to return a clean JSON error."""
    def __init__(self, message, code=400):
        super().__init__(message)
        self.message = message
        self.code = code
