# ZGX Demo Center

A demo catalog and installer/launcher suite with vision, document translation, healthcare, PII, robotics and other examples that share installation and lifecycle tooling.

**Maturity:** Historical demo suite. Active runtime is the bundle referenced by the desktop launcher; the main directory is a separate preserved snapshot. Source syntax checks pass. Downloading/installing all demo workloads, paid/external integrations and container builds were not performed.

## How it works

HTML catalog → shared Python installation plans and launcher utilities → independent demo apps/containers. The repository stays a suite because loader plans and common path utilities couple the included examples. Individual applications retain their original source subdirectories.

## Getting started

Read [installation, configuration and shutdown](docs/OPERATIONS.md) and [model/data retrieval](docs/MODELS.md). Review [dependency evidence](docs/DEPENDENCIES.md) before choosing an environment. The safe review launcher uses loopback and does not install services or load models.

## Security and data

Read [security and safe updates](SECURITY.md) and [ownership/license status](docs/LICENSE-STATUS.md). Runtime originals are preserved separately. This is a sanitized source snapshot with new history: no account state, business records, model weights, unknown media assets or original logs/history are distributed. Third-party notices included in this copy remain applicable.

## Verification

See [verification evidence and limitations](docs/VERIFICATION.md). Tests distinguish synthetic/mocked workflows from live integrations. Original demo screenshots and document recordings are excluded; use the synthetic workflow in the operations guide for your own reviewed demonstration.

## Roadmap

Split stable independent demos when shared loader dependencies are removed; pin and document upstream licenses/assets for every example; add deterministic launcher diagnostics and synthetic-data smoke fixtures.

For route/source details see [architecture](docs/ARCHITECTURE.md).
