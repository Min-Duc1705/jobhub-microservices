import os
import sys
import uuid
import random
import datetime
import re
import subprocess
import argparse

# Cấu hình encoding UTF-8 cho console để in tiếng Việt không lỗi trên Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# ─── AUTO-INSTALL REPORTLAB ──────────────────────────────────────────────────
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("[PDF Gen] Thư viện reportlab chưa được cài đặt. Đang tự động cài đặt...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "reportlab"], check=True)
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        print("[PDF Gen] Đã cài đặt reportlab thành công!")
    except Exception as e:
        print(f"[PDF Gen] Không thể tự động cài đặt reportlab. Lỗi: {e}")
        print("[PDF Gen] Vui lòng chạy lệnh sau trên terminal của bạn: pip install reportlab")
        sys.exit(1)

# ─── CONFIGURE FONTS FOR VIETNAMESE ───────────────────────────────────────────
FONT_REGULAR = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

windows_font_dir = r"C:\Windows\Fonts"
font_path = os.path.join(windows_font_dir, "arial.ttf")
font_bold_path = os.path.join(windows_font_dir, "arialbd.ttf")

if os.path.exists(font_path) and os.path.exists(font_bold_path):
    try:
        pdfmetrics.registerFont(TTFont('Arial', font_path))
        pdfmetrics.registerFont(TTFont('Arial-Bold', font_bold_path))
        FONT_REGULAR = 'Arial'
        FONT_BOLD = 'Arial-Bold'
        print("[PDF Gen] Đã đăng ký thành công font Arial hệ thống cho Tiếng Việt.")
    except Exception as e:
        print(f"[PDF Gen] Không thể đăng ký font Arial: {e}. Sử dụng font mặc định.")
else:
    print("[PDF Gen] Cảnh báo: Không tìm thấy font Arial hệ thống. Chữ tiếng Việt có dấu có thể bị lỗi hiển thị.")

# ─── DATA POOLS FOR COMBINATORIAL GENERATION ──────────────────────────────────
FIRST_NAMES = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
MIDDLE_NAMES = ["Văn", "Thị", "Minh", "Đức", "Thành", "Hoàng", "Ngọc", "Thu", "Hải", "Tuấn", "Hữu", "Xuân", "Phương", "Anh", "Quang"]
LAST_NAMES = ["Tuấn", "Hương", "Nam", "Lan", "Hùng", "Mai", "Phong", "Thảo", "Hải", "Vy", "Bình", "Trang", "Đạt", "Linh", "Duy", "Sơn", "Hà", "Quỳnh", "Khoa", "Dũng"]

UNIVERSITIES = [
    "Đại học Bách khoa Hà Nội",
    "Đại học Quốc gia TP.HCM",
    "Đại học Bách khoa TP.HCM",
    "Đại học Công nghệ - ĐHQGHN",
    "Đại học FPT",
    "Đại học Sư phạm Kỹ thuật TP.HCM",
    "Học viện Công nghệ Bưu chính Viễn thông",
    "Đại học Khoa học Tự nhiên - ĐHQG TP.HCM",
    "Đại học Công nghiệp Hà Nội",
    "Đại học Ngoại thương",
    "Đại học Công nghệ Thông tin - ĐHQG TP.HCM",
    "Đại học Khoa học Tự nhiên - ĐHQGHN",
    "Đại học Giao thông Vận tải",
    "Đại học Thủy lợi",
    "Đại học Mở Hà Nội",
    "Học viện Kỹ thuật Quân sự",
    "Học viện Kỹ thuật Mật mã",
    "Đại học Tôn Đức Thắng",
    "Đại học Cần Thơ",
    "Đại học Bách khoa - Đại học Đà Nẵng"
]

COMPANIES = [
    "FPT Software", "Viettel Group", "VNG Corporation", "Tiki Corp", "One Mount Group",
    "NashTech Vietnam", "KMS Technology", "LogiGear", "Sendo", "Shopee Vietnam",
    "Lazada Vietnam", "NAB Innovation Centre Vietnam", "VinGroup", "CMC Global", "DXC Technology"
]

SPECIALTIES = {
    "Backend .NET": {
        "title": ".NET Developer",
        "skills": [
            {"category": "Ngôn ngữ & Cốt lõi", "items": ["C# (Async/Await, LINQ)", "OOP & SOLID Principles", "Design Patterns", "Clean Code & Refactoring"]},
            {"category": "Frameworks & ORM", "items": ["ASP.NET Core Web API / MVC", "Entity Framework Core", "Dapper", "gRPC & SignalR"]},
            {"category": "Hệ thống & Kiến trúc", "items": ["Microservices Architecture", "CQRS (MediatR) & Onion", "RabbitMQ / Kafka (Message Broker)", "RESTful API Design"]}
        ],
        "projects": [
            {"name": "E-Commerce Microservices Platform", "description": "Thiết kế và xây dựng hệ thống backend cho sàn thương mại điện tử quy mô lớn dựa trên kiến trúc Microservices với .NET 8. Sử dụng Ocelot làm API Gateway, RabbitMQ để truyền thông điệp bất đồng bộ giữa các service, và Redis Distributed Cache giúp tăng tốc độ tải dữ liệu sản phẩm. Kết quả giúp hệ thống chịu tải lên tới 10,000 người dùng đồng thời và giảm độ trễ API 40%.", "tags": [".NET 8", "Microservices", "RabbitMQ", "PostgreSQL", "Redis"]},
            {"name": "E-Payment Gateway Integration", "description": "Phát triển và tích hợp cổng thanh toán trực tuyến tập trung kết nối Momo, ZaloPay, VNPAY. Thiết kế cơ chế đảm bảo tính toàn vẹn dữ liệu giao dịch sử dụng Saga Pattern (Orchestration-based), mã hóa dữ liệu nhạy cảm AES-256, áp dụng JWT & OAuth 2.0 để bảo mật API. Hệ thống xử lý trung bình hơn 50,000 giao dịch mỗi ngày với độ chính xác tuyệt đối.", "tags": ["ASP.NET Core", "Saga Pattern", "JWT", "SQL Server"]},
            {"name": "Smart HR Portal Backend", "description": "Xây dựng cổng thông tin quản lý nhân sự tập trung hỗ trợ phân quyền vai trò chuyên sâu (RBAC & ABAC) cho các tập đoàn đa quốc gia. Tối ưu hóa hiệu năng trích xuất báo cáo thống kê nhân sự hàng tháng dạng động (Dynamic Reporting) từ hàng triệu bản ghi, giảm thời gian xử lý từ 2 phút xuống dưới 5 giây thông qua tối ưu hóa truy vấn PostgreSQL và lập chỉ mục (indexing) thông minh.", "tags": ["C#", "EF Core", "PostgreSQL", "Docker", "RBAC"]}
        ],
        "experiences": [
            {"position": "Backend Developer", "bullets": [
                "Thiết kế và phát triển hơn 50 RESTful API hiệu năng cao cho các phân hệ lõi của ứng dụng bằng ASP.NET Core Web API.",
                "Phân tích và tối ưu hóa các câu lệnh LINQ cùng cấu hình Entity Framework Core (Eager vs Lazy loading, Query Splitting), giúp giảm 45% thời gian phản hồi API.",
                "Triển khai hệ thống phân tích lỗi tự động bằng Serilog kết hợp Elasticsearch & Kibana (ELK Stack) giúp giảm 60% thời gian debug của cả đội ngũ phát triển.",
                "Viết hơn 200 kịch bản kiểm thử tự động sử dụng xUnit, Moq và FluentAssertions, nâng tỷ lệ kiểm thử mã nguồn (code coverage) từ 50% lên 85%.",
                "Phối hợp chặt chẽ với đội ngũ Frontend để thiết kế tài liệu API chuẩn hóa sử dụng Swagger/OpenAPI, tăng 25% hiệu suất làm việc nhóm."
            ]},
            {"position": "Senior Backend Engineer", "bullets": [
                "Làm chủ kiến trúc hệ thống, tái cấu trúc mã nguồn cũ sang mô hình Clean Architecture kết hợp với CQRS (MediatR), giúp tăng khả năng mở rộng và dễ bảo trì mã nguồn.",
                "Triển khai cơ chế giao tiếp bất đồng bộ thông qua RabbitMQ, giải quyết triệt để vấn đề nghẽn cổ chai dữ liệu và tăng khả năng chịu tải của hệ thống lên gấp 3 lần.",
                "Thiết kế và tối ưu cấu trúc cơ sở dữ liệu SQL Server chứa hơn 15 triệu bản ghi bằng cách phân vùng bảng (table partitioning) và tối ưu hóa index, cải thiện tốc độ ghi dữ liệu 30%.",
                "Xây dựng và cấu hình tự động hóa toàn bộ luồng tích hợp và triển khai liên tục (CI/CD pipelines) bằng GitHub Actions kết hợp Docker, rút ngắn quy trình deploy từ 30 phút xuống còn 3 phút.",
                "Đóng vai trò Tech Lead dẫn dắt nhóm 4 thành viên, thường xuyên tổ chức review code, định hướng kỹ thuật và đào tạo kỹ năng cho các kỹ sư Junior."
            ]}
        ]
    },
    "Frontend React": {
        "title": "Frontend Engineer (React)",
        "skills": [
            {"category": "Ngôn ngữ & Cốt lội", "items": ["JavaScript (ES6+), TypeScript", "HTML5, CSS3, Sass/SCSS", "Responsive Web Design", "DOM Manipulation & Web APIs"]},
            {"category": "Frameworks & Thư viện", "items": ["ReactJS (Hooks, Context API)", "Next.js (SSR, SSG, ISR)", "Redux Toolkit / Zustand", "React Query / Axios"]},
            {"category": "Styling & UI Components", "items": ["Tailwind CSS", "Bootstrap / Material-UI (MUI)", "Ant Design / Styled-Components", "Framer Motion (Animations)"]}
        ],
        "projects": [
            {"name": "Admin Dashboard Solution", "description": "Phát triển giao diện quản trị doanh nghiệp toàn diện với các biểu đồ phân tích trực quan (Real-time Analytics Charts) bằng React và Chart.js. Tích hợp cơ chế phân quyền người dùng phức tạp (Role-based Menu Rendering), hỗ trợ cấu hình đa ngôn ngữ (i18n) và chế độ Dark/Light Mode. Giao diện tối ưu hóa hiệu năng kết xuất dữ liệu lưới (Data Grid Virtualization) xử lý mượt mà hơn 10,000 dòng dữ liệu.", "tags": ["React", "Redux Toolkit", "Ant Design", "Chart.js"]},
            {"name": "Portfolio & CV Builder App", "description": "Xây dựng ứng dụng Single Page Application (SPA) cho phép người dùng tự thiết kế CV trực tuyến theo thời gian thực. Áp dụng kỹ thuật Drag-and-Drop phức tạp bằng thư viện `@hello-pangea/dnd`, cho phép xuất file PDF chất lượng cao ngay tại client bằng `html2canvas` và `jspdf`. Ứng dụng thu hút hơn 20,000 lượt tạo CV hàng tháng với phản hồi trải nghiệm người dùng rất cao.", "tags": ["ReactJS", "TypeScript", "Tailwind CSS", "html2canvas"]},
            {"name": "Responsive E-Commerce UI", "description": "Tái cấu trúc và phát triển mặt tiền (Storefront) cho trang thương mại điện tử sử dụng Next.js 14 (App Router) giúp cải thiện chỉ số First Contentful Paint (FCP) giảm 50%. Tích hợp giỏ hàng đồng bộ với LocalStorage và Redux Toolkit, thiết kế trải nghiệm thanh toán một trang (One-page checkout) tối ưu, tăng tỷ lệ chuyển đổi đơn hàng thêm 18%.", "tags": ["Next.js", "Tailwind CSS", "TypeScript", "Redux Toolkit"]}
        ],
        "experiences": [
            {"position": "Frontend Developer", "bullets": [
                "Phát triển và đóng gói hơn 30 component dùng chung chất lượng cao (reusable UI components) tuân thủ triệt để nguyên tắc Clean Code.",
                "Tích hợp API RESTful phức tạp và xử lý đồng bộ trạng thái ứng dụng bằng Redux Toolkit và RTK Query, giảm 35% lượng request dư thừa lên server.",
                "Tối ưu hóa hình ảnh, áp dụng lazy-loading, code-splitting giúp nâng điểm hiệu năng Lighthouse từ 60 lên trên 90 điểm.",
                "Phối hợp với UI/UX designers để chuyển đổi các bản thiết kế Figma thành giao diện web pixel-perfect, tương thích hoàn toàn trên tất cả thiết bị di động.",
                "Sử dụng Jest và React Testing Library để viết unit test cho các luồng nghiệp vụ quan trọng (Login, Checkout, Cart), đảm bảo độ ổn định của ứng dụng."
            ]},
            {"position": "Senior Frontend Developer", "bullets": [
                "Dẫn dắt quá trình di chuyển (migration) toàn bộ mã nguồn dự án lớn từ JavaScript sang TypeScript, giúp phát hiện và ngăn chặn hơn 40% lỗi runtime trước khi deploy.",
                "Xây trúc dự án Frontend theo mô hình Monorepo sử dụng Turborepo, tối ưu hóa quy trình build và tiết kiệm 50% thời gian CI/CD.",
                "Thiết kế và triển khai hệ thống design system nội bộ (cá nhân hóa UI component library) giúp đồng bộ giao diện giữa 3 sản phẩm khác nhau của công ty.",
                "Nghiên cứu và áp dụng thành công Server-Side Rendering (SSR) bằng Next.js, đưa từ khóa sản phẩm lên Top 3 kết quả tìm kiếm Google (SEO).",
                "Tổ chức đào tạo kỹ năng chuyên sâu về React cho các thành viên mới, thiết lập quy chuẩn code-style và quy trình review PR nghiêm ngặt."
            ]}
        ]
    },
    "Frontend Vue": {
        "title": "VueJS Developer",
        "skills": [
            {"category": "Ngôn ngữ & Cốt lõi", "items": ["HTML5, CSS3, JavaScript (ES6+)", "TypeScript (Core & Advanced)", "Responsive Web Design", "RESTful API Integration"]},
            {"category": "Framework & State", "items": ["Vue.js (Vue 2 & Vue 3)", "Composition API & Options API", "Pinia / Vuex (State Management)", "Vue Router & Navigation"]},
            {"category": "Hệ sinh thái & Công cụ", "items": ["NuxtJS (SSR & Static Site Generation)", "Vite / Webpack / Babel", "Tailwind CSS / Vuetify / Element Plus", "ESLint / Prettier / Git"]}
        ],
        "projects": [
            {"name": "NuxtJS Video Streaming Platform", "description": "Xây dựng giao diện cho nền tảng xem video trực tuyến tối ưu hóa SEO sử dụng NuxtJS và Tailwind CSS. Triển khai Custom Video Player với các tính năng tăng tốc độ phát, lazy load ảnh thumbnail, và lưu lịch sử xem video. Điểm số Lighthouse SEO đạt tối đa 100 điểm và tăng trải nghiệm người dùng đáng kể.", "tags": ["NuxtJS", "Vue 3", "Tailwind CSS", "SEO", "Vite"]},
            {"name": "Enterprise ERP Admin Portal", "description": "Phát triển phân hệ dashboard quản trị tài nguyên doanh nghiệp ERP sử dụng Vue 3, Pinia và Element Plus. Thiết kế cấu trúc các biểu đồ phân tích dữ liệu động, bộ lọc tìm kiếm nâng cao đa tiêu chí, và tính năng phân quyền hiển thị menu (RBAC) mượt mà.", "tags": ["Vue 3", "Pinia", "Element Plus", "REST API", "Git"]}
        ],
        "experiences": [
            {"position": "VueJS Developer", "bullets": [
                "Phát triển các màn hình giao diện người dùng đáp ứng (Responsive UI) cho hệ thống thương mại điện tử bằng Vue 3.",
                "Tích hợp API và quản lý state tập trung cho toàn bộ luồng thanh toán sử dụng Pinia, giúp giảm 30% lỗi đồng bộ dữ liệu.",
                "Tối ưu hóa thời gian tải trang bằng cách áp dụng các kỹ thuật lazy-loading component và tối ưu hóa dung lượng hình ảnh.",
                "Viết các kịch bản kiểm thử giao diện sử dụng Jest và Vue Test Utils để đảm bảo chất lượng các component cốt lõi.",
                "Làm việc với đội UI/UX để tinh chỉnh giao diện pixel-perfect theo đúng bản thiết kế Figma."
            ]},
            {"position": "Senior VueJS Specialist", "bullets": [
                "Dẫn dắt kiến trúc và chuyển đổi mã nguồn dự án ERP cũ từ Vue 2 sang Vue 3 Composition API, cải thiện tốc độ render 35%.",
                "Thiết kế thư viện UI components dùng chung (Design System) đóng gói qua NPM giúp đồng bộ giao diện cho 3 dự án độc lập.",
                "Triển khai giải pháp Server-Side Rendering (SSR) với NuxtJS giúp tăng 40% lượng truy cập tự nhiên qua công cụ tìm kiếm Google.",
                "Cấu hình hệ thống CI/CD cho frontend bằng GitLab CI kết hợp deploy tự động lên Docker Container.",
                "Review code định kỳ cho 3 lập trình viên Junior, chia sẻ các best practices về tối ưu bộ nhớ và viết clean code trong Vue."
            ]}
        ]
    },
    "Frontend Angular": {
        "title": "Frontend Engineer (Angular)",
        "skills": [
            {"category": "Ngôn ngữ & Core", "items": ["TypeScript (Advanced)", "HTML5 & CSS3/SCSS", "RxJS (Reactive Extensions)", "JavaScript ES6+"]},
            {"category": "Framework & CLI", "items": ["Angular CLI & Workspace", "Angular Ivy Engine", "Component Lifecycle & Hooks", "Dependency Injection (DI)"]},
            {"category": "State & UI Libraries", "items": ["NgRx Store / Component Store", "Angular Material / NG-ZORRO", "Tailwind CSS", "Angular Router & Lazy Loading"]}
        ],
        "projects": [
            {"name": "Enterprise Logistics Portal", "description": "Xây dựng giao diện hệ thống quản lý logistics lớn bằng Angular 16 và NgRx. Tích hợp RxJS để xử lý các luồng dữ liệu thời gian thực đồng bộ từ WebSockets, tối ưu hóa Change Detection Strategy (OnPush) giúp giảm 50% thời gian render giao diện.", "tags": ["Angular", "TypeScript", "RxJS", "NgRx", "Tailwind CSS"]},
            {"name": "Collaborative Agile Workspace", "description": "Phát triển công cụ quản lý dự án cộng tác sử dụng Angular, RxJS và Firebase. Hỗ trợ cập nhật tiến độ kéo thả nhiệm vụ (Angular CDK Drag and Drop) và tích hợp hệ thống thông báo thời gian thực.", "tags": ["Angular", "RxJS", "Firebase", "Angular CDK", "SCSS"]}
        ],
        "experiences": [
            {"position": "Angular Developer", "bullets": [
                "Phát triển và tối ưu hóa các module tính năng (Lazy Loading Modules) cho ứng dụng quản lý nhân sự bằng Angular.",
                "Tích hợp các dịch vụ HttpClient để giao tiếp với backend, xử lý lỗi tập trung bằng HTTP Interceptors.",
                "Sử dụng Jasmine và Karma để viết unit test cho các components và services cốt lõi của ứng dụng.",
                "Phối hợp với QA để kiểm thử, phát hiện lỗi giao diện và sửa chữa kịp thời trên môi trường Dev.",
                "Thiết kế và tùy biến các component UI phức tạp tuân thủ chặt chẽ bản thiết kế Figma."
            ]},
            {"position": "Senior Angular Engineer", "bullets": [
                "Thiết kế cấu trúc dự án Angular theo chuẩn Monorepo sử dụng Nx Dev Tools, quản lý mã nguồn hiệu quả giữa các dự án con.",
                "Áp dụng các kỹ thuật tối ưu hiệu năng như Route Preloading Strategies, Change Detection OnPush và Server-Side Rendering (Angular Universal).",
                "Xây dựng thư viện component nội bộ dùng chung được đóng gói dưới dạng Angular Library phục vụ các đội nhóm phát triển.",
                "Cấu hình CI/CD tự động chạy unit test và linting trước khi build deploy lên AWS S3.",
                "Dẫn dắt và đào tạo chuyên môn Angular cho 3 thành viên Junior, thường xuyên review PR."
            ]}
        ]
    },
    "Mobile Flutter": {
        "title": "Mobile Developer (Flutter)",
        "skills": [
            {"category": "Ngôn ngữ & Cốt lõi", "items": ["Dart Language (OOP, Null Safety)", "Flutter SDK (Widgets, Render)", "Android SDK (Java/Kotlin)", "iOS Native (Swift/Objective-C)"]},
            {"category": "Quản lý Trạng thái", "items": ["BLoC / Cubit Pattern", "Provider / Riverpod", "GetX Framework"]},
            {"category": "Dữ liệu & Tích hợp", "items": ["SQLite / Hive (Local Cache)", "REST API & GraphQL (Dio)", "Firebase Services (Auth, FCM)", "Google Maps & Core Location"]}
        ],
        "projects": [
            {"name": "JobHub Mobile Client", "description": "Phát triển ứng dụng tìm kiếm việc làm đa nền tảng bằng Flutter phục vụ hơn 100,000 người dùng hoạt động hàng tháng. Tích hợp tính năng định vị GPS thời gian thực tìm việc quanh đây, xây dựng hệ thống thông báo đẩy (Push Notifications) thông qua Firebase Cloud Messaging và tối ưu bộ nhớ cache để lưu trữ thông tin tin tuyển dụng xem offline.", "tags": ["Flutter", "BLoC", "Firebase FCM", "Google Maps"]},
            {"name": "Secure E-Wallet Application", "description": "Xây dựng ứng dụng ví điện tử bảo mật cao, hỗ trợ liên kết thẻ ngân hàng và quét mã QR Code để giao dịch nhanh. Áp dụng công nghệ xác thực sinh trắc học (vân tay và khuôn mặt - FaceID/TouchID) bằng `local_auth`, mã hóa dữ liệu đầu cuối SSL Pinning và cấu hình che giấu thông tin màn hình nhạy cảm khi ứng dụng chạy ngầm.", "tags": ["Flutter", "Dart", "Biometrics", "QR Code", "SSL Pinning"]},
            {"name": "Travel Social Network App", "description": "Phát triển mạng xã hội chia sẻ trải nghiệm du lịch đa nền tảng tích hợp Google Maps API để hiển thị bản đồ định tuyến và chỉ đường thông minh. Xây dựng tính năng chat thời gian thực bằng WebSockets và truyền dữ liệu đa phương tiện (hình ảnh, video chất lượng cao) được tối ưu hóa nén ảnh tự động ngay trên thiết bị.", "tags": ["Flutter", "Provider", "WebSockets", "Google Maps API"]}
        ],
        "experiences": [
            {"position": "Flutter Developer", "bullets": [
                "Xây dựng giao diện ứng dụng di động mượt mà đạt chuẩn 60fps trên cả Android và iOS từ một codebase duy nhất.",
                "Triển khai mô hình quản lý trạng thái BLoC/Cubit kết hợp RxDart giúp tách biệt hoàn toàn logic nghiệp vụ ra khỏi UI.",
                "Tối ưu hóa kích thước file cài đặt ứng dụng (APK/IPA) giảm tới 35% thông qua kỹ thuật Proguard, App Bundles và nén tài nguyên hình ảnh.",
                "Tích hợp thư viện SQLite và Hive để lưu trữ dữ liệu cục bộ (Offline Cache), đảm bảo trải nghiệm sử dụng không bị gián đoạn khi kết nối mạng yếu.",
                "Viết các kịch bản Widget Tests và Unit Tests giúp đảm bảo độ ổn định của giao diện trước các bản cập nhật hệ điều hành mới."
            ]},
            {"position": "Senior Mobile Developer", "bullets": [
                "Thiết kế kiến trúc dự án Flutter theo chuẩn Clean Architecture kết hợp Dependency Injection (GetIt/Injectable), tối ưu hóa tính độc lập giữa các lớp nghiệp vụ.",
                "Cấu hình quy trình tự động hóa đóng gói và xuất bản ứng dụng lên Google Play và App Store sử dụng Fastlane kết hợp Jenkins CI/CD.",
                "Khắc phục triệt để các lỗi rò rỉ bộ nhớ (memory leaks) và giảm 40% lượng CPU sử dụng trong quá trình ứng dụng thực hiện các hoạt ảnh phức tạp.",
                "Viết các Plugin Flutter tùy biến bằng Kotlin (Android) và Swift (iOS) thông qua MethodChannel để can thiệp trực tiếp vào phần cứng của thiết bị.",
                "Định hướng giải pháp công nghệ, thực hiện review code kỹ lưỡng và hỗ trợ kỹ thuật cho 3 lập trình viên di động khác trong dự án."
            ]}
        ]
    },
    "Mobile React Native": {
        "title": "React Native Developer",
        "skills": [
            {"category": "Ngôn ngữ & Core Mobile", "items": ["React Native CLI & Expo Framework", "React Core (Hooks, Context API)", "JavaScript (ES6+) & TypeScript", "React Navigation (Stack/Tabs)"]},
            {"category": "Quản lý Trạng thái & UI", "items": ["Redux Toolkit / Zustand", "React Native Paper / NativeBase", "Styled Components", "Lottie Animations"]},
            {"category": "Tích hợp & Đóng gói", "items": ["Native Modules (Swift, Kotlin)", "Apple HealthKit & Google Fit API", "Push Notifications (FCM / APNs)", "Fastlane & CI/CD cho Mobile"]}
        ],
        "projects": [
            {"name": "Cross-Platform Fitness Companion App", "description": "Phát triển ứng dụng theo dõi sức khỏe đa nền tảng bằng React Native và TypeScript. Tích hợp Apple HealthKit và Google Fit API để đồng bộ hóa số bước chân, nhịp tim theo thời gian thực. Cấu hình cơ sở dữ liệu SQLite lưu trữ dữ liệu offline giúp người dùng có thể sử dụng ứng dụng khi mất mạng.", "tags": ["React Native", "TypeScript", "HealthKit", "Google Fit", "SQLite"]},
            {"name": "Real-time Food Delivery Application", "description": "Xây dựng ứng dụng di động giao đồ ăn hỗ trợ người dùng theo dõi tài xế thời gian thực trên bản đồ Google Maps qua WebSockets. Thiết kế giao diện luồng thanh toán một chạm tích hợp Stripe SDK, và cấu hình thông báo đẩy (Push Notifications) tự động qua Firebase Cloud Messaging.", "tags": ["React Native", "WebSockets", "Google Maps", "Stripe", "FCM"]}
        ],
        "experiences": [
            {"position": "React Native Developer", "bullets": [
                "Xây dựng ứng dụng di động đa nền tảng (Android & iOS) sử dụng duy nhất một codebase React Native.",
                "Tối ưu hóa hiệu năng danh sách cuộn dài bằng FlatList Virtualization, giúp giảm tình trạng giật lag màn hình.",
                "Tích hợp các RESTful API của hệ thống backend và xử lý đồng bộ hóa state bằng Redux Toolkit.",
                "Đóng gói và phân phối ứng dụng lên môi trường TestFlight (iOS) và Google Play Internal Sharing phục vụ test nội bộ.",
                "Viết các unit test cho các service xử lý logic tính toán độc lập bằng thư viện Jest."
            ]},
            {"position": "Senior React Native Specialist", "bullets": [
                "Thiết kế cấu trúc dự án React Native theo mô hình Clean Architecture giúp tách biệt lớp UI và lớp xử lý logic nghiệp vụ.",
                "Viết các Native Modules bằng Swift (iOS) và Kotlin (Android) để tương tác trực tiếp với cảm biến phần cứng của thiết bị.",
                "Cấu hình tự động hóa quy trình build và release app lên App Store Connect và Google Play Console sử dụng Fastlane.",
                "Giảm 45% thời gian khởi động ứng dụng (Cold Start Time) thông qua kỹ thuật tối ưu hóa bundle và áp dụng Hermes engine.",
                "Dẫn dắt đội ngũ mobile gồm 4 thành viên, phối hợp chặt chẽ với Product Owner để định hình lộ trình phát triển sản phẩm."
            ]}
        ]
    },
    "Mobile iOS Swift": {
        "title": "iOS Developer",
        "skills": [
            {"category": "Ngôn ngữ & Framework", "items": ["Swift (Concurrency, Protocol)", "SwiftUI & Combine Framework", "UIKit & Auto Layout", "Xcode & Interface Builder"]},
            {"category": "Dữ liệu & Tích hợp", "items": ["CoreData & SwiftData", "RESTful API (URLSession/Alamofire)", "CocoaPods & Swift Package Manager", "Keychain & Secure Storage"]},
            {"category": "Kiến trúc & Đóng gói", "items": ["MVVM & Clean Architecture", "App Store Connect & TestFlight", "Memory Management (ARC)", "Core Animation & UI Customization"]}
        ],
        "projects": [
            {"name": "Smart Home Controller App", "description": "Phát triển ứng dụng iOS điều khiển thiết bị thông minh qua kết nối Bluetooth Low Energy (BLE). Sử dụng SwiftUI và Combine để đồng bộ hóa trạng thái thiết bị thời gian thực, quản lý cơ sở dữ liệu nội bộ với CoreData.", "tags": ["Swift", "SwiftUI", "Combine", "CoreData", "BLE"]},
            {"name": "Finance Portfolio Tracker", "description": "Xây dựng ứng dụng theo dõi danh mục đầu tư tài chính sử dụng Swift và UIKit. Tích hợp biểu đồ trực quan, cơ chế bảo mật sinh trắc học FaceID/TouchID và đồng bộ dữ liệu qua CloudKit.", "tags": ["Swift", "UIKit", "FaceID", "CloudKit", "Alamofire"]}
        ],
        "experiences": [
            {"position": "iOS Developer", "bullets": [
                "Phát triển giao diện người dùng mượt mà bằng SwiftUI và UIKit tương thích với các dòng iPhone/iPad khác nhau.",
                "Tích hợp các API Restful, xử lý phân tích cú pháp JSON phức tạp và lưu trữ dữ liệu đệm bằng CoreData.",
                "Sử dụng Xcode Instruments để kiểm tra rò rỉ bộ nhớ (Memory Leaks) và tối ưu hóa thời gian khởi động app.",
                "Viết hơn 100 kịch bản Unit Test sử dụng XCTest để kiểm thử luồng đăng ký/đăng nhập và thanh toán.",
                "Tham gia quy trình đưa ứng dụng lên TestFlight để kiểm thử nội bộ trước khi phát hành chính thức."
            ]},
            {"position": "Senior iOS Developer", "bullets": [
                "Thiết kế và cấu trúc ứng dụng theo kiến trúc MVVM-C hoặc Clean Swift giúp tăng khả năng tái sử dụng và kiểm thử.",
                "Triển khai lập trình bất đồng bộ hiện đại sử dụng Swift Concurrency (async/await, Actors) giúp ứng dụng chạy ổn định và mượt mà hơn.",
                "Cấu hình tự động hóa quy trình đóng gói và phát hành ứng dụng lên App Store sử dụng Fastlane và GitHub Actions.",
                "Xây dựng các thành phần giao diện tùy biến (custom UI components) hiệu năng cao hỗ trợ các hiệu ứng hoạt hình phức tạp.",
                "Mentor cho 2 lập trình viên iOS trẻ, hướng dẫn các quy chuẩn thiết kế giao diện của Apple (Human Interface Guidelines)."
            ]}
        ]
    },
    "Mobile Android Kotlin": {
        "title": "Android Developer",
        "skills": [
            {"category": "Ngôn ngữ & Core", "items": ["Kotlin (Coroutines, Flow)", "Android SDK (Activity/Fragment)", "Java Core", "Jetpack Compose (Modern UI)"]},
            {"category": "Kiến trúc & Dữ liệu", "items": ["MVVM / MVI Architecture", "Room Database (SQLite)", "Retrofit & OkHttp (Networking)", "Dagger Hilt (Dependency Injection)"]},
            {"category": "Công cụ & Tích hợp", "items": ["Android Studio & Gradle", "Google Play Console", "Firebase Service Suite", "Git & CI/CD Pipelines"]}
        ],
        "projects": [
            {"name": "E-Learning Mobile App", "description": "Phát triển ứng dụng học trực tuyến đa phương tiện sử dụng Jetpack Compose và Kotlin Coroutines. Tích hợp trình phát video tùy biến ExoPlayer, hỗ trợ tải bài học offline và lưu trữ trạng thái học tập bằng Room.", "tags": ["Kotlin", "Jetpack Compose", "Coroutines", "Room", "ExoPlayer"]},
            {"name": "Location-Based Delivery Tracker", "description": "Xây dựng ứng dụng giao hàng dựa trên vị trí GPS thời gian thực. Tích hợp Google Maps SDK, xử lý chạy ngầm (Foreground Services) để liên tục cập nhật tọa độ tài xế ngay cả khi tắt màn hình.", "tags": ["Kotlin", "Google Maps SDK", "Retrofit", "Hilt", "Foreground Services"]}
        ],
        "experiences": [
            {"position": "Android Developer", "bullets": [
                "Xây dựng giao diện ứng dụng di động Android hiện đại bằng Jetpack Compose kết hợp Material Design 3.",
                "Sử dụng Kotlin Coroutines và Flow để xử lý các tác vụ bất đồng bộ dưới nền tránh gây giật lag luồng giao diện (UI Thread).",
                "Thiết lập cấu trúc lưu trữ cơ sở dữ liệu cục bộ bằng Room Database hỗ trợ trải nghiệm offline cho người dùng.",
                "Đóng gói ứng dụng dạng Android App Bundle (.aab) giúp giảm 20% dung lượng tải xuống trên Google Play.",
                "Thực hiện tìm kiếm và sửa lỗi rò rỉ bộ nhớ sử dụng LeakCanary."
            ]},
            {"position": "Senior Android Developer", "bullets": [
                "Tái cấu trúc toàn bộ dự án lớn sang kiến trúc MVVM kết hợp Dependency Injection bằng Dagger Hilt, nâng cao tính mô-đun hóa.",
                "Tối ưu hóa hiệu năng render giao diện, loại bỏ overdraw giúp tăng 40% độ mượt khi cuộn các danh sách phức tạp.",
                "Thiết lập quy trình Jenkins CI/CD tự động build, chạy unit test và đẩy file cài đặt lên Google Play Console.",
                "Nghiên cứu tích hợp các giải pháp bảo mật Android như Proguard/R8 obfuscation, kiểm tra Root thiết bị và SSL Pinning.",
                "Hướng dẫn kỹ thuật và review mã nguồn hàng ngày cho nhóm 3 lập trình viên di động Android."
            ]}
        ]
    },
    "Data & AI": {
        "title": "AI & Data Engineer",
        "skills": [
            {"category": "Ngôn ngữ & Phân tích", "items": ["Python (Pandas, NumPy, Scipy)", "SQL (Subqueries, Window Functions)", "R Language (Phân tích thống kê)", "Jupyter Notebook & Data Viz"]},
            {"category": "Deep Learning & NLP", "items": ["PyTorch / TensorFlow / Keras", "HuggingFace Transformers (BERT)", "SpaCy, NLTK (NLP Libraries)", "Scikit-Learn (ML Algorithms)"]},
            {"category": "Generative AI & MLOps", "items": ["Large Language Models (Gemini, Llama)", "LangChain / LlamaIndex Frameworks", "RAG (Retrieval-Augmented)", "FastAPI / Docker (Deploy Model)"]}
        ],
        "projects": [
            {"name": "Intelligent Resume Parser System", "description": "Xây dựng hệ thống tự động trích xuất thông tin kỹ năng, kinh nghiệm từ file CV PDF thô bằng mô hình NLP nâng cao. Sử dụng mô hình Sentence-BERT (SBERT) để chuyển đổi text thành vector nhúng ngữ nghĩa, lưu trữ vào Pinecone Vector DB và tính toán độ tương đồng (Cosine Similarity) để so khớp CV với JD. Độ chính xác trích xuất đạt 92% và tốc độ phản hồi dưới 1.5 giây.", "tags": ["Python", "PyTorch", "SBERT", "FastAPI", "Pinecone"]},
            {"name": "Real-time Salary Prediction Model", "description": "Huấn luyện và triển khai mô hình học máy dự báo khoảng lương tuyển dụng dựa trên dữ liệu thu thập từ hơn 200,000 tin tuyển dụng. Sử dụng thuật toán XGBoost Regressor kết hợp tối ưu tham số tự động bằng Optuna. Hệ thống giúp phòng nhân sự tự động ước lượng ngân sách tuyển dụng với sai số trung bình (MAE) cực thấp dưới 8%.", "tags": ["Python", "XGBoost", "Scikit-Learn", "Optuna", "MongoDB"]},
            {"name": "Automated Chat Interview Agent", "description": "Phát triển chatbot phỏng vấn sơ tuyển ứng viên sử dụng các mô hình ngôn ngữ lớn (LLM - Llama 3) qua LangChain. Xây dựng quy trình RAG để chatbot tự động hỏi và đánh giá câu trả lời của ứng viên dựa trên bộ tiêu chí kỹ năng của vị trí tuyển dụng. Tích hợp WebSockets giúp cuộc hội thoại diễn ra theo thời gian thực mượt mà.", "tags": ["FastAPI", "Llama 3", "LangChain", "WebSockets", "RAG"]}
        ],
        "experiences": [
            {"position": "Data Scientist / AI Engineer", "bullets": [
                "Thu thập, làm sạch và chuẩn hóa hơn 500,000 bản ghi dữ liệu tuyển dụng thô từ nhiều nguồn khác nhau bằng thư viện Pandas và Spark.",
                "Xây dựng pipeline phân tích ngữ nghĩa (Semantic Parsing) tự động trích xuất thực thể (Named Entity Recognition - NER) đối với các kỹ năng CNTT.",
                "Thiết kế và deploy dịch vụ AI Services trên nền tảng FastAPI chạy trong container Docker, đảm bảo khả năng mở rộng tốt và chịu tải cao.",
                "Thực hiện kiểm định các giả thuyết thống kê (A/B Testing) để đánh giá hiệu quả của thuật toán gợi ý việc làm mới, giúp tăng 15% tỷ lệ nộp hồ sơ.",
                "Viết tài liệu kỹ thuật chi tiết về quy trình tiền xử lý dữ liệu và huấn luyện mô hình học máy phục vụ chuyển giao công nghệ."
            ]},
            {"position": "Lead AI Engineer", "bullets": [
                "Quy hoạch kiến trúc AI tổng thể cho nền tảng tuyển dụng thông minh của công ty, thiết kế quy trình tự động MLOps từ thu thập dữ liệu đến deploy mô hình.",
                "Tích hợp thành công giải pháp Generative AI kết hợp RAG giúp tự động tạo báo cáo đánh giá chuyên sâu năng lực ứng viên từ CV, tiết kiệm 70% thời gian lọc hồ sơ của HR.",
                "Tối ưu hóa kích thước mô hình học sâu thông qua kỹ thuật lượng tử hóa (Quantization) và chưng cất tri thức (Knowledge Distillation), giảm 50% chi phí tài nguyên máy chủ.",
                "Quản lý và định hướng chuyên môn cho nhóm gồm 3 kỹ sư AI và 2 kỹ sư dữ liệu (Data Engineers), đảm bảo tiến độ và chất lượng sản phẩm.",
                "Nghiên cứu các công nghệ AI mới nhất (như Agentic Workflow) để định hình và cải tiến liên tục các tính năng cốt lõi của nền tảng."
            ]}
        ]
    },
    "Backend Java": {
        "title": "Java Developer",
        "skills": [
            {"category": "Ngôn ngữ & Java Core", "items": ["Java (Core/17/21)", "Spring Boot / Spring Cloud", "Hibernate / JPA / Spring Data", "Multithreading & Concurrency"]},
            {"category": "Cơ sở dữ liệu & Caching", "items": ["MySQL", "PostgreSQL", "Oracle DB", "Redis Cache"]},
            {"category": "Kiến trúc & Hệ thống", "items": ["Microservices Architecture", "Kafka / RabbitMQ", "Docker & Kubernetes", "RESTful API / gRPC"]}
        ],
        "projects": [
            {"name": "Retail Core Banking Backend", "description": "Thiết kế và phát triển phân hệ quản lý giao dịch lõi cho hệ thống ngân hàng bán lẻ sử dụng Java 17 và Spring Boot. Áp dụng cơ chế Distributed Transaction với Saga Pattern, xử lý đồng thời qua Kafka và lưu trữ cache giao dịch thời gian thực trên Redis Cluster. Hệ thống xử lý an toàn hơn 1 triệu giao dịch mỗi ngày với độ trễ thấp.", "tags": ["Java 17", "Spring Boot", "Kafka", "Redis", "PostgreSQL"]},
            {"name": "Microservices Logistics System", "description": "Xây dựng hệ thống quản lý logistics phân phối hàng hóa dựa trên kiến trúc Spring Cloud Microservices. Triển khai các service độc lập giao tiếp qua gRPC, tích hợp Spring Cloud Gateway kết hợp Eureka Service Discovery. Tối ưu hóa thuật toán định tuyến giao hàng giúp giảm thời gian phân phối xuống 15%.", "tags": ["Spring Cloud", "gRPC", "MySQL", "Eureka", "Docker"]}
        ],
        "experiences": [
            {"position": "Java Developer", "bullets": [
                "Thiết kế và triển khai các API nghiệp vụ chính của hệ thống quản lý đơn hàng bằng Spring Boot.",
                "Tối ưu hóa các truy vấn SQL phức tạp và cấu hình Hibernate Second-level cache giúp giảm 40% tải cho cơ sở dữ liệu MySQL.",
                "Tích hợp hệ thống Spring Security kết hợp với JWT để quản lý phiên đăng nhập và phân quyền truy cập cho người dùng.",
                "Viết các unit test bằng JUnit 5 và Mockito, tăng độ phủ mã nguồn (code coverage) lên 80%.",
                "Phối hợp với đội QC để điều tra, debug và sửa đổi các lỗi phát sinh trên môi trường kiểm thử."
            ]},
            {"position": "Senior Java Engineer", "bullets": [
                "Chịu trách nhiệm thiết kế kiến trúc các dịch vụ microservices mới và cải thiện hiệu năng cho các dịch vụ hiện có.",
                "Thiết kế và cấu hình hàng đợi Kafka chịu tải cao để xử lý luồng dữ liệu thông báo và đồng bộ hóa tài khoản.",
                "Tái cấu trúc cơ sở dữ liệu lớn trên Oracle DB, thiết kế phân vùng bảng (partitioning) giúp tốc độ đọc dữ liệu tăng 2.5 lần.",
                "Thiết lập quy trình CI/CD hoàn chỉnh sử dụng GitLab CI để tự động hóa khâu build, test và đẩy Docker image lên container registry.",
                "Hỗ trợ chuyên môn và dẫn dắt 3 lập trình viên Junior, định hướng phong cách viết code sạch và tuân thủ các quy tắc bảo mật."
            ]}
        ]
    },
    "Backend Go": {
        "title": "Go Developer",
        "skills": [
            {"category": "Ngôn ngữ & Concurrency", "items": ["Go Language (Goroutines, Channels)", "Context Package", "Interface & Reflection", "Memory Management & GC Tuning"]},
            {"category": "Frameworks & Web", "items": ["Gin-Gonic / Fiber / Echo", "gRPC & Protocol Buffers", "RESTful API Development", "Go-Micro Framework"]},
            {"category": "Cơ sở dữ liệu & DevOps", "items": ["PostgreSQL / MySQL (GORM)", "Redis (Caching & Pub/Sub)", "Docker & Docker Compose", "Kafka / RabbitMQ (Message Queue)"]}
        ],
        "projects": [
            {"name": "High-Throughput Notification Engine", "description": "Thiết kế và phát triển hệ thống gửi thông báo đẩy hàng loạt sử dụng Go và Kafka. Tận dụng sức mạnh của Goroutines và Channels giúp hệ thống xử lý ổn định hơn 20,000 thông báo mỗi giây với mức tiêu thụ tài nguyên máy chủ cực thấp.", "tags": ["Go", "Kafka", "Redis", "Docker", "Goroutines"]},
            {"name": "Microservices Financial API", "description": "Xây dựng hệ thống giao dịch tài chính phân tán bằng Go, giao tiếp giữa các service qua gRPC hiệu năng cao. Áp dụng kiến trúc Clean Architecture, tích hợp Jaeger để phân tích vết (distributed tracing) và lưu dữ liệu trên PostgreSQL.", "tags": ["Go", "gRPC", "Protobuf", "PostgreSQL", "Jaeger"]}
        ],
        "experiences": [
            {"position": "Go Developer", "bullets": [
                "Viết các dịch vụ API RESTful hiệu năng cao bằng framework Gin và lưu trữ dữ liệu thông qua GORM.",
                "Tận dụng Goroutines để xử lý song song các tác vụ nền độc lập, cải thiện tốc độ phản hồi hệ thống 35%.",
                "Tối ưu hóa các câu lệnh SQL phức tạp trên PostgreSQL và cấu hình cơ chế cache bằng Redis.",
                "Viết unit test đầy đủ sử dụng thư viện testing tích hợp sẵn của Go kết hợp Testify.",
                "Docker hóa ứng dụng Go giúp đồng bộ hóa môi trường phát triển cục bộ và triển khai lên Kubernetes."
            ]},
            {"position": "Senior Go Engineer", "bullets": [
                "Thiết kế kiến trúc hệ thống phân tán chịu tải lớn bằng gRPC, giảm 60% băng thông truyền tải dữ liệu so với REST API truyền thống.",
                "Tối ưu hóa hiệu năng máy chủ Go bằng cách phân tích hồ sơ bộ nhớ (pprof profiling), giảm 40% RAM sử dụng và khắc phục tình trạng nghẽn GC.",
                "Triển khai hệ thống Message Broker (Kafka) để giao tiếp bất đồng bộ giữa các microservices, đảm bảo tính nhất quán cuối cùng của dữ liệu.",
                "Thiết lập hệ thống giám sát Prometheus metrics và Grafana dashboards cho toàn bộ cụm Go services.",
                "Dẫn dắt kỹ thuật nhóm backend gồm 4 thành viên, thường xuyên review thiết kế hệ thống và code."
            ]}
        ]
    },
    "Backend Python": {
        "title": "Python Developer",
        "skills": [
            {"category": "Ngôn ngữ & Frameworks", "items": ["Python (Asyncio, Multiprocessing)", "Django / Django REST Framework", "FastAPI (Asynchronous APIs)", "Flask (Microframework)"]},
            {"category": "Dữ liệu & Caching", "items": ["PostgreSQL / MySQL", "MongoDB (NoSQL)", "SQLAlchemy (ORM)", "Redis (Cache & Celery Broker)"]},
            {"category": "Hệ thống & Tích hợp", "items": ["Celery (Asynchronous Tasks)", "RabbitMQ / Redis (Queues)", "Docker / Docker Compose", "RESTful API / WebSockets"]}
        ],
        "projects": [
            {"name": "Real-time IoT Telemetry Platform", "description": "Xây dựng hệ thống backend thu thập và phân tích dữ liệu cảm biến từ hơn 5,000 thiết bị IoT thời gian thực sử dụng FastAPI và WebSockets. Sử dụng Redis làm hàng đợi thông điệp và Celery để chạy các tác vụ phân tích số liệu thống kê.", "tags": ["FastAPI", "WebSockets", "Redis", "Celery", "PostgreSQL"]},
            {"name": "Content Management REST System", "description": "Thiết kế cổng thông tin nội bộ quy mô lớn cho tập đoàn bằng Django và PostgreSQL. Tích hợp cơ chế tìm kiếm toàn văn (Full-text Search) bằng Elasticsearch, phân quyền người dùng phức tạp và hệ thống báo cáo tự động.", "tags": ["Django", "DRF", "PostgreSQL", "Elasticsearch", "Docker"]}
        ],
        "experiences": [
            {"position": "Python Developer", "bullets": [
                "Phát triển các API RESTful nhanh chóng và an toàn sử dụng Django REST Framework và FastAPI.",
                "Cấu hình Celery kết hợp Redis để chạy các tác vụ nền tốn thời gian như gửi email hàng loạt và xử lý xuất báo cáo Excel.",
                "Thiết kế cấu trúc cơ sở dữ liệu quan hệ, viết và tối ưu hóa các truy vấn SQL sử dụng Django ORM."
                "Sử dụng PyTest để viết các bộ kiểm thử tự động, đảm bảo tỷ lệ phủ mã nguồn trên 80%.",
                "Xây dựng tài liệu API tự động đẹp mắt bằng Swagger tích hợp sẵn trong FastAPI."
            ]},
            {"position": "Senior Python Engineer", "bullets": [
                "Tái thiết kế ứng dụng web cũ từ đồng bộ sang bất đồng bộ sử dụng FastAPI và Asyncio, giúp tăng gấp 5 lần khả năng xử lý yêu cầu đồng thời.",
                "Thiết kế và phát triển kiến trúc dịch vụ microservices sử dụng RabbitMQ làm message broker kết nối các ứng dụng Python.",
                "Tối ưu hóa các truy vấn cơ sở dữ liệu lớn trên PostgreSQL thông qua lập index nâng cao và phân vùng bảng, giảm 50% thời gian phản hồi.",
                "Thiết lập quy trình CI/CD tích hợp Docker giúp tự động hóa quá trình đóng gói và triển khai ứng dụng lên AWS ECS.",
                "Đóng vai trò Tech Lead, hướng dẫn và định hướng chuyên môn Python cho 4 lập trình viên trong nhóm."
            ]}
        ]
    },
    "DevOps": {
        "title": "DevOps Engineer",
        "skills": [
            {"category": "Cloud & Hệ điều hành", "items": ["Amazon Web Services (AWS)", "Google Cloud Platform (GCP)", "Linux Systems Administration", "Bash / Python Scripting"]},
            {"category": "CI/CD & IAC", "items": ["Jenkins / GitLab CI", "Terraform", "Ansible", "ArgoCD / GitOps"]},
            {"category": "Containers & Monitor", "items": ["Docker & Containerization", "Kubernetes (K8s)", "Prometheus & Grafana", "ELK Stack (Elasticsearch, Kibana)"]}
        ],
        "projects": [
            {"name": "Multi-Cloud Infrastructure Automation", "description": "Thiết kế và tự động hóa hạ tầng đám mây có độ sẵn sàng cao (High Availability) trên AWS sử dụng Terraform. Triển khai kiến trúc VPC đa vùng (Multi-AZ), cấu hình Auto Scaling Group kết hợp Load Balancer để tự động điều chỉnh tài nguyên máy chủ. Hệ thống giúp giảm 35% chi phí vận hành hạ tầng hàng tháng.", "tags": ["AWS", "Terraform", "Linux", "Load Balancer"]},
            {"name": "GitOps Kubernetes Migration", "description": "Dẫn dắt dự án chuyển đổi và triển khai toàn bộ ứng dụng của công ty từ máy chủ vật lý lên Kubernetes Cluster. Thiết lập quy trình triển khai GitOps sử dụng ArgoCD kết hợp với Helm Charts, tự động hóa 100% quy trình deploy mã nguồn từ môi trường Dev lên Production mà không cần can thiệp thủ công.", "tags": ["Kubernetes", "ArgoCD", "Helm", "GitLab CI", "Docker"]}
        ],
        "experiences": [
            {"position": "DevOps Engineer", "bullets": [
                "Xây dựng và duy trì các đường ống dẫn tích hợp và triển khai liên tục (CI/CD pipelines) bằng Jenkins cho 10+ dự án phần mềm.",
                "Docker hóa các ứng dụng cũ và viết file cấu hình docker-compose phục vụ môi trường phát triển cục bộ của lập trình viên.",
                "Thiết lập hệ thống giám sát Prometheus và bảng điều khiển Grafana để cảnh báo tức thời các sự cố quá tải RAM/CPU trên máy chủ.",
                "Quản trị hệ thống máy chủ Linux, thiết lập phân quyền người dùng bảo mật và viết các script Bash tự động sao lưu dữ liệu hàng ngày.",
                "Hỗ trợ đội ngũ phát triển giải quyết các vấn đề liên quan đến kết nối mạng, biến môi trường và cấu hình domain."
            ]},
            {"position": "Senior DevOps Specialist", "bullets": [
                "Thiết kế hạ tầng Kubernetes quy mô lớn trên môi trường AWS (EKS), quản lý vòng đời cụm cụm máy chủ và tối ưu hóa tài nguyên.",
                "Triển khai kiến trúc hạ tầng dưới dạng mã nguồn (IaC) bằng Terraform giúp tự động khởi tạo môi trường Staging mới chỉ trong 10 phút.",
                "Cấu hình chính sách bảo mật mạng (Network Policies) và quản lý bí mật bảo mật (Secrets Management) sử dụng HashiCorp Vault.",
                "Tích hợp hệ thống quản lý logs tập trung ELK Stack, giúp thu thập và phân tích hơn 100GB log hệ thống mỗi ngày.",
                "Tham gia tư vấn cấu hình tối ưu chi phí hạ tầng cho ban giám đốc, giảm 40% chi phí hóa đơn dịch vụ đám mây."
            ]}
        ]
    },
    "QA Automation": {
        "title": "QA Automation Engineer",
        "skills": [
            {"category": "Ngôn ngữ & Frameworks", "items": ["Python / Java / TypeScript", "Selenium WebDriver", "Playwright / Cypress", "Appium (Mobile Automation)"]},
            {"category": "API & Công cụ Test", "items": ["Postman / RestAssured", "JMeter (Performance Testing)", "Git & Github", "Jira / Confluence / TestLink"]},
            {"category": "Phương pháp & CI/CD", "items": ["Agile / Scrum Methodology", "CI/CD Integration (Jenkins)", "Page Object Model (POM)", "Behavior-Driven Development (BDD)"]}
        ],
        "projects": [
            {"name": "E-Commerce Automated Test Suite", "description": "Thiết kế và triển khai khung kiểm thử tự động toàn diện cho hệ thống website thương mại điện tử sử dụng Playwright và TypeScript. Xây dựng hơn 500 kịch bản kiểm thử bao phủ toàn bộ luồng mua hàng và thanh toán, tích hợp chạy tự động hàng ngày trên GitLab CI. Kết quả giúp giảm 80% thời gian kiểm thử hồi quy (Regression Testing).", "tags": ["Playwright", "TypeScript", "GitLab CI", "Regression Test"]},
            {"name": "API Automated Security Suite", "description": "Xây dựng hệ thống tự động kiểm thử hiệu năng và bảo mật cho hơn 100 API dịch vụ tài chính sử dụng RestAssured và JMeter. Tự động hóa khâu chuẩn bị dữ liệu test và đối soát kết quả phản hồi từ API gateway, giúp phát hiện sớm hơn 30 lỗi nghiệp vụ nghiêm trọng trước khi phát hành sản phẩm.", "tags": ["RestAssured", "JMeter", "Postman", "Java", "Security Test"]}
        ],
        "experiences": [
            {"position": "QA Automation Engineer", "bullets": [
                "Viết các kịch bản kiểm thử tự động (Automation Scripts) cho giao diện web sử dụng Selenium WebDriver và Python.",
                "Tích hợp các kịch bản test tự động vào luồng CI/CD bằng Jenkins để chạy kích hoạt mỗi khi có pull request mới.",
                "Thực hiện kiểm thử API tự động bằng Postman, thiết lập các đoạn code Assertions kiểm tra tính đúng đắn của dữ liệu JSON trả về.",
                "Báo cáo lỗi chi tiết lên hệ thống Jira, theo dõi vòng đời của lỗi và phối hợp với lập trình viên để xác minh bản vá.",
                "Tham gia viết tài liệu kế hoạch kiểm thử (Test Plan) và thiết kế bộ dữ liệu kiểm thử (Test Data) cho các dự án mới."
            ]},
            {"position": "Senior Automation QA Lead", "bullets": [
                "Định hướng và xây dựng kiến trúc khung kiểm thử tự động (Automation Framework) từ con số 0 sử dụng mô hình Page Object Model.",
                "Thiết lập kịch bản test hiệu năng chịu tải cao sử dụng JMeter giả lập hơn 5,000 người dùng truy cập đồng thời để đo lường giới hạn chịu tải.",
                "Đào tạo chuyển đổi từ kiểm thử thủ công (Manual Testing) sang kiểm thử tự động cho đội ngũ QA gồm 5 thành viên.",
                "Xác định và chuẩn hóa các chỉ số đo lường chất lượng phần mềm (KPIs) và báo cáo trực tiếp tiến độ chất lượng cho giám đốc sản phẩm.",
                "Nghiên cứu các công nghệ kiểm thử mới và áp dụng AI tự động sinh kịch bản test giúp tăng 30% hiệu suất kiểm thử."
            ]}
        ]
    }
}

ADDRESSES = [
    "Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Cần Thơ", "Hải Phòng",
    "Bình Dương", "Đồng Nai", "Bà Rịa - Vũng Tàu", "Khánh Hòa", "Lâm Đồng",
    "Quảng Nam", "Thừa Thiên Huế", "Nghệ An", "Thanh Hóa", "Nam Định",
    "Thái Bình", "Hải Dương", "Quảng Ninh", "Bắc Ninh", "Vĩnh Phúc",
    "Thái Nguyên", "Đắk Lắk", "Gia Lai", "Bình Định", "Phú Yên",
    "Long An", "Tiền Giang", "An Giang", "Kiên Giang", "Tây Ninh",
    "Bến Tre", "Vĩnh Long", "Đồng Tháp", "Cà Mau", "Bạc Liêu"
]

SUMMARIES = {
    "Backend .NET": [
        "Tôi là một Kỹ sư phần mềm chuyên về Backend .NET với hơn 5 năm kinh nghiệm thiết kế và phát triển các hệ thống phân tán quy mô lớn. Đam mê xây dựng kiến trúc Microservices hiệu năng cao, tối ưu hóa cơ sở dữ liệu lớn và áp dụng các nguyên lý Clean Code. Luôn hướng tới việc giải quyết các bài toán kỹ thuật phức tạp và nâng cao trải nghiệm người dùng thông qua các giải pháp backend ổn định, bảo mật và dễ mở rộng.",
        "Lập trình viên .NET nhiệt huyết với tư duy logic tốt và thế mạnh phát triển hệ thống RESTful API. Có kinh nghiệm thực chiến với .NET Core, SQL Server, và kiến trúc Clean Architecture. Luôn chủ động cập nhật các xu hướng công nghệ mới, mong muốn đóng góp kỹ năng kỹ thuật để cùng đội ngũ phát triển nên các sản phẩm phần mềm chất lượng cao."
    ],
    "Frontend React": [
        "Kỹ sư Frontend giàu kinh nghiệm chuyên sâu về ReactJS và Next.js. Có thế mạnh về tối ưu hóa hiệu năng ứng dụng web, cải thiện trải nghiệm người dùng (UX) và tối ưu hóa SEO. Đam mê thiết kế các hệ thống component dùng chung (Design System) chuẩn hóa, viết code sạch bằng TypeScript và luôn phối hợp hiệu quả với UI/UX designers để hiện thực hóa các sản phẩm web tuyệt mỹ, mượt mà.",
        "Frontend Developer đam mê xây dựng giao diện web đẹp mắt, tối ưu trải nghiệm người dùng và tương thích tốt trên mọi thiết bị di động. Có kiến thức vững chắc về HTML5, CSS3, Tailwind CSS và phát triển SPA bằng React. Mong muốn được gia nhập môi trường năng động để thử thách bản thân với các bài toán UI phức tạp và phát triển toàn diện kỹ năng Frontend."
    ],
    "Frontend Vue": [
        "Kỹ sư Frontend giàu kinh nghiệm chuyên sâu về VueJS (Vue 2 & 3) và NuxtJS. Thế mạnh về tối ưu hóa SEO, xây dựng các Single Page Application hiệu năng cao và phát triển hệ thống component dùng chung (Design System) chuẩn hóa. Luôn hướng tới trải nghiệm người dùng mượt mà và viết mã nguồn sạch bằng TypeScript.",
        "Frontend Developer năng động với kiến thức vững chắc về VueJS, Tailwind CSS và RESTful API. Có tư duy logic tốt, khả năng thích nghi nhanh chóng với công nghệ mới và luôn sẵn sàng đóng góp kỹ năng kỹ thuật để tạo ra những giao diện web tuyệt vời."
    ],
    "Frontend Angular": [
        "Kỹ sư Frontend giàu kinh nghiệm chuyên sâu về Angular và phát triển các ứng dụng doanh nghiệp lớn (Enterprise Applications). Đam mê thiết kế các cấu trúc mã nguồn mở rộng, tối ưu hóa hiệu năng render qua cơ chế Change Detection Strategy và sử dụng RxJS để xử lý các luồng dữ liệu phức tạp bất đồng bộ. Luôn mong muốn áp dụng các best practices để tạo nên các sản phẩm web chất lượng cao, dễ bảo trì.",
        "Frontend Developer có kinh nghiệm phát triển SPA bằng Angular và TypeScript. Am hiểu về Component Lifecycle, Services, Routing và HttpClient. Có tư duy logic tốt, khả năng tự học nhanh và mong muốn thử thách bản thân với các bài toán lập trình web phức tạp trong môi trường chuyên nghiệp."
    ],
    "Mobile Flutter": [
        "Lập trình viên di động chuyên nghiệp với hơn 4 năm kinh nghiệm phát triển ứng dụng đa nền tảng bằng Flutter. Am hiểu sâu sắc về quản lý trạng thái (BLoC, Provider), tối ưu hiệu năng render 60fps và tích hợp các dịch vụ Native. Tự tin đóng gói, tối ưu dung lượng và phát hành ứng dụng lên cả hai kho ứng dụng App Store và Google Play Store một cách độc lập.",
        "Flutter Developer nhiệt huyết, có kinh nghiệm xây dựng các ứng dụng di động mượt mà, giao diện thân thiện với người dùng và có khả năng hoạt động offline tốt. Đam mê tối ưu hóa hiệu năng và viết mã nguồn sạch, dễ kiểm thử. Định hướng trở thành một chuyên gia kiến trúc ứng dụng di động trong tương lai gần."
    ],
    "Mobile React Native": [
        "Kỹ sư lập trình di động đa nền tảng với hơn 5 năm kinh nghiệm sử dụng React Native. Có kinh nghiệm viết Native Modules bằng Swift và Kotlin để can thiệp sâu vào hệ thống phần cứng, tối ưu hóa bộ nhớ và cấu hình tự động hóa đóng gói Fastlane. Mong muốn phát triển các sản phẩm mobile ổn định và mang lại giá trị cao.",
        "React Native Developer đam mê phát triển ứng dụng di động mượt mà trên cả hai hệ điều hành Android và iOS. Có thế mạnh về quản lý state bằng Redux Toolkit/Zustand, thiết kế UI/UX thân thiện và tương tác tốt. Tự tin đóng góp giá trị kỹ thuật cho nhóm phát triển."
    ],
    "Mobile iOS Swift": [
        "Kỹ sư lập trình di động iOS chuyên nghiệp với hơn 5 năm kinh nghiệm xây dựng các ứng dụng trên hệ điều hành iOS bằng Swift, SwiftUI và UIKit. Đam mê thiết kế giao diện tinh tế, hoạt ảnh mượt mà và tối ưu hóa hiệu năng ứng dụng. Có kinh nghiệm sâu sắc về lập trình bất đồng bộ bằng Swift Concurrency và Combine, lưu trữ dữ liệu CoreData và phát hành ứng dụng lên App Store.",
        "iOS Developer nhiệt huyết với kỹ năng phát triển ứng dụng di động bằng Swift và SwiftUI. Có kiến thức vững chắc về lập trình hướng đối tượng, tích hợp API RESTful và thiết kế giao diện người dùng đáp ứng. Luôn chủ động học hỏi các công nghệ mới và mong muốn tạo ra những sản phẩm iOS đẳng cấp."
    ],
    "Mobile Android Kotlin": [
        "Kỹ sư lập trình di động Android giàu kinh nghiệm chuyên sâu về Kotlin và Jetpack Compose. Thế mạnh về thiết kế kiến trúc MVVM sạch, tối ưu hóa hiệu năng sử dụng CPU/RAM của thiết bị và lập trình bất đồng bộ hiệu quả với Coroutines/Flow. Tự tin xây dựng, tối ưu hóa và xuất bản các ứng dụng chất lượng cao lên Google Play Store.",
        "Android Developer năng động có kinh nghiệm phát triển ứng dụng di động bằng Kotlin và Java. Có kiến thức vững vàng về Room Database, Retrofit và Android Jetpack components. Mong muốn được làm việc trong môi trường năng động để trau dồi kinh nghiệm và đóng góp giá trị kỹ thuật cho các sản phẩm di động."
    ],
    "Data & AI": [
        "Chuyên gia AI & Data Engineer có kinh nghiệm thiết kế và xây dựng các hệ thống phân tích dữ liệu, ứng dụng mô hình học máy (Machine Learning) và các giải pháp Generative AI (LLM, RAG). Thế mạnh về tiền xử lý dữ liệu lớn, tối ưu hóa truy vấn SQL và triển khai mô hình học sâu lên môi trường Production với hiệu năng cao. Luôn nỗ lực tìm kiếm tri thức từ dữ liệu để giúp doanh nghiệp ra quyết định thông minh.",
        "AI & Machine Learning Engineer có nền tảng toán học và thống kê vững chắc, đam mê nghiên cứu Xử lý ngôn ngữ tự nhiên (NLP) và xây dựng chatbot thông minh. Có kinh nghiệm thực hành với Python, PyTorch, Scikit-Learn và FastAPI. Luôn mong muốn tìm tòi, ứng dụng những mô hình AI tiên tiến nhất để giải quyết các bài toán thực tiễn."
    ],
    "Backend Java": [
        "Kỹ sư phần mềm chuyên Backend Java Spring Boot với hơn 6 năm kinh nghiệm trong ngành Fintech và Logistics. Đam mê thiết kế hệ thống Microservices vững chắc, tối ưu hóa cơ sở dữ liệu lớn và áp dụng các cơ chế truyền thông điệp bất đồng bộ (Kafka/RabbitMQ). Luôn hướng tới code chất lượng cao, có khả năng mở rộng tốt và duy trì tính ổn định tuyệt đối cho doanh nghiệp.",
        "Lập trình viên Java năng động với kỹ năng lập trình hướng đối tượng vững vàng và kinh nghiệm làm việc chuyên sâu với Spring Boot, REST API, Hibernate. Mong muốn áp dụng chuyên môn kỹ thuật để đồng hành cùng doanh nghiệp xây dựng những giải pháp backend mạnh mẽ, an toàn và hiệu năng cao."
    ],
    "Backend Go": [
        "Kỹ sư Backend chuyên Go (Golang) có hơn 5 năm kinh nghiệm thiết kế và xây dựng các hệ thống dịch vụ microservices chịu tải cao. Đam mê lập trình song song bằng Goroutines & Channels, tối ưu hóa băng thông bằng gRPC/Protobuf và giao tiếp bất đồng bộ qua Kafka/RabbitMQ. Luôn hướng tới việc xây dựng các máy chủ có hiệu năng cực cao, độ trễ thấp và độ tin cậy tuyệt đối.",
        "Lập trình viên Go năng động với tư duy logic tốt và thế mạnh phát triển hệ thống RESTful API hiệu năng cao. Có kinh nghiệm làm việc với Gin-Gonic, GORM, Redis và PostgreSQL. Sẵn sàng học hỏi, nghiên cứu sâu về kiến trúc phân tán và hệ thống chịu tải lớn để giải quyết các bài toán backend thực tế."
    ],
    "Backend Python": [
        "Kỹ sư Backend giàu kinh nghiệm chuyên Python với thế mạnh phát triển các ứng dụng web và API hiệu năng cao sử dụng Django và FastAPI. Có kinh nghiệm phong phú về xử lý tác vụ nền bất đồng bộ với Celery/Redis, tối ưu hóa cơ sở dữ liệu lớn và xây dựng hệ thống thu thập dữ liệu tự động. Luôn hướng tới code sạch, có cấu trúc tốt và tự động hóa quy trình triển khai bằng Docker.",
        "Lập trình viên Python nhiệt huyết với kiến thức vững chắc về Django, FastAPI và lập trình hướng đối tượng. Có tư duy phân tích tốt, kinh nghiệm tích hợp các dịch vụ bên thứ ba và xây dựng cơ sở dữ liệu PostgreSQL. Mong muốn đóng góp kỹ năng kỹ thuật để tạo ra những sản phẩm backend chất lượng cao và phát triển toàn diện bản thân."
    ],
    "DevOps": [
        "Chuyên gia DevOps Engineer giàu kinh nghiệm thiết kế hạ tầng đám mây AWS/GCP tự động hóa toàn diện bằng Terraform và quản trị Kubernetes Cluster quy mô lớn. Am hiểu sâu sắc về triển khai GitOps (ArgoCD), tối ưu hóa đường ống dẫn CI/CD và thiết lập hệ thống giám sát Prometheus/Grafana. Đam mê nâng cao tính ổn định của hệ thống và cắt giảm chi phí hạ tầng.",
        "DevOps Engineer nhiệt huyết với nền tảng quản trị hệ thống Linux vững chắc và kỹ năng tự động hóa bằng Bash/Python scripting. Có kinh nghiệm cấu hình CI/CD Pipelines và Containerization (Docker, K8s). Luôn sẵn sàng giải quyết các thách thức vận hành, giúp tối ưu hóa quy trình triển khai phần mềm liên tục."
    ],
    "QA Automation": [
        "QA Automation Lead có hơn 5 năm kinh nghiệm thiết kế và triển khai các khung kiểm thử tự động (Automation Frameworks) từ con số 0 sử dụng Playwright, Selenium WebDriver. Có thế mạnh về lập kịch bản test API tự động, JMeter test hiệu năng và tích hợp hệ thống CI/CD Jenkins. Luôn cam kết đảm bảo sản phẩm phần mềm phát hành với chất lượng cao nhất.",
        "Kỹ sư QA Automation có kinh nghiệm thiết kế kịch bản test tự động giao diện web/API bằng Python/Java và Selenium. Đam mê tối ưu hóa quy trình kiểm thử và làm việc chặt chẽ với lập trình viên để xác minh lỗi sớm. Mong muốn phát triển kỹ năng chuyên sâu về test hiệu năng hệ thống chịu tải lớn."
    ]
}

AWARDS_POOL = {
    "junior": [
        {"year": "2025", "title": "Học bổng sinh viên đạt thành tích học tập xuất sắc toàn khóa"},
        {"year": "2024", "title": "Giải Ba cuộc thi lập trình thuật toán Olympic Tin học Sinh viên"},
        {"year": "2025", "title": "Giải Nhì cuộc thi Hackathon Sáng tạo Công nghệ trẻ toàn quốc"},
        {"year": "2024", "title": "Danh hiệu Sinh viên 5 Tốt cấp Thành phố với thành tích học tập vượt trội"}
    ],
    "senior": [
        {"year": "2025", "title": "Giải thưởng Dự án xuất sắc nhất năm (Best Project of the Year) tại CMC Global"},
        {"year": "2024", "title": "Nhân viên xuất sắc tiêu biểu (Employee of the Year) tại FPT Software"},
        {"year": "2025", "title": "Giải Nhất cuộc thi Sáng kiến Kỹ thuật và Công nghệ cấp Tập đoàn (Viettel Group)"},
        {"year": "2023", "title": "Chứng nhận Cố vấn kỹ thuật xuất sắc (Outstanding Technical Mentor) của năm"}
    ]
}

CERTIFICATES_POOL = {
    "Backend .NET": [
        {"date": "05/2025", "title": "AWS Certified Solutions Architect - Associate"},
        {"date": "11/2024", "title": "Microsoft Certified: Azure Developer Associate (AZ-204)"},
        {"date": "04/2026", "title": "TOEIC 850 - Chứng chỉ tiếng Anh giao tiếp quốc tế"},
        {"date": "08/2025", "title": "Professional Scrum Master I (PSM I - Scrum.org)"}
    ],
    "Frontend React": [
        {"date": "06/2025", "title": "AWS Certified Cloud Practitioner"},
        {"date": "10/2024", "title": "Meta Front-End Developer Professional Certificate (Coursera)"},
        {"date": "04/2026", "title": "TOEIC 800 - Chứng chỉ tiếng Anh giao tiếp quốc tế"},
        {"date": "09/2025", "title": "React Advanced Concepts & Performance Certification (Frontend Masters)"}
    ],
    "Frontend Vue": [
        {"date": "06/2025", "title": "Certified Vue.js Developer (Vue School)"},
        {"date": "10/2024", "title": "NuxtJS Advanced Web Applications Certification"},
        {"date": "04/2026", "title": "TOEIC 810 - Chứng chỉ tiếng Anh giao tiếp quốc tế"},
        {"date": "09/2025", "title": "AWS Certified Cloud Practitioner"}
    ],
    "Frontend Angular": [
        {"date": "07/2025", "title": "Angular Certified Developer (RxJS & State Management)"},
        {"date": "12/2024", "title": "AWS Certified Cloud Practitioner"},
        {"date": "04/2026", "title": "TOEIC 820 - Chứng chỉ tiếng Anh giao tiếp quốc tế"},
        {"date": "03/2025", "title": "Professional Scrum Master I (PSM I)"}
    ],
    "Mobile Flutter": [
        {"date": "08/2025", "title": "Associate Android Developer Certification (Google)"},
        {"date": "03/2025", "title": "Flutter & Dart Certified Developer (Udemy - Dr. Angela Yu)"},
        {"date": "04/2026", "title": "TOEIC 780 - Chứng chỉ tiếng Anh giao tiếp quốc tế"},
        {"date": "01/2026", "title": "Certified Scrum Product Owner (CSPO)"}
    ],
    "Mobile React Native": [
        {"date": "08/2025", "title": "Meta Android/iOS Developer Professional Certificate"},
        {"date": "03/2025", "title": "React Native Advanced Architecture Certification (Udemy)"},
        {"date": "04/2026", "title": "TOEIC 800 - Chứng chỉ tiếng Anh giao tiếp quốc tế"},
        {"date": "01/2026", "title": "Certified Scrum Master (CSM)"}
    ],
    "Mobile iOS Swift": [
        {"date": "08/2025", "title": "App Development with Swift - Certified User (Apple)"},
        {"date": "03/2025", "title": "iOS Developer Advanced Architecture Certification (Udemy)"},
        {"date": "04/2026", "title": "TOEIC 850 - Chứng chỉ tiếng Anh giao tiếp quốc tế"},
        {"date": "01/2026", "title": "AWS Certified Developer - Associate"}
    ],
    "Mobile Android Kotlin": [
        {"date": "07/2025", "title": "Associate Android Developer Certification (Google)"},
        {"date": "11/2024", "title": "Kotlin Multiplatform Certified Developer (JetBrains)"},
        {"date": "04/2026", "title": "TOEIC 810 - Chứng chỉ tiếng Anh giao tiếp quốc tế"},
        {"date": "02/2025", "title": "Certified Scrum Master (CSM)"}
    ],
    "Data & AI": [
        {"date": "07/2025", "title": "AWS Certified Machine Learning - Specialty"},
        {"date": "12/2024", "title": "Google Cloud Professional Data Engineer"},
        {"date": "04/2026", "title": "TOEIC 880 - Chứng chỉ tiếng Anh giao tiếp quốc tế"},
        {"date": "02/2025", "title": "TensorFlow Developer Certificate (Google)"}
    ],
    "Backend Java": [
        {"date": "06/2025", "title": "Oracle Certified Professional: Java SE 17 Developer"},
        {"date": "10/2024", "title": "Spring Certified Professional (Broadcom)"},
        {"date": "04/2026", "title": "TOEIC 840 - Chứng chỉ tiếng Anh giao tiếp quốc tế"},
        {"date": "09/2025", "title": "AWS Certified Developer - Associate"}
    ],
    "Backend Go": [
        {"date": "06/2025", "title": "Go Advanced Concurrency & Systems Certification (Udemy)"},
        {"date": "10/2024", "title": "AWS Certified Solutions Architect - Associate"},
        {"date": "04/2026", "title": "TOEIC 830 - Chứng chỉ tiếng Anh giao tiếp quốc tế"},
        {"date": "09/2025", "title": "Certified Kubernetes Administrator (CKA)"}
    ],
    "Backend Python": [
        {"date": "08/2025", "title": "Python Institute Certified Professional in Python Programming (PCPP)"},
        {"date": "11/2024", "title": "Meta Back-End Developer Professional Certificate"},
        {"date": "04/2026", "title": "TOEIC 840 - Chứng chỉ tiếng Anh giao tiếp quốc tế"},
        {"date": "02/2025", "title": "AWS Certified Developer - Associate"}
    ],
    "DevOps": [
        {"date": "05/2025", "title": "AWS Certified Solutions Architect - Associate"},
        {"date": "11/2024", "title": "Certified Kubernetes Administrator (CKA - Linux Foundation)"},
        {"date": "04/2026", "title": "TOEIC 820 - Chứng chỉ tiếng Anh giao tiếp quốc tế"},
        {"date": "08/2025", "title": "HashiCorp Certified: Terraform Associate"}
    ],
    "QA Automation": [
        {"date": "07/2025", "title": "ISTQB Advanced Level Test Automation Engineer (CTAL-TAE)"},
        {"date": "12/2024", "title": "Selenium Webdriver Automation Specialist Certification"},
        {"date": "04/2026", "title": "TOEIC 800 - Chứng chỉ tiếng Anh giao tiếp quốc tế"},
        {"date": "03/2025", "title": "Certified Agile Software Tester (CAST)"}
    ]
}

INTERESTS_POOL = [
    "Đọc sách công nghệ, Chạy bộ cự ly dài (Half-Marathon), Tham gia các giải chạy cộng đồng",
    "Đá bóng, Viết blog chia sẻ kiến thức công nghệ trên Viblo, Nghe nhạc không lời khi viết code",
    "Chơi cờ vua rèn luyện tư duy logic, Nhiếp ảnh phong cảnh, Nghiên cứu các xu hướng ứng dụng AI mới",
    "Chơi cầu lông, Xem các phim khoa học viễn tưởng và công nghệ vũ trụ, Học ngoại ngữ mới (Tiếng Nhật)"
]

REFERENCES_POOL = {
    "Backend .NET": [
        "Lê Hoàng Nam - Technical Architect tại FPT Software - SĐT: 0987654321 - Email: namlh@fsoft.com.vn",
        "Trần Văn Hùng - Engineering Manager tại CMC Global - SĐT: 0912345678 - Email: hungtv@cmc.com.vn"
    ],
    "Frontend React": [
        "Nguyễn Thị Lan - Frontend Lead tại VNG Corporation - SĐT: 0976543210 - Email: lannt@vng.com.vn",
        "Phạm Minh Đức - UI/UX Manager tại One Mount Group - SĐT: 0909876543 - Email: ducpm@onemount.com"
    ],
    "Frontend Vue": [
        "Trần Văn Tú - Frontend Architect tại Tiki Corp - SĐT: 0989999888 - Email: tutv@tiki.vn",
        "Nguyễn Thị Ngọc - Lead Frontend tại VNG Corporation - SĐT: 0917777666 - Email: ngocnt@vng.com.vn"
    ],
    "Frontend Angular": [
        "Lê Thị Mai - Frontend Architect tại NAB Innovation Centre - SĐT: 0988111222 - Email: mai.le@nab.com.au",
        "Nguyễn Văn Đức - Engineering Manager tại FPT Software - SĐT: 0911222333 - Email: ducnv@fsoft.com.vn"
    ],
    "Mobile Flutter": [
        "Vũ Minh Tuấn - Mobile Lead tại Tiki Corp - SĐT: 0932123456 - Email: tuanvm@tiki.vn",
        "Đặng Thành Nam - Product Owner tại Shopee Vietnam - SĐT: 0945678901 - Email: namdt@shopee.vn"
    ],
    "Mobile React Native": [
        "Hoàng Minh Cường - Mobile Lead tại One Mount Group - SĐT: 0905555444 - Email: cuonghm@onemount.com",
        "Vũ Tiến Đạt - Engineering Manager tại Tiki Corp - SĐT: 0914444333 - Email: datvt@tiki.vn"
    ],
    "Mobile iOS Swift": [
        "Phạm Minh Tuấn - iOS Tech Lead tại VNG Corporation - SĐT: 0903111222 - Email: tuanpm@vng.com.vn",
        "Trần Thị Lan - Product Manager tại One Mount Group - SĐT: 0914222333 - Email: lantt@onemount.com"
    ],
    "Mobile Android Kotlin": [
        "Vũ Văn Hùng - Mobile Lead tại Viettel Group - SĐT: 0968111222 - Email: hungvv@viettel.com.vn",
        "Đỗ Minh Triết - Technical Director tại KMS Technology - SĐT: 0909222333 - Email: trietdm@kms.com"
    ],
    "Data & AI": [
        "Bùi Thị Trang - Head of AI & Data tại Viettel AI - SĐT: 0967890123 - Email: trangbt@viettel.com.vn",
        "Nguyễn Đức Anh - Giảng viên Khoa CNTT - Đại học Bách Khoa Hà Nội - Email: anhnd@hust.edu.vn"
    ],
    "Backend Java": [
        "Nguyễn Văn Minh - Lead Developer tại Techcombank - SĐT: 0915678901 - Email: minhnv@techcombank.com.vn",
        "Hoàng Minh Quân - Tech Lead tại NashTech Vietnam - SĐT: 0981234567 - Email: quan.hoang@nashtech.com"
    ],
    "Backend Go": [
        "Nguyễn Hoàng Sơn - Technical Architect tại VNG Cloud - SĐT: 0989333444 - Email: sonnh@vng.com.vn",
        "Lê Văn Hùng - Engineering Manager tại Shopee Vietnam - SĐT: 0919444555 - Email: hunglv@shopee.vn"
    ],
    "Backend Python": [
        "Trần Đức Anh - Tech Lead tại Tiki Corp - SĐT: 0938555666 - Email: anhtd@tiki.vn",
        "Nguyễn Thị Phương - Data & AI Director tại FPT Software - Email: phuongnt@fsoft.com.vn"
    ],
    "DevOps": [
        "Đỗ Thành Trung - Cloud Director tại Viettel Cloud - SĐT: 0961234567 - Email: trungdt@viettel.com.vn",
        "Phan Thanh Hà - Infrastructure Architect tại VNG Cloud - SĐT: 0979876543 - Email: hapt@vng.com.vn"
    ],
    "QA Automation": [
        "Lê Thị Thảo - QA Manager tại FPT Software - SĐT: 0984567890 - Email: thaolt@fsoft.com.vn",
        "Trần Minh Trí - QC Director tại KMS Technology - SĐT: 0918765432 - Email: trimt@kms.com"
    ]
}

def generate_candidate_profile(full_name, specialty, level, exp_years, location=None):
    spec_data = SPECIALTIES[specialty]
    email_slug = make_slug(full_name)
    email = f"{email_slug}@{random.choice(['gmail.com', 'outlook.com', 'yahoo.com'])}"
    phone = f"09{random.randint(10000000, 99999999)}"
    if not location:
        location = random.choice(ADDRESSES)
    github = f"github.com/{email_slug}"
    
    # Pick objective based on level
    objective_pool = SUMMARIES.get(specialty, SUMMARIES["Backend .NET"])
    if level in ["SENIOR", "LEADER", "MANAGER"]:
        objective = objective_pool[0]
    else:
        objective = objective_pool[1]
    
    # Skills
    skills = spec_data["skills"]
    
    # Experiences
    job_count = 1
    if exp_years >= 5:
        job_count = 2
    elif exp_years >= 2:
        job_count = 2
        
    experiences = []
    start_year = 2026 - exp_years
    for i in range(job_count):
        company = random.choice(COMPANIES)
        
        # Decide if this job gets senior or junior bullets
        is_newer_job = (i == job_count - 1)
        if is_newer_job and (exp_years >= 3 or level in ["SENIOR", "LEADER", "MANAGER"]):
            exp_tmpl = spec_data["experiences"][1]
        else:
            exp_tmpl = spec_data["experiences"][0]
            
        # Distribute years of experience
        step_years = exp_years // job_count if job_count > 1 else exp_years
        s_yr = start_year + i * step_years
        e_yr = s_yr + step_years
        if e_yr > 2026:
            e_yr = 2026
            
        dates = f"01/{s_yr} - nay" if (is_newer_job) else f"01/{s_yr} - 12/{e_yr}"
        
        if is_newer_job:
            job_title = f"{level} {spec_data['title']}"
        else:
            older_level = "Middle" if level in ["SENIOR", "LEADER", "MANAGER"] else "Junior"
            job_title = f"{older_level} {spec_data['title']}"
            
        experiences.append({
            "company": company,
            "position": job_title,
            "dates": dates,
            "bullets": exp_tmpl["bullets"]
        })
        
    # Projects
    projects = []
    selected_proj = random.sample(spec_data["projects"], min(len(spec_data["projects"]), 2))
    p_dates_list = ["04-05/2026", "03-04/2026", "01-02/2026"]
    for idx, p in enumerate(selected_proj):
        projects.append({
            "name": p["name"],
            "description": p["description"],
            "tags": p["tags"],
            "link": f"https://github.com/{email_slug.replace('.', '-')}/{make_slug(p['name']).replace('.', '-')}",
            "role": specialty.replace("Backend .NET", "Backend Developer").replace("Backend Java", "Backend Developer").replace("Backend Go", "Backend Developer").replace("Backend Python", "Backend Developer").replace("Frontend React", "Frontend Developer").replace("Frontend Vue", "Frontend Developer").replace("Frontend Angular", "Frontend Developer").replace("Mobile Flutter", "Mobile Developer").replace("Mobile React Native", "Mobile Developer").replace("Mobile iOS Swift", "iOS Developer").replace("Mobile Android Kotlin", "Android Developer").replace("Data & AI", "AI & Data Engineer").replace("DevOps", "DevOps Engineer").replace("QA Automation", "QA Automation Engineer"),
            "dates": p_dates_list[idx % len(p_dates_list)]
        })
        
    # Education & dynamic GPA / Classification
    edu_school = random.choice(UNIVERSITIES)
    edu_dates = f"20{26 - exp_years - 4 - 2000} - 20{26 - exp_years - 2000}"
    
    gpa_val = random.uniform(2.7, 3.96)
    if gpa_val >= 3.6:
        gpa_class = "Tốt nghiệp loại Xuất sắc"
    elif gpa_val >= 3.2:
        gpa_class = "Tốt nghiệp loại Giỏi"
    else:
        gpa_class = "Tốt nghiệp loại Khá"
        
    major_pool = {
        "Backend .NET": ["Kỹ thuật phần mềm", "Công nghệ thông tin", "Hệ thống thông tin"],
        "Backend Java": ["Kỹ thuật phần mềm", "Công nghệ thông tin", "Khoa học máy tính"],
        "Backend Go": ["Kỹ thuật phần mềm", "Công nghệ thông tin", "Khoa học máy tính"],
        "Backend Python": ["Công nghệ thông tin", "Khoa học máy tính", "Hệ thống thông tin"],
        "Frontend React": ["Kỹ thuật phần mềm", "Công nghệ thông tin", "Hệ thống thông tin"],
        "Frontend Vue": ["Kỹ thuật phần mềm", "Công nghệ thông tin", "Hệ thống thông tin"],
        "Frontend Angular": ["Kỹ thuật phần mềm", "Công nghệ thông tin", "Hệ thống thông tin"],
        "Mobile Flutter": ["Kỹ thuật phần mềm", "Công nghệ thông tin", "Mạng máy tính & Truyền thông"],
        "Mobile React Native": ["Kỹ thuật phần mềm", "Công nghệ thông tin", "Mạng máy tính & Truyền thông"],
        "Mobile iOS Swift": ["Kỹ thuật phần mềm", "Công nghệ thông tin", "Mạng máy tính & Truyền thông"],
        "Mobile Android Kotlin": ["Kỹ thuật phần mềm", "Công nghệ thông tin", "Mạng máy tính & Truyền thông"],
        "Data & AI": ["Khoa học dữ liệu & Trí tuệ nhân tạo", "Khoa học máy tính", "Hệ thống thông tin"],
        "DevOps": ["Mạng máy tính & Truyền thông", "An toàn thông tin", "Công nghệ thông tin"],
        "QA Automation": ["Kỹ thuật phần mềm", "Công nghệ thông tin", "Hệ thống thông tin"]
    }
    edu_major = random.choice(major_pool.get(specialty, ["Công nghệ thông tin"]))
    
    education = {
        "school": edu_school,
        "major": edu_major,
        "dates": edu_dates,
        "gpa": f"{gpa_val:.2f}",
        "details": gpa_class
    }
    
    # Awards & Certificates
    if exp_years >= 3:
        awards = random.sample(AWARDS_POOL["senior"], 2)
    else:
        awards = random.sample(AWARDS_POOL["junior"], 2)
        
    certificates = random.sample(CERTIFICATES_POOL[specialty], 2)
    interests = random.choice(INTERESTS_POOL)
    reference = random.choice(REFERENCES_POOL[specialty])
    
    return {
        "full_name": full_name,
        "specialty": specialty,
        "level": level,
        "exp_years": exp_years,
        "title": spec_data["title"],
        "email": email,
        "phone": phone,
        "address": location,
        "github": github,
        "objective": objective,
        "skills": skills,
        "experiences": experiences,
        "projects": projects,
        "education": education,
        "awards": awards,
        "certificates": certificates,
        "interests": interests,
        "reference": reference
    }

def remove_accents(text):
    patterns = {
        '[àáảãạăằắẳẵặâầấẩẫậ]': 'a',
        '[èéẻẽẹêềếểễệ]': 'e',
        '[ìíỉĩị]': 'i',
        '[òóỏõọôồốổỗộơờớởỡợ]': 'o',
        '[ùúủũụưừứửữự]': 'u',
        '[ỳýỷỹỵ]': 'y',
        '[đ]': 'd',
        '[ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬ]': 'A',
        '[ÈÉẺẼẸÊỀẾỂỄỆ]': 'E',
        '[ÌÍỈĨỊ]': 'I',
        '[ÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢ]': 'O',
        '[ÙÚỦŨỤƯỪỨỬỮỰ]': 'U',
        '[ÝỲỶỸỴ]': 'Y',
        '[Đ]': 'D'
    }
    for regex, replacement in patterns.items():
        text = re.sub(regex, replacement, text)
    return text

def make_slug(name):
    clean_name = remove_accents(name.lower())
    clean_name = re.sub(r'[^a-z\s]', '', clean_name)
    parts = clean_name.split()
    if not parts:
        return "candidate"
    return ".".join(parts)

# ─── SECTION HEADER WITH LEFT COLOR BORDER (TopCV Style) ──────────────────────
def create_section_header(title, style, color_hex='#b82a38'):
    p = Paragraph(f"<b>{title.upper()}</b>", style)
    t = Table([[p]], colWidths=[175])
    t.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('LINEABOVE', (0,0), (-1,-1), 1.2, colors.HexColor(color_hex)),
        ('LINEBELOW', (0,0), (-1,-1), 1.2, colors.HexColor(color_hex)),
    ]))
    return t

