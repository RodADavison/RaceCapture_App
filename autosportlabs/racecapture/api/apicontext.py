from kivy.logger import Logger
import traceback

class ApiDispatcher(object):

    instance = None
    def __init__(self):
        self.msg_listeners = {}

    @staticmethod
    def get_instance():
        if ApiDispatcher.instance is None:
            ApiDispatcher.instance = ApiDispatcher()
        return ApiDispatcher.instance

    def add_listener(self, msg_name, callback):
        listeners = self.msg_listeners.get(msg_name, None)
        if listeners:
            listeners.add(callback)
        else:
            listeners = set()
            listeners.add(callback)
            self.msg_listeners[msg_name] = listeners

    def remove_listener(self, msg_name, callback):
        listeners = self.msg_listeners.get(msg_name, None)
        if listeners:
            listeners.discard(callback)

    def dispatch_msg(self, msg_json, source):
        for msg_name in msg_json.keys():
            Logger.trace('ApiDispatcher: processing message: {}'.format(msg_name))
            listeners = self.msg_listeners.get(msg_name, None)
            if listeners:
                for listener in listeners:
                    try:
                        listener(msg_json, source)
                    except Exception as e:
                        Logger.error('ApiDispatcher: Message Listener Exception for {}'.format(msg_json))
                        Logger.error(traceback.format_exc())
                break
