# Deploy the research demonstration to AWS

This is a prepared deployment procedure, not a record of a completed deployment.
Use one **Amazon Lightsail container service** to run the image tested locally.
Lightsail stores the uploaded image and provides an HTTPS address. The application
inside the container listens on port 8000. This keeps the cloud demonstration to
one service. [AWS container service overview](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-container-services.html)

The endpoint is public and has no login. Use the project's prepared public study
examples for the demonstration. The application accepts uploaded CSVs, so this
setup is not suitable for private clinical data.

AWS documentation was checked on September 17, 2026. App Runner is no longer an
option for new customers as of April 30, 2026.
[AWS availability notice](https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html)

## 1. Test the image locally

Run these PowerShell commands from the project root after preparing the frozen
model and public examples described in the README:

```powershell
uv run --frozen python scripts/prepare_container.py --output-dir build/container
docker build --platform linux/amd64 -t kidney-biopsy:demo .
uv run --frozen python scripts/verify_container.py --image kidney-biopsy:demo --bundle-dir build/container --output results/checks/container-local/verification.json
```

Reuse an existing verified bundle instead of preparing over it. Use a new output
directory for each verification record. Do not continue to AWS if the local
container check fails. The image contains the model, its metadata, and the public
examples; cloud startup does not train a model or download study inputs.

Keep the source revision and the actual image ID with the verification result:

```powershell
git rev-parse HEAD
docker image inspect kidney-biopsy:demo --format '{{.Id}}'
```

## 2. Sign in and check the cost

Install AWS CLI v2 and the `lightsailctl` plugin using the
[AWS installation instructions](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-install-software.html).
Docker must be running in Linux container mode. Confirm the tools are available:

```powershell
aws --version
Get-Command lightsailctl
docker info --format '{{.OSType}}'
```

