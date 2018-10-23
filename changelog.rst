Changelog
=========


v0.11.1 (2018-10-23)
--------------------
- Update changelog. [Panu Lahtinen]
- Bump version: 0.11.0 → 0.11.1. [Panu Lahtinen]
- Merge pull request #34 from pytroll/bugfix-pattern-time-name. [Panu
  Lahtinen]

  Use new public functions from trollsift to get the pattern parts
- Use new public functions from trollsift to get the pattern parts.
  [Panu Lahtinen]
- Merge pull request #33 from pytroll/feature-save-overviews. [Panu
  Lahtinen]

  Embed overviews to saved images
- Move add_overviews() to trollflow_sat.utils. [Panu Lahtinen]
- Add unittests for overview addition. [Panu Lahtinen]
- Return if import fails. [Panu Lahtinen]
- Fix reading filenames from messages, add docstring to add_overviews()
  [Panu Lahtinen]
- Catch exception raised by unsupported files. [Panu Lahtinen]
- Use context manager to handle file opening. [Panu Lahtinen]
- Add a possibility to embed reduced sized images "overviews" [Panu
  Lahtinen]


v0.11.0 (2018-10-09)
--------------------
- Update changelog. [Panu Lahtinen]
- Bump version: 0.10.0 → 0.11.0. [Panu Lahtinen]
- Merge pull request #30 from pytroll/develop. [Panu Lahtinen]

  Add Python 3 compatibility, drop mpop support
- Pass save settings directly as kwargs to save_datasets() [Panu
  Lahtinen]
- Change filename_pattern kwarg to filename. [Panu Lahtinen]
- Add log message if instrument alias is used. [Panu Lahtinen]
- Add aliases to translate sensor name in message to SatPy naming. [Panu
  Lahtinen]
- Fix test for queue size. [Panu Lahtinen]
- Adjust tests for the fixed area-by-area processing. [Panu Lahtinen]
- Fix bug that resulted in processing each area several times. [Panu
  Lahtinen]
- Add config where process_by_area is False. [Panu Lahtinen]
- Move process_by_area from flow config to product config. [Panu
  Lahtinen]
- Add six to requirements. [Panu Lahtinen]
- Update install and test requirements. [Panu Lahtinen]
- Add more unit tests for utility functions. [Panu Lahtinen]
- Remove unnecessary line-split. [Panu Lahtinen]
- Remove unnecessary try/except. [Panu Lahtinen]
- Update variable names. [Panu Lahtinen]
- Fix mocked function name. [Panu Lahtinen]
- Rename utility function. [Panu Lahtinen]
- Remove obsolete utility functions. [Panu Lahtinen]
- Use OrderedDicts, add MockDset class, handle needs for writer tests.
  [Panu Lahtinen]
- Add unit tests for satpy_writer. [Panu Lahtinen]
- Add satpy writer tests to test suite. [Panu Lahtinen]
- Ensure create_fnames() always returns two items. [Panu Lahtinen]
- Use ordered_load from trollflow to read YAML files. [Panu Lahtinen]
- Make sure there's a thread before doing a join() [Panu Lahtinen]
- Ensure save settings is a dictionary. [Panu Lahtinen]
- Delete written files in tearDown() [Panu Lahtinen]
- Add satpy_resampler tests to test suite. [Panu Lahtinen]
- Add unit tests for satpy_resampler. [Panu Lahtinen]
- Add two more product configs, add platform_name to basic config. [Panu
  Lahtinen]
- Add "common" section to product config. [Panu Lahtinen]
- Add resample() method. [Panu Lahtinen]
- Remove more references to non-xarray metadata dictionaries. [Panu
  Lahtinen]
- Remove try/excepts of obsolete non-xarray metadata structures. [Panu
  Lahtinen]
- Move MockScene to utils.py. [Panu Lahtinen]
- Move common things to utils.py. [Panu Lahtinen]
- Rename patched objects with better names. [Panu Lahtinen]
- Add satpy_compositor tests to test suite. [Panu Lahtinen]
- Fix mock import for Py2, remove calls to `assert_called_once()` [Panu
  Lahtinen]
- Add more satpy_compositor unit tests. [Panu Lahtinen]
- Handle readers better, ensure global_data instance is created. [Panu
  Lahtinen]
