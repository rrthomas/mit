'''
Library for reading and processing profile files.

(c) 2019-2020 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import json, random
from dataclasses import dataclass

from specializer_spec import Instruction
from path import Path


@dataclass
class Label:
    '''
    Represents a label of the interpreter that we profiled.
     - index - int - the index of this Label in `profile`.
     - path - Path - the canonical path to this Label.
     - guess - Instruction - the guessed continuation.
     - if_correct - int - the index of the Label to jump to if `guess` is
       correct, or `-1` for the fallback label.
     - if_wrong - int - the index of the Label to jump to if `guess` is
       wrong, or `-1` for the fallback label.
     - correct_count - int - the number of times `guess` was correct.
     - wrong_count - int - the number of times `guess` was wrong.
     - total_count - int - `correct_count + wrong_count`.
    '''
    index: int
    path: Path
    guess: Instruction
    if_correct: int
    if_wrong: int
    correct_count: int
    wrong_count: int

    def __post_init__(self):
        self.total_count = self.correct_count + self.wrong_count


def load(filename):
    '''
    Load a profile data file, and initialize `profile` and `ROOT_LABEL`.
    '''
    global profile, ROOT_LABEL
    with open(filename) as h:
        profile = [
            Label(
                index,
                Path(tuple(
                    Instruction[name]
                    for name in profile['path'].split()
                )),
                Instruction[profile['guess']],
                profile['if_correct'],
                profile['if_wrong'],
                profile['correct_count'],
                profile['wrong_count'],
            )
            for index, profile in enumerate(json.load(h))
        ]
    ROOT_LABEL = get_label(0) if len(profile) > 0 else None


def get_label(index):
    if index == -1:
        return None
    else:
        return profile[index]


def random_trace():
    label = ROOT_LABEL
    while True:
        if label is None:
            # Fallback interpreter is modelled as uniformly random.
            yield random.choice(list(Instruction))
            label = ROOT_LABEL
        elif random.randrange(label.total_count) < label.correct_count:
            # Model a correct guess.
            yield label.guess
            label = get_label(label.if_correct)
        else:
            # Model a wrong guess.
            label = get_label(label.if_wrong)


# Analysis functions.

def instruction_counts():
    '''
    Returns a dict from Instruction to count.
    '''
    # Read trace, computing opcode counts
    counts = {instruction: 0 for instruction in Instruction}
    for label in profile:
        counts[label.guess] += label.correct_count
    return counts

def total_instructions():
    return sum(count for _, count in instruction_counts().items())

def label_counts():
    total_count = sum(label.total_count for label in profile)

    fallback_count = sum(
        label.correct_count
        for label in profile
        if label.if_correct == -1
    ) + sum (
        label.wrong_count
        for label in profile
        if label.if_wrong == -1
    )

    return total_count, fallback_count
