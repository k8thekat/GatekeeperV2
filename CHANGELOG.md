## Version - 1.0.2b - [ba040f5](https://github.com/k8thekat/GatekeeperV2/commit/ba040f5)
#### banner.py
- `isort` imports.
- changed schema layout of multiple tables.
- moved `banner_settings` schema to `instances.py`
- Added `Banner_Group_Message()` dataclass.
- Added `Banner_Group_Channel()` dataclass.
	- Added functionality to update/remove discord channel id
	- Added functionality to add/remove and get discord messages
- Added `Banner_Group()` dataclass.
	- Added functionality to remove a banner group.
	- Added functionality to add/remove/get and update instances in a group.
	- Added functionality to add/remove and get all `Banner_Group_Channels()`.
- Added `DBBanner()` class to handle Instance Banner functionality.

#### server.py -> instance.py
- Changed `server.py` to `instance.py`
- Added methods to update/set every column of the schema.
- Updated class names from `Server` to `Instance`; along with dataclasses in `types.py`.

#### settings.py
- Updated doc strings to be more consistent.

#### types.py
- Added `ButtonStyle()` enum.
- Added `ButtonStyle_Old()` enum.
- Changed `InstanceBannerSettings()` to `Instance_Banner_Settings()` for readability.
	- Changed `server_id` to `instance_id`.
	- Changed `background_path` to `image_path`.
- Changed `InstanceButton()` to `Instance_Button()`.
- Changed `InstanceSettings()` to `Instance_Settings()`.
	- Updated docstring to match schema.
	- Updated attributes to match schema.

#### user.py
- `isort` imports.
- Updated schema's to match `Instance` table change and naming conventions.
- Added `__hash__()` and `__eq__()` methods to the `Metrics()` dataclass for usability with `set()`.
- Added `__hash__()` and `__eq__()` methods to the `IGN()` dataclass for usability with `set()`.
	- Added an `exists()` decorator for all `IGN()` dataclass methods to validate table entries.
	- Removed `_validate_metrics()` as the decorator replaced it's functionality.
	- Changed the `.metrics` property to use `set` instead of `list`. Updated code to match.
	- Fixed login in `update_metrics()` to handle duplicate/existing entries.
	- Added `user_id` validation to `update_user_id()` parameter.
- Updated `User()` dataclass.
	- Removed `_validate_igns()` and created `exists()` wrapper function.
	- Convert `igns` property to a `set`. Updated code to follow.
- Updated `DBUser()`
	- Added `user_id` parameter validation to `add_user()` method.
	- Added `get_unique_visitors()` method to get unique visitors for a specific `instance_id`.
	- Added `role_d` parameter validation to `add_role_instance()` method, same with `remove_role_instance()`, `add_guild_instances()` and `remove_guild_instances()` methods .
- Pushed `1.0.0b` and `1.0.1b` changes.

#### __init__.py
- Version bump `1.0.1b`.

## Version - 1.0.1b - [5d75b51](https://github.com/k8thekat/GatekeeperV2/commit/5d75b51)
#### build.py
- Forgot to commit changes.
- Version bump `1.0.0b`

#### CHANGELOG.md
- Pushed `0.0.11b` changes.

## Version - 1.0.0b - [2b17217](https://github.com/k8thekat/GatekeeperV2/commit/2b17217)
#### base.py
- Added `dir` attribute to assist with `DB_FILE_PATH`.
- Updated global `DB_FILE_PATH` for development.
- Fixed typo in SCHEMA for `VERSION_SETUP_SQL`.
- Added `asqlite.Pool` support.
- Added `pool` property for `asqlite.Pool`.
- Updated existing methods to support `asqlite.Pool`.
- Added `_fetchone()`, `_fetchall()`, `_execute()` and `_execute_with_cursor()`.
- Updated `create_tables()` to `_create_tables()` and add `asqlite.Pool` support.
- Removed property decorators for `version`.
- Added `_get_version()` ,`_set_version()` and `_update_version()`.
- Added `_delete_row_where()`.
- Changed `_update_row()` to `_update_row_where()`.

