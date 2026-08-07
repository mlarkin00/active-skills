# Convention

* [Removing a skill leaves two kinds of reference, and only one of them may be edited](removing-a-skill-leaves-two-kinds-of-reference.md) - A pointer that tells a future agent to go somewhere must be repaired; a citation recording what was observed must not, because rewriting it falsifies the measurement. Re-pin the prose that frames the citation instead.

# Pitfall

* [Deep-research source docs name internal services in prose that no path scan catches](research-docs-carry-internal-codenames-a-path-scan-misses.md) - A 4,774-line research compendium dropped into this public repo named six unreleased internal services as if they were shipping products, and the repo's `google3`/`go/`/`blaze` path scan matches none of them; the doc's own text conceded the names were not publicly documented.
* [Editing a skill in this repo does not change what its slash command runs](editing-a-skill-does-not-change-what-its-command-runs.md) - The runtime loads skills from a versioned plugin cache, never from this authoring repo, so invoking a skill you just edited silently executes the pre-edit text — confirmed by running /close-session against an edited close-session and getting the old workflow back.
