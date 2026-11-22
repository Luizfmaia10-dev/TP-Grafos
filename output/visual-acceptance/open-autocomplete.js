async page => {
  await page.locator('#origin').fill('Estação');
  await page.getByRole('listbox', { name: 'Paradas para origem' }).waitFor({ state: 'visible', timeout: 15000 });
}
