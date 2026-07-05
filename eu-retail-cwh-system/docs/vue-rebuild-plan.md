# Vue Rebuild Plan

## Product Name

EU Retail CWH System

## Rebuild Scope

The first clean version keeps the stable Flask backend and replaces the old
single-file frontend with a Vue application.

## Backend Boundary

Keep these backend domains intact for the first version:

- Authentication and local accounts
- Logistics dashboard, shipment list, manual status maintenance and recycle bin
- Inventory list, image matching, SKU details and export
- Invoice parsing, acceptance calibration and acceptance list
- Core backup restore/export
- Local-only data handling

## Frontend First Slice

The first Vue slice focuses on high-frequency, already-approved flows:

- App shell and navigation
- Login state
- Logistics dashboard shell
- Inventory dashboard shell
- Logistics list
- Inventory list
- Data management shell
- Version information shell

## Release Strategy

The new system starts as a clean full package. It does not need to upgrade from
VN62. Users import `core_backup_no_images.xlsx` plus `images/` after installing
the clean package.

GitHub should be the version backup location. If GitHub binary release upload is
not available through the current connector, the full package is prepared
locally and must be uploaded as a release asset or via Git LFS later.

