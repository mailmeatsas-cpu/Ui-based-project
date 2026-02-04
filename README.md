# Ui-based-project

I need help building an Onboarding Portal web application for tracking multi-phase infrastructure deployment projects. Here are the requirements:

### PROJECT OVERVIEW
I have a 9-phase onboarding process for deploying Pega applications on AWS EKS. Currently tracked in Excel, but I need a simple web UI to:
1. Track project progress across all phases
2. Show commands/steps that engineers need to execute manually
3. Show links/actions for various external systems (JIRA, ServiceNow, Nexus, GitLab, etc.)
4. Allow marking tasks as complete
5. Store execution notes and outputs
6. Eventually add automation hooks (but start with manual process)

### TECHNICAL STACK
- Python with Streamlit (simple web UI)
- SQLite database (file-based, no server needed)
- Should run on single EC2 instance or locally
- Only dependencies: AWS CLI access, GitLab (for storing runbooks)

### THE 9 PHASES (from my Excel)

**Phase 1: Prerequisites**
Tasks include:
- Create AD Groups for AWS (Command: PowerShell New-ADGroup)
- Create AD Groups for EKS - User Cluster Admin (Command: PowerShell)
- Create AD Groups for EKS - User Operator Admin (Command: PowerShell)
- Create AD Groups for EKS - User Cluster Developer (Command: PowerShell)
- Request AWS Account (Action: Create Service Request in ServiceNow)
- Setup GitLab group and projects (Action: GitLab API calls)
- Raise Request for GitLab AD group (Action: ServiceNow ticket)
- System Account Creation for GitLab Pipeline (Action: AD request)
- AD Group Access Request for GitLab System User (Action: ServiceNow)
- Setup Nexus repository (Action: Nexus UI + JIRA for permissions)
- Nexus Onboarding Config upload (Action: Upload to Nexus)
- Image registry username and token (Action: Create credentials)
- Configure IAC Pipeline (Action: GitLab CI/CD setup)
- Setup certificates (Ingress, Internal LB, Prometheus, Loki, Alloy, Tempo) (Action: Certificate request system)

**Phase 2: Infrastructure and Pipelines**
- AWS Account Setup Core (Action: CAF automation + JIRA)
- CSM Safe Creation Request (Action: ServiceNow ticket)
- CSM Safe Access request (Action: ServiceNow)
- GitLab Space Creation (Action: GitLab API)
- ECR setup (Command: AWS CLI)
- EKS Capacity Planning (Action: Sizing calculation)
- EKS Cluster provisioning (Command: AWS CLI / CloudFormation)
- RDS setup (Command: AWS CLI + JIRA for DBA team)
- MSK setup (Command: AWS CLI)
- MSK User creation (Action: IAM + MSK config)
- OpenSearch setup (Command: AWS CLI)
- RDS bootstrap Product (Action: Execute script)
- S3 bucket for Archival and BIX (Command: AWS CLI + bucket policy)

**Phase 3: Application Deployment**
- Namespace creation (Command: kubectl)
- Config update (MSK Prefix / DB creation / Schema Creation / IRSA update / Deploy-upgrade update) (Action: Multiple config files)
- IRSA for Opensearch Access (Command: eksctl + IAM)
- SRS Deployment (Command: Helm chart)
- IRSA Cert Role creation (Command: eksctl)
- Pega Deployment (Command: Helm chart)
- Ingress/ALB Creation (Command: kubectl + AWS ALB controller)
- Oracle DB user for DMS Migrations (Action: JIRA to DBA team + SQL script)

**Phase 4: Data Migration**
- DMS Replication Instance Product Provisioning (Command: AWS CLI)
- DMS fullload and CDC product Provisioning (Command: AWS CLI)
- Schema permission CR (Action: JIRA to DBA)
- DMS Endpoint Creation for source and Destination (Command: AWS CLI)
- Installer Script run (Command: Python script)
- Python Script Execution (Command: Execute migration script)
- DMS Assessment Report (Command: AWS DMS assessment)
- DMS full load run (Command: Start DMS task)
- DMS full load report generation and validation (Command: Query DMS + validation)
- DMS CDC Run - Combine with Full Load (Command: AWS DMS)
- Performance Monitoring of RDS (Action: CloudWatch dashboard)
- Patch download (Action: Download from vendor portal)

