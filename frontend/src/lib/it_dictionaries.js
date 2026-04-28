// Italian-language nationality / country / province dictionaries used across forms.
// Single source of truth — import from any page that needs autocomplete.

// Nationalities — Italian feminine form (used for "Cittadinanza")
export const NATIONALITIES = [
  "Italiana", "Albanese", "Algerina", "Argentina", "Armena", "Australiana",
  "Austriaca", "Bangladese", "Belga", "Bielorussa", "Boliviana", "Bosniaca",
  "Brasiliana", "Britannica", "Bulgara", "Camerunese", "Canadese", "Cilena",
  "Cinese", "Colombiana", "Coreana", "Croata", "Cubana", "Danese",
  "Dominicana", "Ecuadoriana", "Egiziana", "Eritrea", "Estone", "Etiope",
  "Filippina", "Finlandese", "Francese", "Georgiana", "Ghanese", "Giapponese",
  "Giordana", "Greca", "Guatemalteca", "Haitiana", "Hondureña", "Indiana",
  "Indonesiana", "Iraniana", "Irachena", "Irlandese", "Islandese", "Israeliana",
  "Kazaka", "Keniana", "Kosovara", "Kirghisa", "Lettone", "Libanese",
  "Liberiana", "Libica", "Lituana", "Lussemburghese", "Macedone", "Malese",
  "Maliana", "Maltese", "Marocchina", "Messicana", "Moldava", "Mongola",
  "Montenegrina", "Mozambicana", "Nepalese", "Neozelandese", "Nicaraguense", "Nigeriana",
  "Norvegese", "Olandese", "Pakistana", "Panamense", "Paraguaiana", "Peruviana",
  "Polacca", "Portoghese", "Romena", "Russa", "Salvadoregna", "Saudita",
  "Senegalese", "Serba", "Singaporeana", "Siriana", "Slovacca", "Slovena",
  "Somala", "Spagnola", "Sri Lankese", "Statunitense", "Sudafricana", "Sudanese",
  "Svedese", "Svizzera", "Tailandese", "Taiwanese", "Tanzaniana", "Tedesca",
  "Tunisina", "Turca", "Ucraina", "Ugandese", "Ungherese", "Uruguaiana",
  "Uzbeka", "Venezuelana", "Vietnamita", "Yemenita", "Zambiana", "Zimbabwese",
];

// Countries — Italian full names (used for "Paese di nascita")
export const COUNTRIES = [
  "Italia", "Albania", "Algeria", "Argentina", "Armenia", "Australia",
  "Austria", "Bangladesh", "Belgio", "Bielorussia", "Bolivia", "Bosnia ed Erzegovina",
  "Brasile", "Bulgaria", "Camerun", "Canada", "Cile", "Cina", "Colombia",
  "Corea del Sud", "Croazia", "Cuba", "Danimarca", "Repubblica Dominicana",
  "Ecuador", "Egitto", "Eritrea", "Estonia", "Etiopia", "Filippine",
  "Finlandia", "Francia", "Georgia", "Ghana", "Giappone", "Giordania", "Grecia",
  "Guatemala", "Haiti", "Honduras", "India", "Indonesia", "Iran", "Iraq",
  "Irlanda", "Islanda", "Israele", "Kazakistan", "Kenya", "Kosovo", "Kirghizistan",
  "Lettonia", "Libano", "Liberia", "Libia", "Lituania", "Lussemburgo",
  "Macedonia del Nord", "Malesia", "Mali", "Malta", "Marocco", "Messico",
  "Moldavia", "Mongolia", "Montenegro", "Mozambico", "Nepal", "Nuova Zelanda",
  "Nicaragua", "Nigeria", "Norvegia", "Paesi Bassi", "Pakistan", "Panama",
  "Paraguay", "Perù", "Polonia", "Portogallo", "Regno Unito", "Romania",
  "Russia", "El Salvador", "Arabia Saudita", "Senegal", "Serbia", "Singapore",
  "Siria", "Slovacchia", "Slovenia", "Somalia", "Spagna", "Sri Lanka",
  "Stati Uniti", "Sudafrica", "Sudan", "Svezia", "Svizzera",
  "Thailandia", "Taiwan", "Tanzania", "Germania", "Tunisia", "Turchia",
  "Ucraina", "Uganda", "Ungheria", "Uruguay", "Uzbekistan", "Venezuela",
  "Vietnam", "Yemen", "Zambia", "Zimbabwe",
];

