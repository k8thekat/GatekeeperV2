## [da1c189](https://github.com/k8thekat/GatekeeperV2/commit/da1c189)
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