**Phase 5: Upgrade**
- Steps to follow Hazelcast disabling (Command: Config change)
- Deploy new config by disabling Hazelcast from config-pega (Command: kubectl apply)
- Redeploy Pega After Upgrade (Command: Helm upgrade)
- Prometheus SC product for EC2 Provisioning (Command: CloudFormation)
- Prometheus Cloudwatch related configuration Pipeline (Action: GitLab pipeline)
- Prometheus Cloudwatch related configuration (X) (Action: Config file)
- EKS Cluster APP Prequesties (S3/IAM/SG) (Command: AWS CLI)
- EKS Cluster PreReq SC - Reusing APP EKS Pre (Action: Reuse existing)
- EKS Cluster SC (Command: CloudFormation)
- Helm charts Pipeline Publish COMmon Pipeline for publishing (Action: GitLab pipeline)
- Helm Charts for Loki (Action: Customize Helm values)
- Helm Charts for Alloy (Action: Customize Helm values)
- Helm Charts for Tempo (Action: Customize Helm values)

**Phase 6: Logging and Monitoring**
- Config pipeline for Loki/Tempo/Alloy = X (Action: GitLab pipeline)
- Grafana Dashboard Creation - Through config pipelineX (Action: Import dashboards)
- AlertsX (Action: Configure alert rules)
- Update JVM options for OtelX (Command: Update deployment)
- EKS monitoring (Action: CloudWatch + Prometheus)
- MSK Monitoring (Action: CloudWatch)
- OpenSearch Monitoring (Action: CloudWatch)
- RDS Monitoring (Action: CloudWatch + Performance Insights)
- Scaling and right sizing of EKS (Action: Review metrics + adjust)

**Phase 7: Performance**
- Scaling and right sizing of EKS - PODS (Command: HPA configuration)
- Right sizing of MSK (Action: Review + resize)
- Right sizing of OS (Action: Review + resize)
- Right sizing of RDS (Action: Review + resize)
- RDS Databack and restore (Command: AWS RDS backup + restore test)
- KMS key backup (Command: AWS KMS)
- FIS Setup - Role required for IAM accessing it (Command: IAM role)
- FIS Service Role creation (Command: IAM + FIS)
- AZ Cutdown template for Network (Action: Test failover)

**Phase 8: Resiliency**
- Pods go down (Action: Chaos testing)
- Worker node goes down (Action: Terminate node test)
- DMS Assessment Report (Command: Review assessment)
- OpenSearch resilience test (Action: AZ failure test)
- MSK resilience test (Action: Broker failure test)
- RDS resilience test (Action: Failover test)
- EKS resilience test (Action: Control plane test)
- RBAC Role For EKS (Command: kubectl create role)
- Network Policy for NS (Command: kubectl apply network policy)

**Phase 9: Security**
- RDS Backup Service to be enabled (Command: Enable automated backups)
- Cyber Resiliency checks (Action: Security scan + compliance)

### DATABASE SCHEMA REQUIREMENTS

**1. PROJECTS TABLE**
Store: id, project_name, environment, team_name, team_email, jira_ticket, aws_account_id, gitlab_group_url, status, created_at, updated_at, created_by

**2. PHASES TABLE**
Store: id, project_id, phase_number, phase_name, status, started_at, completed_at, completed_by, estimated_hours, actual_hours

**3. TASKS TABLE**
Store: id, phase_id, task_order, task_name, task_description, task_type, commands, action_type, action_url, prerequisites, outputs, status, estimated_minutes, completed_at, completed_by, notes

**4. TASK_ACTIONS TABLE** (NEW - for multiple action types)
Store: id, task_id, action_type, action_name, action_url_template, action_description, button_label, is_automated

Action types include:
- "jira" - Create JIRA ticket
- "servicenow" - Create ServiceNow request
- "gitlab_api" - GitLab API call
- "aws_cli" - AWS CLI command
- "nexus" - Nexus action
- "cert_request" - Certificate request
- "ad_request" - Active Directory request
- "dba_request" - Database team request
- "manual_step" - Manual UI navigation
- "script_execution" - Run script
- "validation" - Validation check

