# SMite: Information for maintainers

See `README.md` for instructions on building from git.

## Testing

ASAN (Address Sanitizer) is recommended for finding various classes of bug. See `.travis.yml` for sample settings to configure GCC to use ASAN. Note the use of `PY_LOG_ENV` to set `LD_PRELOAD` for the tests. This avoids `LD_PRELOAD` being set generally, which can cause problems.

## Making a release

To make a release, run `make release` in the top-level directory. This requires that all changes have been pushed, and needs the [woger](https://github.com/rrthomas/woger/) utility.
