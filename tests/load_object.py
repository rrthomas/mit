# Test load_object().
#
# (c) Reuben Thomas 1995-2019
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

from smite import *
VM = State()
VM.globalize(globals())


def try_load(file):
    print("try_load " + file)
    try:
        load(file)
        ret = 0
    except State.LoadError as e:
        ret = e.args[1]
    print("load_object(\"{}\", 0) returns {}".format(file, ret), end='')
    return ret

def obj_name(prefix, file, use_endism, word_size=None):
    if use_endism:
        endism = "-{}".format("le" if ENDISM.get() == 0 else "be")
    suffix = "-{}".format(word_size) if word_size else ""
    name = "{}/{}{}{}".format(prefix, file, endism if use_endism else "", suffix)
    return name

src_dir = os.environ['srcdir']
build_dir = os.environ['builddir']


bad_files = ["badobj1", "badobj2", "badobj3", "badobj4"]
error_code = [-2, -2, -1, -3]
for i in range(len(bad_files)):
    s = obj_name(src_dir, bad_files[i], False, word_size)
    res = try_load(s)
    print(" should be {}".format(error_code[i]))
    if res != error_code[i]:
        print("Error in load_object() tests: file {}".format(bad_files[i]))
        sys.exit(1)


good_files = ["testobj1", "testobj2"]
for good_file in good_files:
    s = obj_name(src_dir, good_file, True, word_size)
    res = try_load(s)
    print(" should be {}".format(0))
    print("Word 0 of memory is {:#x}; should be 0x01020304".format(M_word[0]))
    if M_word[0] != 0x1020304:
        print("Error in load_object() tests: file {}".format(good_file))
        sys.exit(1)
    if res != 0:
        print("Error in load_object() tests: file {}".format(good_file))
        sys.exit(1)


# Generate test object file
number(-257)
number(12345678)
magic_number = 42
number(magic_number)
action(HALT)
save("numbers.obj")

number_files = ["numbers.obj"]
# FIXME: Generate a single list of numbers for here, numbers.txt and numbers.c
correct = [
    [-257, 12345678],
]
for i in range(len(number_files)):
    s = obj_name(build_dir, number_files[i], False)
    res = try_load(s)
    print(" should be {}".format(0))
    if res != 0:
        print("Error in load_object() tests: file {}".format(number_files[i]))
        sys.exit(1)
    if run() != magic_number:
        print("Error in load_object() tests: file {}".format(number_files[i]))
        sys.exit(1)
    print("Correct stack: {}".format(correct[i]))
    if str(correct[i]) != str(S):
        print("Error in arithmetic tests: PC = {}".format(PC))
        sys.exit(1)

os.remove("numbers.obj")


# Check we get an error trying to load an object file of the wrong
# WORD_SIZE.
assert(word_size == 4 or word_size == 8)
wrong_word_size = 8 if word_size == 4 else 4
s = obj_name(src_dir, good_files[0], True, wrong_word_size)
res = try_load(s)
incorrect_word_size_res = -5
print(" should be {}".format(incorrect_word_size_res))
if res != incorrect_word_size_res:
    print("Error in load_object() tests: file {}".format(good_files[0]))
    sys.exit(1)

print("load_object() tests ran OK")