# ─── GENERATE A PDF CV FILE ───────────────────────────────────────────────────
def generate_pdf_cv(output_path, profile):
    from reportlab.platypus import PageBreak
    
    # 1. Setup Document Template
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )
    
    # 2. Setup Styles
    styles = getSampleStyleSheet()
    
    style_name = ParagraphStyle(
        'CrimsonName',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#b82a38')
    )
    
    style_title = ParagraphStyle(
        'CrimsonTitle',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#475569')
    )
    
    style_sec_header = ParagraphStyle(
        'CrimsonSecHeader',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#b82a38')
    )
    
    style_body = ParagraphStyle(
        'CrimsonBody',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1b1c1c')
    )
    
    style_body_bold = ParagraphStyle(
        'CrimsonBodyBold',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1b1c1c')
    )
    
    style_body_gray = ParagraphStyle(
        'CrimsonBodyGray',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#64748b')
    )
    
    style_bullet = ParagraphStyle(
        'CrimsonBullet',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=13,
        leftIndent=10,
        firstLineIndent=-5,
        textColor=colors.HexColor('#1b1c1c')
    )

    story = []
    
    # 👤 Avatar Table: 110 x 110pt grey box
    avatar_cell = Table([[""]], colWidths=[110], rowHeights=[110])
    avatar_cell.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ececec')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # Header Text on the right
    header_text_flowables = [
        Paragraph(profile["full_name"].upper(), style_name),
        Spacer(1, 4),
        Paragraph(f"{profile['level']} {profile['title']}".upper(), style_title),
        Spacer(1, 8),
        Paragraph(profile["objective"], style_body)
    ]
    
    header_table = Table([[avatar_cell, [], header_text_flowables]], colWidths=[110, 20, 425])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Page 1 Grid (3 columns: Contact, Education, Skills)
    # Contact Column
    col1_flowables = [
        create_section_header("THÔNG TIN CÁ NHÂN", style_sec_header),
        Spacer(1, 8),
        Paragraph(f"✉ {profile['email']}", style_body),
        Spacer(1, 4),
        Paragraph(f"📞 {profile['phone']}", style_body),
        Spacer(1, 4),
        Paragraph(f"🌐 {profile['github']}", style_body),
        Spacer(1, 4),
        Paragraph(f"📍 {profile['address']}", style_body)
    ]
    
    # Education Column
    edu = profile["education"]
    col2_flowables = [
        create_section_header("HỌC VẤN", style_sec_header),
        Spacer(1, 8),
        Paragraph(f"<b>{edu['school']}</b>", style_body_bold),
        Paragraph(edu['major'], style_body),
        Paragraph(edu['dates'], style_body_gray),
        Spacer(1, 4),
        Paragraph(f"• GPA: {edu['gpa']}", style_body),
        Paragraph(f"• {edu['details']}", style_body)
    ]
    
    # Skills Column
    col3_flowables = [
        create_section_header("KỸ NĂNG", style_sec_header),
        Spacer(1, 8)
    ]
    for g in profile["skills"]:
        col3_flowables.append(Paragraph(f"<b>{g['category']}</b>", style_body_bold))
        col3_flowables.append(Spacer(1, 2))
        for item in g["items"]:
            col3_flowables.append(Paragraph(f"• {item}", style_bullet))
        col3_flowables.append(Spacer(1, 6))
        
    grid_table = Table([[col1_flowables, [], col2_flowables, [], col3_flowables]], colWidths=[175, 15, 175, 15, 175])
    grid_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(grid_table)
    story.append(PageBreak())

    # Page 2 content (KINH NGHIỆM LÀM VIỆC & DỰ ÁN - part 1)
    p2_rows = []
    
    # ─── KINH NGHIỆM LÀM VIỆC ───
    p2_rows.append([
        create_section_header("KINH NGHIỆM LÀM VIỆC", style_sec_header),
        [],
        []
    ])
    
    for job in profile["experiences"]:
        job_left = [
            Paragraph(job['dates'], style_body_bold),
            Paragraph(job['company'], style_body_gray)
        ]
        
        job_right = [
            Paragraph(job['position'], style_body_bold),
            Spacer(1, 4)
        ]
        for bullet in job["bullets"]:
            job_right.append(Paragraph(f"• {bullet}", style_bullet))
            
        p2_rows.append([job_left, [], job_right])
        
    p2_rows.append([Spacer(1, 10), [], Spacer(1, 10)])
    
    # ─── DỰ ÁN ───
    p2_rows.append([
        create_section_header("DỰ ÁN", style_sec_header),
        [],
        []
    ])
    
    proj1 = profile["projects"][0]
    proj1_left = [
        Paragraph(proj1['dates'], style_body_bold),
        Paragraph(proj1['name'], style_body_gray)
    ]
    proj1_right = [
        Paragraph(proj1['role'], style_body_bold),
        Spacer(1, 4),
        Paragraph(f"• Mô tả: {proj1['description']}", style_body),
        Spacer(1, 2),
        Paragraph(f"• Công nghệ: {', '.join(proj1['tags'])}", style_body),
        Spacer(1, 2),
        Paragraph(f"• Link: <font color='#b82a38'><u>{proj1['link']}</u></font>", style_body)
    ]
    p2_rows.append([proj1_left, [], proj1_right])
    
    page2_table = Table(p2_rows, colWidths=[175, 20, 360])
    page2_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(page2_table)
    story.append(PageBreak())

    # Page 3 content (DỰ ÁN part 2, CHỨNG CHỈ, DANH HIỆU, SỞ THÍCH, NGƯỜI GIỚI THIỆU)
    p3_rows = []
    
    if len(profile["projects"]) > 1:
        proj2 = profile["projects"][1]
        proj2_left = [
            Paragraph(proj2['dates'], style_body_bold),
            Paragraph(proj2['name'], style_body_gray)
        ]
        proj2_right = [
            Paragraph(proj2['role'], style_body_bold),
            Spacer(1, 4),
            Paragraph(f"• Mô tả: {proj2['description']}", style_body),
            Spacer(1, 2),
            Paragraph(f"• Công nghệ: {', '.join(proj2['tags'])}", style_body),
            Spacer(1, 2),
            Paragraph(f"• Link: <font color='#b82a38'><u>{proj2['link']}</u></font>", style_body)
        ]
        p3_rows.append([proj2_left, [], proj2_right])
        p3_rows.append([Spacer(1, 10), [], Spacer(1, 10)])
        
    # ─── CHỨNG CHỈ ───
    p3_rows.append([
        create_section_header("CHỨNG CHỈ", style_sec_header),
        [],
        []
    ])
    cert_left = []
    cert_right = []
    for c in profile["certificates"]:
        cert_left.append(Paragraph(c['date'], style_body_bold))
        cert_left.append(Spacer(1, 4))
        cert_right.append(Paragraph(c['title'], style_body))
        cert_right.append(Spacer(1, 4))
    p3_rows.append([cert_left, [], cert_right])
    p3_rows.append([Spacer(1, 10), [], Spacer(1, 10)])
    
    # ─── DANH HIỆU VÀ GIẢI THƯỞNG ───
    p3_rows.append([
        create_section_header("DANH HIỆU VÀ GIẢI THƯỞNG", style_sec_header),
        [],
        []
    ])
    award_left = []
    award_right = []
    for a in profile["awards"]:
        award_left.append(Paragraph(a['year'], style_body_bold))
        award_left.append(Spacer(1, 4))
        award_right.append(Paragraph(a['title'], style_body))
        award_right.append(Spacer(1, 4))
    p3_rows.append([award_left, [], award_right])
    p3_rows.append([Spacer(1, 10), [], Spacer(1, 10)])
    
    # ─── SỞ THÍCH ───
    p3_rows.append([
        create_section_header("SỞ THÍCH", style_sec_header),
        [],
        []
    ])
    p3_rows.append([[], [], Paragraph(profile["interests"], style_body)])
    p3_rows.append([Spacer(1, 10), [], Spacer(1, 10)])
    
    # ─── NGƯỜI GIỚI THIỆU ───
    p3_rows.append([
        create_section_header("NGƯỜI GIỚI THIỆU", style_sec_header),
        [],
        []
    ])
    p3_rows.append([[], [], Paragraph(profile["reference"], style_body)])
    
    page3_table = Table(p3_rows, colWidths=[175, 20, 360])
    page3_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(page3_table)
    
    # 3. Build Document
    doc.build(story)


