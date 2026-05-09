import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
    await page.goto('http://localhost:5173/');
    await expect(page).toHaveTitle(/AEGIS CYBERSECURITY PLATFORM/);
});

test('dashboard loads and shows sidebar link', async ({ page }) => {
    await page.goto('http://localhost:5173/');
    const dashLink = page.locator('nav a', { hasText: 'Dashboard' });
    await expect(dashLink).toBeVisible();
});
