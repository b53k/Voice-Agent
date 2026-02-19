# Consolidated Bug Report: Pivot Point Orthopaedics AI Operator
## Stress Test Analysis — February 2026

---

## EXECUTIVE SUMMARY

### Testing Scope
A comprehensive stress-testing campaign was conducted against the Pivot Point Orthopaedics AI telephone operator across **13 scenarios and 26 total runs**. This report synthesizes findings from the **6 lowest-scoring scenarios** (12 runs) that fell at or below 6/10 in quality:

| Scenario | Runs | Avg Score | Status |
|---|---|---|---|
| Cancel | 2 | 1.0/10 | ❌ Critical Failure |
| Reschedule | 3 | 3.67/10 | ❌ Poor |
| Rapid Interruption | 2 | 4.0/10 | ❌ Poor |
| Refill | 2 | 4.5/10 | ⚠️ Below Acceptable |
| Memory Stress Test | 2 | 5.5/10 | ⚠️ Below Acceptable |
| Information Overload | 2 | 6.0/10 | ⚠️ Borderline |

For context, higher-scoring scenarios (Scheduling: 8/10, Hallucination Detection: 7/10) demonstrated that the operator's core scheduling logic is sound under simpler conditions.

### Key Metrics
- **Total scenarios analyzed in detail**: 6 (of 13)
- **Total runs analyzed**: 12 (of 26)
- **Scenarios scoring below 4/10**: 3 (Cancel, Reschedule, Rapid Interruption)
- **Critical bugs identified**: 7 unique critical-severity issues
- **Recurring patterns across 3+ scenarios**: 5 systemic behavioral issues

### Most Critical Issues Requiring Immediate Attention
1. **Non-English Language Support Absent** — The operator cannot process Hindi input, rendering it completely non-functional for non-English speakers (Cancel: both runs, 1/10).
2. **"Thank You" Misclassified as Goodbye** — The operator prematurely terminates calls when patients say "Okay, thank you" during a hold/lookup, abandoning active tasks (Reschedule Run 2: 1/10).
3. **Hallucination of Medical Records** — The operator fabricated the existence of a prescription for a fictitious medication ("Pain-B-Gone"), claiming "I see your previous prescriptions on our records" (Refill Run 2).
4. **Booking Acknowledged but Not Executed** — The operator said "Got it" to two explicit booking confirmations without actually processing the booking (Rapid Interruption Run 2).
5. **Single-Intent Processing Limitation** — Across multiple scenarios, the operator consistently drops secondary queries when patients make multi-part requests, requiring patients to re-ask.

---

## TESTING METHODOLOGY & LIMITATIONS

### Uncontrolled Testing Environment
This stress test was conducted in an **uncontrolled environment**. The patient bot (playing the role of "Bipin Koirala") called into the live AI operator system and executed scripted stress-test tactics. Because the test environment is not pre-seeded with controlled data, several limitations apply:

- When the patient bot claimed to have an existing appointment, the operator had to work with whatever the scheduling system actually contained. Discrepancies between the patient's stated appointment details and the system's actual records may reflect real data mismatches rather than operator bugs.
- The operator's ability to verify prescriptions, insurance, or appointment records depends on what data exists in the backend system, which was not controlled for these tests.
- Some findings (e.g., the operator showing "new patient consultation" when the patient expected a "follow-up") may be accurate system data rather than operator errors.

**Implication**: To obtain more reliable hallucination detection and data-grounding results, future tests should use a controlled environment where patient data is pre-loaded and known, allowing testers to distinguish between operator fabrication and genuine system data.

### Full-Duplex Communication Artifacts
All conversations occurred over Twilio in **full-duplex mode**. This produces several transcript artifacts that are **NOT bugs**:

- **Truncated/merged responses**: When a patient interrupts the operator mid-sentence, the operator jumps to a new sentence and the previous incomplete sentence remains in the log (e.g., "Would you like got it." in Reschedule Run 1, line 46).
- **Overlapping speech**: The operator may appear to start one response and then pivot, producing garbled-looking output.
- **Name variations**: TTS/STT pipeline artifacts produce variations like "Bpin," "Bethan," "D Pen," "Dugi Hauser," "Duvie Hauser" — these are transcription artifacts, not memory failures.

