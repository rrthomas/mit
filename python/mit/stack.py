'''
VM stack.

(c) Mit authors 2019

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from .binding import *


# Stacks
class Stack:
    '''VM stack.'''
    def __init__(self, state, depth):
        self.state = state
        self.depth = depth

    def __str__(self):
        l = []
        for i in range(self.depth.get(), 0, -1):
            v = c_word()
            libmit.mit_load_stack(self.state, i - 1, byref(v))
            l.append('{v} ({v:#x})'.format(v=v.value))
        return '[{}]'.format(', '.join(l))

    def __getitem__(self, index):
        if isinstance(index, slice):
            index_ = slice(index.start, index.stop)
            return [self[i] for i in range(*index_.indices(self.depth.get()))]
        else:
            v = c_word()
            libmit.mit_load_stack(self.state, self.depth.get() - 1 - index, byref(v))
            return v.value

    def __setitem__(self, index, value):
        if type(index) == slice:
            index_ = slice(index.start, index.stop)
            j = 0
            for i in range(*index_.indices(self.depth.get())):
                self[i] = value[j]
                j += 1
        else:
            libmit.mit_store_stack(self.state, self.depth.get() - 1 - index, value)

    def push(self, v):
        '''Push a word on to the stack.'''
        ret = libmit.mit_push_stack(self.state, v)

    def pop(self):
        '''Pop a word off the stack.'''
        v = c_word()
        ret = libmit.mit_pop_stack(self.state, byref(v))
        return v.value
