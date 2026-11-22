async page => {
  await page.route('**/routes/search', async (route) => {
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Serviço temporariamente indisponível.' }),
    });
  }, { times: 1 });
  await page.getByRole('button', { name: 'Calcular trajeto' }).click();
  await page.getByRole('heading', { name: 'Serviço indisponível' }).waitFor();
}
