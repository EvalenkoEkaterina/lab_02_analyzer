class StreamStatsError(Exception):
    pass


class InvalidEventError(StreamStatsError):
    pass


class InvalidTimestampError(InvalidEventError):
    pass

class UnsupportedFormatError(StreamStatsError):
    pass

class CLIConfigError(StreamStatsError):
    pass