#### settings.py
- Updated  Schema types and constraints.
- Added UNIQUE and FOREIGN KEYS to multiple Schemas.
- Added attribute type definition.
- Added `add_guild_id()` function to add Discord Guild IDs to the database.
- Added `get_guild_settings()` to get a Discord Guilds DB settings.
- Removed `msg_timeout`, `mod_role_id`, `donator_role_id` and `prefixes` property's.
- Added `set` methods for `mod_role_id`, `donator_role_id` and `msg_timeout`.
- Added `add`, `remove` and `get` methods for `prefixes`.
- Added methods to `add`, `get` and `remove` owners from the database.

#### types.py
- Added `Settings()` dataclass to support `DBSettings()` method returns.
- Added `Owner()` dataclass to support `DBSettings()` method returns.

#### user.py
- Updated Schema types and constraints.
- Added `USER_INSTANCES_SETUP_SQL`, `ROLE_INSTANCES_SETUP_SQL` and `GUILD_INSTANCES_SETUP_SQL`.
- Added `Metrics()` dataclass to represent the `ign_metrics` table.
	- Added property's to convert posix time values into datetime objects.
- Added `IGN()` dataclass to represent the `ign` table.
	- Added `get_metrics()` and `update_metrics()` to populate and update `ign_metrics`.
	- Added `_validate_metrics()` and `_replace_metrics()` to validate `Metrics()` dataclasses.
	- Added `get_instance_metrics()` to get instance specific metrics.
	- Added `get_instance_last_login()` to get last login details.
	- Added `get_global_playtime()` to get all playtime.
	- Added `update_name()` to change the `ign` name.
	- Added `update_user_id()` to change the `user_id` of the ign.
	- Added `update_type_id()` to change the `ServerType` of the ign.
	- Added `delete_ign()`
- Added `User()` dataclass to represent the `users` table and to hold `IGN` dataclasses.
	- Added `add_ign()` to add an IGN related to the Discord User.
	- Added `_get_igns()` to get all the IGNs related to the Discord User.
	- Added `_get_instance_list()` to get the AMP Instance IDs that the Discord User can interact with.
	- Added `add_user_instance()` to add an AMP Instance ID to the `user_instances` table.
	- Added `remove_user_instance()` to remove an AMP Instance ID from the `user_instances` table.
	- Added `_get_role_based_instance_list()` to get all the AMP Instance IDs related to the Discord Role ID.
	- Added `_get_guild_based_instance_list()` to get all the AMP Instance IDs related to the Discord Guild ID.
- Restructured the `DBUser()`.
	- Added `add_user()` to add a Discord User ID to the `users` table.
	- Added `get_user()` to to retrieve an entry from the `users` table; will populate IGNs, Metrics and Instance Lists.
	- Added `get_ign()` to get a `IGN` dataclass based upon the name and type_id.
	- Added `get_all_igns()` to get all the table `ign` entries.
	- Added `add_role_instance()` to add AMP Instance IDs to the `role_instances` table.
	- Added `remove_role_instance()` to remove AMP Instance IDs from the `role_instances` table.
	- Added `add_guild_instances()` to add AMP Instance IDs to the `guild_instances` table.
	- Added `remove_guild_instances()` to remove AMP Instance IDs from the `guild_instances` table.

#### build.py
- Moved `user` and `project` attributes.
- Updated to `Version 0.0.11b`
- Fixed branch typo.

## Version - 0.0.11b - [bf0a6a4](https://github.com/k8thekat/GatekeeperV2/commit/bf0a6a4)
#### Overall
- Re-organized branch and files to better facilitate development.
- Renamed COPYING to LICENSE.
- Renamed `db.py` to `base.py`.
- Renamed `db_types.py` to `types.py`.

#### build.py
- Version control and changelog generator.

#### banner.py
- Moved the dataclass to `types.py`
- Changed SQL schema naming conventions.
- Added `add_channel_to_banner_group()`, `remove_channel_from_banner_group()`, `add_message_to_banner_group()` and `update_banner_settings()`.

