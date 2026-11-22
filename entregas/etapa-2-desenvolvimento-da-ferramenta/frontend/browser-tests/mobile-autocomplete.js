async page => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route('**/stations?*', route => route.fulfill({
    json: Array.from({ length: 20 }, (_, i) => ({
      station_id: String(i), name: `Avenida ${i}`, latitude: -19.9, longitude: -43.9,
    })),
  }));
  await page.goto('http://127.0.0.1:8765/');
  await page.locator('#origin').fill('avenida');
  await page.locator('#origin-options [role=option]').nth(19).waitFor();
  await page.locator('#departure-picker-trigger').click({ timeout: 3000 });
  if (await page.locator('#departure-picker').isHidden()) throw new Error('Time picker did not open');
  if (await page.locator('#origin-options').isVisible()) throw new Error('Station options remained open');
  await page.locator('[data-time-cancel]').click();
  await page.locator('#origin').click();
  await page.locator('#origin-options [role=option]').first().waitFor();
  await page.locator('#destination').click();
  await page.locator('#destination-options [role=option]').first().waitFor();
  if (await page.locator('#origin-options').isVisible()) throw new Error('Origin options remained open');
  return 'Mobile autocomplete closes and the time picker opens';
}
