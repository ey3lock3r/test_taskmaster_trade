import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';

test.describe('Dashboard Page', () => {
  let userId: number;
  let accessToken: string;

  test.beforeAll(() => {
    // Run the Python script to set up the user and get tokens
    const scriptPath = '../scripts/setup_test_user.py';
    const output = execSync(`python3 ${scriptPath}`).toString();
    const result = JSON.parse(output);
    
    if (result.error) {
      throw new Error(`Failed to set up test user: ${result.error}`);
    }
    userId = result.user_id;
    accessToken = result.access_token;
  });

  test.beforeEach(async ({ page }) => {
    // Inject the access token into localStorage before navigating
    await page.addInitScript(token => {
      localStorage.setItem('authToken', token); // Corrected key to 'authToken'
    }, accessToken);

    // Listen for console messages and log them
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error(`Browser console error: ${msg.text()}`);
      }
    });
 
     await page.goto('/dashboard');
     await page.waitForURL('/dashboard', { timeout: 60000 }); // Wait for the dashboard URL to load
     await page.waitForLoadState('domcontentloaded');
     await page.waitForLoadState('networkidle');
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

    await page.reload(); // Reload to apply mock

    await expect(page.locator('text=Bot Status: active')).toBeVisible();
    await expect(page.locator('text=param1: value1')).toBeVisible();
    await expect(page.locator('text=param2: value2')).toBeVisible();
  });

  test('should start the bot when start button is clicked', async ({ page }) => {
    await page.route('**/api/bot/start', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Bot started' }),
      });
    });

    await page.route('**/api/bot/status', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 1, status: 'running', last_check_in: new Date().toISOString(), is_active: true }),
      });
    });

    await page.click('button:has-text("Start Bot")');
    await expect(page.locator('text=Bot started')).toBeVisible();
    await expect(page.locator('text=Bot Status: running')).toBeVisible();
  });

  test('should stop the bot when stop button is clicked', async ({ page }) => {
    await page.route('**/api/bot/stop', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Bot stopped' }),
      });
    });

    await page.route('**/api/bot/status', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 1, status: 'stopped', last_check_in: new Date().toISOString(), is_active: false }),
      });
    });

    await page.click('button:has-text("Stop Bot")');
    await expect(page.locator('text=Bot stopped')).toBeVisible();
    await expect(page.locator('text=Bot Status: stopped')).toBeVisible();
  });

  test('should show error feedback for failed start action', async ({ page }) => {
    await page.route('**/api/bot/start', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Failed to start bot' }),
      });
    });

    await page.click('button:has-text("Start Bot")');
    await expect(page.locator('text=Failed to start bot')).toBeVisible();
  });

  test('should show error feedback for failed stop action', async ({ page }) => {
    await page.route('**/api/bot/stop', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Failed to stop bot' }),
      });
    });

    await page.click('button:has-text("Stop Bot")');
    await expect(page.locator('text=Failed to stop bot')).toBeVisible();
  });
});