# ─── SECTION HEADER FOR TWO-COLUMN (Orange Underline) ──────────────────────────
def create_right_section_header(title, style):
    p = Paragraph(f"<b>{title.upper()}</b>", style)
    t = Table([[p]], colWidths=[325])
    t.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#ec8f00')),
    ]))
    return t

# ─── GENERATE A TWO-COLUMN SIDEBAR PDF CV ─────────────────────────────────────
def generate_pdf_cv_two_column(output_path, profile):
    from reportlab.platypus import PageBreak
    
    # 1. Setup Document Template (Total printable width: 595 - 70 = 525pt)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=35,
        bottomMargin=35
    )
    
    # 2. Setup Styles
    styles = getSampleStyleSheet()
    
    # Left Sidebar styles
    style_sb_header = ParagraphStyle(
        'SBHeader',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#ec8f00')
    )
    style_sb_text = ParagraphStyle(
        'SBText',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#ffffff')
    )
    style_sb_bullet = ParagraphStyle(
        'SBBullet',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=11,
        leftIndent=10,
        firstLineIndent=-5,
        textColor=colors.HexColor('#ffffff')
    )
    
    # Right Main column styles
    style_name = ParagraphStyle(
        'NameStyle2Col',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#ffffff') # Name is inside sidebar (dark background)
    )
    style_title = ParagraphStyle(
        'TitleStyle2Col',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=11.5,
        leading=14.5,
        textColor=colors.HexColor('#ec8f00') # Title under name inside sidebar
    )
    style_right_header = ParagraphStyle(
        'RightHeader',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor('#ec8f00')
    )
    style_body = ParagraphStyle(
        'BodyStyle2Col',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1b1c1c')
    )
    style_bullet = ParagraphStyle(
        'BulletStyle2Col',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=13,
        leftIndent=12,
        firstLineIndent=-6,
        textColor=colors.HexColor('#1b1c1c')
    )
    style_subhead_left = ParagraphStyle(
        'SubheadLeft2Col',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor('#1b1c1c')
    )
    style_subhead_right = ParagraphStyle(
        'SubheadRight2Col',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontStyle='Italic',
        fontSize=8.5,
        leading=12,
        alignment=2,
        textColor=colors.HexColor('#64748b')
    )

    # 3. Left Sidebar Content - PAGE 1
    left_flowables_p1 = []
    left_flowables_p1.append(Paragraph(profile["full_name"].upper(), style_name))
    left_flowables_p1.append(Spacer(1, 4))
    left_flowables_p1.append(Paragraph(f"{profile['level']} {profile['title']}".upper(), style_title))
    left_flowables_p1.append(Spacer(1, 15))
    
    left_flowables_p1.append(Paragraph("<b>THÔNG TIN CÁ NHÂN</b>", style_sb_header))
    left_flowables_p1.append(Spacer(1, 4))
    left_flowables_p1.append(Paragraph(f"✉ {profile['email']}", style_sb_text))
    left_flowables_p1.append(Spacer(1, 4))
    left_flowables_p1.append(Paragraph(f"📞 {profile['phone']}", style_sb_text))
    left_flowables_p1.append(Spacer(1, 4))
    left_flowables_p1.append(Paragraph(f"📍 {profile['address']}", style_sb_text))
    left_flowables_p1.append(Spacer(1, 4))
    left_flowables_p1.append(Paragraph(f"🌐 {profile['github']}", style_sb_text))
    left_flowables_p1.append(Spacer(1, 15))
    
    left_flowables_p1.append(Paragraph("<b>KỸ NĂNG</b>", style_sb_header))
    left_flowables_p1.append(Spacer(1, 4))
    for g in profile["skills"][:2]:
        left_flowables_p1.append(Paragraph(f"<b>{g['category']}</b>", style_sb_text))
        left_flowables_p1.append(Spacer(1, 2))
        for item in g["items"]:
            left_flowables_p1.append(Paragraph(f"• {item}", style_sb_bullet))
        left_flowables_p1.append(Spacer(1, 6))

    # Left Sidebar Content - PAGE 2
    left_flowables_p2 = []
    left_flowables_p2.append(Paragraph("<b>KỸ NĂNG (TIẾP)</b>", style_sb_header))
    left_flowables_p2.append(Spacer(1, 4))
    for g in profile["skills"][2:]:
        left_flowables_p2.append(Paragraph(f"<b>{g['category']}</b>", style_sb_text))
        left_flowables_p2.append(Spacer(1, 2))
        for item in g["items"]:
            left_flowables_p2.append(Paragraph(f"• {item}", style_sb_bullet))
        left_flowables_p2.append(Spacer(1, 6))
        
    left_flowables_p2.append(Spacer(1, 10))
    left_flowables_p2.append(Paragraph("<b>SỞ THÍCH</b>", style_sb_header))
    left_flowables_p2.append(Spacer(1, 4))
    for interest_item in profile["interests"].split(", "):
        left_flowables_p2.append(Paragraph(f"• {interest_item}", style_sb_bullet))
    left_flowables_p2.append(Spacer(1, 15))
    
    left_flowables_p2.append(Paragraph("<b>NGƯỜI GIỚI THIỆU</b>", style_sb_header))
    left_flowables_p2.append(Spacer(1, 4))
    left_flowables_p2.append(Paragraph(profile["reference"], style_sb_text))

    # 4. Right Main Column Content - PAGE 1
    right_flowables_p1 = []
    
    right_flowables_p1.append(create_right_section_header("MỤC TIÊU NGHỀ NGHIỆP", style_right_header))
    right_flowables_p1.append(Spacer(1, 6))
    right_flowables_p1.append(Paragraph(profile["objective"], style_body))
    right_flowables_p1.append(Spacer(1, 12))
    
    right_flowables_p1.append(create_right_section_header("KINH NGHIỆM LÀM VIỆC", style_right_header))
    right_flowables_p1.append(Spacer(1, 6))
    for job in profile["experiences"]:
        job_table = Table([[
            Paragraph(f"<b>{job['position']}</b>", style_subhead_left),
            Paragraph(job['dates'], style_subhead_right)
        ]], colWidths=[225, 100])
        job_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        
        job_story = [
            job_table,
            Paragraph(job['company'], style_body),
            Spacer(1, 2)
        ]
        for bullet in job["bullets"][:4]:
            job_story.append(Paragraph(f"• {bullet}", style_bullet))
        job_story.append(Spacer(1, 8))
        right_flowables_p1.extend(job_story)
        
    right_flowables_p1.append(Spacer(1, 5))
    
    right_flowables_p1.append(create_right_section_header("HỌC VẤN", style_right_header))
    right_flowables_p1.append(Spacer(1, 6))
    edu = profile["education"]
    edu_table = Table([[
        Paragraph(f"<b>{edu['major']}</b>", style_subhead_left),
        Paragraph(edu['dates'], style_subhead_right)
    ]], colWidths=[240, 85])
    edu_table.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    edu_story = [
        edu_table,
        Paragraph(edu['school'], style_body),
        Spacer(1, 2),
        Paragraph(f"• GPA: {edu['gpa']} - {edu['details']}", style_body)
    ]
    right_flowables_p1.extend(edu_story)
    right_flowables_p1.append(Spacer(1, 12))
    
    right_flowables_p1.append(create_right_section_header("DANH HIỆU VÀ GIẢI THƯỞNG", style_right_header))
    right_flowables_p1.append(Spacer(1, 6))
    award_table_data = []
    for a in profile["awards"]:
        award_table_data.append([
            Paragraph(f"<b>{a['year']}</b>", style_body),
            Paragraph(a['title'], style_body)
        ])
    award_table = Table(award_table_data, colWidths=[50, 275])
    award_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    right_flowables_p1.append(award_table)
    right_flowables_p1.append(Spacer(1, 12))
    
    right_flowables_p1.append(create_right_section_header("CHỨNG CHỈ", style_right_header))
    right_flowables_p1.append(Spacer(1, 6))
    cert_table_data = []
    for c in profile["certificates"]:
        cert_table_data.append([
            Paragraph(f"<b>{c['date']}</b>", style_body),
            Paragraph(c['title'], style_body)
        ])
    cert_table = Table(cert_table_data, colWidths=[60, 265])
    cert_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    right_flowables_p1.append(cert_table)

    # Right Main Column Content - PAGE 2
    right_flowables_p2 = []
    right_flowables_p2.append(create_right_section_header("DỰ ÁN", style_right_header))
    right_flowables_p2.append(Spacer(1, 6))
    for p in profile["projects"]:
        p_table = Table([[
            Paragraph(f"<b>{p['name']}</b>", style_subhead_left),
            Paragraph(p['dates'], style_subhead_right)
        ]], colWidths=[225, 100])
        p_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        proj_story = [
            p_table,
            Paragraph(f"<b>{p['role']}</b>", style_body),
            Spacer(1, 2),
            Paragraph(f"• Mô tả: {p['description']}", style_body),
            Spacer(1, 2),
            Paragraph(f"• Công nghệ sử dụng: {', '.join(p['tags'])}", style_body),
            Spacer(1, 2),
            Paragraph(f"• Link dự án: <font color='#ec8f00'><u>{p['link']}</u></font>", style_body),
            Spacer(1, 10)
        ]
        right_flowables_p2.extend(proj_story)
        
    # 5. Composite Outer Table Layout (Left column width: 145, Right: 360, Gap: 20)
    outer_table_p1 = Table([[left_flowables_p1, [], right_flowables_p1]], colWidths=[145, 20, 360])
    outer_table_p1.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    
    outer_table_p2 = Table([[left_flowables_p2, [], right_flowables_p2]], colWidths=[145, 20, 360])
    outer_table_p2.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    
    def draw_sidebar_background(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#353a3d'))
        canvas.rect(0, 0, 190, 842, fill=1, stroke=0)
        canvas.restoreState()
        
    doc.build([outer_table_p1, PageBreak(), outer_table_p2], onFirstPage=draw_sidebar_background, onLaterPages=draw_sidebar_background)


# ─── GENERATE A PDF CV FILE - TEMPLATE 3 (Teal, 3 Pages) ──────────────────────
def generate_pdf_cv_template_3(output_path, profile):
    from reportlab.platypus import PageBreak
    
    # 1. Setup Document Template
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )
    
    # 2. Setup Styles
    styles = getSampleStyleSheet()
    
    style_name = ParagraphStyle(
        'TealName',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0D4559')
    )
    
    style_title = ParagraphStyle(
        'TealTitle',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#475569')
    )
    
    style_sec_header = ParagraphStyle(
        'TealSecHeader',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0D4559')
    )
    
    style_body = ParagraphStyle(
        'TealBody',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1b1c1c')
    )
    
    style_body_bold = ParagraphStyle(
        'TealBodyBold',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1b1c1c')
    )
    
    style_body_gray = ParagraphStyle(
        'TealBodyGray',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#64748b')
    )
    
    style_bullet = ParagraphStyle(
        'TealBullet',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=13,
        leftIndent=10,
        firstLineIndent=-5,
        textColor=colors.HexColor('#1b1c1c')
    )

    story = []
    
    # 👤 Avatar Table: 110 x 110pt grey box
    avatar_cell = Table([[""]], colWidths=[110], rowHeights=[110])
    avatar_cell.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ececec')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # Header Text on the right
    header_text_flowables = [
        Paragraph(profile["full_name"].upper(), style_name),
        Spacer(1, 4),
        Paragraph(f"{profile['level']} {profile['title']}".upper(), style_title),
        Spacer(1, 8),
        Paragraph(profile["objective"], style_body)
    ]
    
    header_table = Table([[avatar_cell, [], header_text_flowables]], colWidths=[110, 20, 425])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Page 1 Grid (3 columns: Contact, Education, Skills)
    # Contact Column
    col1_flowables = [
        create_section_header("THÔNG TIN CÁ NHÂN", style_sec_header, color_hex='#0D4559'),
        Spacer(1, 8),
        Paragraph(f"✉ {profile['email']}", style_body),
        Spacer(1, 4),
        Paragraph(f"📞 {profile['phone']}", style_body),
        Spacer(1, 4),
        Paragraph(f"🌐 {profile['github']}", style_body),
        Spacer(1, 4),
        Paragraph(f"📍 {profile['address']}", style_body)
    ]
    
    # Education Column
    edu = profile["education"]
    col2_flowables = [
        create_section_header("HỌC VẤN", style_sec_header, color_hex='#0D4559'),
        Spacer(1, 8),
        Paragraph(f"<b>{edu['school']}</b>", style_body_bold),
        Paragraph(edu['major'], style_body),
        Paragraph(edu['dates'], style_body_gray),
        Spacer(1, 4),
        Paragraph(f"• GPA: {edu['gpa']}", style_body),
        Paragraph(f"• {edu['details']}", style_body)
    ]
    
    # Skills Column
    col3_flowables = [
        create_section_header("KỸ NĂNG", style_sec_header, color_hex='#0D4559'),
        Spacer(1, 8)
    ]
    for g in profile["skills"]:
        col3_flowables.append(Paragraph(f"<b>{g['category']}</b>", style_body_bold))
        col3_flowables.append(Spacer(1, 2))
        for item in g["items"]:
            col3_flowables.append(Paragraph(f"• {item}", style_bullet))
        col3_flowables.append(Spacer(1, 6))
        
    grid_table = Table([[col1_flowables, [], col2_flowables, [], col3_flowables]], colWidths=[175, 15, 175, 15, 175])
    grid_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(grid_table)
    story.append(PageBreak())

    # Page 2 content (KINH NGHIỆM LÀM VIỆC & DỰ ÁN - part 1)
    p2_rows = []
    
    # ─── KINH NGHIỆM LÀM VIỆC ───
    p2_rows.append([
        create_section_header("KINH NGHIỆM LÀM VIỆC", style_sec_header, color_hex='#0D4559'),
        [],
        []
    ])
    
    for job in profile["experiences"]:
        job_left = [
            Paragraph(job['dates'], style_body_bold),
            Paragraph(job['company'], style_body_gray)
        ]
        
        job_right = [
            Paragraph(job['position'], style_body_bold),
            Spacer(1, 4)
        ]
        for bullet in job["bullets"]:
            job_right.append(Paragraph(f"• {bullet}", style_bullet))
            
        p2_rows.append([job_left, [], job_right])
        
    p2_rows.append([Spacer(1, 10), [], Spacer(1, 10)])
    
    # ─── DỰ ÁN ───
    p2_rows.append([
        create_section_header("DỰ ÁN", style_sec_header, color_hex='#0D4559'),
        [],
        []
    ])
    
    proj1 = profile["projects"][0]
    proj1_left = [
        Paragraph(proj1['dates'], style_body_bold),
        Paragraph(proj1['name'], style_body_gray)
    ]
    proj1_right = [
        Paragraph(proj1['role'], style_body_bold),
        Spacer(1, 4),
        Paragraph(f"• Mô tả: {proj1['description']}", style_body),
        Spacer(1, 2),
        Paragraph(f"• Công nghệ: {', '.join(proj1['tags'])}", style_body),
        Spacer(1, 2),
        Paragraph(f"• Link: <font color='#0D4559'><u>{proj1['link']}</u></font>", style_body)
    ]
    p2_rows.append([proj1_left, [], proj1_right])
    
    page2_table = Table(p2_rows, colWidths=[175, 20, 360])
    page2_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(page2_table)
    story.append(PageBreak())

    # Page 3 content (DỰ ÁN part 2, CHỨNG CHỈ, DANH HIỆU, SỞ THÍCH, NGƯỜI GIỚI THIỆU)
    p3_rows = []
    
    if len(profile["projects"]) > 1:
        proj2 = profile["projects"][1]
        proj2_left = [
            Paragraph(proj2['dates'], style_body_bold),
            Paragraph(proj2['name'], style_body_gray)
        ]
        proj2_right = [
            Paragraph(proj2['role'], style_body_bold),
            Spacer(1, 4),
            Paragraph(f"• Mô tả: {proj2['description']}", style_body),
            Spacer(1, 2),
            Paragraph(f"• Công nghệ: {', '.join(proj2['tags'])}", style_body),
            Spacer(1, 2),
            Paragraph(f"• Link: <font color='#0D4559'><u>{proj2['link']}</u></font>", style_body)
        ]
        p3_rows.append([proj2_left, [], proj2_right])
        p3_rows.append([Spacer(1, 10), [], Spacer(1, 10)])
        
    # ─── CHỨNG CHỈ ───
    p3_rows.append([
        create_section_header("CHỨNG CHỈ", style_sec_header, color_hex='#0D4559'),
        [],
        []
    ])
    cert_left = []
    cert_right = []
    for c in profile["certificates"]:
        cert_left.append(Paragraph(c['date'], style_body_bold))
        cert_left.append(Spacer(1, 4))
        cert_right.append(Paragraph(c['title'], style_body))
        cert_right.append(Spacer(1, 4))
    p3_rows.append([cert_left, [], cert_right])
    p3_rows.append([Spacer(1, 10), [], Spacer(1, 10)])
    
    # ─── DANH HIỆU VÀ GIẢI THƯỞNG ───
    p3_rows.append([
        create_section_header("DANH HIỆU VÀ GIẢI THƯỞNG", style_sec_header, color_hex='#0D4559'),
        [],
        []
    ])
    award_left = []
    award_right = []
    for a in profile["awards"]:
        award_left.append(Paragraph(a['year'], style_body_bold))
        award_left.append(Spacer(1, 4))
        award_right.append(Paragraph(a['title'], style_body))
        award_right.append(Spacer(1, 4))
    p3_rows.append([award_left, [], award_right])
    p3_rows.append([Spacer(1, 10), [], Spacer(1, 10)])
    
    # ─── SỞ THÍCH ───
    p3_rows.append([
        create_section_header("SỞ THÍCH", style_sec_header, color_hex='#0D4559'),
        [],
        []
    ])
    p3_rows.append([[], [], Paragraph(profile["interests"], style_body)])
    p3_rows.append([Spacer(1, 10), [], Spacer(1, 10)])
    
    # ─── NGƯỜI GIỚI THIỆU ───
    p3_rows.append([
        create_section_header("NGƯỜI GIỚI THIỆU", style_sec_header, color_hex='#0D4559'),
        [],
        []
    ])
    p3_rows.append([[], [], Paragraph(profile["reference"], style_body)])
    
    page3_table = Table(p3_rows, colWidths=[175, 20, 360])
    page3_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(page3_table)
    
    # 3. Build Document
    def draw_t3_meta(canvas, doc):
        canvas.setTitle("Template 3")
    doc.build(story, onFirstPage=draw_t3_meta)


