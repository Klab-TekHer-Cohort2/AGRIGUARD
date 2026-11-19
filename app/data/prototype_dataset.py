"""PROTOTYPE DATA — Farmer Reports, Community Data, Demo Scenarios.

All records here are explicitly PROTOTYPE DATA. They do NOT represent real
outbreaks. They exist so the demo and tests have a stable, realistic dataset to
run against.

Realistic Rwandan context:
    - Locations: Kabarore, Gatsibo, Nyagatare, Kayonza, Rwamagana
    - Crops: maize, beans, cassava, irish-potato, tomato
    - Problems: Fall Armyworm, Late Blight, Mosaic Disease, etc.

Coordinates are approximate community centroids (publicly available), NOT
individual farmer locations.

Demo scenarios:
    1. Fall Armyworm cluster in Kabarore (12 reports → HIGH/CRITICAL risk)
    2. Unknown problem with low confidence (→ agronomist escalation)
    3. Isolated reports (→ LOW risk, no outbreak)
"""

from datetime import datetime, timedelta, timezone

# Capture "now" at import time so all timestamps in this dataset are stable
# relative to the moment the module was first loaded. This mirrors the
# JavaScript `const now = Date.now()` pattern.
_NOW = datetime.now(timezone.utc)
_DAY = timedelta(days=1)


def _recent(days_ago: int) -> str:
    """ISO 8601 timestamp for ``days_ago`` days before module load (UTC, 'Z')."""
    dt = _NOW - days_ago * _DAY
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


