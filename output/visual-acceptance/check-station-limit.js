async page => {
  return page.evaluate(async () => {
    const response = await fetch('/stations?query=Estação&limit=20');
    const stations = await response.json();
    return {
      status: response.status,
      count: stations.length,
      allHaveIdentifiers: stations.every((station) => station.station_id && station.name),
    };
  });
}
