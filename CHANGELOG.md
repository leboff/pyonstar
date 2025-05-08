# Changelog

All notable changes to the OnStar Python library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- Documentation improvements
- Additional examples
- Improved error handling
- Added async file I/O using aiofiles to prevent blocking operations
- Fixed blocking SSL verification in httpx client
- Added proper resource cleanup with close() method
- Better performance in asynchronous environments

## [0.0.1] - 2023-08-22
### Added
- Initial release
- Port of OnStarJS to Python
- Basic OnStar API functionality
- Authentication with GM API
- Vehicle remote commands (start/stop, lock/unlock)
- Vehicle status and diagnostics
- Electric vehicle charging functions 