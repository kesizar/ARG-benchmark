/**
 * Escape The Website - Google Analytics 4 Event Dispatcher & Safety Wrapper
 * Provides failure-proof tracking for game lifecycle, key acquisitions,
 * puzzle completions, secret discovery, and score shares.
 */

(function () {
  'use strict';

  // Internal deduplication registry to guarantee single-fire events per session/run
  const firedEvents = new Set();

  /**
   * Safe GA4 Event Dispatcher
   * @param {string} eventName - GA4 event name (e.g. 'game_start', 'key_01_collected')
   * @param {Object} [params={}] - Optional non-sensitive parameters
   */
  function trackEvent(eventName, params) {
    try {
      if (!eventName || typeof eventName !== 'string') return;

      // Safe parameter sanitization (allow numbers, strings, booleans only)
      const sanitizedParams = {};
      if (params && typeof params === 'object') {
        for (const [key, value] of Object.entries(params)) {
          if (typeof value === 'number' || typeof value === 'string' || typeof value === 'boolean') {
            sanitizedParams[key] = value;
          }
        }
      }

      // Check if official gtag is available and execute safely
      if (typeof window.gtag === 'function') {
        window.gtag('event', eventName, sanitizedParams);
      }
    } catch (err) {
      // Analytics failures must never propagate or break game execution
    }
  }

  /**
   * Track one-time unique events per game run
   * @param {string} eventKey - Unique deduplication key
   * @param {string} eventName - GA4 event name
   * @param {Object} [params={}] - Event parameters
   */
  function trackUniqueEvent(eventKey, eventName, params) {
    if (firedEvents.has(eventKey)) return;
    firedEvents.add(eventKey);
    trackEvent(eventName, params);
  }

  /**
   * Reset run-specific deduplication flags (e.g. on new game start)
   */
  function resetRunEvents() {
    firedEvents.delete('key_01_collected');
    firedEvents.delete('key_02_collected');
    firedEvents.delete('key_03_collected');
    firedEvents.delete('game_completed');
  }

  // Expose global safe analytics interface
  window.analyticsManager = {
    trackEvent,
    trackUniqueEvent,
    resetRunEvents
  };

  // Global shorthand helper
  window.trackEvent = trackEvent;
})();
