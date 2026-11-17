import { test, expect, Page } from '@playwright/test';

const logoutUser = async (page: Page) => {
  await page.click('button:has(svg.lucide-chevron-down)');
  await page.click('button:has-text("Sign out")');
  await page.waitForURL('**/login');
  await expect(page.getByText('Sign in to your account')).toBeVisible();
};

test.describe('AttendAI Production Verification Suite', () => {

  test('1. Administrator Full Platform Navigation & Workflow', async ({ page }) => {
    // Automatically accept any dialogs if triggered
    page.on('dialog', async (dialog) => {
      await dialog.dismiss();
    });

    // 1. Visit Login
    await page.goto('/');
    await expect(page.getByText('AttendAI', { exact: true })).toBeVisible();
    await expect(page.getByText('Intelligent Workforce. Smarter Decisions.')).toBeVisible();

    // 2. Click Admin Demo Account button
    await page.click('button:has-text("Admin")');
    await page.click('button[type="submit"]');

    // 3. Verify Dashboard
    await page.waitForURL('**/');
    await expect(page.getByRole('heading', { name: 'Workforce Dashboard' })).toBeVisible();
    await expect(page.getByText('Active headcount')).toBeVisible();
    await expect(page.getByText('Attendance & Late Trends')).toBeVisible();
    await expect(page.getByText('Department Rates')).toBeVisible();

    // 4. Employees Page
    await page.click('nav a:has-text("Employees")');
    await page.waitForURL('**/employees');
    await expect(page.getByRole('heading', { name: 'Employee Directory' })).toBeVisible();
    await expect(page.getByPlaceholder(/search by name/i)).toBeVisible();

    // Search an employee
    const searchInput = page.getByPlaceholder(/search by name/i);
    await searchInput.fill('Sarah');
    await page.waitForTimeout(400);

    // 5. Attendance Page
    await page.click('nav a:has-text("Attendance")');
    await page.waitForURL('**/attendance');
    await expect(page.getByRole('heading', { name: 'Time & Attendance' })).toBeVisible();
    await expect(page.getByText(/Punch tracking, worked hours/i)).toBeVisible();

    // 6. Shifts & Scheduling Page
    await page.click('nav a:has-text("Shifts & Scheduling")');
    await page.waitForURL('**/shifts');
    await expect(page.getByRole('heading', { name: 'Shifts & Scheduling' })).toBeVisible();
    await expect(page.getByText('General Shift')).toBeVisible();

    // 7. Anomaly Detection Page
    await page.click('nav a:has-text("Anomaly Detection")');
    await page.waitForURL('**/anomalies');
    await expect(page.getByRole('heading', { name: 'Workforce Anomaly Detection' })).toBeVisible();
    await expect(page.getByText('Run Detection Pipeline')).toBeVisible();

    // 8. AI Assistant Page
    await page.click('nav a:has-text("AI Assistant")');
    await page.waitForURL('**/ai');
    await expect(page.getByText('AttendAI Workforce Intelligence')).toBeVisible();
    await expect(page.getByPlaceholder(/Ask AttendAI/i)).toBeVisible();

    // Send AI Question
    await page.getByPlaceholder(/Ask AttendAI/i).fill('Show late arrivals');
    await page.click('form button[type="submit"]');
    await page.waitForTimeout(1500);
    await expect(page.locator('.space-y-4').first()).toBeVisible();

    // 9. Policies & Documents Page
    await page.click('nav a:has-text("Policies & Documents")');
    await page.waitForURL('**/policies');
    await expect(page.getByRole('heading', { name: 'Policies & Guidelines' })).toBeVisible();
    await expect(page.getByPlaceholder(/grace period/i)).toBeVisible();

    // 10. Analytics & Reports Page
    await page.click('nav a:has-text("Analytics & Reports")');
    await page.waitForURL('**/analytics');
    await expect(page.getByRole('heading', { name: 'Analytics & Workforce Reports' })).toBeVisible();
    await expect(page.getByText('Download CSV')).toBeVisible();
    await expect(page.getByText('Download XLSX')).toBeVisible();

    // 11. Settings Page
    await page.click('nav a:has-text("Settings")');
    await page.waitForURL('**/settings');
    await expect(page.getByRole('heading', { name: 'System Settings & Diagnostics' })).toBeVisible();

    // 12. Help & Support Page
    await page.click('nav a:has-text("Help & Support")');
    await page.waitForURL('**/help');
    await expect(page.getByRole('heading', { name: 'Help & Knowledge Base' })).toBeVisible();

    // 13. Logout
    await logoutUser(page);
  });

  test('2. HR Manager Scope & Functionality', async ({ page }) => {
    page.on('dialog', async (dialog) => {
      await dialog.dismiss();
    });

    await page.goto('/login');

    // Quick fill HR Manager
    await page.click('button:has-text("HR Mgr")');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/');
    await expect(page.getByRole('heading', { name: 'Workforce Dashboard' })).toBeVisible();

    // HR can access employees
    await page.click('nav a:has-text("Employees")');
    await page.waitForURL('**/employees');
    await expect(page.getByRole('heading', { name: 'Employee Directory' })).toBeVisible();

    // HR can access leave
    await page.click('nav a:has-text("Leave")');
    await page.waitForURL('**/leave');
    await expect(page.getByRole('heading', { name: 'Leave Management' })).toBeVisible();

    // Logout
    await logoutUser(page);
  });

  test('3. Employee Dedicated Portal, Punch Status & Scope Boundary', async ({ page }) => {
    page.on('dialog', async (dialog) => {
      await dialog.dismiss();
    });

    await page.goto('/login');

    // Quick fill Employee
    await page.click('button:has-text("Employee")');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/');

    // 1. Verify Personal Portal Header
    await expect(page.getByRole('heading', { name: /Welcome back/i })).toBeVisible();
    await expect(page.getByText(/Personal Workforce Portal/i)).toBeVisible();
    await expect(page.getByText(/Shift: General/i)).toBeVisible();

    // 2. Verify Restricted Navigation Boundary (Employees, Shifts, Anomalies, Analytics should NOT exist in nav)
    await expect(page.locator('nav a:has-text("Employees")')).toHaveCount(0);
    await expect(page.locator('nav a:has-text("Shifts & Scheduling")')).toHaveCount(0);
    await expect(page.locator('nav a:has-text("Anomaly Detection")')).toHaveCount(0);
    await expect(page.locator('nav a:has-text("Analytics & Reports")')).toHaveCount(0);

    // 3. Employee Clock Status Verification
    await expect(page.getByText(/Status:/i)).toBeVisible();
    await expect(page.getByText(/Shift Completed|Not Clocked In|Actively Working/i)).toBeVisible();

    // 4. Employee Leave Page
    await page.click('nav a:has-text("Leave")');
    await page.waitForURL('**/leave');
    await expect(page.getByRole('heading', { name: 'Leave Management' })).toBeVisible();
    await expect(page.getByText('Apply for Leave')).toBeVisible();

    // 5. Employee Policy Search
    await page.click('nav a:has-text("Policies & Documents")');
    await page.waitForURL('**/policies');
    await expect(page.getByRole('heading', { name: 'Policies & Guidelines' })).toBeVisible();
    await expect(page.getByPlaceholder(/grace period/i)).toBeVisible();

    // 6. Direct Forbidden URL Access Check
    await page.goto('/anomalies');
    await page.waitForURL('**/403');
    await expect(page.getByText('Access Denied')).toBeVisible();

    // Return to dashboard and logout
    await page.click('a:has-text("Return to Dashboard")');
    await page.waitForURL('**/');
    await logoutUser(page);
  });

});
