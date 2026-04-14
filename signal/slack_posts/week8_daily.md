# Week 8 Slack Update

This section contains the daily updates posted to the team Slack channel during week 8 of the project, covering the period from April 7 to April 13, 2025. These updates include summaries of meetings, progress reports, and community engagement activities.

---

Nuhamin Alemayehu  [8:10 PM]
Gemini-trp@proton.me
************@*******-********

---

Nuhamin Alemayehu  [9:34 PM]

# Second Meeting

The second meeting commenced on 8th April 2025 at 8:00 PM over Google Meet. This meeting was scheduled after the first introduction meeting on 7th April. The task for this meeting was to read the documentations and report back on what we understood about our roles.

## Attendees

- Chalie (Intelligence Officer)
- Liul (Intelligence Officer)
- Eyoel (Driver)
- Dereje (Driver)
- Nuhamin (Signal Corps)

## Core points raised

- Intelligence Officers Chalie and Liul: Explained what they understood about their role. Chalie plans to add two context layer to increase the accuracy. His plan involves adding a memory schema and a correction loop. The intelligence officers have raised a question on whether it would be better if MCP is handled by the drivers or the intelligence officers.
- Drivers Eyoel and Dereje: Explained what they understood about their role. Eyoel has shared that MCP should be handled by the drivers. Dereje has showed us his progress that the dependencies are added and DAB is cloned. He has also mentioned that it is better to add one more context layer (3 in total) for better performance. They have also discussed about the importance of having a clear understanding of the project architecture before starting to work on it.
- Nuhamin (Signal Corps): Explained what she understood about her role. To play the role effectively, she has requested for the signal team to attend not just the team meetings but also the sub-team meetings. She had raised to the team how we will handle the communication, if it is either by personal accounts or the team account. Attendees have unanimously decided to create team account for X.

## Next Steps

- Read the documentation and prepare an input on the final architecture.
- Continue reading documentations and report back on a deeper understanding of our roles.
- Create team account for X

## House keeping

- Next meeting scheduled for 9th April 2025 right after daily standup (tentatively).
- Share updates and progress in the channel and reply to messages in a timely manner
- Use @channel or @here to notify the team when chatting on slack.

---

Rafia  [12:09 PM]
Join the standup guys, we speaking up in a team. No one is in yet? (edited)

---

Rafia  [2:20 PM]
@Dereje Derib push your local changes, and let me n @Nuhamin Alemayehu prepare our post accordingly. (edited)

---

Nuhamin Alemayehu  [2:48 PM]
@channel @GeminiTrp1 is our twitter account pls follow. (edited)

---

Rafia  [3:04 PM]
https://x.com/GeminiTrp1

this is the linkX (formerly Twitter)Gemini TRP1 (@GeminiTrp1) / X

---

Rafia  [3:14 PM]
btw would you mind sharing your linkedin accounts so that we can mention yall in our posts when necessary

---

Rafia  [9:32 PM]
I'm planning on posting this on discord

Hey — sharing a project kickoff.
Oracle Forge — we're building a context-layered, self-correcting data agent targeting UC Berkeley's DataAgentBench. Our team is called Gemini; the benchmark leader is Gemini 3 Pro at 38%. Made it the goal to beat it.
Day 4 status: architecture sketched, Inception doc approved by the team, repo is live but no running code yet. The structure is there — agent/, kb/, eval/, mcp/, probes/ directories — but we're just entering construction.
The architectural core: three context layers (schema knowledge, institutional knowledge, live corrections log) loaded before every session, and failure-class-aware self-correction rather than generic retry across 4 database types.
Honest uncertainty: I don't know if the corrections log injection will help or hurt at scale. Will find out in about 10 days.
Repo: github.com/Deregit2025/data-agent-forge — if you're curious about the directory structure or want to follow along.

what's ur thought guys?

---

Rafia  [7:08 AM]
Well I posted it in hugging face's discord, the first milesone is done!! Our next move is to blog at least in 2 diff platforms. Ik you guys are on holiday so we'll discuss it after. Bu I'll be needing ur approval for some things. (edited)

---

Nuhamin Alemayehu  [7:59 AM]

# Fourth Meeting