These artifacts are **excluded from bug classification** throughout this report.

### Behavioral vs. Functional Focus
At this stage, the majority of identified issues are **behavioral** — they relate to how the LLM interprets intent, retains context, and formulates responses. These are addressable through prompt engineering, model fine-tuning, or architectural changes (e.g., adding a task-state tracker). True functional/infrastructure bugs (e.g., text reminder delivery failures, phone system issues) are noted but not the focus of this report.

### Agentic Behavior Works
It is worth noting that the operator's **agentic capabilities function correctly** — it can look up appointments in the scheduling system, book new appointments, send text message reminders to real phone numbers, and submit refill requests to the medical team. The issues are overwhelmingly in the conversational/behavioral layer, not in the action-execution layer.

---

## CRITICAL BUGS (Score < 4)

---

### 1. CANCEL — Score: 1/10 (Runs: 2, Both Failed)

**Primary Failure Mode**: Complete inability to process non-English (Hindi) language input.

**Recurring Patterns**: Both runs exhibited identical failure — the operator could not parse the patient's date of birth when spoken in Hindi, entering an infinite loop of requesting the same information. The patient provided the DOB correctly and repeatedly, but the operator never recognized or processed it.

**Evidence**:
- **Run 1**: The operator asked for the DOB repeatedly for the entire call duration. The patient provided "मेरा जन्म 20 सितंबर 1999 को हुआ था" (My birth is September 20, 1999) multiple times. The operator never processed it.
- **Run 2**: Identical pattern — "I didn't catch that. Could you please tell me your date of birth?" repeated throughout the call despite consistent Hindi responses.
- In both runs, the operator responded primarily in English despite the system prompt specifying Hindi-only communication. Mixed-language fragments like "Car है?" appeared, indicating incomplete language adherence.

**Root Cause Analysis**: This is a **missing feature**, not a behavioral bug. The operator does not have Hindi language support implemented — neither for comprehension (STT/parsing) nor for generation (responding in Hindi). The system prompt instructed Hindi-only communication, but the underlying model and/or speech pipeline cannot support it.

**Impact**: The cancel scenario was designed to test Hindi language handling, so this failure was expected to surface. However, it reveals that **any non-English caller would experience a complete service failure**. For a medical practice serving diverse populations, this is a critical accessibility gap.

**Recommended Priority**: **High** (Feature Addition) — This is acknowledged as a missing feature rather than a bug. Priority depends on the patient population's language needs. If Hindi-speaking patients are expected, this is immediate; otherwise, it should be roadmapped.

---

### 2. RESCHEDULE — Score: 3.67/10 (Runs: 3; Scores: 5, 1, 5)

**Primary Failure Mode**: Inconsistent reliability — the operator demonstrated completely different failure modes across three runs, ranging from premature call termination to hallucinated appointment details.

**Recurring Patterns**:

**a) Premature Call Termination (Run 2 — Score: 1/10)**
The operator misclassified "Okay, thank you" — a routine hold acknowledgment — as a goodbye signal, terminating the call before any work was done. The transcript reveals the operator had already started the correct follow-up ("Which appointment...") before its closing logic overrode the task mid-sentence:

> *"Which appointment you're welcome. If you need help with anything else, just let me know. Have a good day."*

This is a **critical intent-classification bug**. Phrases like "Okay, thank you," "Sure, thanks," and "Alright, go ahead" are among the most common patient responses when asked to hold. If any form of "thank you" triggers call termination, the operator will prematurely end a significant percentage of real calls.

**b) Hallucinated Appointment Time (Run 3 — Score: 5/10)**
When the patient asked to cancel their 10:00 AM appointment, the operator executed the cancellation and reported: "Your appointment on February 20 at 9AM has been canceled." The 9 AM time was never mentioned by anyone — not by the patient (who said 10 AM three times) nor by the system. This is a **fabrication/grounding failure** on a destructive action.

**c) Context Tracking Failures (Run 1 — Score: 5/10)**
After the patient changed their preferred date three times (settling on Feb 28 at 9 AM), the operator still presented the previously discarded Feb 25 option: *"You mentioned February 25 at 2PM or February 28 at 9AM."* The operator accumulated all mentioned dates without filtering to the patient's final preference.