prototype_dataset = {
    # ── Registered farmers (PROTOTYPE) ──────────────────────────────────────
    # Only farmers with location + contact are eligible for personalised alerts.
    "farmers": [
        {"id": "F001", "name": "Mukamana Beatrice", "lat": -1.4790, "lng": 30.4190, "phone": "+250788111111", "community": "Kabarore"},
        {"id": "F002", "name": "Habimana Jean", "lat": -1.4795, "lng": 30.4195, "phone": "+250788222222", "community": "Kabarore"},
        {"id": "F003", "name": "Uwase Grace", "lat": -1.4800, "lng": 30.4200, "phone": "+250788333333", "community": "Kabarore"},
        {"id": "F004", "name": "Nshimiyimana Eric", "lat": -1.4810, "lng": 30.4210, "phone": "+250788444444", "community": "Kabarore"},
        {"id": "F005", "name": "Mukasine Aline", "lat": -1.4820, "lng": 30.4220, "phone": "+250788555555", "community": "Kabarore"},
        {"id": "F006", "name": "Twizeyimana Paul", "lat": -1.5100, "lng": 30.4300, "phone": "+250788666666", "community": "Gatsibo"},
        {"id": "F007", "name": "Ingabire Diane", "lat": -1.5600, "lng": 30.3300, "phone": "+250788777777", "community": "Nyagatare"},
        {"id": "F008", "name": "Bizimana Claude", "lat": -2.0700, "lng": 30.2500, "phone": "+250788888888", "community": "Kayonza"},
        # Farmer without location → not eligible for personalised radius alerts.
        {"id": "F009", "name": "Umutoni Olive", "lat": None, "lng": None, "phone": None, "community": "Rwamagana"},
    ],

    # ── Farmer reports (PROTOTYPE) ──────────────────────────────────────────
    # Each report mirrors the structure produced by cropAnalysisService.
    "reports": [
        # Scenario 1: Fall Armyworm cluster in Kabarore (12 reports, recent, same crop+problem)
        {"id": "R001", "farmerId": "F001", "crop": "Maize", "cropId": "maize", "problem": "Fall Armyworm", "problemId": "fall-armyworm", "category": "Pest", "confidence": 0.92, "severity": "Moderate", "lat": -1.4790, "lng": 30.4190, "community": "Kabarore", "timestamp": _recent(1)},
        {"id": "R002", "farmerId": "F002", "crop": "Maize", "cropId": "maize", "problem": "Fall Armyworm", "problemId": "fall-armyworm", "category": "Pest", "confidence": 0.90, "severity": "Moderate", "lat": -1.4795, "lng": 30.4195, "community": "Kabarore", "timestamp": _recent(1)},
        {"id": "R003", "farmerId": "F003", "crop": "Maize", "cropId": "maize", "problem": "Fall Armyworm", "problemId": "fall-armyworm", "category": "Pest", "confidence": 0.88, "severity": "High", "lat": -1.4800, "lng": 30.4200, "community": "Kabarore", "timestamp": _recent(2)},
        {"id": "R004", "farmerId": "F004", "crop": "Maize", "cropId": "maize", "problem": "Fall Armyworm", "problemId": "fall-armyworm", "category": "Pest", "confidence": 0.91, "severity": "Moderate", "lat": -1.4810, "lng": 30.4210, "community": "Kabarore", "timestamp": _recent(2)},
        {"id": "R005", "farmerId": "F005", "crop": "Maize", "cropId": "maize", "problem": "Fall Armyworm", "problemId": "fall-armyworm", "category": "Pest", "confidence": 0.93, "severity": "High", "lat": -1.4820, "lng": 30.4220, "community": "Kabarore", "timestamp": _recent(3)},
        {"id": "R006", "farmerId": "F001", "crop": "Maize", "cropId": "maize", "problem": "Fall Armyworm", "problemId": "fall-armyworm", "category": "Pest", "confidence": 0.89, "severity": "Moderate", "lat": -1.4792, "lng": 30.4192, "community": "Kabarore", "timestamp": _recent(3)},
        {"id": "R007", "farmerId": "F002", "crop": "Maize", "cropId": "maize", "problem": "Fall Armyworm", "problemId": "fall-armyworm", "category": "Pest", "confidence": 0.87, "severity": "High", "lat": -1.4797, "lng": 30.4197, "community": "Kabarore", "timestamp": _recent(4)},
        {"id": "R008", "farmerId": "F003", "crop": "Maize", "cropId": "maize", "problem": "Fall Armyworm", "problemId": "fall-armyworm", "category": "Pest", "confidence": 0.90, "severity": "Moderate", "lat": -1.4802, "lng": 30.4202, "community": "Kabarore", "timestamp": _recent(4)},
        {"id": "R009", "farmerId": "F004", "crop": "Maize", "cropId": "maize", "problem": "Fall Armyworm", "problemId": "fall-armyworm", "category": "Pest", "confidence": 0.92, "severity": "High", "lat": -1.4812, "lng": 30.4212, "community": "Kabarore", "timestamp": _recent(5)},
        {"id": "R010", "farmerId": "F005", "crop": "Maize", "cropId": "maize", "problem": "Fall Armyworm", "problemId": "fall-armyworm", "category": "Pest", "confidence": 0.91, "severity": "Critical", "lat": -1.4822, "lng": 30.4222, "community": "Kabarore", "timestamp": _recent(5)},
        {"id": "R011", "farmerId": "F001", "crop": "Maize", "cropId": "maize", "problem": "Fall Armyworm", "problemId": "fall-armyworm", "category": "Pest", "confidence": 0.90, "severity": "High", "lat": -1.4794, "lng": 30.4194, "community": "Kabarore", "timestamp": _recent(6)},
        {"id": "R012", "farmerId": "F002", "crop": "Maize", "cropId": "maize", "problem": "Fall Armyworm", "problemId": "fall-armyworm", "category": "Pest", "confidence": 0.89, "severity": "High", "lat": -1.4799, "lng": 30.4199, "community": "Kabarore", "timestamp": _recent(6)},

        # Scenario 2: Isolated reports (different problems, different areas → LOW risk)
        {"id": "R013", "farmerId": "F006", "crop": "Beans", "cropId": "beans", "problem": "Bean Fly", "problemId": "bean-fly", "category": "Pest", "confidence": 0.74, "severity": "Moderate", "lat": -1.5100, "lng": 30.4300, "community": "Gatsibo", "timestamp": _recent(2)},
        {"id": "R014", "farmerId": "F007", "crop": "Cassava", "cropId": "cassava", "problem": "Cassava Mosaic Disease", "problemId": "cassava-mosaic-disease", "category": "Disease", "confidence": 0.86, "severity": "High", "lat": -1.5600, "lng": 30.3300, "community": "Nyagatare", "timestamp": _recent(3)},
        {"id": "R015", "farmerId": "F008", "crop": "Irish Potato", "cropId": "irish-potato", "problem": "Late Blight", "problemId": "late-blight", "category": "Disease", "confidence": 0.88, "severity": "Critical", "lat": -2.0700, "lng": 30.2500, "community": "Kayonza", "timestamp": _recent(4)},

        # Scenario 3: Unknown problem, low confidence (→ agronomist escalation)
        {"id": "R016", "farmerId": "F009", "crop": "Tomato", "cropId": "tomato", "problem": None, "problemId": None, "category": "Unknown", "confidence": 0.38, "severity": "High", "lat": None, "lng": None, "community": "Rwamagana", "timestamp": _recent(1)},
    ],

    # ── Community summary (PROTOTYPE) ────────────────────────────────────────
    "communities": [
        {"name": "Kabarore", "district": "Gatsibo", "reportCount": 12, "riskLevel": "CRITICAL"},
        {"name": "Gatsibo", "district": "Gatsibo", "reportCount": 1, "riskLevel": "LOW"},
        {"name": "Nyagatare", "district": "Nyagatare", "reportCount": 1, "riskLevel": "LOW"},
        {"name": "Kayonza", "district": "Kayonza", "reportCount": 1, "riskLevel": "LOW"},
        {"name": "Rwamagana", "district": "Rwamagana", "reportCount": 1, "riskLevel": "LOW"},
    ],

    # ── Demo scenarios (PROTOTYPE) ──────────────────────────────────────────
    # Pre-built inputs that reproduce the required demo flow deterministically.
    "demoScenarios": {
        # Smartphone flow: maize + damaged leaves + photo → Fall Armyworm
        "smartphoneReport": {
            "crop": "Maize",
            "description": "The leaves of my maize have holes and I can see small insects near the whorl.",
            "image": "maize-armyworm.jpg",
            "location": {"lat": -1.4790, "lng": 30.4190, "community": "Kabarore"},
            "farmerRequestedHelp": False,
        },
        # Unknown / low confidence scenario
        "unknownReport": {
            "crop": "Tomato",
            "description": "Something strange is happening, I am not sure what it is.",
            "location": {"lat": -2.0700, "lng": 30.2500, "community": "Kayonza"},
            "farmerRequestedHelp": False,
        },
        # Farmer explicitly requests human help
        "farmerRequestsHelp": {
            "crop": "Beans",
            "description": "I want an agronomist to look at my field.",
            "location": {"lat": -1.5100, "lng": 30.4300, "community": "Gatsibo"},
            "farmerRequestedHelp": True,
        },
        # USSD flow: text-only report
        "ussdReport": {
            "farmerId": "F003",
            "crop": "Maize",
            "problemDescription": "Small insects eating maize leaves",
            "location": "Kabarore",
            "channel": "ussd",
        },
        # Ask AgriGuard questions
        "englishQuestion": "My maize leaves are turning yellow, what should I do?",
        "kinyarwandaQuestion": "Ibibabi by'ibigori byanjye birahinduka umuhondo, mbwira n'inama.",
    },

    # Explicit marker so consumers never confuse this with real data.
    "_isPrototype": True,
}

# Convenience aliases mirroring the JS module's top-level exports.
farmers = prototype_dataset["farmers"]
reports = prototype_dataset["reports"]
communities = prototype_dataset["communities"]
demo_scenarios = prototype_dataset["demoScenarios"]
