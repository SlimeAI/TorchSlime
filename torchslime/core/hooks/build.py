from torchslime.core import Context


class BuildHook:

    def build_train(ctx: Context): pass
    def after_build_train(ctx: Context): pass
    def build_eval(ctx: Context): pass
    def after_build_eval(ctx: Context): pass
    def build_predict(ctx: Context): pass
    def after_build_predict(ctx: Context): pass

    def _build_train(ctx: Context):
        h = ctx.hook
        h.plugins.before_build(ctx)
        h.plugins.before_build_train(ctx)
        h.build.build_train(ctx)
        h.build.after_build_train(ctx)
        h.launch.after_build_train(ctx)
        h.plugins.after_build(ctx)
        h.plugins.after_build_train(ctx)
    
    def _build_eval(ctx: Context):
        h = ctx.hook
        h.plugins.before_build(ctx)
        h.plugins.before_build_eval(ctx)
        h.build.build_eval(ctx)
        h.build.after_build_eval(ctx)
        h.launch.after_build_eval(ctx)
        h.plugins.after_build(ctx)
        h.plugins.after_build_eval(ctx)

    def _build_predict(ctx: Context):
        h = ctx.hook
        h.plugins.before_build(ctx)
        h.plugins.before_build_predict(ctx)
        h.build.build_predict(ctx)
        h.build.after_build_predict(ctx)
        h.launch.after_build_predict(ctx)
        h.plugins.after_build(ctx)
        h.plugins.after_build_predict(ctx)


class VanillaBuild(BuildHook):
    
    def build_train(ctx: Context):
        # get handler classes from context
        handler = ctx.handler
        # build training process using handlers
        ctx.run.train = handler.Container([
            # epoch iter
            handler.EpochIteration([
                # set status to 'train'
                handler.State('train', _id='train_status_train'),
                # get dataset
                handler.Dataset(_id='train_dataset_train'),
                # init average setting
                handler.AverageInit(_id='train_average_init_train'),
                # dataset iter
                handler.Iteration([
                    # forward
                    handler.Forward(_id='train_forward_train'),
                    # compute loss
                    handler.Loss(_id='train_loss_train'),
                    # backward and optimizer step
                    handler.Optimizer([
                        handler.Backward(_id='train_backward')
                    ], _id='train_optimizer'),
                    # compute metrics
                    handler.Metrics(_id='train_metrics_train'),
                    # compute average loss value and metrics
                    handler.Average(_id='train_average_train'),
                    # display in console or in log files
                    handler.Display(_id='train_display_train')
                ], _id='train_iteration_train'),
                # apply learning rate decay
                handler.LRDecay(_id='train_lr_decay'),
                # set status to 'val'
                handler.State('val', _id='train_status_val'),
                # get dataset
                handler.Dataset(_id='train_dataset_val'),
                # init average setting
                handler.AverageInit(_id='train_average_init_val'),
                # dataset iter
                handler.Iteration([
                    # forward
                    handler.Forward(_id='train_forward_val'),
                    # compute loss
                    handler.Loss(_id='train_loss_val'),
                    # metrics
                    handler.Metrics(_id='train_metrics_val'),
                    # compute average loss value and metrics
                    handler.Average(_id='train_average_val'),
                    # display in console or in log files
                    handler.Display(_id='train_display_val')
                ], _id='train_iteration_val')
            ], _id='train_epoch_iteration')
        ], _id='train_container')
    
    def after_build_train(ctx: Context):
        ctx.hook.lr_decay_mode
        return super().after_build_train()

    def build_eval(ctx: Context):
        # get handler classes from context
        handler = ctx.handler
        # build evaluating process using handlers
        ctx.run.eval = handler.Container([
            # set status to 'eval'
            handler.State('eval', _id='eval_status'),
            # get dataset
            handler.Dataset(_id='eval_dataset'),
            # clear average metrics
            handler.AverageInit(_id='eval_average_init'),
            # dataset iteration
            handler.Iteration([
                # forward
                handler.Forward(_id='eval_forward'),
                # compute loss
                handler.Loss(_id='eval_loss'),
                # compute metrics
                handler.Metrics(_id='eval_metrics'),
                # compute average metrics
                handler.Average(_id='eval_average'),
                # display
                handler.Display(_id='eval_display')
            ], _id='eval_iteration')
        ], _id='eval_container')
    
    def build_predict(ctx: Context):
        # get handler classes from context
        handler = ctx.handler
        # build predicting process using handlers
        ctx.run.predict = handler.Container([
            # set status to 'predict'
            handler.State('predict', _id='predict_status'),
            # get dataset
            handler.Dataset(_id='predict_dataset'),
            # dataset iteration
            handler.Iteration([
                # forward
                handler.Forward(_id='predict_forward'),
                # display
                handler.Display(_id='predict_display')
            ], _id='predict_iteration')
        ], _id='predict_container')


class StepBuild(VanillaBuild):

    def build_train(ctx: Context):
        return super().build_train()