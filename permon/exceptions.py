class NoStatError(Exception):
    """
    This is raised if the app is started without
    any stats to display.
    """
    pass


class InvalidStatError(Exception):
    """
    This is raised if an invalid stat is encountered
    e. g. the tag does not exist.
    """
    pass


class StatNotAvailableError(Exception):
    """
    This is raised if the stat does exist but is not available
    e. g. a required module is not installed.
    """
    pass


class FrontendNotAvailableError(Exception):
    """
    This is raised if the desired frontend is not available
    e. g. the user has answered no to installing the required modules.
    """
    pass
