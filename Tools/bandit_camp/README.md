# Úkol 3 – Banditský tábor (greybox v UE 5.5)

Level: `Content/Skvt/BanditCamp/L_BanditCamp` · AI: `Content/Skvt/BanditCamp/AI`
Screenshot shora se zakreslenými cestami: `Tools/bandit_camp/screenshots/BanditCamp_Top_Routes.png`

Celé se to dá přestavět z běžícího editoru:

```
python Tools/ue_exec.py --timeout 10 -f Tools/bandit_camp/build_all.py
```

(`build_level.py` blockout, `build_ai.py` bandité a hlídky, `build_routes.py` trasy, `screenshot.py` snímky.
Pozor: `build_level.py` smaže a znovu vytvoří všechno ve složce Outlineru `Camp`.)

## Co je v levelu

| Prvek | Kde (X = sever, Y = východ) |
|---|---|
| Vraní skála 600 UU + hřeben (rampa od JZ přes vyhlídku) | sever, X 1800+ |
| Potok – koryto hloubka 120 UU | východ, Y 2000–2600 |
| Houští s kozí stezkou (ulička 120 UU) + 2 pasti s plechovkami (červené) | západ |
| Lesní cesta + posed (plošina 300 UU, zvon) | jih |
| Kápův stan (2×, dutý, boční vchod, zadní stěna „prořízni zde“, truhla) | pod skálou |
| Schody + lano schované za kápovým stanem | X 1620–1800 |
| 2 stany, ohniště s lavicemi, rožeň, kotlík, plachta, sušení masa, brousek, sud na kostky, hromada dřeva + špalek, vůz s kořistí, kůň + koryto, rybaření, mytí | tábor |
| Nav Mesh Bounds Volume přes celou mapu | (P = zelená plocha) |

Bandité (barvy Manny): **Kápo** červený a **Kuchař** zelený u ohně, **Strážný** žlutý na posedu
(RotatingMovement 11,25°/s = 90° za 8 s), **Pochůzkář** modrý – 6 Target Pointů, okruh ≈ 90 s,
**Nováček** fialový – 3 body (potok, oheň, dřevo), okruh ≈ 60 s. Všichni mají PawnSensing 1500 UU / 60°.

Trasy v levelu (jen editor, ve hře skryté): červená = varianta A, modrá = varianta B,
světlejší = alternativy, žlutá = okruh pochůzkáře, fialová = okruh nováčka.

## Hlídky (Behavior Tree)

Grafy jsou hotové v editoru (Python v UE 5.5 je upravovat neumí, proto nejsou ve skriptech):

1. **BTTask_NextPatrolPoint**: `Event Receive Execute AI` → `Cast To BP_Bandit` → `Get PatrolPoints[PatrolIndex]`
   → `Set Blackboard Value as Object` (`PatrolTargetKey`) → `PatrolIndex = (PatrolIndex + 1) % Length`
   → `Finish Execute` (Success).
2. **BT_BanditPatrol** (Blackboard `BB_Bandit`, klíč `PatrolTarget` typu Actor):
   Root → Sequence → `BTTask_NextPatrolPoint` → **Move To** `PatrolTarget` (radius 50) → **Wait** 5 s.
3. **AIC_BanditPatrol**: `BeginPlay` → `Run Behavior Tree` (`BT_BanditPatrol`).

Ověřeno v Simulate: pochůzkář jde skála → houští → JZ → …, nováček potok → oheň → dřevo, strážný se otáčí.
