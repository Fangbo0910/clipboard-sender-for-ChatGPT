import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from sites import CDP_URL, SITE_PRIORITY


# CDP bridge to existing Edge instance.
class BrowserBridge:
    def __init__(self):
        self._playwright = None
        self._browser = None

    def is_debug_port_available(self):
        try:
            response = requests.get(f"{CDP_URL}/json/version", timeout=1.5)
            return response.status_code == 200
        except Exception:
            return False

    def connect(self):
        if self._browser is not None:
            return True
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.connect_over_cdp(CDP_URL)
        return True

    def close(self):
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass
        self._browser = None
        self._playwright = None

    def find_target_page(self):
        pages = self._list_pages()
        if not pages:
            return None, None
        for site in SITE_PRIORITY:
            for page in pages:
                url = page.url or ""
                if any(match in url for match in site["match"]):
                    return page, site
        return None, None

    def send_text(self, text):
        page, site = self.find_target_page()
        if page is None:
            return "no_site"
        selector = self._find_input_selector(page, site["selectors"])
        if selector is None:
            return "no_input"
        try:
            page.bring_to_front()
            locator = page.locator(selector).first
            locator.click(timeout=1500)
            page.keyboard.press("Control+V")
            page.keyboard.press("Enter")
        except Exception:
            return "send_failed"
        return "ok"

    # Open author link in a new tab.
    def open_author_page(self):
        if self._browser is None:
            return "no_debug"
        try:
            context = self._browser.contexts[0] if self._browser.contexts else None
            if context is None:
                return "open_failed"
            page = context.new_page()
            page.goto("https://blog.dengfangbo.com", wait_until="domcontentloaded")
        except Exception:
            return "open_failed"
        return "ok"

    def _list_pages(self):
        pages = []
        if self._browser is None:
            return pages
        for context in self._browser.contexts:
            pages.extend(context.pages)
        return pages

    @staticmethod
    def _find_input_selector(page, selectors):
        for selector in selectors:
            try:
                page.wait_for_selector(selector, timeout=1500, state="visible")
                return selector
            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue
        return None
