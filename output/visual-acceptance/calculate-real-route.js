async page => {
  await page.getByRole('button', { name: 'Calcular trajeto' }).click();
  await page.getByRole('heading', { name: 'Itinerário' }).waitFor({ timeout: 30000 });
}
