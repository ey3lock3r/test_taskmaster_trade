# Test info

- Name: Dashboard Page >> should display bot status and parameters
- Location: /home/ey3lock3r/test_taskmaster_trade/frontend/e2e/dashboard.spec.ts:58:9

# Error details

```
Error: Timed out 5000ms waiting for expect(locator).toBeVisible()

Locator: locator('text=Bot Status: active')
Expected: visible
Received: <element(s) not found>
Call log:
  - expect.toBeVisible with timeout 5000ms
  - waiting for locator('text=Bot Status: active')

    at /home/ey3lock3r/test_taskmaster_trade/frontend/e2e/dashboard.spec.ts:78:59
```

# Page snapshot

```yaml
- text: Bot Dashboard
- paragraph: "Error fetching data: HTTP error! status: 404"
- paragraph: "Bot Status:"
- text: Error
- paragraph: "Parameters:"
- text: Error
- button "Start Bot"
- button "Stop Bot"
- alert
- button "Open Next.js Dev Tools":
  - img
- button "Open issues overlay": 1 Issue
- button "Collapse issues badge":
  - img
```

# Test source

```ts
   1 | import { test, expect } from '@playwright/test';
   2 | test.describe('Dashboard Page', () => {
   3 |   test.beforeEach(async ({ page }) => {
   4 |     // Listen for console messages and log them
   5 |     page.on('console', msg => {
   6 |       if (msg.type() === 'error') {
   7 |         console.error(`Browser console error: ${msg.text()}`);
   8 |       }
   9 |     });
   10 |
   11 |     // 1. Navigate to signup page
   12 |     await page.goto('/signup');
   13 |     await page.waitForLoadState('domcontentloaded'); // Wait for DOM to be ready
   14 |     await page.waitForLoadState('networkidle'); // Wait for the page to be fully loaded
   15 |
   16 |     // Fill out signup form
   17 |     const randomNum = Math.floor(Math.random() * 10000);
   18 |     const username = `testuser${randomNum}`;
   19 |     const email = `test${randomNum}@example.com`;
   20 |     const password = 'password123';
   21 |
   22 |     await page.waitForSelector('input[name="username"]');
   23 |     await page.locator('input[name="username"]').click(); // Click before filling
   24 |     await page.waitForTimeout(100); // Small delay
   25 |     await page.fill('input[name="username"]', username);
   26 |     await page.fill('input[name="email"]', email);
   27 |     await page.fill('input[name="password"]', password);
   28 |     await page.fill('input[name="confirmPassword"]', password);
   29 |     await page.waitForLoadState('domcontentloaded');
   30 |     await page.waitForLoadState('networkidle');
   31 |     await page.click('button[type="submit"]');
   32 |
   33 |     // Wait for navigation to login page after signup
   34 |     await page.waitForURL('/login', { timeout: 90000 }); // Wait for URL change
   35 |     await page.waitForLoadState('networkidle'); // Ensure the page is fully loaded
   36 |     await page.waitForSelector('input[name="email"]'); // Wait for email input to ensure page is ready
   37 |     await expect(page).toHaveURL('/login');
   38 |     await expect(page.locator('div[data-slot="card-title"].text-2xl.font-bold')).toHaveText('Login'); // Ensure the title is present and has text
   39 |
   40 |     // 2. Fill out login form
   41 |     await page.waitForSelector('input[name="email"]');
   42 |     await page.locator('input[name="email"]').click(); // Click before filling
   43 |     await page.waitForTimeout(100); // Small delay
   44 |     await page.fill('input[name="email"]', email);
   45 |     await page.fill('input[name="password"]', password);
   46 |     await page.waitForLoadState('domcontentloaded');
   47 |     await page.waitForLoadState('networkidle');
   48 |     await page.click('button[type="submit"]');
   49 |
   50 |     // Wait for navigation to dashboard page after login
   51 |     await page.waitForURL('/dashboard', { timeout: 90000 }); // Wait for URL change
   52 |     await page.waitForLoadState('networkidle'); // Ensure the page is fully loaded
   53 |     await expect(page).toHaveURL('/dashboard');
   54 |     // Check for a specific element on the dashboard to confirm login
   55 |     await expect(page.locator('div[data-slot="card-title"].text-center')).toHaveText('Bot Dashboard');
   56 |   });
   57 |
   58 |     test('should display bot status and parameters', async ({ page }) => {
   59 |     // Mock API responses for /bot/status and /bot/parameters
   60 |     await page.route('**/api/bot/status', route => {
   61 |       route.fulfill({
   62 |         status: 200,
   63 |         contentType: 'application/json',
   64 |         body: JSON.stringify({ id: 1, status: 'active', last_check_in: new Date().toISOString(), is_active: true }),
   65 |       });
   66 |     });
   67 |
   68 |     await page.route('**/api/bot/parameters?bot_id=*', route => {
   69 |       route.fulfill({
   70 |         status: 200,
   71 |         contentType: 'application/json',
   72 |         body: JSON.stringify({ parameters: { param1: 'value1', param2: 'value2' } }),
   73 |       });
   74 |     });
   75 |
   76 |     await page.reload(); // Reload to apply mock
   77 |
>  78 |     await expect(page.locator('text=Bot Status: active')).toBeVisible();
      |                                                           ^ Error: Timed out 5000ms waiting for expect(locator).toBeVisible()
   79 |     await expect(page.locator('text=param1: value1')).toBeVisible();
   80 |     await expect(page.locator('text=param2: value2')).toBeVisible();
   81 |   });
   82 |
   83 |   // test('should start the bot when start button is clicked', async ({ page }) => {
   84 |   //   await page.route('**/api/bot/start', route => {
   85 |   //     route.fulfill({
   86 |   //       status: 200,
   87 |   //       contentType: 'application/json',
   88 |   //       body: JSON.stringify({ message: 'Bot started' }),
   89 |   //     });
   90 |   //   });
   91 |
   92 |   //   await page.route('**/api/bot/status', route => {
   93 |   //     route.fulfill({
   94 |   //       status: 200,
   95 |   //       contentType: 'application/json',
   96 |   //       body: JSON.stringify({ id: 1, status: 'running', last_check_in: new Date().toISOString(), is_active: true }),
   97 |   //     });
   98 |   //   });
   99 |
  100 |   //   await page.click('button:has-text("Start Bot")');
  101 |   //   await expect(page.locator('text=Bot started')).toBeVisible();
  102 |   //   await expect(page.locator('text=Bot Status: running')).toBeVisible();
  103 |   // });
  104 |
  105 |   // test('should stop the bot when stop button is clicked', async ({ page }) => {
  106 |   //   await page.route('**/api/bot/stop', route => {
  107 |   //     route.fulfill({
  108 |   //       status: 200,
  109 |   //       contentType: 'application/json',
  110 |   //       body: JSON.stringify({ message: 'Bot stopped' }),
  111 |   //     });
  112 |   //   });
  113 |
  114 |   //   await page.route('**/api/bot/status', route => {
  115 |   //     route.fulfill({
  116 |   //       status: 200,
  117 |   //       contentType: 'application/json',
  118 |   //       body: JSON.stringify({ id: 1, status: 'stopped', last_check_in: new Date().toISOString(), is_active: false }),
  119 |   //     });
  120 |   //   });
  121 |
  122 |   //   await page.click('button:has-text("Stop Bot")');
  123 |   //   await expect(page.locator('text=Bot stopped')).toBeVisible();
  124 |   //   await expect(page.locator('text=Bot Status: stopped')).toBeVisible();
  125 |   // });
  126 |
  127 |   // test('should show error feedback for failed start action', async ({ page }) => {
  128 |   //   await page.route('**/api/bot/start', route => {
  129 |   //     route.fulfill({
  130 |   //       status: 500,
  131 |   //       contentType: 'application/json',
  132 |   //       body: JSON.stringify({ detail: 'Failed to start bot' }),
  133 |   //     });
  134 |   //   });
  135 |
  136 |   //   await page.click('button:has-text("Start Bot")');
  137 |   //   await expect(page.locator('text=Failed to start bot')).toBeVisible();
  138 |   // });
  139 |
  140 |   // test('should show error feedback for failed stop action', async ({ page }) => {
  141 |   //   await page.route('**/api/bot/stop', route => {
  142 |   //     route.fulfill({
  143 |   //       status: 500,
  144 |   //       contentType: 'application/json',
  145 |   //       body: JSON.stringify({ detail: 'Failed to stop bot' }),
  146 |   //     });
  147 |   //   });
  148 |
  149 |   //   await page.click('button:has-text("Stop Bot")');
  150 |   //   await expect(page.locator('text=Failed to stop bot')).toBeVisible();
  151 |   // });
  152 | });
```