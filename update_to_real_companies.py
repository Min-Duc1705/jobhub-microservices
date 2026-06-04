import os
import sys
import re
import uuid
import json
import random
import psycopg2
import unicodedata

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

def make_slug(name):
    clean_name = remove_accents_str(name.lower())
    clean_name = re.sub(r'[^a-z0-9\s]', '', clean_name)
    parts = clean_name.split()
    if not parts:
        return "hr"
    return ".".join(parts)

# 100 Real IT and Tech Companies operating in Vietnam (No overlap with original 60)
REAL_COMPANIES = [
    {
        "name": "Lazada Vietnam",
        "website": "https://www.lazada.vn",
        "email": "recruitment@lazada.vn",
        "industry": "E-commerce & Retail Tech",
        "address": "Lầu 19, Tòa nhà Saigon Centre, 67 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Lazada Group là một trong những nền tảng thương mại điện tử hàng đầu tại Đông Nam Á, kết nối hàng triệu người tiêu dùng và nhà bán hàng thông qua công nghệ và logistics hiện đại."
    },
    {
        "name": "VCCorp",
        "website": "https://vccorp.vn",
        "email": "hr@vccorp.vn",
        "industry": "Internet & Digital Content",
        "address": "Tòa nhà Center Building, Số 85 Vũ Trọng Phụng, Thanh Xuân, Hà Nội",
        "size": "ENTERPRISE",
        "description": "VCCorp là công ty đi đầu trong lĩnh vực truyền thông số và công nghệ internet tại Việt Nam, sở hữu hệ sinh thái adtech, báo chí trực tuyến và điện toán đám mây lớn."
    },
    {
        "name": "Tencent Vietnam",
        "website": "https://www.tencent.com",
        "email": "recruitment.vn@tencent.com",
        "industry": "Internet Services & Gaming",
        "address": "Tòa nhà Deutsches Haus, 33 Lê Duẩn, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Tencent là tập đoàn công nghệ toàn cầu chuyên cung cấp dịch vụ internet, trò chơi trực tuyến và giải pháp đám mây chất lượng cao cho hàng triệu người dùng toàn cầu."
    },
    {
        "name": "Garena Vietnam",
        "website": "https://www.garena.vn",
        "email": "careers@garena.vn",
        "industry": "Online Gaming & Digital Entertainment",
        "address": "Tòa nhà Saigon Centre, 67 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Garena là nhà phát hành trò chơi trực tuyến hàng đầu tại Đông Nam Á, sở hữu các tựa game Esport nổi tiếng thế giới và nền tảng kết nối game thủ chuyên nghiệp."
    },
    {
        "name": "Tinhvan Group",
        "website": "https://tinhvan.com",
        "email": "recruitment@tinhvan.com",
        "industry": "Software & Digital Solutions",
        "address": "Tầng 8, Tòa nhà Khách sạn Thể thao, Hacinco, Thanh Xuân, Hà Nội",
        "size": "SME",
        "description": "Tinhvan Group là một trong những đơn vị công nghệ thông tin lâu đời nhất Việt Nam, chuyên cung cấp các giải pháp phần mềm giáo dục, quản trị doanh nghiệp và nội dung số."
    },
    {
        "name": "HPT Vietnam",
        "website": "https://hpt.vn",
        "email": "recruitment@hpt.vn",
        "industry": "IT Solutions & System Integration",
        "address": "Tầng 9, Tòa nhà Paragon, Số 3 Nguyễn Lương Bằng, Quận 7, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "HPT là nhà cung cấp giải pháp và dịch vụ công nghệ thông tin uy tín hàng đầu Việt Nam, chuyên về tích hợp hệ thống, an ninh mạng và phát triển phần mềm doanh nghiệp."
    },
    {
        "name": "FAST Software Company",
        "website": "https://fast.com.vn",
        "email": "hr@fast.com.vn",
        "industry": "ERP & Cloud Accounting Software",
        "address": "Tòa nhà FAST, Số 29 Nguyễn Bỉnh Khiêm, Đa Kao, Quận 1, TP. Hồ Chí Minh",
        "size": "SME",
        "description": "FAST chuyên phát triển và tư vấn ứng dụng phần mềm quản trị doanh nghiệp (ERP) và kế toán đám mây cho các doanh nghiệp vừa và nhỏ tại Việt Nam."
    },
    {
        "name": "Katalon Vietnam",
        "website": "https://katalon.com",
        "email": "recruitment@katalon.com",
        "industry": "Software Testing Tools",
        "address": "Tòa nhà Flemington, 182 Lê Đại Hành, Quận 11, TP. Hồ Chí Minh",
        "size": "SME",
        "description": "Katalon phát triển nền tảng kiểm thử tự động chất lượng cao (Katalon Studio) được sử dụng rộng rãi bởi hàng triệu kỹ sư QA toàn cầu."
    },
    {
        "name": "DEK Technologies",
        "website": "https://www.dektech.com.au",
        "email": "careers.vn@dektech.com.au",
        "industry": "Telecommunications & Embedded Software",
        "address": "Tòa nhà Waseco, 10 Phổ Quang, Phường 2, Tân Bình, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "DEK Technologies chuyên thiết kế và phát triển phần mềm viễn thông, hệ thống nhúng và giải pháp cloud chất lượng cao cho các đối tác toàn cầu."
    },
    {
        "name": "NFQ Asia",
        "website": "https://www.nfq.asia",
        "email": "hr.vn@nfq.asia",
        "industry": "E-commerce Tech & Scale-ups development",
        "address": "Tầng 5, Tòa nhà Green Plaza, 223 Trần Phú, Hải Châu, Đà Nẵng",
        "size": "ENTERPRISE",
        "description": "NFQ Asia là chuyên gia phát triển phần mềm và tối ưu hóa hạ tầng công nghệ cho các dự án thương mại điện tử lớn trên thị trường Châu Âu và Châu Á."
    },
    {
        "name": "Eastgate Software",
        "website": "https://eastgate-software.com",
        "email": "careers@eastgate-software.com",
        "industry": "Software Development & Outsourcing",
        "address": "Tòa nhà Toyota Mỹ Đình, 15 Phạm Hùng, Mỹ Đình 2, Nam Từ Liêm, Hà Nội",
        "size": "SME",
        "description": "Eastgate Software chuyên cung cấp dịch vụ phát triển phần mềm chất lượng cao cho thị trường Nhật Bản và Châu Âu với văn phòng tại Hà Nội."
    },
    {
        "name": "BAP IT Co.",
        "website": "https://bap-software.net",
        "email": "recruitment@bap-software.net",
        "industry": "Blockchain, AI & Web Development",
        "address": "Tòa nhà BAP, 81 Quang Trung, Hải Châu, Đà Nẵng",
        "size": "ENTERPRISE",
        "description": "BAP Software cung cấp dịch vụ gia công phần mềm, tích hợp trí tuệ nhân tạo (AI), công nghệ Blockchain và phát triển ứng dụng di động cho thị trường Nhật Bản."
    },
    {
        "name": "Gear Inc.",
        "website": "https://www.gearinc.com",
        "email": "jobs@gearinc.com",
        "industry": "Game Development & Outsourcing Services",
        "address": "Tòa nhà Peakview Plaza, 36 Hoàng Cầu, Ô Chợ Dừa, Đống Đa, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Gear Inc. là công ty đa quốc gia chuyên về phát triển game di động, kiểm định chất lượng phần mềm và quản trị nội dung số cho khách hàng toàn cầu."
    },
    {
        "name": "Panasonic R&D Center Vietnam",
        "website": "https://www.panasonic.com/vn",
        "email": "recruitment.prdv@vn.panasonic.com",
        "industry": "Hardware R&D & Embedded Systems",
        "address": "Tòa nhà Sunrise, 90 Trần Thái Tông, Cầu Giấy, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Trung tâm Nghiên cứu và Phát triển Panasonic tại Việt Nam chuyên thiết kế thiết bị điện tử, giải pháp nhúng thông minh và phát triển IoT cho tập đoàn toàn cầu."
    },
    {
        "name": "Home Credit Vietnam",
        "website": "https://www.homecredit.vn",
        "email": "careers@homecredit.vn",
        "industry": "Fintech & Consumer Finance",
        "address": "Tòa nhà Phụ Nữ, 20 Nguyễn Đăng Giai, Thảo Điền, Quận 2, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Home Credit là tập đoàn tài chính tiêu dùng đa quốc gia, áp dụng công nghệ và dữ liệu lớn để cung cấp các giải pháp vay tiêu dùng thông minh."
    },
    {
        "name": "NEC Vietnam",
        "website": "https://vn.nec.com",
        "email": "careers@nec.vn",
        "industry": "System Integration & Biometrics Tech",
        "address": "Tòa nhà Etown 1, 364 Cộng Hòa, Tân Bình, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "NEC Vietnam cung cấp giải pháp nhận diện sinh trắc học thông minh, tích hợp hệ thống mạng viễn thông và dịch vụ quản trị hạ tầng IT doanh nghiệp."
    },
    {
        "name": "Hitachi Vantara Vietnam",
        "website": "https://www.hitachivantara.com",
        "email": "careers.vn@hitachivantara.com",
        "industry": "Big Data & Storage Solutions",
        "address": "Tòa nhà Helix, Số 5 Nguyễn Gia Thiều, Quận 3, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Hitachi Vantara chuyên cung cấp dịch vụ quản trị dữ liệu lớn, lưu trữ đám mây và phân tích số liệu thông minh phục vụ chuyển đổi số doanh nghiệp."
    },
    {
        "name": "VTI Software",
        "website": "https://vti.com.vn",
        "email": "hr@vti.com.vn",
        "industry": "Software Development & IT Outsourcing",
        "address": "Tòa nhà Mễ Trì Plaza, Nam Từ Liêm, Hà Nội",
        "size": "ENTERPRISE",
        "description": "VTI Software cung cấp dịch vụ gia công xuất khẩu phần mềm chất lượng cao và chuyển đổi số cho thị trường Nhật Bản, Hàn Quốc và Việt Nam."
    },
    {
        "name": "Pyco Group",
        "website": "https://www.pycogroup.com",
        "email": "jobs@pycogroup.com",
        "industry": "Digital Transformation & Web Development",
        "address": "Tòa nhà Somerset Chancellor Court, 21-23 Nguyễn Thị Minh Khai, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Pyco Group chuyên tư vấn chuyển đổi số doanh nghiệp và xây dựng hạ tầng web, ứng dụng thương mại điện tử chuyên nghiệp cho thị trường quốc tế."
    },
    {
        "name": "Wizeline Vietnam",
        "website": "https://www.wizeline.com",
        "email": "recruitment.vn@wizeline.com",
        "industry": "AI Research & Digital Product Engineering",
        "address": "Tòa nhà Deutsches Haus, 33 Lê Duẩn, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Wizeline là nhà cung cấp dịch vụ thiết kế và kỹ thuật phần mềm toàn cầu, hợp tác với các tập đoàn lớn để xây dựng sản phẩm số và ứng dụng trí tuệ nhân tạo."
    },
    {
        "name": "Napas",
        "website": "https://napas.com.vn",
        "email": "recruitment@napas.com.vn",
        "industry": "Payment Gateway & Fintech",
        "address": "Tòa nhà 18 Lạc Trung, Hai Bà Trưng, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Napas vận hành hệ thống chuyển mạch tài chính quốc gia và bù trừ điện tử lớn nhất Việt Nam, kết nối hàng chục ngân hàng thành viên."
    },
    {
        "name": "Enclave",
        "website": "https://enclave.vn",
        "email": "hr@enclave.vn",
        "industry": "Software Engineering & Outsourcing",
        "address": "Tòa nhà Enclave, 453 Nguyễn Hữu Thọ, Cẩm Lệ, Đà Nẵng",
        "size": "SME",
        "description": "Enclave cung cấp dịch vụ gia công phần mềm bền vững và chuyên nghiệp cho các khách hàng Mỹ, Singapore và Châu Âu với đội ngũ kỹ sư giàu kinh nghiệm."
    },
    {
        "name": "Global CyberSoft",
        "website": "https://www.globalcybersoft.com",
        "email": "careers@gcs-vn.com",
        "industry": "System Integration & Embedded Software",
        "address": "Tòa nhà Helios, Công viên phần mềm Quang Trung, Quận 12, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Global CyberSoft (một thành viên của Hitachi Consulting) chuyên cung cấp dịch vụ giải pháp nhúng thiết bị thông minh và tích hợp hệ thống sản xuất (MES)."
    },
    {
        "name": "FPT Information System",
        "website": "https://www.fpt-is.com",
        "email": "hr.fis@fpt.com.vn",
        "industry": "System Integration & Digital Public Services",
        "address": "Tòa nhà Keangnam Landmark 72, Phạm Hùng, Cầu Giấy, Hà Nội",
        "size": "ENTERPRISE",
        "description": "FPT IS là đơn vị thành viên của tập đoàn FPT chuyên xây dựng các hệ thống công nghệ công cộng, ERP chính phủ và giải pháp tài chính ngân hàng lõi."
    },
    {
        "name": "FPT Telecom",
        "website": "https://fpt.vn",
        "email": "careers.telecom@fpt.com.vn",
        "industry": "Telecommunications & Internet Provider",
        "address": "Tòa nhà FPT Cầu Giấy, 17 Duy Tân, Dịch Vọng Hậu, Cầu Giấy, Hà Nội",
        "size": "ENTERPRISE",
        "description": "FPT Telecom là nhà cung cấp hạ tầng internet cáp quang, truyền hình tương tác và dịch vụ trung tâm dữ liệu đám mây hàng đầu tại Việt Nam."
    },
    {
        "name": "CMC Telecom",
        "website": "https://cmctelecom.vn",
        "email": "hr@cmctelecom.vn",
        "industry": "Telecom infrastructure & Cloud Service",
        "address": "Tòa nhà CMC, Duy Tân, Cầu Giấy, Hà Nội",
        "size": "ENTERPRISE",
        "description": "CMC Telecom cung cấp hạ tầng kết nối viễn thông cao cấp trung lập và dịch vụ đám mây doanh nghiệp (Multi-cloud) hàng đầu Việt Nam."
    },
    {
        "name": "Netnam",
        "website": "https://netnam.vn",
        "email": "recruitment@netnam.vn",
        "industry": "Premium Internet Service & Cybersecurity",
        "address": "Tòa nhà Viện Công nghệ thông tin, 18 Hoàng Quốc Việt, Cầu Giấy, Hà Nội",
        "size": "SME",
        "description": "Netnam là nhà tiên phong cung cấp dịch vụ internet chất lượng cao và giải pháp quản trị bảo mật mạng thông minh cho các khách hàng khách sạn 5 sao và doanh nghiệp."
    },
    {
        "name": "KBTG Vietnam",
        "website": "https://www.kbtg.tech",
        "email": "careers.vn@kbtg.tech",
        "industry": "Fintech & Banking Technology",
        "address": "Tòa nhà Friendship Tower, 156 Lê Duẩn, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "KBTG Vietnam (thuộc tập đoàn tài chính Kasikornbank) phát triển các ứng dụng ngân hàng số K PLUS và các giải pháp fintech tối tân phục vụ thị trường AEC+3."
    },
    {
        "name": "Woori Bank IT Center",
        "website": "https://wooribank.com.vn",
        "email": "recruitment@wooribank.com.vn",
        "industry": "Digital Banking & Finance Technology",
        "address": "Tòa nhà Keangnam Landmark 72, Phạm Hùng, Cầu Giấy, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Trung tâm Công nghệ Woori Bank chịu trách nhiệm phát triển hạ tầng ngân hàng lõi và các ứng dụng thanh toán di động tiên tiến tại Việt Nam."
    },
    {
        "name": "Shinhan Bank IT Center",
        "website": "https://shinhan.com.vn",
        "email": "hr.it@shinhan.com.vn",
        "industry": "Banking Technology & Fintech Solutions",
        "address": "Tòa nhà Empress Tower, 138-142 Hai Bà Trưng, Đa Kao, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Trung tâm Công nghệ Thông tin Shinhan Bank Việt Nam đảm nhận phát triển các hệ thống thanh toán di động SOL App và hạ tầng bảo mật tài chính ngân hàng."
    },
    {
        "name": "HSBC IT Center",
        "website": "https://www.hsbc.com.vn",
        "email": "recruitment@hsbc.com.vn",
        "industry": "Global Financial IT & Fintech",
        "address": "Tòa nhà Metropolitan, 235 Đồng Khởi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "HSBC IT Center chuyên quản trị các luồng hệ thống thanh toán liên ngân hàng toàn cầu và hỗ trợ phát triển các dịch vụ internet banking bảo mật cao."
    },
    {
        "name": "Techbase Vietnam",
        "website": "https://www.techbasevn.com",
        "email": "recruitment@techbasevn.com",
        "industry": "Web development & E-commerce System",
        "address": "Tòa nhà Vincom Center, 72 Lê Thánh Tôn, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
        "size": "SME",
        "description": "Techbase Vietnam là công ty con của Yahoo Japan Group, phát triển và tối ưu hóa hệ thống mua sắm trực tuyến, dịch vụ bản đồ và công cụ internet hàng đầu Nhật Bản."
    },
    {
        "name": "Cybozu Vietnam",
        "website": "https://cybozu.vn",
        "email": "recruitment@cybozu.vn",
        "industry": "Collaborative Software & Groupware",
        "address": "Tòa nhà Saigon Trade Center, 37 Tôn Đức Thắng, Quận 1, TP. Hồ Chí Minh",
        "size": "SME",
        "description": "Cybozu Vietnam phát triển hệ thống phần mềm cộng tác doanh nghiệp (Kintone, Garoon) giúp số hóa quy trình quản trị doanh nghiệp hiệu quả."
    },
    {
        "name": "Mercari Vietnam",
        "website": "https://www.mercari.com",
        "email": "careers-vn@mercari.com",
        "industry": "C2C Marketplace & Mobile Tech",
        "address": "Tòa nhà Deutsches Haus, 33 Lê Duẩn, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Mercari là kỳ lân công nghệ của Nhật Bản, vận hành ứng dụng mua bán đồ cũ trực tuyến C2C lớn nhất Nhật Bản với đội ngũ kỹ sư chất lượng cao tại Việt Nam."
    },
    {
        "name": "Money Forward Vietnam",
        "website": "https://moneyforward.vn",
        "email": "recruitment@moneyforward.vn",
        "industry": "Personal Finance & ERP SaaS",
        "address": "Tòa nhà eTown Central, 11 Đoàn Văn Bơ, Quận 4, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Money Forward phát triển phần mềm quản lý tài chính cá nhân và các hệ thống hoạch định tài nguyên doanh nghiệp (SaaS ERP) hàng đầu Nhật Bản."
    },
    {
        "name": "Sansan Vietnam",
        "website": "https://www.sansan.com",
        "email": "hr-vn@sansan.com",
        "industry": "B2B SaaS & Contact Management",
        "address": "Tòa nhà Lim Tower 3, 29A Nguyễn Đình Chiểu, Quận 1, TP. Hồ Chí Minh",
        "size": "SME",
        "description": "Sansan cung cấp giải pháp B2B SaaS quản trị danh thiếp số và dữ liệu danh bạ khách hàng thông minh cho các tập đoàn toàn cầu."
    },
    {
        "name": "Henny Penny Vietnam",
        "website": "https://www.hennypenny.com",
        "email": "recruitment-vn@hennypenny.com",
        "industry": "Industrial Software & Embedded Systems",
        "address": "Tòa nhà Peakview Plaza, 36 Hoàng Cầu, Đống Đa, Hà Nội",
        "size": "SME",
        "description": "Henny Penny phát triển các phần mềm điều khiển nhúng thông minh và IoT cho các thiết bị công nghiệp quy mô lớn toàn cầu."
    },
    {
        "name": "Niteco",
        "website": "https://niteco.com",
        "email": "hr@niteco.com",
        "industry": "CMS, E-commerce Solutions & Web Dev",
        "address": "Tòa nhà Toyota Mỹ Đình, 15 Phạm Hùng, Mỹ Đình 2, Nam Từ Liêm, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Niteco là công ty công nghệ đa quốc gia chuyên cung cấp các giải pháp thương mại điện tử trên nền Optimizely (Episerver), Sitecore và Umbraco."
    },
    {
        "name": "Teko Vietnam",
        "website": "https://teko.vn",
        "email": "hr@teko.vn",
        "industry": "Retail Technology & Omni-channel solutions",
        "address": "Tầng 5, Tòa nhà Center Building, 85 Vũ Trọng Phụng, Thanh Xuân, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Teko Vietnam (thành viên của VNLife) phát triển các hệ thống ERP bán lẻ, kho bãi thông minh và giải pháp Omni-channel phục vụ chuỗi Phong Vũ."
    },
    {
        "name": "Ahamove",
        "website": "https://www.ahamove.com",
        "email": "hr@ahamove.com",
        "industry": "Logistics Technology & On-demand Delivery",
        "address": "Tầng 9, Tòa nhà Mipec Tower, 229 Tây Sơn, Ngã Tư Sở, Đống Đa, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Ahamove là nền tảng công nghệ vận tải theo nhu cầu hàng đầu Việt Nam, tối ưu hóa thuật toán ghép đơn hàng thời gian thực cho tài xế và cửa hàng."
    },
    {
        "name": "Gojek Vietnam",
        "website": "https://www.gojek.com/vi-vn",
        "email": "careers.vn@gojek.com",
        "industry": "Super App & Ride-Hailing Technology",
        "address": "Tòa nhà Friendship Tower, 156 Lê Duẩn, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Gojek vận hành ứng dụng siêu đa dịch vụ (gọi xe, giao thức ăn, ví điện tử) kết nối hàng triệu khách hàng và đối tác tài xế trên toàn Đông Nam Á."
    },
    {
        "name": "Be Group",
        "website": "https://be.com.vn",
        "email": "careers@begroup.com.vn",
        "industry": "Ride-Hailing & Mobility Platform",
        "address": "Tòa nhà Pearl Plaza, 561A Điện Biên Phủ, Bình Thạnh, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Be Group là công ty công nghệ Việt Nam sở hữu siêu ứng dụng gọi xe 'be', cung cấp giải pháp vận chuyển tích hợp thanh toán ngân hàng số."
    },
    {
        "name": "Traveloka Vietnam",
        "website": "https://www.traveloka.com/vi-vn",
        "email": "careers.vn@traveloka.com",
        "industry": "Travel Tech & Online Booking Platform",
        "address": "Tòa nhà An Phú, 117-119 Lý Chính Thắng, Quận 3, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Traveloka là nền tảng du lịch trực tuyến hàng đầu Đông Nam Á, cung cấp giải pháp đặt vé máy bay, phòng khách sạn và vé vui chơi giải trí trực tuyến."
    },
    {
        "name": "Vntrip",
        "website": "https://www.vntrip.vn",
        "email": "hr@vntrip.vn",
        "industry": "Travel Tech & Hotel Booking System",
        "address": "Tầng 5, Tòa nhà 29T1 Hoàng Đạo Thúy, Cầu Giấy, Hà Nội",
        "size": "SME",
        "description": "Vntrip cung cấp nền tảng so sánh giá vé máy bay và đặt phòng khách sạn trực tuyến tiên tiến phục vụ thị trường khách du lịch tự túc Việt Nam."
    },
    {
        "name": "iVIVU.com",
        "website": "https://www.ivivu.com",
        "email": "jobs@ivivu.com",
        "industry": "Online Travel Platform & Holiday Booking",
        "address": "Tòa nhà Pax Sky, 159C Đề Thám, Cô Giang, Quận 1, TP. Hồ Chí Minh",
        "size": "SME",
        "description": "iVIVU.com là thành viên của TMG Group, chuyên cung cấp các gói tour nghỉ dưỡng cao cấp trực tuyến và hệ thống đặt vé máy bay thông minh."
    },
    {
        "name": "Cốc Cốc",
        "website": "https://coccoc.com",
        "email": "recruitment@coccoc.com",
        "industry": "Web Browser & Adtech Search Engine",
        "address": "Tầng 8, Tòa nhà Peakview Plaza, 36 Hoàng Cầu, Đống Đa, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Cốc Cốc phát triển trình duyệt web và công cụ tìm kiếm nội địa lớn nhất Việt Nam, tích hợp giải pháp quảng cáo Adtech thông minh hàng đầu."
    },
    {
        "name": "Zalo Group",
        "website": "https://zalo.me",
        "email": "hr@zalo.me",
        "industry": "Instant Messaging & Social Platform",
        "address": "VNG Campus, Đường số 13, Tân Thuận Đông, Quận 7, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Zalo phát triển ứng dụng liên lạc tức thời và mạng xã hội lớn nhất Việt Nam, kết nối hơn 70 triệu người dùng và hỗ trợ dịch vụ công trực tuyến."
    },
    {
        "name": "VTC Intecom",
        "website": "https://vtcintecom.vn",
        "email": "tuyendung.intecom@vtc.vn",
        "industry": "E-payment & Game Publishing",
        "address": "Tòa nhà VTC, 23 Lạc Trung, Hai Bà Trưng, Hà Nội",
        "size": "ENTERPRISE",
        "description": "VTC Intecom là đơn vị thành viên của VTC, chuyên vận hành cổng thanh toán điện tử VTC Pay và phát hành các sản phẩm game trực tuyến quy mô lớn."
    },
    {
        "name": "VTC Online",
        "website": "https://vtconline.vn",
        "email": "hr@vtc.vn",
        "industry": "Edtech & Online Game Publishing",
        "address": "Tòa nhà VTC Online, 18 Tam Trinh, Hai Bà Trưng, Hà Nội",
        "size": "ENTERPRISE",
        "description": "VTC Online phát triển ứng dụng thi tiếng Anh trực tuyến IOE quốc gia và là một trong những nhà phát hành game trực tuyến kỳ cựu nhất Việt Nam."
    },
    {
        "name": "SohaGame",
        "website": "https://sohagame.vn",
        "email": "hr@sohagame.vn",
        "industry": "Mobile Game Publishing & Platform",
        "address": "Tòa nhà Center Building, 85 Vũ Trọng Phụng, Thanh Xuân, Hà Nội",
        "size": "ENTERPRISE",
        "description": "SohaGame (một thành viên của VCCorp) là nhà phát hành game di động hàng đầu Việt Nam sở hữu cổng kết nối cộng đồng game thủ cực lớn."
    },
    {
        "name": "Gameloft Vietnam",
        "website": "https://www.gameloft.com",
        "email": "recruitment.glv@gameloft.com",
        "industry": "Mobile Game Development",
        "address": "Tòa nhà Pax Sky, 159C Đề Thám, Cô Giang, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Gameloft Vietnam là studio phát triển trò chơi di động chất lượng cao lớn nhất của tập đoàn Gameloft toàn cầu đóng tại Sài Gòn và Đà Nẵng."
    },
    {
        "name": "Koei Tecmo Vietnam",
        "website": "https://www.koeitecmo.co.jp",
        "email": "recruitment.ktv@koeitecmo.com.vn",
        "industry": "3D Console Game Development",
        "address": "Tòa nhà Geleximco, 36 Hoàng Cầu, Đống Đa, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Koei Tecmo Vietnam phát triển các dự án game đồ họa 3D chất lượng cao (như series Tam Quốc Diễn Nghĩa) cho dòng máy console lớn thế giới."
    },
    {
        "name": "Glass Egg Digital Media",
        "website": "https://www.glassegg.com",
        "email": "jobs@glassegg.com",
        "industry": "3D Art Production & Game Art Outsourcing",
        "address": "Tòa nhà REE Tower, 9 Đoàn Văn Bơ, Quận 4, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Glass Egg (một thành viên của Virtuos) là nhà sản xuất nghệ thuật game 3D hàng đầu chuyên về các thiết kế phương tiện di chuyển 3D siêu thực cho game bom tấn."
    },
    {
        "name": "Sparx* - a Virtuos Studio",
        "website": "https://www.sparx.com",
        "email": "jobs@sparx.com",
        "industry": "VFX & 3D Game Art Production",
        "address": "Tòa nhà Hải Âu, 39B Trường Sơn, Tân Bình, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Sparx* là studio nghệ thuật 3D và VFX hàng đầu Đông Nam Á, tham gia sản xuất hiệu ứng hình ảnh cho các bom tấn Hollywood và game toàn cầu."
    },
    {
        "name": "Ubisoft Da Nang",
        "website": "https://danang.ubisoft.com",
        "email": "recruitment.danang@ubisoft.com",
        "industry": "Casual Mobile Game Development",
        "address": "Tầng 5, Tòa nhà Indochina Riverside, 74 Bạch Đằng, Hải Châu, Đà Nẵng",
        "size": "SME",
        "description": "Ubisoft Da Nang phát triển các trò chơi di động HTML5 nhẹ và hấp dẫn (casual games) kết nối trực tiếp vào kho ứng dụng toàn cầu của Ubisoft."
    },
    {
        "name": "NCS Vietnam",
        "website": "https://www.ncs.com.sg",
        "email": "recruitment@ncs.com.sg",
        "industry": "Enterprise Digital Solutions & Tech Services",
        "address": "Tòa nhà Indochina Plaza, 241 Xuân Thủy, Cầu Giấy, Hà Nội",
        "size": "ENTERPRISE",
        "description": "NCS Vietnam (thuộc Singtel Group) cung cấp các giải pháp phần mềm doanh nghiệp, đám mây và dịch vụ an ninh mạng chất lượng cao cho thị trường Châu Á."
    },
    {
        "name": "DXC Technology Vietnam",
        "website": "https://dxc.com",
        "email": "careers.vn@dxc.com",
        "industry": "IT Infrastructure & Software Engineering",
        "address": "Tòa nhà Etown 5, 364 Cộng Hòa, Tân Bình, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "DXC Technology cung cấp giải pháp chuyển đổi hạ tầng số, gia công phần mềm quy mô lớn và tư vấn giải pháp CNTT doanh nghiệp cho khách hàng toàn cầu."
    },
    {
        "name": "Luxoft Vietnam",
        "website": "https://www.luxoft.com",
        "email": "recruitment.vn@luxoft.com",
        "industry": "Automotive Software & Financial Tech",
        "address": "Tòa nhà REE Tower, 9 Đoàn Văn Bơ, Quận 4, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Luxoft (một thành viên của DXC) chuyên phát triển phần mềm ô tô tự lái (Automotive Software) và công cụ tài chính chất lượng cao cho thị trường Mỹ, EU."
    },
    {
        "name": "EPAM Systems Vietnam",
        "website": "https://www.epam.com",
        "email": "careers-vn@epam.com",
        "industry": "Digital Product Engineering & Outsourcing",
        "address": "Tòa nhà Lim Tower 3, 29A Nguyễn Đình Chiểu, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "EPAM Systems cung cấp dịch vụ thiết kế sản phẩm số, kỹ thuật phần mềm phức hợp và giải pháp chuyển đổi công nghệ số doanh nghiệp hàng đầu thế giới."
    },
    {
        "name": "Capgemini Vietnam",
        "website": "https://www.capgemini.com",
        "email": "recruitment.vn@capgemini.com",
        "industry": "Business Consulting & Digital Transformation",
        "address": "Tòa nhà Friendship Tower, 156 Lê Duẩn, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Capgemini cung cấp dịch vụ tư vấn chiến lược kinh doanh số, tích hợp hệ thống điện toán đám mây và kỹ thuật phần mềm tối tân cho các tập đoàn đa quốc gia."
    },
    {
        "name": "Cognizant Vietnam",
        "website": "https://www.cognizant.com",
        "email": "careers.vn@cognizant.com",
        "industry": "Enterprise SaaS Consulting & IT Services",
        "address": "Tòa nhà Deutsches Haus, 33 Lê Duẩn, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Cognizant chuyên tư vấn chuyển đổi hệ thống ERP doanh nghiệp, gia công phần mềm đám mây và tích hợp quy trình nghiệp vụ số cho khách hàng đa quốc gia."
    },
    {
        "name": "Infosys Vietnam",
        "website": "https://www.infosys.com",
        "email": "careers.vn@infosys.com",
        "industry": "Business Consulting & IT Outsourcing",
        "address": "Tòa nhà Keangnam Landmark 72, Phạm Hùng, Cầu Giấy, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Infosys cung cấp dịch vụ gia công phần mềm doanh nghiệp chất lượng cao, tư vấn ứng dụng AI và chuyển đổi số cho thị trường Châu Á và Châu Âu."
    },
    {
        "name": "Wipro Vietnam",
        "website": "https://www.wipro.com",
        "email": "careers.vn@wipro.com",
        "industry": "Digital Transformation & Business Consulting",
        "address": "Tòa nhà Saigon Trade Center, 37 Tôn Đức Thắng, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Wipro cung cấp các giải pháp phần mềm đám mây, tích hợp hệ thống an ninh mạng và tư vấn nghiệp vụ tối ưu hóa chi phí IT cho doanh nghiệp."
    },
    {
        "name": "HCLTech Vietnam",
        "website": "https://www.hcltech.com",
        "email": "recruitment.vn@hcl.com",
        "industry": "Software Engineering & R&D Services",
        "address": "Tòa nhà Peakview Plaza, 36 Hoàng Cầu, Đống Đa, Hà Nội",
        "size": "ENTERPRISE",
        "description": "HCLTech cung cấp dịch vụ gia công kỹ thuật phần mềm, nghiên cứu R&D thiết bị viễn thông và giải pháp điện toán đám mây cho thị trường toàn cầu."
    },
    {
        "name": "Tata Consultancy Services Vietnam",
        "website": "https://www.tcs.com",
        "email": "careers.vn@tcs.com",
        "industry": "IT Services & Business Solutions",
        "address": "Tòa nhà Bitexco Financial Tower, 2 Hải Triều, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "TCS cung cấp dịch vụ tư vấn công nghệ lõi ngân hàng, phát triển phần mềm doanh nghiệp lớn và dịch vụ bảo mật thông tin đám mây."
    },
    {
        "name": "Ericsson Vietnam",
        "website": "https://www.ericsson.com",
        "email": "recruitment@ericsson.com",
        "industry": "Telecommunications Network & 5G Infrastructure",
        "address": "Tòa nhà Keangnam Landmark 72, Phạm Hùng, Cầu Giấy, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Ericsson là tập đoàn viễn thông lớn thế giới thiết lập hạ tầng mạng di động 4G/5G và cung cấp dịch vụ truyền dữ liệu không dây chất lượng cao tại Việt Nam."
    },
    {
        "name": "Nokia Vietnam",
        "website": "https://www.nokia.com",
        "email": "recruitment.vn@nokia.com",
        "industry": "Telecom Hardware & Cloud Network",
        "address": "Tòa nhà Sentinel Place, 41A Lý Thái Tổ, Hoàn Kiếm, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Nokia thiết kế và phân phối thiết bị truyền dẫn vô tuyến viễn thông, hạ tầng cáp quang băng rộng và dịch vụ phần mềm đám mây cho nhà mạng di động."
    },
    {
        "name": "Huawei Vietnam",
        "website": "https://www.huawei.com/vn",
        "email": "recruitment.vn@huawei.com",
        "industry": "Information Devices & Telecom Networks",
        "address": "Tòa nhà Keangnam Landmark 72, Phạm Hùng, Cầu Giấy, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Huawei cung cấp thiết bị viễn thông phần cứng cao cấp, các giải pháp năng lượng số thông minh và dịch vụ điện toán đám mây (Huawei Cloud) tại Việt Nam."
    },
    {
        "name": "Cisco Vietnam",
        "website": "https://www.cisco.com/c/vi_vn",
        "email": "careers.vn@cisco.com",
        "industry": "Networking Hardware & Security Software",
        "address": "Tòa nhà Deutsches Haus, 33 Lê Duẩn, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Cisco là hãng sản xuất thiết bị mạng viễn thông hàng đầu thế giới, cung cấp bộ chuyển mạch, router, giải pháp mạng không dây và phần mềm bảo mật."
    },
    {
        "name": "Fortinet Vietnam",
        "website": "https://www.fortinet.com",
        "email": "careers.vn@fortinet.com",
        "industry": "Cybersecurity & Firewall Hardware",
        "address": "Tòa nhà CornerStone, 16 Phan Chu Trinh, Hoàn Kiếm, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Fortinet cung cấp giải pháp bảo mật mạng tích hợp cao cấp bao gồm thiết bị tường lửa (FortiGate), bảo mật điểm cuối và giám sát an ninh thông minh."
    },
    {
        "name": "Palo Alto Networks Vietnam",
        "website": "https://www.paloaltonetworks.com",
        "email": "careers.vn@paloaltonetworks.com",
        "industry": "Cybersecurity & Next-Gen Firewall",
        "address": "Tòa nhà Bitexco Financial Tower, 2 Hải Triều, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Palo Alto Networks cung cấp giải pháp an ninh mạng tối tân dựa trên đám mây, tường lửa thế hệ mới (NGFW) và công cụ phòng chống tấn công mạng nâng cao."
    },
    {
        "name": "Check Point Software Vietnam",
        "website": "https://www.checkpoint.com",
        "email": "recruitment.vn@checkpoint.com",
        "industry": "Cybersecurity & Cloud Protection",
        "address": "Tòa nhà Saigon Tower, 29 Lê Duẩn, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Check Point cung cấp giải pháp bảo mật đám mây tích hợp đa tầng, thiết bị tường lửa hiệu năng cao và các dịch vụ phòng chống mã độc tống tiền."
    },
    {
        "name": "Kaspersky Vietnam",
        "website": "https://www.kaspersky.com.vn",
        "email": "jobs.vn@kaspersky.com",
        "industry": "Antivirus & Endpoint Security",
        "address": "Tòa nhà Pax Sky, 186 Nguyễn Thị Minh Khai, Quận 3, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Kaspersky cung cấp phần mềm diệt virus gia đình và giải pháp bảo mật điểm cuối doanh nghiệp (Endpoint Security), phân tích mã độc chuyên nghiệp."
    },
    {
        "name": "VNG Games",
        "website": "https://vnggames.com",
        "email": "hr.games@vng.com.vn",
        "industry": "Online Gaming & Digital Entertainment",
        "address": "VNG Campus, Đường số 13, Tân Thuận Đông, Quận 7, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "VNG Games là nhà phát hành và phát triển game hàng đầu Việt Nam, phân phối các sản phẩm game chất lượng cao cho thị trường Đông Nam Á."
    },
    {
        "name": "VNCS (Vietnam Cyber Security)",
        "website": "https://vncs.vn",
        "email": "hr@vncs.vn",
        "industry": "Cybersecurity & Security Operations Center",
        "address": "Tầng 5, Tòa nhà Khách sạn Thể thao Hacinco, Thanh Xuân, Hà Nội",
        "size": "SME",
        "description": "VNCS là nhà phân phối và cung cấp giải pháp an ninh mạng hàng đầu Việt Nam, vận hành trung tâm giám sát an toàn thông tin (SOC) chuyên nghiệp."
    },
    {
        "name": "Viettel Cyber Security",
        "website": "https://viettelcybersecurity.com",
        "email": "recruitment.vcs@viettel.com.vn",
        "industry": "Cybersecurity & Threat Detection",
        "address": "Tòa nhà Viettel, Ngõ 11 Duy Tân, Cầu Giấy, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Viettel Cyber Security chuyên cung cấp dịch vụ đánh giá an toàn thông tin doanh nghiệp, giám sát tấn công mạng trực tiếp 24/7 và ứng cứu sự cố bảo mật."
    },
    {
        "name": "CMC Cyber Security",
        "website": "https://cmccybersecurity.com",
        "email": "tuyendung.cs@cmc.com.vn",
        "industry": "Cybersecurity & Malware Analysis",
        "address": "Tòa nhà CMC, Duy Tân, Cầu Giấy, Hà Nội",
        "size": "SME",
        "description": "CMC Cyber Security cung cấp giải pháp diệt mã độc CMC Antivirus quốc gia, dịch vụ đánh giá lỗ hổng bảo mật (Pentest) và giám sát SOC."
    },
    {
        "name": "VSEC",
        "website": "https://vsec.com.vn",
        "email": "hr@vsec.com.vn",
        "industry": "Cybersecurity consulting & Security Assessment",
        "address": "Tòa nhà Charmvit Tower, 117 Trần Duy Hưng, Cầu Giấy, Hà Nội",
        "size": "SME",
        "description": "VSEC là tổ chức đánh giá an toàn thông tin độc lập đầu tiên tại Việt Nam, chuyên về dịch vụ Pentesting, xử lý mã độc và tư vấn tuân thủ bảo mật."
    },
    {
        "name": "SecurityBox",
        "website": "https://securitybox.vn",
        "email": "hr@securitybox.vn",
        "industry": "Network Vulnerability Management",
        "address": "Tầng 9, Tòa nhà Sunrise, 90 Trần Thái Tông, Cầu Giấy, Hà Nội",
        "size": "STARTUP",
        "description": "SecurityBox phát triển thiết bị tự động quét và cảnh báo sớm lỗ hổng bảo mật hạ tầng mạng và website cho các cơ quan và doanh nghiệp lớn."
    },
    {
        "name": "ChongLuaDao",
        "website": "https://chongluadao.vn",
        "email": "contact@chongluadao.vn",
        "industry": "Non-profit Cybersecurity & Phishing Protection",
        "address": "Tòa nhà Bitexco Financial Tower, 2 Hải Triều, Quận 1, TP. Hồ Chí Minh",
        "size": "STARTUP",
        "description": "ChongLuaDao phát triển tiện ích mở rộng giúp cảnh báo sớm trang web lừa đảo, giả mạo trực tuyến nhằm bảo vệ người dùng internet Việt Nam."
    },
    {
        "name": "VinAI Research",
        "website": "https://www.vinai.io",
        "email": "hr.vinai@vinai.io",
        "industry": "Artificial Intelligence Research",
        "address": "Vinhomes Times City, 458 Minh Khai, Hai Bà Trưng, Hà Nội",
        "size": "ENTERPRISE",
        "description": "VinAI là viện nghiên cứu trí tuệ nhân tạo hàng đầu Việt Nam, tập trung vào công nghệ ô tô tự lái và xử lý hình ảnh thị giác máy tính."
    },
    {
        "name": "VinBrain",
        "website": "https://vinbrain.net",
        "email": "hr@vinbrain.net",
        "industry": "AI in Healthcare & Medical Imaging",
        "address": "Tòa nhà Vinhomes Symphony, Long Biên, Hà Nội",
        "size": "SME",
        "description": "VinBrain phát triển các giải pháp trợ lý bác sĩ thông minh dựa trên AI (DrAid) giúp phân tích hình ảnh X-quang phổi và chuẩn đoán bệnh sớm."
    },
    {
        "name": "VinBigData",
        "website": "https://vinbigdata.org",
        "email": "tuyendung@vinbigdata.org",
        "industry": "Big Data Analytics & Conversational AI",
        "address": "Tòa nhà Vinhomes Symphony, Long Biên, Hà Nội",
        "size": "ENTERPRISE",
        "description": "VinBigData phát triển trợ lý ảo giọng nói tiếng Việt ViVi tích hợp trên ô tô điện VinFast và các công cụ xử lý dữ liệu lớn, gen học."
    },
    {
        "name": "FPT Smart Cloud",
        "website": "https://fptcloud.com",
        "email": "recruitment.fci@fpt.com.vn",
        "industry": "Cloud Computing & Conversational AI",
        "address": "Tầng 7, Tòa nhà FPT Cầu Giấy, 17 Duy Tân, Cầu Giấy, Hà Nội",
        "size": "ENTERPRISE",
        "description": "FPT Smart Cloud cung cấp hạ tầng điện toán đám mây FPT Cloud chuẩn doanh nghiệp và phát triển nền tảng hội thoại thông minh FPT.AI chatbot."
    },
    {
        "name": "Viettel AI Center",
        "website": "https://viettel.ai",
        "email": "careers.ai@viettel.com.vn",
        "industry": "Artificial Intelligence & Big Data Solutions",
        "address": "Tòa nhà Viettel, Ngõ 11 Duy Tân, Cầu Giấy, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Trung tâm Không gian mạng Viettel (Viettel AI) phát triển hệ thống trợ lý ảo giọng nói tiếng Việt, nhận diện khuôn mặt và phân tích dữ liệu lớn."
    },
    {
        "name": "VNPT AI Center",
        "website": "https://vnpt.ai",
        "email": "careers.ai@vnpt.vn",
        "industry": "AI Research & Digital Identity",
        "address": "Tòa nhà VNPT, 57 Huỳnh Thúc Kháng, Đống Đa, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Trung tâm Trí tuệ nhân tạo VNPT phát triển giải pháp nhận diện khuôn mặt VNPT FaceID và công nghệ nhận dạng ký tự quang học (OCR) thông minh."
    },
    {
        "name": "Cinnamon AI",
        "website": "https://cinnamon.is",
        "email": "careers.vn@cinnamon.is",
        "industry": "AI Consulting & Cognitive Document Processing",
        "address": "Tòa nhà Pax Sky, 159C Đề Thám, Cô Giang, Quận 1, TP. Hồ Chí Minh",
        "size": "SME",
        "description": "Cinnamon AI phát triển các giải pháp trích xuất dữ liệu tài liệu tự động (OCR) dựa trên AI giúp số hóa hồ sơ cho các ngân hàng Nhật Bản."
    },
    {
        "name": "MindX Technology School",
        "website": "https://mindx.edu.vn",
        "email": "hr@mindx.edu.vn",
        "industry": "Edtech & Programming School",
        "address": "Tòa nhà Peakview Plaza, 36 Hoàng Cầu, Đống Đa, Hà Nội",
        "size": "ENTERPRISE",
        "description": "MindX là hệ sinh thái đào tạo lập trình cho mọi lứa tuổi tại Việt Nam, kết nối học viên trực tiếp với các nhà tuyển dụng và quỹ đầu tư công nghệ."
    },
    {
        "name": "Teky Academy",
        "website": "https://teky.edu.vn",
        "email": "hr@teky.edu.vn",
        "industry": "Edtech & STEAM Education",
        "address": "Tòa nhà Sunrise, 90 Trần Thái Tông, Cầu Giấy, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Học viện Sáng tạo Công nghệ TEKY cung cấp chương trình đào tạo STEAM, khoa học máy tính và lắp ráp robot cho trẻ em từ 4 đến 18 tuổi."
    },
    {
        "name": "CoderSchool",
        "website": "https://www.coderschool.vn",
        "email": "careers@coderschool.vn",
        "industry": "Edtech & Coding Bootcamp",
        "address": "Tòa nhà Pax Sky, 186 Nguyễn Thị Minh Khai, Quận 3, TP. Hồ Chí Minh",
        "size": "STARTUP",
        "description": "CoderSchool cung cấp các chương trình đào tạo lập trình ngắn hạn (Bootcamps) về Web Dev, Mobile Dev và Data Science cam kết việc làm đầu ra."
    },
    {
        "name": "Funix",
        "website": "https://funix.edu.vn",
        "email": "hr@funix.edu.vn",
        "industry": "Edtech & Online IT Mentoring",
        "address": "Tòa nhà FPT Cầu Giấy, 17 Duy Tân, Cầu Giấy, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Funix (thuộc tập đoàn FPT) cung cấp mô hình học lập trình trực tuyến tự học có sự hỗ trợ trực tiếp từ đội ngũ mentor là chuyên gia IT đầu ngành."
    },
    {
        "name": "Topica Edtech Group",
        "website": "https://topica.edu.vn",
        "email": "tuyendung@topica.edu.vn",
        "industry": "Edtech & E-learning Platform",
        "address": "Tòa nhà Geleximco, 36 Hoàng Cầu, Đống Đa, Hà Nội",
        "size": "ENTERPRISE",
        "description": "Topica Edtech Group là đơn vị đi đầu về đào tạo trực tuyến tại Đông Nam Á, cung cấp chương trình luyện thi tiếng Anh trực tuyến Elsa Speak, Native."
    },
    {
        "name": "Jio Health Vietnam",
        "website": "https://jiohealth.com",
        "email": "recruitment@jiohealth.com",
        "industry": "Healthtech & Digital Healthcare Platform",
        "address": "Tòa nhà M-Plaza, 39 Lê Duẩn, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
        "size": "SME",
        "description": "Jio Health kết hợp ứng dụng đặt lịch khám bệnh trực tuyến, tư vấn từ xa qua video (telemedicine) và chuỗi phòng khám đa khoa hiện đại."
    },
    {
        "name": "eDoctor",
        "website": "https://edoctor.io",
        "email": "hr@edoctor.vn",
        "industry": "Healthtech & Medical Consult Platform",
        "address": "Tòa nhà Pax Sky, 186 Nguyễn Thị Minh Khai, Quận 3, TP. Hồ Chí Minh",
        "size": "STARTUP",
        "description": "eDoctor cung cấp dịch vụ đặt lịch xét nghiệm tại nhà trực tuyến, chat trực tiếp với bác sĩ chuyên khoa và tra cứu thông tin y tế nhanh chóng."
    },
    {
        "name": "Buymed (Thuocsi.vn)",
        "website": "https://thuocsi.vn",
        "email": "recruitment@buymed.cpl",
        "industry": "Healthtech & Pharmaceutical Marketplace",
        "address": "Tòa nhà REE Tower, 9 Đoàn Văn Bơ, Quận 4, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Buymed vận hành cổng thương mại điện tử Thuocsi.vn kết nối nhà phân phối dược phẩm chính hãng trực tiếp với hơn 20.000 nhà thuốc tây cả nước."
    },
    {
        "name": "Med247",
        "website": "https://med247.vn",
        "email": "hr@med247.co",
        "industry": "Healthtech & Clinic Chain",
        "address": "Tòa nhà Peakview Plaza, 36 Hoàng Cầu, Đống Đa, Hà Nội",
        "size": "STARTUP",
        "description": "Med247 vận hành chuỗi phòng khám thông minh 24/7 tích hợp ứng dụng y tế từ xa để theo dõi chăm sóc bệnh nhân liên tục tiện lợi."
    },
    {
        "name": "Navigos Group (VietnamWorks)",
        "website": "https://www.navigosgroup.com",
        "email": "recruitment@navigosgroup.com",
        "industry": "Recruitment & HR Tech Platform",
        "address": "Tòa nhà eTown Central, 11 Đoàn Văn Bơ, Quận 4, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Navigos Group sở hữu VietnamWorks - cổng thông tin tuyển dụng lớn nhất Việt Nam và Navigos Search - đơn vị cung cấp dịch vụ tuyển dụng nhân sự cấp cao."
    },
    {
        "name": "J&T Express Vietnam",
        "website": "https://jtexpress.vn",
        "email": "hr@jtexpress.vn",
        "industry": "Logistics & Delivery Tech",
        "address": "Tòa nhà Flemington, 182 Lê Đại Hành, Quận 11, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "J&T Express là thương hiệu chuyển phát nhanh công nghệ hàng đầu, tối ưu hóa quy trình giao nhận bằng hệ thống phân loại tự động."
    },
    {
        "name": "Ninja Van Vietnam",
        "website": "https://www.ninjavan.co/vi-vn",
        "email": "careers@ninjavan.co",
        "industry": "Logistics Tech & Delivery Network",
        "address": "Tòa nhà Pax Sky, 186 Nguyễn Thị Minh Khai, Quận 3, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Ninja Van là đơn vị cung cấp dịch vụ giao nhận công nghệ lớn nhất khu vực Đông Nam Á, tối ưu hóa chặng cuối bằng thuật toán thông minh."
    },
    {
        "name": "Qualcomm Vietnam",
        "website": "https://www.qualcomm.com",
        "email": "jobs.vn@qualcomm.com",
        "industry": "Semiconductors & Wireless Tech",
        "address": "Tòa nhà Deutsches Haus, 33 Lê Duẩn, Quận 1, TP. Hồ Chí Minh",
        "size": "ENTERPRISE",
        "description": "Qualcomm là tập đoàn công nghệ bán dẫn và thiết bị viễn thông không dây hàng đầu thế giới, phát triển chipset di động Snapdragon."
    }
]

