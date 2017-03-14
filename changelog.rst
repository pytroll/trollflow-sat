Changelog
=========

v0.4.0 (2017-03-14)
-------------------

- Update changelog. [Panu Lahtinen]

- Bump version: 0.3.0 → 0.4.0. [Panu Lahtinen]

- Merge branch 'master' into develop. [Panu Lahtinen]

- Add list of used instruments. [Panu Lahtinen]

- Fix getting filenames from collected datasets. [Panu Lahtinen]

- Fix checking what type of collection is used. [Panu Lahtinen]

- Fix reading filenames from a collection. [Panu Lahtinen]

- Add check for collection id, catch some errors when loading data.
  [Panu Lahtinen]

- Fix formatting of log message. [Panu Lahtinen]

- Fix typo. [Panu Lahtinen]

- Get configuration for single product. [Panu Lahtinen]

- Fix incorrect logic. [Panu Lahtinen]

- Add missing argument. [Panu Lahtinen]

- Add a possibility to limit production based on Sun zenith angle. [Panu
  Lahtinen]

- Fix syntax error. [Panu Lahtinen]

- Catch NoSectionError when trying to create composites. [Panu Lahtinen]

- Release previous lock when skipping data, add logging. [Panu Lahtinen]

- Add log message listing used files. [Panu Lahtinen]

- Check used instruments, give data filenames as arguments to load()
  [Panu Lahtinen]

v0.3.0 (2017-03-07)
-------------------

- Update changelog. [Panu Lahtinen]

- Bump version: 0.2.0 → 0.3.0. [Panu Lahtinen]

- Compose the topic to include {area_id} (if configured) [Panu Lahtinen]

v0.2.0 (2017-02-28)
-------------------

- Update changelog. [Panu Lahtinen]

- Bump version: 0.1.0 → 0.2.0. [Panu Lahtinen]

- Add missing calls to release_lock() [Panu Lahtinen]

- Ensure non-unicode filename (I'm looking at you, gdal) [Panu Lahtinen]

- Fix dictionary key naming "areaname" to "area_id" [Panu Lahtinen]

- Ensure downstream workers have finished before releasing upstream
  locks. [Panu Lahtinen]

- Add use_lock for daemons to config templates. [Panu Lahtinen]

- Add "use_lock" kwarg to daemons, lock only if set to True. [Panu
  Lahtinen]

- Adjust lock handling order, use trollflow.utils for lock
  acquire/release. [Panu Lahtinen]

- Move lock acquire/release to trollflow.utils. [Panu Lahtinen]

- Fix locking, add data reload, add satproj. [Panu Lahtinen]

  - use RLock instead of Lock
  - fix incorrectly understood lock acquire/release
  - reload data for each area group
  - make it possible to save data in satellite projection by
    defining areaname as "satproj"
  - check lock usage as first step in invoke()
  - if using locking, wait 1 sec after releasing local lock


- Add config examples for locking. [Panu Lahtinen]

- Remove unnecessary "content" dictionaries. [Panu Lahtinen]

- Delete incomplete plugin. [Panu Lahtinen]

- Fix locking. [Panu Lahtinen]

- Add locking. [Panu Lahtinen]

- Add queue.task_done() [Panu Lahtinen]

- Remove incomplete components. [Panu Lahtinen]

- PEP8. [Panu Lahtinen]

- PEP8. [Panu Lahtinen]

- PEP8. [Panu Lahtinen]

- PEP8. [Panu Lahtinen]

- Fix package name for coverage. [Panu Lahtinen]

- Update "format" section. [Panu Lahtinen]

- Fix intendation. [Panu Lahtinen]

- Add config option for use_threading. [Panu Lahtinen]

- Fix class names, change items under "config" to dicts. [Panu Lahtinen]

- Adjust log messages, set output queues to None by default. [Panu
  Lahtinen]

- Adjust log messages. [Panu Lahtinen]

- Change default argument of nameservers from [] to None and handle the
  change. [Panu Lahtinen]

- Fix unittest so that they use ordered_load and the new format
  structure. [Panu Lahtinen]

- Return list instead of a set. [Panu Lahtinen]

- Remove hardcoded loading of composite "overview" [Panu Lahtinen]

- Fix writer indexing. [Panu Lahtinen]

- Make it possible to define specific writers for satpy. [Panu Lahtinen]

- Fix function name. [Panu Lahtinen]

- Add handling for dataset messages and placeholder for collections.
  [Panu Lahtinen]

- Add log config example. [Panu Lahtinen]

- Add tests for time name adjustments. [Panu Lahtinen]

- Fix time name adjustment, ignore time tags having 'proc' and 'end' in
  them. [Panu Lahtinen]

- Add plugins using satpy instead of mpop, add example YAML configs.
  [Panu Lahtinen]

- Add logger, figure out time name used in filename pattern and metadata
  and use them to update pattern if necessary. [Panu Lahtinen]

- Change composites from list to dict. [Panu Lahtinen]

v0.1.0 (2016-11-22)
-------------------

- Update changelog. [Panu Lahtinen]

- Bump version: 0.0.1 → 0.1.0. [Panu Lahtinen]

- Fix path to version file. [Panu Lahtinen]

- Adjust install requirements. [Panu Lahtinen]

- Adjust to use listener from posttroll. [Panu Lahtinen]

- Moved to posttroll. [Panu Lahtinen]

- Update TODO. [Panu Lahtinen]

- Add unittests for trollflow_sat.utils.create_fnames() [Panu Lahtinen]

- Clarify naming, fix incorrect dict structure, adjust logging. [Panu
  Lahtinen]

- Ensure absolute path for URI. [Panu Lahtinen]

- Fix import, adapt to YAML config patterns. [Panu Lahtinen]

- Fix import, adapt to YAML config patterns. [Panu Lahtinen]

- Fix import, clarify naming. [Panu Lahtinen]

- Fix syntax, change out_dir to output_dir, add log warning if no output
  directory is given. [Panu Lahtinen]

- Clarify structure, add missing quotes around file patterns. [Panu
  Lahtinen]

- Fix package name. [Panu Lahtinen]

- Rename package. [Panu Lahtinen]

- Set built-in default for output format. [Panu Lahtinen]

- Remove check for empty file pattern, as default is used if all else
  fails, give warning if this happens. [Panu Lahtinen]

- Use common settings if more specific settings are not given. [Panu
  Lahtinen]

- Add .eggs/ to ignored files. [Panu Lahtinen]

- Adjust requirements. [Panu Lahtinen]

- Add unittests. [Panu Lahtinen]

- Example product confgi in YAML. [Panu Lahtinen]

- Add todo-list. [Panu Lahtinen]

- Get area specific resampling search radius if available. [Panu
  Lahtinen]

- Take output directory name from config. [Panu Lahtinen]

- Adjust to YAML product config, simplify what is passed to output
  queue. [Panu Lahtinen]

- Add example configs, adapt to new package name. [Panu Lahtinen]

- Copy plugins from trollduction@feature_trollflow. [Panu Lahtinen]

- Add basic files. [Panu Lahtinen]

- Add placeholder for tests. [Panu Lahtinen]

- Initial commit. [Panu Lahtinen]


