import sys

def run_test(name, state, correct):
    for i, stack in enumerate(correct):
        state.step()
        print("Data stack: {}".format(state.S))
        print("Correct stack: {}\n".format(stack))
        if str(stack) != str(state.S):
            print("Error in {} tests: PC = {:#x}".format(name, state.registers["PC"].get()))
            sys.exit(1)
        print("I = {}".format(state.disassemble_pc()))

    print("{} tests ran OK".format(name.upper()))
