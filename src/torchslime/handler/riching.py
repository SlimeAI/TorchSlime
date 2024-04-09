from torchslime.utils.typing.native import (
    Any,
    Callable,
    Iterable,
    Tuple,
    TYPE_CHECKING,
    Union
)
from torchslime.utils.typing.extension import (
    NOTHING,
    NoneOrNothing,
    is_none_or_nothing
)
from torchslime.logging.rich import (
    Group,
    RenderableType,
    Table,
    Text,
    Tree,
    parse_renderable,
    escape
)
from torchslime.utils.base import (
    BaseList,
    CompositeBFT
)
from torchslime.utils.store import store
from contextlib import contextmanager

if TYPE_CHECKING:
    from torchslime.context import Context
    from torchslime.handler import Handler
    from torchslime.handler.wrapper import HandlerWrapper, HandlerWrapperContainer

#
# Handler Progress Interface
#

class _ProgressInterface:
    
    def create_progress__(self, ctx: "Context") -> Tuple[Any, Any]: pass
    def progress_update__(self, ctx: "Context") -> None: pass
    def remove_progress__(self, ctx: "Context") -> None: pass

    def add_progress__(self, ctx: "Context") -> None:
        display_ctx = ctx.display_ctx
        display_ctx.live_group.append(display_ctx.handler_progress)

    @contextmanager
    def progress_context__(self, ctx: "Context"):
        progress, task_id = self.create_progress__(ctx)
        with ctx.display_ctx.assign__(
            handler_progress=progress,
            progress_task_id=task_id
        ):
            self.add_progress__(ctx)
            yield
            self.remove_progress__(ctx)


class ProgressInterface(_ProgressInterface):
    
    def progress_update__(self, ctx: "Context") -> None:
        """
        Update the progress bar.
        """
        ctx.display_ctx.handler_progress.advance(
            task_id=ctx.display_ctx.progress_task_id,
            advance=1
        )

    def remove_progress__(self, ctx: "Context") -> None:
        # Remove self from the ``Live`` object.
        ctx.display_ctx.handler_progress.remove_self__()
        # detach observer
        store.builtin__().detach__(ctx.display_ctx.handler_progress)


class ProfileProgressInterface(_ProgressInterface):

    def progress_update__(self, ctx: "Context") -> None:
        """
        Update the progress bar and the displayed text.
        """
        ctx.display_ctx.handler_progress.progress.advance(
            task_id=ctx.display_ctx.progress_task_id,
            advance=1
        )
        ctx.display_ctx.handler_progress.set_text__(
            f'{ctx.pipeline_ctx.pipeline_profiler.meter_profile(ctx)}'
        )

    def remove_progress__(self, ctx: "Context") -> None:
        # Remove self from the ``Live`` object.
        ctx.display_ctx.handler_progress.remove_self__()
        # detach observer
        store.builtin__().detach__(ctx.display_ctx.handler_progress.progress)

#
# Handler Structure Display
#

