# Artichoke Growth
Buckets like leaves tend to grow.

## Scope
This little helper provides an index as proxy to a hash bucket store.

Periodically polling the bucket store on the file system provides a history of writes and deletes.

Interesting attributes stored in the procy are:
* name of the bucket
* size of the blob in bytes
* date of creation
* one or more hashes

Index entries for buckets entering are stored in addition in the added index store.
Index entries for Buckets that are not present on file system anymore are moved to the graveyard and act as tombstones.
