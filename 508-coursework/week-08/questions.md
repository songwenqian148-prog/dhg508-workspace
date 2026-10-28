# Questions

Unresolved, and honest about it. Ordered by how much they would change the build.

1. **Is a reachable counterfactual ending acceptable in the brief's terms?**
   The simulation lets the player, by waiting for the man who never came and
   having trained the sword hand, kill the king. It is labelled 史外 and the
   historical ending is the default. But the brief asks for a historical lesson,
   and a winning branch could be read as teaching that the attempt *could* have
   worked. Should the win branch exist at all, or should every branch end in the
   record?

2. **When two chapters disagree, what does the course want?**
   S2 has 体解 and a different date for Dan's head; S1 and S3 agree with each
   other. I followed S1/S3 and declared the choice. The alternative — putting the
   disagreement itself into the game as a scene — is more honest historiography
   but would break the fiction at its climax.

3. **Whose mouth may the model speak with?**
   The two agentic characters get a profile, a fixed perception and a closed
   action list, and the world rejects anything else. Is that enough constraint for
   class, or should the agentic characters be limited to *rephrasing* lines that
   are already in the Shiji?

4. **How much invented dialogue is too much?**
   22 of 141 lines are marked `inv`, and 54 are narration. They are the player's
   own voice and the connective tissue between quoted passages. Is that ratio
   defensible for a "historical simulation", or does the brief expect the player's
   voice to be silent (choices only, no first-person lines)?

5. **Pixel scale vs material evidence.**
   16×24 was chosen so the whole game fits in 480×270 and stays readable on a
   projector. It cannot show period costume or architecture, which is why the art
   is declared invented. Should this instead be 32×32, or a mix of pixel sprites
   and the AI illustrations, at the cost of a consistent look?

6. **Concurrency and cost in class.**
   A single playthrough costs about ¥0.01. Twenty people playing at once, each
   triggering four or five counterfactual panels, is still trivial — but the
   DeepSeek account is one key on one laptop, and the server is single-process
   with a 90 s timeout. Is a shared classroom endpoint expected, or does each
   student run their own?

7. **Language.**
   The course documents are in English; the simulation is in Chinese (浅近文言
   dialogue, 白话 narration) because the source is. Should the presenter's index
   (this README, `research/`) stay English, or is a bilingual version expected?

8. **Is moe anime acceptable for a history course, and if so where is the line?**
   This version dropped the reconstruction claim entirely: kawaii-moe portraits, cute
   pastel backgrounds, no pixel art left. The sourcing table still marks all of it as
   invented. Is an openly moe reading of the Shiji acceptable, or does the visual side
   need to stay documentary even when the text does not?

9. **A version that runs with no server.**
   The game falls back to scripted text when the API is unreachable, but it still
   needs `python code/server.py` to serve the files (ES modules will not load from
   `file://`). Should there be a single-file, no-backend build for handing in a
   link?

10. **How far should free speech be allowed to go?**
    Every typed line is a model call, and the player can say anything to anyone. The
    world refuses to act on an unrecognised intent, but the *character* always answers
    — including in ways that might contradict a later scene. Is it better to bound the
    input (suggested phrases, a keyword filter), or to keep it open and accept that a
    curious player will sometimes hear a guard say something a guard should not know?

11. **Should the model be allowed to write the historical figures' *arguments*?**
    Right now the quotations are fixed and the model only speaks where the record is
    silent. Letting it argue — 太子丹 defending the plan, 秦王 justifying the war — would
    make the simulation richer and the sourcing table weaker. Where is the line?