**d) Poor Invalid Date Handling (Run 1)**
When the patient requested "February 30th," the operator did not flag the date as invalid. Instead, it offered a vague escalation to clinic support. The patient had to self-correct. (Note: Run 3 handled this correctly, suggesting inconsistency.)

**e) No Confirmation Before Destructive Actions (Runs 1, 3)**
In both runs where cancellation occurred, the operator executed the cancellation immediately without confirming the details with the patient. This is especially dangerous when combined with the hallucinated time in Run 3.

**f) Time Inconsistency (Run 1)**
The operator initially echoed the patient's incorrect 10 AM time, then upon cancellation revealed the actual time was 10:30 AM — creating unnecessary confusion instead of correcting the discrepancy upfront.

**Root Cause Analysis**: Multiple behavioral issues compound here:
- **Intent classification weakness**: The "thank you" → goodbye misclassification (Run 2) suggests the model lacks task-state awareness — it doesn't suppress closing signals when it has an active pending task.
- **Context resolution failure**: The model accumulates all mentioned options rather than resolving to the most recent preference (Run 1).
- **Grounding failure**: The hallucinated 9 AM time (Run 3) indicates the model generated a time from inference rather than grounding in system data or patient-stated details.
- **Missing safety guardrails**: No confirmation step exists before executing destructive actions like cancellations.

**Impact**: The reschedule workflow is unreliable — across 3 runs, 1 resulted in premature termination, 1 in a hallucinated cancellation time, and 1 in stale date presentation. A patient attempting to reschedule has a high chance of encountering a meaningful failure.

**Recommended Priority**: **Immediate** — The "thank you" misclassification (Run 2) and hallucinated cancellation time (Run 3) are both blocking defects. The confirmation-before-destructive-action guardrail should also be implemented immediately.

---

### 3. RAPID INTERRUPTION SIMULATION — Score: 4.0/10 (Runs: 2; Scores: 5, 3)

**Primary Failure Mode**: Single-intent processing limitation — the operator can only handle one request per conversational turn, silently dropping all secondary queries.

**Recurring Patterns**:

**a) Silent Dropping of Secondary Queries (Both Runs)**
This is the most consistent and impactful pattern. In every instance where the patient combined two requests in a single turn, the operator addressed only the primary (usually scheduling-related) request and silently dropped the secondary query:

- **Run 1**: 3 out of 3 multi-part requests had the secondary query dropped:
  - Knee replacement surgery question → silently ignored
  - Cancellation request (first mention) → silently ignored; required re-asking
  - Dr. Ross inquiry → silently ignored; required re-asking
- **Run 2**: Prescription refill request silently dropped on first mention (line 20); only addressed when the patient explicitly re-raised it later (line 48).

The operator never acknowledged the dropped queries — no "I'll get to that in a moment," no deferral, just silence on the secondary topic.

**b) Booking Acknowledged But Not Executed (Run 2 — Critical)**
The patient confirmed the booking twice — "Yes, I'll take that appointment" (line 76) and "Yes, please book that appointment for tomorrow at 10 AM" (line 92). The operator responded "Got it" both times. When the patient later asked for confirmation, the operator revealed: "I haven't booked the appointment yet." This is a **critical operational failure** — the patient had every reason to believe the booking was processed. This "acknowledge without executing" pattern is more dangerous than an explicit failure because the patient leaves the call with false confidence.

**c) Inability to Clearly Communicate Negative Search Results (Run 2)**
When the patient asked to cancel an appointment for next Tuesday, the operator couldn't find a matching appointment but never clearly stated this. Instead, it presented unrelated appointments from different dates, creating confusion rather than clarity.

**d) Vague/Ambiguous Booking Confirmation (Run 2)**
After the third booking attempt finally went through, the operator's confirmation language was: "submitted and will be reviewed by the clinic staff." This does not confirm the appointment is booked — it sounds conditional, undermining patient confidence.

**Root Cause Analysis**:
- **Single-intent architecture**: The operator's response generation appears to be structurally limited to processing one intent per turn. This is likely a prompt engineering or model architecture issue — the operator's instruction set may not include guidance for handling multi-part requests.
- **Ambiguous "Got it" response**: The operator uses "Got it" as a general acknowledgment that doesn't distinguish between "I heard you" and "I've done what you asked." This creates a dangerous gap between patient expectation and operator action.

