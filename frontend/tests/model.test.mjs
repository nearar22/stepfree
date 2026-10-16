import test from "node:test";
import assert from "node:assert/strict";
import { actionsFor, clean, criterionLabel, short } from "../src/model.mjs";
test("SDK structures become plain display data",()=>assert.deepEqual(clean(new Map([["revision",1n]])),{revision:1}));
test("route actions follow roles and revocable certification",()=>{const item={owner:"0xaaa",assessor:"0xbbb",status:"EVIDENCE_PENDING"};assert.deepEqual(actionsFor(item,""),["freeze"]);assert.deepEqual(actionsFor({...item,status:"FROZEN"},""),["assess"]);assert.deepEqual(actionsFor({...item,status:"READY_TO_CERTIFY"},"0xBbB"),["certify"]);assert.deepEqual(actionsFor({...item,status:"CERTIFIED"},"0xccc"),["challenge"]);assert.deepEqual(actionsFor({...item,status:"CHALLENGE_PENDING"},""),["resolve"]);assert.deepEqual(actionsFor({...item,status:"NEEDS_REROUTE"},"0xAaA"),["revise"])});
test("human labels stay stable",()=>{assert.equal(criterionLabel("RESTROOM_ACCESS"),"Restroom access");assert.equal(short("0x1234567890abcdef"),"0x1234…cdef")});
