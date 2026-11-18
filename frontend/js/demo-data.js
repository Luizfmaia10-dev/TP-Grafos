/** Known stops from the first three stop_times of the line 50 sample trip. */
export const DEMO_STATIONS = [
  {
    stationId: "15252270",
    name: "Estação Pampulha - Plataforma G4",
    label: "Estação Pampulha · G4",
    mapName: "Estação Pampulha",
    shortName: "Est. Pampulha",
    platform: "G4",
    district: "Pampulha",
    latitude: -19.84347457,
    longitude: -43.96700111,
  },
  {
    stationId: "14792447",
    name: "Estação Rio de Janeiro - Plataforma 1B",
    label: "Estação Rio de Janeiro · 1B",
    mapName: "Estação Rio de Janeiro",
    shortName: "Est. Rio de Janeiro",
    platform: "1B",
    district: "Centro",
    latitude: -19.9157808,
    longitude: -43.93817059,
  },
  {
    stationId: "14787448",
    name: "Avenida Parana 162",
    label: "Av. Paraná, 162",
    mapName: "Av. Paraná, 162",
    shortName: "Av. Paraná, 162",
    platform: "1A",
    district: "Centro",
    latitude: -19.9176435,
    longitude: -43.94189701,
  },
];

/** Timetable provenance only; serviceId does not identify an inferred weekday. */
export const DEMO_TRIP = {
  routeId: "561929",
  routeShortName: "50",
  routeName: "Estação Pampulha / Centro - Direta",
  tripId: "2662438S307679P075100",
  serviceId: "307679",
  sourceFiles: ["stops.txt", "routes.txt", "trips.txt", "stop_times.txt"],
  stopTimes: [
    { stationId: "15252270", sequence: 1, arrivalTime: "07:51:00", departureTime: "07:51:00" },
    { stationId: "14792447", sequence: 2, arrivalTime: "08:16:51", departureTime: "08:16:51" },
    { stationId: "14787448", sequence: 3, arrivalTime: "08:20:16", departureTime: "08:20:16" },
  ],
};
