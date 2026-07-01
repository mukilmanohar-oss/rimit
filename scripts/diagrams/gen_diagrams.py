"""
Render 4 Mermaid architecture diagrams to PNG via Playwright + mermaid.js CDN.
Output: /home/z/my-project/scripts/diagrams/*.png
"""
import os
import subprocess
import sys

DIAG_DIR = "/home/z/my-project/scripts/diagrams"
os.makedirs(DIAG_DIR, exist_ok=True)

# Mermaid diagram sources (kept compact for clean rendering)
DIAGRAMS = {
    "01_system_context.mmd": r"""
flowchart LR
    classDef actor fill:#f5f5f5,stroke:#888,stroke-width:1.5px,color:#222
    classDef system fill:#e8f1f8,stroke:#1f6c92,stroke-width:2px,color:#131515
    classDef external fill:#fbeee9,stroke:#b85450,stroke-width:2px,color:#222
    classDef idp fill:#fdf6e3,stroke:#d6b656,stroke-width:2px,color:#222

    SA["Super Admin (MD)<br/>RIMIT Leadership"]
    AH["Academic Heads<br/>& Managers"]
    CO["Counselors /<br/>Admission Officers"]
    FO["Finance /<br/>Accounts Officers"]
    SC["Sub-Center Staff<br/>(B2B Partners)"]

    SYS["RIMIT-SPES B2B Aggregator<br/>& Admission Mgmt System<br/>(Django Monolith)"]

    META["Meta Ads<br/>(FB / Instagram<br/>Lead Gen)"]
    WA["WhatsApp<br/>Business API"]
    SMTP["SMTP /<br/>Amazon SES"]
    PAY["Razorpay<br/>Payment Gateway"]
    S3["MinIO / S3<br/>Document Vault"]
    KC["Keycloak<br/>(OIDC / MFA)"]

    SA --> SYS
    AH --> SYS
    CO --> SYS
    FO --> SYS
    SC --> SYS

    META -->|lead webhook| SYS
    SYS -->|notifications| WA
    SYS -->|email| SMTP
    SYS -->|payment| PAY
    SYS -->|docs| S3
    SYS <-->|auth| KC

    class SA,AH,CO,FO,SC actor
    class SYS system
    class META,WA,SMTP,PAY,S3 external
    class KC idp
""",
    "02_container_diagram.mmd": r"""
flowchart TB
    classDef ingress fill:#e8f1f8,stroke:#1f6c92,stroke-width:2px,color:#131515
    classDef app fill:#eef5f9,stroke:#32454e,stroke-width:2px,color:#131515
    classDef data fill:#eaf3ec,stroke:#529067,stroke-width:2px,color:#131515
    classDef queue fill:#f5efe7,stroke:#8c7443,stroke-width:2px,color:#131515
    classDef sec fill:#fdf6e3,stroke:#d6b656,stroke-width:2px,color:#131515

    NGINX["Nginx<br/>Reverse Proxy<br/>SSL / Rate-Limit"]
    subgraph APP["Django 5.x Application (Monolith)"]
        DRF["DRF ViewSets<br/>+ drf-spectacular"]
        SIG["Django Signals<br/>post_save triggers"]
        SER["DRF Serializers<br/>+ Validation"]
        RLS["RLS Middleware<br/>Sets tenant context"]
    end
    CELERY["Celery Workers<br/>Async tasks"]
    BEAT["Celery Beat<br/>Scheduled jobs"]
    REDIS["Redis<br/>Broker + Cache"]
    PG["PostgreSQL 16<br/>RLS + GIN tsvector<br/>+ JSONB"]
    KC["Keycloak<br/>OIDC / OAuth2"]
    MINIO["MinIO / S3<br/>Encrypted at rest"]

    NGINX --> DRF
    DRF --> SER
    SER --> RLS
    RLS --> PG
    DRF --> SIG
    SIG --> CELERY
    CELERY --> REDIS
    BEAT --> REDIS
    CELERY --> PG
    CELERY --> MINIO
    DRF <-->|JWT verify| KC
    DRF -->|presigned URLs| MINIO

    class NGINX ingress
    class DRF,SIG,SER,RLS,CELERY,BEAT app
    class PG,REDIS,MINIO data
    class KC sec
""",
    "03_deployment_topology.mmd": r"""
flowchart TB
    classDef public fill:#e8f1f8,stroke:#1f6c92,stroke-width:2px,color:#131515
    classDef private fill:#eaf3ec,stroke:#529067,stroke-width:2px,color:#131515
    classDef isolated fill:#fdf6e3,stroke:#d6b656,stroke-width:2px,color:#131515
    classDef external fill:#fbeee9,stroke:#b85450,stroke-width:2px,color:#222

    CDN["Cloudflare CDN<br/>DNS + DDoS"]

    subgraph VPC["VPC 10.0.0.0/16"]
        subgraph PUB1["Public Subnet AZ-1"]
            ALB["ALB<br/>HTTPS :443"]
            NG1["Nginx<br/>ECS Fargate"]
        end
        subgraph PUB2["Public Subnet AZ-2"]
            NG2["Nginx<br/>(standby)"]
        end
        subgraph PRIV1["Private Subnet AZ-1"]
            APP1["Django App<br/>ECS Fargate x2"]
            CEL1["Celery Worker<br/>ECS Fargate x2"]
            BEAT1["Celery Beat<br/>Fargate x1"]
        end
        subgraph PRIV2["Private Subnet AZ-2"]
            APP2["Django App<br/>(standby)"]
            CEL2["Celery Worker<br/>(standby)"]
        end
        subgraph DATA["Isolated Data Subnet"]
            RDS["RDS PostgreSQL 16<br/>Multi-AZ<br/>+ Read Replica"]
            REDIS["ElastiCache Redis<br/>Multi-AZ"]
            KC["Keycloak on ECS<br/>+ RDS schema"]
            MINIO["MinIO Cluster<br/>3 nodes / AZ-distributed"]
        end
    end

    S3["S3 Backup Bucket<br/>WAL archives + dumps"]

    CDN --> ALB
    ALB --> NG1
    ALB --> NG2
    NG1 --> APP1
    NG2 --> APP2
    APP1 --> RDS
    APP2 --> RDS
    APP1 --> REDIS
    APP1 --> KC
    APP1 --> MINIO
    CEL1 --> REDIS
    CEL1 --> RDS
    CEL1 --> MINIO
    BEAT1 --> REDIS
    RDS -->|WAL every 15min| S3

    class CDN external
    class ALB,NG1,NG2 public
    class APP1,APP2,CEL1,CEL2,BEAT1 private
    class RDS,REDIS,KC,MINIO isolated
    class S3 external
""",
    "04_enrollment_sequence.mmd": r"""
sequenceDiagram
    autonumber
    participant SC as Sub-Center Staff
    participant API as Django DRF
    participant RLS as RLS Middleware
    participant DB as PostgreSQL
    participant SIG as Django Signal
    participant Q as Celery Queue
    participant WA as WhatsApp API
    participant PAY as Razorpay

    SC->>API: POST /api/v1/enrollments/<br/>{student_id, course_id, session_id}
    API->>API: DRF Serializer<br/>validates payload
    API->>API: Session Enforcement Matrix<br/>rule check (e.g. fresh candidate<br/>cannot enroll in July session)
    alt Rule Violated
        API-->>SC: 400 Rejected + suggests<br/>valid October session
    else Rule Passed
        API->>RLS: SET app.current_sub_center_id
        RLS->>DB: INSERT enrollments<br/>(RLS enforces tenant)
        DB-->>API: enrollment_id
        API->>SIG: post_save trigger
        SIG->>Q: enqueue notify + payment_link
        API-->>SC: 201 Created {enrollment_id,<br/>status:"Applied"}
        Q->>PAY: create payment link
        PAY-->>Q: payment_url
        Q->>WA: send "Fee Pending"<br/>template to student
        WA-->>Q: message_id
        Q->>DB: UPDATE enrollments<br/>SET status="Fee Link Sent"
    end
""",
}


