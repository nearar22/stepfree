import { createAccount, createClient } from "genlayer-js";
import { studioDevnet } from "genlayer-js/chains";

const contract = process.env.CONTRACT_ADDRESS?.trim();
const raw = process.env.GENLAYER_PRIVATE_KEY?.trim();
const secondary = process.env.GENLAYER_SECONDARY_PRIVATE_KEY?.trim();
if (!contract || !raw || !secondary) throw new Error("CONTRACT_ADDRESS and both GenLayer private keys are required");
const key = value => value.startsWith("0x") ? value : `0x${value}`;
const chain = { ...studioDevnet, id: 61997, name: "GenLayer Studio Next", rpcUrls: { default: { http: ["https://studio-next.genlayer.com/api"] } } };
const owner = createClient({ chain, account: createAccount(key(raw)) });
const assessorAccount = createAccount(key(secondary));
const assessor = createClient({ chain, account: assessorAccount });
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const resumeId = process.env.ROUTE_ID?.trim();
const id = resumeId || `stepfree-${Date.now().toString(36)}`;
const profile = "https://raw.githubusercontent.com/nearar22/stepfree/main/docs/venue-profile.txt";
const survey = "https://cdn.jsdelivr.net/gh/nearar22/stepfree@main/docs/independent-survey.txt";

async function finalized(hash) {
  for (let index = 0; index < 300; index++) {
    const receipt = await owner.getTransaction({ hash }).catch(() => null);
    const status = String(receipt?.statusName ?? receipt?.status ?? "PENDING").toUpperCase();
    if (status === "FINALIZED") return receipt;
    if (["UNDETERMINED", "DECLINED", "CANCELED", "CANCELLED"].includes(status)) throw new Error(`Transaction ended ${status}`);
    await sleep(3000);
  }
  throw new Error("Transaction timed out");
}

async function write(client, label, functionName, args, intelligent = false) {
  const fees = await client.estimateTransactionFees({ leaderTimeunitsAllocation: intelligent ? 500n : 180n, validatorTimeunitsAllocation: intelligent ? 600n : 360n });
  const hash = await client.writeContract({ address: contract, functionName, args, fees });
  console.log(`${label}_TX=${hash}`);
  const receipt = await finalized(hash);
  const execution = String(receipt.txExecutionResultName ?? receipt.txExecutionResult);
  if (execution !== "FINISHED_WITH_RETURN") throw new Error(`${label} failed: ${execution}`);
  return hash;
}

if (!resumeId) {
  await write(owner, "CREATE", "create_route", [id, "Harbor Arts Hall", "Wheelchair user requires a continuous step-free route, accessible restroom, and verified evacuation support.", JSON.stringify(["North entrance", "Lift lobby", "Level two corridor", "Studio 4"]), profile, survey, assessorAccount.address]);
  await write(owner, "FREEZE", "freeze_route", [id], true);
}
await write(owner, "ASSESS", "assess_route", [id], true);
let state = await owner.readContract({ address: contract, functionName: "get_route", args: [id], jsonSafeReturn: true });
console.log(`ROUTE_ID=${id}\nASSESSMENT=${state.assessment?.overall}\nSTATE=${state.status}\nGATE=${state.route_gate}`);
if (!["PASSABLE", "ASSISTED"].includes(state.assessment?.overall) || state.status !== "READY_TO_CERTIFY" || state.route_gate !== "BLOCKED") throw new Error("Live assessment did not preserve the certification gate");
await write(assessor, "CERTIFY", "certify_route", [id]);
state = await owner.readContract({ address: contract, functionName: "get_route", args: [id], jsonSafeReturn: true });
console.log(`FINAL_STATE=${state.status}\nFINAL_GATE=${state.route_gate}`);
if (state.status !== "CERTIFIED" || !["PASSABLE", "ASSISTED"].includes(state.route_gate)) throw new Error("Live assessor certification failed");