- **Date**: 9th April 8:00 PM
- **Attendees**: Full House
- **Core Points Discussed**: Final decision on system architecture.
- **Next Milestone**: First RUN of the system by 8 PM today.
- **Next Meeting**: 10th April 2025 at 8:00 PM in google meet and midday slack chat.

---

Nuhamin Alemayehu  11:38 AM
@channel Our first thread is up.
https://x.com/i/status/2042522406699360407 (edited) X (formerly Twitter)Gemini TRP1 (@GeminiTrp1) on XIntroducing #TheOracleForge: Our two-week mission to bridge the gap between "clean demos" and production-grade data agents. We are engineering a systemic architecture inspired by the #ClaudeCodeLeak. (1/7) :thread::thread:

---

Nuhamin Alemayehu  [1:27 PM]
@here we have got our first comment from a totally mysterious acct (:wink:). Please comment on the draft before we publish.

Edit: It is posted. But comments are still welcome. (edited)

---

Rafia  [10:01 AM]
https://medium.com/p/26f844bc9bf1?postPublishedType=initial
MediumWe’re Trying to Beat Gemini 3 Pro on a Public Benchmark.Team Gemini — Oracle Forge, Day 4 of 14Reading time5 min readYesterday at 8:36 AMhttps://medium.com/p/26f844bc9bf1?postPublishedType=initial[10:01 AM]https://app.readytensor.ai/publications/were-trying-to-beat-gemini-3-pro-on-a-public-benchmark-w29HwYbedo5Y
app.readytensor.aiWe’re Trying to Beat Gemini 3 Pro on a Public Benchmark.Here's the Architecture We're Betting On — Before We Know If It Works.

Team Gemini — Oracle Forge, Day 4 of 14

Our team is called Gemini. The best current score on the UC Berkeley DataAgentBench is...Yesterday at 9:14 AM[10:02 AM]Our first blogs are out! Combined with our tweets on X, We will now log our posts n feedback n push it to github.

---

Rafia  [10:39 AM]
@channel can we all attend the stand up meeting 2day or do some of us need to be excused?

---

Rafia  [11:00 AM]
Good morning! Hope everyone had a great Easter :blush:
Week 8–9 update from our side:
We’ve set up the shared environment on the TRP-Gemini server and are all working in the same folder. Repo structure is in place, and we’re actively pushing changes to GitHub.
Team is collaborating closely and progressing well.
Let us know if there’s anything specific you’d like us to prioritize or if you have any suggestions!
We might need help on finding the DAB community on discord (edited)

---

Nuhamin Alemayehu  [7:19 PM]
@channel confirming our meeting at the usual 8 pm?

---

Nuhamin Alemayehu  [11:31 PM]
We have written a couple of threads on our progress, please engage with it. It is also a refresher on everyone's status.

https://x.com/GeminiTrp1/status/2043026176432545821?s=20
https://x.com/GeminiTrp1/status/2043655547207999759?s=20X (formerly Twitter)Gemini TRP1 (@GeminiTrp1) on XWe are diving deep into the #ClaudeCode source leak and #OpenAI's internal data agent papers. While the world is talking about the 512k lines of code, our team is obsessed with the three-layer context architecture required to make these systems reliable in production. :yarn: (1/6)X (formerly Twitter)Gemini TRP1 (@GeminiTrp1) on XOur drivers and intelligence officers (IOs) are racing us to the finish line. Because of our drivers, our subagent can now get a structured query from conductors and generate correct query syntax for each db types. (1/n)

---

Nuhamin Alemayehu  [11:43 PM]

# Week 8 conclusion and week 9 commencement meeting 

- *Date*: 13th April 2025 at 8:00 PM
- *Core Points Discussed*: Wrap-up of week 8 activities and planning for week 9.
                        - We are ready for the interim submission.
                        - Our system is now running and we are able to get results.
                        - We have identified the area of domain knowledge as a key area for improvement to improve the performance of our system.
                        - Tomorrow at 8 PM, we will have a meeting to see at a demo and discuss the results in more detail.
                        - We will also discuss the strategy to divide the runs among the 6 of us.
- *Next Milestone*: Improvement of the system based on the interim feedback.
- *Next Meeting*: 14th April 2025 at 8:00 PM in google meet.