'''
Writable memory view.

(c) Mit authors 2019-2020

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from ctypes import addressof

from .binding import word_bytes, uword_max


class Memory:
    '''
    A writable byte- or word-addressed view of a block of memory.

     - buffer - a value returned by ctypes.create_string_buffer - the memory.
     - element_size - int - the number of bytes read/written at a time.
     - view - the underlying memoryview.

    Memory addresses are specified in bytes. Only addresses that are multiples
    of `element_size` are valid.

    Memory address slices' `start` and `stop` fields must be valid addresses.
    The `step` field must be `None` or `element_size`; either will be treated as
    `element_size`, i.e. only the valid addresses will be accessed.

    `len()` gives the number of elements.
    '''
    def __init__(self, buffer, element_size=1):
        self.buffer = buffer
        assert element_size in (1, word_bytes)
        self.element_size = element_size
        self.view = memoryview(self.buffer).cast('B')
        if element_size == word_bytes:
            self.view = self.view.cast('N')

    @property
    def addr(self):
        'The base address of the memory.'
        return addressof(self.buffer)

    def __len__(self):
        return len(self.view)

    def _address_to_index(self, addr):
        if isinstance(addr, slice):
            assert addr.step in (None, self.element_size)
            return slice(
                self._address_to_index(addr.start),
                self._address_to_index(addr.stop),
            )
        else:
            assert addr % self.element_size == 0
            return (addr - self.addr) // self.element_size

    def __getitem__(self, addr):
        return self.view.__getitem__(self._address_to_index(addr))

    def __setitem__(self, addr, value):
        if not isinstance(value, bytes):
            value = int(value) & uword_max
        self.view.__setitem__(self._address_to_index(addr), value)
