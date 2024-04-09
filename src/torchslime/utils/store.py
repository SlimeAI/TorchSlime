import threading
from abc import ABCMeta
from io import TextIOWrapper
from slime_core.utils.store import (
    ScopedStore,
    CoreStore
)
from .metaclass import (
    Metaclasses,
    SingletonMetaclass
)
from .typing.native import (
    List,
    Union,
    TextIO
)
from .typing.extension import (
    Nothing
)
from .metaclass.metabase import Singleton


class BuiltinScopedStore(
    ScopedStore,
    Singleton,
    metaclass=Metaclasses(ABCMeta, SingletonMetaclass)
):
    
    def __init__(self) -> None:
        """
        set ``builtin__`` store config
        """
        super().__init__()
        # call debug config
        self.call_debug = False
        self.call_debug_full_exec_name = False
        # indent str for CLI display
        self.indent_str = ' ' * 4  # default is 4 spaces
        # log template
        self.log_template: str = '{prefix__} - {asctime} - "{filename}:{lineno}" - {message}'
        self.log_rich_template: str = '{message}'
        self.log_dateformat: str = '%Y/%m/%d %H:%M:%S'
        # launch
        # NOTE: The ``launch`` value should ONLY be str in order to be compatible with 
        # different LaunchUtils and Launchers (Specifically, ``Context`` uses ``LaunchHook`` 
        # while the ``logger`` and rich launcher use the native ``LaunchUtil``, so the 
        # ``launch`` value should ONLY be str, which can be accepted by all of them).
        # NOTE: All the launch-related registries should share the naming to keep consistency 
        # (e.g., the name 'vanilla' should mean the non-distributed running in all registries, 
        # and they may have similar behaviors).
        self.launch: str = 'vanilla'
    
    def delay_init__(self) -> None:
        """
        Delay initialization.
        Initialization of some items should be delayed due to circular import.
        This method should be called after creation of ``torchslime.utils.store.store``.
        """
        # console
        from torchslime.logging.rich import (
            SlimeConsoleLauncher,
            SlimeAltConsoleLauncher,
            rich
        )
        self.console_launcher: Union[SlimeConsoleLauncher, Nothing] = SlimeConsoleLauncher()
        self.alt_console_launcher: Union[SlimeAltConsoleLauncher, Nothing] = SlimeAltConsoleLauncher(
            color_system=None,
            force_terminal=False,
            force_jupyter=False,
            force_interactive=False
        )
        self.alt_console_files: List[Union[TextIO, TextIOWrapper]] = []
        # set rich default console
        rich._console = self.console_launcher


# NOTE: ``_builtin_scoped_store`` is NOT thread-independent, and it is a global object.
_builtin_scoped_store = BuiltinScopedStore()

#
# Store
#

class Store(CoreStore):
    
    scoped_store_local__: threading.local = threading.local()
    
    def builtin__(self) -> BuiltinScopedStore:
        return _builtin_scoped_store


store = Store()
# Builtin scoped store delay initialization.
store.builtin__().delay_init__()
