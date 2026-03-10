# Telegram Daily Capture Flow

## Goal
Define the intended daily flow where OpenClaw reminds the user to send today's
portfolio screenshots through Telegram.

## Flow
1. A scheduler sends a daily reminder through Telegram.
2. The user replies with:
   - a holdings overview screenshot
   - an optional separate gold screenshot
3. OpenClaw stores the attachments at local temporary paths.
4. OpenClaw runs `import-snapshot`.
5. If the vision path is unavailable or fails, the importer falls back to local OCR.
6. OpenClaw reviews missing fields and asks for confirmation if needed.
7. OpenClaw routes the candidate payload into `portfolio_editor`.
8. After sync, OpenClaw runs:
   - `refresh-prices`
   - `signal-review`
   - `weekly-review` or `monthly-review`

## Boundary
- Telegram is the transport layer only.
- The investment project should consume local image paths or attachment payloads.
- Final portfolio writes must still pass validation before they update live state.