- Add tests for SceneLoader. [Panu Lahtinen]
- Add placeholders for satpy plugins. [Panu Lahtinen]
- Merge pull request #32 from pytroll/bugfix-urlparse. [Panu Lahtinen]

  Use urlparse to guarantee local path
- Fix urlparse import. [Panu Lahtinen]
- Use urlparse to guarantee local path. [Panu Lahtinen]
- Fix test due to changed default save format. [Panu Lahtinen]
- Merge pull request #31 from pytroll/feature-fill_value. [Panu
  Lahtinen]

  Better handling of save format settings
- Use default format setting if none is configured. [Panu Lahtinen]
- Refactor save format setting handling. [Panu Lahtinen]
- Read fill values from the product config. [Panu Lahtinen]
- Update dict used to compose message topic, again. [Panu Lahtinen]
- Merge branch 'develop' of https://github.com/pytroll/trollflow-sat
  into develop. [Panu Lahtinen]
- Merge pull request #29 from pytroll/feature-lazy. [Panu Lahtinen]

  Collect areas and composites together for processing
- Add more metadata that can be used in topic compose() [Panu Lahtinen]
- Reorder logging to reduce output. [Panu Lahtinen]
- Fix config example: do not use locking in compositor. [Panu Lahtinen]
- Fix lock release/acquisition in resampler. [Panu Lahtinen]
- Fix queue import, restructure and clean code. [Panu Lahtinen]
- Check if trollsched is available. [Panu Lahtinen]
- Add use_locks to instance attributes and set default to False. [Panu
  Lahtinen]
- Restructure and clean invoke() [Panu Lahtinen]
- Remove mention of external calibration. [Panu Lahtinen]
- Remove grouping by area. [Panu Lahtinen]
- Remove obsolete .info attribute access. [Panu Lahtinen]
- Update and clarify example configs. [Panu Lahtinen]
- Make it possible to process one area at a time. [Panu Lahtinen]
- Fix log message copy&paste typo. [Panu Lahtinen]
- Make config string unicode. [Panu Lahtinen]
- Update example configs for current SatPy version. [Panu Lahtinen]
- Collect all areas and composites together for optimized processing.
  [Panu Lahtinen]
- Use simple_image writer as default. [Panu Lahtinen]
- Merge pull request #28 from pytroll/feature-python3-support. [Panu
  Lahtinen]

  Python 3 compatibility
- Add Python 3 to Travis tests. [Panu Lahtinen]
- Use six to import queue. [Panu Lahtinen]
- Fix StringIO import, reflow long lines. [Panu Lahtinen]
- Cast dict.items() to tuple for Python 3 support. [Panu Lahtinen]
- Remove mpop and mipp from requirements. [Panu Lahtinen]
- Remove mpop plugins and example config files. [Panu Lahtinen]
- Remove mpop import. [Panu Lahtinen]
- Add _template to the filename. [Panu Lahtinen]
- Update dict used to compose message topic. [Panu Lahtinen]
- Merge pull request #26 from pytroll/feature-reader-config. [Panu
  Lahtinen]

  Optionally give readers in the flow configuration file
- Read readers to try from flow configuration file, update example
  config. [Panu Lahtinen]
- Merge pull request #24 from pytroll/feature-separate-extra-metadata.
  [Panu Lahtinen]

  Separate scene and additional information
- Use productname returned by utils.create_fnames() [Panu Lahtinen]
- Use the correct metadata dictionary for area_id. [Panu Lahtinen]
- Add area ID to scene attrs/info instead of external metadata. [Panu
  Lahtinen]
- Merge branch 'feature-separate-extra-metadata' of
  https://github.com/pytroll/trollflow-sat into feature-separate-extra-
  metadata. [Panu Lahtinen]
- Separate scene and additional information. [Panu Lahtinen]
- Separate scene and additional information. [Panu Lahtinen]
- Merge pull request #23 from pytroll/fix-fetch-collections. [Panu
  Lahtinen]

  Add support for fetching collections
