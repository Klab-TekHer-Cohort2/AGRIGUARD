"""PROTOTYPE DATA — Agricultural Crop Knowledge Base.

Contains structured information about crops grown by Rwandan smallholder
farmers.

Sources: FAO, Rwanda Agriculture and Animal Resources Development Board (RAB),
and publicly available agricultural extension literature.

NOTE: This is prototype/demo data. It is not a complete or certified
agricultural reference.

Dict keys are kept identical to the JavaScript version (camelCase) so the
knowledge-base index and RAG article builder produce byte-identical content.
"""

crops = [
    {
        "id": "maize",
        "name": {"en": "Maize", "rw": "Ibigori"},
        "scientificName": "Zea mays",
        "description": {
            "en": "Maize is one of the most important staple crops in Rwanda, grown across all altitude zones.",
            "rw": "Ibigori ni kimwe mu birimwa by'ibanze byingenzi mu Rwanda, biragundwa mu ntera zose z'uburebure.",
        },
        "growingSeasons": ["Season A (Sep-Feb)", "Season B (Mar-Jun)"],
        "altitudeRange": "900–2000 m",
        "commonProblems": [
            "fall-armyworm",
            "maize-streak-virus",
            "gray-leaf-spot",
            "nitrogen-deficiency",
            "drought-stress",
            "stalk-borer",
        ],
        "preventionTips": {
            "en": [
                "Use certified seeds from approved suppliers.",
                "Practice crop rotation with legumes.",
                "Monitor fields regularly, especially during early vegetative stages.",
                "Ensure proper spacing to reduce humidity and disease pressure.",
                "Apply fertiliser according to RAB recommendations.",
            ],
            "rw": [
                "Koresha imbuto zemerewe zaturutse ku bagemurizi bemerewe.",
                "Hindura imyaka ukoresheje ibibyimba.",
                "Genzura inzu z'imyaka buri gihe, cyane cyane mu bihe bya mbere by'imikurire.",
                "Jya ukora umuzi w'ibigori neza kugira ngo ugabanye ubuhehere n'indwara.",
                "Shira ifumbire hakurikijwe inama za RAB.",
            ],
        },
        "expertContact": "Rwanda Agriculture Board (RAB) extension officer",
    },
    {
        "id": "beans",
        "name": {"en": "Beans", "rw": "Ibishyimbo"},
        "scientificName": "Phaseolus vulgaris",
        "description": {
            "en": "Beans are a primary protein source and cash crop for Rwandan farmers, grown in both seasons.",
            "rw": "Ibishyimbo ni inkomoko y'ibwoya kandi ni umusaruro w'amafaranga ku barima b'u Rwanda.",
        },
        "growingSeasons": ["Season A (Sep-Feb)", "Season B (Mar-Jun)"],
        "altitudeRange": "1000–2000 m",
        "commonProblems": [
            "bean-fly",
            "angular-leaf-spot",
            "bean-rust",
            "pythium-root-rot",
            "potassium-deficiency",
            "waterlogging",
        ],
        "preventionTips": {
            "en": [
                "Use disease-resistant varieties recommended by RAB.",
                "Avoid planting in poorly drained soils.",
                "Practice crop rotation — do not plant beans in the same field every season.",
                "Inspect young seedlings for bean fly damage within the first two weeks.",
                "Remove and destroy infected plant material.",
            ],
            "rw": [
                "Koresha ubwoko bw'imbuto bwuzuye indwara bushyigikiwe na RAB.",
                "Irinde gutera mu butaka butagira imiringoti myiza y'amazi.",
                "Hindura imyaka — ntukore ibishyimbo mu murima umwe buri gihembwe.",
                "Genzura inshyitsi nto ku biribwa by'ibibondo mu cyumweru cya mbere n'icya kabiri.",
                "Vana kandi ukumbye ibimera byanduye.",
            ],
        },
        "expertContact": "Rwanda Agriculture Board (RAB) extension officer",
    },
    {
        "id": "cassava",
        "name": {"en": "Cassava", "rw": "Imyumbati"},
        "scientificName": "Manihot esculenta",
        "description": {
            "en": "Cassava is a drought-tolerant food security crop grown widely in lower-altitude Rwanda.",
            "rw": "Imyumbati ni umusaruro w'umutekano w'ibiribwa ushobora guhangana n'amapfa, uragundwa cyane mu ntera zaba hasi mu Rwanda.",
        },
        "growingSeasons": ["Year-round with seasonal planting"],
        "altitudeRange": "700–1800 m",
        "commonProblems": [
            "cassava-mosaic-disease",
            "cassava-brown-streak",
            "cassava-mealybug",
            "whitefly",
            "zinc-deficiency",
            "waterlogging",
        ],
        "preventionTips": {
            "en": [
                "Use CMD-resistant and CBSD-tolerant varieties.",
                "Only plant certified, disease-free cuttings.",
                "Remove and destroy mosaic-infected plants immediately.",
                "Control whitefly populations which spread mosaic virus.",
                "Avoid introducing planting material from infected areas.",
            ],
            "rw": [
                "Koresha ubwoko bwuzuye CMD no kugumya CBSD.",
                "Tera gusa gacaca emerewe, nta ndwara.",
                "Vana kandi ukumbye imyumbati yanduye indwara ya mosaic vuba.",
                "Genzura inyoni zo gutera amata mu buhehere zivura virusi ya mosaic.",
                "Irinde gutera gacaca iturutse mu turere twanduye.",
            ],
        },
        "expertContact": "Rwanda Agriculture Board (RAB) extension officer",
    },
    {
        "id": "irish-potato",
        "name": {"en": "Irish Potato", "rw": "Ibirayi"},
        "scientificName": "Solanum tuberosum",
        "description": {
            "en": "Irish potato is a major cash and food crop grown primarily in the high-altitude regions of Rwanda.",
            "rw": "Ibirayi ni umusaruro w'amafaranga n'ibiribwa by'ingenzi biragundwa cyane mu turere two hejuru mu Rwanda.",
        },
        "growingSeasons": ["Season A (Sep-Feb)", "Season B (Mar-Jun)"],
        "altitudeRange": "1500–2800 m",
        "commonProblems": [
            "late-blight",
            "early-blight",
            "potato-virus-y",
            "aphids",
            "phosphorus-deficiency",
            "frost-damage",
        ],
        "preventionTips": {
            "en": [
                "Use certified, blight-resistant seed tubers.",
                "Apply copper-based fungicides preventively during rainy seasons.",
                "Earthing up reduces tuber exposure to blight spores.",
                "Avoid overhead irrigation which promotes blight spread.",
                "Inspect fields twice weekly during high blight risk periods.",
            ],
            "rw": [
                "Koresha imbuto z'ibirayi emerewe, zuzuye late blight.",
                "Koresha ubuvuzi bwa fungicide ya kobre mbere y'igihe mu bihe by'imvura.",
                "Kubita ubutaka munsi y'ibirayi bigabanya kubonekera kwa blight ku cyori.",
                "Irinde gusukura amazi mu bwirukane bibasha gutera blight gukwirakwira.",
                "Genzura inzu z'imyaka inshuro ebyiri mu cyumweru mu bihe bya blight bya hejuru.",
            ],
        },
        "expertContact": "Rwanda Agriculture Board (RAB) extension officer",
    },
    {
        "id": "tomato",
        "name": {"en": "Tomato", "rw": "Inyanya"},
        "scientificName": "Solanum lycopersicum",
        "description": {
            "en": "Tomatoes are grown as a cash crop across Rwanda, particularly in lowland and valley areas.",
            "rw": "Inyanya ziragundwa nk'umusaruro w'amafaranga mu Rwanda hose, cyane cyane mu turere two hasi no mu biyaga.",
        },
        "growingSeasons": ["Year-round under irrigation"],
        "altitudeRange": "900–1800 m",
        "commonProblems": [
            "early-blight",
            "late-blight",
            "tomato-leaf-miner",
            "whitefly",
            "bacterial-wilt",
            "blossom-end-rot",
            "magnesium-deficiency",
        ],
        "preventionTips": {
            "en": [
                "Use grafted or resistant tomato varieties for blight-prone areas.",
                "Practice crop rotation — avoid planting in fields with recent solanaceous crops.",
                "Install yellow sticky traps to monitor and reduce whitefly populations.",
                "Avoid excessive nitrogen which promotes vegetative growth over fruiting.",
                "Ensure adequate calcium availability to prevent blossom end rot.",
            ],
            "rw": [
                "Koresha ubwoko bw'inyanya yashongewe cyangwa yuzuye indwara mu turere two kugirwa n'indwara ya blight.",
                "Hindura imyaka — irinde gutera mu mirima yari ifite ibimera bya solanaceous vuba aha.",
                "Shira imishono ishungura umuhondo kugira ngo urebe kandi ugabanye inyoni zo gutera amata mu buhehere.",
                "Irinde azote nyinshi zitera imikurire y'amashami aho gutera imbuto.",
                "Menya neza ko kalisiyo ihari bihagije kugira ngo wirinde kurota kw'imbuto.",
            ],
        },
        "expertContact": "Rwanda Agriculture Board (RAB) extension officer",
    },
]
