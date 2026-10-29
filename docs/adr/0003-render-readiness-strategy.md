# Render Readiness Detection Strategy

We chose a dual readiness detection strategy: the renderer waits for `networkidle` by default, but allows templates to specify an optional explicit ready signal (e.g., `#render-ready` selector or `window.__RENDER_READY__`). This ensures static templates render reliably without boilerplate, while dynamic templates containing client-side charts or web fonts can prevent premature PDF snapshots.