def main():
    print("=== ĐANG BẮT ĐẦU CẬP NHẬT 100 CÔNG TY GIẢ THÀNH CÔNG TY THẬT ===")
    
    # Connect to databases
    try:
        conn_comp = psycopg2.connect(host=DB_CONFIG["host"], port=DB_CONFIG["port"], dbname="CompanyService", user=DB_CONFIG["user"], password=DB_CONFIG["password"])
        conn_auth = psycopg2.connect(host=DB_CONFIG["host"], port=DB_CONFIG["port"], dbname="AuthService", user=DB_CONFIG["user"], password=DB_CONFIG["password"])
        conn_profile = psycopg2.connect(host=DB_CONFIG["host"], port=DB_CONFIG["port"], dbname="ProfileService", user=DB_CONFIG["user"], password=DB_CONFIG["password"])
        conn_job = psycopg2.connect(host=DB_CONFIG["host"], port=DB_CONFIG["port"], dbname="JobService", user=DB_CONFIG["user"], password=DB_CONFIG["password"])
        
        cur_comp = conn_comp.cursor()
        cur_auth = conn_auth.cursor()
        cur_profile = conn_profile.cursor()
        cur_job = conn_job.cursor()
    except Exception as e:
        print(f"❌ Lỗi kết nối CSDL: {e}")
        return

    # Find the 100 synthetic companies we created
    cur_comp.execute('SELECT "Id", "Name" FROM "Companies" WHERE "CreatedBy" = \'CompanySeeder\' ORDER BY "Name"')
    seeded_companies = cur_comp.fetchall()
    
    print(f"Tìm thấy {len(seeded_companies)} công ty giả cần cập nhật.")
    
    # We update up to the length of REAL_COMPANIES (which has exactly 100 entries)
    updated_count = 0
    for idx, (comp_id, old_name) in enumerate(seeded_companies):
        if idx >= len(REAL_COMPANIES):
            break
        real_data = REAL_COMPANIES[idx]
        new_name = real_data["name"]
        new_slug = make_slug(new_name).replace(".", "_")
        new_email = f"hr.{new_slug}@jobhub.vn"
        new_username = f"HR {new_name}"
        
        # Update CompanyService.Companies
        logo = f"https://picsum.photos/id/{10 + idx}/100/100"
        cover = f"https://picsum.photos/id/{10 + idx}/800/400"
        
        cur_comp.execute('''
            UPDATE "Companies"
            SET "Name" = %s, "Website" = %s, "ContactEmail" = %s, "Industry" = %s,
                "Address" = %s, "CompanySize" = %s, "Description" = %s,
                "Logo" = %s, "CoverImage" = %s
            WHERE "Id" = %s
        ''', (
            new_name, real_data["website"], real_data["email"], real_data["industry"],
            real_data["address"], real_data["size"], real_data["description"],
            logo, cover, comp_id
        ))
        
        # Find corresponding HR AppUserId from ProfileService
        cur_profile.execute('SELECT "AppUserId", "Id" FROM "Customers" WHERE "CompanyId" = %s AND "Type" = \'EMPLOYER\'', (comp_id,))
        profile_row = cur_profile.fetchone()
        
        if profile_row:
            app_user_id, cust_profile_id = profile_row
            
            # Update ProfileService.Customers
            cur_profile.execute('''
                UPDATE "Customers"
                SET "FullName" = %s
                WHERE "Id" = %s
            ''', (new_username, cust_profile_id))
            
            # Update AuthService.AppUsers
            cur_auth.execute('''
                UPDATE "AppUsers"
                SET "Email" = %s, "Username" = %s
                WHERE "Id" = %s
            ''', (new_email, new_username, app_user_id))
            
        # Update JobService.Jobs
        cur_job.execute('''
            UPDATE "Jobs"
            SET "CompanyName" = %s, "CompanyLogo" = %s
            WHERE "CompanyId" = %s
        ''', (new_name, logo, comp_id))
        
        updated_count += 1
        if updated_count % 10 == 0:
            print(f"  -> Đã cập nhật xong {updated_count}/100 công ty.")
            
    # Commit all changes!
    conn_comp.commit()
    conn_auth.commit()
    conn_profile.commit()
    conn_job.commit()
    
    print("\n=== HOÀN THÀNH CẬP NHẬT ===")
    print(f"Đã cập nhật thành công {updated_count} công ty từ giả sang THẬT và đồng bộ tất cả HR, Jobs liên quan!")
    
    cur_comp.close()
    cur_auth.close()
    cur_profile.close()
    cur_job.close()
    
    conn_comp.close()
    conn_auth.close()
    conn_profile.close()
    conn_job.close()

if __name__ == "__main__":
    main()
