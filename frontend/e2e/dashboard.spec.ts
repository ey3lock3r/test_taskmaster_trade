import { test, expect } from '@playwright/test';
test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    // Listen for console messages and log them
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error(`Browser console error: ${msg.text()}`);
      }
    });

    // 1. Navigate to signup page
    await page.goto('/signup');
    await page.waitForLoadState('domcontentloaded'); // Wait for DOM to be ready
    await page.waitForLoadState('networkidle'); // Wait for the page to be fully loaded

    // Fill out signup form
    const randomNum = Math.floor(Math.random() * 10000);
    const username = `testuser${randomNum}`;
    const email = `test${randomNum}@example.com`;
    const password = 'password123';

    await page.waitForSelector('input[name="username"]');
    await page.locator('input[name="username"]').click(); // Click before filling
    await page.waitForTimeout(100); // Small delay
    await page.fill('input[name="username"]', username);
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', password);
    await page.fill('input[name="confirmPassword"]', password);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');
    await page.click('button[type="submit"]');

    // Wait for navigation to login page after signup
    await page.waitForURL('/login', { timeout: 90000 }); // Wait for URL change
    await page.waitForLoadState('networkidle'); // Ensure the page is fully loaded
    await page.waitForSelector('input[name="email"]'); // Wait for email input to ensure page is ready
    await expect(page).toHaveURL('/login');
    await expect(page.locator('div[data-slot="card-title"].text-2xl.font-bold')).toHaveText('Login'); // Ensure the title is present and has text

    // 2. Fill out login form
    await page.waitForSelector('input[name="email"]');
    await page.locator('input[name="email"]').click(); // Click before filling
    await page.waitForTimeout(100); // Small delay
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', password);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');
    await page.click('button[type="submit"]');

    // Wait for navigation to dashboard page after login
    await page.waitForURL('/dashboard', { timeout: 90000 }); // Wait for URL change
    await page.waitForLoadState('networkidle'); // Ensure the page is fully loaded
    await expect(page).toHaveURL('/dashboard');
    // Check for a specific element on the dashboard to confirm login
    await expect(page.locator('div[data-slot="card-title"].text-center')).toHaveText('Bot Dashboard');
  });

    test('should display bot status and parameters', async ({ page }) => {
    // Mock API responses for /bot/status and /bot/parameters
    await page.route('**/api/bot/status', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 1, status: 'active', last_check_in: new Date().toISOString(), is_active: true }),
      });
    });

    await page.route('**/api/bot/parameters?bot_id=*', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ parameters: { param1: 'value1', param2: 'value2' } }),
      });
    });


    await expect(page.locator('text=Bot Status: active')).toBeVisible();
    await expect(page.locator('text=param1: value1')).toBeVisible();
    await expect(page.locator('text=param2: value2')).toBeVisible();
  });

  // test('should start the bot when start button is clicked', async ({ page }) => {
  //   await page.route('**/api/bot/start', route => {
  //     route.fulfill({
  //       status: 200,
  //       contentType: 'application/json',
  //       body: JSON.stringify({ message: 'Bot started' }),
  //     });
  //   });

  //   await page.route('**/api/bot/status', route => {
  //     route.fulfill({
  //       status: 200,
  //       contentType: 'application/json',
  //       body: JSON.stringify({ id: 1, status: 'running', last_check_in: new Date().toISOString(), is_active: true }),
  //     });
  //   });

  //   await page.click('button:has-text("Start Bot")');
  //   await expect(page.locator('text=Bot started')).toBeVisible();
  //   await expect(page.locator('text=Bot Status: running')).toBeVisible();
  // });

  // test('should stop the bot when stop button is clicked', async ({ page }) => {
  //   await page.route('**/api/bot/stop', route => {
  //     route.fulfill({
  //       status: 200,
  //       contentType: 'application/json',
  //       body: JSON.stringify({ message: 'Bot stopped' }),
  //     });
  //   });

  //   await page.route('**/api/bot/status', route => {
  //     route.fulfill({
  //       status: 200,
  //       contentType: 'application/json',
  //       body: JSON.stringify({ id: 1, status: 'stopped', last_check_in: new Date().toISOString(), is_active: false }),
  //     });
  //   });

  //   await page.click('button:has-text("Stop Bot")');
  //   await expect(page.locator('text=Bot stopped')).toBeVisible();
  //   await expect(page.locator('text=Bot Status: stopped')).toBeVisible();
  // });

  // test('should show error feedback for failed start action', async ({ page }) => {
  //   await page.route('**/api/bot/start', route => {
  //     route.fulfill({
  //       status: 500,
  //       contentType: 'application/json',
  //       body: JSON.stringify({ detail: 'Failed to start bot' }),
  //     });
  //   });

  //   await page.click('button:has-text("Start Bot")');
  //   await expect(page.locator('text=Failed to start bot')).toBeVisible();
  // });

  // test('should show error feedback for failed stop action', async ({ page }) => {
  //   await page.route('**/api/bot/stop', route => {
  //     route.fulfill({
  //       status: 500,
  //       contentType: 'application/json',
  //       body: JSON.stringify({ detail: 'Failed to stop bot' }),
  //     });
  //   });

  //   await page.click('button:has-text("Stop Bot")');
  //   await expect(page.locator('text=Failed to stop bot')).toBeVisible();
  // });
});