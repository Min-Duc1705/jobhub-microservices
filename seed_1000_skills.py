import psycopg2
import uuid
import sys
from datetime import datetime, timezone

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=== SEEDING 1000+ TECH & PROFESSIONAL SKILLS ===")
    
    # Connect to JobService DB
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="JobService",
            user="postgres",
            password="root"
        )
        cur = conn.cursor()
    except Exception as e:
        print(f"❌ Lỗi kết nối JobService DB: {e}")
        sys.exit(1)
        
    # Query existing skills in DB (case-insensitive check)
    cur.execute('SELECT "Name" FROM "Skills"')
    existing_skills = {r[0].lower().strip() for r in cur.fetchall()}
    print(f"Đang có {len(existing_skills)} kỹ năng trong database.")
    
    # 1,130 Unique IT & Professional Skills
    skills_to_seed = [
        # 1. Programming Languages (80)
        "JavaScript", "TypeScript", "Python", "Java", "C#", "C++", "C", "Go (Golang)", "Rust", "PHP",
        "Ruby", "Swift", "Kotlin", "Scala", "Dart", "R", "Objective-C", "Shell", "Bash", "PowerShell",
        "Perl", "Haskell", "Julia", "Lua", "Groovy", "Clojure", "Erlang", "Elixir", "F#",
        "Fortran", "Cobol", "ABAP", "Apex", "Solidity", "Vyper", "Lisp", "Scheme", "Prolog", "VHDL",
        "Verilog", "Delphi", "Pascal", "PL/SQL", "Transact-SQL", "ActionScript", "Ada", "ColdFusion", "D", "Eiffel",
        "Forth", "Hack", "Icon", "IDL", "LabVIEW", "Logo", "ML", "Nim", "PostScript", "Racket",
        "SAS", "SPARQL", "Tcl", "VBScript", "XQuery", "YAML", "XML", "JSON", "Markdown", "LaTeX",
        "HTML5", "CSS3", "SASS", "SCSS", "LESS", "Stylus", "PostCSS", "WebAssembly", "C/C++", "C/C++ Assembly",

        # 2. Frontend Frameworks & Libraries (100)
        "React", "Vue.js", "Angular", "Next.js", "Nuxt.js", "Gatsby", "Svelte", "SolidJS", "Remix", "Preact",
        "Alpine.js", "Lit", "Ember.js", "Backbone.js", "jQuery", "Redux", "Zustand", "MobX", "Recoil", "Pinia",
        "Vuex", "NgRx", "RxJS", "Axios", "Lodash", "Underscore.js", "Ramda", "D3.js", "Chart.js", "Three.js",
        "Babylon.js", "WebGL", "Canvas API", "SvelteKit", "Astro", "Qwik", "Stencil", "Riot.js", "Knockout.js", "Polymer",
        "React Router", "Vue Router", "Angular Router", "Redux Toolkit", "Redux-Saga", "Redux-Observable", "Vuex ORM", "XState", "Formik", "React Hook Form",
        "Yup", "Zod", "Joi", "Superstruct", "Valibot", "Apollo Client", "Relay", "URQL", "GraphQL Request", "React Query",
        "SWR", "RTK Query", "Immutable.js", "Mantine", "Shadcn UI", "Radix UI", "Headless UI", "Ariakit", "Reakit", "Chakra UI",
        "Tailwind CSS", "Bootstrap", "Material UI", "Ant Design", "Bulma", "Foundation", "Semantic UI", "DaisyUI", "Flowbite", "Preline UI",
        "Styled Components", "Emotion", "Linaria", "Vanilla Extract", "TailwindCSS", "CSS Modules", "BEM", "OOCSS", "SMACSS", "CSS-in-JS",
        "Framer Motion", "GreenSock (GSAP)", "Anime.js", "Velocity.js", "Popmotion", "Web Animations API", "Lottie", "Rive", "SVG", "HTML",

        # 3. Backend Frameworks & Runtimes (100)
        "Node.js", "Express.js", "NestJS", "Fastify", "Koa", "Hapi", "Sails.js", "LoopBack", "AdonisJS", "Strapi",
        "Spring Boot", "Spring Cloud", "Spring Security", "Spring Data", "Spring MVC", "Struts", "Hibernate", "MyBatis", "Play Framework", "Grails",
        "Django", "Flask", "FastAPI", "Tornado", "Web2py", "Bottle", "CherryPy", "Sanic", "Celery", "SQLAlchemy",
        "ASP.NET Core", "ASP.NET MVC", "ASP.NET Web API", "Entity Framework Core", "Dapper", "SignalR", "Nancy", "ServiceStack", "WCF", "SharePoint",
        "Laravel", "Symfony", "Yii", "CodeIgniter", "CakePHP", "Zend Framework", "Phalcon", "Slim", "Lumen", "Drupal",
        "Ruby on Rails", "Sinatra", "Hanami", "Padrino", "Cuba", "Roda", "Grape", "Jekyll", "Hugo", "GatsbyJS",
        "Gin", "Fiber", "Echo", "Beego", "Revel", "Martini", "Buffalo", "Go-kit", "Chi", "Gorilla Mux",
        "Phoenix", "Nerves", "Erlang OTP", "Akka", "Lagom", "Micronaut", "Quarkus", "Helidon", "Vert.x", "Ktor",
        "Django REST Framework", "Flask-RESTful", "Pyramid", "Masonite", "Falcon", "Web.py", "Gunicorn", "Uvicorn", "ASGI", "WSGI",
        "Fastify CLI", "NestJS CLI", "Koa Router", "Sequelize", "Prisma", "TypeORM", "Mongoose", "Bookshelf.js", "Knex.js", "Waterline",

        # 4. Databases & Caching (80)
        "PostgreSQL", "MySQL", "MariaDB", "SQLite", "Microsoft SQL Server", "Oracle Database", "IBM DB2", "Firebird", "Sybase", "Informix",
        "MongoDB", "Cassandra", "DynamoDB", "CouchDB", "Couchbase", "HBase", "RethinkDB", "RavenDB", "ScyllaDB", "Accumulo",
        "Redis", "Memcached", "Elasticsearch", "Solr", "Meilisearch", "Algolia", "Sphinx", "OpenSearch", "Kendra", "Typesense",
        "Neo4j", "ArangoDB", "OrientDB", "GraphDB", "Dgraph", "JanusGraph", "TigerGraph", "AnzoGraph", "Blazegraph", "Neptune",
        "ClickHouse", "InfluxDB", "TimescaleDB", "Prometheus", "Cortex", "Thanos", "VictoriaMetrics", "QuestDB", "Druid", "Pinot",
        "Firebase Realtime Database", "Cloud Firestore", "Supabase", "PocketBase", "Appwrite", "Realm", "ObjectBox", "SQL", "NoSQL", "NewSQL",
        "CockroachDB", "Spanner", "TiDB", "YugabyteDB", "SingleStore", "VoltDB", "HStore", "JSONB", "PL/pgSQL", "T-SQL",
        "PgAdmin", "DBeaver", "DataGrip", "Robo 3T", "MongoDB Compass", "Redis Commander", "Sequel Pro", "TablePlus", "HeidiSQL", "MySQL Workbench",

        # 5. Cloud Platforms & DevOps Tools (100)
        "Amazon Web Services (AWS)", "Microsoft Azure", "Google Cloud Platform (GCP)", "Oracle Cloud Infrastructure (OCI)", "DigitalOcean", "Heroku", "Vercel", "Netlify", "Render", "Cloudflare",
        "AWS EC2", "AWS S3", "AWS Lambda", "AWS RDS", "AWS ECS", "AWS EKS", "AWS DynamoDB", "AWS IAM", "AWS CloudFormation", "AWS CloudWatch",
        "Azure DevOps", "Azure Virtual Machines", "Azure SQL Database", "Azure App Service", "Azure Functions", "Azure Kubernetes Service (AKS)", "Azure Blob Storage", "Azure Active Directory", "Azure Key Vault", "Azure Monitor",
        "GCP Compute Engine", "GCP Cloud Storage", "GCP Cloud Run", "GCP Cloud Functions", "GCP Google Kubernetes Engine (GKE)", "GCP BigQuery", "GCP Cloud SQL", "GCP IAM", "GCP Pub/Sub", "GCP Stackdriver",
        "Docker", "Docker Compose", "Docker Swarm", "Kubernetes", "Helm", "Kustomize", "Rancher", "OpenShift", "Minikube", "Kind",
        "Terraform", "Ansible", "Chef", "Puppet", "SaltStack", "Vagrant", "Packer", "Cloud-init", "Pulumi", "Crossplane",
        "Jenkins", "GitLab CI/CD", "GitHub Actions", "CircleCI", "Travis CI", "Bamboo", "Bitbucket Pipelines", "ArgoCD", "FluxCD", "Tekton",
        "Prometheus Operator", "Grafana", "Kibana", "Logstash", "Fluentd", "Fluent Bit", "Jaeger", "Zipkin", "OpenTelemetry", "Datadog",
        "Dynatrace", "New Relic", "Splunk", "AppDynamics", "Sentry", "Rollbar", "Loggly", "Sumo Logic", "Graylog", "ELK Stack",
        "HashiCorp Vault", "HashiCorp Consul", "HashiCorp Nomad", "HashiCorp Consul", "Linkerd", "Istio", "Consul Connect", "Kuma", "Traefik Mesh", "Nginx Service Mesh",

        # 6. Systems, Servers & Networking (60)
        "Linux", "Ubuntu", "Debian", "CentOS", "RedHat Enterprise Linux (RHEL)", "Fedora", "Alpine Linux", "Arch Linux", "SUSE Linux", "Rocky Linux",
        "Windows Server", "macOS", "Unix", "FreeBSD", "OpenBSD", "NetBSD", "Solaris", "AIX", "HP-UX", "CentOS Stream",
        "Nginx", "Apache HTTP Server", "HAProxy", "Envoy", "Traefik", "Caddy", "IIS (Internet Information Services)", "Squid", "Varnish Cache", "Lighttpd",
        "DNS", "DHCP", "SSH", "SFTP", "FTP", "NFS", "Samba", "LDAP", "Active Directory", "Kerberos",
        "TCP/IP", "UDP", "HTTP/2", "HTTP/3", "WebSocket", "gRPC", "WebRTC", "TLS/SSL", "HTTPS", "IPv6",
        "VPN", "OpenVPN", "WireGuard", "IPsec", "VLAN", "Routing", "Switching", "Load Balancing", "Firewall", "WAF (Web Application Firewall)",

        # 7. Testing & Quality Assurance (60)
        "Testing", "Unit Testing", "Integration Testing", "Functional Testing", "System Testing", "Acceptance Testing", "Regression Testing", "Performance Testing", "Load Testing", "Stress Testing",
        "JUnit", "TestNG", "Mockito", "PowerMock", "AssertJ", "Hamcrest", "JUnit5", "Mockito-Kotlin", "Spock Framework", "Robolectric",
        "PyTest", "Unittest", "Nose2", "Tox", "Behave", "Robot Framework", "Doctest", "Mocks", "Stubs", "Fakes",
        "NUnit", "xUnit", "MSTest", "Moq", "AutoFixture", "FluentAssertions", "SpecFlow", "WireMock", "NSubstitute", "FakeItEasy",
        "Jest", "Mocha", "Jasmine", "Vitest", "Cypress", "Selenium", "Playwright", "Puppeteer", "Nightwatch.js", "WebdriverIO",
        "Appium", "Espresso", "XCTest", "Detox", "Calabash", "Cucumber", "Postman", "Newman", "SoapUI", "JMeter",

        # 8. Machine Learning, AI & Data Science (80)
        "Machine Learning", "Deep Learning", "Artificial Intelligence (AI)", "Natural Language Processing (NLP)", "Computer Vision", "Generative AI", "Reinforcement Learning", "Supervised Learning", "Unsupervised Learning", "Transfer Learning",
        "TensorFlow", "Keras", "PyTorch", "Scikit-Learn", "XGBoost", "LightGBM", "CatBoost", "Fast.ai", "Caffe", "MXNet",
        "OpenCV", "NLTK", "SpaCy", "Hugging Face Transformers", "LangChain", "LlamaIndex", "OpenAI API", "Anthropic Claude API", "Google Gemini API", "Cohere API",
        "Vector Databases", "Pinecone", "Milvus", "ChromaDB", "Qdrant", "Faiss", "Weaviate", "Vald", "Milvus Lite", "LanceDB",
        "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "Plotly", "Bokeh", "Statsmodels", "Scrapy", "BeautifulSoup",
        "Hadoop", "Apache Spark", "Apache Hive", "Apache Pig", "Apache Flink", "Apache Storm", "MapReduce", "YARN", "Zookeeper", "Oozie",
        "Airflow", "Prefect", "Luigi", "dbt (data build tool)", "Kafka", "RabbitMQ", "ActiveMQ", "Pulsar", "Flink SQL", "Spark SQL",
        "Jupyter Notebook", "Google Colab", "Anaconda", "MLflow", "Kubeflow", "DVC (Data Version Control)", "TensorBoard", "Weights & Biases", "Neptune.ai", "Sagemaker",

        # 9. Mobile Development (50)
        "Android SDK", "iOS SDK", "SwiftUI", "Jetpack Compose", "React Native", "Flutter", "Xamarin", "Cordova", "Ionic", "NativeScript",
        "Android Studio", "Xcode", "Gradle", "CocoaPods", "Swift Package Manager", "Fastlane", "Firebase Crashlytics", "App Center", "TestFlight", "Google Play Console",
        "Apple Developer Portal", "Kotlin Multiplatform Mobile (KMM)", "Objective-C", "Swift", "Kotlin", "Java (Android)", "Dart (Flutter)", "Expo", "Native Modules", "Hermes Engine",
        "ProGuard", "R8", "Android NDK", "Core Data", "SQLite (Mobile)", "Realm Mobile", "Room Database", "Shared Preferences", "Keychain", "Biometrics Auth",
        "Push Notifications", "APNS (Apple Push Notification service)", "FCM (Firebase Cloud Messaging)", "Deep Linking", "App Store Optimization (ASO)", "Mobile UI Design", "Responsive Layouts", "Camera API", "Geolocation API", "Bluetooth API",

        # 10. Web Technologies & APIs (50)
        "REST API", "GraphQL", "gRPC", "SOAP", "WebSocket", "Webhooks", "JSON-RPC", "XML-RPC", "OData", "Falcon API",
        "Swagger", "OpenAPI", "API Gateway", "Kong Gateway", "Apigee", "AWS API Gateway", "Tyk", "KrakenD", "Zuul", "Spring Cloud Gateway",
        "OAuth 2.0", "OpenID Connect", "SAML", "JWT (JSON Web Tokens)", "Basic Auth", "API Keys", "HMAC", "RBAC (Role-Based Access Control)", "ABAC (Attribute-Based Access Control)", "LDAP Authentication",
        "CORS", "Rate Limiting", "IP Whitelisting", "Throttling", "Caching (API)", "ETags", "Gzip Compression", "Keep-Alive", "DNS Prefetching", "CDN (Content Delivery Network)",
        "Cloudflare CDN", "Akamai", "Fastly", "AWS CloudFront", "Azure CDN", "Keycdn", "RESTful Web Services", "GraphQL Subscriptions", "gRPC-Web", "JSON Schema",

        # 11. Security, Identity & Cryptography (50)
        "Cybersecurity", "Information Security", "Network Security", "Application Security", "Cloud Security", "Cryptography", "Penetration Testing", "Vulnerability Assessment", "Ethical Hacking", "Digital Forensics",
        "OWASP Top 10", "WAF", "DDoS Protection", "IAM (Identity and Access Management)", "Keycloak", "Auth0", "Okta", "Ping Identity", "OneLogin", "Firebase Authentication",
        "HashiCorp Vault", "AWS Secrets Manager", "Azure Key Vault", "GCP Secret Manager", "Symmetric Cryptography", "Asymmetric Cryptography", "AES", "RSA", "ECC", "Diffie-Hellman",
        "Hashing Algorithms", "SHA-256", "MD5", "Bcrypt", "Argon2", "Scrypt", "Digital Signatures", "PKI (Public Key Infrastructure)", "SSL Certificates", "SSH Keys",
        "Multi-Factor Authentication (MFA)", "Two-Factor Authentication (2FA)", "Single Sign-On (SSO)", "Directory Services", "Active Directory Federation Services (ADFS)", "LDAP Over SSL (LDAPS)", "OAuth Authorization Server", "JWT Verification", "Data Encryption at Rest", "Data Encryption in Transit",

        # 12. Software Concepts, Architectures & Methodologies (70)
        "Microservices Architecture", "Monolithic Architecture", "Serverless Architecture", "Event-Driven Architecture", "CQRS (Command Query Responsibility Segregation)", "Event Sourcing", "Domain-Driven Design (DDD)", "Clean Architecture", "Hexagonal Architecture", "SOLID Principles",
        "Design Patterns", "MVC (Model-View-Controller)", "MVVM (Model-View-ViewModel)", "MVP (Model-View-Presenter)", "Object-Oriented Programming (OOP)", "Functional Programming", "Reactive Programming", "Aspect-Oriented Programming (AOP)", "Service-Oriented Architecture (SOA)", "Lambda Architecture",
        "Kappa Architecture", "TDD (Test-Driven Development)", "BDD (Behavior-Driven Development)", "DDD (Domain-Driven Design)", "CI/CD (Continuous Integration/Continuous Deployment)", "Agile Methodology", "Scrum Framework", "Kanban Framework", "DevOps Culture", "DevSecOps",
        "SRE (Site Reliability Engineering)", "Chaos Engineering", "Infrastructure as Code (IaC)", "GitOps", "NoOps", "ChatOps", "Scalability", "High Availability", "Fault Tolerance", "Disaster Recovery",
        "DRY (Don't Repeat Yourself)", "KISS (Keep It Simple, Stupid)", "YAGNI (You Aren't Gonna Need It)", "Clean Code", "Refactoring", "Code Review", "Pair Programming", "Mob Programming", "Trunk-Based Development", "Git Flow",
        "GitHub Flow", "Semantic Versioning (SemVer)", "Monorepo", "Polyrepo", "Micro Frontends", "Web Performance Optimization", "SEO (Search Engine Optimization)", "Accessibility (a11y)", "Internationalization (i18n)", "Localization (l10n)",
        "Server-Side Rendering (SSR)", "Static Site Generation (SSG)", "Client-Side Rendering (CSR)", "Incremental Static Regeneration (ISR)", "Hydration", "Lazy Loading", "Code Splitting", "Tree Shaking", "Virtual DOM", "Shadow DOM",

        # 13. Project Management, PM Tools & Collaboration (50)
        "Project Management", "Product Management", "Scrum Master", "Product Owner", "Agile Project Management", "Waterfalls Methodology", "Jira", "Confluence", "Trello", "Asana",
        "Monday.com", "Basecamp", "ClickUp", "Notion", "Slack", "Microsoft Teams", "Zoom", "Discord", "Skype", "Google Meet",
        "Git", "GitHub", "GitLab", "Bitbucket", "SVN (Subversion)", "Mercurial", "TFVC (Team Foundation Version Control)", "Gerrit", "Phabricator", "GitKraken",
        "Sourcetree", "TortoiseGit", "Git CLI", "Markdown Documentation", "Sphinx Documentation", "Wiki Documentation", "ReadMe", "API Documentation", "Swagger UI", "Redoc",
        "Slack Integrations", "Microsoft Teams Webhooks", "Zapier", "Make (Integromat)", "IFTTT", "Google Workspace", "Microsoft 365", "Draw.io", "Lucidchart", "Miro Board",

        # 14. ERP, CRM & Business Software (50)
        "SAP ERP", "Salesforce", "Odoo", "Microsoft Dynamics 365", "Oracle ERP", "NetSuite", "HubSpot CRM", "Zoho CRM", "Salesforce Service Cloud", "Salesforce Marketing Cloud",
        "WordPress", "Joomla", "Drupal", "Magento (Adobe Commerce)", "Shopify", "WooCommerce", "BigCommerce", "Squarespace", "Wix", "Webflow",
        "Ghost CMS", "Strapi CMS", "Contentful", "Sanity.io", "Decap CMS", "KeystoneJS", "Directus", "Payload CMS", "Typo3", "Umbraco",
        "ERP implementation", "CRM integration", "Supply Chain Management (SCM)", "Human Capital Management (HCM)", "Warehouse Management System (WMS)", "Enterprise Asset Management (EAM)", "Business Intelligence (BI) Tools", "Financial Management Software", "Accounting Software", "QuickBooks",
        "Xero", "Zoho Books", "Wave Accounting", "Sage ERP", "Epicor", "Infor", "Workday", "Peoplesoft", "Oracle Fusion", "Odoo ERP development",

        # 15. UI/UX Design & Prototyping (50)
        "UI Design", "UX Research", "Wireframing", "Prototyping", "User Testing", "Information Architecture", "Visual Design", "Interaction Design", "Responsive Design", "Mobile UI/UX",
        "Figma", "Adobe XD", "Sketch", "Photoshop", "Illustrator", "InVision", "Zeplin", "Miro", "Balsamiq", "Axure RP", "Principle",
        "Marvel App", "Framer", "Protopie", "LottieFiles", "Design Systems", "UI Kit", "Style Guides", "Typography", "Color Theory", "Grid Systems",
        "User Personas", "User Journey Mapping", "User Flow Diagrams", "Site Maps", "A/B Testing (Design)", "Heuristic Evaluation", "Accessibility Guidelines (WCAG)", "Dark Mode Design", "Micro-interactions", "Design Hand-off",
        "Figma Plugins", "Adobe Creative Cloud", "Sketch App", "Vector Graphics", "Raster Graphics", "Icon Design", "Logo Design", "Brand Identity", "Design Collaboration", "Design Specifications",

        # 16. Hardware, Embedded & IoT (50)
        "C (Embedded)", "C++ (Embedded)", "Assembly Language", "Arduino", "Raspberry Pi", "ESP32", "ESP8266", "FreeRTOS", "RTOS (Real-Time Operating System)", "Firmware Development",
        "MQTT", "CoAP", "Zigbee", "Bluetooth Low Energy (BLE)", "Modbus", "CAN Bus", "I2C", "SPI", "UART", "GPIO",
        "VHDL", "Verilog", "FPGA Development", "Microcontrollers", "ARM Cortex", "PIC Microcontrollers", "AVR Microcontrollers", "Embedded Linux", "Yocto Project", "Device Drivers",
        "IoT Security", "Edge Computing", "Sensors Integration", "Actuators Control", "PCB Design", "Altium Designer", "Eagle PCB", "KiCad", "Hardware Troubleshooting", "Oscilloscope Usage",
        "Logic Analyzer", "Digital Electronics", "Analog Electronics", "Power Management (Hardware)", "Signal Integrity", "RF Engineering", "Wireless Communication", "LoRaWAN", "Cellular IoT", "Zigbee Networking",

        # 17. Professional Skills, Certifications & General (50)
        "AWS Certified Solutions Architect", "AWS Certified Developer", "Azure Solutions Architect Expert", "Google Cloud Certified Professional Cloud Architect", "Project Management Professional (PMP)", "Certified ScrumMaster (CSM)", "Cisco Certified Network Associate (CCNA)", "Cisco Certified Network Professional (CCNP)", "Certified Information Systems Security Professional (CISSP)", "Certified Ethical Hacker (CEH)",
        "ITIL Foundation", "CompTIA Security+", "CompTIA Network+", "CompTIA A+", "Oracle Certified Associate (OCA)", "Oracle Certified Professional (OCP)", "Microsoft Certified: Azure DevOps Engineer Expert", "Google Cloud Certified Professional DevOps Engineer", "Terraform Associate Certification", "Kubernetes Administrator (CKA)",
        "Kubernetes Application Developer (CKAD)", "Kubernetes Security Specialist (CKS)", "Salesforce Certified Administrator", "Salesforce Certified Platform Developer", "ISTQB Foundation Level", "ISTQB Advanced Level", "PMI Agile Certified Practitioner (PMI-ACP)", "Professional Scrum Master (PSM)", "IT Professional", "Software Engineer Certification",
        "English (Professional)", "Japanese (Conversational)", "Japanese (Business)", "Chinese (Conversational)", "Chinese (Business)", "Korean (Conversational)", "Korean (Business)", "Vietnamese (Native)", "French (Conversational)", "German (Conversational)",
        "Technical Writing", "Public Speaking", "Team Leadership", "People Management", "Strategic Planning", "Financial Analysis", "Business Analysis", "Client Relations", "Negotiation", "Problem Solving"
    ]
    
    # Filter unique and non-duplicate skills
    unique_skills_to_seed = []
    seen = set()
    for s in skills_to_seed:
        name_clean = s.strip()
        name_lower = name_clean.lower()
        if name_lower not in existing_skills and name_lower not in seen:
            seen.add(name_lower)
            unique_skills_to_seed.append(name_clean)
            
    print(f"Có {len(unique_skills_to_seed)} kỹ năng mới sẽ được chèn.")
    
    # Bulk insert new skills
    success_count = 0
    now = datetime.now(timezone.utc)
    for s in unique_skills_to_seed:
        skill_id = str(uuid.uuid4())
        try:
            cur.execute('''
                INSERT INTO "Skills" (
                    "Id", "Name", "CreatedDate", "LastModifiedDate", "IsDeleted", "CreatedBy", "LastModifiedBy"
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (skill_id, s, now, now, False, 'SkillSeeder', 'SkillSeeder'))
            conn.commit()
            success_count += 1
        except Exception as e:
            conn.rollback()
            print(f"  [Warning] Lỗi chèn kỹ năng '{s}': {e}")
            
    cur.close()
    conn.close()
    
    print("\n=== KẾT QUẢ SEEDING HOÀN TẤT ===")
    print(f"Tổng số kỹ năng mới được chèn thành công: {success_count}")

if __name__ == "__main__":
    main()
