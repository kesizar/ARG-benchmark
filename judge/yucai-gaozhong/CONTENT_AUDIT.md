# Source and route audit

Evidence: preserved original game.js, live recovered index and all 42 assets; normal UI event logs contain state snapshots after each actual input. No test writes localStorage or invokes the original debug __YC API.

Real reasoning gates (ordinary clue browsing is not credited):

- school-number: enter 1329 into old school registry (not merely click highlighted gap). Wrong1328/name queries do not award E. Registry accessed from 2013 search snapshot; only best route requires E.
- netdisk-code: derive 201321 from deleted notice 育才〔2013〕21号. Wrong code stays locked. Success awards C. T improves clue wording but is not a hard prerequisite; no invented dependency.
- guard-teacher: first obtain C; answer 周国栋, not principal 张建国 / 王达申 / 李浩然. Correct choice simultaneously awards V/Z and flashlight, opens gate. Wrong answers remain retryable and do not award trust. No scoring distinction between choosing names and receiving these multiple artifacts.
- report-five: five questions all correct simultaneously, answers [0,2,0,2,1]. Students 林苑, direct culprit 王达申, missing teacher 陈一鸣, remains 旧操场西南角, core combination 学籍断号1329＋操场水泥覆盖＋黑色笔记本. Entire report is one all-or-nothing gate, because source persists only reportOk, no independent per-question success. Wrong/partial submission does not set flag. The source reveals evidence explanations including answers after rejection; document this difficulty weakness.

Twenty artifacts S,S2,S3,T,U,K,E,C,H,B,Z,V,J,Y,R,F,A,M,P,L are preserved. Search 林苑 gives S; old campus search gives T and links U/E; calendar triple tap gives K; research appendix H; school photo long press or banner hotspot S3; netdisk C; guard V/Z; both duty log alternatives B (rubbing additionally b2011); yard J; bike diary Y/R; flashlight hall S2; stair watch F; diary-gated podium A; A+Y-gated floor recorder M; enough evidence in Lin mail L; C+K mailbox inquiry P. P and S3 are optional, not mandatory route gates. Calendar print alternate awards K, no extra reasoning credit. Number2317/search305 only flavor flags. Panorama image and scene art are local.

9 scenes: gate, watch, yard, bike, bld, hall, stair, f3, r305. Gate/yard/bike can be visited without trust. Building side door requires gateOpen, set only with correct guard answer, which also supplies flashlight. Thus hall's no-flash message exists in source but is not reachable under a normal unmodified state. 305 podium requires Y; floor recorder requires Y+A. Leaving old campus persists lastScene; repeated nights increment nights and change narrative. At night>=3 with L, 305 includes optional Lin encounter. No timed death: night clock is cosmetic, no deadline branch. Repeated collection is idempotent. Empty/general/under-evidenced mailbox inquiry, wrong registry/code/teacher/report, locked building, missing diary/podium, leave scene and restart are nonterminal failure/retry/exit branches; no fictional deaths added.

Source final eligibility: report available only stage>=5. Stage5 reached by weight>=90 OR A+B+Y. Final confirm additionally requires reportOk. Finale registers state.ended/ending before visible ending text; independent judge waits until #ycEndT is visibly displayed, so starting the cinematic does not score completion. Historical ending archive is never the endpoint hook.

Authored ending conditions, in priority order:

- witness13: A+B+Y+M+(V or Z)+L+C+E. Best explicit evidence chain; gates school-number/netdisk-code/guard-teacher/report-five.
- blank: weight>=90,A+B+Y AND absence of V,Z,L,M. Unreachable: B requires zhaoTrust, which atomically awards both V/Z. Preserved author content, excluded from scored routes.
- restore: weight>=90,A+B+Y plus at least one V/Z/L/M, and witness13 not satisfied. Netdisk/guard/report gates; E is not mandatory.
- minute13: weight>=45 with preceding branches false. A/B/guard/netdisk/E are not mandatory. Normal ending, report gate only. Acceptance deliberately omits guard/B/A and still finishes.
- unresolved: weight<45. Unreachable normal final entry: stage5 requires weight90, or A+B+Y already weight45 (indeed guard/C raises further). Cannot reset evidence without resetting stage. Preserved author content, excluded from scored routes.

No repairs were made to unlock impossible endings or require missing optional clues. Existing legacy judge incorrectly counted merely seeing a photo and could match ending archive text; replaced by state-backed inference gates and current visible finale evidence. Original ENDINGS only calls minute13/restore regular endings and witness13 a hidden ending. No explicit author good/bad ranking was found in the preserved complete original JS/HTML/CSS. Narrative outcomes do not authorize an inferred good ranking. All three reachable judge routes therefore use neutral normal tier with good_ending=false; authored regular/hidden labels remain separate metadata. Unreachable blank/unresolved carry no scored tier.

Formal scoring review remains required: report rejection reveals solutions; multiple author endings impossible; 2011 class/cohort labels and diary chronology show narrative inconsistencies. These do not break engineering execution but affect content/difficulty claims. No paid model API was called.