- Bugfix filenames missing for collection. [Martin Raspaud]
- Support collections in compositor. [Martin Raspaud]
- Allow collections of simple files. [Martin Raspaud]
- Add support for fetching collections. [Martin Raspaud]
- Merge pull request #22 from ch-k/feature-satpywriter-complex-
  publishvars. [Panu Lahtinen]

  Complex expressions for SatpyWrite publish_vars
- Support for dpath expressions in publish_vars. [Christian Kliche]

  example:

  publish_vars:
      source_uri: "/dataset/*/uri"

  This creates a list of the original URIs and publishs it as source_uri.

- Complex expressions for SatpyWrite publish_vars. [Christian Kliche]

  It is now possible to use python expressions to forward more complex values:

  publish_vars:
      source_uri: "=[e.get('uri') for e in info['dataset']]"

  This creates a list of the original URIs and publishs it as source_uri.

  Conflicts:
  	examples/flow_processor_satpy.yaml_template
  	trollflow_sat/satpy_writer.py

- Comment out adaguc writer, add coverage_check config option. [Panu
  Lahtinen]
- Update changelog. [Panu Lahtinen]
- Bump version: 0.9.0 → 0.10.0. [Panu Lahtinen]
- Merge pull request #21 from pytroll/feature-ignore-message-items.
  [Panu Lahtinen]

  Add ignore_* functionnality for messages items
- Comment out ignore_ parameter in example workflow. [Martin Raspaud]
- Add ignore_* functionnality for messages items. [Martin Raspaud]
- Merge pull request #17 from pytroll/bugfix-xarray. [Panu Lahtinen]

  Fix compatibility with satpy/feature-xarray
- Merge branch 'develop' into bugfix-xarray. [Martin Raspaud]
- Add an option to completely skip coverage checking. [Panu Lahtinen]
- Merge pull request #16 from pytroll/bugfix-xarray. [Martin Raspaud]

  Fix compatibility with satpy/feature-xarray
- Merge pull request #15 from pytroll/develop. [Panu Lahtinen]

  Merge develop to master
- Fix satpy_resampler to support xarray. [Martin Raspaud]
- Fix compatibility with satpy/feature-xarray. [Martin Raspaud]
- Fix compatibility with satpy/feature-xarray. [Martin Raspaud]


v0.9.0 (2017-12-08)
-------------------
- Update changelog. [Panu Lahtinen]
- Bump version: 0.8.0 → 0.9.0. [Panu Lahtinen]
- Merge pull request #14 from pytroll/fix-saving-removed. [Panu
  Lahtinen]

  Avoid crashing when a composite has been removed
- Check that the configure composite is still available in the Scene.
  [Panu Lahtinen]
- Merge pull request #9 from pytroll/fix-delayed. [Panu Lahtinen]

  Fix processing of delayed datasets
- Merge branch 'fix-delayed' of https://github.com/pytroll/trollflow-sat
  into fix-delayed. [Panu Lahtinen]
- Merge branch 'fix-delayed' of https://github.com/pytroll/trollflow-sat
  into fix-delayed. [Panu Lahtinen]
- Add mask_area kwarg, add comments. [Panu Lahtinen]
- Expose "mask_area" kwarg. [Panu Lahtinen]
- Remove dataset IDs from the scene info as unecessary. [Panu Lahtinen]
- Fix handling of "delayed" datasets. [Panu Lahtinen]
- Fix topic of message for new files. [Panu Lahtinen]
- Add mask_area kwarg, add comments. [Panu Lahtinen]
- Expose "mask_area" kwarg. [Panu Lahtinen]
- Remove dataset IDs from the scene info as unecessary. [Panu Lahtinen]
- Fix handling of "delayed" datasets. [Panu Lahtinen]
- Fix topic of message for new files. [Panu Lahtinen]
- Remove dataset IDs from the scene info as unecessary. [Panu Lahtinen]
- Add mask_area kwarg, add comments. [Panu Lahtinen]
- Expose "mask_area" kwarg. [Panu Lahtinen]
- Remove dataset IDs from the scene info as unecessary. [Panu Lahtinen]
- Fix handling of "delayed" datasets. [Panu Lahtinen]
- Fix topic of message for new files. [Panu Lahtinen]
- Merge pull request #11 from pytroll/add-satpy-sun-check. [Panu
  Lahtinen]

  Add a check for Sun zenith angle for Satpy plugins
