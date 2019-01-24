# Changelog
All notable changes to this project will be documented in this file.

## [4.0.0] - 2019-01-23
### Changed
* **Moduel Imports** - All modules (e.g bwproject, bwresources, etc...) have been moved into a single package called `bwapi`. This helps to keep things organised and avoid collisions with any other packages you happen to using. All code dependent on bwapi will need to be updated, such that modules are imported from the `bwapi` package. See the following examples for more specific guidance:
    ```python
    from bwproject import BWProject, ...
    from bwresources import BWQueries, BWGroups, ...
    from bwdata import BWData ...
    ```
    must be updated to
    ```python
    from bwapi.bwproject import BWProject, ...
    from bwapi.bwresources import BWQueries, BWGroups, ...
    from bwapi.bwdata import BWData ...
    ```
    Importing modules can be changed from
    ```python
    import bwproject
    ```
    to the following without breaking existing functionality
    ```python
    import bwapi.bwproject as bwproject
    ```
* **Authentication** - `authenticate.py` script changed to command line program `bwapi-authenticate` added to the PATH
    ```bash
    $ ./authenticate.py
    ```
    changed to
    ```bash
    $ bwapi-authenticate
    Please enter your Brandwatch credentials below
    Username: example@example
    Password:
    Authenticating user: example@example
    Writing access token for user: example@example
    Writing access token for user: example@example
    Success! Access token: 00000000-0000-0000-0000-000000000000
    ```