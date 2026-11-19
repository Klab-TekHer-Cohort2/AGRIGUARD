import logging
from typing import Any, Dict, List, Optional
from app.core.config import settings

logger = logging.getLogger("agriguard.neo4j")

# Seed data for Rwandan Agricultural Knowledge Graph
RWANDA_KNOWLEDGE_GRAPH_SEEDS = [
    {
        "crop": "Maize",
        "crop_rw": "Ibigori",
        "pest": "Fall Armyworm",
        "pest_rw": "Nkongwa",
        "type": "PEST",
        "severity": "HIGH",
        "symptoms": [
            {"en": "ragged leaf feeding holes", "rw": "imyobo mu mababi"},
            {"en": "sawdust-like frass in whorl", "rw": "umukungugu nk'urumece mu mutima w'ikigori"},
            {"en": "visible caterpillar inside central whorl", "rw": "inyo ziri mu mutima w'ikigori"},
            {"en": "windowpane damage on young leaves", "rw": "amababi asa n'ibirahure bitose"}
        ],
        "treatments": [
            {"en": "Apply Neem seed extract or approved bio-pesticide early morning.", "rw": "Fuhira umuti ukozwe mu biti by'umwarubaini kare mu gitondo."},
            {"en": "Handpick and destroy egg masses and caterpillars in small plots.", "rw": "Toragura amagi n'inyo zikiri nto uzangize."},
            {"en": "Use certified insecticides such as Emamectin Benzoate if infestation exceeds 20%.", "rw": "Koresha imiti yemejwe na RAB nka Emamectin Benzoate niba byarenze 20%."}
        ]
    },
    {
        "crop": "Irish Potato",
        "crop_rw": "Ibirayi",
        "pest": "Potato Late Blight",
        "pest_rw": "Imvura y'Ibirayi",
        "type": "DISEASE",
        "severity": "CRITICAL",
        "symptoms": [
            {"en": "water-soaked dark brown spots on leaves", "rw": "amabara yirabura asa n'atose ku mababi"},
            {"en": "white fuzzy fungal growth under damp leaves", "rw": "uruzori rwera munsi y'ibabi ritose"},
            {"en": "rapid blackening and dying of stems", "rw": "amashami ahinduka umukara akuma vuba"}
        ],
        "treatments": [
            {"en": "Apply preventative fungicide (Mancozeb) before rainy periods.", "rw": "Fuhira imiti y'amazi mbere y'imvura nka Mancozeb cyangwa Ridomil."},
            {"en": "Properly hill up soil around potato roots to protect tubers from spores.", "rw": "Kura ibirayi ibyatsi kandi usasire neza ngo imvura itageza ibifunguzo ku birayi."},
            {"en": "Uproot and destroy heavily blighted plants immediately.", "rw": "Randura ibiti byafashwe cyane ubitwike kure y'umurima."}
        ]
    },
    {
        "crop": "Banana",
        "crop_rw": "Ibitoki",
        "pest": "Banana Bacterial Wilt (BXW)",
        "pest_rw": "Kirabiranya y'Ibitoki",
        "type": "DISEASE",
        "severity": "CRITICAL",
        "symptoms": [
            {"en": "yellowing and wilting of leaves", "rw": "amababi ahinduka umuhondo akuma"},
            {"en": "premature uneven fruit ripening", "rw": "igitoki cyera imburagihe kigakomera"},
            {"en": "yellow or brownish bacterial ooze from cut pseudostem", "rw": "amazi y'umuhondo acika iyo utemye umutumba"},
            {"en": "drying and shriveling of the male flower bud", "rw": "umutwe w'igitoki urakaba ukuma"}
        ],
        "treatments": [
            {"en": "Sterilize all farm tools (machetes) using fire or chlorine bleach (JIK) after pruning.", "rw": "Oza imipanga n'amasuka mu muriro cyangwa amazi arimo JIK mbere yo gukata ikindi giti."},
            {"en": "Remove male buds with a wooden fork immediately after bunch formation.", "rw": "Kura umutwe w'igitoki ukoresheje igiti cy'ingasire aho gukoresha umupanga."},
            {"en": "Uproot infected mats and bury them deeply.", "rw": "Randura igitoki cyose cyafashwe ugihambe munsi y'ubutaka."}
        ]
    },
    {
        "crop": "Beans",
        "crop_rw": "Ibishyimbo",
        "pest": "Bean Anthracnose",
        "pest_rw": "Ibimungu by'Ibishyimbo",
        "type": "DISEASE",
        "severity": "MEDIUM",
        "symptoms": [
            {"en": "dark sunken circular spots on bean pods", "rw": "utubara twirabura twicaye ku bishyimbo"},
            {"en": "reddish-purple discoloration along leaf veins", "rw": "imitsi y'amababi ihinduka umutuku wijimye"}
        ],
        "treatments": [
            {"en": "Use certified clean disease-free seeds for planting.", "rw": "Koresha imbuto nziza yemejwe idafite uburwayi."},
            {"en": "Do not weed or harvest when plants are wet with dew or rain.", "rw": "Irinde kugenda mu murima igihe ibiti bitose kuko bikwirakwiza indwara."}
        ]
    },
    {
        "crop": "Cassava",
        "crop_rw": "Imyumbati",
        "pest": "Cassava Mosaic Disease (CMD)",
        "pest_rw": "Ububembe bw'Imyumbati",
        "type": "DISEASE",
        "severity": "HIGH",
        "symptoms": [
            {"en": "yellow and green mosaic patches on leaves", "rw": "amababi arimo ibara ry'icyatsi n'umuhondo bivanze"},
            {"en": "twisted and distorted leaf blades", "rw": "amababi ahinamirana akaba mato cyane"},
            {"en": "stunted overall plant growth", "rw": "igiti kiragwingira ntigikure neza"}
        ],
        "treatments": [
            {"en": "Plant certified resistant cassava stem cuttings (e.g., Gahene, Nase 14).", "rw": "Hinga imbuto y'imyumbati yihanganira ububembe nka Gahene cyangwa Nase 14."},
            {"en": "Rogue (uproot) diseased plants within the first 3 months of planting.", "rw": "Randura ibiti byagaragaje ibimenyetso mu mezi 3 ya mbere ugatwike."}
        ]
    }
]


