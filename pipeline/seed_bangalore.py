"""Generate real Bengaluru POIs and residential project dataset for Flat Finder pipeline.

Produces pipeline/out/bangalore/{mb_projects.json, osm_pois.json, osm_areas.geojson, osm_buildings.geojson}
so that `python3 pipeline/build_city.py bangalore` builds the complete web dataset.
"""
import json
import math
import pathlib
import random
import re

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "out" / "bangalore"

# Real Bengaluru POIs (Namma Metro, parks/lakes, hospitals, malls, schools) with accurate coordinates
POIS = [
    # Namma Metro Purple Line
    {"k": "metro", "name": "Whitefield (Kadugodi) Metro", "lat": 12.9958, "lng": 77.7576},
    {"k": "metro", "name": "Hopefarm Channasandra Metro", "lat": 12.9873, "lng": 77.7536},
    {"k": "metro", "name": "Kadugodi Tree Park Metro", "lat": 12.9857, "lng": 77.7466},
    {"k": "metro", "name": "Pattandur Agrahara Metro", "lat": 12.9874, "lng": 77.7377},
    {"k": "metro", "name": "Sri Sathya Sai Hospital Metro", "lat": 12.9812, "lng": 77.7276},
    {"k": "metro", "name": "Nallurhalli Metro", "lat": 12.9765, "lng": 77.7248},
    {"k": "metro", "name": "Kundalahalli Metro", "lat": 12.9776, "lng": 77.7155},
    {"k": "metro", "name": "Seetharampalya Metro", "lat": 12.9808, "lng": 77.7087},
    {"k": "metro", "name": "Hoodi Metro", "lat": 12.9888, "lng": 77.7113},
    {"k": "metro", "name": "Garudacharpalya Metro", "lat": 12.9934, "lng": 77.7037},
    {"k": "metro", "name": "Singayyanapalya Metro", "lat": 12.9960, "lng": 77.6920},
    {"k": "metro", "name": "KR Puram Metro", "lat": 12.9999, "lng": 77.6775},
    {"k": "metro", "name": "Benniganahalli Metro", "lat": 12.9965, "lng": 77.6683},
    {"k": "metro", "name": "Baiyappanahalli Metro", "lat": 12.9907, "lng": 77.6525},
    {"k": "metro", "name": "Swami Vivekananda Road Metro", "lat": 12.9858, "lng": 77.6449},
    {"k": "metro", "name": "Indiranagar Metro", "lat": 12.9783, "lng": 77.6387},
    {"k": "metro", "name": "Halasuru Metro", "lat": 12.9765, "lng": 77.6267},
    {"k": "metro", "name": "Trinity Metro", "lat": 12.9730, "lng": 77.6170},
    {"k": "metro", "name": "MG Road Metro", "lat": 12.9756, "lng": 77.6066},
    {"k": "metro", "name": "Cubbon Park Metro", "lat": 12.9809, "lng": 77.5975},
    {"k": "metro", "name": "Majestic Interchange Metro", "lat": 12.9756, "lng": 77.5728},
    {"k": "metro", "name": "Vijayanagar Metro", "lat": 12.9709, "lng": 77.5374},
    {"k": "metro", "name": "Mysore Road Metro", "lat": 12.9467, "lng": 77.5300},
    {"k": "metro", "name": "Kengeri Metro", "lat": 12.9079, "lng": 77.4765},
    # Namma Metro Green Line
    {"k": "metro", "name": "Madavara Metro", "lat": 13.0568, "lng": 77.4737},
    {"k": "metro", "name": "Nagasandra Metro", "lat": 13.0480, "lng": 77.5001},
    {"k": "metro", "name": "Dasarahalli Metro", "lat": 13.0434, "lng": 77.5125},
    {"k": "metro", "name": "Peenya Industry Metro", "lat": 13.0363, "lng": 77.5255},
    {"k": "metro", "name": "Yeshwanthpur Metro", "lat": 13.0232, "lng": 77.5499},
    {"k": "metro", "name": "Sandal Soap Factory Metro", "lat": 13.0147, "lng": 77.5540},
    {"k": "metro", "name": "Mahalakshmi Metro", "lat": 13.0082, "lng": 77.5488},
    {"k": "metro", "name": "Rajajinagar Metro", "lat": 13.0003, "lng": 77.5496},
    {"k": "metro", "name": "Mantri Square Sampige Road Metro", "lat": 12.9905, "lng": 77.5707},
    {"k": "metro", "name": "Lalbagh Metro", "lat": 12.9464, "lng": 77.5800},
    {"k": "metro", "name": "South End Circle Metro", "lat": 12.9383, "lng": 77.5801},
    {"k": "metro", "name": "Jayanagar Metro", "lat": 12.9295, "lng": 77.5802},
    {"k": "metro", "name": "RV Road Interchange Metro", "lat": 12.9214, "lng": 77.5801},
    {"k": "metro", "name": "Banashankari Metro", "lat": 12.9154, "lng": 77.5736},
    {"k": "metro", "name": "JP Nagar Metro", "lat": 12.9073, "lng": 77.5731},
    {"k": "metro", "name": "Yelachenahalli Metro", "lat": 12.8960, "lng": 77.5702},
    {"k": "metro", "name": "Konanakunte Cross Metro", "lat": 12.8846, "lng": 77.5629},
    {"k": "metro", "name": "Doddakallasandra Metro", "lat": 12.8842, "lng": 77.5528},
    {"k": "metro", "name": "Vajarahalli Metro", "lat": 12.8774, "lng": 77.5447},
    {"k": "metro", "name": "Thalaghattapura Metro", "lat": 12.8712, "lng": 77.5384},
    {"k": "metro", "name": "Silk Institute Metro", "lat": 12.8617, "lng": 77.5300},
    # Namma Metro Yellow & Blue Lines
    {"k": "metro", "name": "Jayadeva Interchange Metro", "lat": 12.9165, "lng": 77.5997},
    {"k": "metro", "name": "BTM Layout Metro", "lat": 12.9165, "lng": 77.6085},
    {"k": "metro", "name": "Central Silk Board Metro", "lat": 12.9173, "lng": 77.6228},
    {"k": "metro", "name": "HSR Layout Metro", "lat": 12.9168, "lng": 77.6388},
    {"k": "metro", "name": "Agara Metro", "lat": 12.9222, "lng": 77.6485},
    {"k": "metro", "name": "Iblur Metro", "lat": 12.9211, "lng": 77.6619},
    {"k": "metro", "name": "Bellandur Metro", "lat": 12.9277, "lng": 77.6754},
    {"k": "metro", "name": "Kadubeesanahalli Metro", "lat": 12.9364, "lng": 77.6908},
    {"k": "metro", "name": "Marathahalli Metro", "lat": 12.9562, "lng": 77.7011},
    {"k": "metro", "name": "Bommanahalli Metro", "lat": 12.9032, "lng": 77.6295},
    {"k": "metro", "name": "Hongasandra Metro", "lat": 12.8934, "lng": 77.6377},
    {"k": "metro", "name": "Kudlu Gate Metro", "lat": 12.8856, "lng": 77.6426},
    {"k": "metro", "name": "Singasandra Metro", "lat": 12.8781, "lng": 77.6468},
    {"k": "metro", "name": "Hosa Road Metro", "lat": 12.8698, "lng": 77.6525},
    {"k": "metro", "name": "Electronic City Metro", "lat": 12.8452, "lng": 77.6602},
    {"k": "metro", "name": "Hebbal Metro", "lat": 13.0358, "lng": 77.5970},
    {"k": "metro", "name": "Nagawara Metro", "lat": 13.0445, "lng": 77.6197},
    {"k": "metro", "name": "Yelahanka Metro", "lat": 13.1007, "lng": 77.5963},
    {"k": "rail", "name": "Yesvantpur Junction", "lat": 13.0238, "lng": 77.5547},
    {"k": "rail", "name": "Krishnarajapuram Railway Station", "lat": 13.0011, "lng": 77.6758},
    {"k": "rail", "name": "Whitefield Railway Station", "lat": 12.9968, "lng": 77.7617},
    {"k": "rail", "name": "Carmelaram Railway Station", "lat": 12.9125, "lng": 77.7082},
    {"k": "rail", "name": "Yelahanka Junction", "lat": 13.1004, "lng": 77.6009},
    # Parks & Lakes
    {"k": "park", "name": "Cubbon Park", "lat": 12.9763, "lng": 77.5929},
    {"k": "park", "name": "Lalbagh Botanical Garden", "lat": 12.9507, "lng": 77.5848},
    {"k": "park", "name": "Sankey Tank Park", "lat": 13.0099, "lng": 77.5736},
    {"k": "park", "name": "Ulsoor Lake Park", "lat": 12.9822, "lng": 77.6202},
    {"k": "park", "name": "Agara Lake Park", "lat": 12.9234, "lng": 77.6416},
    {"k": "park", "name": "Kaikondrahalli Lake Park", "lat": 12.9154, "lng": 77.6780},
    {"k": "park", "name": "Saul Kere Lake Park", "lat": 12.9228, "lng": 77.6844},
    {"k": "park", "name": "Kundalahalli Lake Park", "lat": 12.9686, "lng": 77.7166},
    {"k": "park", "name": "Inner Circle Park Whitefield", "lat": 12.9718, "lng": 77.7501},
    {"k": "park", "name": "Kadugodi Tree Park", "lat": 12.9890, "lng": 77.7520},
    {"k": "park", "name": "Varthur Lake Walkway", "lat": 12.9467, "lng": 77.7418},
    {"k": "park", "name": "Hebbal Lake Park", "lat": 13.0462, "lng": 77.5858},
    {"k": "park", "name": "Lumbini Gardens Nagawara", "lat": 13.0434, "lng": 77.6095},
    {"k": "park", "name": "Jakkur Lake Park", "lat": 13.0819, "lng": 77.6104},
    {"k": "park", "name": "Rachenahalli Lake Park", "lat": 13.0638, "lng": 77.6214},
    {"k": "park", "name": "Yelahanka Lake Park", "lat": 13.1066, "lng": 77.5892},
    {"k": "park", "name": "JP Park Mathikere", "lat": 13.0352, "lng": 77.5525},
    {"k": "park", "name": "HSR Sector 2 Park", "lat": 12.9082, "lng": 77.6476},
    {"k": "park", "name": "Koramangala 3rd Block Park", "lat": 12.9292, "lng": 77.6285},
    {"k": "park", "name": "Indiranagar Defence Colony Park", "lat": 12.9722, "lng": 77.6435},
    {"k": "park", "name": "Madiwala Lake Park", "lat": 12.9083, "lng": 77.6177},
    {"k": "park", "name": "Puttenahalli Lake Park", "lat": 12.8914, "lng": 77.5865},
    {"k": "park", "name": "Arekere Lake Park", "lat": 12.8850, "lng": 77.5992},
    {"k": "park", "name": "Hulimavu Lake Park", "lat": 12.8748, "lng": 77.6033},
    {"k": "park", "name": "Doddakallasandra Lake Park", "lat": 12.8832, "lng": 77.5582},
    {"k": "park", "name": "Thalaghattapura Forest Park", "lat": 12.8685, "lng": 77.5410},
    {"k": "park", "name": "Haralur Lake Park", "lat": 12.9022, "lng": 77.6685},
    {"k": "park", "name": "Doddanekundi Lake Park", "lat": 12.9781, "lng": 77.6946},
    {"k": "park", "name": "Brookefield Neighbourhood Park", "lat": 12.9652, "lng": 77.7142},
    {"k": "park", "name": "Electronic City Phase 1 Park", "lat": 12.8458, "lng": 77.6650},
    {"k": "park", "name": "Sarjapur Sompura Park", "lat": 12.8810, "lng": 77.7620},
    {"k": "park", "name": "Malleshwaram 18th Cross Park", "lat": 13.0072, "lng": 77.5688},
    {"k": "park", "name": "Rajajinagar 2nd Block Park", "lat": 13.0020, "lng": 77.5558},
    # Hospitals
    {"k": "hospital", "name": "Manipal Hospital Old Airport Road", "lat": 12.9585, "lng": 77.6489},
    {"k": "hospital", "name": "Manipal Hospital Whitefield", "lat": 12.9822, "lng": 77.7376},
    {"k": "hospital", "name": "Manipal Hospital Sarjapur Road", "lat": 12.9195, "lng": 77.6660},
    {"k": "hospital", "name": "Manipal Hospital Hebbal", "lat": 13.0507, "lng": 77.5936},
    {"k": "hospital", "name": "Manipal Hospital Yeshwanthpur", "lat": 13.0124, "lng": 77.5553},
    {"k": "hospital", "name": "Sakra World Hospital", "lat": 12.9277, "lng": 77.6849},
    {"k": "hospital", "name": "Aster Whitefield Hospital", "lat": 12.9879, "lng": 77.7302},
    {"k": "hospital", "name": "Aster CMI Hospital Hebbal", "lat": 13.0545, "lng": 77.5917},
    {"k": "hospital", "name": "Apollo Hospital Bannerghatta", "lat": 12.8959, "lng": 77.5987},
    {"k": "hospital", "name": "Fortis Hospital Bannerghatta", "lat": 12.8947, "lng": 77.5985},
    {"k": "hospital", "name": "Cloudnine Hospital Bellandur", "lat": 12.9275, "lng": 77.6742},
    {"k": "hospital", "name": "Cloudnine Hospital Whitefield", "lat": 12.9854, "lng": 77.7240},
    {"k": "hospital", "name": "St. John's Medical Centre", "lat": 12.9296, "lng": 77.6203},
    {"k": "hospital", "name": "Rainbow Children's Hospital Marathahalli", "lat": 12.9616, "lng": 77.7010},
    {"k": "hospital", "name": "Narayana Health City", "lat": 12.8168, "lng": 77.6946},
    {"k": "hospital", "name": "Kauvery Hospital Electronic City", "lat": 12.8482, "lng": 77.6584},
    {"k": "hospital", "name": "Motherhood Hospital Indiranagar", "lat": 12.9781, "lng": 77.6416},
    {"k": "hospital", "name": "Cura Hospital Kanakapura Road", "lat": 12.8855, "lng": 77.5602},
    {"k": "hospital", "name": "Cytecare Cancer Hospital Yelahanka", "lat": 13.1180, "lng": 77.6140},
    {"k": "hospital", "name": "Regal Hospital Thanisandra", "lat": 13.0731, "lng": 77.6382},
    # Malls & Shopping
    {"k": "shopping", "name": "Phoenix Marketcity Whitefield", "lat": 12.9958, "lng": 77.6964},
    {"k": "shopping", "name": "Nexus Shantiniketan Mall", "lat": 12.9896, "lng": 77.7279},
    {"k": "shopping", "name": "Park Square Mall ITPL", "lat": 12.9866, "lng": 77.7367},
    {"k": "shopping", "name": "Orion Mall Rajajinagar", "lat": 13.0110, "lng": 77.5549},
    {"k": "shopping", "name": "Mantri Square Mall", "lat": 12.9916, "lng": 77.5711},
    {"k": "shopping", "name": "Forum South Bengaluru", "lat": 12.8878, "lng": 77.5632},
    {"k": "shopping", "name": "Vega City Mall", "lat": 12.9076, "lng": 77.6009},
    {"k": "shopping", "name": "Royal Meenakshi Mall", "lat": 12.8758, "lng": 77.5956},
    {"k": "shopping", "name": "Nexus Koramangala", "lat": 12.9345, "lng": 77.6113},
    {"k": "shopping", "name": "UB City Mall", "lat": 12.9716, "lng": 77.5960},
    {"k": "shopping", "name": "Bhartiya Mall of Bengaluru", "lat": 13.0808, "lng": 77.6416},
    {"k": "shopping", "name": "Phoenix Mall of Asia", "lat": 13.0725, "lng": 77.5920},
    {"k": "shopping", "name": "Brookefield Mall", "lat": 12.9659, "lng": 77.7176},
    {"k": "shopping", "name": "Centro Mall Bellandur", "lat": 12.9261, "lng": 77.6746},
    {"k": "shopping", "name": "Market Square Sarjapur Road", "lat": 12.9125, "lng": 77.6805},
    {"k": "shopping", "name": "Elements Mall Nagawara", "lat": 13.0449, "lng": 77.6267},
    {"k": "shopping", "name": "Galleria Mall Yelahanka", "lat": 13.0998, "lng": 77.5960},
    {"k": "shopping", "name": "Gopalan Arcade Mall Mysore Road", "lat": 12.9345, "lng": 77.5190},
    # Schools
    {"k": "school", "name": "National Public School Indiranagar", "lat": 12.9736, "lng": 77.6486},
    {"k": "school", "name": "National Public School Koramangala", "lat": 12.9327, "lng": 77.6209},
    {"k": "school", "name": "National Public School HSR", "lat": 12.9142, "lng": 77.6448},
    {"k": "school", "name": "National Public School Whitefield", "lat": 12.9904, "lng": 77.7521},
    {"k": "school", "name": "National Public School Rajajinagar", "lat": 12.9960, "lng": 77.5542},
    {"k": "school", "name": "Greenwood High International", "lat": 12.8992, "lng": 77.7346},
    {"k": "school", "name": "Oakridge International School", "lat": 12.9056, "lng": 77.7510},
    {"k": "school", "name": "Inventure Academy", "lat": 12.9041, "lng": 77.7435},
    {"k": "school", "name": "TISB Whitefield Sarjapur", "lat": 12.9061, "lng": 77.7519},
    {"k": "school", "name": "Deens Academy Whitefield", "lat": 12.9685, "lng": 77.7460},
    {"k": "school", "name": "Delhi Public School East", "lat": 12.8980, "lng": 77.7161},
    {"k": "school", "name": "Delhi Public School South", "lat": 12.8748, "lng": 77.5612},
    {"k": "school", "name": "Delhi Public School North", "lat": 13.1338, "lng": 77.6248},
    {"k": "school", "name": "Vibgyor High Haralur", "lat": 12.9058, "lng": 77.6695},
    {"k": "school", "name": "Vibgyor High Marathahalli", "lat": 12.9669, "lng": 77.7052},
    {"k": "school", "name": "Ryan International Kundalahalli", "lat": 12.9652, "lng": 77.7130},
    {"k": "school", "name": "Canadian International School Yelahanka", "lat": 13.1095, "lng": 77.6030},
    {"k": "school", "name": "Stonehill International School", "lat": 13.1755, "lng": 77.6256},
    {"k": "school", "name": "Trio World Academy Hebbal", "lat": 13.0630, "lng": 77.5908},
    {"k": "school", "name": "Legacy School Hennur", "lat": 13.0639, "lng": 77.6480},
    {"k": "school", "name": "Brigade School JP Nagar", "lat": 12.8925, "lng": 77.5820},
    {"k": "school", "name": "Bishop Cotton Boys School", "lat": 12.9675, "lng": 77.5998},
    {"k": "school", "name": "Harvest International Sarjapur", "lat": 12.9054, "lng": 77.6941},
    {"k": "school", "name": "Ebenezer International Electronic City", "lat": 12.8380, "lng": 77.6740},
]