def render_one(mmd_path: str, png_path: str):
    """Render a single .mmd file to PNG via Playwright + mermaid.ink-style local rendering."""
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  html, body {{ margin: 0; padding: 0; background: #ffffff; }}
  #target {{ padding: 24px; }}
  svg {{ max-width: 100%; height: auto; }}
</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
</head>
<body>
<div id="target" class="mermaid">{open(mmd_path, encoding='utf-8').read()}</div>
<script>
  mermaid.initialize({{ startOnLoad: true, theme: 'base', securityLevel: 'loose',
    themeVariables: {{
      primaryColor: '#e8f1f8',
      primaryTextColor: '#131515',
      primaryBorderColor: '#1f6c92',
      lineColor: '#32454e',
      secondaryColor: '#eaf3ec',
      tertiaryColor: '#fdf6e3',
      fontFamily: 'Helvetica, Arial, sans-serif',
      fontSize: '14px'
    }}
  }});
</script>
</body></html>"""
    html_path = png_path.replace(".png", ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Use Playwright to render the HTML and screenshot the SVG element
    render_script = f"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={{'width': 1600, 'height': 1200}}, device_scale_factor=2)
        await page.goto('file://{html_path}')
        # Wait for mermaid to render
        await page.wait_for_selector('svg', timeout=15000)
        await page.wait_for_timeout(500)
        el = await page.query_selector('#target')
        await el.screenshot(path='{png_path}', omit_background=False)
        await browser.close()

asyncio.run(main())
"""
    subprocess.run([sys.executable, "-c", render_script], check=True)
    print(f"  rendered {png_path}")


def main():
    for fname, content in DIAGRAMS.items():
        mmd_path = os.path.join(DIAG_DIR, fname)
        with open(mmd_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        png_path = mmd_path.replace(".mmd", ".png")
        render_one(mmd_path, png_path)
    print("All diagrams rendered.")


if __name__ == "__main__":
    main()