- Merge branch 'add-satpy-sun-check' of
  https://github.com/pytroll/trollflow-sat into add-satpy-sun-check.
  [Panu Lahtinen]
- Add check for solar zenith angles, don't create composites outside
  their range. [Panu Lahtinen]
- Add check for solar zenith angles, don't create composites outside
  their range. [Panu Lahtinen]
- Merge pull request #12 from pytroll/feature-satpy-coverage. [Panu
  Lahtinen]

  Add coverage calculations to SatPy plugins
- Merge branch 'feature-satpy-coverage' of
  https://github.com/pytroll/trollflow-sat into feature-satpy-coverage.
  [Panu Lahtinen]
- Fix typo: sensor -> 'sensor' [Panu Lahtinen]
- Fix call to Pass() with existing metadata. [Panu Lahtinen]
- Add coverage config item. [Panu Lahtinen]
- Add coverage check. [Panu Lahtinen]
- Move covers() to utils.py. [Panu Lahtinen]
- Fix typo: sensor -> 'sensor' [Panu Lahtinen]
- Fix call to Pass() with existing metadata. [Panu Lahtinen]
- Add coverage config item. [Panu Lahtinen]
- Add coverage check. [Panu Lahtinen]
- Move covers() to utils.py. [Panu Lahtinen]
- Merge branch 'develop' of https://github.com/pytroll/trollflow-sat
  into develop. [Panu Lahtinen]
- Fix area missing in some datasets for satpy_writer. [Martin Raspaud]
- Fix info -> attrs rename in satpy_writer. [Martin Raspaud]
- Merge branch 'develop' of https://github.com/pytroll/trollflow-sat
  into develop. [Panu Lahtinen]
- Fix .attrs compatibility in satpy resampler. [Martin Raspaud]
- Add .attrs to possible metadata holders for satpy scene. [Martin
  Raspaud]
- Remove metadata from Scene instantiation. [Martin Raspaud]
- Update changelog. [Panu Lahtinen]
- Merge pull request #6 from ch-k/feature-publish-vars-param. [Panu
  Lahtinen]

  Satpy writer parameter to specify published values
- Added sample to template. [Christian Kliche]
- Configuration option to publish everything. [Christian Kliche]

  Configuration of satpy_writer now supports "*" in parameter
  "publish_vars".

  Example 1:

  publish_vars: "*"

  Example 2:

  publish_vars:
    "*": ""
    super_param: gatherer_time

- Satpy writer parameter to specify published values. [Christian Kliche]

  By default writer publishes only a fixed set of variables
  in its posttroll message. If you want to forward attributes
  that were received from a previous processing stage, you
  can define a map called publish_vars. The keys denote variable
  names in the message to be published. The value defines the
  variable name in the received message.

  publish_vars:
    gatherer_time: gatherer_time

  see example examples/flow_processor_satpy.yaml_template

- Merge pull request #5 from ch-k/feature-param-proj-cache-dir. [Panu
  Lahtinen]

  Parameter cache_dir for satpy resampler
- Parameter cache_dir for satpy resampler. [Christian Kliche]
- Merge pull request #4 from ch-k/fix-satpy-resampler-radius. [Panu
  Lahtinen]

  Fix config of resampling radius in satpy_resampler
- Reset 'radius_of_influence' at loop start. [Christian Kliche]
- Fix config of resampling radius in satpy_resampler. [Christian Kliche]
- Merge pull request #3 from ch-k/fix-non-xarray-dataset-attr. [Panu
  Lahtinen]

  Fix compatibility with satpy non-xarray branch
- Fix compatibility with satpy non-xarray branch. [Christian Kliche]
- Merge pull request #2 from ch-k/fix-writer-restart-params. [Panu
  Lahtinen]

  Fix writer restart with parameters
- Fix writer restart with parameters. [Christian Kliche]
- Merge pull request #1 from ch-k/feature-scene-reader-param. [Panu
  Lahtinen]

  Use metadata reader param for scene creation
- Use metadata reader param for scene creation. [Christian Kliche]
- Use the main logger from the fetch file. [Martin Raspaud]
- Change setup.cfg's provides to reflect rpm name. [Martin Raspaud]
- Adapt satpy_writer to xarray branch. [Martin Raspaud]
- Check if file is local before fetching. [Martin Raspaud]


