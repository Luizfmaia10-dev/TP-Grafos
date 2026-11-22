async page => {
  await page.getByRole('button', { name: 'Cancelar' }).click();
}
