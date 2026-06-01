using Microsoft.EntityFrameworkCore;
using ProfileService.Data;
using ProfileService.Models;

namespace ProfileService.Data.SeedData;

/// <summary>
/// Seed ~250 kỹ năng chuyên ngành thực tế vào bảng Skills khi khởi động.
/// Chỉ chạy khi bảng trống (idempotent).
/// </summary>
public static class SkillSeeder
{
    public static async Task SeedAsync(ProfileDbContext db)
    {
        if (await db.Skills.IgnoreQueryFilters().AnyAsync()) return;

        var now = DateTimeOffset.UtcNow;

        // ── Danh sách kỹ năng (tên chuẩn quốc tế dùng trong CV/JD) ───────────
        var skillNames = new[]
        {
            // ── Programming Languages ─────────────────────────────────────────
            "Python", "Java", "C#", "C++", "C", "JavaScript", "TypeScript",
            "Go (Golang)", "Rust", "Swift", "Kotlin", "PHP", "Ruby", "Scala",
            "R", "MATLAB", "Dart", "Lua", "Perl", "Elixir", "Haskell",
            "Objective-C", "Assembly", "COBOL", "Groovy", "F#",

            // ── Frontend / Web UI ─────────────────────────────────────────────
            "React", "Vue.js", "Angular", "Next.js", "Nuxt.js", "Svelte",
            "SvelteKit", "HTML5", "CSS3", "Sass / SCSS", "Less",
            "Tailwind CSS", "Bootstrap", "Material UI", "Ant Design",
            "jQuery", "Redux", "Zustand", "MobX", "Pinia", "Vuex",
            "Webpack", "Vite", "Rollup", "Babel", "ESLint", "Prettier",
            "WebAssembly", "Three.js", "D3.js", "Chart.js", "Storybook",
            "Micro Frontend", "Progressive Web App (PWA)",

            // ── Backend / API ─────────────────────────────────────────────────
            "Node.js", "Express.js", "NestJS", "Fastify",
            "Spring Boot", "Spring MVC", "Spring Security", "Hibernate",
            "ASP.NET Core", "Entity Framework Core", "SignalR",
            "Django", "Flask", "FastAPI", "SQLAlchemy",
            "Laravel", "Symfony", "CodeIgniter",
            "Ruby on Rails", "Sinatra",
            "Gin (Go)", "Echo (Go)", "Fiber (Go)",
            "Ktor", "Micronaut",
            "GraphQL", "REST API", "gRPC", "WebSocket", "SOAP",
            "OpenAPI / Swagger",

            // ── Mobile Development ────────────────────────────────────────────
            "Android (Native)", "iOS (Native)", "React Native", "Flutter",
            "SwiftUI", "Jetpack Compose", "Xamarin", "Ionic",
            "Expo", "Capacitor",

            // ── Database ──────────────────────────────────────────────────────
            "PostgreSQL", "MySQL", "Microsoft SQL Server", "SQLite",
            "MariaDB", "Oracle Database",
            "MongoDB", "Redis", "Elasticsearch", "Apache Cassandra",
            "DynamoDB", "Firebase Firestore", "CouchDB", "Neo4j",
            "InfluxDB", "TimescaleDB",
            "SQL", "PL/SQL", "T-SQL", "NoSQL",
            "Database Design", "Query Optimization", "Indexing",

            // ── Cloud & Infrastructure ────────────────────────────────────────
            "Amazon Web Services (AWS)", "Microsoft Azure",
            "Google Cloud Platform (GCP)", "Oracle Cloud",
            "AWS EC2", "AWS S3", "AWS Lambda", "AWS RDS",
            "AWS EKS", "AWS CloudFormation",
            "Azure Functions", "Azure DevOps", "Azure Kubernetes Service",
            "Google BigQuery", "Google Cloud Run",
            "Cloudflare", "Vercel", "Netlify", "Heroku",

            // ── DevOps / CI-CD ────────────────────────────────────────────────
            "Docker", "Kubernetes", "Helm", "Istio",
            "Terraform", "Ansible", "Puppet", "Chef",
            "Jenkins", "GitHub Actions", "GitLab CI/CD",
            "CircleCI", "ArgoCD", "Tekton",
            "Prometheus", "Grafana", "Datadog", "New Relic",
            "ELK Stack (Elasticsearch, Logstash, Kibana)",
            "Linux / Unix", "Bash / Shell Scripting",
            "Nginx", "Apache HTTP Server", "HAProxy",
            "Infrastructure as Code (IaC)",
            "Site Reliability Engineering (SRE)",

            // ── Data & AI / ML ────────────────────────────────────────────────
            "Machine Learning", "Deep Learning", "Natural Language Processing (NLP)",
            "Computer Vision", "Generative AI", "Large Language Model (LLM)",
            "TensorFlow", "PyTorch", "Keras", "Scikit-learn",
            "Hugging Face Transformers", "LangChain", "OpenAI API",
            "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly",
            "Apache Spark", "Hadoop", "Hive", "Kafka",
            "Apache Airflow", "dbt (Data Build Tool)",
            "Data Warehouse", "Data Lake", "ETL / ELT",
            "Power BI", "Tableau", "Looker Studio", "Metabase",
            "Data Analysis", "Statistical Analysis", "A/B Testing",
            "Reinforcement Learning", "Recommendation System",
            "Time Series Analysis",

            // ── Architecture & Design Patterns ────────────────────────────────
            "Microservices Architecture", "Monolithic Architecture",
            "Event-Driven Architecture", "CQRS", "Event Sourcing",
            "Domain-Driven Design (DDD)", "Clean Architecture",
            "Hexagonal Architecture", "SOLID Principles",
            "Design Patterns (GoF)", "API Gateway", "Service Mesh",
            "Message Queue", "Apache Kafka", "RabbitMQ", "NATS",
            "Serverless Architecture", "BFF (Backend for Frontend)",

            // ── Security ──────────────────────────────────────────────────────
            "Application Security", "Network Security", "Cloud Security",
            "Penetration Testing", "Ethical Hacking",
            "OAuth 2.0", "OpenID Connect", "JWT", "SAML",
            "SSL/TLS", "OWASP Top 10", "SAST / DAST",
            "Vulnerability Assessment", "SOC / SIEM",
            "Zero Trust Security",

            // ── Testing & QA ──────────────────────────────────────────────────
            "Unit Testing", "Integration Testing", "End-to-End Testing",
            "Test-Driven Development (TDD)", "Behavior-Driven Development (BDD)",
            "Jest", "Vitest", "Cypress", "Playwright", "Selenium",
            "JUnit", "NUnit", "xUnit", "PyTest",
            "Postman", "k6", "JMeter", "Gatling",
            "SonarQube", "Code Review",

            // ── Project Management & Soft Skills ──────────────────────────────
            "Agile / Scrum", "Kanban", "SAFe", "Waterfall",
            "JIRA", "Confluence", "Notion", "Trello", "Linear",
            "Technical Documentation", "System Design",
            "Problem Solving", "Critical Thinking",
            "Team Leadership", "Mentoring", "Communication",
            "Presentation Skills",

            // ── Tools & Platforms ─────────────────────────────────────────────
            "Git", "GitHub", "GitLab", "Bitbucket",
            "VS Code", "IntelliJ IDEA", "PyCharm", "Eclipse",
            "Vim / Neovim",
            "Figma", "Adobe XD", "Sketch",
            "UI/UX Design", "Responsive Design", "Accessibility (a11y)",
            "Jira", "Slack", "Miro",
            "MinIO", "Keycloak",

            // ── Blockchain & Web3 ─────────────────────────────────────────────
            "Blockchain", "Smart Contract", "Solidity", "Ethereum",
            "Web3.js", "Hardhat", "NFT Development",

            // ── Embedded & IoT ────────────────────────────────────────────────
            "Embedded Systems", "IoT", "Arduino", "Raspberry Pi",
            "RTOS", "FPGA", "Firmware Development",

            // ── Networking ────────────────────────────────────────────────────
            "TCP/IP", "HTTP/HTTPS", "DNS", "Load Balancing", "CDN",
            "VPN", "Firewall", "Network Monitoring",

            // ── ERP / SAP ─────────────────────────────────────────────────────
            "SAP ERP", "SAP S/4HANA", "SAP ABAP",
            "Microsoft Dynamics 365", "Odoo",

            // ── Business Analysis ─────────────────────────────────────────────
            "Business Analysis", "Requirements Gathering",
            "Process Modeling (BPMN)", "User Story Mapping",
        };

        var skills = skillNames
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .Select(name => new Skill
            {
                Id          = CreateDeterministicGuid(name),
                Name        = name.Trim(),
                CreatedDate = now,
                CreatedBy   = "system",
                IsDeleted   = false,
            })
            .ToList();

        await db.Skills.AddRangeAsync(skills);
        await db.SaveChangesAsync();
    }

    private static Guid CreateDeterministicGuid(string input)
    {
        using (var md5 = System.Security.Cryptography.MD5.Create())
        {
            byte[] hash = md5.ComputeHash(System.Text.Encoding.UTF8.GetBytes(input.Trim().ToLowerInvariant()));
            return new Guid(hash);
        }
    }
}
