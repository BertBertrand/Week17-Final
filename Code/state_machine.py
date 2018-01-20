#The following code was taken from David Mertz's excellent book
#'Text Processing in Python' available at http://gnosis.cx/TPiP/.
#All code examples in TPIP has been graciously released to the 
#public domain by David Mertz.

class InitializationError(Exception): pass

class StateMachine:
    def __init__(self):
        self.handlers = []
        self.startState = None
        self.endStates = []

    def add_state(self, handler, end_state=0):
        self.handlers.append(handler)
        if end_state:
            self.endStates.append(handler)

    def set_start(self, handler):
        self.startState = handler

    def run(self, cargo=None):
        if not self.startState:
            raise InitializationError,\
                  "must call .set_start() before .run()"
        if not self.endStates:
            raise InitializationError, \
                  "at least one state must be an end_state"
        handler = self.startState
        while 1:
            (newState, cargo) = handler(cargo)
            if newState in self.endStates:
                newState(cargo)
                break
            elif newState not in self.handlers:
                raise RuntimeError, "Invalid target %s" % newState
            else:
                handler = newState
