# Example Resolution Path

Question: "Where should I add rate limiting to the API?"

Use `CodeLOD` like this:

1. Read `.context/L0.md` to find the API-related directories.
2. Read the matching lines in `.context/L1.md` to identify the router, middleware, and server bootstrap files.
3. Open the relevant `.context/L2/...json` files to inspect handler and middleware signatures.
4. Read only the final implementation files needed to confirm control flow and make the edit.

This keeps the rest of the repository at low detail while still allowing exact code changes in the narrow slice that matters.