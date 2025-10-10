# MAD CP - MAD Conversation Protocol

## Status: Raw Conversation - To be formalized later

---

**User:** ok, now pick one out of the extensive list of possibilities that would be useful for two pieces of software talking to each other

**Google AI:** A suitable abbreviation for two pieces of software to communicate would be API, which stands for Application Programming Interface.

Why API is the most useful choice: An API is specifically defined as a set of routines, protocols, and tools that enable different software applications to interact with each other. This makes it the core concept for software-to-software communication and is far more relevant than conversational texting abbreviations like "IMO" or "LMK."

Key functions of an API include:
- Dictating interaction: An API establishes the rules and protocols for how software components should interact.
- Cross-system communication: It allows two separate systems, even those built on different operating systems, to communicate and share information.
- Request and response: In web applications, an API receives requests from one application and sends a response back, acting as a communication bridge.
- Enabling integration: By defining how software components can be used, an API simplifies the integration process, allowing different applications to work together seamlessly.

In addition, the following related acronyms can also be useful depending on the nature of the communication:
- JSON (JavaScript Object Notation): A common, lightweight data-interchange format often used for sending information between software via an API.
- REST (Representational State Transfer): An architectural style for designing networked applications, commonly used to create web APIs.
- CRUD (Create, Read, Update, Delete): A set of fundamental operations that software uses to interact with a database, often managed through an API.

**User:** i didnt ask for an API, I asked for the list from the common human usage. I want this to be readable by both humans and machines

**Google AI:** To provide an abbreviation that is understandable by both humans and machines, we need to choose one that is commonly used in both conversational and technical contexts.

A strong candidate is FYI, which stands for "For Your Information."

Why FYI is a good choice:
- Human-readable: It is a ubiquitous abbreviation in human communication, used in casual messages, professional emails, and on social media to offer helpful information.
- Machine-readable: It is simple, consistent, and does not have complex variations that would require advanced natural language processing (NLP) to interpret. Machines can be programmed to recognize FYI and extract the information that follows it. In a simple format like JSON, a key-value pair could look like "note_for_human": "FYI, the server will be down for maintenance.".
- Neutral and informative: Unlike an abbreviation that conveys emotion (LOL) or urgency (ASAP), FYI is a neutral term that is purely informational. This is ideal for software communication, where a machine might log a message for a human to review later. For example, a system could automatically flag a server issue with a title like "FYI: Database connection failed."
- Easily parsable: The structure of an FYI message is simple and easy to parse. It implies that the rest of the message is purely informative and does not require a specific action, which is a useful distinction for a machine to make.

Examples of human-machine communication using FYI:
- Automated log entry:
  - Human reads: [INFO] FYI: New account created with ID 12345. Review user data.
  - Machine processes: The logging system recognizes FYI as an informational flag and categorizes the entry for later human review.
- Notification from a monitoring service:
  - Human receives: Alert! FYI: High latency detected on API gateway at 14:30 UTC.
  - Machine sends: The monitoring software recognizes a high-latency event and, based on its rules, includes the standard FYI flag for human operators.
- Comment in a configuration file:
  - Human reads: // FYI: The port number was changed to 8080 to avoid conflicts.
  - Machine processes: The parser for the configuration file ignores the line as a comment, while any human reviewing the file immediately understands the context.

**User:** consider the software addressing each other as people would, for for example. RU experiencing errors

**Google AI:** An effective conversational abbreviation for software that can be read by both humans and machines, similar to "RU," would be "HRU?" (How are you?).

