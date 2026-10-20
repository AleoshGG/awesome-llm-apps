class ToolNotFoundError(LookupError):
    pass


class InvalidToolArgumentsError(ValueError):
    pass


class ProviderConnectionError(RuntimeError):
    pass