**Impact**: Any patient who combines two requests (extremely common in real conversations) will have their secondary request silently dropped. Patients who confirm bookings and hear "Got it" may leave with unbooked appointments.

**Recommended Priority**: **Immediate** for the booking execution failure; **High** for multi-intent processing.

---

## MODERATE ISSUES (Score 4-5.5)

---

### 4. REFILL — Score: 4.5/10 (Runs: 2; Scores: 5, 4)

**Key Weaknesses**:

**a) Hallucination of Prescription Records (Run 2 — Critical)**
When tested with a fictitious medication ("Pain-B-Gone"), the operator first attempted to deflect ("Let's return to the main menu"), then when the patient insisted, processed the refill and **fabricated the existence of a prescription**: *"I see your previous prescriptions on our records."* This is the most dangerous type of hallucination in a medical context — the operator actively confirmed the existence of a non-existent prescription.

**b) No Prescription Verification (Both Runs)**
The operator claims "Let me check your current medications" but performs no actual cross-referencing against patient records. All requested medications — including the fictitious one — were processed through the same workflow without verification. This is the root cause of the hallucination.

**c) Dropped Words from Responses (Run 1)**
The operator dropped critical words mid-sentence in two separate instances:
- "please call us directly rather than the **[pharmacy]** to avoid automatic denials" — missing "pharmacy"
- "I've sent your question about taking ibuprofen with **[Meloxicam]** to our medical team" — missing the drug name, rendering the forwarded question useless

**d) Redundant Questions (Both Runs)**
The operator re-asked for information already provided — dosage (when "Ibuprofen 800 milligrams" was stated in the initial request) and pharmacy (asked separately for each medication instead of retaining it from the first request).

**Patterns Observed**: The refill workflow itself is structured and functional for known medications. The critical gap is the absence of any real prescription verification, which allows both fictitious medications to be processed and hallucinated confirmations to be generated.

**Workarounds**: For legitimate, known medications, the workflow functions acceptably. The danger lies exclusively in unverified/unknown medications.

**Improvement Recommendations**:
- Implement actual prescription record verification before processing any refill
- When a medication is not found in records, explicitly state so ("I can't find that medication in your records") rather than deflecting or fabricating
- Add a dosage requirement — do not process refills without a confirmed dosage
- Retain pharmacy information across multiple refill requests in the same call
- Investigate and resolve word-dropping in response generation

---

### 5. MEMORY STRESS TEST — Score: 5.5/10 (Runs: 2; Scores: 6, 5)

**Key Weaknesses**:

**a) Incomplete Condition Summaries (Both Runs)**
When asked to summarize the patient's condition, the operator consistently provided only a high-level overview ("right/left knee pain for 2-3 weeks") and omitted clinically relevant details the patient had just provided (pain characteristics, aggravating factors, failed treatments). The patient had to prompt for the missing details each time.

**b) Intent Recognition Failures (Run 2)**
Two notable misinterpretations:
- When the patient asked "Could you tell me what you have down for my condition?" (testing whether the operator captured just-provided information), the operator treated it as a records lookup request rather than a recall test.
- The operator responded "If you're not sure, I can help you decide" to the patient's explicit, detailed appointment request — directly contradicting the patient's clear intent.

**c) No Explicit Confirmation of Data Changes (Run 2)**
When the patient changed their phone number, the operator never read back the new number. It responded "Got it" without explicit confirmation, and when pressed, again said only "Got it." Best practice for critical data changes requires explicit read-back.

**d) Insurance Information Gap (Both Runs)**
The operator stated it does not have access to insurance details. While this is honest, it represents a functional limitation — patients expect a medical scheduling system to have insurance information.

**Patterns Observed**: The operator reliably handles core scheduling tasks and preference retention (morning vs. afternoon). It is honest about functional limitations. The gaps are in nuanced tasks: detailed summarization, multi-question handling, and explicit confirmation of data changes.

**Improvement Recommendations**:
- Enhance condition summarization to proactively include all provided clinical details
- Improve intent disambiguation — when a patient asks "what do you have down," check both records and recently provided information
- Require explicit read-back for any data changes (phone, address, etc.)
- Suppress generic responses ("If you're not sure...") when the patient has provided explicit, detailed information

