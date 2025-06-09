import { test, expect } from '@playwright/test';

test.describe('Current Positions Page', () => {
  test.beforeEach(async ({ page }) => {
    // Assuming authentication is required to access the page
    // You might need to implement a login flow here or use a global setup
    await page.goto('http://localhost:3000/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('http://localhost:3000/dashboard'); // Wait for redirect to dashboard after login

    await page.goto('http://localhost:3000/current-positions');
    await page.waitForLoadState('networkidle');
  });

  test('should display current positions data', async ({ page }) => {
    // Mock the API response for positions
    await page.route('**/api/trading/positions', async route => {
      const mockPositions = [
        {
          optionContract: 'SPY240621C00450000',
          underlying: 'SPY',
          quantity: 10,
          averageEntryPrice: 1.50,
          legType: 'Call'
        },
        {
          optionContract: 'AAPL240719P00180000',
          underlying: 'AAPL',
          quantity: 5,
          averageEntryPrice: 2.25,
          legType: 'Put'
        }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPositions),
      });
    });

    await page.reload(); // Reload to trigger the mocked API call

    await expect(page.locator('h1')).toHaveText('Current Positions');
    await expect(page.getByText('SPY240621C00450000')).toBeVisible();
    await expect(page.getByText('AAPL240719P00180000')).toBeVisible();
    await expect(page.getByText('SPY')).toBeVisible();
    await expect(page.getByText('AAPL')).toBeVisible();
    await expect(page.getByText('10')).toBeVisible();
    await expect(page.getByText('5')).toBeVisible();
    await expect(page.getByText('$1.50')).toBeVisible();
    await expect(page.getByText('$2.25')).toBeVisible();
    await expect(page.getByText('Call')).toBeVisible();
    await expect(page.getByText('Put')).toBeVisible();
  });

  test('should handle no current positions data', async ({ page }) => {
    // Mock an empty API response
    await page.route('**/api/trading/positions', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.reload(); // Reload to trigger the mocked API call

    await expect(page.getByText('No current positions found.')).toBeVisible();
  });

  test('should display error message on API failure', async ({ page }) => {
    // Mock an API error response
    await page.route('**/api/trading/positions', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Internal Server Error' }),
      });
    });

    await page.reload(); // Reload to trigger the mocked API call

    await expect(page.getByText('Error: HTTP error! status: 500')).toBeVisible();
  });

  test('should filter trade history by underlying', async ({ page }) => {
    // Mock the API response for positions
    await page.route('**/api/trading/positions', async route => {
      const mockPositions = [
        {
          optionContract: 'SPY240621C00450000',
          underlying: 'SPY',
          quantity: 10,
          averageEntryPrice: 1.50,
          legType: 'Call'
        },
        {
          optionContract: 'AAPL240719P00180000',
          underlying: 'AAPL',
          quantity: 5,
          averageEntryPrice: 2.25,
          legType: 'Put'
        },
        {
          optionContract: 'GOOG240816C00150000',
          underlying: 'GOOG',
          quantity: 2,
          averageEntryPrice: 3.00,
          legType: 'Call'
        }
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPositions),
      });
    });

    await page.reload(); // Reload to trigger the mocked API call

    // Filter by 'SPY'
    await page.fill('input[placeholder="Filter underlying..."]', 'SPY');
    await expect(page.getByText('SPY240621C00450000')).toBeVisible();
    await expect(page.getByText('AAPL240719P00180000')).not.toBeVisible();
    await expect(page.getByText('GOOG240816C00150000')).not.toBeVisible();

    // Clear filter and filter by 'AAPL'
    await page.fill('input[placeholder="Filter underlying..."]', '');
    await page.fill('input[placeholder="Filter underlying..."]', 'AAPL');
    await expect(page.getByText('SPY240621C00450000')).not.toBeVisible();
    await expect(page.getByText('AAPL240719P00180000')).toBeVisible();
    await expect(page.getByText('GOOG240816C00150000')).not.toBeVisible();

    // Clear filter and filter by 'GOOG'
    await page.fill('input[placeholder="Filter underlying..."]', '');
    await page.fill('input[placeholder="Filter underlying..."]', 'GOOG');
    await expect(page.getByText('SPY240621C00450000')).not.toBeVisible();
    await expect(page.getByText('AAPL240719P00180000')).not.toBeVisible();
    await expect(page.getByText('GOOG240816C00150000')).toBeVisible();
  });
});