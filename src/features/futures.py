'''
A tool for optimizing decision trees.

Copyright (c) 2018-2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import textwrap

from mit_core.vm_data import Instruction

class Future:
    '''
    Represents a node of a tree of possible futures. The futures are
    distinguished by what Instructions we execute.
     - probability - float - the probability that this Future occurs (including
       the probabilities of `children`).
     - children - {Instruction: Future} - Subtrees representing the
       possible futures starting with each Instruction.
    Probabilities need not be normalized.
    '''
    def __init__(self, probability, children):
        assert type(probability) is float, probability
        for instruction, child in children.items():
            assert isinstance(instruction, Instruction)
            assert isinstance(child, Future)
        self.probability = probability
        self.children = children

    def __repr__(self):
        return 'Future(probability={}, children={{{}\n}})'.format(
            self.probability,
            textwrap.indent(''.join(
                '\n{}: {}'.format(instruction.name, repr(child))
                for instruction, child in self.children.items()
            ), '  ')
        )

    def most_probable_child(self):
        '''
        Returns the Instruction leading to the most probable child,
        or `None` if there are no children.
        '''
        best, best_probability = None, 0.0
        for instruction, child in self.children.items():
            if child.probability >= best_probability:
                best, best_probability = instruction, child.probability
        return best

    def guess(self):
        '''
        Picks the most profitable Future to guess.
        Returns it as a list of Instructions.
        If the guess is wrong, call `eliminate(guess)`, and try again.
        '''
        path = []
        node = self
        while node.children:
            instruction = node.most_probable_child()
            if instruction is None:
                # We have no other options.
                break
            child = node.children[instruction]
            if node.probability + child.probability < self.probability:
                # Guess `node` first, and if correct, `child` later.
                break
            # We prefer to guess `child` first, and if wrong, `node` later.
            # Guessing a descendent of `child` might be even better, so loop.
            path.append(instruction)
            node = child
        return path

    def eliminate(self, path):
        '''
        Deletes the specified node, and subtracts its probability from that of
        all of its ancestors.
         - path - iterable of Instructions. Must be non-empty.
        '''
        nodes = []
        node = self
        for instruction in path:
            nodes.append(node)
            node = node.children[instruction]
        probability = node.probability
        del nodes[-1].children[instruction]
        for node in nodes:
            node.probability -= probability

