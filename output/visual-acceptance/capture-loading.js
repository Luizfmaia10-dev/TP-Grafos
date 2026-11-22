async page => {
  await page.route('**/routes/search', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 3000));
    await route.continue();
  }, { times: 1 });

  await page.evaluate(() => document.querySelector('#route-form').requestSubmit());
  await page.waitForTimeout(120);
  await page.screenshot({
    path: 'output/visual-acceptance/05-loading.png',
    scale: 'css',
    type: 'png',
  });
  await page.getByRole('heading', { name: 'Itinerário' }).waitFor({ timeout: 30000 });
}
