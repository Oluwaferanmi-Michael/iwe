# Render PDFs using Headless Chromium via Playwright

We chose Playwright (headless Chromium) as our rendering engine over pure Python PDF libraries (like WeasyPrint or ReportLab) to enable modern CSS support (Flexbox, Grid, web fonts) and client-side JavaScript execution (charts and dynamic formatting). While Chromium incurs a larger binary footprint and startup overhead, it eliminates the styling quirks and CSS subset limitations of standalone converters.
