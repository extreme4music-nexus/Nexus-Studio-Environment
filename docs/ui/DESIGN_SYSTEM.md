# Shared Studio design candidate

One Python widget tree on Windows/Linux/macOS, Fusion style and Noto Sans. Logical sizes: 28px outer spacing, 14px body, 24px page title, 28px brand, minimum window 850×620. Shared colors are defined in theme.py: dark canvas #11151c, raised surfaces #1b222d, readable text #e7edf5, secondary #aab9cb, amber action #edba72, borders #354153.

Navigation: project list left; selected project's brief and metadata right. Future modules are descriptive text, with no inactive fake controls. Empty, busy, dirty, conflict and error states are explicit. Primary save disables for clean/empty-name/busy states. Keyboard focus is visible; widgets have accessible labels. Full assistive-technology verification is still pending.

Acceptance pending beyond this prototype: native keyboard/screen-reader review, 100/150/200% scaling, long-text translations, small screens, cross-platform screenshot comparison and agreed tolerances for window chrome/rasterization. UI-01/02 are intentionally still open in the system checklist.
