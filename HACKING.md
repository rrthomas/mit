# Mit: Information for maintainers

See `README.md` for instructions on building from git.

## Testing

ASAN (Address Sanitizer) is recommended for finding various classes of bug.
See `.travis.yml` for sample settings to configure GCC to use ASAN. Note
the use of `PY_LOG_ENV` to set `LD_PRELOAD` and `PYTHONMALLOC` for the
tests. This avoids needing to set these variables globally.

The benchmarks (`make bench`) are timed by default with `time`. To use
another program, for example `oprofile`, either run `configure` setting
`TIME=/path/to/program` (note: the program must be a full path, and command-line options cannot be supplied), or set it on the command line to the actual test; for example:

```
make check TIME="operf --events INST_RETIRED:100000,LLC_MISSES:100000,LLC_REFS:100000"
```

## Making a release

To make a release, run `make release` in the top-level directory. This
requires that all changes have been pushed, and needs the
[woger](https://github.com/rrthomas/woger/) utility.
