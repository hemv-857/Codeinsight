# Tests

Repository-wide test suites live here.

`make test` runs pytest through the first-party Python coverage gate and fails
below 90% line coverage for backend repositories/services, `graph`, `parser`,
and worker modules. Package markers and startup entrypoints are omitted from the
coverage denominator.
