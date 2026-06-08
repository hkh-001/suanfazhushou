# Product Brief

## Product Name

AlgoMentor AI

## Product Positioning

AlgoMentor AI is an AI-powered algorithm learning platform for students. It is not only a chatbot. It organizes algorithm knowledge, AI tutoring, code diagnosis, learning records, and progress feedback into a closed learning loop.

The product goal is to help learners move from fragmented problem solving to structured algorithm learning.

## Target Users

Primary users:

- algorithm competition beginners
- undergraduate students learning data structures and algorithms
- programming learners moving from syntax basics to algorithm practice
- students preparing for Blue Bridge Cup, ICPC basics, Luogu basics, or course exams

## User Pain Points

Typical pain points:

- unclear algorithm learning order
- difficulty understanding editorials
- uncertainty about when to use an algorithm
- inability to debug WA, TLE, or RE
- weak transfer from learned concepts to problems
- lack of review after mistakes
- AI tools often give final answers too directly

## Core Learning Loop

```text
diagnose level
-> generate learning path
-> learn topic
-> read template code
-> solve recommended problem
-> paste code for diagnosis
-> record mistakes and weak points
-> update dashboard
-> recommend next step
```

The MVP focuses on a simplified loop:

```text
topic -> AI explanation -> code diagnosis -> learning record -> dashboard
```

## Differentiation

Compared with directly asking a general chatbot, AlgoMentor AI should provide:

- structured knowledge map
- learning state memory
- topic-aware AI tutoring
- code diagnosis connected with learning records
- mistake review and weak-point tracking
- dashboard feedback
- future recommendation based on learning history

## Product Principles

- Build as a maintainable product, not a pure demo.
- Implement in small phases.
- Prioritize the main learning loop.
- Keep AI educational and heuristic by default.
- Avoid exposing secrets to frontend.
- Avoid copying third-party copyrighted problem content.
