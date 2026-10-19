---
name: definition-abstraction
description: "Use when designing, naming, or reviewing an abstraction — the interface/implementation split, object vs action vs question, deep vs shallow, the name/scope gradient, and when an abstraction is wrong. Works with any project, any language. Provides language-agnostic definitions and pseudocode."
---

# Abstraction — Definitions

This skill is **definitions + pseudocode only**. No language-specific code, no toolchain.
The concrete names and file layout live in `lele-syntax-rs` (`references/RATIONALE.md` §13,
`references/SMELLS.md` S5–S7); this skill defines the concept only.

## 1. At a glance

| Term | Meaning |
|------|---------|
| **Abstraction** | A simplified way of thinking about something that omits unimportant details. |
| **Interface** | What matters to the *caller*: the name, arguments, return value and effects. |
| **Implementation** | What does not matter to the caller: fields, locals, private helpers. |
| **Deep** | Interface much simpler than the implementation — worth existing. |
| **Shallow** | Interface not much simpler than the implementation — a layer, not an abstraction. |
| **Pass-through** | A method that only forwards its arguments to another method with a similar signature. |
| **False abstraction** | A name that hides a decision the caller actually depends on. |
| **Object abstraction** | A *noun*: the thing, its state, its invariants. |
| **Action abstraction** | A *verb*: the transformation. |
| **Question** | The exception: a `bool` is neither noun nor verb — always a yes/no question. |

## 2. What an abstraction is

An abstraction is **not** a synonym for its parts, and **not** a restatement of its body.
Dijkstra: *"the purpose of abstracting is not to be vague, but to create a new semantic
level in which one can be absolutely precise."* Parnas: a module hides **one design
decision** — the one that may change. Ousterhout: the interface is what matters to the users
of the module; the rest is hidden where it is less obvious.

Two consequences:

1. The name must be a **new concept at a new level**, or there is no abstraction.
2. What the interface hides must be a decision the caller genuinely does not need.

## 3. The three kinds

```
struct ClickCounter   # object abstraction: a thing, named for what it IS
fn    increment()     # action abstraction: a change, named for what it DOES
bool  is_ready        # question: the exception, named as the question it ANSWERS
```

## 4. The name/scope gradient

Names get shorter as scope widens, and longer as scope narrows — with no upper bound:

```
wide scope  : parse_config, handshake, render_frame       # 1-2 words: a domain concept the caller knows
narrow scope: is_least_relevant_multiple_of_larger_prime  # as many words as the detail needs
```

A wide-scope name written at the mechanism's level leaks the implementation; a narrow-scope
name written at the concept's level is vague. Long names are correct when the detail is that
specific — two, three, four words or more. **There is no word cap**; truncating a name is
worse than lengthening it, and the only error is climbing a level that is not its own.
"Wide" means *widely known concept*, not *public visibility*: internal machinery is narrow
scope even when exported, and gets the long, descriptive name.

## 5. The depth test (the guardrail)

Does the interface hide something worth hiding? If the body is one call to another item with
a similar signature, the caller still has to read it — that is a **shallow module /
pass-through**, not an abstraction. Extraction is meaningful only when the implementation
**is more deeply detailed than the interface**.

```
# BAD - name and body are the same level
function read_config(path) -> Config:
    return parse_file(path)

# GOOD - the body is the detail below the name
function read_config(path) -> Config:
    text = read_to_string(path)
    config = Config.default()
    for line in text.lines():
        if not line.starts_with("#"):
            config.set(parse_entry(line))
    return config
```

The test judges *designed* seams, not mandated shape. A one-line forwarder that exists
because the structure demands it — a delegate shell, a trait impl, a thin adapter — is not a
shallow abstraction. Judge the concept, not the line count.

## 6. How to create one (do not abstract ahead of the code)

Write the concrete thing first; when the **same semantic thing** appears a second time,
extract it ("semantic compression") — the duplicated text shows exactly where the seam is.
Abstracting before the second occurrence guesses the seam. Keep **one level of abstraction
per body**: the body reads as a list of calls one level below the name (the step-down rule).

## 7. When an abstraction is wrong

Signals: the abstraction keeps gaining parameters, conditionals, or "just this once"
exceptions. The fix is **backwards, not forwards** — inline it into every caller, delete
what each caller does not need, then re-isolate the duplication that survives. A wrong
abstraction is more expensive than the duplication it removed.

Abstractions also **leak**: an interface can never fully hide the thing underneath. Keep the
boundary honest (see `definition-function-taxonomy`) and keep the leak at the top.

## 8. Checklist (reviews)

1. Is the name a concept/noun/verb/question — not a restatement of the body?
2. Is the interface much simpler than the implementation (deep), or the same level (shallow)?
3. Is the name at the caller's level (short, wide scope) rather than the mechanism's?
4. Is only **one** level of abstraction present in the body?
5. Does the interface hide a decision the caller never needs (not one they do)?
6. If it keeps growing parameters/conditionals, is it a wrong abstraction to inline?

This is a **separate axis from honesty**: honesty is about whether the real inputs and
outputs are in the signature (`definition-function-taxonomy`); abstraction is about how much
implementation sits behind the interface. An honest function can still be a shallow
pass-through; a deep module can still read the clock.

Refs: Ousterhout, *A Philosophy of Software Design*; the Ousterhout–Martin discussion
(*Method Length*); Martin, *Clean Code* ch. 3 and ch. 6; Liskov & Guttag, *Abstraction and
Specification in Program Development*; Dijkstra, *The Humble Programmer* (EWD340); Parnas,
*On the Criteria To Be Used in Decomposing Systems into Modules*; Metz, *The Wrong
Abstraction*; Muratori, *Semantic Compression*; Spolsky, *The Law of Leaky Abstractions*.
See `references/RESOURCES.md` for the annotated, verified link list.
