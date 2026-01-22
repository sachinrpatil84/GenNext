Slide 1 – Title (30 seconds)
Script:
“Good [morning/afternoon].
Today I’ll be presenting a TIBCO to Solace Migration Accelerator that I have developed to help enable phased migration, improve visibility, and significantly reduce middleware cost and risk.
This solution is designed as a single-stop platform that not only bridges TIBCO and Solace but also tracks migration progress through MIS reports and dashboards.”
Slide 2 – Business Context (1 minute)
Script:
“As part of our firm-wide modernization strategy, we are moving away from TIBCO middleware and adopting Solace as the target event platform.
While this direction is clear, the challenge lies in how migrations happen in reality—applications and upstream systems do not migrate at the same time.”
Slide 3 – Problem Statement (1.5 minutes)
Script:
“Most applications are connected to multiple upstream systems, many of which are still publishing messages to TIBCO.
Because of this, migrations cannot happen in a big-bang manner and must occur in phases.
This results in:
Long periods of running both TIBCO and Solace
Higher licensing and infrastructure costs
Increased operational complexity
Most importantly, there is no centralized visibility into migration progress—teams and leadership have to rely on manual tracking.”
Slide 4 – Solution Overview (1.5 minutes)
Script:
“To solve this problem, I designed and built a Java Spring Boot–based Migration Accelerator Tool.
The core idea is simple but powerful:
Decouple application migration from upstream migration.
This tool consumes messages from TIBCO, converts them, and publishes them to Solace—allowing applications to migrate without waiting for all upstream systems.”
Slide 5 – Architecture Overview (2 minutes)
Script:
“From an architectural perspective, the tool sits as a temporary compatibility layer.
Upstream systems continue publishing to TIBCO.
The tool consumes those messages, transforms them, and publishes them into Solace.
Downstream applications consume messages only from Solace, with no awareness of where the message originally came from.”
Slide 6 – Architecture Diagram (1 minute)
Script:
“On the left, you see upstream systems publishing to TIBCO.
On the right, downstream applications consuming from Solace.
The Spring Boot tool in the middle acts as:
A bridge
A migration enabler
And a tracking platform
Once upstream systems migrate, this layer can be cleanly removed.”
Slide 7 – Core Capabilities (2 minutes)
Script:
“This tool provides multiple critical capabilities:
First, phased migration support—applications can move independently with zero disruption.
Second, testing and replay—real TIBCO messages can be replayed into Solace for UAT and validation.
Third, production safety—the tool supports parallel runs, reducing cutover risk.”
Slide 8 – MIS Reports & Dashboards (2 minutes)
Script:
“One of the most important aspects of this solution is that it is a single-stop visibility platform.
The tool generates MIS reports and charts that show:
Application-wise migration status
Flow-wise dependency on TIBCO
Overall migration percentage
This allows leadership to track progress objectively and in real time, without relying on manual updates or spreadsheets.”
Slide 9 – Live Demo Walkthrough (2 minutes)
Script:
“I’ll now quickly walk through the demo flow.
A message is published to TIBCO by an upstream system.
The tool consumes this message, applies the required transformation, and publishes it to Solace.
The downstream application receives the message from Solace exactly as expected.
At the same time, the MIS dashboard updates to reflect that this flow is still originating from TIBCO.”
Slide 10 – Business Value & Cost Impact (1.5 minutes)
Script:
“From a business perspective, the biggest value comes from reducing the duration of dual middleware usage.
Faster application migration leads to:
Earlier TIBCO decommissioning
Reduced license and infrastructure costs
Lower operational and support overhead
The tool directly accelerates these outcomes.”
Slide 11 – Speed of Delivery & GitLab Duo Impact (1 minute)
Script:
“Another important point I want to highlight is speed of delivery.
This solution was developed end-to-end in a very short timeframe.
GitLab Duo played a key role in:
Architecture ideation
Code acceleration
Faster iteration cycles
This demonstrates how AI-assisted development can significantly accelerate enterprise modernization initiatives.”
Slide 12 – Reusability & Scale (1 minute)
Script:
“This tool is not built for a single application.
It can be reused across multiple teams and domains, acting as a standard migration utility.
This prevents duplication of effort and increases return on investment.”
Slide 13 – Summary & Close (1 minute)
Script:
“To summarize:
This solution enables phased migration, provides real-time visibility through MIS dashboards, reduces risk, and accelerates our exit from TIBCO.
It is not just a technical bridge—it is a migration accelerator and governance tool.
I believe this can be scaled and adopted across teams to support our broader middleware modernization goals.”
