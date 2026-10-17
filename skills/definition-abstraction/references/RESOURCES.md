# Abstraction — annotated resources

What each source teaches and which section of `SKILL.md` it backs. Every link was fetched
and verified live when this file was written. Sources whose publisher page blocks agents
(MIT Press, O'Reilly, ACM Digital Library PDFs) are listed as **book only** rather than given
a link that would rot.

## Primary — how to create and judge an abstraction

| Source | Link | Teaches | Section |
|---|---|---|---|
| Ousterhout & Martin, *A Philosophy of Software Design vs Clean Code* | https://github.com/johnousterhout/aposd-vs-clean-code | Both halves of the rule, from the authors themselves: Martin's **scope↔name-length gradient** ("the larger the scope of a method, the shorter its name") and his own **depth guardrail** ("the implementation is not more deeply detailed than the interface"), set against Ousterhout's **deep vs shallow** critique | 4, 5, 7 |
| Ousterhout, *A Philosophy of Software Design* (2nd ed.) | https://web.stanford.edu/~ouster/cgi-bin/book.php | Deep vs shallow modules; pass-through method; false abstraction; "different layer, different abstraction"; "abstractions, not features" | 5, 6, 7 |
| Martin, *Clean Code* — ch. 3 *Functions* | book only | One level of abstraction per function; the step-down rule; descriptive names | 4, 6 |
| Martin, *Clean Code* — ch. 6 *Objects and Data Structures* | book only | Data abstraction; data/object anti-symmetry → the object-abstraction half | 3 |
| Martin, *Clean Code* talk 3, distilled | https://herbertograca.com/2016/09/03/clean-code-3-functions-by-robert-c-martin-uncle-bob | The one-line form of §3: classes take **nouns**, functions take **verbs** | 3 |
| Dijkstra, *The Humble Programmer* (EWD340, 1972) | https://www.cs.utexas.edu/~EWD/transcriptions/EWD03xx/EWD340.html | "The purpose of abstracting is not to be vague, but to create a new semantic level in which one can be absolutely precise" — the test that kills a synonym-name | 2 |
| Parnas, *On the Criteria To Be Used in Decomposing Systems into Modules* (1972) | https://cacm.acm.org/research/on-the-criteria-to-be-used-in-decomposing-systems-into-modules | A module hides **one design decision** — the one that may change; that decides *which* detail the interface hides | 2, 5 |
| Liskov & Guttag, *Abstraction and Specification in Program Development* (1986) | book only | Data abstraction and the **abstraction function**: what the representation means | 2, 3 |
| Booch, *Object-Oriented Analysis and Design with Applications* | book only | "An object is an abstract software model of a problem-domain entity" → object vs action | 3 |

## Creating one, and undoing a wrong one

| Source | Link | Teaches | Section |
|---|---|---|---|
| Muratori, *Semantic Compression* | https://caseymuratori.com/blog_0015 | Write the concrete thing first; compress when the same semantic thing appears twice | 6 |
| Muratori, *Complexity and Granularity* | https://caseymuratori.com/blog_0016 | The follow-up: granularity and layering; never leave a hole in an API | 5, 6 |
| Metz, *The Wrong Abstraction* | https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction | Detect a wrong abstraction (parameters and conditionals accumulating); undo it by inlining, then re-compressing | 7 |
| Spolsky, *The Law of Leaky Abstractions* | https://www.joelonsoftware.com/2002/11/11/the-law-of-leaky-abstractions/ | Every non-trivial abstraction leaks; keep the boundary honest and the leak at the top | 7 |
| Smith, *How to write the perfect function* | talk (transcript kept at the repo root) | "Write the functions you want to see in the world" — name from the call site's level | 4 |

## Community skills worth mining (do not vendor)

| Skill | Link | Note |
|---|---|---|
| `aiocean/claude-plugins` deep vs shallow modules | https://github.com/aiocean/claude-plugins/blob/main/plugins/aio-advisor/volume-01-foundations/07-deep-vs-shallow-modules.md | Long worked treatment; names the "conflating smallness with depth" mistake |
| `Island-Dev-Crew/uncle-bob-skills` | https://github.com/Island-Dev-Crew/uncle-bob-skills/blob/main/research/ousterhout-debate.md | Provenance of the Ousterhout–Martin debate, with citations |