# ─── GENERATE A PDF CV FILE - TEMPLATE 4 (Slate Blue, 4 Pages) ────────────────
def generate_pdf_cv_template_4(output_path, profile):
    from reportlab.platypus import PageBreak
    
    # 1. Setup Document Template
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=35,
        bottomMargin=35
    )
    
    # 2. Setup Styles
    styles = getSampleStyleSheet()
    
    THEME_COLOR = '#263A4D'
    
    # Sidebar styles (white background sidebar, dark text)
    style_sb_header = ParagraphStyle(
        'T4SBHeader',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor(THEME_COLOR)
    )
    style_sb_text = ParagraphStyle(
        'T4SBText',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1b1c1c')
    )
    style_sb_bullet = ParagraphStyle(
        'T4SBBullet',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=11,
        leftIndent=10,
        firstLineIndent=-5,
        textColor=colors.HexColor('#1b1c1c')
    )
    
    # Right Main column styles
    style_name = ParagraphStyle(
        'T4NameStyle',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=22,
        leading=26,
        textColor=colors.HexColor(THEME_COLOR)
    )
    style_title = ParagraphStyle(
        'T4TitleStyle',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=11.5,
        leading=14.5,
        textColor=colors.HexColor('#475569')
    )
    style_right_header = ParagraphStyle(
        'T4RightHeader',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor(THEME_COLOR)
    )
    style_body = ParagraphStyle(
        'T4BodyStyle',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1b1c1c')
    )
    style_bullet = ParagraphStyle(
        'T4BulletStyle',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=13,
        leftIndent=12,
        firstLineIndent=-6,
        textColor=colors.HexColor('#1b1c1c')
    )
    style_subhead_left = ParagraphStyle(
        'T4SubheadLeft',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor('#1b1c1c')
    )
    style_subhead_right = ParagraphStyle(
        'T4SubheadRight',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8.5,
        leading=12,
        alignment=2,
        textColor=colors.HexColor('#64748b')
    )

    def create_t4_section_header(title):
        p = Paragraph(f"<b>{title.upper()}</b>", style_right_header)
        t = Table([[p]], colWidths=[265])
        t.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor(THEME_COLOR)),
        ]))
        return t

    def create_t4_sidebar_header(title):
        p = Paragraph(f"<b>{title.upper()}</b>", style_sb_header)
        t = Table([[p]], colWidths=[240])
        t.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('LINEBELOW', (0,0), (-1,-1), 1.2, colors.HexColor(THEME_COLOR)),
        ]))
        return t

    # Page 1 Left
    left_flowables_p1 = [
        Paragraph(profile["full_name"].upper(), style_name),
        Spacer(1, 4),
        Paragraph(f"{profile['level']} {profile['title']}".upper(), style_title),
        Spacer(1, 15),
        create_t4_sidebar_header("THÔNG TIN CÁ NHÂN"),
        Spacer(1, 6),
        Paragraph(f"✉ {profile['email']}", style_sb_text),
        Spacer(1, 4),
        Paragraph(f"📞 {profile['phone']}", style_sb_text),
        Spacer(1, 4),
        Paragraph(f"📍 {profile['address']}", style_sb_text),
        Spacer(1, 4),
        Paragraph(f"🌐 {profile['github']}", style_sb_text),
        Spacer(1, 15),
        create_t4_sidebar_header("MỤC TIÊU NGHỀ NGHIỆP"),
        Spacer(1, 6),
        Paragraph(profile["objective"], style_sb_text),
        Spacer(1, 15),
        create_t4_sidebar_header("KỸ NĂNG"),
        Spacer(1, 6)
    ]
    if len(profile["skills"]) > 0:
        g = profile["skills"][0]
        left_flowables_p1.append(Paragraph(f"<b>{g['category']}</b>", style_sb_text))
        left_flowables_p1.append(Spacer(1, 2))
        for item in g["items"]:
            left_flowables_p1.append(Paragraph(f"• {item}", style_sb_bullet))
            
    # Page 1 Right
    right_flowables_p1 = [
        create_t4_section_header("HỌC VẤN"),
        Spacer(1, 6)
    ]
    edu = profile["education"]
    edu_table = Table([[
        Paragraph(f"<b>{edu['major']}</b>", style_subhead_left),
        Paragraph(edu['dates'], style_subhead_right)
    ]], colWidths=[180, 85])
    edu_table.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    right_flowables_p1.extend([
        edu_table,
        Paragraph(edu['school'], style_body),
        Spacer(1, 2),
        Paragraph(f"• GPA: {edu['gpa']} - {edu['details']}", style_body),
        Spacer(1, 15),
        create_t4_section_header("KINH NGHIỆM LÀM VIỆC"),
        Spacer(1, 6)
    ])
    if len(profile["experiences"]) > 0:
        job = profile["experiences"][0]
        job_table = Table([[
            Paragraph(f"<b>{job['position']}</b>", style_subhead_left),
            Paragraph(job['dates'], style_subhead_right)
        ]], colWidths=[165, 100])
        job_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        right_flowables_p1.extend([
            job_table,
            Paragraph(job['company'], style_body),
            Spacer(1, 2)
        ])
        for bullet in job["bullets"]:
            right_flowables_p1.append(Paragraph(f"• {bullet}", style_bullet))

    # Page 2 Left
    left_flowables_p2 = [
        create_t4_sidebar_header("KỸ NĂNG (TIẾP)"),
        Spacer(1, 6)
    ]
    for g in profile["skills"][1:]:
        left_flowables_p2.append(Paragraph(f"<b>{g['category']}</b>", style_sb_text))
        left_flowables_p2.append(Spacer(1, 2))
        for item in g["items"]:
            left_flowables_p2.append(Paragraph(f"• {item}", style_sb_bullet))
        left_flowables_p2.append(Spacer(1, 6))
        
    left_flowables_p2.extend([
        Spacer(1, 10),
        create_t4_sidebar_header("SỞ THÍCH"),
        Spacer(1, 6)
    ])
    for interest_item in profile["interests"].split(", "):
        left_flowables_p2.append(Paragraph(f"• {interest_item}", style_sb_bullet))
        
    left_flowables_p2.extend([
        Spacer(1, 10),
        create_t4_sidebar_header("NGƯỜI GIỚI THIỆU"),
        Spacer(1, 6),
        Paragraph(profile["reference"], style_sb_text)
    ])
    
    # Page 2 Right
    right_flowables_p2 = []
    if len(profile["experiences"]) > 1:
        right_flowables_p2.extend([
            create_t4_section_header("KINH NGHIỆM LÀM VIỆC (TIẾP)"),
            Spacer(1, 6)
        ])
        job = profile["experiences"][1]
        job_table = Table([[
            Paragraph(f"<b>{job['position']}</b>", style_subhead_left),
            Paragraph(job['dates'], style_subhead_right)
        ]], colWidths=[165, 100])
        job_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        right_flowables_p2.extend([
            job_table,
            Paragraph(job['company'], style_body),
            Spacer(1, 2)
        ])
        for bullet in job["bullets"]:
            right_flowables_p2.append(Paragraph(f"• {bullet}", style_bullet))
        right_flowables_p2.append(Spacer(1, 15))
        
    right_flowables_p2.extend([
        create_t4_section_header("DỰ ÁN"),
        Spacer(1, 6)
    ])
    proj1 = profile["projects"][0]
    p_table1 = Table([[
        Paragraph(f"<b>{proj1['name']}</b>", style_subhead_left),
        Paragraph(proj1['dates'], style_subhead_right)
    ]], colWidths=[165, 100])
    p_table1.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    right_flowables_p2.extend([
        p_table1,
        Paragraph(f"<b>{proj1['role']}</b>", style_body),
        Spacer(1, 2),
        Paragraph(f"• Mô tả: {proj1['description']}", style_body),
        Spacer(1, 2),
        Paragraph(f"• Công nghệ: {', '.join(proj1['tags'])}", style_body),
        Spacer(1, 2),
        Paragraph(f"• Link: <font color='{THEME_COLOR}'><u>{proj1['link']}</u></font>", style_body)
    ])

    # Page 3 Left
    left_flowables_p3 = []
    
    # Page 3 Right
    right_flowables_p3 = []
    if len(profile["projects"]) > 1:
        proj2 = profile["projects"][1]
        p_table2 = Table([[
            Paragraph(f"<b>{proj2['name']}</b>", style_subhead_left),
            Paragraph(proj2['dates'], style_subhead_right)
        ]], colWidths=[165, 100])
        p_table2.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        right_flowables_p3.extend([
            p_table2,
            Paragraph(f"<b>{proj2['role']}</b>", style_body),
            Spacer(1, 2),
            Paragraph(f"• Mô tả: {proj2['description']}", style_body),
            Spacer(1, 2),
            Paragraph(f"• Công nghệ: {', '.join(proj2['tags'])}", style_body),
            Spacer(1, 2),
            Paragraph(f"• Link: <font color='{THEME_COLOR}'><u>{proj2['link']}</u></font>", style_body),
            Spacer(1, 15)
        ])
        
    right_flowables_p3.extend([
        create_t4_section_header("CHỨNG CHỈ"),
        Spacer(1, 6)
    ])
    if len(profile["certificates"]) > 0:
        c = profile["certificates"][0]
        c_table = Table([[
            Paragraph(f"<b>{c['title']}</b>", style_subhead_left),
            Paragraph(c['date'], style_subhead_right)
        ]], colWidths=[195, 70])
        c_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        right_flowables_p3.append(c_table)

    # Page 4 Left
    left_flowables_p4 = []
    
    # Page 4 Right
    right_flowables_p4 = []
    if len(profile["certificates"]) > 1:
        c = profile["certificates"][1]
        c_table = Table([[
            Paragraph(f"<b>{c['title']}</b>", style_subhead_left),
            Paragraph(c['date'], style_subhead_right)
        ]], colWidths=[195, 70])
        c_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        right_flowables_p4.extend([
            c_table,
            Spacer(1, 15)
        ])
        
    right_flowables_p4.extend([
        create_t4_section_header("DANH HIỆU VÀ GIẢI THƯỞNG"),
        Spacer(1, 6)
    ])
    for a in profile["awards"]:
        a_table = Table([[
            Paragraph(f"<b>{a['title']}</b>", style_subhead_left),
            Paragraph(a['year'], style_subhead_right)
        ]], colWidths=[205, 60])
        a_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        right_flowables_p4.extend([
            a_table,
            Spacer(1, 4)
        ])

    outer_table_p1 = Table([[left_flowables_p1, [], right_flowables_p1]], colWidths=[240, 20, 265])
    outer_table_p1.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    
    outer_table_p2 = Table([[left_flowables_p2, [], right_flowables_p2]], colWidths=[240, 20, 265])
    outer_table_p2.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    
    outer_table_p3 = Table([[left_flowables_p3, [], right_flowables_p3]], colWidths=[240, 20, 265])
    outer_table_p3.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    
    outer_table_p4 = Table([[left_flowables_p4, [], right_flowables_p4]], colWidths=[240, 20, 265])
    outer_table_p4.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    
    def draw_t4_line(canvas, doc):
        canvas.saveState()
        canvas.setTitle("Template 4")
        canvas.setStrokeColor(colors.HexColor(THEME_COLOR))
        canvas.setLineWidth(0.7)
        canvas.line(285, 35, 285, 807)
        canvas.restoreState()
        
    doc.build(
        [outer_table_p1, PageBreak(), outer_table_p2, PageBreak(), outer_table_p3, PageBreak(), outer_table_p4],
        onFirstPage=draw_t4_line,
        onLaterPages=draw_t4_line
    )


