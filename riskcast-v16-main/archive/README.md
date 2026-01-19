# RISKCAST Archive

This directory contains legacy code that has been archived but kept for reference and backward compatibility.

## Structure

- `engines/v14/` - Legacy v14 engine code
- `engines/v15/` - Legacy v15 engine code (if exists)
- `pages/input_v19/` - Legacy input page v19
- `pages/summary_v100/` - Legacy summary pages (if exists)

## Purpose

Legacy code is archived here to:
1. Preserve history and reference
2. Enable backward compatibility via adapters
3. Allow gradual migration without breaking changes

## Important Notes

- **DO NOT** import directly from archive in new code
- Use adapters in `app/core/adapters/` instead
- Legacy code is kept for reference only
- Deprecated endpoints will be removed in future versions

## Migration Status

See `docs/DEPRECATION.md` for migration timeline and guides.

