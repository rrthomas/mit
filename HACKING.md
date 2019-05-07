# Mit: Information for maintainers

See `README.md` for instructions on building from git.

## Testing

ASAN (Address Sanitizer) is recommended for finding various classes of bug.
See `.appveyor.yml` for sample settings to configure GCC to use ASAN. Note
the use of `PY_LOG_ENV` to set `LD_PRELOAD` and `PYTHONMALLOC` for the
tests. This avoids needing to set these variables globally.

## Making a release

To make a release, run `make release` in the top-level directory. This
requires that all changes have been pushed, and needs the
[woger](https://github.com/rrthomas/woger/) utility.