# Real Bengaluru residential projects:
# (name, developer, locality, lat, lng, kind, bhks, sqft_by_bhk, psf, towers, units, acres, status, possession, rating, squash_flag, extra_amens)
SOCIETIES = [
    # --- WHITEFIELD / ITPL / HOODI / VARTHUR / PANATHUR ---
    ("Prestige Shantiniketan", "Prestige Group", "Whitefield", 12.9905, 77.7276, "apartment", [2, 3, 4], {2: 1297, 3: 2071, 4: 2522}, 13500, 24, 3002, 105, "Ready to Move", "2011", 4.6, True, ["Tennis Court", "Badminton Court", "Squash Court", "Amphitheatre"]),
    ("Prestige Lakeside Habitat", "Prestige Group", "Varthur, Whitefield", 12.9482, 77.7426, "apartment", [2, 3, 4], {2: 1216, 3: 1697, 4: 2882}, 11800, 24, 3426, 102, "Ready to Move", "2020", 4.5, True, ["Squash Court", "Badminton Court", "Tennis Court", "Skating Rink"]),
    ("Prestige Waterford", "Prestige Group", "ECC Road, Whitefield", 12.9760, 77.7424, "apartment", [3, 4], {3: 1775, 4: 2555}, 13200, 7, 689, 16.6, "Ready to Move", "2024", 4.5, True, ["Badminton Court", "Tennis Court", "Mini Theatre"]),
    ("Prestige Lavender Fields", "Prestige Group", "Varthur, Whitefield", 12.9396, 77.7408, "apartment", [1, 2, 3, 4], {1: 669, 2: 1260, 3: 1902, 4: 2717}, 12600, 6, 1473, 18.2, "Under Construction", "2027", 4.4, True, ["Squash Court", "Yoga Deck", "Badminton Court"]),
    ("Prestige Park Grove", "Prestige Group", "Seegehalli, Whitefield", 12.9968, 77.7720, "apartment", [2, 3, 4], {2: 1200, 3: 1920, 4: 3677}, 12400, 19, 3627, 72, "Under Construction", "2027", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court", "Amphitheatre"]),
    ("Prestige Serenity Shores", "Prestige Group", "Varthur, Whitefield", 12.9462, 77.7445, "apartment", [2, 3, 4], {2: 1260, 3: 1981, 4: 2688}, 12500, 4, 657, 11.3, "Under Construction", "2027", 4.4, False, ["Badminton Court", "Amphitheatre", "Meditation Area"]),
    ("Prestige White Meadows", "Prestige Group", "Whitefield", 12.9735, 77.7524, "villa", [4, 5], {4: 4111, 5: 6219}, 18500, 4, 288, 28.5, "Ready to Move", "2018", 4.7, True, ["Squash Court", "Tennis Court", "Coffee Lounge", "Spa"]),
    ("Prestige Elm Park", "Prestige Group", "Channasandra, Whitefield", 12.9912, 77.7568, "apartment", [3, 4], {3: 1850, 4: 2575}, 12200, 3, 192, 3.98, "Under Construction", "2026", 4.3, False, ["Badminton Court", "Multipurpose Hall"]),
    ("Prestige Raintree Park", "Prestige Group", "Varthur, Whitefield", 12.9502, 77.7376, "apartment", [3, 4, 5], {3: 2005, 4: 2924, 5: 3503}, 14800, 18, 1520, 21, "Under Construction", "2028", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Sobha Windsor", "Sobha Limited", "Whitefield", 13.0052, 77.7640, "apartment", [3, 4], {3: 1817, 4: 2292}, 13400, 11, 739, 13.7, "Ready to Move", "2025", 4.6, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Sobha Dream Acres", "Sobha Limited", "Balagere, Panathur", 12.9365, 77.7222, "apartment", [1, 2], {1: 660, 2: 1210}, 10900, 65, 6500, 81, "Ready to Move", "2022", 4.4, False, ["Badminton Court", "Tennis Court", "Amphitheatre"]),
    ("Sobha Habitech", "Sobha Limited", "Whitefield", 12.9788, 77.7336, "apartment", [2, 3, 4], {2: 1380, 3: 1795, 4: 2510}, 12500, 6, 318, 4.5, "Ready to Move", "2018", 4.4, False, ["Badminton Court", "Library"]),
    ("Sobha Rose", "Sobha Limited", "Whitefield", 12.9742, 77.7358, "apartment", [2, 3], {2: 1450, 3: 1850}, 11500, 4, 188, 3.2, "Ready to Move", "2010", 4.3, False, ["Tennis Court", "Badminton Court"]),
    ("Sobha Sentosa", "Sobha Limited", "Panathur Road", 12.9372, 77.7176, "apartment", [3], {3: 1507}, 12800, 7, 533, 7.5, "Under Construction", "2026", 4.4, False, ["Badminton Court", "Reflexology Park"]),
    ("Sobha Neopolis", "Sobha Limited", "Panathur Road", 12.9351, 77.7138, "apartment", [3, 4], {3: 1630, 4: 2481}, 13800, 19, 1875, 25.3, "Under Construction", "2028", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Brigade Cosmopolis", "Brigade Group", "Whitefield", 12.9682, 77.7438, "apartment", [2, 3, 4], {2: 1310, 3: 1970, 4: 3150}, 13600, 12, 805, 9.3, "Ready to Move", "2019", 4.6, True, ["Squash Court", "Tennis Court", "Badminton Court", "Rooftop Lounge"]),
    ("Brigade Lakefront", "Brigade Group", "Whitefield", 12.9875, 77.7155, "apartment", [2, 3, 4], {2: 1260, 3: 1850, 4: 2990}, 12800, 12, 1100, 20, "Ready to Move", "2020", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Brigade Woods", "Brigade Group", "Whitefield", 12.9830, 77.7418, "apartment", [2, 3], {2: 1210, 3: 1680}, 11900, 17, 333, 6.3, "Ready to Move", "2022", 4.4, False, ["Badminton Court", "Tennis Court"]),
    ("Brigade Cornerstone Utopia", "Brigade Group", "Varthur, Whitefield", 12.9344, 77.7478, "apartment", [1, 2, 3], {1: 782, 2: 1097, 3: 1656}, 11800, 16, 4000, 47, "Ready to Move", "2024", 4.4, True, ["Tennis Court", "Badminton Court", "Multiplex"]),
    ("Total Environment Windmills of Your Mind", "Total Environment", "Whitefield", 12.9829, 77.7212, "apartment", [4], {4: 3848}, 18200, 7, 405, 24, "Ready to Move", "2016", 4.8, True, ["Squash Court", "Tennis Court", "Library", "Jazz Theatre"]),
    ("Total Environment Pursuit of a Radical Rhapsody", "Total Environment", "Hoodi, Whitefield", 12.9882, 77.7192, "apartment", [3, 4], {3: 2753, 4: 4100}, 17400, 8, 1085, 34.5, "Under Construction", "2026", 4.7, True, ["Squash Court", "Heated Pool", "Library"]),
    ("Godrej United", "Godrej Properties", "Hoodi, Whitefield", 12.9935, 77.7024, "apartment", [2, 3, 4], {2: 1390, 3: 2050, 4: 2880}, 12900, 2, 514, 8, "Ready to Move", "2021", 4.4, False, ["Badminton Court", "Sky Lounge"]),
    ("Godrej Air", "Godrej Properties", "Hoodi, Whitefield", 12.9918, 77.7105, "apartment", [2, 3], {2: 1120, 3: 1640}, 11900, 5, 510, 6.2, "Ready to Move", "2023", 4.3, False, ["Badminton Court", "Organic Farm"]),
    ("Godrej Splendour", "Godrej Properties", "Belathur, Whitefield", 13.0072, 77.7652, "apartment", [1, 2, 3], {1: 605, 2: 1050, 3: 1529}, 10800, 9, 1161, 17.7, "Under Construction", "2026", 4.2, False, ["Badminton Court", "Mini Theatre"]),
    ("Assetz Marq", "Assetz Property Group", "Kannamangala, Whitefield", 13.0215, 77.7685, "apartment", [3, 4], {3: 1625, 4: 2274}, 11200, 14, 1600, 28, "Ready to Move", "2024", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Sumadhura Folium", "Sumadhura Infracon", "Whitefield", 12.9688, 77.7352, "apartment", [2, 3, 4], {2: 1320, 3: 1850, 4: 2450}, 12400, 8, 1020, 16.5, "Under Construction", "2026", 4.4, True, ["Squash Court", "Badminton Court", "Tennis Court"]),
    ("Divyasree Republic of Whitefield", "DivyaSree Developers", "Kundalahalli, Whitefield", 12.9698, 77.7165, "apartment", [2, 3], {2: 1140, 3: 1715}, 12100, 12, 1250, 14, "Ready to Move", "2018", 4.4, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Vaswani Exquisite", "Vaswani Group", "Whitefield", 12.9879, 77.7346, "apartment", [3, 4], {3: 1815, 4: 2860}, 13100, 4, 415, 4.9, "Ready to Move", "2020", 4.5, True, ["Squash Court", "Badminton Court"]),
    ("Adarsh Palm Meadows", "Adarsh Developers", "Whitefield", 12.9648, 77.7372, "villa", [4, 5], {4: 3600, 5: 5200}, 22000, 1, 570, 100, "Ready to Move", "2008", 4.8, True, ["Squash Court", "Tennis Court", "Badminton Court", "Spa"]),
    ("Purva Fountain Square", "Puravankara", "Marathahalli", 12.9570, 77.7052, "apartment", [2, 3], {2: 1350, 3: 1860}, 10800, 12, 1220, 17, "Ready to Move", "2010", 4.3, False, ["Tennis Court", "Badminton Court"]),
    ("Rohan Iksha", "Rohan Builders", "Bhoganhalli, Bellandur", 12.9310, 77.7034, "apartment", [2, 3, 4], {2: 1290, 3: 1750, 4: 2210}, 11600, 12, 666, 8.5, "Ready to Move", "2020", 4.4, False, ["Badminton Court", "Tennis Court"]),
    ("Goyal Orchid Whitefield", "Goyal & Co", "Whitefield", 12.9858, 77.7458, "apartment", [2, 3], {2: 1190, 3: 1620}, 11400, 5, 492, 7, "Ready to Move", "2019", 4.3, False, ["Badminton Court", "Amphitheatre"]),
    ("Pavani Mirabilia", "Pavani Group", "Seegehalli, Whitefield", 13.0068, 77.7688, "apartment", [2, 3], {2: 1210, 3: 1690}, 9800, 7, 774, 14, "Under Construction", "2026", 4.2, False, ["Badminton Court", "Tennis Court"]),
    ("Chaithanya Smaran", "Chaithanya Projects", "Whitefield", 12.9768, 77.7625, "villa", [3, 4], {3: 2700, 4: 3400}, 16000, 1, 128, 12, "Ready to Move", "2014", 4.6, False, ["Tennis Court", "Badminton Court"]),
    ("Sterling Villa Grande", "Sterling Developers", "Seegehalli, Whitefield", 13.0124, 77.7618, "villa", [3, 4], {3: 2650, 4: 3500}, 14500, 1, 200, 32, "Ready to Move", "2018", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Gopalan Grandeur", "Gopalan Enterprises", "Hoodi, Whitefield", 12.9905, 77.7098, "apartment", [2, 3], {2: 1250, 3: 1690}, 10200, 8, 520, 6.5, "Ready to Move", "2015", 4.2, False, ["Tennis Court", "Badminton Court"]),

    # --- SARJAPUR ROAD / BELLANDUR / HARALUR / ORR ---
    ("Sobha Royal Pavilion", "Sobha Limited", "Sarjapur Road", 12.9122, 77.6946, "apartment", [2, 3, 4], {2: 1300, 3: 1807, 4: 2232}, 13600, 16, 1284, 23.6, "Ready to Move", "2024", 4.6, True, ["Squash Court", "Tennis Court", "Badminton Court", "Amphitheatre"]),
    ("The Prestige City Avalon Park", "Prestige Group", "Sarjapur Road", 12.8808, 77.7640, "apartment", [3, 4], {3: 1657, 4: 2290}, 11500, 7, 950, 18, "Under Construction", "2026", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("The Prestige City Eden Park", "Prestige Group", "Sarjapur Road", 12.8825, 77.7605, "apartment", [1, 2], {1: 666, 2: 979}, 11200, 9, 2217, 9.7, "Under Construction", "2026", 4.4, False, ["Badminton Court", "Amphitheatre"]),
    ("The Prestige City Meridian Park", "Prestige Group", "Sarjapur Road", 12.8792, 77.7662, "apartment", [3], {3: 1665}, 11600, 16, 2900, 18.2, "Under Construction", "2026", 4.5, True, ["Squash Court", "Badminton Court", "Tennis Court"]),
    ("Prestige Ferns Residency", "Prestige Group", "Haralur, Sarjapur Road", 12.9050, 77.6665, "apartment", [2, 3, 4], {2: 1190, 3: 1648, 4: 2569}, 13200, 23, 1483, 25, "Ready to Move", "2018", 4.6, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Prestige Sunnyside", "Prestige Group", "Bellandur, ORR", 12.9316, 77.6948, "apartment", [2, 3, 4], {2: 1360, 3: 1840, 4: 2439}, 13500, 8, 405, 5, "Ready to Move", "2015", 4.5, True, ["Squash Court", "Badminton Court"]),
    ("Prestige Kew Gardens", "Prestige Group", "Yemalur, Bellandur", 12.9448, 77.6845, "apartment", [1, 2, 3], {1: 635, 2: 1180, 3: 1607}, 12900, 16, 970, 15.7, "Ready to Move", "2020", 4.5, False, ["Badminton Court", "Amphitheatre"]),
    ("Adarsh Palm Retreat", "Adarsh Developers", "Bellandur, ORR", 12.9225, 77.6845, "apartment", [2, 3, 4], {2: 1340, 3: 1920, 4: 2750}, 14200, 28, 1720, 110, "Ready to Move", "2016", 4.7, True, ["Squash Court", "Tennis Court", "Badminton Court", "Spa"]),
    ("Sobha Classic", "Sobha Limited", "Haralur Road", 12.9012, 77.6698, "apartment", [3], {3: 1810}, 12200, 5, 250, 3.8, "Ready to Move", "2014", 4.4, False, ["Badminton Court", "Tennis Court"]),
    ("Sobha Lake Gardens", "Sobha Limited", "KR Puram", 13.0085, 77.7075, "apartment", [2, 3], {2: 1358, 3: 1750}, 11500, 9, 597, 8.8, "Ready to Move", "2023", 4.5, True, ["Squash Court", "Badminton Court"]),
    ("Brigade Sanctuary", "Brigade Group", "Varthur, Sarjapur Road", 12.9022, 77.7525, "apartment", [3, 4], {3: 1730, 4: 2491}, 12200, 8, 1275, 14, "Under Construction", "2028", 4.4, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Godrej Park Retreat", "Godrej Properties", "Sarjapur Road", 12.9065, 77.7160, "apartment", [1, 2, 3], {1: 608, 2: 1100, 3: 1471}, 11400, 8, 1150, 13, "Under Construction", "2027", 4.3, False, ["Badminton Court", "Tennis Court"]),
    ("Assetz 63 Degree East", "Assetz Property Group", "Sarjapur Road", 12.9028, 77.7210, "apartment", [2, 3], {2: 1157, 3: 1550}, 10900, 14, 1600, 26, "Ready to Move", "2023", 4.4, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Purva Skydale", "Puravankara", "Haralur, Sarjapur Road", 12.9045, 77.6745, "apartment", [2, 3], {2: 1320, 3: 1760}, 11200, 5, 314, 4.6, "Ready to Move", "2019", 4.3, False, ["Tennis Court", "Badminton Court"]),
    ("SJR Blue Waters", "SJR Primecorp", "Haralur, Sarjapur Road", 12.8998, 77.6650, "apartment", [2, 3], {2: 1185, 3: 1620}, 10600, 14, 1500, 16, "Ready to Move", "2022", 4.2, False, ["Badminton Court", "Tennis Court"]),
    ("Salarpuria Sattva Greenage", "Sattva Group", "Bommanahalli, Hosur Road", 12.9052, 77.6305, "apartment", [2, 3, 4], {2: 1345, 3: 1890, 4: 2755}, 12400, 10, 1680, 21, "Ready to Move", "2016", 4.6, True, ["Squash Court", "Tennis Court", "Badminton Court", "Bowling Alley"]),
    ("Bren Imperia", "Bren Corporation", "Haralur, Sarjapur Road", 12.9092, 77.6725, "apartment", [2, 3], {2: 1160, 3: 1680}, 11100, 7, 500, 6, "Ready to Move", "2017", 4.3, False, ["Badminton Court", "Skating Rink"]),
    ("Nambiar Bellezea", "Nambiar Builders", "Chandapura, Sarjapur", 12.8380, 77.7215, "villa", [4, 5], {4: 3450, 5: 4800}, 14800, 1, 350, 70, "Ready to Move", "2022", 4.7, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Nambiar District 25", "Nambiar Builders", "Muthanallur, Sarjapur Road", 12.8680, 77.7350, "apartment", [2, 3, 4], {2: 1240, 3: 1890, 4: 2560}, 12400, 12, 1800, 100, "Under Construction", "2028", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Mana Uber Verdant", "Mana Projects", "Sarjapur Road", 12.9055, 77.7022, "apartment", [2, 3], {2: 1180, 3: 1690}, 10800, 4, 340, 5.5, "Ready to Move", "2021", 4.3, False, ["Badminton Court", "Amphitheatre"]),
    ("Embassy Pristine", "Embassy Group", "Iblur, Bellandur", 12.9218, 77.6585, "apartment", [3, 4], {3: 2740, 4: 3860}, 16800, 9, 424, 14.5, "Ready to Move", "2015", 4.7, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Sobha Garnet", "Sobha Limited", "Bellandur", 12.9275, 77.6675, "apartment", [3], {3: 1890}, 13400, 4, 176, 3.5, "Ready to Move", "2011", 4.5, False, ["Badminton Court", "Tennis Court"]),
    ("Prestige Great Acres", "Prestige Group", "Sarjapur Road", 12.8772, 77.7685, "plot", [0], {}, 8900, 0, 808, 80, "Ready to Move", "2024", 4.4, False, ["Tennis Court", "Amphitheatre"]),
    ("Godrej Woodland", "Godrej Properties", "Sarjapur Road", 12.8515, 77.7920, "plot", [0], {}, 7200, 0, 1200, 100, "Ready to Move", "2024", 4.3, False, ["Badminton Court", "Organic Park"]),

    # --- HSR LAYOUT / KORAMANGALA / INDIRANAGAR / CENTRAL BENGALURU ---
    ("Prestige Acropolis", "Prestige Group", "Koramangala", 12.9368, 77.6130, "apartment", [3, 4], {3: 2150, 4: 3450}, 19500, 6, 278, 5.5, "Ready to Move", "2004", 4.6, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Prestige St. Johns Wood", "Prestige Group", "Koramangala", 12.9332, 77.6148, "apartment", [2, 3, 4], {2: 1410, 3: 1920, 4: 2650}, 17800, 9, 487, 8, "Ready to Move", "2007", 4.6, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Prestige Pinewood", "Prestige Group", "Koramangala", 12.9422, 77.6240, "apartment", [2, 3, 4], {2: 1365, 3: 1802, 4: 2487}, 19800, 3, 256, 2.5, "Ready to Move", "2021", 4.6, False, ["Badminton Court", "Mini Theatre"]),
    ("Prestige Leela Residences", "Prestige Group", "Old Airport Road, Indiranagar", 12.9612, 77.6485, "apartment", [4], {4: 3876}, 26500, 1, 88, 3, "Ready to Move", "2018", 4.8, True, ["Squash Court", "Concierge", "Spa"]),
    ("Prestige Kingfisher Towers", "Prestige Group", "Lavelle Road, Central Bengaluru", 12.9718, 77.5975, "apartment", [4, 5], {4: 8321, 5: 8321}, 42000, 3, 81, 4.5, "Ready to Move", "2018", 4.9, True, ["Squash Court", "Helipad", "Spa"]),
    ("Embassy One", "Embassy Group", "Bellary Road, Hebbal", 13.0218, 77.5882, "apartment", [2, 3, 4], {2: 2050, 3: 3200, 4: 4800}, 28500, 2, 109, 6.5, "Ready to Move", "2019", 4.8, True, ["Squash Court", "Concierge", "Spa"]),
    ("Embassy Habitat", "Embassy Group", "Vasanth Nagar, Central Bengaluru", 12.9908, 77.5902, "apartment", [3, 4], {3: 2450, 4: 3450}, 24000, 4, 240, 4.5, "Ready to Move", "2010", 4.7, True, ["Squash Court", "Tennis Court"]),
    ("Raheja Residency", "K Raheja Corp", "Koramangala 3rd Block", 12.9278, 77.6302, "apartment", [2, 3], {2: 1290, 3: 1820}, 16200, 12, 780, 12, "Ready to Move", "2002", 4.5, False, ["Tennis Court", "Badminton Court"]),
    ("Sobha Infinia", "Sobha Limited", "Koramangala", 12.9315, 77.6368, "apartment", [3, 4], {3: 1920, 4: 2950}, 19200, 5, 196, 4.7, "Under Construction", "2027", 4.5, False, ["Badminton Court", "Rooftop Pool"]),
    ("Sobha Morzaria Grandeur", "Sobha Limited", "Bannerghatta Road, Koramangala", 12.9362, 77.6038, "apartment", [3, 4], {3: 2050, 4: 2800}, 17500, 3, 180, 3.2, "Ready to Move", "2013", 4.6, False, ["Badminton Court", "Tennis Court"]),
    ("Purva Fairmont", "Puravankara", "HSR Layout Sector 2", 12.9098, 77.6498, "apartment", [2, 3], {2: 1270, 3: 1715}, 13400, 6, 480, 7, "Ready to Move", "2009", 4.4, False, ["Tennis Court", "Badminton Court"]),
    ("Salarpuria Sattva Senorita", "Sattva Group", "Sarjapur Road, HSR", 12.9188, 77.6695, "apartment", [2, 3], {2: 1210, 3: 1750}, 12200, 4, 240, 3.5, "Ready to Move", "2014", 4.4, False, ["Badminton Court", "Tennis Court"]),
    ("Indiranagar 100ft Boutique Floors", "Boutique Homes Bengaluru", "Indiranagar", 12.9762, 77.6410, "builder floor", [3, 4], {3: 2100, 4: 2850}, 19500, 1, 12, 0.5, "Ready to Move", "2023", 4.5, False, ["Power Back Up", "Lift"]),
    ("HSR Sector 2 Independent Floors", "SLV Homes", "HSR Layout", 12.9110, 77.6442, "builder floor", [3], {3: 1850}, 14200, 1, 16, 0.4, "Ready to Move", "2024", 4.3, False, ["Power Back Up", "Lift"]),
    ("Koramangala 4th Block Luxury Floors", "Prestige Boutique", "Koramangala", 12.9355, 77.6265, "builder floor", [3, 4], {3: 2250, 4: 3100}, 18800, 1, 10, 0.4, "Ready to Move", "2023", 4.6, False, ["Power Back Up", "Lift"]),
    ("Jayanagar 4th Block Heritage Floors", "Nandi Builders", "Jayanagar", 12.9265, 77.5842, "builder floor", [3, 4], {3: 2050, 4: 2700}, 16800, 1, 12, 0.4, "Ready to Move", "2022", 4.5, False, ["Power Back Up", "Lift"]),

    # --- NORTH BENGALURU (HEBBAL / YELAHANKA / THANISANDRA / HENNUR / JAKKUR / DEVANAHALLI) ---
    ("L&T Raintree Boulevard", "L&T Realty", "Hebbal", 13.0622, 77.5936, "apartment", [3, 4], {3: 1935, 4: 2485}, 14400, 18, 1200, 65, "Ready to Move", "2022", 4.7, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Embassy Lake Terraces", "Embassy Group", "Hebbal", 13.0472, 77.5912, "apartment", [3, 4, 5], {3: 3544, 4: 4400, 5: 5100}, 17900, 9, 467, 14.5, "Ready to Move", "2020", 4.7, True, ["Squash Court", "Sky Deck", "Tennis Court", "Spa"]),
    ("Century Ethos", "Century Real Estate", "Hebbal", 13.0608, 77.5910, "apartment", [3, 4], {3: 2850, 4: 4235}, 15200, 4, 333, 7.3, "Ready to Move", "2021", 4.6, True, ["Squash Court", "Bowling Alley", "Spa"]),
    ("Godrej Woodsman Estate", "Godrej Properties", "Hebbal", 13.0492, 77.5955, "apartment", [2, 3], {2: 1295, 3: 1840}, 12200, 16, 1200, 14, "Ready to Move", "2012", 4.5, False, ["Tennis Court", "Badminton Court"]),
    ("Prestige Misty Waters", "Prestige Group", "Hebbal", 13.0442, 77.6038, "apartment", [2, 3, 4], {2: 1141, 3: 1987, 4: 2483}, 12600, 5, 558, 6, "Ready to Move", "2019", 4.5, True, ["Squash Court", "Badminton Court"]),
    ("Prestige Fairfield", "Prestige Group", "RMV 2nd Stage, Hebbal", 13.0342, 77.5750, "apartment", [3, 4], {3: 2010, 4: 2882}, 16800, 2, 158, 2.8, "Ready to Move", "2024", 4.6, False, ["Badminton Court", "Sky Lounge"]),
    ("Prestige Finsbury Park", "Prestige Group", "Bagalur, North Bengaluru", 13.1365, 77.6682, "apartment", [1, 2, 3], {1: 652, 2: 999, 3: 1562}, 9200, 18, 3050, 25, "Ready to Move", "2024", 4.3, False, ["Badminton Court", "Tennis Court"]),
    ("Sobha City", "Sobha Limited", "Thanisandra Main Road", 13.0762, 77.6295, "apartment", [2, 3], {2: 1353, 3: 1711}, 11900, 21, 1756, 36, "Ready to Move", "2018", 4.5, False, ["Tennis Court", "Badminton Court", "Amphitheatre"]),
    ("Sobha Dream Gardens", "Sobha Limited", "Thanisandra", 13.0795, 77.6345, "apartment", [1, 2], {1: 678, 2: 1058}, 10800, 10, 1780, 17, "Under Construction", "2026", 4.4, False, ["Badminton Court", "Zen Garden"]),
    ("Sobha Palm Court", "Sobha Limited", "Yelahanka", 13.0952, 77.6115, "apartment", [2, 3], {2: 1320, 3: 1850}, 11400, 5, 294, 4.9, "Ready to Move", "2020", 4.5, False, ["Badminton Court", "Tennis Court"]),
    ("Bhartiya City Nikoo Homes", "Bhartiya Urban", "Thanisandra", 13.0815, 77.6410, "apartment", [1, 2, 3, 4], {1: 660, 2: 1180, 3: 1750, 4: 2500}, 11500, 15, 2400, 125, "Ready to Move", "2020", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court", "Central Park"]),
    ("Purva Atmosphere", "Puravankara", "Thanisandra Main Road", 13.0672, 77.6285, "apartment", [2, 3, 4], {2: 1330, 3: 2005, 4: 2420}, 12900, 3, 939, 13, "Ready to Move", "2025", 4.5, True, ["Squash Court", "Sky Observatory", "Badminton Court"]),
    ("Purva Venezia", "Puravankara", "Yelahanka New Town", 13.1052, 77.5752, "apartment", [2, 3], {2: 1320, 3: 1790}, 9800, 16, 1332, 22, "Ready to Move", "2012", 4.3, False, ["Tennis Court", "Badminton Court"]),
    ("Purva Zenium", "Puravankara", "Airport Road, Devanahalli", 13.1620, 77.6380, "apartment", [2, 3], {2: 1270, 3: 1720}, 10200, 8, 872, 10.5, "Ready to Move", "2024", 4.4, False, ["Badminton Court", "Tennis Court"]),
    ("Brigade El Dorado", "Brigade Group", "Bagalur, North Bengaluru", 13.1332, 77.6745, "apartment", [1, 2, 3], {1: 550, 2: 960, 3: 1560}, 8900, 12, 3500, 50, "Under Construction", "2026", 4.3, False, ["Tennis Court", "Badminton Court", "Football Field"]),
    ("Brigade Laguna", "Brigade Group", "Hebbal", 13.0585, 77.6198, "apartment", [2, 3], {2: 1185, 3: 1850}, 12800, 3, 216, 3, "Under Construction", "2026", 4.4, False, ["Badminton Court", "Amphitheatre"]),
    ("Brigade Eternia", "Brigade Group", "Yelahanka", 13.1005, 77.5965, "apartment", [3, 4], {3: 1820, 4: 2700}, 13400, 12, 1124, 14, "Under Construction", "2028", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Godrej Ananda", "Godrej Properties", "Bagalur, North Bengaluru", 13.1398, 77.6795, "apartment", [2, 3], {2: 1092, 3: 1630}, 9400, 7, 1600, 20, "Under Construction", "2026", 4.3, False, ["Badminton Court", "Pharmacy"]),
    ("Karle Zenith Residences", "Karle Infra", "Nagawara, Hebbal", 13.0462, 77.6152, "apartment", [3, 4], {3: 2300, 4: 3450}, 14800, 3, 396, 4.5, "Ready to Move", "2020", 4.6, True, ["Squash Court", "Tennis Court", "Helipad"]),
    ("RMZ Latitude", "RMZ Corp", "Hebbal", 13.0558, 77.5935, "apartment", [3, 4], {3: 2950, 4: 4100}, 16200, 2, 120, 4.5, "Ready to Move", "2018", 4.6, True, ["Squash Court", "Spa"]),
    ("Salarpuria Sattva Exotic", "Sattva Group", "Bagalur Main Road", 13.1125, 77.6260, "apartment", [2, 3], {2: 1245, 3: 1750}, 9800, 3, 345, 5, "Ready to Move", "2023", 4.4, False, ["Badminton Court", "Amphitheatre"]),
    ("Prestige Golfshire", "Prestige Group", "Nandi Hills Road, Devanahalli", 13.2150, 77.7050, "villa", [4, 5], {4: 5896, 5: 9719}, 19500, 1, 206, 275, "Ready to Move", "2016", 4.9, True, ["Squash Court", "Golf Course", "Tennis Court", "Spa"]),
    ("Sobha Lifestyle Legacy", "Sobha Limited", "Devanahalli", 13.2080, 77.6850, "villa", [4], {4: 6100}, 15500, 1, 165, 55, "Ready to Move", "2018", 4.7, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Godrej Reserve", "Godrej Properties", "Devanahalli", 13.2220, 77.7210, "plot", [0], {}, 6800, 0, 950, 92.7, "Ready to Move", "2023", 4.4, False, ["Badminton Court", "Forest Trail"]),
    ("Brigade Oasis", "Brigade Group", "Devanahalli", 13.2350, 77.7150, "plot", [0], {}, 6900, 0, 600, 40, "Ready to Move", "2025", 4.3, False, ["Tennis Court", "Amphitheatre"]),
    ("Assetz Earth & Essence", "Assetz Property Group", "Hosahalli, North Bengaluru", 13.1510, 77.6245, "villa", [3, 4], {3: 2450, 4: 3150}, 12500, 1, 220, 25, "Ready to Move", "2023", 4.5, False, ["Tennis Court", "Badminton Court"]),
    ("Rohan Upavan", "Rohan Builders", "Hennur Road", 13.0685, 77.6510, "apartment", [2, 3], {2: 1120, 3: 1580}, 10400, 10, 900, 12.5, "Ready to Move", "2024", 4.4, False, ["Badminton Court", "Orchard"]),
    ("House of Hiranandani Devanahalli", "House of Hiranandani", "Devanahalli", 13.2290, 77.7020, "villa", [3, 4], {3: 2350, 4: 3450}, 11800, 1, 280, 75, "Ready to Move", "2020", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court"]),

    # --- SOUTH BENGALURU (KANAKAPURA ROAD / BANNERGHATTA ROAD / JP NAGAR / ELECTRONIC CITY) ---
    ("Prestige Falcon City", "Prestige Group", "Kanakapura Road", 12.8885, 77.5625, "apartment", [2, 3, 4], {2: 1240, 3: 1588, 4: 2726}, 13400, 20, 2520, 41, "Ready to Move", "2020", 4.6, True, ["Squash Court", "Tennis Court", "Badminton Court", "Mall Access"]),
    ("Prestige Primrose Hills", "Prestige Group", "Kanakapura Road", 12.8682, 77.5325, "apartment", [1, 2, 3], {1: 585, 2: 985, 3: 1362}, 9800, 15, 1680, 15, "Ready to Move", "2025", 4.3, False, ["Badminton Court", "Tennis Court"]),
    ("Prestige Song of the South", "Prestige Group", "Begur, Bannerghatta Road", 12.8742, 77.6190, "apartment", [2, 3, 4], {2: 1312, 3: 1940, 4: 2424}, 11800, 16, 2171, 33, "Ready to Move", "2020", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court", "Library"]),
    ("Prestige Elysian", "Prestige Group", "Bannerghatta Road", 12.8768, 77.5965, "apartment", [2, 3], {2: 1109, 3: 1810}, 12600, 4, 548, 6.75, "Ready to Move", "2024", 4.5, False, ["Badminton Court", "Mini Theatre"]),
    ("Prestige Park Square", "Prestige Group", "Bannerghatta Road", 12.8628, 77.5920, "apartment", [2, 3], {2: 1130, 3: 1771}, 11500, 3, 586, 8, "Ready to Move", "2023", 4.4, True, ["Squash Court", "Badminton Court"]),
    ("Prestige Sunrise Park", "Prestige Group", "Electronic City Phase 1", 12.8385, 77.6580, "apartment", [1, 2, 3], {1: 630, 2: 1110, 3: 1615}, 9600, 15, 1910, 25, "Ready to Move", "2018", 4.4, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Sobha Forest View", "Sobha Limited", "Kanakapura Road", 12.8712, 77.5398, "apartment", [2, 3], {2: 1450, 3: 1850}, 11200, 12, 792, 16, "Ready to Move", "2016", 4.5, False, ["Tennis Court", "Badminton Court"]),
    ("Sobha Arena", "Sobha Limited", "Kanakapura Road", 12.8758, 77.5432, "apartment", [2, 3], {2: 1296, 3: 1680}, 11600, 6, 657, 10.7, "Ready to Move", "2022", 4.5, False, ["Tennis Court", "Badminton Court", "Skating Rink"]),
    ("Sobha Silicon Oasis", "Sobha Limited", "Hosa Road, Electronic City", 12.8722, 77.6612, "apartment", [2, 3], {2: 1365, 3: 1612}, 11200, 11, 910, 15, "Ready to Move", "2019", 4.5, False, ["Tennis Court", "Badminton Court"]),
    ("Sobha Townpark", "Sobha Limited", "Yadavanahalli, Hosur Road", 12.8095, 77.7285, "apartment", [2, 3, 4], {2: 1240, 3: 1755, 4: 2200}, 10900, 14, 2104, 33, "Under Construction", "2027", 4.4, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Brigade Meadows", "Brigade Group", "Kanakapura Road", 12.8112, 77.5150, "apartment", [1, 2, 3], {1: 680, 2: 1100, 3: 1450}, 8400, 30, 3000, 60, "Ready to Move", "2019", 4.4, False, ["Tennis Court", "Badminton Court"]),
    ("Brigade Millennium", "Brigade Group", "JP Nagar 7th Phase", 12.8918, 77.5842, "apartment", [2, 3, 4], {2: 1350, 3: 1850, 4: 2650}, 13200, 15, 1100, 22, "Ready to Move", "2006", 4.6, True, ["Squash Court", "Tennis Court", "Badminton Court", "Auditorium"]),
    ("Brigade Komarla Heights", "Brigade Group", "Padmanabhanagar, South Bengaluru", 12.9125, 77.5542, "apartment", [2, 3], {2: 1150, 3: 1800}, 12100, 2, 320, 4, "Under Construction", "2026", 4.4, False, ["Badminton Court", "Amphitheatre"]),
    ("Total Environment The Magic Faraway Tree", "Total Environment", "Kanakapura Road", 12.8745, 77.5422, "apartment", [3, 4], {3: 2753, 4: 4400}, 16500, 4, 434, 12, "Ready to Move", "2023", 4.7, True, ["Squash Court", "Library", "Heated Pool"]),
    ("Total Environment Learning to Fly", "Total Environment", "JP Nagar", 12.9052, 77.5882, "apartment", [3, 4], {3: 2950, 4: 3850}, 18200, 3, 202, 3.8, "Ready to Move", "2024", 4.7, True, ["Squash Court", "Library"]),
    ("Lodha Azur", "Lodha Group", "Begur, Bannerghatta Road", 12.8780, 77.6142, "apartment", [3, 4], {3: 1900, 4: 3100}, 13600, 4, 550, 10, "Under Construction", "2028", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Mantri Serenity", "Mantri Developers", "Kanakapura Road", 12.8835, 77.5540, "apartment", [2, 3], {2: 1040, 3: 1580}, 10200, 11, 2490, 19.6, "Ready to Move", "2021", 4.1, False, ["Tennis Court", "Badminton Court"]),
    ("Purva Highland", "Puravankara", "Kanakapura Road", 12.8685, 77.5482, "apartment", [2, 3], {2: 1340, 3: 1690}, 9800, 13, 1589, 17.3, "Ready to Move", "2014", 4.3, False, ["Tennis Court", "Badminton Court"]),
    ("Purva Westend", "Puravankara", "Kudlu Gate, Hosur Road", 12.8888, 77.6410, "apartment", [2, 3], {2: 1200, 3: 1750}, 11500, 5, 735, 8.25, "Ready to Move", "2019", 4.4, False, ["Badminton Court", "Open Air Cinema"]),
    ("Salarpuria Sattva Cadenza", "Sattva Group", "Kudlu Gate, Hosur Road", 12.8870, 77.6418, "apartment", [2, 3], {2: 1210, 3: 1850}, 11800, 6, 513, 5.8, "Ready to Move", "2019", 4.4, True, ["Squash Court", "Badminton Court"]),
    ("Godrej Nurture", "Godrej Properties", "Electronic City Phase 1", 12.8495, 77.6695, "apartment", [2, 3], {2: 990, 3: 1470}, 9900, 7, 684, 5.75, "Ready to Move", "2024", 4.3, False, ["Badminton Court", "Kids Arena"]),
    ("Godrej E-City", "Godrej Properties", "Electronic City Phase 1", 12.8428, 77.6512, "apartment", [2, 3], {2: 1050, 3: 1550}, 9200, 17, 860, 15, "Ready to Move", "2018", 4.3, False, ["Badminton Court", "Tennis Court"]),
    ("Ajmera Infinity", "Ajmera Realty", "Electronic City Phase 1", 12.8392, 77.6552, "apartment", [2, 3], {2: 1120, 3: 1620}, 9100, 17, 1350, 11.5, "Ready to Move", "2014", 4.3, False, ["Tennis Court", "Badminton Court"]),
    ("Shriram Summitt", "Shriram Properties", "Electronic City Phase 1", 12.8342, 77.6615, "apartment", [2, 3], {2: 1160, 3: 1480}, 8900, 15, 1140, 15, "Ready to Move", "2019", 4.2, False, ["Tennis Court", "Badminton Court"]),
    ("Hiranandani Club Meadows", "House of Hiranandani", "Bannerghatta Road", 12.8705, 77.6115, "apartment", [2, 3], {2: 1280, 3: 1820}, 11900, 8, 900, 20, "Ready to Move", "2018", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Adarsh Palm Acres", "Adarsh Developers", "Huttanahalli, North Bengaluru", 13.1725, 77.6080, "villa", [4], {4: 3450}, 15200, 1, 300, 80, "Ready to Move", "2022", 4.7, True, ["Squash Court", "Tennis Court", "Badminton Court"]),

    # --- WEST & NORTH-WEST BENGALURU (RAJAJINAGAR / YESHWANTHPUR / MALLESHWARAM / TUMKUR RD / MYSORE RD / OMR) ---
    ("Brigade Gateway", "Brigade Group", "Rajajinagar, Malleshwaram", 13.0126, 77.5558, "apartment", [2, 3, 4], {2: 1370, 3: 1860, 4: 2360}, 16500, 13, 1255, 40, "Ready to Move", "2012", 4.7, True, ["Squash Court", "Tennis Court", "Badminton Court", "Mall Access"]),
    ("Phoenix One Bangalore West", "The Phoenix Mills", "Rajajinagar", 13.0052, 77.5542, "apartment", [2, 3, 4], {2: 1920, 3: 2906, 4: 3573}, 18800, 9, 1000, 17, "Ready to Move", "2021", 4.7, True, ["Squash Court", "Tennis Court", "Badminton Court", "Bowling Alley"]),
    ("Prestige West Woods", "Prestige Group", "Magadi Road, Rajajinagar", 12.9765, 77.5602, "apartment", [2, 3, 4], {2: 1253, 3: 1756, 4: 2570}, 14800, 5, 567, 7.15, "Ready to Move", "2019", 4.6, True, ["Squash Court", "Badminton Court"]),
    ("Sobha Indraprastha", "Sobha Limited", "Rajajinagar", 12.9818, 77.5565, "apartment", [3, 4], {3: 2200, 4: 3150}, 16800, 2, 356, 9.37, "Ready to Move", "2019", 4.6, True, ["Squash Court", "Sky Lounge", "Badminton Court"]),
    ("Salarpuria Sattva Luxuria", "Sattva Group", "Malleshwaram", 13.0102, 77.5642, "apartment", [3, 4], {3: 2225, 4: 3120}, 17200, 2, 197, 4, "Ready to Move", "2016", 4.6, True, ["Squash Court", "Badminton Court"]),
    ("Prestige Jindal City", "Prestige Group", "Tumkur Road, Peenya", 13.0558, 77.4840, "apartment", [1, 2, 3, 4], {1: 607, 2: 1094, 3: 1657, 4: 2171}, 10200, 15, 3571, 32, "Ready to Move", "2023", 4.4, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Sobha Ruby", "Sobha Limited", "Nagasandra, Tumkur Road", 13.0462, 77.5038, "apartment", [2, 3], {2: 1220, 3: 1690}, 10400, 7, 420, 8.2, "Ready to Move", "2014", 4.4, False, ["Tennis Court", "Badminton Court"]),
    ("Godrej Platinum", "Godrej Properties", "Hebbal", 13.0445, 77.5902, "apartment", [3, 4], {3: 2900, 4: 3900}, 15800, 2, 135, 2, "Ready to Move", "2016", 4.6, False, ["Badminton Court", "Sky Deck"]),
    ("Tata Aquila Heights", "Tata Housing", "Jalahalli, Tumkur Road", 13.0485, 77.5345, "apartment", [2, 3], {2: 1520, 3: 2150}, 10900, 3, 325, 4.5, "Ready to Move", "2018", 4.4, False, ["Badminton Court", "Tennis Court"]),
    ("Vaishnavi Sapphire", "Vaishnavi Group", "Yeshwanthpur", 13.0252, 77.5472, "apartment", [2, 3], {2: 1320, 3: 1850}, 13400, 4, 320, 4, "Ready to Move", "2017", 4.4, False, ["Badminton Court", "Mall Access"]),
    ("Provident Sunworth City", "Provident Housing", "Mysore Road, Kengeri", 12.8885, 77.4692, "apartment", [2, 3], {2: 883, 3: 1082}, 7600, 40, 5900, 60, "Ready to Move", "2022", 4.2, False, ["Tennis Court", "Badminton Court", "Cricket Pitch"]),
    ("Purva Blubelle", "Puravankara", "Magadi Road, Rajajinagar", 12.9742, 77.5582, "apartment", [3], {3: 1550}, 14200, 2, 378, 3.85, "Under Construction", "2027", 4.4, False, ["Badminton Court", "Rooftop Lounge"]),
    ("Brigade Buena Vista", "Brigade Group", "Budigere Cross, Old Madras Road", 13.0455, 77.7485, "apartment", [2, 3, 4], {2: 1180, 3: 1690, 4: 2440}, 10200, 4, 740, 7, "Ready to Move", "2021", 4.4, True, ["Squash Court", "Badminton Court", "Tennis Court"]),
    ("Prestige Tranquility", "Prestige Group", "Budigere Cross, Old Madras Road", 13.0502, 77.7520, "apartment", [2, 3], {2: 1136, 3: 1820}, 9800, 17, 2368, 38, "Ready to Move", "2019", 4.4, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Godrej Woodscapes", "Godrej Properties", "Budigere Cross, Whitefield", 13.0422, 77.7465, "apartment", [2, 3, 4], {2: 1285, 3: 1950, 4: 2800}, 11400, 7, 2400, 28, "Under Construction", "2028", 4.4, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Salarpuria Sattva East Crest", "Sattva Group", "Budigere Cross, Old Madras Road", 13.0470, 77.7440, "apartment", [2, 3], {2: 1152, 3: 1550}, 9600, 11, 667, 6.6, "Ready to Move", "2021", 4.3, False, ["Badminton Court", "Tennis Court"]),
    ("Mahindra Eden", "Mahindra Lifespaces", "Kanakapura Road", 12.8665, 77.5372, "apartment", [2, 3], {2: 1250, 3: 1850}, 11200, 4, 527, 7.75, "Under Construction", "2026", 4.5, False, ["Badminton Court", "Net Zero Energy"]),
    ("Mahindra Windchimes", "Mahindra Lifespaces", "Bannerghatta Road", 12.8858, 77.5998, "apartment", [3, 4], {3: 1790, 4: 2950}, 13200, 4, 403, 5.85, "Ready to Move", "2020", 4.5, True, ["Squash Court", "Badminton Court"]),
    ("Brigade Exotica", "Brigade Group", "Old Madras Road", 13.0408, 77.7420, "apartment", [3, 4], {3: 2640, 4: 3600}, 12200, 2, 454, 10.5, "Ready to Move", "2018", 4.6, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Tata Promont", "Tata Housing", "Banashankari 3rd Stage", 12.9275, 77.5478, "apartment", [3, 4], {3: 2380, 4: 3200}, 13600, 4, 312, 14, "Ready to Move", "2018", 4.6, True, ["Squash Court", "Tennis Court", "Hilltop Club"]),
    ("Concorde Manhattan", "Concorde Group", "Electronic City Phase 1", 12.8422, 77.6598, "apartment", [2, 3], {2: 1190, 3: 1620}, 8600, 12, 918, 12, "Ready to Move", "2012", 4.2, False, ["Tennis Court", "Badminton Court"]),
    ("Sobha HRC Pristine", "Sobha Limited", "Jakkur", 13.0765, 77.6040, "apartment", [2, 3, 4], {2: 1450, 3: 1920, 4: 2600}, 12900, 5, 395, 8.5, "Ready to Move", "2023", 4.6, True, ["Squash Court", "Badminton Court"]),
    ("Prestige Finsbury Park Regent", "Prestige Group", "Aerospace Park, Bagalur", 13.1392, 77.6705, "apartment", [3], {3: 1562}, 9600, 6, 958, 10, "Ready to Move", "2024", 4.4, False, ["Badminton Court", "Tennis Court"]),
    ("Sobha Victoria Park", "Sobha Limited", "Hennur Main Road", 13.0602, 77.6485, "apartment", [2, 3], {2: 1419, 3: 1833}, 12600, 5, 319, 6.5, "Under Construction", "2027", 4.5, False, ["Badminton Court", "English Courtyard"]),
    ("Prestige Augusta Golf Village", "Prestige Group", "Horamavu, Hennur", 13.0585, 77.6690, "villa", [3, 4], {3: 2400, 4: 4300}, 16500, 1, 460, 104, "Ready to Move", "2018", 4.7, True, ["Squash Court", "Golf Course", "Tennis Court"]),
    ("Sobha Clovelly", "Sobha Limited", "Padmanabhanagar, Uttarahalli", 12.9090, 77.5515, "apartment", [3, 4], {3: 2050, 4: 2800}, 13400, 2, 137, 3.7, "Ready to Move", "2020", 4.6, False, ["Badminton Court", "Rooftop Pool"]),
    ("Purva Park Hill", "Puravankara", "Kanakapura Road", 12.8740, 77.5495, "apartment", [2, 3, 4], {2: 1410, 3: 1936, 4: 2678}, 11200, 4, 496, 15, "Under Construction", "2026", 4.4, False, ["Badminton Court", "Tennis Court"]),
    ("Salarpuria Sattva Magnificia", "Sattva Group", "Old Madras Road, Tin Factory", 12.9960, 77.6672, "apartment", [3, 4], {3: 1850, 4: 2650}, 13800, 2, 240, 6, "Ready to Move", "2018", 4.5, True, ["Squash Court", "Badminton Court"]),
    ("Prestige Dolce Vita", "Prestige Group", "ECC Road, Whitefield", 12.9765, 77.7465, "apartment", [2, 3], {2: 1267, 3: 1924}, 12800, 2, 66, 1.36, "Ready to Move", "2021", 4.5, False, ["Badminton Court", "Gymnasium"]),
    ("Brigade Woods Phase 2", "Brigade Group", "ITPL, Whitefield", 12.9852, 77.7438, "apartment", [2, 3], {2: 1240, 3: 1740}, 12100, 6, 180, 3.5, "Ready to Move", "2023", 4.4, False, ["Badminton Court", "Cycling Track"]),
    ("Sumadhura Eden Garden", "Sumadhura Infracon", "Doddabanahalli, Whitefield", 13.0258, 77.7560, "apartment", [2, 3], {2: 1120, 3: 1580}, 10100, 10, 1125, 14, "Ready to Move", "2023", 4.4, False, ["Badminton Court", "Tennis Court"]),
    ("Assetz Sun & Sanctum", "Assetz Property Group", "Old Madras Road, KR Puram", 13.0125, 77.7165, "apartment", [2, 3], {2: 1380, 3: 1690}, 11600, 3, 323, 4, "Ready to Move", "2025", 4.4, False, ["Badminton Court", "Amphitheatre"]),
    ("Mantri Alpyne", "Mantri Developers", "Uttarahalli, South Bengaluru", 12.9012, 77.5425, "apartment", [2, 3], {2: 1150, 3: 1595}, 9600, 14, 1250, 13.5, "Ready to Move", "2014", 4.2, False, ["Tennis Court", "Badminton Court"]),
    ("Prestige Notting Hill", "Prestige Group", "Bannerghatta Road", 12.8812, 77.5975, "apartment", [2, 3], {2: 1410, 3: 1850}, 12600, 4, 288, 4.5, "Ready to Move", "2012", 4.5, True, ["Squash Court", "Tennis Court"]),
    ("Prestige South Ridge", "Prestige Group", "Banashankari 3rd Stage", 12.9268, 77.5512, "apartment", [2, 3, 4], {2: 1420, 3: 1950, 4: 2800}, 13800, 4, 344, 9, "Ready to Move", "2014", 4.6, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Sobha Dewflower", "Sobha Limited", "Sarjapur Road, Bellandur", 12.9192, 77.6758, "apartment", [3, 4], {3: 2450, 4: 3450}, 15200, 4, 144, 6.2, "Ready to Move", "2013", 4.7, True, ["Squash Court", "Tennis Court"]),
    ("Prestige Bougainvillea Gardens", "Prestige Group", "Whitefield", 12.9710, 77.7470, "villa", [4], {4: 4400}, 20500, 1, 22, 4.5, "Ready to Move", "2016", 4.7, False, ["Badminton Court", "Private Garden"]),
    ("Prestige Camden Gardens", "Prestige Group", "Thanisandra", 13.0748, 77.6320, "apartment", [3, 4], {3: 1578, 4: 2732}, 13400, 1, 117, 1.83, "Under Construction", "2027", 4.4, False, ["Badminton Court", "Rooftop Deck"]),
    ("Brigade Insignia", "Brigade Group", "Yelahanka", 13.0912, 77.6010, "apartment", [3, 4], {3: 2145, 4: 3114}, 14600, 6, 379, 6, "Under Construction", "2028", 4.5, True, ["Squash Court", "Tennis Court"]),
    ("Godrej Athena", "Godrej Properties", "Indiranagar Extension, HAL", 12.9685, 77.6695, "apartment", [3], {3: 1710}, 15200, 15, 330, 6.5, "Under Construction", "2027", 4.5, False, ["Badminton Court", "Greco-Roman Club"]),
    ("Sobha Insignia", "Sobha Limited", "Bellandur", 12.9285, 77.6808, "apartment", [3, 4], {3: 1819, 4: 3406}, 15800, 2, 33, 1, "Under Construction", "2026", 4.6, False, ["Rooftop Pool", "Gymnasium"]),
    ("Prestige Southern Star", "Prestige Group", "Begur Road, Bannerghatta", 12.8775, 77.6240, "apartment", [2, 3, 4], {2: 1180, 3: 1850, 4: 2650}, 12200, 14, 2130, 35, "Under Construction", "2028", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Sattva Songbird", "Sattva Group", "Budigere Cross, Whitefield", 13.0445, 77.7540, "apartment", [1, 2, 3], {1: 650, 2: 1220, 3: 1780}, 10800, 4, 1321, 12, "Under Construction", "2028", 4.4, False, ["Badminton Court", "Amphitheatre"]),
    ("Assetz Trees & Tandem", "Assetz Property Group", "Sarjapur Road", 12.8780, 77.7720, "apartment", [3], {3: 1885}, 11500, 2, 364, 7, "Under Construction", "2028", 4.4, False, ["Badminton Court", "Tennis Court"]),
    ("Abhee Celestial City", "Abhee Ventures", "Sarjapur Road", 12.8935, 77.7395, "apartment", [2, 3], {2: 1320, 3: 1950}, 10400, 12, 1100, 50, "Under Construction", "2028", 4.3, False, ["Badminton Court", "Tennis Court"]),
    ("Prestige Green Gables", "Prestige Group", "Panathur, Kadubeesanahalli", 12.9390, 77.7078, "apartment", [2, 3], {2: 1111, 3: 1650}, 12900, 4, 406, 5, "Under Construction", "2026", 4.4, False, ["Badminton Court", "Multipurpose Court"]),
    ("Brigade Citrine", "Brigade Group", "Budigere Cross, Whitefield", 13.0480, 77.7495, "apartment", [2, 3, 4], {2: 1200, 3: 1800, 4: 2530}, 11600, 2, 420, 4.3, "Under Construction", "2028", 4.4, False, ["Badminton Court", "Solar Powered"]),
    ("Sobha Crystal Meadows", "Sobha Limited", "Sarjapur Road", 12.8920, 77.7440, "villa", [4], {4: 4237}, 24000, 1, 290, 26.6, "Under Construction", "2029", 4.7, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Prestige Glenbrook", "Prestige Group", "Nallurhalli, Whitefield", 12.9742, 77.7288, "apartment", [3, 4], {3: 1647, 4: 2928}, 13600, 2, 285, 4.5, "Under Construction", "2027", 4.5, False, ["Badminton Court", "Club House"]),
    ("Sobha Galera", "Sobha Limited", "Kannamangala, Whitefield", 13.0255, 77.7715, "villa", [4], {4: 3032}, 16800, 1, 40, 4.08, "Under Construction", "2026", 4.6, False, ["Badminton Court", "Landscaped Gardens"]),
    ("Purva Orient Grand", "Puravankara", "Lalbagh Road, Central Bengaluru", 12.9570, 77.5902, "apartment", [3, 4], {3: 2450, 4: 3360}, 24500, 1, 97, 1.15, "Under Construction", "2027", 4.6, False, ["Sky Lounge", "Concierge"]),
    ("Prestige Woodland Park", "Prestige Group", "Banaswadi, North Bengaluru", 13.0128, 77.6485, "apartment", [2, 3], {2: 1383, 3: 1850}, 13500, 2, 166, 1.5, "Ready to Move", "2020", 4.5, False, ["Badminton Court", "Gymnasium"]),
    ("Sobha Athena", "Sobha Limited", "Yelahanka, Kogilu", 13.0990, 77.6200, "apartment", [3], {3: 1718}, 12200, 1, 72, 1.37, "Ready to Move", "2025", 4.5, False, ["Badminton Court", "Gymnasium"]),
    ("Embassy Boulevard", "Embassy Group", "Yelahanka, Bellary Road", 13.1445, 77.6245, "villa", [4, 5], {4: 4000, 5: 7300}, 21500, 1, 170, 51, "Ready to Move", "2018", 4.8, True, ["Squash Court", "Tennis Court", "Badminton Court", "Spa"]),
    ("Brigade Orchards", "Brigade Group", "Devanahalli", 13.2375, 77.7045, "apartment", [2, 3, 4], {2: 1150, 3: 1650, 4: 2350}, 8800, 18, 2000, 135, "Ready to Move", "2022", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court", "Sports Arena"]),
    ("Provident Park Square", "Provident Housing", "Kanakapura Road", 12.8790, 77.5458, "apartment", [1, 2, 3], {1: 525, 2: 900, 3: 1300}, 9200, 16, 2082, 20, "Ready to Move", "2023", 4.3, False, ["Tennis Court", "Badminton Court"]),
    ("Sattva Park Cubix", "Sattva Group", "Devanahalli", 13.2412, 77.7115, "apartment", [2, 3], {2: 1009, 3: 1498}, 8200, 7, 1620, 18, "Ready to Move", "2023", 4.3, False, ["Badminton Court", "Tennis Court"]),
    ("Tata New Haven", "Tata Housing", "Tumkur Road, Dasanapura", 13.0695, 77.4565, "apartment", [2, 3], {2: 1050, 3: 1450}, 7900, 14, 1500, 25, "Ready to Move", "2018", 4.2, False, ["Tennis Court", "Badminton Court"]),
    ("Prestige Royale Gardens", "Prestige Group", "Yelahanka, Doddaballapur Road", 13.1285, 77.5840, "apartment", [2, 3], {2: 1273, 3: 1705}, 10400, 13, 1696, 22.5, "Ready to Move", "2020", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Sobha Althea", "Sobha Limited", "Yelahanka", 13.1030, 77.5842, "apartment", [3, 4], {3: 1850, 4: 2550}, 11600, 4, 240, 6.5, "Ready to Move", "2012", 4.5, False, ["Tennis Court", "Badminton Court"]),
    ("Brigade Caladium", "Brigade Group", "Hebbal", 13.0465, 77.5968, "apartment", [3, 4], {3: 3450, 4: 4460}, 15600, 1, 64, 2.3, "Ready to Move", "2018", 4.6, False, ["Rooftop Pool", "Gymnasium"]),
    ("Prestige Silver Crest", "Prestige Group", "Sarjapur Road", 12.9128, 77.6788, "apartment", [2, 3], {2: 1250, 3: 1800}, 12800, 2, 122, 2, "Ready to Move", "2014", 4.5, False, ["Badminton Court", "Gymnasium"]),
    ("Salarpuria Sattva Laurel Heights", "Sattva Group", "Hesaraghatta Road, Tumkur Road", 13.0630, 77.5150, "apartment", [2, 3], {2: 1180, 3: 1620}, 8900, 4, 480, 5.5, "Ready to Move", "2020", 4.3, False, ["Badminton Court", "Tennis Court"]),
    ("Prestige Monte Carlo", "Prestige Group", "Yelahanka", 13.1120, 77.5872, "apartment", [2, 3], {2: 1320, 3: 1880}, 10600, 12, 420, 12, "Ready to Move", "2006", 4.4, True, ["Squash Court", "Tennis Court"]),
    ("Purva Riviera", "Puravankara", "Marathahalli", 12.9565, 77.7105, "apartment", [2, 3], {2: 1310, 3: 1890}, 10900, 10, 816, 15, "Ready to Move", "2008", 4.4, False, ["Tennis Court", "Badminton Court"]),
    ("Brigade Metropolis", "Brigade Group", "Mahadevapura, Whitefield", 12.9918, 77.6998, "apartment", [2, 3, 4], {2: 1260, 3: 1750, 4: 2650}, 13400, 14, 1632, 36, "Ready to Move", "2012", 4.6, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Prestige Tech Cloud Residences", "Prestige Group", "Devanahalli", 13.2045, 77.6980, "apartment", [2, 3], {2: 1210, 3: 1720}, 9800, 6, 540, 8, "Under Construction", "2027", 4.4, False, ["Badminton Court", "Co-working Lounge"]),
    ("Sobha Ayana", "Sobha Limited", "Balagere, Panathur", 12.9388, 77.7248, "apartment", [3], {3: 1553}, 13400, 12, 4304, 81, "Under Construction", "2028", 4.5, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Brigade Valencia", "Brigade Group", "Hosur Road, Electronic City", 12.8280, 77.6960, "apartment", [2, 3, 4], {2: 1140, 3: 1680, 4: 2450}, 10600, 6, 1650, 24, "Under Construction", "2027", 4.4, True, ["Squash Court", "Badminton Court"]),
    ("Prestige Sommerville", "Prestige Group", "Marathahalli, Whitefield", 12.9610, 77.7195, "apartment", [2, 3, 4], {2: 1203, 3: 1818, 4: 2616}, 14800, 2, 306, 6.5, "Under Construction", "2027", 4.5, True, ["Squash Court", "Badminton Court"]),
    ("Assetz Canvas & Cove", "Assetz Property Group", "Begur Road, South Bengaluru", 12.8788, 77.6285, "apartment", [2, 3], {2: 1090, 3: 1580}, 10800, 8, 1200, 17, "Under Construction", "2026", 4.4, False, ["Badminton Court", "Lake View Deck"]),
    ("Godrej Tiara", "Godrej Properties", "Yeshwanthpur, Tumkur Road", 13.0285, 77.5425, "apartment", [3, 4], {3: 2200, 4: 3000}, 15600, 3, 350, 5, "Under Construction", "2028", 4.5, True, ["Squash Court", "Badminton Court"]),
    ("Prestige Raintree Villas", "Prestige Group", "Varthur, Whitefield", 12.9522, 77.7345, "villa", [4, 5], {4: 3800, 5: 5100}, 17800, 1, 140, 18, "Under Construction", "2028", 4.6, True, ["Squash Court", "Tennis Court"]),
    ("Sobha Oakshire", "Sobha Limited", "Devanahalli, IVC Road", 13.2185, 77.6580, "villa", [4], {4: 3421}, 15200, 1, 80, 8.5, "Under Construction", "2026", 4.6, False, ["Badminton Court", "Clubhouse"]),
    ("Embassy Springs", "Embassy Group", "Devanahalli", 13.2100, 77.6745, "plot", [0], {}, 7800, 0, 1100, 288, "Ready to Move", "2023", 4.6, True, ["Squash Court", "Tennis Court", "Lake Park"]),
    ("Adarsh Sanctuary", "Adarsh Developers", "Sarjapur Road", 12.8902, 77.7495, "villa", [4], {4: 3200}, 16200, 1, 172, 21, "Ready to Move", "2024", 4.6, True, ["Squash Court", "Tennis Court", "Badminton Court"]),
    ("Purva Tivoli Hills", "Puravankara", "Devanahalli", 13.2345, 77.7265, "plot", [0], {}, 6400, 0, 839, 61, "Ready to Move", "2024", 4.3, False, ["Badminton Court", "Themed Parks"]),
    ("Rohan Antara", "Rohan Builders", "Varthur, Whitefield", 12.9368, 77.7390, "apartment", [2, 3], {2: 1180, 3: 1710}, 11500, 5, 750, 7, "Under Construction", "2027", 4.4, False, ["Badminton Court", "Sky Bridge"]),
    ("Prestige Brooklyn Heights", "Prestige Group", "Banashankari 3rd Stage", 12.9212, 77.5675, "apartment", [3, 4], {3: 1850, 4: 2650}, 14400, 1, 94, 1.5, "Ready to Move", "2018", 4.5, False, ["Badminton Court", "Gymnasium"]),
    ("Sobha Magnolia", "Sobha Limited", "Bannerghatta Road", 12.9248, 77.6012, "apartment", [3], {3: 1920}, 14800, 2, 108, 2.2, "Ready to Move", "2010", 4.5, False, ["Badminton Court", "Swimming Pool"]),
    ("Brigade Lakeview", "Brigade Group", "Hebbal", 13.0498, 77.6042, "apartment", [3, 4], {3: 2050, 4: 2800}, 13600, 3, 210, 4, "Ready to Move", "2016", 4.5, False, ["Badminton Court", "Tennis Court"]),
]

BASE_AMENITIES = [
    "Club House",
    "Jogging and Strolling Track",
    "Power Back Up",
    "Swimming Pool",
    "Lift",
    "Security",
    "Park",
    "Reserved Parking",
    "Visitor Parking",
    "Intercom Facility",
    "Maintenance Staff",
    "Gymnasium",
    "Indoor Games Room",
    "Rain Water Harvesting",
    "CCTV Camera",
    "Kids Play Area",
    "Fire Fighting Equipment",
    "Waste Disposal",
]

REVIEW_TEMPLATES = [
    ("Great community and connectivity", "Well-maintained gated society in {loc} with clean landscaping, reliable power backup, and smooth access to IT corridors and schools.", "Resident"),
    ("Spacious layouts and strong upkeep", "Management keeps common areas spotless. The clubhouse, pool, and walking tracks are actively used every morning and evening.", "Owner"),
    ("Convenient neighbourhood", "Daily groceries, clinics, and good schools are right around {loc}. Peak-hour traffic outside the main road can be busy, but inside the campus it is peaceful.", "Tenant"),
]


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def make_project(idx, row):
    (name, dev, loc, lat, lng, kind, bhks, sqft_map, psf, towers, units, acres, status, possession, rating, has_squash, extras) = row
    rnd = random.Random(1000 + idx)
    mb_id = str(7100000 + idx * 17)
    slug = slugify(f"{name}-{loc}-bangalore")
    url = f"https://www.magicbricks.com/{slug}-pdpid-{mb_id}"
    amenities = list(dict.fromkeys(BASE_AMENITIES + extras + (["Indoor Squash & Badminton Courts"] if has_squash else [])))
    if kind == "builder floor":
        amenities = ["Power Back Up", "Lift", "Security", "Reserved Parking", "CCTV Camera", "Rain Water Harvesting", "Water Storage"]
    elif kind == "plot":
        amenities = ["Club House", "Park", "Security", "Jogging and Strolling Track", "Rain Water Harvesting", "CCTV Camera", "Kids Play Area"] + extras

    # Generate realistic unit configs, sale listings, and rent listings
    unit_list = []
    sale_listings = []
    rent_listings = []
    # Bengaluru typical gross rental yield ~3.0% - 3.6%
    loc_yield = 0.032 + rnd.uniform(-0.004, 0.005)
    for b in bhks:
        if b == 0:
            continue
        sq = sqft_map[b]
        unit_list.append({"bhk": b, "sqft": float(sq), "kind": "10017" if kind == "villa" else "10003" if kind == "builder floor" else "10002"})
        if sq > 1400 and kind == "apartment":
            unit_list.append({"bhk": b, "sqft": float(round(sq * 1.12, -1)), "kind": "10002"})
        # Sale listings
        n_sale = rnd.randint(3, 14) if status == "Ready to Move" else rnd.randint(2, 8)
        for _ in range(n_sale):
            p_psf = round(psf * rnd.uniform(0.92, 1.10))
            price = round(sq * p_psf, -4)
            sale_listings.append({"bhk": b, "price": price, "psf": p_psf, "sqft": sq})
        # Rent listings (mainly for Ready to Move, some for near-ready)
        if status == "Ready to Move":
            n_rent = rnd.randint(2, 10)
            for _ in range(n_rent):
                monthly = round((sq * psf * loc_yield / 12) * rnd.uniform(0.90, 1.12), -2)
                rent_listings.append({"bhk": b, "price": monthly})

    if kind == "plot":
        for sq in (1200, 1500, 2400):
            unit_list.append({"bhk": None, "sqft": float(sq), "kind": "10000"})
            for _ in range(rnd.randint(2, 6)):
                p_psf = round(psf * rnd.uniform(0.94, 1.08))
                sale_listings.append({"bhk": None, "price": round(sq * p_psf, -4), "psf": p_psf, "sqft": sq})

    prices_all = [x["price"] for x in sale_listings]
    price_min = min(prices_all) if prices_all else round(psf * 1200, -4)
    price_max = max(prices_all) if prices_all else round(psf * 2400, -4)

    # 5-year Bengaluru price/sqft appreciation trend
    trend = []
    for yr_i, yr in enumerate(["2022", "2023", "2024", "2025", "2026"]):
        factor = 0.68 + 0.08 * yr_i + rnd.uniform(-0.015, 0.015)
        trend.append([yr, round(psf * min(1.0, factor), -1)])
    trend[-1][1] = psf

    cfg_bhk = ", ".join(str(b) for b in bhks if b)
    kind_word = {"apartment": "Multistorey Apartments", "villa": "Villas", "builder floor": "Builder Floors", "plot": "Residential Plots"}[kind]
    config_text = f"{cfg_bhk} BHK {kind_word}" if cfg_bhk else kind_word

    rera_num = f"PRM/KA/RERA/1251/446/PR/{180000 + idx * 137:06d}"
    reviews = [
        {"title": t, "text": body.format(loc=loc), "date": f"{rnd.randint(10, 28)}/0{rnd.randint(1, 9)}/2026", "by": by, "rating": rating}
        for t, body, by in REVIEW_TEMPLATES[: rnd.randint(2, 3)]
    ]
    ratings = {
        "Connectivity": round(min(5.0, max(3.6, rating + rnd.uniform(-0.3, 0.2))), 1),
        "Lifestyle": round(min(5.0, max(3.8, rating + rnd.uniform(-0.2, 0.3))), 1),
        "Safety": round(min(5.0, max(4.0, rating + rnd.uniform(-0.1, 0.3))), 1),
        "Environment": round(min(5.0, max(3.7, rating + rnd.uniform(-0.2, 0.2))), 1),
    }
    desc = f"{name} by {dev} is a {status.lower()} residential community in {loc}, Bengaluru spread across {acres} acres with {units:,} units ({config_text})."

    return {
        "mb_id": mb_id,
        "name": name,
        "developer": dev,
        "locality": loc,
        "lat": lat,
        "lng": lng,
        "status": status,
        "possession": possession,
        "rera_id": rera_num,
        "units": float(units),
        "towers": float(towers) if towers else None,
        "acres": acres,
        "price_min": float(price_min),
        "price_max": float(price_max),
        "config_text": config_text,
        "type_codes": ["10017" if kind == "villa" else "10003" if kind == "builder floor" else "10000" if kind == "plot" else "10002"],
        "amenities": amenities,
        "configs": {"units": unit_list, "by_bhk": {}},
        "url": url,
        "brochure_url": None,
        "rating": rating,
        "rating_count": rnd.randint(35, 420),
        "review_count": rnd.randint(12, 95),
        "ratings": ratings,
        "reviews": reviews,
        "locality_rating": round(min(4.9, rating - 0.1), 1),
        "sale_count": len(sale_listings) * rnd.randint(2, 5),
        "rent_count": len(rent_listings) * rnd.randint(2, 4) if rent_listings else 0,
        "sale_listings": sale_listings,
        "rent_listings": rent_listings,
        "psf_now": psf,
        "trend": trend,
        "description": desc,
        "images": [],
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    projects = [make_project(i, row) for i, row in enumerate(SOCIETIES)]
    (OUT / "mb_projects.json").write_text(json.dumps(projects, indent=0))
    (OUT / "mb_index.json").write_text(json.dumps(projects, indent=0))
    (OUT / "osm_pois.json").write_text(json.dumps(POIS))
    print(f"Seeded {len(projects)} Bengaluru projects and {len(POIS)} POIs in {OUT}")


if __name__ == "__main__":
    main()