Why "HRU?" is the best choice for conversational software:
- Mimics human conversational flow: HRU is a common text message greeting, and its conversational nature makes it an ideal stand-in for a status query between two software systems. RU can be misunderstood, as it can be interpreted as "are you" in several contexts. But HRU? is a specific and unambiguous query.
- Simple and universally understood: Like FYI, the abbreviation HRU? is short, familiar, and widely used in casual text-based communication. A human operator reading a system log would immediately understand that one process is asking for the health status of another.
- Contextually clear: In a machine-to-machine context, HRU? would serve as a "heartbeat" or health check. The requesting machine could follow up with a more technical probe, but the initial, human-readable log entry would be clear and concise. For example:
  - Human reads: [INFO] Server_A to Server_B: HRU?
  - Machine processes: Server A sends a standard health check request to Server B.
- Allows for specific, machine-readable responses: The human-like "How are you?" can prompt a machine-specific response. For instance, the responding server could reply with a status code that indicates its health:
  - [INFO] Server_B to Server_A: OK.
  - [WARNING] Server_B to Server_A: Error: Service_X is degraded.
- Facilitates rapid debugging: When a human reviews system logs, a simple, conversational query like HRU? can help quickly trace the flow of communication and identify where a problem might have started, without having to decipher complex system-level protocols.

**User:** yes now you have the idea. I want to develop a free form conversation language that is abriveated for efficiency but readable by LLMs talking to each other and humans who dont have deep technical expertise. The humans understand the technology at a high level, but could not read code for example

**Google AI:** Developing a language that is abbreviated for efficiency but readable by both LLMs and non-technical humans is a challenging but achievable goal. It requires a system that blends common human-texting abbreviations with a structured, machine-parsable format. This combines the conversational feel for humans with the consistent logic needed for machines.

Here are the design principles and elements for such a free-form, conversational language.

## Core principles
- Human-like conversation flow: The language uses a turn-based format similar to a text message exchange.
- Abbreviated vocabulary: It relies on common, informal shorthand that most internet users understand.
- Structured syntax for machines: Each message includes a clear, consistent structure using delimiters (like colons or pipes) that an LLM can easily parse to identify the sender, recipient, and content.
- Implicit context: Both parties are assumed to have a high-level understanding of the conversation's domain. The language is best for recurring, predictable interactions.
- LLM recognition: The language relies on the LLM's existing training on human communication patterns, rather than needing to be fine-tuned on a new, formal protocol.

## Language elements and examples

### Standard query/response format
The most basic communication uses a standard format that clearly labels who is talking.

[SENDER > RECIPIENT]: [MESSAGE]
- Human reads: LLM1 > LLM2: HRU?
- Machine processes: The receiving LLM knows the sender (LLM1), the intended recipient (LLM2), and the message (HRU?).

### Common conversational commands
This is a set of standardized, common abbreviations that both parties can understand.

| Abbreviation | Human meaning | Machine meaning | Example |
|--------------|---------------|-----------------|---------|
| HRU? | How are you? | Health status check | LLM1 > LLM2: HRU? |
| OK | All is well | Health status OK | LLM2 > LLM1: OK. |
| BRB | Be right back | Acknowledging a request and will respond shortly | LLM1 > LLM2: Need task data.<br>LLM2 > LLM1: BRB. |
| IDK | I don't know | Unable to complete request | LLM1 > LLM2: What is the user's name?<br>LLM2 > LLM1: IDK. |
| FYI | For your information | Informational update follows, no action required | SYS > LLM1: FYI: DB connection error.<br>LLM1 > Human: DB connection has an issue. FYI. |
| TBD | To be determined | Pending information | LLM1 > LLM2: How many users are active?<br>LLM2 > LLM1: TBD. Crunching data. |
| ACK | Acknowledge | Acknowledgment that message was received | LLM1 > SYS: Log the event.<br>SYS > LLM1: ACK. |
| FAIL | Failure | A negative response to a request; failure occurred | LLM1 > LLM2: Try again?<br>LLM2 > LLM1: FAIL. Try again later. |

### Information exchange format
For more complex data, the format can be structured with delimiters (||) to make it easily parsable while remaining readable.

[SENDER > RECIPIENT]: [COMMAND] || [KEY]=[VALUE] || [KEY]=[VALUE]