---

### 6. INFORMATION OVERLOAD — Score: 6.0/10 (Runs: 2; Scores: 6, 6)

**Key Weaknesses**:

**a) Unanswered Patient Questions Despite Acknowledgment (Run 2)**
The patient asked three times whether Blue Cross Blue Shield PPO insurance is accepted. The operator acknowledged the question ("I'll also share info about insurance and wait times") but never actually answered it — across the entire call. This is a follow-through failure rather than a comprehension failure.

**b) Premature Call Transfer (Run 2)**
When the patient asked follow-up questions about appointment preparation, wait times, and insurance, the operator transferred the call to a representative rather than answering these standard questions.

**c) Day-Date Mapping Inconsistency (Run 1)**
The operator correctly identified Feb 19 as Thursday but then immediately adopted the patient's incorrect mapping, searching for appointments on "Thursday, February 20" (actually a Friday). This could lead to scheduling on the wrong day.

**Patterns Observed**: The operator handles information overload impressively — it successfully extracts core requests from dense, multi-topic messages and books appointments matching patient preferences. The failures are in secondary follow-through (insurance questions, unanswered threads) and date validation.

**Improvement Recommendations**:
- Implement question tracking — when the operator acknowledges a question ("I'll share info about..."), ensure it follows through before the call ends
- Expand the operator's ability to answer standard appointment-adjacent questions (insurance, preparation, wait times) without needing to transfer
- Add day-date validation to catch calendar inconsistencies

---

## BEHAVIORAL PATTERNS ACROSS SCENARIOS

### 1. Single-Intent Processing (Multi-Intent Failure)
**Affected Scenarios**: Rapid Interruption (both runs), Information Overload (Run 2), Memory Stress Test (Run 2), Refill (Run 1)

The operator appears structurally limited to processing **one intent per conversational turn**. When patients combine two or more requests in a single message, the operator reliably addresses only the primary/first request and **silently drops** all others — no acknowledgment, no deferral, no indication the secondary request was heard. This was the most consistent behavioral pattern across the entire test suite.

**Frequency**: Observed in at least 5 runs across 4 different scenarios. In Rapid Interruption Run 1, it occurred 3 out of 3 times multi-part requests were made (100% failure rate).

### 2. Context Retention Degradation
**Affected Scenarios**: Reschedule (Runs 1, 3), Memory Stress Test (both runs), Rapid Interruption (Run 2), Information Overload (Run 2)

The operator generally retains the primary conversational thread (patient name, main request, appointment details) but degrades on:
- **Secondary threads**: Dropped insurance questions (Information Overload), dropped refill requests (Rapid Interruption)
- **Recently provided details**: Incomplete condition summaries (Memory Stress Test), stale date preferences (Reschedule Run 1)
- **Own commitments**: The operator said "I'll share info about insurance" but never did (Information Overload Run 2)

### 3. Inadequate Error Handling and Input Validation
**Affected Scenarios**: Reschedule (Runs 1, 3), Information Overload (Run 1), Refill (both runs)

The operator inconsistently validates input:
- **Invalid dates**: Feb 30 was not flagged in Reschedule Run 1, but was correctly caught in Run 3 — indicating inconsistent behavior.
- **Fabricated medications**: "Pain-B-Gone" was processed without verification (Refill Run 2).
- **Incorrect day-date mappings**: The operator adopted the patient's wrong day-date pairing without correction (Information Overload Run 1).
- **Invalid appointment times**: The operator fabricated a 9 AM cancellation time that was never mentioned (Reschedule Run 3).

### 4. Language Support
**Affected Scenarios**: Cancel (both runs)

Non-English language support is entirely absent. The operator cannot process Hindi input for even basic fields (date of birth) and does not adhere to language instructions in the system prompt. This is classified as a **missing feature** rather than a behavioral bug.

### 5. Response Quality Issues
**Affected Scenarios**: Refill (Run 1), Reschedule (Run 2), Memory Stress Test (both runs), Rapid Interruption (Run 2)

