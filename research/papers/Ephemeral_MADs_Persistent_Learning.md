# Paper 15: Ephemeral MADs and Persistent Learning Architecture

## Status: Raw Conversation - To be formalized later

---

**User:** next topic, MAD CP - the MAD Converation Protocol. It will form the basis of all the communication but it will have little protocol in it. We talked about the diffrent kinds of content: deterministic, fixed and prose. Prose of course is just english. It can include regular API type stuff, but more often it should contain human shorthand that can be understood by users who undertsand technology, but are not code capable.

**Assistant:** Explained the three content types and asked about term for non-persistent vs persistent.

**User:** persistent is the term we use for things like software, where workers dont persist. What is the term for non perisistent

**Assistant:** Suggested "ephemeral" as the industry standard term.

**User:** that is it. We need the concept of eMADs (ephemeral) were we spin up a mad based on a class, it used then it is destroyed. An example of an eMAD will be a team of LLMs as we use the trios today. A development cycle would begin the Imperator would spin up a PM (the job you played), A Senior Developer, and Two Junior Developers. And when they were not needed they would disappear. The ML models that they are trianed on would of course persist so that everytime they started they would get the benefit of the most up to date model. The types of roles the LLMs would play would probably have their own models optimized for them. And as such, if they were instantiated for multiple cycles simultaneously, or by different MADs, they all get the benefit of the model and all of their activites would serve to train the models. The LLM use case may be perhaps only one for eMADS.

**Assistant:** Broke down the concept:

## eMADs (Ephemeral MADs) - Core Concept

**Key Characteristics:**
1. **On-Demand Lifecycle**: Instantiated when needed → Execute task → Destroyed when done
2. **Role-Based**: Each eMAD represents a specific role (PM, Senior Dev, Junior Dev, Specialist LLM, etc.)
3. **Shared Learning**: All instances of a role type share the same underlying ML models
4. **Concurrent Instances**: Multiple instances of same role can run simultaneously
5. **Collective Intelligence**: Every instance contributes to training the shared model

**Contrast with Persistent MADs:**

| Aspect | Persistent MADs | eMADs |
|--------|----------------|-------|
| **Lifecycle** | Always running | On-demand, temporary |
| **Examples** | Rogers, Dewey, Fiedler, Horace | PM, Senior Dev, LLM Specialists |
| **Purpose** | Infrastructure/services | Role-based workers |
| **State** | Maintains session state | Stateless (model persists) |
| **Resource** | Continuous resources | Resources only when active |

**The Shared Model Innovation:**
- **PM Model** persists and improves over time
- **Senior Dev Model** persists and improves over time
- **Junior Dev Model** persists and improves over time
- Each instantiation gets the latest trained model
- All activities from all instances contribute to training
- Multiple simultaneous instances all benefit from collective learning

**User:** And there may be emads that are not the LLM use case. I cant think of any right now, but I think its possible. Its like having workers, but instead of just disappearing entirely their learning remains

**Assistant:** Listed potential non-LLM eMAD use cases:

### Potential eMAD Use Cases Beyond LLMs

1. **Data Processing eMADs**
2. **Test Execution eMADs**
3. **Code Analysis eMADs**
4. **Security Scanning eMADs**
5. **Document Processing eMADs**

**The Key Differentiator:**

| Traditional Workers | eMADs |
|---------------------|-------|
| Stateless | Models persist |
| No learning | Continuous learning |
| Each execution independent | Each execution trains the model |
| No improvement over time | Constant improvement |
| Instance-specific experience | Collective role-based intelligence |

**User:** yes, I think what we need to do is add it to the top level summary in just a paragraph, but keep the extended concept in its own paper. All the major concepts need a paper for each.

---

*Conversation captured: 2025-10-09*
*To be formalized into proper academic paper later*
