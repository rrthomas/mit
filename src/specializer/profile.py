'''
Library for reading and processing profile files.

(c) 2019-2020 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import json, random

from spec import Instruction
from path import Path


class State:
    '''
    Represents a state of the interpreter that we profiled.
     - index - the index of this State in `profile`.
     - path - Path - the canonical path to this State.
     - guess - Instruction - the guessed continuation.
     - correct_state - int - the index of the State to jump to if `guess` is
       correct, or `-1` for the fallback state.
     - wrong_state - int - the index of the State to jump to if `guess` is
       wrong, or `-1` for the fallback state.
     - correct_count - the number of times `guess` was correct.
     - wrong_count - the number of times `guess` was wrong.
     - total_count - `correct_count + wrong_count`.
    '''
    def __init__(
        self,
        index,
        path,
        guess,
        correct_state,
        wrong_state,
        correct_count,
        wrong_count,
    ):
        assert isinstance(path, Path)
        assert isinstance(guess, Instruction)
        self.index = index
        self.path = path
        self.guess = guess
        self.correct_state = correct_state
        self.wrong_state = wrong_state
        self.correct_count = correct_count
        self.wrong_count = wrong_count
        self.total_count = correct_count + wrong_count

    def __repr__(self):
        return 'State({}, {!r}, {!r}, {}, {}, {}, {})'.format(
            self.index,
            self.path,
            self.guess,
            self.correct_state,
            self.wrong_state,
            self.correct_count,
            self.wrong_count,
        )


def load(filename):
    '''
    Load a profile data file, and initialize `profile` and `ROOT_STATE`.
    '''
    global profile, ROOT_STATE
    with open(filename) as h:
        profile = [
            State(
                index,
                Path(tuple(
                    Instruction[name]
                    for name in profile['path'].split()
                )),
                Instruction[profile['guess']],
                profile['correct_state'],
                profile['wrong_state'],
                profile['correct_count'],
                profile['wrong_count'],
            )
            for index, profile in enumerate(json.load(h))
        ]
    ROOT_STATE = get_state(0) if len(profile) > 0 else None


def get_state(index):
    if index == -1:
        return None
    else:
        return profile[index]


def random_trace():
    profile_state = ROOT_STATE
    while True:
        if profile_state is None:
            # Fallback interpreter is modelled as uniformly random.
            yield random.choice(list(Instruction))
            profile_state = ROOT_STATE
        elif random.randrange(profile_state.total_count) < profile_state.correct_count:
            # Model a correct guess.
            yield profile_state.guess
            profile_state = get_state(profile_state.correct_state)
        else:
            # Model a wrong guess.
            profile_state = get_state(profile_state.wrong_state)


def counts():
    '''
    Returns a dict from Instruction to count.
    '''
    # Read trace, computing opcode counts
    counts = {instruction: 0 for instruction in Instruction}
    for state in profile:
        counts[state.guess] += state.correct_count
    return counts