# ─── GENERATE A PDF CV FILE - TEMPLATE 5 (Beige & Olive Green, 2 Pages) ───────
def generate_pdf_cv_template_5(output_path, profile):
    from reportlab.platypus import PageBreak
    
    # 1. Setup Document Template
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=35,
        bottomMargin=35
    )
    
    # 2. Setup Styles
    styles = getSampleStyleSheet()
    
    THEME_COLOR = '#4B5346'
    
    style_sb_header = ParagraphStyle(
        'T5SBHeader',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor(THEME_COLOR)
    )
    style_sb_text = ParagraphStyle(
        'T5SBText',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1b1c1c')
    )
    style_sb_bullet = ParagraphStyle(
        'T5SBBullet',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=11,
        leftIndent=10,
        firstLineIndent=-5,
        textColor=colors.HexColor('#1b1c1c')
    )
    
    # Right column styles
    style_right_header = ParagraphStyle(
        'T5RightHeader',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor(THEME_COLOR)
    )
    style_body = ParagraphStyle(
        'T5BodyStyle',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1b1c1c')
    )
    style_bullet = ParagraphStyle(
        'T5BulletStyle',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=13,
        leftIndent=12,
        firstLineIndent=-6,
        textColor=colors.HexColor('#1b1c1c')
    )
    style_subhead_left = ParagraphStyle(
        'T5SubheadLeft',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor('#1b1c1c')
    )
    style_subhead_right = ParagraphStyle(
        'T5SubheadRight',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8.5,
        leading=12,
        alignment=2,
        textColor=colors.HexColor('#64748b')
    )

    def create_t5_section_header(title):
        p = Paragraph(f"<b>{title.upper()}</b>", style_right_header)
        t = Table([[p]], colWidths=[330])
        t.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor(THEME_COLOR)),
        ]))
        return t

    def create_t5_sidebar_header(title):
        p = Paragraph(f"<b>{title.upper()}</b>", style_sb_header)
        t = Table([[p]], colWidths=[175])
        t.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('LINEBELOW', (0,0), (-1,-1), 1.2, colors.HexColor(THEME_COLOR)),
        ]))
        return t

    # Page 1 Left
    left_flowables_p1 = [
        create_t5_sidebar_header("THÔNG TIN CÁ NHÂN"),
        Spacer(1, 6),
        Paragraph(f"✉ {profile['email']}", style_sb_text),
        Spacer(1, 4),
        Paragraph(f"📞 {profile['phone']}", style_sb_text),
        Spacer(1, 4),
        Paragraph(f"📍 {profile['address']}", style_sb_text),
        Spacer(1, 4),
        Paragraph(f"🌐 {profile['github']}", style_sb_text),
        Spacer(1, 15),
        create_t5_sidebar_header("KỸ NĂNG"),
        Spacer(1, 6)
    ]
    for g in profile["skills"][:2]:
        left_flowables_p1.append(Paragraph(f"<b>{g['category']}</b>", style_sb_text))
        left_flowables_p1.append(Spacer(1, 2))
        for item in g["items"]:
            left_flowables_p1.append(Paragraph(f"• {item}", style_sb_bullet))
        left_flowables_p1.append(Spacer(1, 6))
        
    left_flowables_p1.extend([
        Spacer(1, 10),
        create_t5_sidebar_header("HỌC VẤN"),
        Spacer(1, 6)
    ])
    edu = profile["education"]
    edu_table = Table([[
        Paragraph(f"<b>{edu['major']}</b>", style_subhead_left),
        Paragraph(edu['dates'], style_subhead_right)
    ]], colWidths=[110, 65])
    edu_table.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    left_flowables_p1.extend([
        edu_table,
        Paragraph(edu['school'], style_sb_text),
        Spacer(1, 2),
        Paragraph(f"• GPA: {edu['gpa']} - {edu['details']}", style_sb_text)
    ])

    # Page 1 Right
    style_header_name = ParagraphStyle(
        'T5HeaderName',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#ffffff')
    )
    style_header_title = ParagraphStyle(
        'T5HeaderTitle',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#ffffff')
    )
    style_header_obj = ParagraphStyle(
        'T5HeaderObj',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#ffffff')
    )
    header_flowables = [
        Paragraph(profile["full_name"].upper(), style_header_name),
        Spacer(1, 4),
        Paragraph(f"{profile['level']} {profile['title']}".upper(), style_header_title),
        Spacer(1, 6),
        Paragraph(profile["objective"], style_header_obj)
    ]
    header_table = Table([[header_flowables]], colWidths=[330], rowHeights=[159])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 15),
        ('RIGHTPADDING', (0,0), (-1,-1), 15),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    
    right_flowables_p1 = [
        header_table,
        Spacer(1, 15),
        create_t5_section_header("KINH NGHIỆM LÀM VIỆC"),
        Spacer(1, 6)
    ]
    for job in profile["experiences"]:
        job_table = Table([[
            Paragraph(f"<b>{job['position']}</b>", style_subhead_left),
            Paragraph(job['dates'], style_subhead_right)
        ]], colWidths=[230, 100])
        job_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        right_flowables_p1.extend([
            job_table,
            Paragraph(job['company'], style_body),
            Spacer(1, 2)
        ])
        for bullet in job["bullets"]:
            right_flowables_p1.append(Paragraph(f"• {bullet}", style_bullet))
        right_flowables_p1.append(Spacer(1, 10))
        
    right_flowables_p1.extend([
        Spacer(1, 5),
        create_t5_section_header("DỰ ÁN"),
        Spacer(1, 6)
    ])
    proj1 = profile["projects"][0]
    p_table1 = Table([[
        Paragraph(f"<b>{proj1['name']}</b>", style_subhead_left),
        Paragraph(proj1['dates'], style_subhead_right)
    ]], colWidths=[230, 100])
    p_table1.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    right_flowables_p1.extend([
        p_table1,
        Paragraph(f"<b>{proj1['role']}</b>", style_body),
        Spacer(1, 2),
        Paragraph(f"• Mô tả: {proj1['description']}", style_body),
        Spacer(1, 2),
        Paragraph(f"• Công nghệ: {', '.join(proj1['tags'])}", style_body),
        Spacer(1, 2),
        Paragraph(f"• Link: <font color='{THEME_COLOR}'><u>{proj1['link']}</u></font>", style_body)
    ])

    # Page 2 Left
    left_flowables_p2 = []
    if len(profile["skills"]) > 2:
        left_flowables_p2.extend([
            create_t5_sidebar_header("KỸ NĂNG (TIẾP)"),
            Spacer(1, 6)
        ])
        for g in profile["skills"][2:]:
            left_flowables_p2.append(Paragraph(f"<b>{g['category']}</b>", style_sb_text))
            left_flowables_p2.append(Spacer(1, 2))
            for item in g["items"]:
                left_flowables_p2.append(Paragraph(f"• {item}", style_sb_bullet))
            left_flowables_p2.append(Spacer(1, 6))
            
    left_flowables_p2.extend([
        Spacer(1, 10),
        create_t5_sidebar_header("CHỨNG CHỈ"),
        Spacer(1, 6)
    ])
    for c in profile["certificates"]:
        c_table = Table([[
            Paragraph(f"<b>{c['title']}</b>", style_subhead_left),
            Paragraph(c['date'], style_subhead_right)
        ]], colWidths=[110, 65])
        c_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        left_flowables_p2.extend([
            c_table,
            Spacer(1, 6)
        ])
        
    left_flowables_p2.extend([
        Spacer(1, 10),
        create_t5_sidebar_header("DANH HIỆU VÀ GIẢI THƯỞNG"),
        Spacer(1, 6)
    ])
    for a in profile["awards"]:
        a_table = Table([[
            Paragraph(f"<b>{a['title']}</b>", style_subhead_left),
            Paragraph(a['year'], style_subhead_right)
        ]], colWidths=[120, 55])
        a_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        left_flowables_p2.extend([
            a_table,
            Spacer(1, 4)
        ])
        
    left_flowables_p2.extend([
        Spacer(1, 10),
        create_t5_sidebar_header("NGƯỜI GIỚI THIỆU"),
        Spacer(1, 6),
        Paragraph(profile["reference"], style_sb_text),
        Spacer(1, 10),
        create_t5_sidebar_header("SỞ THÍCH"),
        Spacer(1, 6)
    ])
    for interest_item in profile["interests"].split(", "):
        left_flowables_p2.append(Paragraph(f"• {interest_item}", style_sb_bullet))
        
    # Page 2 Right
    right_flowables_p2 = [
        create_t5_section_header("DỰ ÁN (TIẾP)"),
        Spacer(1, 6)
    ]
    if len(profile["projects"]) > 1:
        proj2 = profile["projects"][1]
        p_table2 = Table([[
            Paragraph(f"<b>{proj2['name']}</b>", style_subhead_left),
            Paragraph(proj2['dates'], style_subhead_right)
        ]], colWidths=[230, 100])
        p_table2.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        right_flowables_p2.extend([
            p_table2,
            Paragraph(f"<b>{proj2['role']}</b>", style_body),
            Spacer(1, 2),
            Paragraph(f"• Mô tả: {proj2['description']}", style_body),
            Spacer(1, 2),
            Paragraph(f"• Công nghệ: {', '.join(proj2['tags'])}", style_body),
            Spacer(1, 2),
            Paragraph(f"• Link: <font color='{THEME_COLOR}'><u>{proj2['link']}</u></font>", style_body)
        ])

    outer_table_p1 = Table([[left_flowables_p1, [], right_flowables_p1]], colWidths=[175, 20, 330])
    outer_table_p1.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    
    outer_table_p2 = Table([[left_flowables_p2, [], right_flowables_p2]], colWidths=[175, 20, 330])
    outer_table_p2.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    
    def draw_t5_bg_p1(canvas, doc):
        canvas.saveState()
        canvas.setTitle("Template 5")
        canvas.setFillColor(colors.HexColor('#e6d5b8'))
        canvas.rect(0, 0, 595.27, 841.89, fill=1, stroke=0)
        
        canvas.setFillColor(colors.HexColor('#e8ded5'))
        canvas.rect(0, 483, 228.8, 842 - 483, fill=1, stroke=0)
        
        canvas.setFillColor(colors.HexColor('#4B5346'))
        canvas.rect(228.8, 648, 595.27 - 228.8, 842 - 648, fill=1, stroke=0)
        
        canvas.restoreState()
        
    def draw_t5_bg_p2(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#e6d5b8'))
        canvas.rect(0, 0, 595.27, 841.89, fill=1, stroke=0)
        canvas.restoreState()
        
    doc.build(
        [outer_table_p1, PageBreak(), outer_table_p2],
        onFirstPage=draw_t5_bg_p1,
        onLaterPages=draw_t5_bg_p2
    )


# ─── GENERATE A PDF CV FILE - TEMPLATE 6 (Dark Crimson, 2 Pages) ──────────────
def generate_pdf_cv_template_6(output_path, profile):
    from reportlab.platypus import PageBreak
    
    # 1. Setup Document Template
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=15,
        leftMargin=15,
        topMargin=20,
        bottomMargin=20
    )
    
    # 2. Setup Styles
    styles = getSampleStyleSheet()
    
    THEME_COLOR = '#A94A4B'
    
    style_name = ParagraphStyle(
        'T6Name',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=22,
        leading=26,
        textColor=colors.HexColor(THEME_COLOR)
    )
    style_title_right = ParagraphStyle(
        'T6TitleRight',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=14,
        alignment=2,
        textColor=colors.HexColor('#475569')
    )
    style_sec_header = ParagraphStyle(
        'T6SecHeader',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor(THEME_COLOR)
    )
    style_body = ParagraphStyle(
        'T6Body',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1b1c1c')
    )
    style_body_bold = ParagraphStyle(
        'T6BodyBold',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1b1c1c')
    )
    style_body_gray = ParagraphStyle(
        'T6BodyGray',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8.0,
        leading=10.5,
        textColor=colors.HexColor('#64748b')
    )
    style_bullet = ParagraphStyle(
        'T6Bullet',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8.5,
        leading=11,
        leftIndent=10,
        firstLineIndent=-5,
        textColor=colors.HexColor('#1b1c1c')
    )
    style_subhead_right = ParagraphStyle(
        'T6SubheadRight',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8.0,
        leading=11,
        alignment=2,
        textColor=colors.HexColor('#64748b')
    )

    def create_t6_section_header(title):
        p = Paragraph(f"<b>{title.upper()}</b>", style_sec_header)
        t = Table([[p]], colWidths=[565])
        t.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('LINEBELOW', (0,0), (-1,-1), 1.0, colors.HexColor('#cccccc')),
        ]))
        return t

    def create_t6_col_section_header(title):
        p = Paragraph(f"<b>{title.upper()}</b>", style_sec_header)
        t = Table([[p]], colWidths=[275])
        t.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('LINEBELOW', (0,0), (-1,-1), 1.0, colors.HexColor('#cccccc')),
        ]))
        return t

    story = []
    
    # 👤 Avatar Table: 90 x 90pt grey box (reduced from 110 for vertical space)
    avatar_cell = Table([[""]], colWidths=[90], rowHeights=[90])
    avatar_cell.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ececec')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # Header Name & Title Table
    name_para = Paragraph(profile["full_name"].upper(), style_name)
    title_para = Paragraph(f"{profile['level']} {profile['title']}".upper(), style_title_right)
    name_title_table = Table([[name_para, title_para]], colWidths=[250, 210])
    name_title_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor(THEME_COLOR)),
    ]))
    
    # Contact Info Table
    contact_left = [
        Paragraph(f"📞 {profile['phone']}", style_body),
        Spacer(1, 3),
        Paragraph(f"📍 {profile['address']}", style_body),
    ]
    contact_right = [
        Paragraph(f"✉ {profile['email']}", style_body),
        Spacer(1, 3),
        Paragraph(f"🌐 {profile['github']}", style_body),
    ]
    contact_table = Table([[contact_left, contact_right]], colWidths=[220, 240])
    contact_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    
    header_text_flowables = [
        name_title_table,
        contact_table
    ]
    
    header_table = Table([[avatar_cell, [], header_text_flowables]], colWidths=[90, 15, 460])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    
    # ─── MỤC TIÊU NGHỀ NGHIỆP ───
    story.append(create_t6_section_header("MỤC TIÊU NGHỀ NGHIỆP"))
    story.append(Spacer(1, 4))
    story.append(Paragraph(profile["objective"], style_body))
    story.append(Spacer(1, 10))
    
    # ─── HỌC VẤN ───
    story.append(create_t6_section_header("HỌC VẤN"))
    story.append(Spacer(1, 4))
    edu = profile["education"]
    edu_left = [
        Paragraph(f"<b>{edu['major']}</b>", style_body_bold),
        Paragraph(edu['dates'], style_body_gray)
    ]
    edu_right = [
        Paragraph(f"<b>{edu['school']}</b>", style_body_bold),
        Spacer(1, 2),
        Paragraph(f"• GPA: {edu['gpa']} - {edu['details']}", style_body)
    ]
    edu_table = Table([[edu_left, [], edu_right]], colWidths=[175, 20, 370])
    edu_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(edu_table)
    story.append(Spacer(1, 10))
    
    # ─── KINH NGHIỆM LÀM VIỆC ───
    story.append(create_t6_section_header("KINH NGHIỆM LÀM VIỆC"))
    story.append(Spacer(1, 4))
    for job in profile["experiences"]:
        job_left = [
            Paragraph(f"<b>{job['position']}</b>", style_body_bold),
            Paragraph(job['dates'], style_body_gray)
        ]
        job_right = [
            Paragraph(f"<b>{job['company']}</b>", style_body_bold),
            Spacer(1, 2)
        ]
        for bullet in job["bullets"]:
            job_right.append(Paragraph(f"• {bullet}", style_bullet))
        job_table = Table([[job_left, [], job_right]], colWidths=[175, 20, 370])
        job_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(job_table)
    story.append(Spacer(1, 6))
    
    # ─── PAGE 2 ───
    story.append(PageBreak())
    
    # Split section Page 2
    col1_flowables_p2 = [
        create_t6_col_section_header("KỸ NĂNG"),
        Spacer(1, 4)
    ]
    for g in profile["skills"]:
        col1_flowables_p2.append(Paragraph(f"<b>{g['category']}</b>", style_body_bold))
        col1_flowables_p2.append(Spacer(1, 2))
        for item in g["items"]:
            col1_flowables_p2.append(Paragraph(f"• {item}", style_bullet))
        col1_flowables_p2.append(Spacer(1, 4))
            
    col1_flowables_p2.extend([
        Spacer(1, 6),
        create_t6_col_section_header("NGƯỜI GIỚI THIỆU"),
        Spacer(1, 4),
        Paragraph(profile["reference"], style_body),
        Spacer(1, 10),
        create_t6_col_section_header("SỞ THÍCH"),
        Spacer(1, 4)
    ])
    for interest_item in profile["interests"].split(", "):
        col1_flowables_p2.append(Paragraph(f"• {interest_item}", style_bullet))
        
    col2_flowables_p2 = [
        create_t6_col_section_header("CHỨNG CHỈ"),
        Spacer(1, 4)
    ]
    for c in profile["certificates"]:
        c_table = Table([[
            Paragraph(f"<b>{c['title']}</b>", style_body_bold),
            Paragraph(c['date'], style_subhead_right)
        ]], colWidths=[205, 70])
        c_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        col2_flowables_p2.extend([
            c_table,
            Spacer(1, 3)
        ])
        
    col2_flowables_p2.extend([
        Spacer(1, 6),
        create_t6_col_section_header("DANH HIỆU VÀ GIẢI THƯỞNG"),
        Spacer(1, 4)
    ])
    for a in profile["awards"]:
        a_table = Table([[
            Paragraph(f"<b>{a['title']}</b>", style_body_bold),
            Paragraph(a['year'], style_subhead_right)
        ]], colWidths=[215, 60])
        a_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        col2_flowables_p2.extend([
            a_table,
            Spacer(1, 3)
        ])
        
    # Projects on Page 2 Right
    col2_flowables_p2.extend([
        Spacer(1, 8),
        create_t6_col_section_header("DỰ ÁN"),
        Spacer(1, 4)
    ])
    for p in profile["projects"]:
        p_table = Table([[
            Paragraph(f"<b>{p['name']}</b>", style_body_bold),
            Paragraph(p['dates'], style_subhead_right)
        ]], colWidths=[205, 70])
        p_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        col2_flowables_p2.extend([
            p_table,
            Paragraph(f"<b>{p['role']}</b>", style_body),
            Spacer(1, 2),
            Paragraph(f"• Mô tả: {p['description']}", style_body),
            Spacer(1, 2),
            Paragraph(f"• Công nghệ: {', '.join(p['tags'])}", style_body),
            Spacer(1, 2),
            Paragraph(f"• Link: <font color='{THEME_COLOR}'><u>{p['link']}</u></font>", style_body),
            Spacer(1, 8)
        ])
        
    page2_split_table = Table([[col1_flowables_p2, [], col2_flowables_p2]], colWidths=[275, 15, 275])
    page2_split_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(page2_split_table)
    
    # 3. Build Document
    def draw_t6_meta(canvas, doc):
        canvas.saveState()
        canvas.setTitle("Template 6")
        canvas.restoreState()
        
    doc.build(story, onFirstPage=draw_t6_meta, onLaterPages=draw_t6_meta)

