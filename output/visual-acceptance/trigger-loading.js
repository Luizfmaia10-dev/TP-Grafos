async page => {
  await page.route('**/routes/search', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1200));
    await route.continue();
  }, { times: 1 });
  await page.getByRole('button', { name: 'Calcular trajeto' }).click();
  await page.waitForTimeout(150);
}
