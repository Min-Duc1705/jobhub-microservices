import os
import sys
import uuid
import psycopg2
import unicodedata
import re

sys.stdout.reconfigure(encoding='utf-8')

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "root"
}

def remove_accents_str(input_str):
    s = input_str.replace('Đ', 'D').replace('đ', 'd')
    nfkd_form = unicodedata.normalize('NFKD', s)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

# Get company category based on its name
def get_company_category(comp_name):
    norm = remove_accents_str(comp_name).lower()
    if any(k in norm for k in ['vinai', 'vinbrain', 'vinbigdata', 'cinnamon', 'viettel ai', 'vnpt ai', 'data intelligence']):
        return 'AI_ML'
    if any(k in norm for k in ['momo', 'bank', 'vietcombank', 'techcombank', 'vpbank', 'woori', 'shinhan', 'hsbc', 'kbtg', 'napas', 'vnlife', 'vnpay', 'coin98', 'home credit', 'money forward']):
        return 'FINTECH_BANKING'
    if any(k in norm for k in ['shopee', 'lazada', 'tiki', 'grab', 'gojek', 'be group', 'traveloka', 'ivivu', 'vntrip', 'onpoint', 'sapotech', 'sapo', 'kiotviet', 'teko', 'haravan']):
        return 'ECOMMERCE_RETAIL'
    if any(k in norm for k in ['giao hang', 'ghn', 'ghtk', 'ahamove', 'j&t', 'ninja van']):
        return 'LOGISTICS'
    if any(k in norm for k in ['amanotes', 'garena', 'sky mavis', 'vng games', 'sohagame', 'gameloft', 'koei tecmo', 'glass egg', 'sparx', 'ubisoft', 'vtc']):
        return 'GAME'
    if any(k in norm for k in ['bkav', 'vncs', 'viettel cyber', 'cmc cyber', 'vsec', 'securitybox', 'chongluadao', 'fortinet', 'palo alto', 'check point', 'kaspersky']):
        return 'CYBERSECURITY'
    if any(k in norm for k in ['prep', 'mindx', 'teky', 'coderschool', 'funix', 'topica', 'elsa']):
        return 'EDTECH'
    if any(k in norm for k in ['jio health', 'edoctor', 'buymed', 'thuocsi', 'med247']):
        return 'HEALTHTECH'
    if any(k in norm for k in ['viettel group', 'viettel telecom', 'vnpt', 'fpt telecom', 'cmc telecom', 'netnam', 'cisco', 'nokia', 'huawei', 'ericsson', 'qualcomm', 'intel', 'semiconductors']):
        return 'TELECOM_NETWORKING'
    return 'SOFTWARE_SERVICES'