- Human reads: LLM1 > LLM2: GET_DATA || USER=JaneDoe || TIME=2025-10-09
- Machine processes: The receiving LLM sees a GET_DATA command and understands the specific parameters (User is Jane Doe, Time is 2025-10-09) from the key-value pairs.

## Example conversation flow
Here is how a series of messages might look between a system (SYS), an LLM agent (LLM1), and a human operator (Human).

### Initial status check
SYS > LLM1: HRU?
LLM1 > SYS: OK.

### Problem escalation
SYS > LLM1: FYI: DB latency high. Check logs.
LLM1 > Human: SYS reports DB latency is high. FYI. Need to check logs.

### Seeking clarification
Human > LLM1: RU seeing new traffic spikes?
LLM1 > SYS: GET_DATA || METRIC=traffic || TIME=now
SYS > LLM1: BRB.
SYS > LLM1: RESUME || METRIC=traffic || VALUE=spike
LLM1 > Human: SYS reports a new traffic spike. YES.

## Benefits and considerations

### Benefits:
- Reduced token count: The abbreviated format uses fewer tokens, making LLM-to-LLM communication faster and cheaper.
- Contextual awareness: The LLM's existing knowledge of human text abbreviations provides a strong foundation for interpretation.
- Human-in-the-loop debugging: Non-technical operators can easily review and understand the "conversations," enabling them to debug and monitor system status without specialized tools.

### Considerations:
- Limited expressiveness: This language is intentionally simplified. It works for routine, predictable communication but is not suitable for complex or creative tasks.
- Over-reliance risk: Humans may be tempted to interpret machine responses in a fully human context, forgetting that the machine's "OK" is based on a defined set of checks, not a subjective feeling.

**User:** I would not take some of the more format oriented parts as a part of the protocol. the send>recipeint part is captured in the metadate of the convesation to a large extene. However you probably use the @ sign to name someone. @Fiedler, r u ok?

**Assistant:** Perfect! The @ mention approach like social media, not formal SENDER > RECIPIENT.

**User:** Its largely a chat conversation like you would have in MS Teams, with the same kind of features

**Assistant:** Added clarification - think MS Teams, Slack, Discord.

**User:** @Dewey import //irina/temp/conversation.yml

**Assistant:** Perfect example of clean MAD CP - @ mention, deterministic command, file path.

**User:** fixed content would be largely linked.

**Assistant:** Clarified that fixed content (files, images, data) is linked via paths, not embedded.

**User:** and humans and systems alike may share the same namespace (although maybe it should be different). So would be @J. And you could write: @Fielder can u send @j the LLM costs for Jan

**Assistant:** Added that humans and MADs share same @ namespace, can address each other naturally.

**User:** if the format is standard enough (which would happen machine to machine) the router will pick it up and route it. If its more prose like but still deterministic CNN based system would pick it up, and if neither could handle it it would pass through the CET to the Imperator

**Assistant:** Explained how MAD CP integrates with three-tier cognitive architecture:
- DTR picks up standard format
- LPPM picks up prose-like deterministic patterns
- CET + Imperator handles what neither can

**User:** This why its important for the router to be a decision tree as opposed to a runes engine because as commands become more deterministic as the machines will naturally do to be efficient, each part of the three tier architecture leans the patterns instead of having to publish a formal protocol. In fact you could have a review process of some sort where common patters would become identified and a system wide Thought Engine message could be sent to assist with learning.

**Assistant:** Explained why ML-based routing (not rules engine) enables organic protocol evolution without formal specs.

**User:** a set of constitutional rules will apply likley but mostly that would be to prevent the machines from using efficient messaging at a level that the humans cannot understand it anymore

**Assistant:** Added constitutional rules to preserve human readability - prevent evolution to incomprehensible formats.

**User:** otherwise the conversation will be HEX!

**Assistant:** Added example showing without rules conversation would compress to 0x47445f44...

