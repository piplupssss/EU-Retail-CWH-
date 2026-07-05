# EU Retail CWH System

Clean Vue rebuild of the EU Retail Central Warehouse local management tool.

This branch starts a new product line after VN62. It does not patch the old
single-file frontend. Existing production data should be restored from:

- `core_backup_no_images.xlsx`
- `images/`

## Architecture

- `backend/`: Flask business API copied from the stable VN62 backend.
- `frontend/`: Vue 3 + Vite app for the rebuilt user interface.
- `docs/`: migration and release notes for the clean rebuild.

## Principles

- Business data stays local.
- Excel import/export, image matching, logistics status protection, inventory
  calculation, backup and update logic are not rewritten in the first step.
- The old `vn8` app remains untouched so VN62 can continue running.
- New full system releases are published as clean packages, not old-version
  patches.

