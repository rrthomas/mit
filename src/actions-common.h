#define RAISE_NON_ZERO(code)                \
    do {                                    \
        int maybe_error = (code);           \
        if ((maybe_error) != 0)             \
            RAISE(maybe_error);             \
    } while (0)
