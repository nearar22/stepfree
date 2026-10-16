import json, sys

CONTRACT = "contracts/stepfree.py"
PROFILE_URL = "https://venue.example/access/profile"
SURVEY_URL = "https://access-audit.example/routes/main-hall"
COUNTER_URL = "https://community.example/reports/lift-outage"
REVISED_URL = "https://new-audit.example/routes/ramp-detour"
ASSESSOR = "0x2222222222222222222222222222222222222222"
WAYPOINTS = json.dumps(["North entrance", "Lift lobby", "Level two corridor", "Studio 4"])
PROFILE = "Step-free continuity: the north entrance, lift lobby, level two corridor, and Studio 4 are connected without stairs. Width and clearance: every doorway on this route is at least 920 millimetres. Gradient and surface: the entrance ramp is 1:20 with a firm non-slip surface. Restroom access: an accessible restroom is available beside the level two lift. Evacuation support: the refuge point has two-way communication and trained staff assistance."
SURVEY = "Independent route survey confirms a continuous step-free path from the north entrance to Studio 4. Measured clear door width is 930 millimetres at the narrowest point. The ramp gradient measured 1:20 and the surface was firm and slip resistant. The level two accessible restroom was unlocked and usable. The refuge intercom connected to staffed security during the inspection."
COUNTER = "Community access report: the level two lift was out of service during the evening event, breaking the only step-free connection to Studio 4. Staff could not provide an equivalent alternate route."
REVISED = "Independent follow-up survey confirms a temporary exterior ramp detour from the north entrance directly to Studio 4. The route is continuous, 1100 millimetres wide, has a 1:20 gradient, reaches the accessible restroom, and terminates beside the staffed evacuation refuge."
CRITERIA = ["STEP_FREE_CONTINUITY", "WIDTH_AND_CLEARANCE", "GRADIENT_AND_SURFACE", "RESTROOM_ACCESS", "EVACUATION_SUPPORT"]
PROFILE_QUOTES = ["the north entrance, lift lobby, level two corridor, and Studio 4 are connected without stairs", "every doorway on this route is at least 920 millimetres", "the entrance ramp is 1:20 with a firm non-slip surface", "an accessible restroom is available beside the level two lift", "the refuge point has two-way communication and trained staff assistance"]
SURVEY_QUOTES = ["a continuous step-free path from the north entrance to Studio 4", "Measured clear door width is 930 millimetres", "The ramp gradient measured 1:20 and the surface was firm and slip resistant", "The level two accessible restroom was unlocked and usable", "The refuge intercom connected to staffed security"]


def enable_consensus(contract, monkeypatch):
    module = sys.modules[contract.__class__.__module__]
    monkeypatch.setattr(module.gl.eq_principle, "strict_eq", lambda fn: fn())
    monkeypatch.setattr(module.gl.eq_principle, "prompt_comparative", lambda fn, *_args, **_kwargs: fn())


def result(blocked=False):
    rows = []
    for index, criterion in enumerate(CRITERIA):
        state = "BLOCKED" if blocked and index == 0 else "PASS"
        rows.append({"criterion": criterion, "state": state})
    return {"criteria": rows}


def create(contract):
    return contract.create_route("studio-four-route", "Harbor Arts Hall", "Wheelchair user requires a continuous step-free route, accessible restroom, and verified evacuation support.", WAYPOINTS, PROFILE_URL, SURVEY_URL, ASSESSOR)


def web_mocks(vm, survey_url=SURVEY_URL, survey_text=SURVEY):
    vm.mock_web(PROFILE_URL, {"method": "GET", "status": 200, "body": PROFILE})
    vm.mock_web(survey_url, {"method": "GET", "status": 200, "body": survey_text})


def mock_llm(vm, value):
    vm.mock_llm("STEPFREE_PRODUCER", json.dumps(json.dumps(value)))


def prepare(contract, vm, monkeypatch, assessment=None):
    enable_consensus(contract, monkeypatch); route_id = create(contract); web_mocks(vm); contract.freeze_route(route_id); vm.clear_mocks(); mock_llm(vm, assessment or result()); contract.assess_route(route_id); vm.clear_mocks(); return route_id


def test_contract_loads(direct_deploy):
    assert direct_deploy(CONTRACT) is not None


