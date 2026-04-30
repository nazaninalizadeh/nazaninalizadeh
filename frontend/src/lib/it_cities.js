// Top Italian cities with their province sigla — used for autocomplete in
// "Luogo di Nascita" / "Comune di nascita" fields. The province on the right
// is what fills the "Provincia di Nascita" / "Provincia o nazione estera"
// field automatically when a city is picked.
export const ITALIAN_CITIES = [
  ["Roma", "RM"], ["Milano", "MI"], ["Napoli", "NA"], ["Torino", "TO"],
  ["Palermo", "PA"], ["Genova", "GE"], ["Bologna", "BO"], ["Firenze", "FI"],
  ["Bari", "BA"], ["Catania", "CT"], ["Venezia", "VE"], ["Verona", "VR"],
  ["Messina", "ME"], ["Padova", "PD"], ["Trieste", "TS"], ["Brescia", "BS"],
  ["Taranto", "TA"], ["Prato", "PO"], ["Reggio Calabria", "RC"], ["Modena", "MO"],
  ["Reggio Emilia", "RE"], ["Parma", "PR"], ["Perugia", "PG"], ["Livorno", "LI"],
  ["Ravenna", "RA"], ["Cagliari", "CA"], ["Foggia", "FG"], ["Rimini", "RN"],
  ["Salerno", "SA"], ["Ferrara", "FE"], ["Sassari", "SS"], ["Latina", "LT"],
  ["Giugliano in Campania", "NA"], ["Monza", "MB"], ["Siracusa", "SR"], ["Pescara", "PE"],
  ["Bergamo", "BG"], ["Forlì", "FC"], ["Trento", "TN"], ["Vicenza", "VI"],
  ["Terni", "TR"], ["Bolzano", "BZ"], ["Novara", "NO"], ["Piacenza", "PC"],
  ["Ancona", "AN"], ["Andria", "BT"], ["Arezzo", "AR"], ["Udine", "UD"],
  ["Cesena", "FC"], ["Lecce", "LE"], ["Pesaro", "PU"], ["Barletta", "BT"],
  ["Alessandria", "AL"], ["La Spezia", "SP"], ["Pistoia", "PT"], ["Pisa", "PI"],
  ["Catanzaro", "CZ"], ["Guidonia Montecelio", "RM"], ["Lucca", "LU"], ["Brindisi", "BR"],
  ["Torre del Greco", "NA"], ["Treviso", "TV"], ["Busto Arsizio", "VA"], ["Como", "CO"],
  ["Marsala", "TP"], ["Grosseto", "GR"], ["Sesto San Giovanni", "MI"],
  ["Pozzuoli", "NA"], ["Varese", "VA"], ["Fiumicino", "RM"], ["Casoria", "NA"],
  ["Asti", "AT"], ["Cinisello Balsamo", "MI"], ["Caserta", "CE"], ["Gela", "CL"],
  ["Aprilia", "LT"], ["Ragusa", "RG"], ["Pavia", "PV"], ["Cremona", "CR"],
  ["Carpi", "MO"], ["Quartu Sant'Elena", "CA"], ["Lamezia Terme", "CZ"],
  ["Altamura", "BA"], ["Imola", "BO"], ["L'Aquila", "AQ"], ["Trapani", "TP"],
  ["Massa", "MS"], ["Carrara", "MS"], ["Viterbo", "VT"], ["Cosenza", "CS"],
  ["Potenza", "PZ"], ["Castellammare di Stabia", "NA"], ["Afragola", "NA"],
  ["Vittoria", "RG"], ["Fano", "PU"], ["Crotone", "KR"], ["Vigevano", "PV"],
  ["Acireale", "CT"], ["Bisceglie", "BT"], ["Bagheria", "PA"], ["Tivoli", "RM"],
  ["Rho", "MI"], ["Cuneo", "CN"], ["Velletri", "RM"], ["Battipaglia", "SA"],
  ["Pordenone", "PN"], ["Pomigliano d'Arco", "NA"], ["Foligno", "PG"],
  ["Manfredonia", "FG"], ["Civitavecchia", "RM"], ["Faenza", "RA"],
  ["Cerignola", "FG"], ["Savona", "SV"], ["Rivoli", "TO"], ["San Severo", "FG"],
  ["Sassuolo", "MO"], ["Rovigo", "RO"], ["Belluno", "BL"], ["Matera", "MT"],
  ["Caltanissetta", "CL"], ["Imperia", "IM"], ["Avellino", "AV"], ["Benevento", "BN"],
  ["Macerata", "MC"], ["Fermo", "FM"], ["Ascoli Piceno", "AP"], ["Mantova", "MN"],
  ["Lodi", "LO"], ["Sondrio", "SO"], ["Lecco", "LC"], ["Verbania", "VB"],
  ["Aosta", "AO"], ["Nuoro", "NU"], ["Oristano", "OR"], ["Olbia", "SS"],
  ["Carbonia", "SU"], ["Iglesias", "SU"], ["Vibo Valentia", "VV"], ["Isernia", "IS"],
  ["Campobasso", "CB"], ["Frosinone", "FR"], ["Rieti", "RI"], ["Chieti", "CH"],
  ["Teramo", "TE"], ["Enna", "EN"], ["Agrigento", "AG"],
];

export const searchCities = (q) => {
  if (!q) return ITALIAN_CITIES.slice(0, 25);
  const ql = q.toLowerCase();
  return ITALIAN_CITIES.filter(([city, prov]) =>
    city.toLowerCase().includes(ql) || prov.toLowerCase() === ql
  ).slice(0, 30);
};
