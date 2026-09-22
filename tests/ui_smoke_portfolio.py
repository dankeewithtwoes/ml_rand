from playwright.sync_api import sync_playwright


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors: list[str] = []
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:8801", wait_until="networkidle")
        assert page.locator(".card").count() == 21
        page.locator(".card").nth(3).get_by_role("button", name="Открыть инструмент").click()
        assert page.locator("#runner").is_visible()
        page.locator("#runButton").click()
        page.locator("#runStatus").filter(has_text="pending review").wait_for(timeout=10_000)
        assert '"result": 11' in page.locator("#result").inner_text()
        page.get_by_role("button", name="Принять").click()
        page.locator("#runStatus").filter(has_text="approved").wait_for()
        page.locator("#runner .close").click()
        page.locator("#historyButton").click()
        page.locator("#historyDialog").wait_for(state="visible")
        assert page.locator(".history-item").count() >= 1
        page.set_viewport_size({"width": 390, "height": 844})
        page.locator("#historyDialog .close").click()
        assert page.locator(".card").first.is_visible()
        assert not errors, errors
        browser.close()


if __name__ == "__main__":
    main()
