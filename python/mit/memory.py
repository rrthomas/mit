'''
VM memory.

(c) Mit authors 2019

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import collections.abc

from .binding import *


# Memory access (word & byte)
class AbstractMemory(collections.abc.Sequence):
    '''A VM memory (abstract superclass).'''
    def __init__(self, VM, element_size):
        self.VM = VM
        self.element_size = element_size

    def __getitem__(self, index):
        if isinstance(index, slice):
            index_ = slice(index.start, index.stop, self.element_size)
            return [self[i] for i in range(*index_.indices(len(self)))]
        else:
            return self.load(index)

    def __setitem__(self, index, value):
        if type(index) == slice:
            index_ = slice(index.start, index.stop, self.element_size)
            j = 0
            for i in range(*index_.indices(len(self))):
                self[i] = value[j]
                j += 1
        else:
            self.store(index, value)

    def load(self, index):
        '''
        Return the value at `index`.
        This is an abstract method, which must be overridden.
        '''
        raise NotImplementedError

    def store(self):
        '''
        Store `value` at `index`.
        This is an abstract method, which must be overridden.
        '''
        raise NotImplementedError

    def __len__(self):
        '''
        Returns the number of read/writable locations.
        '''
        return self.VM.memory_bytes // self.element_size

class Memory(AbstractMemory):
    '''A VM memory (byte-accessed).'''
    def __init__(self, VM):
        super().__init__(VM, 1)

    def load(self, index):
        word = c_word()
        libmit.mit_load(self.VM.state, index, 0, byref(word))
        return word.value

    def store(self, index, value):
        libmit.mit_store(self.VM.state, index, 0, value)

class WordMemory(AbstractMemory):
    '''A VM memory (word-accessed).'''
    def __init__(self, VM):
        super().__init__(VM, word_bytes)

    def load(self, index):
        word = c_word()
        libmit.mit_load(self.VM.state, index, size_word, byref(word))
        return word.value

    def store(self, index, value):
        libmit.mit_store(self.VM.state, index, size_word, value)
