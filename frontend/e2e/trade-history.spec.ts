import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';

test.describe('Trade History Page', () => {
  let userId: number;
  let accessToken: string;

  test.beforeAll(() => {
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
    await page.addInitScript(token => {
      localStorage.setItem('authToken', token);
    }, accessToken);

    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error(`Browser console error: ${msg.text()}`);
      }
    });
 
    await page.goto('/trade-history');
    await page.waitForURL('/trade-history', { timeout: 60000 });
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');
  });

  test('should display trade history data', async ({ page }) => {
    await page.route('**/api/trading/orders*', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: "1",
            symbol: "AAPL",
            action: "BUY",
            quantity: 10,
            price: 150.00,
            status: "FILLED",
            timestamp: "2023-01-01T10:00:00Z",
          },
          {
            id: "2",
            symbol: "GOOG",
            action: "SELL",
            quantity: 5,
            price: 1000.00,
            status: "PENDING",
            timestamp: "2023-01-02T11:30:00Z",
          },
        ]),
      });
    });

    await page.reload();

    await expect(page.locator('text=AAPL')).toBeVisible();
    await expect(page.locator('text=BUY')).toBeVisible();
    await expect(page.locator('text=$150.00')).toBeVisible();
    await expect(page.locator('text=GOOG')).toBeVisible();
    await expect(page.locator('text=SELL')).toBeVisible();
    await expect(page.locator('text=$1,000.00')).toBeVisible();
    await expect(page.locator('text=PENDING')).toBeVisible();
  });

  test('should filter trade history by symbol', async ({ page }) => {
    await page.route('**/api/trading/orders?symbol=AAPL*', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: "1",
            symbol: "AAPL",
            action: "BUY",
            quantity: 10,
            price: 150.00,
            status: "FILLED",
            timestamp: "2023-01-01T10:00:00Z",
          },
        ]),
      });
    });

    await page.fill('input[placeholder="AAPL"]', 'AAPL');
    await page.click('button:has-text("Apply Filters")');

    await expect(page.locator('text=AAPL')).toBeVisible();
    await expect(page.locator('text=GOOG')).not.toBeVisible();
  });

  test('should handle no trade history data', async ({ page }) => {
    await page.route('**/api/trading/orders*', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.reload();
    await expect(page.locator('text=No results.')).toBeVisible();
  });

  test('should display error message on API failure', async ({ page }) => {
    await page.route('**/api/trading/orders*', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal Server Error' }),
      });
    });

    await page.reload();
    await expect(page.locator('text=Failed to load trade history. Please try again.')).toBeVisible();
  });
});