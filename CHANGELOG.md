v0.1.0 (in development)
-----------------------
- Add more logging messages
- Changed default version formats to something that doesn't use
  `{next_version}`
- "basic" `tag2version` method:
    - If `regex` is given and it does not contain a group named "`version`,"
      the entire text matched by the regex will be used as the version
    - Added a `require-match` parameter for erroring if the regex does not
      match
- "basic" `write` method: `encoding` now defaults to UTF-8
- New `next-version` methods: `"minor-release"`, `"smallest-release"`, and
  `"null`"
- Replaced `entry-points` dependency with `importlib-metadata`
- Added `tool.versioningit.default-version` for setting the version to use if
  an error occurs

v0.1.0a1 (2021-07-05)
---------------------
Alpha release
