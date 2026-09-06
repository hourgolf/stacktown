"""Mutation check: prove the ported tests can actually fail.

ENGINEERING_LANE.md: "A test that cannot fail is not a test: make it fail once
on purpose." A suite that passes tells you nothing until you have seen it go red
for a defect you planted.

Each mutation below is applied to a COPY of StacktownEconomyRules.cpp - the
committed source is never touched - and the pre-flight harness is rebuilt and
run against it. A mutation that does NOT turn the harness red is reported as
SURVIVED, which is a hole in the suite, not a pass.

  python3 Tools/preflight/mutate.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
RULES = os.path.join(ROOT, 'Source', 'StacktownAlpha', 'Private', 'StacktownEconomyRules.cpp')
RUN = os.path.join(HERE, 'run.sh')

# (name, what it breaks, find, replace, expected_to_be_caught)
MUTATIONS = [
    ('rent-drops-the-tier-offset', 'rent no longer scales with tier',
     'return R.RentPerTier * (Tier + 1) * Demand;',
     'return R.RentPerTier * Tier * Demand;', True),

    ('price-wrong-width-divisor', 'width priced per 10uu instead of per 100uu',
     'return R.PriceBase + R.PricePer100uu * (Width / 100.0) + R.PricePerTier * Tier;',
     'return R.PriceBase + R.PricePer100uu * (Width / 10.0) + R.PricePerTier * Tier;', True),

    ('climb-goes-flat', 'upgrade cost stops climbing with tier',
     'return Tier + 1;\n}\n\ndouble Premium',
     'return 1;\n}\n\ndouble Premium', True),

    ('premium-grants-a-discount', 'good performance wrongly discounts the upgrade',
     'return 1.0 + (Penalty > 0.0 ? Penalty : 0.0);',
     'return 1.0 + Penalty;', True),

    ('ladder-off-by-one', 'a lot can climb one rung past the top of its ladder',
     'if (Next >= Tiers)', 'if (Next > Tiers)', True),

    ('buy-does-not-transfer', 'a paid-for parcel is never marked owned',
     'P->bOwned = true;\n\tP->Accum = 0.0;', 'P->Accum = 0.0;', True),

    ('tick-pays-unowned-parcels', 'rent accrues on parcels nobody bought',
     'if (!P.bOwned)\n\t\t{\n\t\t\tcontinue;\n\t\t}', 'if (false)\n\t\t{\n\t\t\tcontinue;\n\t\t}', True),

    ('growth-un-retires', 'a tick advances a tier again, the retired behaviour',
     'P.Accum += Earned;',
     'P.Accum += Earned;\n\t\tif (P.Accum > R.GrowthThreshold) { P.Tier += 1; }', True),

    ('ledger-recounts-from-zero', 'replaying a ledger double-counts every trade',
     'TradeCountReward(Processed, NewCount, R.TradeCreditsPerN, R.TradeCreditAmount)',
     'TradeCountReward(0, LedgerPnls.Num(), R.TradeCreditsPerN, R.TradeCreditAmount)', True),

    ('ledger-loses-idempotency', 'the already-processed prefix is re-read',
     'const int32 Processed = State.TradesProcessed;', 'const int32 Processed = 0;', True),

    ('refusal-string-drift', 'a refusal reason stops saying what it used to',
     'return FVerbResult::No(TEXT("not failed"));',
     'return FVerbResult::No(TEXT("not broken"));', True),

    ('blocked-growth-loses-the-asset-name', 'the refusal no longer names the missing mesh',
     'FString::Printf(TEXT("GROWTH BLOCKED: %s not baked"),\n\t\t\t*Catalogue.AssetName(Rid, Next, Width))',
     'FString::Printf(TEXT("GROWTH BLOCKED: a mesh is not baked"))', True),

    ('is-win-counts-breakeven', 'a scratch trade farms a bonus',
     'return Pnl > 0.0;', 'return Pnl >= 0.0;', True),

    # The honest negative. The shim's TMap is std::map, which is ORDERED, so
    # removing the explicit sort changes nothing here. Only a real UE build can
    # catch this one - which is exactly why a green harness is not the proof.
    ('tick-iteration-order-unsorted', 'parcels summed in map order instead of sorted',
     'OutIds.Sort([](const FString& A, const FString& B) { return A < B; });', '', False),
]


def run_harness(rules_path, out_path):
    env = dict(os.environ, STACKTOWN_RULES_CPP=rules_path)
    r = subprocess.run([RUN, out_path], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def main():
    original = open(RULES).read()
    tmp = tempfile.mkdtemp(prefix='stacktown-mutate-')
    try:
        code, out = run_harness(RULES, os.path.join(tmp, 'baseline'))
        if code != 0:
            print('BASELINE IS ALREADY RED - fix that before mutating:\n' + out)
            return 1
        print('baseline: %s' % out.strip().splitlines()[-1])
        print()

        caught = survived = 0
        unexpected = []
        for name, what, find, repl, expect_caught in MUTATIONS:
            if find not in original:
                print('  ??  %-38s PATTERN NOT FOUND (mutation is stale)' % name)
                unexpected.append(name)
                continue
            mutated = os.path.join(tmp, name + '.cpp')
            with open(mutated, 'w') as f:
                f.write(original.replace(find, repl, 1))
            code, out = run_harness(mutated, os.path.join(tmp, name))
            was_caught = (code != 0)
            if was_caught:
                caught += 1
                # which cases noticed
                cases = sorted({l.split(']')[0].split('[')[-1]
                                for l in out.splitlines() if l.strip().startswith('FAIL')})
                print('  ok  %-38s caught by: %s' % (name, ', '.join(cases)))
            else:
                survived += 1
                print('  --  %-38s SURVIVED (%s)' % (name, what))
            if was_caught != expect_caught:
                unexpected.append(name)

        print()
        print('mutations: %d caught, %d survived, %d total' % (caught, survived, len(MUTATIONS)))
        if unexpected:
            print('UNEXPECTED RESULT for: %s' % ', '.join(unexpected))
            return 1
        print('every mutation behaved as declared. The one deliberate SURVIVOR is')
        print('tick-iteration-order-unsorted: the shim maps TMap onto std::map,')
        print('which is ordered, so only a real UE build can catch it.')
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
