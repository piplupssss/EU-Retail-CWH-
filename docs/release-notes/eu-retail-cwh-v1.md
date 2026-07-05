# EU Retail CWH System V1

Release date: 2026-07-05 23:22 CEST

This is the first clean Vue rebuild package for the European Retail Central Warehouse local management tool.

## What changed

- Product name changed to `EU Retail CWH System`.
- Frontend rebuilt with Vue and Vite as the new clean foundation.
- Existing Flask backend is retained to protect current import, export, backup, authentication, invoice, logistics, inventory, and image-matching rules.
- Windows full package keeps the embedded Python runtime, so normal users do not need to install Python.
- Package starts empty: no business database, no uploaded files, no invoices, no inventory images.
- Data migration path is `core_backup_no_images.xlsx` plus the `images` folder.

## Release assets

The full Windows package is published as a GitHub Release asset:

- `EU-Retail-CWH-System-V1-20260705-2322.zip`
- SHA256: `e7d90e4c46fee65231f8acd4ddc58b86b02d975c909dc24a7bcccf6b5f2c0dba`

## Notes

- Do not commit business data, uploaded Excel files, PDFs, invoices, SQLite databases, or real images to this repository.
- Future software versions should be published through GitHub Releases.
- The local app should download update metadata from the GitHub-backed update channel.