#### base.py
- Renamed class from `Database()` to `Base()`.
- Moved the `version` SQL schema to a global attribute.
- Changed the `DB_FILENAME` to "gatekeeper.db".
- Changed the `VERSION` to "0.0.1".

#### server.py
- Moved `Server()` dataclass to `types.py`.
- Changed dataclass name to `ServerSettings()`.

#### settings.py
- Changed `DBsettings()` to `DBSettings()`.
- Added version control.
- Version bump `0.0.11b`

## Version - 0.0.1b - [f14ceb0](https://github.com/k8thekat/GatekeeperV2/commit/f14ceb0)
#### Changelog.md
- Implemented new Changelog Formatting.

#### banner.py
- `pep8` and `isort` formatting.
- Formatted SQL Schema.
- Created Banner dataclass.
- Began work on DBBanner class.

#### db_types.py
- Created ServerTypes enum.

#### db.py
- `pep8` and `isort` formatting.
- Handled TODOs.
- Improved logic on _update_row to support no `where` parameter.
- Added a `_select_row_where()` method.

#### server.py
- `pep8` and `isort` formatting.
- Formatted SQL Schema.
- Added return type to `add_server()`.
	- Changed DB method's to support `where` clauses.
- Changed `update_server()` to use `where` clauses.
- Changed `_remove_server()` to use `where` clauses.

#### settings.py
- `pep8` and `isort` formatting.
- Changed `prefixs` to `prefixes`
	- Fixed typo's related to the method and table name.
- Replaced `update_guild_id()` with `set_guild_id()` and added logic to handle both cases.
- Replaced `update_role_id()` with `set_mod_role_id()` and added logic to handle both cases.
- Added `set_donator_role_id()`.
- Fixed SQL logic in `update_message_timeout()`.
- Fixed SQL logic in `add_owner()`.
- Fixed SQL logic in `remove_owner()`.
- Fixed SQL logic in `add_prefix()`.
- Fixed SQL logic in `remove_prefix()`.

#### users.py
- `pep8` and `isort` formatting.
- removed logic for `ign_types` and the related Table and methods.
	- Changed to db_types -> ServerTypes(Enum).
- Updated SQL statements to use new `_select_row_where()`.

## [f14ceb0](https://github.com/k8thekat/GatekeeperV2/commit/f14ceb0)
#### Changelog.md
- Implemented new Changelog Formatting.

#### banner.py
- `pep8` and `isort` formatting.
- Formatted SQL Schema.
- Created Banner dataclass.
- Began work on DBBanner class.

#### db_types.py
- Created ServerTypes enum.

#### db.py
- `pep8` and `isort` formatting.
- Handled TODOs.
- Improved logic on _update_row to support no `where` parameter.
- Added a `_select_row_where()` method.

#### server.py
- `pep8` and `isort` formatting.
- Formatted SQL Schema.
- Added return type to `add_server()`.
	- Changed DB method's to support `where` clauses.
- Changed `update_server()` to use `where` clauses.
- Changed `_remove_server()` to use `where` clauses.

#### settings.py
- `pep8` and `isort` formatting.
- Changed `prefixs` to `prefixes`
	- Fixed typo's related to the method and table name.
- Replaced `update_guild_id()` with `set_guild_id()` and added logic to handle both cases.
- Replaced `update_role_id()` with `set_mod_role_id()` and added logic to handle both cases.
- Added `set_donator_role_id()`.
- Fixed SQL logic in `update_message_timeout()`.
- Fixed SQL logic in `add_owner()`.
- Fixed SQL logic in `remove_owner()`.
- Fixed SQL logic in `add_prefix()`.
- Fixed SQL logic in `remove_prefix()`.

#### users.py
- `pep8` and `isort` formatting.
- removed logic for `ign_types` and the related Table and methods.
	- Changed to db_types -> ServerTypes(Enum).
- Updated SQL statements to use new `_select_row_where()`.

