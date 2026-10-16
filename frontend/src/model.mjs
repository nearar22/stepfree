export const clean = value => value instanceof Map
  ? Object.fromEntries([...value].map(([key, item]) => [key, clean(item)]))
  : Array.isArray(value) ? value.map(clean)
  : value && typeof value === "object" ? Object.fromEntries(Object.entries(value).map(([key, item]) => [key, clean(item)]))
  : typeof value === "bigint" ? Number(value) : value;
export const short = value => value ? `${value.slice(0, 6)}…${value.slice(-4)}` : "";
export const criterionLabel = value => ({ STEP_FREE_CONTINUITY: "Step-free continuity", WIDTH_AND_CLEARANCE: "Width & clearance", GRADIENT_AND_SURFACE: "Gradient & surface", RESTROOM_ACCESS: "Restroom access", EVACUATION_SUPPORT: "Evacuation support" }[value] || value);
export function actionsFor(record, account) {
  if (!record) return [];
  const actor=(account||"").toLowerCase(),owner=(record.owner||"").toLowerCase(),assessor=(record.assessor||"").toLowerCase();
  if(record.status==="EVIDENCE_PENDING")return["freeze"];
  if(record.status==="FROZEN")return["assess"];
  if(record.status==="READY_TO_CERTIFY"&&actor===assessor)return["certify"];
  if(record.status==="NEEDS_REROUTE"&&actor===owner)return["revise"];
  if(["READY_TO_CERTIFY","CERTIFIED"].includes(record.status)&&actor&&actor!==owner&&actor!==assessor)return["challenge"];
  if(record.status==="CHALLENGE_PENDING")return["resolve"];
  return[];
}