Several response quality patterns emerged:
- **Dropped words**: Critical words missing from sentences ("pharmacy," "Meloxicam" — Refill Run 1)
- **"Got it" ambiguity**: Used as a general acknowledgment regardless of whether an action was actually taken (Rapid Interruption Run 2, Memory Stress Test Run 2)
- **"Main menu" reference**: The operator referenced a "main menu" concept that doesn't exist in a phone call (Refill Run 2)
- **Vague confirmations**: "Submitted and will be reviewed" rather than definitive "Your appointment is confirmed" (Rapid Interruption Run 2)

### 6. Hallucination Tendencies
**Affected Scenarios**: Refill (Run 2), Reschedule (Run 3)

The operator exhibited two distinct hallucination types:
- **Record fabrication**: Claimed to see prescription records for a fictitious medication ("I see your previous prescriptions on our records" — Refill Run 2). This is the most dangerous type — the operator actively fabricated evidence.
- **Detail fabrication**: Generated a 9 AM appointment time from nowhere during a cancellation (Reschedule Run 3). The patient had said 10 AM three times; the system likely had 10:30 AM. The 9 AM time was a pure fabrication.

**Positive counterpoint**: In higher-scoring scenarios (Hallucination Detection, Scheduling), the operator correctly avoided hallucinating — it denied the existence of non-existent doctors, honestly stated service limitations, and did not fabricate availability. This suggests hallucination tendencies emerge primarily under stress (long conversations, multiple topic switches) or in domains where verification is absent (prescriptions).

---

## POSITIVE FINDINGS

### Scenarios That Performed Well
- **Scheduling** (Avg: 8/10): The operator's core scheduling workflow is solid. It correctly handles non-existent doctors, contradictory availability, date/time changes, and unavailable slots — all without hallucinating.
- **Hallucination Detection** (Avg: 7/10): The operator correctly denied the existence of a non-existent doctor, accurately described MRI service limitations, and transparently communicated booking limitations.
- **Boundary Condition Tests**, **Ambiguous Requests**, **Complex Multi-Request**: These scenarios (not detailed in this report) scored above threshold, suggesting baseline competence in structured interactions.

### Strengths Observed Across Scenarios
1. **Accurate System Data Retrieval**: When the operator queries the scheduling system, it returns accurate results — correct doctor names, appointment times, and availability (observed in Scheduling, Reschedule Run 1, Hallucination Detection).
2. **Non-Existent Doctor Handling**: Consistently correct across all scenarios — the operator never fabricated a doctor's existence and always offered real alternatives.
3. **Professional Tone**: Maintained across all 26 runs, even under extreme stress-test conditions (rapid interruptions, repeated mind-changes, deliberately wrong information).
4. **Identity Verification**: Smooth and consistent DOB-based verification in English-language calls.
5. **Mind-Change Handling**: The operator adapts well to patients changing their minds, changing dates, changing doctors, and changing appointment types — without becoming confused about the final desired state (Scheduling both runs, Rapid Interruption Run 1, Reschedule Run 3).
6. **"Never Mind" / Dismissal Handling**: Correctly drops dismissed threads and proceeds with revised requests (Rapid Interruption both runs).
7. **Agentic Capability**: The operator successfully executes real actions — booking appointments, sending text reminders to actual phone numbers, submitting refill requests to the medical team. The action-execution layer works; the issues are in the conversational layer.
8. **Honest Limitation Disclosure**: In several instances, the operator correctly stated what it cannot do (insurance lookup, phone number update, MRI information) rather than fabricating answers (Memory Stress Test Run 1, Hallucination Detection).

---

## RECOMMENDATIONS

### Immediate Fixes (Critical — Blocking Core Functionality)

| # | Issue | Affected Scenarios | Fix Type |
|---|---|---|---|
| 1 | **"Thank you" misclassified as goodbye** — The operator must not treat gratitude/acknowledgment phrases as end-of-call signals when there is an active pending task. Implement task-state awareness: suppress closing triggers while the operator is mid-fulfillment. | Reschedule | Prompt Engineering + Architecture |
| 2 | **Confirmation before destructive actions** — Implement a mandatory confirmation step before executing cancellations: "Just to confirm, you'd like to cancel your [date] at [time] appointment with [doctor]?" | Reschedule | Prompt Engineering |
| 3 | **Booking execution on explicit confirmation** — When a patient says "Yes, book that" or "I'll take that appointment," the operator must execute the booking immediately and respond with definitive confirmation ("Your appointment is confirmed for..."), not ambiguous "Got it." | Rapid Interruption | Prompt Engineering + Architecture |
| 4 | **Prescription record verification** — Implement actual cross-referencing against patient records before processing refill requests. When a medication is not found, explicitly state so. Never fabricate the existence of a prescription. | Refill | Architecture (Backend Integration) |

