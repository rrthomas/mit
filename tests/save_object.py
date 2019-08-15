# Test save_object().
#
# (c) Mit authors 1995-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit import *
memory_bytes = 256 * word_bytes
VM = State(memory_bytes)


# Test data
VM.M_word[0] = 0x01020304
VM.M_word[word_bytes] = 0x05060708

# Test results
addr = [memory_bytes + word_bytes, 0, 0]
length = [32, 5000, 32]
correct = [-2, -2, 0]

# Test
def try_save(file, address, length):
    try:
        VM.save(file, address, length)
        ret = 0
    except VMError as e:
        ret = e.args[0]
    print("save_object(\"{}\", {}, {}) returns {}".format(file, address, length, ret), end='')
    return ret

for i in range(3):
    res = try_save("saveobj", addr[i], length[i])
    if i != 2:
      os.remove("saveobj")
    print(" should be {}".format(correct[i]))
    if res != correct[i]:
        print("Error in save_object() test {}".format(i + 1))
        sys.exit(1)

ret = VM.load("saveobj", 4 * word_bytes)
os.remove("saveobj")

for i in range(4):
    old = VM.M_word[i * word_bytes]
    new = VM.M_word[(i + 4) * word_bytes]
    print("Word {} of memory is {}; should be {}".format(i, new, old))
    if new != old:
        print("Error in save_object() tests: loaded file does not match data saved")
        sys.exit(1)

print("save_object() tests ran OK")
