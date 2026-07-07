// Firebase web config — intentionally public (security lives in firestore.rules).
// null = sync disabled, app runs local-only exactly like Phase 1.
// After creating the Firebase project (see PHASE2-HANDOFF.md), replace null with
// the config object from Console → Project settings → Your apps → Web app.
window.FIREBASE_CONFIG = null;
