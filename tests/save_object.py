# Test save_object().
#
# (c) SMite authors 1995-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
size = 256
VM = State(size)
VM.globalize(globals())


# Test data
M_word[0] = 0x01020304
M_word[word_bytes] = 0x05060708

# Test results
addr = [(size + 1) * word_bytes, 0, 0]
length = [16, 3000, 16]
correct = [-2, -2, 0]

# Test
def try_save(file, address, length):
    try:
        save(file, address, length)
        ret = 0
    except ErrorCode as e:
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

ret = load("saveobj", 4 * word_bytes)
os.remove("saveobj")

for i in range(4):
    old = M_word[i * word_bytes]
    new = M_word[(i + 4) * word_bytes]
    print("Word {} of memory is {}; should be {}".format(i, new, old))
    if new != old:
        print("Error in save_object() tests: loaded file does not match data saved")
        sys.exit(1)

print("save_object() tests ran OK")
