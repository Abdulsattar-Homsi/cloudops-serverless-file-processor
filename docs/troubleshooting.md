# Troubleshooting and lessons learned

## 1. Event Grid reported a TLS error although TLS was correct

### Symptom

Creating the Event Grid subscription failed with:

```text
MinimumTlsVersion is not supported by webhook endpoint
```

### Investigation

Both the Function App and Event Grid webhook were configured for TLS 1.2. Selecting the system topic's TLS version produced the same error, which showed that changing TLS settings was not resolving the underlying problem.

The Blob extension webhook was then tested directly with a simulated `Microsoft.EventGrid.SubscriptionValidationEvent`. PowerShell returned:

```text
No such host is known
```

### Root cause

The endpoint used the legacy predictable hostname:

```text
<function-app-name>.azurewebsites.net
```

The portal-created Function App had a secure unique default hostname instead:

```text
<function-app-name>-<hash>.<region>.azurewebsites.net
```

The TLS message was therefore a secondary webhook-validation error. Event Grid could not resolve the hostname and never reached the Function App.

### Resolution

The actual `Default domain` was copied from the Function App Overview page and used to build the Blob extension endpoint:

```text
https://<actual-default-domain>/runtime/webhooks/blobs?functionName=Host.Functions.process_blob_upload&code=<blobs_extension_key>
```

Webhook validation then succeeded and the Event Subscription entered the `Succeeded` provisioning state.

### Lesson

Do not infer a cloud endpoint from a resource name. Retrieve the platform-provided hostname and test DNS and the webhook independently when a higher-level deployment error is ambiguous.

## 2. GitHub federated credential required immutable identifiers

### Symptom

The Azure portal disabled the Add button and displayed guidance to use immutable GitHub organization and repository identifiers.

### Root cause

New GitHub repositories use an OIDC subject format containing numeric owner and repository IDs. A legacy name-only subject did not match the repository's token format.

### Resolution

The public GitHub repository metadata was queried to obtain `owner.id` and `repository.id`. The federated credential used an immutable subject in this form:

```text
repo:<owner>@<owner-id>/<repository>@<repository-id>:ref:refs/heads/main
```

### Lesson

OIDC removes stored secrets, but the trust boundary must still be exact. Immutable identifiers prevent a renamed, transferred, or recreated repository from silently inheriting deployment trust.

## 3. Storage keys could not be disabled before deployment storage was converted

### Risk

Flex Consumption stores the application package in Blob Storage. Disabling Shared Key access while deployment storage still used a connection string could break future GitHub Actions deployments or Function startup.

### Resolution

The deployment storage authentication type was changed to `SystemAssignedIdentity`. A GitHub Actions deployment was verified before and after disabling Storage Shared Key access.

### Lesson

Security hardening must include platform dependencies, not only application bindings. Safe migration uses the sequence: grant identity, configure identity authentication, verify, remove secrets, disable legacy authentication, verify again.

## 4. Generated files were committed empty

### Symptom

Git reported new files but showed `0 insertions`, indicating that the editor buffers had not been saved before the commit.

### Resolution

All files were saved, file lengths were verified, seven tests were run, and the commit was amended. The corrected commit showed the expected insertions.

### Lesson

Before committing generated or newly created files, validate file size, run tests, inspect `git diff`, and review the commit statistics.

## 5. Local Event Grid behavior differs from Azure

Azurite emulates Blob, Queue, and Table Storage but does not publish Azure Event Grid events. Local testing therefore verifies the Functions host and the isolated processing core. The complete BlobCreated-to-Function integration must be tested in Azure or invoked with a simulated event payload.

Separating `file_processor.py` from the trigger made seven unit tests possible without Azure, Storage, or Event Grid dependencies.

