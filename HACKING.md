# Mit: Information for maintainers

See `README.md` for instructions on building from git.

## Managing the profile

See `src/specializer/specializer.am`.

## Testing

ASAN (Address Sanitizer) is recommended for finding various classes of bug.
See `.appveyor.yml` for sample settings to configure GCC to use ASAN. Note
the use of `PY_LOG_ENV` to set `LD_PRELOAD` and `PYTHONMALLOC` for the
tests. This avoids needing to set these variables globally.

The benchmarks (`make bench`) are timed by default with `time`. To use
another program, for example `operf`, either run `configure` setting
`TIME=/path/to/program` (note: the program must be a full path, and
command-line options cannot be supplied), or set it on the command line to
make; for example:

```
make check TIME="operf --events INST_RETIRED:100000"
```

## Using Docker

To run a non-native version of mit; for example, to run 32-bit Mit on a
64-bit machine, which is currently necessary to run pForth, Docker is
recommended. A `Dockerfile` is provided to run 32-bit Mit.

See `.appveyor.yml` for the recipe used to test Mit on arches unsupported by Travis.

To develop Mit, it's more convenient to use a bind mount to share a git
checkout between the host system (editor etc.) and Docker container, thus:

```
docker build --build-arg BASE_IMAGE=i386/ubuntu --tag test - < Dockerfile
docker run --interactive --privileged --tty --mount type=bind,source="$(pwd)",target=/work test /bin/bash
```

## Making a release

To make a release, run `make release` in the top-level directory. This
requires that all changes have been pushed, and needs the
[woger](https://github.com/rrthomas/woger/) utility.