def test_rejects_duplicate_sources_waypoints_and_assessor(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    with direct_vm.expect_revert("distinct authorities"):
        contract.create_route("same-host-route", "Harbor Arts Hall", "Wheelchair user needs a complete step-free route and restroom access.", WAYPOINTS, PROFILE_URL, "https://venue.example/other", ASSESSOR)
    with direct_vm.expect_revert("unique"):
        contract.create_route("duplicate-waypoint", "Harbor Arts Hall", "Wheelchair user needs a complete step-free route and restroom access.", json.dumps(["Lobby", "Lobby"]), PROFILE_URL, SURVEY_URL, ASSESSOR)
    with direct_vm.expect_revert("distinct valid address"):
        contract.create_route("same-assessor", "Harbor Arts Hall", "Wheelchair user needs a complete step-free route and restroom access.", WAYPOINTS, PROFILE_URL, SURVEY_URL, str(direct_vm.sender))


def test_freeze_stores_complete_route_and_bodies(direct_vm, direct_deploy, monkeypatch):
    contract = direct_deploy(CONTRACT); enable_consensus(contract, monkeypatch); route_id = create(contract); web_mocks(direct_vm); frozen = contract.freeze_route(route_id); record = contract.get_route(route_id); snapshot = record["snapshots"][0]
    assert frozen["status"] == "FROZEN" and snapshot["complete"] is True
    assert snapshot["waypoints"] == json.loads(WAYPOINTS)
    assert [row["content"] for row in snapshot["documents"]] == [PROFILE, SURVEY]
    assert len(snapshot["digest"]) == 64


def test_all_criteria_required_and_quotes_bound(direct_vm, direct_deploy, monkeypatch):
    contract = direct_deploy(CONTRACT); enable_consensus(contract, monkeypatch); route_id = create(contract); web_mocks(direct_vm); contract.freeze_route(route_id); direct_vm.clear_mocks()
    missing = result(); missing["criteria"].pop(); mock_llm(direct_vm, missing)
    with direct_vm.expect_revert("Every accessibility criterion"):
        contract.assess_route(route_id)
    direct_vm.clear_mocks(); forged = result(); forged["criteria"][0]["state"] = "UNKNOWN"; mock_llm(direct_vm, forged)
    with direct_vm.expect_revert("Invalid accessibility state"):
        contract.assess_route(route_id)


def test_blocked_route_cannot_be_certified(direct_vm, direct_deploy, monkeypatch):
    contract = direct_deploy(CONTRACT); route_id = prepare(contract, direct_vm, monkeypatch, result(True)); record = contract.get_route(route_id)
    assert record["status"] == "NEEDS_REROUTE" and record["route_gate"] == "BLOCKED"
    direct_vm.sender = ASSESSOR
    with direct_vm.expect_revert("not eligible"):
        contract.certify_route(route_id)


def test_passable_route_requires_assessor_and_can_be_challenged(direct_vm, direct_deploy, direct_alice, monkeypatch):
    contract = direct_deploy(CONTRACT); route_id = prepare(contract, direct_vm, monkeypatch)
    with direct_vm.expect_revert("appointed assessor"):
        contract.certify_route(route_id)
    direct_vm.sender = ASSESSOR; certified = contract.certify_route(route_id)
    assert certified["status"] == "CERTIFIED" and certified["route_gate"] == "PASSABLE"
    direct_vm.sender = direct_alice; challenged = contract.challenge_route(route_id, COUNTER_URL, "The only lift was unavailable and no equivalent step-free detour was offered.")
    assert challenged["status"] == "CHALLENGE_PENDING" and contract.get_route_gate(route_id)["route_gate"] == "BLOCKED"


def test_upheld_challenge_forces_reroute_and_preserves_history(direct_vm, direct_deploy, direct_alice, monkeypatch):
    contract = direct_deploy(CONTRACT); route_id = prepare(contract, direct_vm, monkeypatch); direct_vm.sender = ASSESSOR; contract.certify_route(route_id); direct_vm.sender = direct_alice; contract.challenge_route(route_id, COUNTER_URL, "The lift outage breaks the certified step-free route and no alternate path was available.")
    direct_vm.mock_web(COUNTER_URL, {"method": "GET", "status": 200, "body": COUNTER}); direct_vm.mock_llm("STEPFREE_CHALLENGE", json.dumps(json.dumps({"verdict": "UPHELD", "criterion": "STEP_FREE_CONTINUITY", "counter_quote": "the level two lift was out of service", "reason": "The outage removes the only step-free connection described by the certified route."})))
    ruling = contract.resolve_challenge(route_id); direct_vm.clear_mocks()
    assert ruling["status"] == "NEEDS_REROUTE" and ruling["route_gate"] == "BLOCKED"
    direct_vm.sender = bytes.fromhex(contract.get_route(route_id)["owner"][2:]); revised = contract.revise_route(route_id, json.dumps(["North entrance", "Exterior ramp detour", "Studio 4"]), REVISED_URL)
    assert revised["revision"] == 1 and revised["preserved_snapshots"] == 1
    direct_vm.mock_web(REVISED_URL, {"method": "GET", "status": 200, "body": REVISED}); frozen = contract.freeze_route(route_id); record = contract.get_route(route_id)
    assert frozen["status"] == "FROZEN" and len(record["snapshots"]) == 2
    assert record["snapshots"][0]["documents"][0]["sha256"] == record["snapshots"][1]["documents"][0]["sha256"]