# ─── BATCH GENERATOR ──────────────────────────────────────────────────────────
def batch_generate_pdfs(count, template_id=None):
    output_dir = "CV"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n[PDF Gen] === KHỞI ĐỘNG BATCH GENERATE ({count} FILE PDF) ===")
    print(f"[PDF Gen] Thư mục lưu trữ: {os.path.abspath(output_dir)}")
    
    success = 0
    for i in range(count):
        # Determine template
        curr_template = template_id
        if not curr_template:
            # Cycle through all templates (1 to 6)
            curr_template = (i % 6) + 1

        # Random Candidate Profile
        sex = random.choice(["MALE", "FEMALE"])
        first_name = random.choice(FIRST_NAMES)
        middle_name = "Thị" if sex == "FEMALE" else random.choice([m for m in MIDDLE_NAMES if m != "Thị"])
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {middle_name} {last_name}"
        
        specs = list(SPECIALTIES.keys())
        if i < len(specs):
            specialty = specs[i]
        else:
            specialty = random.choice(specs)
        level = random.choice(["INTERN", "FRESHER", "JUNIOR", "MIDDLE", "SENIOR", "LEADER", "MANAGER"])
        
        # Calculate Experience Years
        exp_years = 0
        if level == "FRESHER": exp_years = random.choice([0, 1])
        elif level == "JUNIOR": exp_years = random.randint(1, 2)
        elif level == "MIDDLE": exp_years = random.randint(3, 4)
        elif level == "SENIOR": exp_years = random.randint(5, 7)
        elif level == "LEADER": exp_years = random.randint(7, 9)
        elif level == "MANAGER": exp_years = random.randint(9, 12)
        
        # Select location from ADDRESSES list in order to ensure diversity
        loc = ADDRESSES[i % len(ADDRESSES)]
        # Generate full candidate profile dictionary
        profile = generate_candidate_profile(full_name, specialty, level, exp_years, location=loc)
        
        # File Name
        name_slug = make_slug(full_name).replace(".", "_")
        spec_slug = specialty.lower().replace(" .", "").replace(" & ", "_").replace(" ", "_")
        file_name = f"cv_{name_slug}_{spec_slug}_{level.lower()}.pdf"
        file_path = os.path.join(output_dir, file_name)
        
        try:
            if curr_template == 1:
                generate_pdf_cv(file_path, profile)
            elif curr_template == 2:
                generate_pdf_cv_two_column(file_path, profile)
            elif curr_template == 3:
                generate_pdf_cv_template_3(file_path, profile)
            elif curr_template == 4:
                generate_pdf_cv_template_4(file_path, profile)
            elif curr_template == 5:
                generate_pdf_cv_template_5(file_path, profile)
            elif curr_template == 6:
                generate_pdf_cv_template_6(file_path, profile)
            else:
                generate_pdf_cv_template_3(file_path, profile)
            success += 1
            print(f"[PDF Gen] -> [{success}/{count}] Đã tạo (Mẫu {curr_template}): {file_name}")
        except Exception as e:
            print(f"[PDF Gen] ❌ Lỗi khi tạo file {file_name}: {e}")
            import traceback
            traceback.print_exc()
            
    print(f"\n[PDF Gen] ✅ HOÀN THÀNH BATCH GENERATE!")
    print(f"[PDF Gen] Tổng cộng: Đã tạo thành công {success}/{count} file PDF tại thư mục: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch generate PDF resumes for JobHub.")
    parser.add_argument("--count", type=int, default=5, help="Số lượng file PDF cần tạo. Mặc định là 5.")
    parser.add_argument("--template", type=int, default=None, choices=[1, 2, 3, 4, 5, 6], help="Chọn mẫu CV (1-6). Mặc định là sinh đan xen 1 và 2.")
    args = parser.parse_args()
    
    batch_generate_pdfs(args.count, args.template)
