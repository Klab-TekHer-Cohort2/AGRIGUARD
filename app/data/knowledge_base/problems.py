"""PROTOTYPE DATA — Pest / Disease / Deficiency Knowledge Base.

Structured info on common crop problems in Rwanda.
Categories: Pest | Disease | NutrientDeficiency | EnvironmentalStress | Unknown

Sources: FAO, RAB, CABI Crop Protection Compendium (public summaries).
NOTE: Prototype data — not a complete agricultural reference.

Dict keys are kept identical to the JavaScript version (camelCase).
"""

problems = [
    # ── PESTS ──────────────────────────────────────────────────────────────
    {
        "id": "fall-armyworm",
        "name": {"en": "Fall Armyworm", "rw": "Inzito y'ibigori"},
        "scientificName": "Spodoptera frugiperda",
        "category": "Pest",
        "affectedCrops": ["maize"],
        "severityExample": "Moderate",
        "symptoms": {
            "en": [
                "Irregular holes and ragged feeding on leaves",
                "Window-pane damage on young leaves",
                "Sawdust-like frass near the whorl",
                "Larvae hiding in the maize whorl during the day",
                "Complete defoliation in severe cases",
            ],
            "rw": [
                "Imyanya idahindura n'amababi yafunguye nabi",
                "Impanuka nk'amadirishwa ku mababi mata",
                "Mu gihindure amatunguru ya sawdust hafi y'uruhinja",
                "Udukoko two mu ruhinja rw'ibigori mu manya",
                "Kw'amababi yose mu bihe bikomeye",
            ],
        },
        "recommendations": {
            "en": [
                "Inspect nearby maize plants, especially the whorl, for larvae.",
                "Monitor the affected field every 2–3 days.",
                "Use fall armyworm pheromone traps for early detection.",
                "Apply locally approved biological or chemical control following RAB guidance.",
                "Contact an agronomist if the infestation spreads rapidly.",
            ],
            "rw": [
                "Genzura ibigori byo hafi, cyane cyane uruhinja, urebe utudomoko.",
                "Komeza genzura umurima buri minsi 2–3.",
                "Koresha uturingo twa pheromone kugira ngo menye vuba.",
                "Koresha uburyo bwemewe na RAB bwo kurwanya utudomoko.",
                "Vuga umuhinzi w'ubuhinzi niba bibanduka vuba.",
            ],
        },
        "confidence": 0.92,
        "keywords": ["armyworm", "insects", "holes", "leaves", "whorl", "frass", "maize"],
    },
    {
        "id": "stalk-borer",
        "name": {"en": "Maize Stalk Borer", "rw": "Udukoro ku biti by'ibigori"},
        "scientificName": "Busseola fusca",
        "category": "Pest",
        "affectedCrops": ["maize"],
        "severityExample": "Moderate",
        "symptoms": {
            "en": [
                "Deadheart symptoms in young plants",
                "Holes in the stem and wilting",
                "Sawdust-like frass at entry holes",
                "Stunted growth and yellowing",
            ],
            "rw": [
                "Imypanuka yo gufa y'imitima mu birimwa bibiri",
                "Imyanda ku giti n'ukweyize",
                "Amatunguru ya sawdust ku myanda y'injira",
                "Kugenda nabi no guhindura umuhondo",
            ],
        },
        "recommendations": {
            "en": [
                "Inspect stems for bore holes and frass.",
                "Remove and destroy infested plants.",
                "Use crop rotation to disrupt the pest cycle.",
                "Follow RAB-approved integrated pest management.",
            ],
            "rw": [
                "Genzura imisatsi urebe imyanda n'amatunguru.",
                "Vana kandi ukumye ibiribwa byanduye.",
                "Hindura imyaka kugira ngo ugabanye umuzunguko w'udomoko.",
                "Kurikiza inama za RAB zo kugenzura udokoko.",
            ],
        },
        "confidence": 0.78,
        "keywords": ["stalk", "borer", "stem", "holes", "wilting", "maize"],
    },
    {
        "id": "bean-fly",
        "name": {"en": "Bean Fly", "rw": "Udukoko two mu bashyimbo"},
        "scientificName": "Ophiomyia phaseoli",
        "category": "Pest",
        "affectedCrops": ["beans"],
        "severityExample": "High",
        "symptoms": {
            "en": [
                "Yellowing and wilting of seedlings",
                "Tunnels in the stem base",
                "Stunted or dead young plants",
                "Split stems reveal maggots",
            ],
            "rw": [
                "Guhindura umuhondo n'ukweyize ku bibondo",
                "Imyanda mu gice cyo hasi cy'igiti",
                "Ibibondo bikomeza nabi cyangwa bi fite",
                "Mu gukomata ibiti byerekana amafi",
            ],
        },
        "recommendations": {
            "en": [
                "Inspect seedlings within 1–2 weeks of emergence.",
                "Use seed treatment with RAB-approved insecticide.",
                "Remove and destroy infected plants.",
                "Plant in rotation and avoid consecutive bean crops.",
            ],
            "rw": [
                "Genzura ibibondo mu cyumweru cya 1–2 cyo kubyara.",
                "Koresha ubuvuzi bw'imbuto na RAB wemewe.",
                "Vana kandi ukumye ibimera byanduye.",
                "Tera ukoresheje guhindura imyaka, irinde gutera ibishyimba buri gihe.",
            ],
        },
        "confidence": 0.74,
        "keywords": ["bean", "fly", "seedling", "yellow", "wilting", "maggot"],
    },
    {
        "id": "aphids",
        "name": {"en": "Aphids", "rw": "Imibyembe"},
        "scientificName": "Myzus persicae",
        "category": "Pest",
        "affectedCrops": ["irish-potato", "tomato"],
        "severityExample": "Moderate",
        "symptoms": {
            "en": [
                "Clusters of small soft-bodied insects under leaves",
                "Curled or distorted leaves",
                "Sticky honeydew on the plant surface",
                "Sooty mould growth on honeydew",
            ],
            "rw": [
                "Mu byari by'udukoko duto cyane munsi y'amababi",
                "Amababi atabaye cyangwa ataruhuye",
                "Umwembe ushize ku gice cy'ikimera",
                "Ubukara bwa sooty ku mwembe",
            ],
        },
        "recommendations": {
            "en": [
                "Monitor for aphid colonies under leaves.",
                "Use insecticidal soap or neem-based sprays.",
                "Encourage natural predators like ladybirds.",
                "Remove heavily infested plant parts.",
                "Follow RAB-approved pest control guidance.",
            ],
            "rw": [
                "Genzura ibyari by'imibyembe munsi y'amababi.",
                "Koresha savo y'udokoko cyangwa neem.",
                "Erekana inzoka z'ikirera nka ladybird.",
                "Vana amababi yanduye cyane.",
                "Kurikiza inama za RAB.",
            ],
        },
        "confidence": 0.81,
        "keywords": ["aphid", "small", "insects", "under", "leaves", "sticky", "honeydew"],
    },
    {
        "id": "whitefly",
        "name": {"en": "Whitefly", "rw": "Udukoko tukara tuzitiriye"},
        "scientificName": "Bemisia tabaci",
        "category": "Pest",
        "affectedCrops": ["cassava", "tomato"],
        "severityExample": "Moderate",
        "symptoms": {
            "en": [
                "Small white insects flying when plant is disturbed",
                "Yellowing and curling of leaves",
                "Whitefly nymphs on the underside of leaves",
                "Virus-like symptoms on cassava (mosaic)",
            ],
            "rw": [
                "Udukoko tukara tuto dukoze igihe ikimera kimeze",
                "Guhindura umuhondo n'ukunyegama kw'amababi",
                "Amahuri ya whitefly munsi y'amababi",
                "Ibimenyetso bya virusi ku myumbati (mosaic)",
            ],
        },
        "recommendations": {
            "en": [
                "Install yellow sticky traps to monitor adults.",
                "Remove weeds that host whitefly.",
                "Use RAB-approved insecticide if infestation is severe.",
                "Control whitefly to reduce virus transmission.",
            ],
            "rw": [
                "Shira umushono wera umuhondo kugira ngo urebe utukoko.",
                "Vana ibyatsi bya virusi bya whitefly.",
                "Koresha ubuvuzi bwa RAB niba ari bibyimbye.",
                "Genzura whitefly kugira ngo ugabanye kwanduza virusi.",
            ],
        },
        "confidence": 0.79,
        "keywords": ["whitefly", "white", "insects", "flying", "curling", "virus"],
    },
    {
        "id": "cassava-mealybug",
        "name": {"en": "Cassava Mealybug", "rw": "Udukoko two ku myumbati"},
        "scientificName": "Phenacoccus manihoti",
        "category": "Pest",
        "affectedCrops": ["cassava"],
        "severityExample": "Moderate",
        "symptoms": {
            "en": [
                "White cottony masses on stems and leaf bases",
                "Stunted and distorted plant growth",
                "Yellowing and premature leaf drop",
                "Reduced tuber yield",
            ],
            "rw": [
                "Ingingo zera nk'ubworo ku misatsi n'ku gice cy'amababi",
                "Kugenda nabi n'ikimera kidahinduka neza",
                "Guhindura umuhondo n'amababi akungira vuba",
                "Gutanga nabi kw'imyumbati",
            ],
        },
        "recommendations": {
            "en": [
                "Inspect stems and leaf bases for white masses.",
                "Use biological control — parasitoid wasps where available.",
                "Remove and burn heavily infested plants.",
                "Plant clean, mealybug-free cuttings.",
            ],
            "rw": [
                "Genzura imisatsi n'amababi urebe ingingo zera.",
                "Koresha uburyo bw'ikirera — inzoka za parasitoid.",
                "Vana kandi ushyire ku mudomo ibimera byanduye.",
                "Tera gacaca nta mealybug.",
            ],
        },
        "confidence": 0.77,
        "keywords": ["mealybug", "white", "cottony", "cassava", "stunted"],
    },
    # ── DISEASES ────────────────────────────────────────────────────────────
    {
        "id": "maize-streak-virus",
        "name": {"en": "Maize Streak Virus", "rw": "Indwara ya streak y'ibigori"},
        "scientificName": "Maize streak virus",
        "category": "Disease",
        "affectedCrops": ["maize"],
        "severityExample": "High",
        "symptoms": {
            "en": [
                "Chlorotic streaks along leaf veins",
                "Yellowish parallel streaks on young leaves",
                "Stunted and severely reduced yield",
                "Spread by leafhoppers",
            ],
            "rw": [
                "Imypanuka yera n'umuhondo ku mababi",
                "Impanuka z'umuhondo ku mababi mata",
                "Kugenda nabi n'umusaruro uri munsi",
                "Iterwa n'udukoko two guhaha",
            ],
        },
        "recommendations": {
            "en": [
                "Remove and destroy infected plants immediately.",
                "Control leafhopper populations.",
                "Use MSV-resistant maize varieties.",
                "Avoid planting near infected fields.",
            ],
            "rw": [
                "Vana kandi ukumye ibimera byanduye vuba.",
                "Genzura ubwinshi bwa leafhopper.",
                "Koresha ubwoko bw'ibigori bwuzuye MSV.",
                "Irinde gutera hafi y'imirima yanduye.",
            ],
        },
        "confidence": 0.85,
        "keywords": ["streak", "yellow", "veins", "maize", "leafhopper"],
    },
    {
        "id": "gray-leaf-spot",
        "name": {"en": "Gray Leaf Spot", "rw": "Indwara ya gray leaf spot"},
        "scientificName": "Cercospora zeae-maydis",
        "category": "Disease",
        "affectedCrops": ["maize"],
        "severityExample": "Moderate",
        "symptoms": {
            "en": [
                "Gray to tan rectangular lesions on leaves",
                "Lesions parallel to leaf veins",
                "Premature leaf death in severe cases",
                "Most severe in humid conditions",
            ],
            "rw": [
                "Imypanuka yera nka tan-erukura ku mababi",
                "Imypanuka ikurikije imyenda y'amababi",
                "Gufa kw'amababi vuba mu bihe bikomeye",
                "Bikomeye cyane mu bihe by'ubuhehere",
            ],
        },
        "recommendations": {
            "en": [
                "Use resistant maize hybrids.",
                "Practice crop rotation with non-host crops.",
                "Improve field drainage and reduce humidity.",
                "Apply fungicide if severe, per RAB guidance.",
            ],
            "rw": [
                "Koresha ubwoko bw'ibigori bwuzuye indwara.",
                "Hindura imyaka n'ibyo bitari ibigori.",
                "Kongera gutunga kw'ubutaka no kugabanya ubuhehere.",
                "Koresha fungicide niba ari bikomeye, hakurikijwe RAB.",
            ],
        },
        "confidence": 0.80,
        "keywords": ["gray", "lesion", "spot", "tan", "humidity", "maize"],
    },
    {
        "id": "angular-leaf-spot",
        "name": {"en": "Angular Leaf Spot", "rw": "Indwara ya angular leaf spot"},
        "scientificName": "Pseudocercospora griseola",
        "category": "Disease",
        "affectedCrops": ["beans"],
        "severityExample": "Moderate",
        "symptoms": {
            "en": [
                "Angular brown spots on leaves",
                "Spots limited by leaf veins",
                "Yellow halo around lesions",
                "Premature defoliation",
            ],
            "rw": [
                "Imypanuka y'umukara nk'imikongo ku mababi",
                "Imypanuka igabanijwe n'imyenda y'amababi",
                "Uruzitiro rw'umuhondo ku ngingo",
                "Kw'amababi vuba",
            ],
        },
        "recommendations": {
            "en": [
                "Use ALS-resistant bean varieties.",
                "Practice crop rotation.",
                "Remove infected plant debris.",
                "Apply RAB-approved fungicide preventively.",
            ],
            "rw": [
                "Koresha ubwoko bw'ibishyimbo bwuzuye ALS.",
                "Hindura imyaka.",
                "Vana amasaka y'ibimera byanduye.",
                "Koresha fungicide ya RAB hakurikijwe inama.",
            ],
        },
        "confidence": 0.76,
        "keywords": ["angular", "brown", "spot", "lesion", "beans", "halo"],
    },
    {
        "id": "late-blight",
        "name": {"en": "Late Blight", "rw": "Indwara ya late blight"},
        "scientificName": "Phytophthora infestans",
        "category": "Disease",
        "affectedCrops": ["irish-potato", "tomato"],
        "severityExample": "Critical",
        "symptoms": {
            "en": [
                "Water-soaked dark green to brown lesions on leaves",
                "White mould on underside of lesions in humid conditions",
                "Rapid leaf collapse and necrosis",
                "Tuber rot in potato",
            ],
            "rw": [
                "Imypanuka ya kijyagana nk'amazi ku mababi",
                "Ubukara buera munsi y'imypanuka mu bihe by'ubuhehere",
                "Kw'amababi byihuse n'ukw'ibimenyetso",
                "Gukwandura kw'ibirayi mu mafunguro",
            ],
        },
        "recommendations": {
            "en": [
                "Use certified, blight-resistant seed.",
                "Apply copper-based fungicide preventively during rainy season.",
                "Destroy infected plants immediately.",
                "Avoid overhead irrigation.",
                "Escalate to agronomist — late blight can destroy a crop in days.",
            ],
            "rw": [
                "Koresha imbuto zemerewe, zuzuye blight.",
                "Koresha fungicide ya kobre mbere y'igihe mu gihe cy'imvura.",
                "Kumye ibimera byanduye vuba.",
                "Irinde gusukura amazi ku giti.",
                "Vuga umuhinzi — late blight ishobora kwangiza umusaruro mu minsi.",
            ],
        },
        "confidence": 0.88,
        "keywords": ["blight", "water", "brown", "mould", "rot", "potato", "tomato"],
    },
    {
        "id": "early-blight",
        "name": {"en": "Early Blight", "rw": "Indwara ya early blight"},
        "scientificName": "Alternaria solani",
        "category": "Disease",
        "affectedCrops": ["irish-potato", "tomato"],
        "severityExample": "High",
        "symptoms": {
            "en": [
                "Concentric ring lesions (target-spot) on leaves",
                "Yellowing around older lesions",
                "Lesions on stems and tubers",
                "Premature defoliation",
            ],
            "rw": [
                "Imypanuka y'imirongo iburyo (target-spot) ku mababi",
                "Guhindura umuhondo hafi y'imypanuka ya kera",
                "Imypanuka ku misatsi n'ibirayi",
                "Kw'amababi vuba",
            ],
        },
        "recommendations": {
            "en": [
                "Use resistant varieties where available.",
                "Practice crop rotation — 2–3 years without solanaceous crops.",
                "Remove infected plant debris.",
                "Apply RAB-approved fungicide.",
            ],
            "rw": [
                "Koresha ubwoko bwuzuye aho bwubahirijwe.",
                "Hindura imyaka — imyaka 2–3 nta solanaceous.",
                "Vana amasaka y'ibimera byanduye.",
                "Koresha fungicide ya RAB.",
            ],
        },
        "confidence": 0.83,
        "keywords": ["early", "blight", "concentric", "ring", "target", "potato", "tomato"],
    },
    {
        "id": "cassava-mosaic-disease",
        "name": {"en": "Cassava Mosaic Disease", "rw": "Indwara ya mosaic y'imyumbati"},
        "scientificName": "African cassava mosaic virus",
        "category": "Disease",
        "affectedCrops": ["cassava"],
        "severityExample": "High",
        "symptoms": {
            "en": [
                "Mottled, yellow and green mosaic pattern on leaves",
                "Distorted and twisted leaves",
                "Stunted plant growth",
                "Reduced tuber yield",
            ],
            "rw": [
                "Imypanuka y'umuhongo n'icyatsi (mosaic) ku mababi",
                "Amababi atahinduka neza n'ukwangukirwa",
                "Kugenda nabi kw'ikimera",
                "Umusaruro w'imyumbati munsi",
            ],
        },
        "recommendations": {
            "en": [
                "Use CMD-resistant varieties (e.g. from RAB).",
                "Remove and destroy infected plants.",
                "Control whitefly which spreads the virus.",
                "Plant only disease-free cuttings.",
            ],
            "rw": [
                "Koresha ubwoko bwuzuye CMD (kurikiza RAB).",
                "Vana kandi ukumye ibimera byanduye.",
                "Genzura whitefly ivura virusi.",
                "Tera gusa gacaca nta ndwara.",
            ],
        },
        "confidence": 0.86,
        "keywords": ["mosaic", "mottled", "yellow", "green", "cassava", "twisted"],
    },
    {
        "id": "bacterial-wilt",
        "name": {"en": "Bacterial Wilt", "rw": "Indwara ya bacterial wilt"},
        "scientificName": "Ralstonia solanacearum",
        "category": "Disease",
        "affectedCrops": ["tomato"],
        "severityExample": "Critical",
        "symptoms": {
            "en": [
                "Sudden wilting of the entire plant",
                "Bacterial ooze from cut stems",
                "Yellowing of lower leaves",
                "Plant death within days",
            ],
            "rw": [
                "Kweyize byihuse by'ikimera cyose",
                "Ibyatsi by'ubaktiriya ku misatsi yacitwe",
                "Guhindura umuhondo kw'amababi ya hasi",
                "Gufa kw'ikimera mu minsi",
            ],
        },
        "recommendations": {
            "en": [
                "Remove and destroy infected plants immediately.",
                "Avoid planting solanaceous crops in the same soil for 3+ years.",
                "Use disease-free seedlings.",
                "Escalate to agronomist — bacterial wilt is soil-borne and persistent.",
            ],
            "rw": [
                "Vana kandi ukumye ibimera byanduye vuba.",
                "Irinde gutera solanaceous mu butaka bumwe imyaka 3+.",
                "Koresha ibibondo nta ndwara.",
                "Vuga umuhinzi — bacterial wilt iri mu butaka kandi ikomeza.",
            ],
        },
        "confidence": 0.84,
        "keywords": ["wilt", "sudden", "ooze", "bacterial", "tomato", "yellowing"],
    },
    # ── NUTRIENT DEFICIENCIES ────────────────────────────────────────────────
    {
        "id": "nitrogen-deficiency",
        "name": {"en": "Nitrogen Deficiency", "rw": "Kubura kw'azote"},
        "scientificName": "N deficiency",
        "category": "NutrientDeficiency",
        "affectedCrops": ["maize", "beans", "cassava", "irish-potato", "tomato"],
        "severityExample": "Moderate",
        "symptoms": {
            "en": [
                "Yellowing (chlorosis) starting from older lower leaves",
                "Stunted plant growth",
                "Pale green overall appearance",
                "Reduced tillering in cereals",
            ],
            "rw": [
                "Guhindura umuhondo (chlorosis) guturutse ku mababi ya hasi",
                "Kugenda nabi kw'ikimera",
                "Gufata mu maso y'icyatsi gikaze",
                "Kugabanya imyaka y'ibyatsi",
            ],
        },
        "recommendations": {
            "en": [
                "Apply nitrogen fertiliser (urea or NPK) per RAB recommendations.",
                "Incorporate organic matter or compost.",
                "Practice crop rotation with nitrogen-fixing legumes.",
                "Test soil before fertiliser application.",
            ],
            "rw": [
                "Koresha ifumbire ya azote (urea cyangwa NPK) hakurikijwe RAB.",
                "Shyira mu butaka ibyatsi cyangwa ifumbire y'ibimera.",
                "Hindura imyaka n'ibibyimba bifasha gukora azote.",
                "Gerageza ubutaka mbere yo koresha ifumbire.",
            ],
        },
        "confidence": 0.72,
        "keywords": ["yellow", "chlorosis", "pale", "stunted", "lower", "leaves", "nitrogen"],
    },
    {
        "id": "potassium-deficiency",
        "name": {"en": "Potassium Deficiency", "rw": "Kubura kw'potasiyumu"},
        "scientificName": "K deficiency",
        "category": "NutrientDeficiency",
        "affectedCrops": ["beans", "maize", "irish-potato", "tomato"],
        "severityExample": "Moderate",
        "symptoms": {
            "en": [
                "Yellowing and browning at leaf margins (edges)",
                "Symptoms on older leaves first",
                "Weak stems and lodging in cereals",
                "Poor fruit/tuber quality",
            ],
            "rw": [
                "Guhindura umuhondo n'umukara ku ngingo z'amababi",
                "Ibimenyetso ku mababi ya kera",
                "Imisatsi yereranye n'isigamira",
                "Gutanga nabi kw'imbuto cyangwa imyumbati",
            ],
        },
        "recommendations": {
            "en": [
                "Apply potash (KCl or NPK with K) per RAB guidance.",
                "Use compost or green manure.",
                "Test soil for potassium levels.",
                "Avoid excessive nitrogen which worsens K imbalance.",
            ],
            "rw": [
                "Koresha potashi (KCl cyangwa NPK na K) hakurikijwe RAB.",
                "Koresha ifumbire y'ibimera cyangwa compost.",
                "Gerageza ubutaka uburebure bwa potasiyumu.",
                "Irinde azote nyinshi zitera K kunanirana.",
            ],
        },
        "confidence": 0.70,
        "keywords": ["yellow", "brown", "margins", "edges", "potassium", "lodging"],
    },
    {
        "id": "phosphorus-deficiency",
        "name": {"en": "Phosphorus Deficiency", "rw": "Kubura kw'fOSifore"},
        "scientificName": "P deficiency",
        "category": "NutrientDeficiency",
        "affectedCrops": ["maize", "irish-potato", "beans"],
        "severityExample": "Moderate",
        "symptoms": {
            "en": [
                "Dark green or purplish leaves",
                "Stunted root and shoot growth",
                "Delayed maturity",
                "Poor tillering",
            ],
            "rw": [
                "Amababi y'icyatsi cyijima cyangwa cy'umukara",
                "Kugenda nabi kw'imizzi n'amashami",
                "Kworohera gukura",
                "Kugabanya imyaka y'ibyatsi",
            ],
        },
        "recommendations": {
            "en": [
                "Apply DAP or NPK fertiliser at planting.",
                "Apply near the root zone for uptake.",
                "Use rock phosphate or organic compost on acidic soils.",
                "Test soil pH — phosphorus uptake is poor in very acidic soil.",
            ],
            "rw": [
                "Koresha DAP cyangwa NPK igihe cyo gutera.",
                "Shyira hafi y'imizzi kugira ngo ifungure.",
                "Koresha phosphate ya butaka cyangwa compost ku butaka bworoshye.",
                "Gerageza pH y'ubutaka — phosphorus ifungura nabi mu butaka bworoshye cyane.",
            ],
        },
        "confidence": 0.69,
        "keywords": ["purple", "dark", "green", "stunted", "phosphorus", "maturity"],
    },
    {
        "id": "magnesium-deficiency",
        "name": {"en": "Magnesium Deficiency", "rw": "Kubura kw'magnESiyumu"},
        "scientificName": "Mg deficiency",
        "category": "NutrientDeficiency",
        "affectedCrops": ["tomato", "irish-potato"],
        "severityExample": "Low",
        "symptoms": {
            "en": [
                "Interveinal chlorosis (yellow between veins) on older leaves",
                "Leaves may develop reddish or purple tint",
                "Symptoms progress upward as deficiency worsens",
            ],
            "rw": [
                "Guhindura umuhondo hagati y'imyenda (interveinal) ku mababi ya kera",
                "Amababi ashobora kugira ibara cy'umutuku",
                "Ibimenyetso byiyongera hejuru n'uko ibibazo bikomeza",
            ],
        },
        "recommendations": {
            "en": [
                "Apply magnesium sulphate (Epsom salts) or dolomitic lime.",
                "Maintain balanced soil pH.",
                "Use foliar Mg spray for quick correction.",
                "Test soil for Mg levels.",
            ],
            "rw": [
                "Koresha magnasiyumu sulufate cyangwa dolomitic lime.",
                "Komeza pH y'ubutaka ibanze.",
                "Koresha Mg spray y'amababi kugira ngo vuba.",
                "Gerageza ubutaka uburebure bwa Mg.",
            ],
        },
        "confidence": 0.66,
        "keywords": ["interveinal", "yellow", "veins", "magnesium", "magnESiyumu", "purple"],
    },
    {
        "id": "zinc-deficiency",
        "name": {"en": "Zinc Deficiency", "rw": "Kubura kw'zinki"},
        "scientificName": "Zn deficiency",
        "category": "NutrientDeficiency",
        "affectedCrops": ["cassava", "maize"],
        "severityExample": "Low",
        "symptoms": {
            "en": [
                "Interveinal chlorosis on young leaves",
                "Shortened internodes and stunted growth",
                "Narrow, rosette-like leaf arrangement",
                "White bands on maize leaves",
            ],
            "rw": [
                "Guhindura umuhondo hagati y'imyenda ku mababi mata",
                "Kugenda nabi n'ingingo nini",
                "Amababi makuru nka rosette",
                "Imirongo yera ku mababi y'ibigori",
            ],
        },
        "recommendations": {
            "en": [
                "Apply zinc sulphate as soil or foliar application.",
                "Avoid over-liming which reduces zinc availability.",
                "Use zinc-enriched compound fertilisers.",
                "Test soil pH and zinc levels.",
            ],
            "rw": [
                "Koresha zinc sulphate mu butaka cyangwa ku mababi.",
                "Irinde koresha lime nyinshi bikagabanya zinc.",
                "Koresha ifumbire ikungahaye kuri zinc.",
                "Gerageza pH n'uburebure bwa zinc.",
            ],
        },
        "confidence": 0.64,
        "keywords": ["interveinal", "young", "leaves", "stunted", "zinc", "rosette"],
    },
    # ── ENVIRONMENTAL STRESS ────────────────────────────────────────────────
    {
        "id": "drought-stress",
        "name": {"en": "Drought Stress", "rw": "Amapfa"},
        "scientificName": "Water deficit",
        "category": "EnvironmentalStress",
        "affectedCrops": ["maize", "beans", "cassava", "irish-potato", "tomato"],
        "severityExample": "High",
        "symptoms": {
            "en": [
                "Wilting during the day, partial recovery at night",
                "Leaf rolling and curling",
                "Dry, brittle leaf edges",
                "Premature senescence of lower leaves",
            ],
            "rw": [
                "Kweyize ku manya, byongera gukira nijoro",
                "Kunyegama n'ukwangukirwa kw'amababi",
                "Ingingo z'amababi za kamere",
                "Kw'amababi ya hasi vuba",
            ],
        },
        "recommendations": {
            "en": [
                "Apply irrigation if available, especially during critical growth stages.",
                "Use mulch to conserve soil moisture.",
                "Plant drought-tolerant varieties.",
                "Practice water harvesting and conservation tillage.",
            ],
            "rw": [
                "Koresha amazi niba ahari, cyane mu bihe by'ingenzi by'imikurire.",
                "Koresha ibikomere by'ibyatsi kugira ngo umaze igihe.",
                "Tera ubwoko bw'amapfa.",
                "Koresha gukunga amazi n'ubuhinzi bw'ubutaka.",
            ],
        },
        "confidence": 0.73,
        "keywords": ["drought", "wilting", "dry", "curling", "rolling", "water", "stress"],
    },
    {
        "id": "waterlogging",
        "name": {"en": "Waterlogging", "rw": "Kwitura amazi nyinshi"},
        "scientificName": "Excess water",
        "category": "EnvironmentalStress",
        "affectedCrops": ["beans", "cassava", "tomato"],
        "severityExample": "Moderate",
        "symptoms": {
            "en": [
                "Yellowing and wilting despite wet soil",
                "Stunted root growth and root rot",
                "Leaf drop and reduced vigour",
                "Algae or moss on the soil surface",
            ],
            "rw": [
                "Guhindura umuhondo n'ukweyize n'ubwo butaka ari buhehere",
                "Kugenda nabi kw'imizzi n'ukwandura kw'imizzi",
                "Kw'amababi n'kugabanya imbaraga",
                "Algae cyangwa moss ku butaka",
            ],
        },
        "recommendations": {
            "en": [
                "Improve field drainage with raised beds or channels.",
                "Avoid planting in low-lying waterlogged areas.",
                "Use waterlogging-tolerant varieties.",
                "Reduce irrigation frequency.",
            ],
            "rw": [
                "Kongera gutunga kw'ubutaka n'imirima y'hejuru cyangwa umuyoboro.",
                "Irinde gutera mu byatsi byo hasi cyo kwitura amazi.",
                "Koresha ubwoko bwuzuye kwitura amazi.",
                "Kaganya imirima yo gusukura amazi.",
            ],
        },
        "confidence": 0.71,
        "keywords": ["water", "wet", "yellow", "wilting", "waterlogging", "drainage", "rot"],
    },
    {
        "id": "frost-damage",
        "name": {"en": "Frost Damage", "rw": "Kwandura n'ubukonje"},
        "scientificName": "Low temperature",
        "category": "EnvironmentalStress",
        "affectedCrops": ["irish-potato", "tomato", "beans"],
        "severityExample": "High",
        "symptoms": {
            "en": [
                "Water-soaked patches on leaves that turn black",
                "Wilting and blackening of young tissue",
                "Leaf curling downward",
                "Symptoms worst after cold nights",
            ],
            "rw": [
                "Imypanuka y'amazi ku mababi byahita bikara",
                "Kweyize n'ikara by'udukoko tw'ibibondo",
                "Kunyegama kw'amababi ku mana",
                "Ibimenyetso bikomeye nyuma y'ijoro rikonje",
            ],
        },
        "recommendations": {
            "en": [
                "Avoid planting frost-sensitive crops in frost-prone valleys.",
                "Use mulch or row covers on cold nights.",
                "Plant after the last expected frost date.",
                "Irrigate lightly before frost — wet soil retains heat.",
            ],
            "rw": [
                "Irinde gutera ibiribwa by'ubukonje mu biyaga bya frost.",
                "Koresha ibikomere cyangwa imyambaro mu bihe by'ubukonje.",
                "Tera nyuma y'igihe cy'ubukonje cyanyuma.",
                "Sukura amazi merere mbere ya frost — ubutaka bw'amazi bubika ubushyuhe.",
            ],
        },
        "confidence": 0.68,
        "keywords": ["frost", "cold", "black", "water", "soaked", "wilt", "night"],
    },
]
