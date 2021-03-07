#A python-artichoke_growth
Document some binary repository management storage.

**Implementation Note**: File type analysis currently relies on the file command.  
Thus, this package is only useful on systems that provide the file command.

## Status
Experimental.

## Example Use of Dockerized application

Build the local docker image within this directory:

```bash
$ docker build --tag "${USER}/artichoke-growth" .
```

Provide host filesystem access to the internal container user (action) by eg.
```bash
$ mkdir -p store/proxy && chmod -R 777 store
```
or some more intelligent (secure) means.

Bootstrap the proxy index by adding a dummy entry that will sort before factual entries:
```bash
$ touch store/proxy/proxy-0.csv && xz -9e store/proxy/proxy-0.csv
```

Run first on the test data (and notice how 21 entries do enter the index:)
```bash
$ docker run --rm --mount type=bind,source="$(pwd)"/,target=/app \
  -e BRM_FS_ROOT=/app/tests/fixtures/prefix_store/sha256 \
  -e BRM_PROXY_DB=AUTO \
  "${USER}/artichoke-growth"
Read 0 from AUTO artifacts below /app/tests/fixtures/prefix_store/sha256
Job visiting file store starts at 2021-03-07 13:34:37
Entered 21 entries / 4634 bytes at store/enter/added-20210307T133437Z.csv
Ignored 0 entries / 0 bytes for hashing
Kept 21 entries / 4634 bytes at store/proxy/proxy-20210307T133437Z.csv
Removed 0 entries / 0 bytes at store/tombs/gone-20210307T133437Z.csv
Total size in added files is 0.00 Gigabytes (4634 bytes)
Job visiting file store finished at 2021-03-07 13:34:37
$
```

Next run will show no etnering entries (keeping all 21 and removing none):
```bash
$ docker run --rm --mount type=bind,source="$(pwd)"/,target=/app \
  -e BRM_FS_ROOT=/app/tests/fixtures/prefix_store/sha256 \
  -e BRM_PROXY_DB=AUTO \
  "${USER}/artichoke-growth"
Read 21 from AUTO artifacts below /app/tests/fixtures/prefix_store/sha256
Job visiting file store starts at 2021-03-07 13:35:41
Entered 0 entries / 0 bytes at store/enter/added-20210307T133541Z.csv
Ignored 21 entries / 4634 bytes for hashing
Kept 21 entries / 4634 bytes at store/proxy/proxy-20210307T133541Z.csv
Removed 0 entries / 0 bytes at store/tombs/gone-20210307T133541Z.csv
Total size in added files is 0.00 Gigabytes (0 bytes)
Job visiting file store finished at 2021-03-07 13:35:41
$
```

Clean up after test (or ensure the store directory tree is in good shape
when runnning again - i.e. permissions and present files are as expected
and accessible by the container user).

**Note**: The name of the default branch is `default`.
