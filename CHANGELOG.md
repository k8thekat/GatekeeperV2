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