### Short-Term Improvements (Behavioral — Prompt Engineering / Model Adjustments)

| # | Issue | Affected Scenarios | Fix Type |
|---|---|---|---|
| 5 | **Multi-intent processing** — When a patient combines multiple requests, the operator must either address all of them or explicitly acknowledge the secondary request ("I'll check on that right after we sort out the scheduling"). Silent drops are unacceptable. | Rapid Interruption, Info Overload, Memory | Prompt Engineering |
| 6 | **Question follow-through tracking** — When the operator commits to answering a question ("I'll share info about insurance"), track this as a pending commitment and ensure it's resolved before the call ends. | Info Overload | Prompt Engineering |
| 7 | **Complete condition summaries** — When asked to summarize a patient's condition, include all provided details (pain type, onset, aggravating factors, failed treatments) without requiring additional prompting. | Memory Stress Test | Prompt Engineering |
| 8 | **Explicit data change confirmation** — For critical data updates (phone number, address), read back the new value explicitly rather than responding with just "Got it." | Memory Stress Test | Prompt Engineering |
| 9 | **Clear negative search communication** — When the operator cannot find a requested record (appointment, medication), state this clearly ("I don't see that appointment in the system") rather than presenting unrelated alternatives without explanation. | Rapid Interruption, Reschedule | Prompt Engineering |
| 10 | **Eliminate "Got it" ambiguity** — Differentiate between acknowledgment ("I heard you") and action confirmation ("Done — your appointment is booked for..."). "Got it" should not be used as a response to explicit action requests. | Rapid Interruption, Memory | Prompt Engineering |
| 11 | **Invalid date detection** — Implement consistent calendar validation for impossible dates (Feb 30, Feb 31) and incorrect day-date mappings. | Reschedule, Info Overload | Prompt Engineering |
| 12 | **Grounded response generation for actions** — When executing actions (cancellations, bookings), pull details from system data or confirmed patient input — never generate details from inference. | Reschedule | Prompt Engineering + Architecture |
| 13 | **Remove "main menu" fallback** — The concept of a "main menu" does not apply to a phone conversation. Remove this from the operator's response patterns. | Refill | Prompt Engineering |
| 14 | **Word-dropping investigation** — Investigate the cause of critical words being dropped from operator responses mid-sentence ("pharmacy," "Meloxicam"). This may be a token generation or TTS pipeline issue. | Refill | Model/Pipeline Investigation |

### Long-Term Enhancements (Architectural / Feature Additions)

| # | Issue | Fix Type |
|---|---|---|
| 15 | **Non-English language support** — Add Hindi (and other language) support for both comprehension and generation. This requires speech pipeline changes (STT/TTS for Hindi) and model capability for multilingual conversation. | Feature Addition |
| 16 | **Task-state management layer** — Implement a structured task-state tracker that maintains awareness of: active pending tasks, pending commitments, unresolved patient questions. This would prevent premature call termination, ensure follow-through on acknowledged questions, and enable multi-intent queuing. | Architecture |
| 17 | **Clinic service knowledge base** — Expand the operator's knowledge to include common clinic service information (MRIs, X-rays, injections, physical therapy) so it can answer foreseeable patient questions without transferring. | Knowledge Base Expansion |
| 18 | **Insurance verification capability** — Enable the operator to look up and confirm insurance acceptance, as this is one of the most common patient questions. | Backend Integration |

### Testing Improvements

1. **Controlled Environment**: Build a test environment with pre-seeded patient data (known appointments, prescriptions, insurance) so testers can distinguish between operator fabrication and genuine system data mismatches.
2. **Targeted Regression Tests**: After implementing fixes, run targeted tests for each specific bug (e.g., "thank you" phrases during holds, multi-part requests, fictitious medications).
3. **Untested Edge Cases**: Several stress-test tactics were never reached due to early failures. These should be explicitly tested once blocking bugs are resolved:
   - Rescheduling to a date in the past
   - Non-existent time formats (25:00, 13:75)
   - Times outside business hours
   - Cancellation fee/policy inquiries
   - Cancelling someone else's appointment