# Real-world Job templates for each category
TEMPLATES = {
    "AI_ML": {
        "python": {
            "title": "AI/ML Research Scientist (Generative AI)",
            "skills": ["Python", "Generative AI", "Machine Learning", "Deep Learning", "Natural Language Processing (NLP)"],
            "desc": "Tham gia nghiên cứu và phát triển các mô hình ngôn ngữ lớn (LLM), AI tạo sinh (Generative AI) phục vụ các sản phẩm cốt lõi của công ty. Thử nghiệm các kiến trúc mô hình mới, tối ưu hóa quá trình huấn luyện và tinh chỉnh (fine-tuning) mô hình.",
            "req": "Tốt nghiệp Thạc sĩ/Tiến sĩ ngành Khoa học máy tính hoặc liên quan. Có kinh nghiệm huấn luyện mô hình học sâu sử dụng PyTorch/TensorFlow. Có bài báo khoa học tại các hội nghị uy tín (NeurIPS, CVPR, ACL, v.v.) là lợi thế lớn.",
            "benefits": "Thu nhập hấp dẫn cùng gói thưởng dự án cuối năm. Được làm việc cùng đội ngũ chuyên gia hàng đầu và tiếp cận hạ tầng tính toán GPU cực mạnh. Hỗ trợ kinh phí tham gia hội thảo quốc tế."
        },
        "computer_vision": {
            "title": "Senior Computer Vision Engineer",
            "skills": ["Python", "C/C++", "OpenCV", "Deep Learning", "PyTorch"],
            "desc": "Phát triển các thuật toán thị giác máy tính và học sâu phục vụ nhận diện khuôn mặt, phát hiện vật thể và phân tích hành vi thời gian thực. Tối ưu hóa mô hình chạy trên các thiết bị nhúng và thiết bị biên (Edge Devices).",
            "req": "Tối thiểu 3 năm kinh nghiệm làm việc về Computer Vision. Sử dụng thành thạo Python, C++, OpenCV và một trong các framework PyTorch, TensorFlow. Có kinh nghiệm tối ưu hóa mô hình (quantization, pruning).",
            "benefits": "Mức lương cạnh tranh và cơ hội nhận cổ phần (ESOP). Môi trường làm việc năng động, sáng tạo. Bảo hiểm sức khỏe quốc tế chất lượng cao."
        },
        "data_engineer": {
            "title": "Big Data Engineer (Spark / Kafka / Python)",
            "skills": ["Python", "SQL", "Hadoop", "Spark", "Kafka"],
            "desc": "Thiết kế, xây dựng và tối ưu hóa hệ thống đường ống dẫn dữ liệu (Data Pipelines) thời gian thực phục vụ phân tích dữ liệu lớn. Thiết lập kiến trúc Data Lakehouse và tối ưu hóa hiệu năng truy vấn dữ liệu.",
            "req": "Tối thiểu 2 năm kinh nghiệm ở vị trí Data Engineer. Thành thạo Python, SQL. Kinh nghiệm làm việc với Apache Spark, Apache Kafka và các công cụ điều phối (Airflow).",
            "benefits": "Được làm việc với các hệ thống dữ liệu quy mô Petabyte. Xét duyệt tăng lương 2 lần/năm. Đào tạo chuyên sâu về Big Data và Cloud."
        },
        "default": {
            "title": "AI Product Engineer",
            "skills": ["Python", "Generative AI", "TypeScript", "REST API", "Docker"],
            "desc": "Tham gia tích hợp các mô hình AI/LLMs vào sản phẩm web và ứng dụng của công ty. Xây dựng các API hiệu năng cao và thiết lập hệ thống giám sát chất lượng phản hồi từ mô hình AI.",
            "req": "Có kinh nghiệm phát triển backend (Python/Node.js). Hiểu biết về cách sử dụng API của các mô hình LLM (OpenAI, Gemini, Claude). Có kinh nghiệm sử dụng Docker và deploy sản phẩm lên Cloud.",
            "benefits": "Mức lương cạnh tranh và cơ hội nhận thưởng dự án. Được làm việc trực tiếp với các công nghệ AI tiên phong. Môi trường làm việc năng động."
        }
    },
    "FINTECH_BANKING": {
        "java": {
            "title": "Senior Java Developer (Core Banking & Microservices)",
            "skills": ["Java", "Spring Boot", "Microservices", "PostgreSQL", "Redis", "RabbitMQ"],
            "desc": "Tham gia phát triển hệ thống ngân hàng số và các cổng thanh toán chịu tải cao. Thiết kế và tối ưu hóa các API microservices phục vụ hàng triệu giao dịch mỗi ngày, đảm bảo tính bảo mật và an toàn thông tin tối đa.",
            "req": "Tối thiểu 4 năm kinh nghiệm lập trình Java/Spring Boot. Am hiểu kiến trúc Microservices, RESTful API. Có kinh nghiệm tối ưu hóa cơ sở dữ liệu PostgreSQL/Oracle và xử lý hàng đợi tin nhắn (RabbitMQ/Kafka).",
            "benefits": "Lương tháng 13 + thưởng hiệu quả kinh doanh lên tới 3-4 tháng lương. Gói bảo hiểm sức khỏe VIP cho cá nhân và người thân. Cơ hội thăng tiến lên Technical Lead."
        },
        "architect": {
            "title": "Tech Lead / Solution Architect (Fintech & Payment Gateway)",
            "skills": ["Java", "Go (Golang)", "Microservices", "Architecture", "Cloud", "SQL"],
            "desc": "Thiết kế kiến trúc tổng thể cho hệ thống thanh toán điện tử và ví điện tử tích hợp. Đảm bảo hệ thống đạt độ sẵn sàng cao (High Availability), khả năng chịu lỗi (Fault Tolerance) và tuân thủ các tiêu chuẩn bảo mật PCI-DSS.",
            "req": "Tối thiểu 6 năm kinh nghiệm trong ngành phát triển phần mềm, với ít nhất 2 năm làm ở vị trí Solution Architect trong lĩnh vực Fintech/Banking. Thành thạo Java, Go và hạ tầng AWS/Kubernetes.",
            "benefits": "Mức lương đột phá hàng đầu thị trường. Được cấp Macbook Pro đời mới nhất. Xét tăng lương hàng năm và có chế độ thưởng theo dự án đặc biệt."
        },
        "dba": {
            "title": "Database Administrator (SQL Server / Oracle / Postgres)",
            "skills": ["SQL", "Oracle", "PostgreSQL", "Microsoft SQL Server"],
            "desc": "Quản trị, giám sát và tối ưu hóa hiệu năng các hệ thống cơ sở dữ liệu lớn của ngân hàng. Thiết lập các phương án sao lưu (Backup & Recovery), cơ chế High Availability (Clustering, Replication) và khắc phục sự cố dữ liệu.",
            "req": "Có kinh nghiệm quản trị các DB Oracle, PostgreSQL hoặc SQL Server lớn. Am hiểu sâu sắc về điều chỉnh hiệu năng SQL (SQL Tuning), quản lý tài nguyên DB và bảo mật dữ liệu.",
            "benefits": "Thưởng lễ tết, thưởng sinh nhật hấp dẫn. Cơ hội tham gia các khóa đào tạo chứng chỉ quốc tế do hãng tài trợ 100%. Môi trường làm việc chuyên nghiệp, văn phòng hiện đại."
        },
        "default": {
            "title": "Fintech Software Engineer (Go / Python)",
            "skills": ["Go (Golang)", "Python", "SQL", "REST API", "Docker"],
            "desc": "Phát triển và bảo trì các dịch vụ thanh toán và quản lý số dư của khách hàng. Phối hợp với đội ngũ an ninh mạng để triển khai các cơ chế kiểm soát giao dịch, chống gian lận.",
            "req": "Tối thiểu 2 năm kinh nghiệm lập trình Backend (Go hoặc Python). Nắm vững kiến thức về database, SQL query optimization. Có kinh nghiệm với hệ thống phân tán.",
            "benefits": "Lương thưởng cạnh tranh. Review tăng lương hàng năm. Môi trường ngân hàng/fintech chuyên nghiệp, chế độ đãi ngộ xuất sắc."
        }
    },
    "ECOMMERCE_RETAIL": {
        "golang": {
            "title": "High-Throughput Go Backend Engineer (E-commerce Core)",
            "skills": ["Go (Golang)", "MySQL", "Redis", "Kafka", "Docker"],
            "desc": "Phát triển các dịch vụ backend cốt lõi như quản lý giỏ hàng, thanh toán và xử lý đơn hàng chịu tải lớn (High Concurrency). Tối ưu hóa hiệu năng API và giao tiếp gRPC giữa các microservices để giảm thiểu độ trễ trong các đợt Siêu Sale.",
            "req": "Có tối thiểu 2 năm kinh nghiệm lập trình Go (Golang) thực tế. Am hiểu về concurrency, channel và memory management trong Go. Có kinh nghiệm với Redis, Kafka, MySQL.",
            "benefits": "Được làm việc trực tiếp trong hệ sinh thái e-commerce triệu người dùng. Review lương định kỳ hàng năm. Cung cấp Macbook và các trang thiết bị làm việc hiện đại."
        },
        "frontend": {
            "title": "Senior Frontend Engineer (ReactJS / Next.js)",
            "skills": ["React", "Next.js", "TypeScript", "Tailwind CSS", "JavaScript"],
            "desc": "Xây dựng giao diện web storefront và trang quản trị (Admin Dashboard) mượt mà, phản hồi nhanh. Tối ưu hóa SEO và chỉ số Core Web Vitals của trang web bằng cách áp dụng Next.js Server-Side Rendering (SSR).",
            "req": "Tối thiểu 3 năm kinh nghiệm phát triển Web Frontend sử dụng ReactJS và Next.js. Nắm vững TypeScript, CSS Grid/Flexbox và các thư viện quản lý state (Redux Toolkit, Zustand).",
            "benefits": "Môi trường làm việc trẻ trung, năng động, không mặc đồng phục. Nhiều hoạt động team building, câu lạc bộ thể thao. Xét tăng lương cạnh tranh."
        },
        "mobile": {
            "title": "Mobile Software Engineer (React Native / iOS / Android)",
            "skills": ["React Native", "Mobile", "TypeScript", "JavaScript"],
            "desc": "Phát triển và cải tiến ứng dụng mua sắm trên di động sử dụng React Native. Tích hợp các SDK thanh toán, tối ưu hóa luồng trải nghiệm người dùng và đảm bảo ứng dụng chạy mượt mà trên cả iOS và Android.",
            "req": "Ít nhất 2 năm kinh nghiệm lập trình di động với React Native. Nắm vững kiến thức về React Native lifecycle, hiệu năng render và tương tác native modules.",
            "benefits": "Hỗ trợ 100% chi phí gửi xe, teabreak hàng ngày. Gói khám sức khỏe định kỳ hàng năm tại bệnh viện quốc tế. Thưởng cuối năm hấp dẫn."
        },
        "default": {
            "title": "E-commerce Backend Developer (Java / Node.js)",
            "skills": ["Java", "Node.js", "MySQL", "REST API", "Git"],
            "desc": "Tham gia thiết kế các dịch vụ nghiệp vụ mua bán, quản lý mã giảm giá, khuyến mại cho hệ thống bán lẻ. Tích hợp và làm việc với các hệ thống thanh toán bên thứ ba.",
            "req": "Có kinh nghiệm lập trình Backend Java hoặc Node.js tối thiểu 2 năm. Hiểu rõ cấu trúc dữ liệu, giải thuật và lập trình hướng đối tượng.",
            "benefits": "Lương tháng 13 + thưởng hiệu quả. Bảo hiểm PVI chất lượng cao. teabreak, café miễn phí tại văn phòng."
        }
    },
    "LOGISTICS": {
        "nodejs": {
            "title": "Node.js Backend Engineer (Logistics Tracking System)",
            "skills": ["Node.js", "Express.js", "NestJS", "MongoDB", "Redis"],
            "desc": "Xây dựng hệ thống theo dõi đơn hàng (Order Tracking) và định tuyến giao hàng thời gian thực. Phát triển các cổng API kết nối giữa shipper, cửa hàng và khách hàng đảm bảo độ trễ thấp nhất.",
            "req": "Tối thiểu 2 năm kinh nghiệm phát triển Backend với Node.js (Express hoặc NestJS). Có kinh nghiệm làm việc với MongoDB/PostgreSQL và Redis. Biết sử dụng WebSocket.",
            "benefits": "Mức lương thỏa thuận hấp dẫn tùy theo năng lực. Thưởng tháng lương 13 + KPIs. Cơ hội làm việc trực tiếp với các bài toán tối ưu hóa định tuyến giao vận phức tạp."
        },
        "devops": {
            "title": "Senior DevOps / System Engineer (Logistics Platform)",
            "skills": ["DevOps", "Docker", "Kubernetes", "Linux", "AWS", "Git"],
            "desc": "Thiết lập và quản lý hạ tầng đám mây phân tán phục vụ hệ thống logistics quy mô lớn toàn quốc. Triển khai CI/CD pipeline tự động hóa quy trình test và release phần mềm, giám sát hệ thống cảnh báo sớm lỗi dịch vụ.",
            "req": "Trên 3 năm kinh nghiệm ở vị trí DevOps. Thành thạo Linux system admin, Docker, Kubernetes và các dịch vụ AWS. Viết kịch bản tự động hóa tốt bằng Python/Bash.",
            "benefits": "Thu nhập cạnh tranh cùng gói chăm sóc sức khỏe toàn diện. Cơ hội làm việc trong môi trường công nghệ lớn, quy mô vận hành toàn quốc. Xét tăng lương hàng năm."
        },
        "default": {
            "title": "Logistics Software Developer (C# / .NET)",
            "skills": ["C#", ".NET", "PostgreSQL", "REST API", "Docker"],
            "desc": "Phát triển các ứng dụng quản lý kho bãi, quản lý đơn vận chuyển cho chuỗi logistics. Cải tiến và nâng cấp hiệu năng hệ thống quản trị nội bộ.",
            "req": "Tối thiểu 2 năm kinh nghiệm lập trình C#/.NET. Hiểu biết về hệ quản trị cơ sở dữ liệu quan hệ PostgreSQL/SQL Server. Có tư duy logic tốt.",
            "benefits": "Môi trường năng động, thân thiện. Đóng BHXH đầy đủ. Hỗ trợ tiền ăn trưa và gửi xe."
        }
    },
    "GAME": {
        "unity": {
            "title": "Game Developer (Unity / C# / Mobile Games)",
            "skills": ["C#", "Unity", "Mobile", "3D", "Game Design"],
            "desc": "Tham gia phát triển các dự án game di động (3D/2D Casual, Mid-core) trên nền tảng Unity. Viết code logic game sạch, tối ưu hóa hiệu năng đồ họa và fps trên các dòng máy di động cấu hình thấp.",
            "req": "Có tối thiểu 2 năm kinh nghiệm lập trình game sử dụng Unity và C#. Nắm vững kiến thức về toán học 3D, vật lý trong game, tối ưu hóa bộ nhớ và giảm thiểu draw calls.",
            "benefits": "Thưởng theo doanh thu phát hành game cực kỳ hấp dẫn. Môi trường làm việc thoải mái, đầy sáng tạo với khu giải trí, chơi game tại văn phòng."
        },
        "artist": {
            "title": "3D Game Artist (Modeling / Texturing / Rigging)",
            "skills": ["3D", "Game Design", "Photoshop"],
            "desc": "Thiết kế và tạo hình các mô hình 3D cho nhân vật, vũ khí và môi trường trong game dựa trên concept art có sẵn. Thực hiện vẽ texture chi tiết, tạo khung xương (rigging) và diễn hoạt (animation) cho nhân vật.",
            "req": "Thành thạo các công cụ thiết kế 3D (Blender, Maya, hoặc 3ds Max) và Photoshop. Có gu thẩm mỹ tốt về tỷ lệ cơ thể, ánh sáng và màu sắc. Gửi kèm Portfolio dự án đã thực hiện khi ứng tuyển.",
            "benefits": "Xét duyệt lương 2 lần/năm. Thưởng dự án dựa trên tiến độ và chất lượng sản phẩm nghệ thuật. Teambuilding hoành tráng hàng năm."
        },
        "default": {
            "title": "C++ Game Engine Programmer",
            "skills": ["C/C++", "Python", "Data Structures", "Algorithms", "3D"],
            "desc": "Phát triển và bảo trì mã nguồn công cụ đồ họa game (Game Engine) cốt lõi của studio. Tối ưu hóa tốc độ xử lý vật lý, ánh sáng và các luồng đa nhân xử lý trong game.",
            "req": "Thành thạo lập trình C/C++, cấu trúc dữ liệu và giải thuật tốt. Hiểu biết về toán học ma trận, vector 3D và các thư viện đồ họa (OpenGL/DirectX).",
            "benefits": "Lương cạnh tranh, thưởng dự án hấp dẫn. Xét duyệt tăng lương hàng năm. Hỗ trợ máy tính cấu hình khủng làm việc."
        }
    },
    "CYBERSECURITY": {
        "pentest": {
            "title": "Senior Penetration Tester (Pentest / Red Team)",
            "skills": ["Testing", "QA QC", "Cybersecurity", "Linux"],
            "desc": "Thực hiện đánh giá an toàn thông tin, dò quét lỗ hổng (Vulnerability Assessment) và kiểm thử xâm nhập (Penetration Testing) hệ thống mạng, ứng dụng web/mobile của khách hàng. Đề xuất giải pháp khắc phục lỗ hổng bảo mật.",
            "req": "Tối thiểu 3 năm kinh nghiệm làm Pentest. Có kiến thức sâu sắc về OWASP Top 10, lỗ hổng hệ thống và giao thức mạng. Ưu tiên ứng viên có chứng chỉ quốc tế như OSCP, CEH, LPT.",
            "benefits": "Mức lương cao cùng thưởng hấp dẫn khi phát hiện các lỗ hổng nghiêm trọng. Được tài trợ 100% kinh phí thi các chứng chỉ bảo mật cao cấp quốc tế."
        },
        "soc": {
            "title": "Cybersecurity Specialist (Security Operations Center - SOC)",
            "skills": ["Cybersecurity", "Network", "Linux"],
            "desc": "Giám sát và phân tích các cảnh báo an ninh thông tin từ hệ thống SIEM. Phát hiện kịp thời các cuộc tấn công mạng, phân tích mã độc và tham gia điều tra, ứng cứu sự cố bảo mật thông tin doanh nghiệp.",
            "req": "Có kiến thức nền tảng tốt về mạng, hệ điều hành Linux/Windows Server và các kỹ thuật tấn công mạng phổ biến. Biết sử dụng các công cụ giám sát mạng (Wireshark, Splunk, ELK).",
            "benefits": "Được đào tạo bài bản từ đầu về ứng cứu sự cố và phân tích mã độc. Lương tháng 13 + thưởng hiệu quả công việc. Xét tăng lương hàng năm."
        },
        "default": {
            "title": "Security Software Developer",
            "skills": ["Python", "C/C++", "Cybersecurity", "Linux", "Docker"],
            "desc": "Phát triển các công cụ bảo mật nội bộ, agent giám sát an toàn thông tin trên thiết bị đầu cuối và phần mềm tường lửa thế hệ mới.",
            "req": "Có kinh nghiệm lập trình tốt bằng Python hoặc C/C++. Am hiểu sâu sắc về hệ điều hành Linux và lập trình mạng. Có đam mê về lĩnh vực an ninh bảo mật.",
            "benefits": "Chế độ đãi ngộ xuất sắc, hỗ trợ tiền cơm trưa. Xét tăng lương cạnh tranh. Được hướng dẫn bởi các chuyên gia bảo mật hàng đầu."
        }
    },
    "EDTECH": {
        "backend": {
            "title": "Python Backend Engineer (E-learning Platform)",
            "skills": ["Python", "Django", "PostgreSQL", "REST API", "Docker"],
            "desc": "Phát triển hệ thống quản lý học tập trực tuyến (LMS) phục vụ hàng trăm ngàn học viên. Xây dựng các API RESTful mượt mà phục vụ học tập, thi thử trực tuyến và chấm điểm tự động.",
            "req": "Có tối thiểu 2 năm kinh nghiệm phát triển Backend sử dụng Python và Django hoặc FastAPI. Thành thạo SQL và thiết kế cơ sở dữ liệu PostgreSQL. Có kinh nghiệm triển khai dự án với Docker.",
            "benefits": "Lương cạnh tranh, thử việc hưởng 100% lương. Cơ hội học tiếng Anh/các khóa học chuyên môn miễn phí trên nền tảng của công ty. Môi trường trẻ, cởi mở."
        },
        "frontend": {
            "title": "Frontend ReactJS Developer (Interactive Edtech Interface)",
            "skills": ["React", "TypeScript", "JavaScript", "Tailwind CSS"],
            "desc": "Thiết kế giao diện học tập tương tác cao, sinh động dành cho học sinh. Tích hợp các tính năng video call học tập trực tuyến, bảng vẽ ảo tương tác và hệ thống trò chơi hóa học tập (gamification).",
            "req": "Tối thiểu 1 năm kinh nghiệm lập trình ReactJS. Tư duy logic tốt, khả năng tối ưu hóa trải nghiệm người dùng (UX) và làm việc phối hợp nhóm tốt.",
            "benefits": "Hỗ trợ ăn trưa, gửi xe miễn phí tại tòa nhà văn phòng. Thưởng hiệu quả công việc định kỳ. Các chế độ BHXH, BHYT theo quy định nhà nước."
        },
        "default": {
            "title": "Edtech Product Developer (Node.js / React)",
            "skills": ["Node.js", "React", "MongoDB", "TypeScript", "Git"],
            "desc": "Tham gia xây dựng sản phẩm công nghệ giáo dục mới của công ty, tối ưu các tính năng lớp học ảo và bài tập tự luyện.",
            "req": "Kinh nghiệm JavaScript/TypeScript vững chắc. Từng phát triển ứng dụng Web hoàn chỉnh với Node.js và React. Thích nghi nhanh với công nghệ mới.",
            "benefits": "Lương cạnh tranh, đóng BHXH full lương. Review tăng lương hàng năm. Hưởng các chương trình ưu đãi học tập nội bộ."
        }
    },
    "HEALTHTECH": {
        "backend": {
            "title": "Python / Node.js Backend Engineer (Healthtech Platform)",
            "skills": ["Python", "Node.js", "PostgreSQL", "REST API"],
            "desc": "Thiết kế và xây dựng hệ thống quản lý hồ sơ y tế điện tử và đặt lịch khám bệnh trực tuyến bảo mật cao. Thiết lập các cổng kết nối API tích hợp với hệ thống quản lý của các bệnh viện đối tác.",
            "req": "Tối thiểu 2 năm kinh nghiệm làm Backend với Python hoặc Node.js. Ý thức cao về bảo mật thông tin và quyền riêng tư dữ liệu cá nhân (HIPAA).",
            "benefits": "Gói bảo hiểm sức khỏe cá nhân đặc biệt. Nghỉ phép năm lên tới 15 ngày/năm. Thưởng cuối năm và xét tăng lương định kỳ."
        },
        "mobile": {
            "title": "React Native Developer (Doctor Consult App)",
            "skills": ["React Native", "Mobile", "TypeScript", "JavaScript"],
            "desc": "Phát triển ứng dụng di động tư vấn sức khỏe từ xa dành cho bệnh nhân và bác sĩ. Tối ưu hóa tính năng gọi điện thoại video trực tiếp (Telemedicine) và tích hợp các cảm biến đo chỉ số sức khỏe di động.",
            "req": "Tối thiểu 2 năm kinh nghiệm lập trình React Native. Có kinh nghiệm làm việc với WebRTC hoặc các dịch vụ truyền phát video thời gian thực.",
            "benefits": "Hỗ trợ 100% lương trong thời gian thử việc. Cơ hội nhận thưởng dự án đột phá. Văn phòng làm việc hiện đại, thân thiện."
        },
        "default": {
            "title": "Healthtech Web Engineer (ReactJS)",
            "skills": ["React", "TypeScript", "JavaScript", "Tailwind CSS"],
            "desc": "Xây dựng cổng thông tin y tế, cổng tra cứu thuốc và quản lý toa thuốc trực tuyến cho bệnh nhân. Cải tiến giao diện thân thiện với người dùng lớn tuổi.",
            "req": "Tối thiểu 1.5 năm kinh nghiệm lập trình ReactJS, thành thạo Tailwind CSS hoặc CSS in JS. Có kỹ năng tối ưu hóa UI/UX tốt.",
            "benefits": "Thưởng lễ tết đầy đủ, lương tháng 13. Khám sức khỏe toàn diện định kỳ. Môi trường công nghệ nhân văn."
        }
    },
    "TELECOM_NETWORKING": {
        "embedded": {
            "title": "Embedded Software Engineer (C/C++ / Linux / Firmware)",
            "skills": ["C/C++", "Embedded", "Linux", "Python"],
            "desc": "Thiết kế và lập trình phần mềm nhúng (Firmware/OS drivers) cho các thiết bị định tuyến mạng, thiết bị thu phát sóng 5G và IoT thông minh. Giao tiếp phần cứng, tối ưu hóa tiêu thụ năng lượng và xử lý ngắt thời gian thực.",
            "req": "Tốt nghiệp đại học chuyên ngành Điện tử viễn thông, CNTT hoặc Hệ thống nhúng. Thành thạo lập trình C/C++, hiểu biết về kiến trúc vi điều khiển (ARM) và lập trình Linux nhúng.",
            "benefits": "Được làm việc trực tiếp trong các dự án phát triển thiết bị quốc gia. Xét tăng lương hàng năm và thưởng sáng kiến công nghệ đột phá. Cơ hội đào tạo nước ngoài."
        },
        "network": {
            "title": "Network Engineer / Cloud DevOps (Telecom Cloud Services)",
            "skills": ["DevOps", "Network", "Linux", "Cloud"],
            "desc": "Cấu hình, quản trị và tối ưu hóa hệ thống mạng viễn thông lõi và đám mây riêng (Private Cloud). Thiết lập hạ tầng SDN, cấu hình router/switch chịu tải lớn và tự động hóa triển khai hạ tầng ảo hóa.",
            "req": "Có kiến thức sâu sắc về giao thức mạng TCP/IP, định tuyến (BGP, OSPF) và bảo mật mạng. Có chứng chỉ CCNA/CCNP hoặc tương đương. Kinh nghiệm quản trị Linux tốt.",
            "benefits": "Phụ cấp điện thoại, phụ cấp ăn trưa hàng tháng. Thưởng lễ tết, lương tháng 13 cùng thưởng thâm niên hấp dẫn. Bảo hiểm y tế nâng cao."
        },
        "default": {
            "title": "Telecom Software System Developer",
            "skills": ["Java", "Python", "SQL", "Linux", "Docker"],
            "desc": "Phát triển các phần mềm quản lý hệ thống tổng đài, phân tích lưu lượng cuộc gọi và xử lý dữ liệu cước viễn thông thời gian thực chịu tải lớn.",
            "req": "Có kinh nghiệm lập trình Java hoặc Python tối thiểu 2 năm. Sử dụng thành thạo Linux. Am hiểu về tối ưu hóa cơ sở dữ liệu quan hệ.",
            "benefits": "Thưởng lễ tết, thưởng quý cạnh tranh. Cơ hội thăng tiến lên các vị trí quản lý công nghệ. Môi trường tập đoàn chuyên nghiệp."
        }
    },
    "SOFTWARE_SERVICES": {
        "java": {
            "title": "Senior Java Spring Boot Developer (Enterprise Solutions)",
            "skills": ["Java", "Spring Boot", "PostgreSQL", "Docker", "Git"],
            "desc": "Tham gia phát triển các dự án phần mềm doanh nghiệp (ERP, CRM) quy mô lớn cho các đối tác quốc tế (Nhật Bản, Mỹ, Singapore). Thiết kế kiến trúc module sạch, tối ưu hóa câu lệnh SQL và triển khai ứng dụng.",
            "req": "Tối thiểu 3 năm kinh nghiệm lập trình Java. Thành thạo Spring Boot, Hibernate/JPA và thiết kế cơ sở dữ liệu quan hệ (SQL Server, PostgreSQL, MySQL). Sử dụng tốt Git và quy trình Agile.",
            "benefits": "Lương thử việc 100%. Review lương 2 lần/năm. Thưởng tháng 13 + thưởng dự án. Lớp đào tạo ngoại ngữ (tiếng Anh/tiếng Nhật) miễn phí tại công ty."
        },
        "dotnet": {
            "title": ".NET Backend Engineer (C# / .NET Core 8 / Microservices)",
            "skills": ["C#", ".NET", "SQL", "REST API", "Git"],
            "desc": "Phát triển các hệ thống web APIs và dịch vụ backend sử dụng .NET Core. Tham gia phân tích yêu cầu kỹ thuật từ khách hàng nước ngoài, thiết kế sơ đồ dữ liệu và viết unit tests đảm bảo chất lượng code.",
            "req": "Tối thiểu 2 năm kinh nghiệm lập trình C# và .NET Core. Am hiểu Entity Framework, RESTful API. Có tư duy logic tốt, biết cách tối ưu hóa hiệu năng truy vấn DB.",
            "benefits": "Thu nhập cạnh tranh thỏa thuận theo năng lực. Tham gia các hoạt động thể thao, du lịch hè hoành tráng của công ty. Bảo hiểm sức khỏe VIP Care."
        },
        "fullstack": {
            "title": "Full-Stack Engineer (ReactJS & Node.js / TypeScript)",
            "skills": ["React", "Node.js", "TypeScript", "JavaScript", "SQL"],
            "desc": "Đảm nhận phát triển cả giao diện frontend (React) và logic backend (Node.js/TypeScript). Xây dựng ứng dụng hoàn chỉnh từ đầu, thiết lập luồng xác thực (JWT), kết nối cơ sở dữ liệu và triển khai lên máy chủ.",
            "req": "Có tối thiểu 2 năm kinh nghiệm ở vị trí Fullstack Developer. Sử dụng tốt ReactJS và Node.js. Nắm vững TypeScript và viết clean code.",
            "benefits": "Được làm việc trực tiếp với khách hàng nước ngoài, cải thiện kỹ năng giao tiếp tiếng Anh. Xét duyệt tăng lương định kỳ cạnh tranh. teabreak, hoa quả miễn phí hàng tuần."
        },
        "qa": {
            "title": "QA QC Engineer (Manual & Automation Testing)",
            "skills": ["Testing", "QA QC", "Automation Test", "Java", "Python"],
            "desc": "Viết kịch bản kiểm thử (Test Cases), chuẩn bị dữ liệu test và thực hiện kiểm thử chức năng hệ thống ứng dụng web/mobile. Phát triển các script kiểm thử tự động sử dụng Selenium hoặc Cypress để giảm thời gian regression test.",
            "req": "Tối thiểu 1 năm kinh nghiệm làm QA/QC Tester. Có hiểu biết về quy trình kiểm thử phần mềm, viết test case tốt. Ưu tiên ứng viên có thể viết script automation test (Java/Python/JS).",
            "benefits": "Lương tháng 13 và thưởng dự án hàng quý. Hỗ trợ kinh phí thi các chứng chỉ ISTQB quốc tế. Môi trường làm việc thân thiện, hòa đồng, nhiều cơ hội phát triển bản thân."
        },
        "default": {
            "title": "Software Engineer (Web / Mobile Developer)",
            "skills": ["React", "JavaScript", "TypeScript", "SQL", "Git"],
            "desc": "Tham gia vào quy trình phát triển và bảo trì ứng dụng web hoặc ứng dụng di động cho khách hàng. Viết mã nguồn sạch, tối ưu và thực hiện sửa lỗi kịp thời theo yêu cầu.",
            "req": "Có kinh nghiệm lập trình JavaScript/TypeScript và một framework hiện đại (React/Angular/Vue/Node.js). Khả năng làm việc độc lập và hợp tác nhóm tốt.",
            "benefits": "Lương thưởng thỏa thuận hấp dẫn. Hỗ trợ tiền ăn trưa, trà café miễn phí. Review lương 2 lần/năm."
        }
    }
}

