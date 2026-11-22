async page => {
  const chooseStation = async (fieldId, query, name) => {
    const input = page.locator(`#${fieldId}`);
    const current = await input.inputValue();
    if (current === name) return;
    await input.fill(query);
    const option = page.getByRole('option').filter({ hasText: name }).first();
    await option.waitFor({ state: 'visible', timeout: 15000 });
    await option.click();
  };

  await chooseStation('origin', 'Estação Barreiro - Plataforma A6', 'Estação Barreiro - Plataforma A6');
  await chooseStation('destination', 'Avenida Afonso Vaz De Melo 992', 'Avenida Afonso Vaz De Melo 992');
  await page.locator('#departure-time').fill('04:00');
  await page.locator('#departure-time').blur();
}
