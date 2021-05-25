import event_bus

_event_bus = event_bus.EventBus()


class EventBus(object):
    def on(self, event: str):
        return _event_bus.on(event)

    def emit(self, event: str, *args, **kwargs):
        _event_bus.emit(event, *args, **kwargs)
