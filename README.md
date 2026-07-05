# EU Retail CWH

This repository stores the source code, release manifests, and GitHub Release packages for **EU Retail CWH System**.

The system is a local Windows warehouse and logistics management tool for European retail central warehouse operations. Business data is processed locally and must not be committed to this repository.

## Current tracks

- `eu-retail-cwh-system/` - clean Vue + Flask rebuild foundation.
- `github_publish/` - update manifests and release metadata.
- `tools/` - packaging and release helper scripts.
- `docs/release-notes/` - version notes for released builds.

## Data policy

Do not commit:

- uploaded supplier Excel files
- invoices or PDFs
- SQLite databases
- inventory photos
- `core_backup_no_images.xlsx`
- customer or shipment business data

Runtime data should stay on the user PC. Clean software packages are published through GitHub Releases.

## Latest clean package

The first clean rebuild package is published under the `eu-retail-cwh-v1` release.
