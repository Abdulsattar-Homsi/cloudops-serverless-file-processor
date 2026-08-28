# Architecture

## Event-driven processing

```mermaid
flowchart TD
    U["Upload TXT, CSV, or unsupported file"] --> I["Private incoming container"]
    I -->|"Microsoft.Storage.BlobCreated"| T["Event Grid system topic"]
    T -->|"Filtered to incoming path"| S["Event subscription"]
    S -->|"Blob extension webhook"| F["process_blob_upload"]
    F --> V{"Validation result"}
    V -->|"Valid"| P["Process content and calculate SHA-256"]
    P --> O["processed/<name>.json"]
    V -->|"Rejected"| R["Build structured failure report"]
    R --> X["failed/<name>.json"]
```

The Event Grid subject filter begins with `/blobServices/default/containers/incoming/blobs/`. Output writes therefore do not trigger another execution.

## Identity and authorization

```mermaid
flowchart TD
    G["GitHub Actions"] -->|"OIDC short-lived token"| D["Deployment user-assigned identity"]
    D -->|"Website Contributor<br/>Function scope"| F["Azure Function App"]
    F -->|"System-assigned identity"| R["Azure RBAC"]
    R --> B["Blob data"]
    R --> Q["Queue data for trigger coordination"]
    R --> H["Host and deployment storage"]
    F -->|"Microsoft Entra authenticated telemetry"| A["Application Insights"]
```

Runtime and deployment access remain passwordless after Storage Shared Key authorization is disabled.

## CI/CD pipeline

```mermaid
flowchart TD
    C["Push to main"] --> W["GitHub Actions runner"]
    W --> T["Compile check and seven unit tests"]
    T -->|"Pass"| O["GitHub OIDC token"]
    O --> L["Azure login"]
    L --> B["Flex remote build"]
    B --> D["One Deploy package"]
    D --> F["Azure Function App"]
    T -->|"Fail"| X["Deployment blocked"]
```

The federated credential is restricted to the repository and `main` branch and uses GitHub's immutable owner and repository identifiers.

## Monitoring and alerting

```mermaid
flowchart TD
    F["Function execution"] --> T["Structured traces"]
    T --> A["Application Insights"]
    A --> L["Log Analytics workspace"]
    L --> K["KQL scheduled query"]
    K -->|"Validation failures > 0"| R["Azure Monitor alert"]
    R --> G["Action Group"]
    G --> E["Email notification"]
```

The tested alert detects structured validation rejection traces, transitions to `Fired`, and automatically resolves when the query window no longer contains matching events.