# Advanced skill mapping logic to match template string tags to actual database GUIDs
def map_skill_to_db(skill_name, skill_map):
    s = skill_name.lower().strip()
    if s in skill_map:
        return skill_map[s]
    
    aliases = {
        'reactjs': 'react',
        'react native': 'react native',
        'golang': 'go (golang)',
        'go': 'go (golang)',
        '.net': 'c#',
        'net': 'c#',
        'nodejs': 'node.js',
        'node': 'node.js',
        'vuejs': 'vue.js',
        'vue': 'vue.js',
        'angularjs': 'angular',
        'c++': 'c/c++',
        'c': 'c/c++',
        'aws': 'aws ec2',
        'gcp': 'google cloud platform (gcp)',
        'azure': 'microsoft azure',
        'kubernetes': 'kubernetes',
        'k8s': 'kubernetes',
        'qa': 'testing',
        'tester': 'testing',
        'test': 'testing',
        'sql server': 'microsoft sql server',
        'mssql': 'microsoft sql server',
        'spring boot': 'java spring boot',
        'spring': 'java spring boot',
        'nextjs': 'next.js',
        'nestjs': 'nestjs',
        'express': 'express.js',
        'laravel': 'laravel',
        'fastapi': 'fastapi',
        'ml': 'machine learning',
        'dl': 'deep learning',
        'nlp': 'natural language processing (nlp)',
        'ai': 'generative ai',
        'microservices': 'microservices architecture',
        'rest api': 'rest api',
        'rest': 'rest api',
        'rabbitmq': 'rabbitmq',
    }
    
    if s in aliases:
        target = aliases[s]
        if target in skill_map:
            return skill_map[target]
            
    for db_name, db_id in skill_map.items():
        if s in db_name or db_name in s:
            return db_id
            
    return None

