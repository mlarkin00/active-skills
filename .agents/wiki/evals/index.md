# Pitfall

* [run_eval.py scores every positive as a miss for a skill that is also installed](run-eval-scores-an-installed-skill-as-a-miss.md) - The probe injects a uniquely-named command file and counts only calls to that name, but the real installed plugin skill wins the call, so trigger rates read 0.00 for descriptions that are in fact firing correctly.
* [run_loop.py cannot run on this box — it needs the anthropic SDK and an API key](run-loop-needs-an-api-key-this-box-does-not-have.md) - The eval half shells out to the claude CLI and works, but the improve half calls the Anthropic API directly, and neither the SDK nor ANTHROPIC_API_KEY is present, so description optimization has to be iterated by hand.

# Runtime Behaviour

* [Trigger evals at 3 runs per query cannot separate two skill descriptions](three-runs-per-query-cannot-separate-two-descriptions.md) - Two candidate descriptions produced an identical mean positive trigger rate of 0.500 while 4 of 10 individual queries flipped by 0.66 or more, so the per-query pass/fail totals that skill-creator-enhanced reports are noise.
