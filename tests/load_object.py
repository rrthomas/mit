# Test load_object().
#
# (c) SMite authors 1995-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
VM = State()
VM.globalize(globals())


def try_load(file):
    try:
        load(file)
        ret = 0
    except ErrorCode as e:
        ret = e.args[0]
    print("load_object(\"{}\", 0) returns {}".format(file, ret), end='')
    return ret

def obj_name(prefix, file, word_bytes=None, use_endism=True):
    endism = "-{}".format("le" if ENDISM.get() == 0 else "be")
    suffix = "-{}".format(word_bytes) if word_bytes else ""
    name = "{}/{}{}{}".format(prefix, file, endism if use_endism else "", suffix)
    return name

src_dir = os.environ['srcdir']
build_dir = os.environ['builddir']


bad_files = ["badobj1", "badobj2", "badobj3", "badobj4"]
error_code = [-2, -2, -4, -2]
for i, bad_file in enumerate(bad_files):
    s = obj_name(src_dir, bad_file, word_bytes)
    res = try_load(s)
    print(" should be {}".format(error_code[i]))
    if res != error_code[i]:
        print("Error in load_object() tests: file {}".format(bad_file))
        sys.exit(1)


good_files = ["testobj1", "testobj2"]
for good_file in good_files:
    s = obj_name(src_dir, good_file, word_bytes)
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
number_file = "numbers.obj"
correct = [-128, 12345678]
for n in correct:
    lit(n)
ass(HALT)
save(number_file, length=assembler.label())

s = obj_name(build_dir, number_file, use_endism=False)
res = try_load(s)
print(" should be {}".format(0))
if res != 0:
    print("Error in load_object() tests: file {}".format(number_file))
    sys.exit(1)
try:
    run()
except ErrorCode:
    print("Error in load_object() tests: file {}".format(number_file))
    sys.exit(1)
print("Data stack: {}".format(S))
print("Correct stack: {}".format(correct))
if str(correct) != str(S):
    print("Error in load_object() tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)

os.remove(number_file)


# Check we get an error trying to load an object file of the wrong
# WORD_BYTES.
assert(word_bytes == 4 or word_bytes == 8)
wrong_word_bytes = 8 if word_bytes == 4 else 4
s = obj_name(src_dir, good_files[0], wrong_word_bytes, use_endism=True)
res = try_load(s)
incorrect_word_bytes_res = -3
print(" should be {}".format(incorrect_word_bytes_res))
if res != incorrect_word_bytes_res:
    print("Error in load_object() tests: file {}".format(good_files[0]))
    sys.exit(1)

print("load_object() tests ran OK")
