import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    page.on('console', (message) => {
      console.log(`[Browser Console] ${message.type().toUpperCase()}: ${message.text()}`);
    });
  });

  test('should allow a user to sign up and then log in', async ({ page }) => {
    // Navigate to signup page
    await page.goto('/signup');
    await page.waitForLoadState('domcontentloaded'); // Wait for DOM to be ready
    await page.waitForLoadState('networkidle'); // Wait for the page to be fully loaded

    // Fill out signup form
    const randomNum = Math.floor(Math.random() * 10000);
    const username = `testuser${randomNum}`;
    const email = `test${randomNum}@example.com`;

    await page.waitForSelector('input[name="username"]');
    await page.locator('input[name="username"]').click(); // Click before filling
    await page.waitForTimeout(100); // Small delay
    await page.fill('input[name="username"]', username);
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'password123');
    await page.fill('input[name="confirmPassword"]', 'password123');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');
    await page.click('button[type="submit"]');

    // Expect to be redirected to login page after successful signup
    await page.waitForURL('/login', { timeout: 90000 }); // Wait for URL change
    await page.waitForLoadState('networkidle'); // Ensure the page is fully loaded
    await page.waitForSelector('input[name="email"]'); // Wait for email input to ensure page is ready
    await expect(page).toHaveURL('/login');
    await expect(page.locator('div[data-slot="card-title"].text-2xl.font-bold')).toHaveText('Login'); // Ensure the title is present and has text

    // Fill out login form
    await page.waitForSelector('input[name="email"]');
    await page.locator('input[name="email"]').click(); // Click before filling
    await page.waitForTimeout(100); // Small delay
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'password123');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');
    await page.click('button[type="submit"]');

    // Expect to be redirected to home page after successful login (or a dashboard)
    await page.waitForURL('/dashboard', { timeout: 90000 }); // Wait for URL change
    await page.waitForLoadState('networkidle'); // Ensure the page is fully loaded
    await expect(page).toHaveURL('/dashboard');
    // Check for a specific element on the dashboard to confirm login
    await expect(page.locator('div[data-slot="card-title"].text-center')).toHaveText('Bot Dashboard');
  });

  test('should display an error for invalid login credentials', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded'); // Wait for DOM to be ready
    await page.waitForLoadState('networkidle'); // Wait for the page to be fully loaded
    await page.waitForSelector('input[name="email"]'); // Wait for email input

    await page.waitForSelector('input[name="email"]');
    await page.locator('input[name="email"]').click(); // Click before filling
    await page.waitForTimeout(100); // Small delay
    await page.fill('input[name="email"]', 'invalid@example.com'); // Use email for login
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');
    await page.click('button[type="submit"]');

    // Expect an error message to be displayed
    await page.waitForSelector('p.text-red-500', { timeout: 60000 }); // Increased timeout for error message
    await expect(page.locator('p.text-red-500')).toBeVisible();
    await page.waitForTimeout(500); // Small delay to ensure text is rendered
    await expect(page.locator('p.text-red-500')).toContainText('Incorrect username or password'); // Use toContainText for partial match
  });

  test('should display an error for mismatched signup passwords', async ({ page }) => {
    await page.goto('/signup');
    await page.waitForLoadState('domcontentloaded'); // Wait for DOM to be ready
    await page.waitForLoadState('networkidle'); // Wait for the page to be fully loaded
    await page.waitForSelector('input[name="username"]'); // Wait for username input

    await page.waitForSelector('input[name="username"]');
    await page.locator('input[name="username"]').click(); // Click before filling
    await page.waitForTimeout(100); // Small delay
    await page.fill('input[name="username"]', 'newuser');
    await page.fill('input[name="email"]', 'newuser@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.fill('input[name="confirmPassword"]', 'password124'); // Mismatched password, but still valid format
    await page.waitForLoadState('domcontentloaded');
    await page.waitForLoadState('networkidle');
    await page.click('button[type="submit"]');

    // Expect an error message for password mismatch from frontend validation
    const confirmPasswordError = page.locator('input[name="confirmPassword"] + p');
    await expect(confirmPasswordError).toBeVisible();
    await expect(confirmPasswordError).toHaveText('Passwords don\'t match.');
  });
});