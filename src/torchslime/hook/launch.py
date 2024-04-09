"""
Distributed Launch Hook
"""
from torchslime.utils.launch import LaunchUtil, VanillaLaunchUtil, DistributedLaunchUtil
from torchslime.utils.typing.native import (
    Generator,
    TYPE_CHECKING
)
from .build import BuildInterface
from slime_core.abc.hook.launch import CoreLaunchHook
from torchslime.utils.registry import Registry
if TYPE_CHECKING:
    from torchslime.context import Context

launch_registry = Registry('launch_registry')


class LaunchHook(LaunchUtil, BuildInterface, CoreLaunchHook["Context"]):

    def get_device_info(self, ctx: "Context"): pass


@launch_registry(key='vanilla')
class VanillaLaunch(LaunchHook, VanillaLaunchUtil):
    
    def get_device_info(self, ctx: "Context"):
        return super().get_device_info(ctx)


@launch_registry(key='distributed')
class DistributedLaunch(LaunchHook, DistributedLaunchUtil):

    def build_train_yield(self, ctx: "Context") -> Generator:
        yield
        handler = ctx.handler_ctx
        average_handlers = ctx.pipeline_ctx.train_container.get_by_class(handler.MeterHandler)
        for a_handler in average_handlers:
            state = a_handler.get_id().split('_')[-1]
            a_handler.insert_before_self__(handler.GatherAverageHandler(id=f'gather_average_{state}'))

    def build_eval_yield(self, ctx: "Context") -> Generator:
        yield
        handler = ctx.handler_ctx
        average_handlers = ctx.pipeline_ctx.eval_container.get_by_class(handler.MeterHandler)
        for a_handler in average_handlers:
            state = a_handler.get_id().split('_')[-1]
            a_handler.insert_before_self__(handler.GatherAverageHandler(id=f'gather_average_{state}'))
    
    def get_device_info(self, ctx: "Context"):
        return super().get_device_info(ctx)