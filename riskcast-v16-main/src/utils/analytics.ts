/**
 * Minimal event tracking abstraction.
 * Sends events to backend /api/account/events with batching potential.
 */

export async function track(eventName: string, payload: Record<string, unknown> = {}) {
  try {
    await fetch('/api/account/events', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ event_name: eventName, payload }),
    });
  } catch (err) {
    // Fail silently to avoid blocking UX
    console.warn('[analytics] failed to send event', err);
  }
}
