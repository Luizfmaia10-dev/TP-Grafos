async page => {
  const clear = page.getByRole('button', { name: 'Limpar origem' });
  if (await clear.isVisible()) {
    await clear.click();
  }
  await page.waitForTimeout(100);

  return page.evaluate(() => ({
    origin: document.querySelector('#origin').value,
    destination: document.querySelector('#destination').value,
    originOptionsHidden: document.querySelector('#origin-options').hidden,
    resultVisible: !document.querySelector('#route-itinerary').hidden,
    activeElement: document.activeElement?.id || document.activeElement?.tagName,
  }));
}