class HandlerTreeProfiler:

    def handler_profile(
        self,
        handler: "Handler",
        display_attr: bool = True,
        target_handlers: Union[Iterable["Handler"], NoneOrNothing] = NOTHING,
        wrap_func: Union[str, Callable[[Group, "Handler"], Group], NoneOrNothing] = NOTHING
    ) -> Group:
        renderables = [
            Text(handler.get_classname(), style='bold blue')
        ]

        if display_attr:
            attr = handler.get_display_attr_dict()
            if len(attr) >= 1:
                attr_table = Table()
                attr_table.add_column('Attr', style='cyan')
                attr_table.add_column('Value', style='green')

                for key, value in attr.items():
                    attr_table.add_row(
                        parse_renderable(key),
                        parse_renderable(value)
                    )

                renderables.append(attr_table)

        group = Group(*renderables)
        if not self.check_target_handler(handler, target_handlers):
            return group

        wrap_func = self.get_handler_profile_wrap_func(wrap_func)
        if is_none_or_nothing(wrap_func):
            from torchslime.logging.logger import logger
            logger.warning(
                'Handler profile wrap func is ``None`` or ``NOTHING``, '
                'and it will do nothing during display.'
            )
            return group
        return wrap_func(group, handler)

    def profile(
        self,
        handler: "Handler",
        display_attr: bool = True,
        target_handlers: Union[Iterable["Handler"], NoneOrNothing] = NOTHING,
        wrap_func: Union[str, Callable[[Group, "Handler"], Group], NoneOrNothing] = NOTHING
    ) -> Tree:
        root = Tree(self.handler_profile(handler))
        queue = [
            root
        ]

        def visit(node: "Handler"):
            tree = queue.pop(0)
            for child in node.composite_iterable__():
                new_tree = tree.add(self.handler_profile(
                    child,
                    display_attr=display_attr,
                    target_handlers=target_handlers,
                    wrap_func=wrap_func
                ))
                queue.append(new_tree)

        CompositeBFT(handler, visit)
        return root

    def check_target_handler(
        self,
        handler: "Handler",
        target_handlers: Union[Iterable["Handler"], NoneOrNothing] = NOTHING
    ) -> bool:
        return handler in BaseList.create__(
            target_handlers,
            return_constant=False
        )

    def get_handler_profile_wrap_func(
        self,
        wrap_func: Union[str, Callable[[Group, "Handler"], Group], NoneOrNothing] = NOTHING
    ) -> Union[Callable[[Group, "Handler"], Group], NoneOrNothing]:
        if isinstance(wrap_func, str):
            return handler_profile_wrap_func.get(wrap_func, NOTHING)
        return wrap_func


from torchslime.utils.registry import Registry
handler_profile_wrap_func = Registry[Callable[[Group, "Handler"], Group]]('handler_profile_wrap_func')


@handler_profile_wrap_func(key='exception')
def _exception_wrap(group: Group, handler: "Handler") -> Group:
    _separator_len = 10
    # ×  <---------- EXCEPTION Here ----------
    _exception_indicator = f' {chr(0x00D7)}  <{"-" * _separator_len} EXCEPTION Here {"-" * _separator_len}'
    original_text = group.renderables[0]
    group.renderables[0] = Text.assemble(original_text, Text(_exception_indicator, style='bold red'))
    return group


@handler_profile_wrap_func(key='terminate')
def _terminate_wrap(group: Group, handler: "Handler") -> Group:
    _separator_len = 10
    # ||---------- Handler TERMINATE Here ----------||
    _terminate_indicator = f' ||{"-" * _separator_len} Handler TERMINATE Here {"-" * _separator_len}||'
    original_text = group.renderables[0]
    group.renderables[0] = Text.assemble(original_text, Text(_terminate_indicator, style='bold green'))
    return group

#
# Handler Wrapper Display
#

class HandlerWrapperContainerProfiler:

    # When used as wrappers, these attributes won't work, so neither should they 
    # be displayed.
    ignored_display_attrs = ('exec_ranks', 'wrappers', 'lifecycle')

    def wrapper_profile(
        self,
        wrapper: Union["HandlerWrapper", "HandlerWrapperContainer"]
    ) -> str:
        from torchslime.utils.common import dict_to_key_value_str_list, concat_format

        class_name = wrapper.get_classname()

        display_attr_dict = wrapper.get_display_attr_dict()
        # Remove the ignored display attributes.
        for ignored_attr in self.ignored_display_attrs:
            display_attr_dict.pop(ignored_attr, None)

        display_attr_list = dict_to_key_value_str_list(display_attr_dict)
        attr = concat_format('(', display_attr_list, ')', item_sep=', ')

        return escape(f'{class_name}{attr}')

    def profile(self, handler_wrapper_container: "HandlerWrapperContainer") -> RenderableType:
        table = Table(show_lines=True)
        table.add_column('index')
        table.add_column('wrapper/container')

        table.add_row('[bold]Container', f'[bold]{self.wrapper_profile(handler_wrapper_container)}')

        for index, handler_wrapper in enumerate(handler_wrapper_container):
            table.add_row(str(index), self.wrapper_profile(handler_wrapper))

        return table