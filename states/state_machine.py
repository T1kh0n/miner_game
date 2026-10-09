class State:
    def __init__(self, manager):
        self.manager = manager
    def enter(self): pass
    def exit(self): pass
    def handle_event(self, event, mouse_pos): pass
    def update(self, dt): pass
    def render(self, surface): pass

class StateMachine:
    def __init__(self):
        self.states = {}
        self.current_state = None
    def add_state(self, name, state):
        self.states[name] = state
    def change(self, name):
        if self.current_state: self.current_state.exit()
        self.current_state = self.states[name]
        self.current_state.enter()
    def handle_event(self, event, mouse_pos):
        if self.current_state: self.current_state.handle_event(event, mouse_pos)
    def update(self, dt):
        if self.current_state: self.current_state.update(dt)
    def render(self, surface):
        if self.current_state: self.current_state.render(surface)
