# NOTE: import here just for backward compatibility. Importing from the specific 
# modules is recommended.
from .native import *
from .extension import *

#
# Torch version adapter
#

try:
    from torch.optim.lr_scheduler import LRScheduler as TorchLRScheduler
except ImportError:
    from torch.optim.lr_scheduler import _LRScheduler as TorchLRScheduler
