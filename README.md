# NAS official localization input

This branch contains only the verified official Chinese localization input for
this repository's existing data-refresh pipeline. It is not a website branch.

Resolve this branch to a commit first, then read source.json and global.ini.gz
from that same commit. Verify the decompressed byte length and SHA-256 before
using it. Version evidence is major/minor only, not an exact LIVE build.

The NAS publisher reads the source directory without modifying it. Unchanged
content produces no commit. A failed read, validation or push preserves the
last good published input. Website refresh and deployment remain in the main
branch's existing workflow, including compatibility and quality checks.