**5. EXECUTION_LOGS TABLE**
Store: id, task_id, log_entry, output_data, created_by, created_at, log_type

**6. PROJECT_OUTPUTS TABLE** (NEW - store important outputs)
Store: id, project_id, output_key, output_value, phase_number, created_at
Examples: aws_account_id, eks_cluster_name, rds_endpoint, gitlab_group_url, nexus_repo_url

### UI REQUIREMENTS

**1. DASHBOARD PAGE**
- Show metrics: Active projects, Completed this month, Phases in progress, Avg completion time
- Recent activity feed
- Projects by status chart
- Phase completion heatmap

**2. NEW PROJECT PAGE**
- Form with: project_name, environment (dev/uat/prod), team_name, team_email, jira_ticket
- AWS region selector
- Select which phases to execute (checkboxes)
- Resource requirements (EKS nodes, RDS size, etc.)
- Submit button creates project + selected phases

**3. ACTIVE PROJECTS PAGE**
- List all in-progress projects
- Each project shows:
  - Project name, environment, team
  - Progress bar (% complete)
  - Phase status indicators
  - Quick actions (View details, Add notes, Export report)

**4. PROJECT DETAIL PAGE**
- Project header with key info
- Progress timeline visualization
- All phases listed with expand/collapse
- Each phase shows:
  - Tasks with status icons
  - Estimated vs actual time
  - Who completed what when

**5. TASK DETAIL VIEW** (Most important!)
For each task, show:

**Header:**
- Task name and description
- Status badge (Pending/In Progress/Completed)
- Estimated time vs actual time
- Assigned to / Completed by

**Prerequisites Section:**
- List what must be done before this task
- Link to prerequisite tasks
- Show if prerequisites are met

**Action Buttons Section** (Dynamic based on task type):
- If task has commands: [📋 Copy Commands] button
- If task needs JIRA: [🎫 Create JIRA Ticket] button → Opens pre-filled URL
- If task needs ServiceNow: [📝 Create ServiceNow Request] button
- If task needs GitLab: [🦊 Execute in GitLab] button
- If task needs Nexus: [📦 Open Nexus] button
- If task has script: [▶️ Run Script] button (future automation hook)
- Multiple actions possible per task!

**Commands Section** (if applicable):
- Syntax-highlighted code block
- Copy button
- Variables replaced with actual project values

**Execution Section:**
- Text area for execution notes
- File upload for outputs (screenshots, logs, etc.)
- Record output values (e.g., "RDS Endpoint: xxx")
- Save button

**Validation Section:**
- Checklist of validation steps
- Each with checkbox
- Mark complete only when all validated

**Action Buttons:**
- [💾 Save Progress]
- [✅ Mark Complete]
- [🔄 Need Help] → Creates support ticket

**6. OUTPUTS PAGE** (NEW)
- Table showing all key outputs for a project
- Examples:
  - AWS Account ID: 123456789012
  - EKS Cluster: pega-claims-dev
  - RDS Endpoint: xxx.rds.amazonaws.com
  - GitLab Group: https://gitlab.com/pega-claims
  - Nexus Repo: https://nexus.com/pega-claims
- Export button to copy all as YAML/JSON

**7. REPORTS PAGE**
- Project status report (exportable to PDF)
- Time tracking report
- Team performance metrics
- Bottleneck analysis

### TASK CONFIGURATION EXAMPLES

**Example 1: Multi-action task**
```json
{
  "task_name": "Setup Nexus Repository",
  "description": "Configure artifact repository for Pega binaries",
  "estimated_minutes": 30,
  "actions": [
    {
      "action_type": "manual_step",
      "action_name": "Create Repository in Nexus UI",
      "action_url": "https://nexus.company.com/repositories",
      "button_label": "🔗 Open Nexus"
    },
    {
      "action_type": "jira",
      "action_name": "Request Nexus Permissions",
      "action_url_template": "https://jira.company.com/create?project=NEXUS&summary=Access+for+{project_name}",
      "button_label": "🎫 Create JIRA"
    }
  ],
  "outputs": ["nexus_repo_url", "nexus_credentials"],
  "validation": [
    "Repository visible in Nexus",
    "Can upload test artifact",
    "Team members have access"
  ]
}
