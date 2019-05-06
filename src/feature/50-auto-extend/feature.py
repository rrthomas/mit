Option('no-auto-extend',
       'do not automatically extend stack or memory',
       top_level_code='''\
static mit_UWORD round_up(mit_UWORD n, mit_UWORD multiple)
{
    return (n - 1) - (n - 1) % multiple + multiple;
}
''',
       init_code='''\
// getpagesize() is obsolete, but gnulib provides it, and
// sysconf(_SC_PAGESIZE) does not work on some platforms.
mit_UWORD page_size = getpagesize();
mit_UWORD memory_size = WORD_BYTES == 2 ? 0x1000U : 0x100000U;
mit_UWORD stack_size = WORD_BYTES == 2 ? 1024U : 16384U;
''',
       exception_handler='''\
case 2:
    // Grow stack on demand
    if (S->BAD >= S->stack_size &&
        S->BAD < mit_uword_max - S->stack_size &&
        (res = mit_realloc_stack(S, round_up(S->stack_size + S->BAD, page_size))) == 0)
        continue;
    break;
case 5:
case 6:
    // Grow memory on demand
    if (S->BAD >= S->memory_size &&
        (res = mit_realloc_memory(S, round_up(S->BAD, page_size))) == 0)
        continue;
    break;''')
