import pluggy

hookspec = pluggy.HookspecMarker('default')
hookimpl = pluggy.HookimplMarker('default')


@hookspec
def load_blueprints(core):
    """
    Hook for registering blueprints.
    :param core: The Core controller.
    """