v0.8.0 (2017-05-09)
-------------------

Fix
~~~
- Bugfix: use start_time instead of time_slot in satpy_writer. [Martin
  Raspaud]

Other
~~~~~
- Update changelog. [Panu Lahtinen]
- Bump version: 0.7.0 → 0.8.0. [Panu Lahtinen]
- Bugfix satpy resampler. [Martin Raspaud]
- Fix satpy resampler for satpy syntax. [Martin Raspaud]
- Bugfix in satpy compositor. [Martin Raspaud]
- Add fetch plugin. [Martin Raspaud]
- Fix PyYAML case as dependency in setup.cfg. [Martin Raspaud]


v0.7.0 (2017-04-04)
-------------------
- Update changelog. [Panu Lahtinen]
- Bump version: 0.6.0 → 0.7.0. [Panu Lahtinen]
- Add restart() and is_alive() [Panu Lahtinen]
- Add restart() and is_alive(), remove double setting of logger. [Panu
  Lahtinen]
- Move _prev_lock to class attribute, add is_alive() [Panu Lahtinen]
- Move _prev_lock to class attribute, add self.is_alive() [Panu
  Lahtinen]
- Skip coverage calculation if min_coverage is not defined. [Panu
  Lahtinen]


v0.6.0 (2017-03-28)
-------------------
- Update changelog. [Panu Lahtinen]
- Bump version: 0.5.1 → 0.6.0. [Panu Lahtinen]
- Wrap a long line. [Panu Lahtinen]
- Add locking functionality to enhance.Pansharpener. [Panu Lahtinen]
- Fix import, fix name of area defs in scene info dictionary. [Panu
  Lahtinen]
- Add minimal product config. [Panu Lahtinen]
- Add _template to filenames. [Panu Lahtinen]
- Rename example config. [Panu Lahtinen]
- Set save_settings to empty dict if no settings are given. [Panu
  Lahtinen]
- Add minimal config example. [Panu Lahtinen]
- Add coverage module. [Panu Lahtinen]
- Add plugin to check coverage. [Panu Lahtinen]

  This plugin removes areas from production if the data doesn't cover the
  area well enough.

- Reflow overlong line. [Panu Lahtinen]
- Add raised error message to log. [Panu Lahtinen]
- Import trollflow_sat.utils instead of trollflow.utils. [Panu Lahtinen]
- Fix typo in call to release_locks() [Panu Lahtinen]
- Fix incorrect call to release_locks() [Panu Lahtinen]
- Fix typo in function call. [Panu Lahtinen]
- Fix typo. [Panu Lahtinen]
- Add TypeError to catched errors. [Panu Lahtinen]
- Pass full message, not only message data. [Panu Lahtinen]
- Add missing kwarg. [Panu Lahtinen]


v0.5.1 (2017-03-21)
-------------------
- Update changelog. [Panu Lahtinen]
- Bump version: 0.5.0 → 0.5.1. [Panu Lahtinen]
- Fix missing acquire_lock. [Panu Lahtinen]


v0.5.0 (2017-03-21)
-------------------
- Update changelog. [Panu Lahtinen]
- Bump version: 0.4.0 → 0.5.0. [Panu Lahtinen]
- Add missing parameters. [Panu Lahtinen]
- Add check for valid instruments. [Panu Lahtinen]
- Bring satpy plugins up-to-date with mpop versions. [Panu Lahtinen]
- Remove import of acquire_lock(), instead use utils.acquire_lock()
  [Panu Lahtinen]
- Move monitor messaging after scene creation. [Panu Lahtinen]
- Fix publisher name. [Panu Lahtinen]
- Add monitoring message setting examples. [Panu Lahtinen]
- Use lock release wrapper. [Panu Lahtinen]
- Add wrapper to lock release. [Panu Lahtinen]
- Remove unused import. [Panu Lahtinen]
- Add more tests for utils. [Panu Lahtinen]
- Add helper functions for monitoring messaging. [Panu Lahtinen]
- Add monitoring messages. [Panu Lahtinen]


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