class Neo4jClient:
    """
    Manages connection to the Neo4j Graph Database.
    Supports Cypher query execution, Knowledge Graph querying,
    and graceful mock fallback when Neo4j is offline in local dev.
    """

    def __init__(self):
        self._driver = None
        self._is_connected = False
        self._mock_data = RWANDA_KNOWLEDGE_GRAPH_SEEDS

    def connect(self):
        """Attempts to initialize the Neo4j driver connection pool."""
        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            self._driver.verify_connectivity()
            self._is_connected = True
            logger.info("Successfully connected to Neo4j Graph Database.")
            self._init_graph_schema()
            self.seed_knowledge_graph()
        except Exception as exc:
            self._is_connected = False
            if settings.NEO4J_MOCK_FALLBACK:
                logger.warning(
                    f"Neo4j offline at {settings.NEO4J_URI} ({exc}). "
                    "Running in MOCK GRAPH mode for AI & symptom reasoning."
                )
            else:
                logger.error(f"Failed to connect to Neo4j: {exc}")
                raise exc

    def close(self):
        """Closes the Neo4j driver connection."""
        if self._driver:
            self._driver.close()
            self._is_connected = False
            logger.info("Neo4j driver connection closed.")

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def _init_graph_schema(self):
        """Sets up uniqueness constraints and indexes in Neo4j."""
        if not self._is_connected:
            return

        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Crop) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Pest) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (v:Village) REQUIRE v.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:District) REQUIRE d.name IS UNIQUE"
        ]
        with self._driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint notice: {e}")

    def seed_knowledge_graph(self):
        """Seeds the Rwandan crop pest knowledge graph into Neo4j."""
        if not self._is_connected:
            return

        query = """
        MERGE (c:Crop {name: $crop, name_rw: $crop_rw})
        MERGE (p:Pest {name: $pest, name_rw: $pest_rw, type: $type, severity: $severity})
        MERGE (c)-[:SUSCEPTIBLE_TO]->(p)
        WITH p
        UNWIND $symptoms AS s_data
            MERGE (s:Symptom {name: s_data.en, name_rw: s_data.rw})
            MERGE (p)-[:EXHIBITS_SYMPTOM]->(s)
        WITH p
        UNWIND $treatments AS t_data
            MERGE (t:Treatment {description: t_data.en, description_rw: t_data.rw})
            MERGE (p)-[:RECOMMENDED_TREATMENT]->(t)
        """
        try:
            with self._driver.session() as session:
                for entry in self._mock_data:
                    session.run(query, entry)
            logger.info("Rwandan agricultural knowledge graph seeded in Neo4j.")
        except Exception as exc:
            logger.error(f"Error seeding Neo4j knowledge graph: {exc}")

    def query_symptoms_for_crop(self, crop_name: str, language: str = "en") -> List[Dict[str, Any]]:
        """
        Retrieves symptoms associated with a given crop.
        Traverses: (Crop)-[:SUSCEPTIBLE_TO]->(Pest)-[:EXHIBITS_SYMPTOM]->(Symptom)
        """
        if self._is_connected:
            cypher = """
            MATCH (c:Crop)-[:SUSCEPTIBLE_TO]->(p:Pest)-[:EXHIBITS_SYMPTOM]->(s:Symptom)
            WHERE toLower(c.name) = toLower($crop_name) OR toLower(c.name_rw) = toLower($crop_name)
            RETURN DISTINCT 
                s.name AS symptom_en, 
                s.name_rw AS symptom_rw,
                p.name AS pest_name,
                p.severity AS pest_severity
            """
            try:
                with self._driver.session() as session:
                    result = session.run(cypher, crop_name=crop_name)
                    return [record.data() for record in result]
            except Exception as e:
                logger.error(f"Neo4j query error: {e}")

        # Fallback to in-memory graph
        matches = []
        for entry in self._mock_data:
            if (entry["crop"].lower() == crop_name.lower() or 
                entry["crop_rw"].lower() == crop_name.lower()):
                for sym in entry["symptoms"]:
                    matches.append({
                        "symptom_en": sym["en"],
                        "symptom_rw": sym["rw"],
                        "pest_name": entry["pest"],
                        "pest_severity": entry["severity"]
                    })
        return matches

    def infer_pest_from_symptoms(
        self, crop_name: str, reported_symptoms: List[str], language: str = "en"
    ) -> Dict[str, Any]:
        """
        AI Reasoning Engine: Matches reported symptoms against the Knowledge Graph
        and calculates confidence score based on symptom overlap.
        """
        candidates: Dict[str, Dict[str, Any]] = {}

        # Use mock knowledge base or query Neo4j
        relevant_entries = [
            e for e in self._mock_data 
            if e["crop"].lower() == crop_name.lower() or e["crop_rw"].lower() == crop_name.lower()
        ]

        if not relevant_entries:
            # If crop not strictly matched, search all
            relevant_entries = self._mock_data

        for entry in relevant_entries:
            pest_name = entry["pest"]
            pest_symptoms = [s["en"].lower() for s in entry["symptoms"]] + [s["rw"].lower() for s in entry["symptoms"]]
            matched_count = 0
            
            for reported in reported_symptoms:
                r_clean = reported.lower().strip()
                if any(r_clean in sym or sym in r_clean for sym in pest_symptoms):
                    matched_count += 1

            total_symptoms = len(entry["symptoms"])
            score = round(min(1.0, (matched_count / max(1, total_symptoms)) + 0.3), 2) if matched_count > 0 else 0.1

            candidates[pest_name] = {
                "pest_name": entry["pest"],
                "pest_name_rw": entry["pest_rw"],
                "type": entry["type"],
                "severity": entry["severity"],
                "confidence": score,
                "matched_symptoms_count": matched_count,
                "recommendations": entry["treatments"],
            }

        if not candidates:
            return {
                "predicted_pest": "Unknown Pest / Suspected Nutrient Deficiency",
                "confidence": 0.30,
                "severity": "LOW",
                "recommendations": [{"en": "Monitor crop closely and consult local agronomist.", "rw": "Komeza gukurikirana umurima kandi wegere umwunganizi mu buhinzi."}]
            }

        # Rank candidate with highest confidence
        best_candidate = max(candidates.values(), key=lambda x: x["confidence"])
        return {
            "predicted_pest": best_candidate["pest_name"],
            "predicted_pest_rw": best_candidate["pest_name_rw"],
            "confidence": best_candidate["confidence"],
            "severity": best_candidate["severity"],
            "recommendations": [
                r[language] if language in r else r["en"] 
                for r in best_candidate["recommendations"]
            ],
            "raw_candidates": list(candidates.values())
        }

    def check_connection(self) -> Dict[str, Any]:
        """Returns health status of the Neo4j graph database."""
        return {
            "status": "connected" if self._is_connected else "mock_mode",
            "uri": settings.NEO4J_URI,
            "connected": self._is_connected,
            "mock_fallback_active": not self._is_connected and settings.NEO4J_MOCK_FALLBACK
        }


# Global Neo4j singleton instance
neo4j_client = Neo4jClient()
