// static/js/climate_data_2025.js

const CLIMATE_DATA_2025 = {
  "climate_data_2025": {
    "months": [
      { "month": "January",   "enso": "La Niña", "oni": -0.7, "storms": 0,  "sst": -0.6, "stress": 3.2 },
      { "month": "February",  "enso": "La Niña", "oni": -0.8, "storms": 0,  "sst": -0.7, "stress": 3.5 },
      { "month": "March",     "enso": "La Niña", "oni": -0.9, "storms": 1,  "sst": -0.8, "stress": 4.1 },
      { "month": "April",     "enso": "Neutral", "oni": -0.5, "storms": 1,  "sst": -0.4, "stress": 4.0 },
      { "month": "May",       "enso": "Neutral", "oni": -0.2, "storms": 2,  "sst": -0.1, "stress": 4.8 },
      { "month": "June",      "enso": "Neutral", "oni": 0.0,  "storms": 4,  "sst": 0.1,  "stress": 6.2 },
      { "month": "July",      "enso": "Neutral", "oni": 0.2,  "storms": 5,  "sst": 0.3,  "stress": 7.1 },
      { "month": "August",    "enso": "Neutral", "oni": 0.1,  "storms": 6,  "sst": 0.2,  "stress": 7.8 },
      { "month": "September", "enso": "Neutral", "oni": -0.1, "storms": 7,  "sst": 0.0,  "stress": 8.5 },
      { "month": "October",   "enso": "La Niña", "oni": -0.4, "storms": 5,  "sst": -0.3, "stress": 8.9 },
      { "month": "November",  "enso": "La Niña", "oni": -0.6, "storms": 3,  "sst": -0.5, "stress": 8.7 },
      { "month": "December",  "enso": "La Niña", "oni": -0.7, "storms": 1,  "sst": -0.6, "stress": 7.9 }
    ]
  }
};

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.CLIMATE_DATA_2025 = CLIMATE_DATA_2025;
    console.log('✅ CLIMATE_DATA_2025 loaded successfully');
}

