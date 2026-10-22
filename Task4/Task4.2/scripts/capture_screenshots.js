const { chromium } = require("playwright");

async function loginAndCapture(url, outputPath) {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(3000);

  const username = page.getByLabel("Username");
  if (await username.count()) {
    await username.fill("demo");
    await page.locator("#password, input[name='password']").first().fill("demo");
    await page.getByRole("button", { name: "Login" }).click();
    await page.waitForTimeout(8000);
    await page.getByRole("link", { name: "Processes" }).click();
    await page.waitForTimeout(5000);
  }

  await page.screenshot({ path: outputPath, fullPage: true });
  await browser.close();
}

(async () => {
  await loginAndCapture("http://localhost:8081/", "screenshots/tasklist_allow.png");
  await loginAndCapture("http://localhost:8082/", "screenshots/tasklist_deny.png");
})();