def main():
    print("=== ĐANG KHỞI CHẠY CẬP NHẬT 1,000 TIN TUYỂN DỤNG THẬT ===")
    
    try:
        conn_comp = psycopg2.connect(host=DB_CONFIG["host"], port=DB_CONFIG["port"], dbname="CompanyService", user=DB_CONFIG["user"], password=DB_CONFIG["password"])
        conn_job = psycopg2.connect(host=DB_CONFIG["host"], port=DB_CONFIG["port"], dbname="JobService", user=DB_CONFIG["user"], password=DB_CONFIG["password"])
        
        cur_comp = conn_comp.cursor()
        cur_job = conn_job.cursor()
    except Exception as e:
        print(f"❌ Lỗi kết nối CSDL: {e}")
        return

    # 1. Load companies and map their domains
    cur_comp.execute('SELECT "Id", "Name" FROM "Companies"')
    companies_data = cur_comp.fetchall()
    company_category_map = {row[0]: get_company_category(row[1]) for row in companies_data}
    company_name_map = {row[0]: row[1] for row in companies_data}
    print(f"Đã tải {len(company_category_map)} công ty và phân nhóm lĩnh vực thành công.")

    # 2. Load skills map
    cur_job.execute('SELECT "Id", "Name" FROM "Skills"')
    skills_data = cur_job.fetchall()
    skill_map = {row[1].lower().strip(): row[0] for row in skills_data}
    print(f"Đã tải {len(skill_map)} kỹ năng phục vụ so khớp.")

    # 3. Load all jobs
    cur_job.execute('SELECT "Id", "CompanyId", "Name" FROM "Jobs"')
    jobs = cur_job.fetchall()
    print(f"Tổng số tin tuyển dụng cần cập nhật: {len(jobs)} jobs.")

    updated_jobs = 0
    job_skills_to_insert = []
    
    for idx, (job_id, comp_id, old_title) in enumerate(jobs):
        category = company_category_map.get(comp_id, 'SOFTWARE_SERVICES')
        comp_name = company_name_map.get(comp_id, 'Công ty Công nghệ')
        
        # Pick template based on old job title keywords to keep tech alignment
        title_lower = old_title.lower()
        role_key = 'default'
        
        cat_templates = TEMPLATES.get(category, TEMPLATES['SOFTWARE_SERVICES'])
        
        if category == 'AI_ML':
            if 'vision' in title_lower or 'image' in title_lower or 'c++' in title_lower:
                role_key = 'computer_vision'
            elif 'data' in title_lower or 'spark' in title_lower or 'kafka' in title_lower:
                role_key = 'data_engineer'
            elif 'python' in title_lower or 'model' in title_lower or 'machine' in title_lower or 'deep' in title_lower or 'nlp' in title_lower:
                role_key = 'python'
        elif category == 'FINTECH_BANKING':
            if 'architect' in title_lower or 'lead' in title_lower or 'manager' in title_lower:
                role_key = 'architect'
            elif 'dba' in title_lower or 'database' in title_lower or 'sql' in title_lower:
                role_key = 'dba'
            elif 'java' in title_lower or 'spring' in title_lower:
                role_key = 'java'
        elif category == 'ECOMMERCE_RETAIL':
            if 'react' in title_lower or 'next' in title_lower or 'front' in title_lower or 'ui' in title_lower:
                role_key = 'frontend'
            elif 'native' in title_lower or 'ios' in title_lower or 'android' in title_lower or 'mobile' in title_lower:
                role_key = 'mobile'
            elif 'go' in title_lower or 'golang' in title_lower:
                role_key = 'golang'
        elif category == 'LOGISTICS':
            if 'devops' in title_lower or 'cloud' in title_lower or 'kubernetes' in title_lower or 'infra' in title_lower:
                role_key = 'devops'
            elif 'node' in title_lower or 'nest' in title_lower or 'js' in title_lower or 'express' in title_lower:
                role_key = 'nodejs'
        elif category == 'GAME':
            if 'unity' in title_lower or 'c#' in title_lower or 'game' in title_lower:
                role_key = 'unity'
            elif 'artist' in title_lower or '3d' in title_lower or 'texture' in title_lower:
                role_key = 'artist'
        elif category == 'CYBERSECURITY':
            if 'pentest' in title_lower or 'red' in title_lower or 'hack' in title_lower:
                role_key = 'pentest'
            elif 'soc' in title_lower or 'security' in title_lower or 'monitor' in title_lower:
                role_key = 'soc'
        elif category == 'EDTECH':
            if 'react' in title_lower or 'front' in title_lower or 'ui' in title_lower:
                role_key = 'frontend'
            elif 'python' in title_lower or 'django' in title_lower or 'flask' in title_lower:
                role_key = 'backend'
        elif category == 'HEALTHTECH':
            if 'native' in title_lower or 'ios' in title_lower or 'android' in title_lower or 'mobile' in title_lower:
                role_key = 'mobile'
            elif 'python' in title_lower or 'node' in title_lower or 'backend' in title_lower:
                role_key = 'backend'
        elif category == 'TELECOM_NETWORKING':
            if 'embedded' in title_lower or 'firmware' in title_lower or 'hardware' in title_lower or 'c++' in title_lower:
                role_key = 'embedded'
            elif 'network' in title_lower or 'devops' in title_lower or 'sys' in title_lower:
                role_key = 'network'
        
        # Fallback to software services rules if default is chosen but old title matches generic stack
        if role_key == 'default':
            if 'java' in title_lower:
                if 'java' in cat_templates: role_key = 'java'
                elif 'backend' in cat_templates: role_key = 'backend'
            elif 'net' in title_lower or 'c#' in title_lower:
                if 'dotnet' in cat_templates: role_key = 'dotnet'
            elif 'react' in title_lower or 'front' in title_lower:
                if 'frontend' in cat_templates: role_key = 'frontend'
            elif 'node' in title_lower or 'nest' in title_lower or 'express' in title_lower:
                if 'nodejs' in cat_templates: role_key = 'nodejs'
                elif 'fullstack' in cat_templates: role_key = 'fullstack'
            elif 'python' in title_lower:
                if 'python' in cat_templates: role_key = 'python'
                elif 'backend' in cat_templates: role_key = 'backend'
            elif 'test' in title_lower or 'qa' in title_lower or 'qc' in title_lower:
                if 'qa' in cat_templates: role_key = 'qa'
                elif 'pentest' in cat_templates: role_key = 'pentest'
        
        # Get selected template
        template = cat_templates.get(role_key, cat_templates['default'])
        
        # Format new job name based on company context (strip mismatched prefixes if any)
        new_title = template["title"]
        if "hcm" in title_lower or "tp. hồ chí minh" in title_lower or "tp.hcm" in title_lower:
            if not new_title.startswith("[HCM]"):
                new_title = f"[HCM] {new_title}"
        elif "hà nội" in title_lower or "ha noi" in title_lower:
            if not new_title.startswith("[HN]"):
                new_title = f"[HN] {new_title}"
                
        # Update Job in DB
        cur_job.execute('''
            UPDATE "Jobs"
            SET "Name" = %s, "Description" = %s, "Requirements" = %s, "Benefits" = %s, "Category" = %s
            WHERE "Id" = %s
        ''', (new_title, template["desc"], template["req"], template["benefits"], category, job_id))
        
        # Map template skills to DB IDs
        for skill_tag in template["skills"]:
            skill_guid = map_skill_to_db(skill_tag, skill_map)
            if skill_guid:
                job_skills_to_insert.append((job_id, skill_guid))
                
        updated_jobs += 1
        if updated_jobs % 100 == 0:
            print(f"  -> Đã cập nhật xong {updated_jobs}/1000 jobs.")

    # Commit jobs update
    conn_job.commit()
    print("🧹 Đang làm sạch bảng JobSkills cũ...")
    cur_job.execute('DELETE FROM "JobSkills"')
    conn_job.commit()

    # Bulk insert new JobSkills
    print("🚀 Đang tiến hành chèn JobSkills mới...")
    job_skills_inserted = 0
    unique_job_skills = set(job_skills_to_insert)
    
    for jid, sid in unique_job_skills:
        try:
            cur_job.execute('INSERT INTO "JobSkills" ("JobId", "SkillId") VALUES (%s, %s) ON CONFLICT DO NOTHING', (jid, sid))
            conn_job.commit()
            job_skills_inserted += 1
        except Exception as e:
            conn_job.rollback()
            print(f"  [Warning] Lỗi chèn kỹ năng ({jid}, {sid}): {e}")

    print(f"✅ Đã cập nhật thành công {updated_jobs} tin tuyển dụng!")
    print(f"✅ Đã liên kết thành công {job_skills_inserted} bản ghi kỹ năng mới!")

    cur_comp.close()
    cur_job.close()
    conn_comp.close()
    conn_job.close()
    print("\n=== HOÀN THÀNH CẬP NHẬT JOBS ===")

if __name__ == "__main__":
    main()