Use your own AWS account and an identity allowed to manage Lightsail container
services. The browser sign-in below requires AWS CLI 2.32.0 or later and the
`SignInLocalDevelopmentAccess` permission. If your account uses IAM Identity
Center, sign in to its configured profile with `aws sso login` instead.
[AWS sign-in instructions](https://docs.aws.amazon.com/signin/latest/userguide/command-line-sign-in.html)

```powershell
$DemoProfile = 'kidney-demo'
$DemoRegion = 'us-east-1'
$DemoService = 'kidney-biopsy-demo'
aws login --profile $DemoProfile --region $DemoRegion
aws sts get-caller-identity --profile $DemoProfile
aws lightsail get-container-service-powers --profile $DemoProfile --region $DemoRegion --output table --no-cli-pager
```

Check that the returned account is the one you intend to use. Select an unused
service name if `kidney-biopsy-demo` already exists.

The commands below start with one **Micro** node: 1 GB memory and 0.25 shared vCPU.
The listed base price was **$10/month per node** when checked; transfer overages
can add charges. Check the live pricing before creating the service. This is a
starting allocation, not a measured capacity claim. Verify startup and request
time on AWS before the presentation. Delete the service after the demonstration;
do not assume disabling it stops billing.
[Lightsail pricing](https://aws.amazon.com/lightsail/pricing/)

## 3. Create the service and upload the image

**This step creates a billable AWS resource.** Run it when ready to host the
demonstration. No AWS credentials belong in the image or deployment JSON.

```powershell
aws lightsail create-container-service --service-name $DemoService --power micro --scale 1 --profile $DemoProfile --region $DemoRegion --no-cli-pager
aws lightsail get-container-services --service-name $DemoService --profile $DemoProfile --region $DemoRegion --query 'containerServices[0].state' --output text
```

Wait until the state is `READY`; rerun the second command to check. Then upload
the image that passed the local check:

```powershell
aws lightsail push-container-image --service-name $DemoService --label research --image kidney-biopsy:demo --profile $DemoProfile --region $DemoRegion
```

Copy the **exact numbered image name** printed by that command. For example,
the first upload might be `:kidney-biopsy-demo.research.1`. Use the number returned
by AWS, not `latest`, so this deployment refers to a specific uploaded image.
[AWS image upload instructions](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-pushing-container-images.html)

## 4. Deploy that version

The two small configuration files have separate purposes:

| File | Meaning |
| --- | --- |
| `deploy/lightsail-containers.json` | Run one container named `api` and open its HTTP port 8000 |
| `deploy/lightsail-endpoint.json` | Route the public endpoint to `api:8000`; require HTTP 200 from `/health` |

Replace the placeholder below with the exact image name from the upload. Write
the filled configuration under ignored `build/`, leaving the tracked template
unchanged:

```powershell
$DemoImage = 'REPLACE_WITH_NUMBERED_IMAGE_NAME'
$DemoContainers = Get-Content deploy/lightsail-containers.json -Raw | ConvertFrom-Json
$DemoContainers.api.image = $DemoImage
$DemoContainers | ConvertTo-Json -Depth 10 | Set-Content build/lightsail-containers.json -Encoding ascii
aws lightsail create-container-service-deployment --service-name $DemoService --containers file://build/lightsail-containers.json --public-endpoint file://deploy/lightsail-endpoint.json --profile $DemoProfile --region $DemoRegion --no-cli-pager
```

The Docker image supplies its startup command and model paths. `/health` returns
503 if the model cannot load, so serving the HTML page alone cannot pass readiness.
Lightsail handles HTTPS for its public address and forwards to HTTP port 8000.
[AWS deployment configuration](https://docs.aws.amazon.com/cli/latest/reference/lightsail/create-container-service-deployment.html)

Check deployment progress:

```powershell
aws lightsail get-container-services --service-name $DemoService --profile $DemoProfile --region $DemoRegion --query 'containerServices[0].{state:state,active:currentDeployment.state,next:nextDeployment.state,url:url}' --output table
```

Continue when the service is `RUNNING` and the current deployment is `ACTIVE`.
For a later update, also check that the current deployment uses the numbered
image you just selected. A failed update can leave the previous image running.
If deployment fails, inspect the service's state detail and container logs:

```powershell
aws lightsail get-container-services --service-name $DemoService --profile $DemoProfile --region $DemoRegion --no-cli-pager
aws lightsail get-container-log --service-name $DemoService --container-name api --profile $DemoProfile --region $DemoRegion --no-cli-pager
```

## 5. Verify the cloud application

Get the HTTPS address and run the same prediction check against it:

```powershell
$DemoUrl = aws lightsail get-container-services --service-name $DemoService --profile $DemoProfile --region $DemoRegion --query 'containerServices[0].url' --output text
uv run --frozen python scripts/verify_container.py --url $DemoUrl --bundle-dir build/container --output results/checks/lightsail-first-deployment/cloud.json
```

This checks readiness, model identity, public examples, expected scores and flags,
and rejection of invalid input. Then open `$DemoUrl` in a browser and run a public
example through the page. Record the observed response time during rehearsal.

Save the date, region, service name, numbered image name, deployment version,
source revision, image ID, and verification file in a short deployment note.
These are the evidence for saying the application was deployed. This guide alone
is not that evidence. Do not include credentials or AWS account identifiers in
the public note.

For an update, build and verify a new image, push it, and repeat steps 4 and 5
with its new numbered name. To restore a previously verified image, repeat step
4 with that earlier name, then verify it again.

## 6. Remove the demonstration

Once the demonstration is finished, delete this service. Deletion permanently
removes its deployments and stored images, so preserve the local verification
record first. This procedure creates no custom domain or separate database.
[AWS deletion instructions](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-deleting-container-services.html)

```powershell
aws lightsail delete-container-service --service-name $DemoService --profile $DemoProfile --region $DemoRegion
aws lightsail get-container-services --profile $DemoProfile --region $DemoRegion --query 'containerServices[].containerServiceName' --output table
```

Confirm the service disappears from the regional list and check the AWS billing
page for the final charges. Stopping your local Docker container does not remove
the AWS service.
