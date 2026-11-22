async page => {
  await page.getByRole('button', { name: 'Escolher horário' }).click();
  await page.getByRole('dialog').waitFor({ state: 'visible' });
}