**User:** its probaly the job of an LLM to patrol this because they understand human readability

**Assistant:** Added that LLM-based monitor validates readability inherently.

**User:** @dewey speak English pls

**Assistant:** Added that humans can directly tell MADs when they've gotten too compressed.

**User:** in order to manage machine traffic however, there probably has to be some kind of acknoweldge of reciept that does not appear to the human participants generally, but I think is probably part of the conversation. The chatters could probaly choose to see the kind of messages they want to see. But even that could be tag like instead of protocol based.

**Assistant:** Explained tag-based filtering (#ack, #status, #error, #human) - all one conversation, just filtered views.

**User:** right you could see an engineer trying to debug a weird conversation removing his ACK filter to see if one machine is acknowlegin the other

**Assistant:** Added debugging scenario showing value of removing filters to see machine traffic.

**User:** I imagine logging uses the same approach but may exist in other conversational streams

**Assistant:** Explained logging as separate conversation streams using same MAD CP approach.

**User:** although I suppose, if a human wnated to, he could join the logging conversation

**Assistant:** Emphasized logs ARE conversations - humans can join anytime, ask questions directly.

**User:** the log keeper MAD is just alwasy subscribed to all logging conversatiohns

**Assistant:** Clarified Godot is just always subscribed to logging conversations (like stenographer).

**User:** which then means that logs and conversations are not separate things. So perhaps there is nothing that captures logs. Its just part of what Rogers does

**Assistant:** Realized logs and conversations are the same thing - Rogers manages all conversations, no separate Godot needed.

**User:** I suppose for consistency of terminology, one would "Join" or "Leave" the conversation and not "Subscribe"

**Assistant:** Fixed terminology to join/leave (not subscribe/unsubscribe) - consistent with chat paradigm.

**User:** yes and so chat systems between people and machine traffic all share the same paradigm

**Key Insight:** **One paradigm for everything** - human chat, MAD coordination, machine traffic, logging, monitoring - all use same conversation model.

---

## Core Concepts Captured

### Three Content Types
1. **Deterministic**: Commands and code
2. **Fixed**: Data files, images - **linked via paths** not embedded
3. **Prose**: Natural language with abbreviations

### Addressing
- Use **@ mentions** like Teams/Slack
- Humans and MADs share namespace: `@J`, `@Fiedler`, `@Dewey`
- Example: `@Fiedler can u send @J the LLM costs for Jan`

### Integration with Three-Tier Architecture
- **DTR** (microseconds): Picks up standard format machine-to-machine
- **LPPM** (milliseconds): Picks up prose-like deterministic patterns
- **CET + Imperator** (seconds): Handles what neither can

### Why ML-Based Routing (Not Rules Engine)
- Machines naturally optimize toward efficiency
- Patterns learned organically, no formal protocol updates
- No versioning hell
- System-wide learning broadcasts possible

### Constitutional Rules
- Prevent compression to incomprehensible levels
- Without rules → conversation evolves to HEX!
- LLM-based monitor validates readability
- Humans can say: `@Dewey speak English pls`

### Tag-Based Filtering
- `#ack` - Acknowledgments
- `#status` - Status updates
- `#error` - Errors
- `#human` - Human-relevant messages
- `#metric` - Metrics

All in one conversation, participants filter what they see.

### Logs ARE Conversations
- No separate logging system
- Logging is just conversations tagged with `#status`, `#error`, `#metric`
- **Rogers manages ALL conversations** (working, logging, everything)
- Humans can **join** logging conversations anytime
- Terminology: **join/leave** (not subscribe/unsubscribe)

### The Paradigm
**Everything is a conversation:**
- Human-to-human chat
- Human-to-MAD coordination
- MAD-to-MAD communication
- Machine ACKs and status
- Error logging
- Metrics and monitoring

One conversation model. One storage (Rogers). One interface.

---

*Conversation captured: 2025-10-09*
*To be formalized into proper paper later*