// Italian provinces (sigla → name)
export const PROVINCES = [
  ["AG", "Agrigento"], ["AL", "Alessandria"], ["AN", "Ancona"], ["AO", "Aosta"],
  ["AR", "Arezzo"], ["AP", "Ascoli Piceno"], ["AT", "Asti"], ["AV", "Avellino"],
  ["BA", "Bari"], ["BT", "Barletta-Andria-Trani"], ["BL", "Belluno"], ["BN", "Benevento"],
  ["BG", "Bergamo"], ["BI", "Biella"], ["BO", "Bologna"], ["BZ", "Bolzano"],
  ["BS", "Brescia"], ["BR", "Brindisi"], ["CA", "Cagliari"], ["CL", "Caltanissetta"],
  ["CB", "Campobasso"], ["CE", "Caserta"], ["CT", "Catania"], ["CZ", "Catanzaro"],
  ["CH", "Chieti"], ["CO", "Como"], ["CS", "Cosenza"], ["CR", "Cremona"],
  ["KR", "Crotone"], ["CN", "Cuneo"], ["EN", "Enna"], ["FM", "Fermo"],
  ["FE", "Ferrara"], ["FI", "Firenze"], ["FG", "Foggia"], ["FC", "Forlì-Cesena"],
  ["FR", "Frosinone"], ["GE", "Genova"], ["GO", "Gorizia"], ["GR", "Grosseto"],
  ["IM", "Imperia"], ["IS", "Isernia"], ["AQ", "L'Aquila"], ["SP", "La Spezia"],
  ["LT", "Latina"], ["LE", "Lecce"], ["LC", "Lecco"], ["LI", "Livorno"],
  ["LO", "Lodi"], ["LU", "Lucca"], ["MC", "Macerata"], ["MN", "Mantova"],
  ["MS", "Massa-Carrara"], ["MT", "Matera"], ["ME", "Messina"], ["MI", "Milano"],
  ["MO", "Modena"], ["MB", "Monza e Brianza"], ["NA", "Napoli"], ["NO", "Novara"],
  ["NU", "Nuoro"], ["OR", "Oristano"], ["PD", "Padova"], ["PA", "Palermo"],
  ["PR", "Parma"], ["PV", "Pavia"], ["PG", "Perugia"], ["PU", "Pesaro e Urbino"],
  ["PE", "Pescara"], ["PC", "Piacenza"], ["PI", "Pisa"], ["PT", "Pistoia"],
  ["PN", "Pordenone"], ["PZ", "Potenza"], ["PO", "Prato"], ["RG", "Ragusa"],
  ["RA", "Ravenna"], ["RC", "Reggio Calabria"], ["RE", "Reggio Emilia"], ["RI", "Rieti"],
  ["RN", "Rimini"], ["RM", "Roma"], ["RO", "Rovigo"], ["SA", "Salerno"],
  ["SS", "Sassari"], ["SV", "Savona"], ["SI", "Siena"], ["SR", "Siracusa"],
  ["SO", "Sondrio"], ["SU", "Sud Sardegna"], ["TA", "Taranto"], ["TE", "Teramo"],
  ["TR", "Terni"], ["TO", "Torino"], ["TP", "Trapani"], ["TN", "Trento"],
  ["TV", "Treviso"], ["TS", "Trieste"], ["UD", "Udine"], ["VA", "Varese"],
  ["VE", "Venezia"], ["VB", "Verbano-Cusio-Ossola"], ["VC", "Vercelli"], ["VR", "Verona"],
  ["VV", "Vibo Valentia"], ["VI", "Vicenza"], ["VT", "Viterbo"],
];

// Get nationality matches for a query (case-insensitive substring search).
export const searchNationalities = (q) => {
  if (!q) return NATIONALITIES.slice(0, 20);
  const ql = q.toLowerCase();
  return NATIONALITIES.filter((n) => n.toLowerCase().includes(ql)).slice(0, 30);
};

export const searchCountries = (q) => {
  if (!q) return COUNTRIES.slice(0, 20);
  const ql = q.toLowerCase();
  return COUNTRIES.filter((n) => n.toLowerCase().includes(ql)).slice(0, 30);
};

export const searchProvinces = (q) => {
  if (!q) return PROVINCES;
  const ql = q.toLowerCase();
  return PROVINCES.filter(([s, n]) => s.toLowerCase().includes(ql) || n.toLowerCase().includes(ql));
};
