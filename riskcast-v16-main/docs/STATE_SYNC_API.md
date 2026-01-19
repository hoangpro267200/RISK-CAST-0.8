# RISKCAST State Sync API

Backend state synchronization endpoints for preventing data loss and unifying source of truth.

## Overview

The State Sync API provides persistent backend storage for shipment state (RISKCAST_STATE), enabling:
- **Data persistence** - State survives browser cache clears
- **Multi-device sync** - Access state from any device
- **Conflict resolution** - Last-write-wins with timestamps
- **Offline support** - localStorage as cache/fallback

## Endpoints

### GET /api/v1/state/{shipment_id}

Get shipment state from backend.

**Response:**
```json
{
  "success": true,
  "data": {
    "shipment_id": "abc123...",
    "state": {
      "shipment": { ... },
      "riskModules": { ... }
    },
    "updated_at": "2024-01-15T10:30:00Z",
    "created_at": "2024-01-15T09:00:00Z"
  },
  "error": null,
  "meta": {
    "request_id": "...",
    "ts": "...",
    "version": "v16"
  }
}
```

### PUT /api/v1/state/{shipment_id}

Save shipment state to backend.

**Request:**
```json
{
  "state": {
    "shipment": { ... },
    "riskModules": { ... }
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "shipment_id": "abc123...",
    "state": { ... },
    "updated_at": "2024-01-15T10:35:00Z",
    "created_at": "2024-01-15T09:00:00Z"
  },
  "error": null,
  "meta": { ... }
}
```

### POST /api/v1/state

Create new shipment state (generates shipment_id if not provided).

**Request:**
```json
{
  "state": { ... },
  "shipment_id": "optional-custom-id"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "shipment_id": "generated-or-provided-id",
    "state": { ... },
    "updated_at": "...",
    "created_at": "..."
  },
  "error": null,
  "meta": { ... }
}
```

### GET /api/v1/state

List recent shipments.

**Query Parameters:**
- `limit` (optional, default: 100) - Maximum number of shipments

**Response:**
```json
{
  "success": true,
  "data": {
    "shipments": [
      {
        "shipment_id": "abc123...",
        "updated_at": "2024-01-15T10:30:00Z",
        "created_at": "2024-01-15T09:00:00Z"
      },
      ...
    ],
    "count": 10
  },
  "error": null,
  "meta": { ... }
}
```

## Frontend Integration Pattern

### Recommended Approach

1. **On Page Load:**
   ```javascript
   async function loadState(shipmentId) {
     // Priority 1: Try backend
     try {
       const response = await fetch(`/api/v1/state/${shipmentId}`);
       if (response.ok) {
         const data = await response.json();
         if (data.success && data.data) {
           // Use backend state
           return data.data.state;
         }
       }
     } catch (error) {
       console.warn('Backend state unavailable, using localStorage');
     }
     
     // Priority 2: Fallback to localStorage
     const localState = localStorage.getItem('RISKCAST_STATE');
     if (localState) {
       return JSON.parse(localState);
     }
     
     return null;
   }
   ```

2. **On State Change (Debounced):**
   ```javascript
   let saveTimeout;
   
   function saveState(shipmentId, state) {
     // Clear previous timeout
     clearTimeout(saveTimeout);
     
     // Save to localStorage immediately (cache)
     localStorage.setItem('RISKCAST_STATE', JSON.stringify(state));
     
     // Debounce backend save (500ms)
     saveTimeout = setTimeout(async () => {
       try {
         await fetch(`/api/v1/state/${shipmentId}`, {
           method: 'PUT',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ state })
         });
       } catch (error) {
         console.error('Failed to save to backend:', error);
         // State is still in localStorage, so no data loss
       }
     }, 500);
   }
   ```

3. **Conflict Detection:**
   ```javascript
   async function saveStateWithConflictCheck(shipmentId, state, clientUpdatedAt) {
     // Include client's updated_at in state for conflict detection
     state._updated_at = clientUpdatedAt;
     
     const response = await fetch(`/api/v1/state/${shipmentId}`, {
       method: 'PUT',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ state })
     });
     
     const data = await response.json();
     
     // Check if server has newer version
     if (data.success && data.data.updated_at > clientUpdatedAt) {
       // Conflict: Server has newer version
       console.warn('State conflict detected - server has newer version');
       // Optionally: Show user warning, merge, or reload
     }
     
     return data;
   }
   ```

## Shipment ID Generation

If not provided, shipment_id is auto-generated from state:
- Based on: POL + POD + Mode + Cargo Type + Date
- Format: 16-character hex string (MD5 hash)
- Deterministic: Same inputs = same ID

## Storage Backends

### File-based (Default)
- Location: `data/state/{shipment_id}.json`
- No database required
- Works out of the box

### MySQL (Optional)
- Enable: Set `USE_MYSQL=true` in `.env`
- Requires: MySQL database configured
- Future: Will use `app/core/state_storage_mysql.py`

## Error Handling

All endpoints return standard response envelope:
- `success: true/false`
- `data: {...}` or `null`
- `error: { code, message, details }` or `null`
- `meta: { request_id, ts, version }`

## Migration from localStorage-only

1. **Phase 1 (Current):** Backend endpoints available, localStorage still primary
2. **Phase 2 (Future):** Frontend updated to backend-first
3. **Phase 3 (Future):** localStorage becomes cache-only

## Security

- State is stored per shipment_id (no user authentication yet)
- Future: Add user/session-based access control
- Sanitization: State is sanitized before storage (via existing sanitizers)

---

**Status:** Backend endpoints complete ✅  
**Frontend Integration:** Phase 7 (Frontend Consolidation)

