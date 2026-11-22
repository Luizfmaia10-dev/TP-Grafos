async page => {
  await page.route('**/routes/search', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'no-route',
        service_date: '2026-11-17',
        departure_time: '04:00',
        origin: {
          station_id: '15140072',
          name: 'Estação Barreiro - Plataforma A6',
          latitude: -19.976,
          longitude: -44.026,
        },
        destination: {
          station_id: '14788235',
          name: 'Avenida Afonso Vaz De Melo 992',
          latitude: -19.978,
          longitude: -44.024,
        },
        route: null,
      }),
    });
  }, { times: 1 });
  await page.getByRole('button', { name: 'Calcular trajeto' }).click();
  await page.getByRole('heading', { name: 'Nenhum trajeto encontrado' }).waitFor();
}