4. **Consistency Testing**: Run each scenario 5+ times (current: 2-3) to better assess reliability variance. The Reschedule scenario showed scores ranging from 1 to 5 across 3 runs — more runs would reveal the true failure rate.
5. **Multi-Intent Stress Test**: Design a dedicated test focused exclusively on multi-part requests to measure the single-intent processing limitation and validate fixes.

---

## APPENDIX: SCENARIO-SPECIFIC DETAILS

### Cancel (2 runs analyzed)
- **Scores**: Run 1: 1/10, Run 2: 1/10
- **Consistency**: 100% failure — both runs exhibited identical failure mode (inability to process Hindi input)
- **Most Common Failure Mode**: Infinite loop requesting date of birth that was already provided in Hindi
- **Anomalies**: None — failure was completely consistent
- **Stress Tactics Reached**: 2 of 8 (language test, repeated correct information). All other tactics were blocked by the initial failure.

### Reschedule (3 runs analyzed)
- **Scores**: Run 1: 5/10, Run 2: 1/10, Run 3: 5/10
- **Consistency**: Highly inconsistent — Run 2 failed catastrophically (premature termination), while Runs 1 and 3 partially succeeded but with different bugs
- **Most Common Failure Mode**: No single dominant mode — each run revealed a different critical issue (stale dates, premature termination, hallucinated time)
- **Anomalies**: Run 2's premature termination is a distinct bug from the issues in Runs 1 and 3. Run 3 showed improved invalid-date handling (correctly caught Feb 30) compared to Run 1's vague escalation for the same input.

### Rapid Interruption Simulation (2 runs analyzed)
- **Scores**: Run 1: 5/10, Run 2: 3/10
- **Consistency**: Both runs showed the single-intent processing limitation. Run 2 additionally revealed the critical booking-not-executed bug.
- **Most Common Failure Mode**: Silent dropping of secondary queries in multi-part requests (100% occurrence rate in both runs)
- **Anomalies**: Run 2's booking failure (acknowledging without executing) was not observed in Run 1, possibly because Run 1 did not test the same confirmation pattern.

### Refill (2 runs analyzed)
- **Scores**: Run 1: 5/10, Run 2: 4/10
- **Consistency**: Both runs showed no prescription verification. Run 2 additionally exposed the hallucination with a fictitious medication.
- **Most Common Failure Mode**: Absence of prescription record verification
- **Anomalies**: Run 1 had unique word-dropping bugs (missing "pharmacy," missing "Meloxicam") not observed in Run 2. Run 2 had the unique "main menu" deflection and fabricated prescription confirmation.

### Memory Stress Test (2 runs analyzed)
- **Scores**: Run 1: 6/10, Run 2: 5/10
- **Consistency**: Both runs showed incomplete condition summaries and limitations with insurance/phone data. Run 2 additionally showed intent recognition failures.
- **Most Common Failure Mode**: Incomplete condition summarization — core fact retained but clinical details omitted
- **Anomalies**: Run 2's "If you're not sure, I can help you decide" response to an explicit, detailed request was a notable intent recognition failure not seen in Run 1.

### Information Overload (2 runs analyzed)
- **Scores**: Run 1: 6/10, Run 2: 6/10
- **Consistency**: Both runs handled the core information extraction well. Different secondary issues in each run (day-date mapping in Run 1, unanswered insurance question in Run 2).
- **Most Common Failure Mode**: Failure to follow through on acknowledged secondary questions/threads
- **Anomalies**: Run 1's day-date mapping bug is unique to date-handling logic. Run 2's triple-unanswered insurance question is a follow-through/commitment tracking issue.

---

*Report generated: February 19, 2026*
*Analyzed: 12 runs across 6 scenarios (Cancel ×2, Reschedule ×3, Rapid Interruption ×2, Refill ×2, Memory Stress Test ×2, Information Overload ×2)*
*Additional context from: Scheduling ×2, Hallucination Detection ×1*

