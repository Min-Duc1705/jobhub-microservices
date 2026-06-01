using Microsoft.EntityFrameworkCore;
using CompanyService.Data;
using CompanyService.Models;
using CompanyService.Models.Enums;
using System.Security.Cryptography;
using System.Text;

namespace CompanyService.Data.SeedData;

/// <summary>
/// Seed ~50 công ty IT chuyên nghiệp tại Việt Nam và quốc tế vào bảng Companies.
/// Idempotent dựa trên check tên công ty.
/// </summary>
public static class CompanySeeder
{
    public static async Task SeedAsync(CompanyDbContext db)
    {
        var rawCompanies = new List<Company>
        {
            // ── VIETNAM ENTERPRISES & TECH HUBS ───────────────────────────────────
            new Company
            {
                Name = "VNG Corporation",
                Description = "VNG là một trong những doanh nghiệp công nghệ hàng đầu Việt Nam, nổi tiếng với các sản phẩm như Zalo, Zing MP3, ZaloPay và các tựa game nổi tiếng toàn cầu.",
                Address = "Z06 Đường số 13, KCX Tân Thuận, Phường Tân Thuận Đông, Quận 7, TP. Hồ Chí Minh",
                Website = "https://vng.com.vn",
                Industry = "Internet & Game Development",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "recruitment@vng.com.vn",
                TaxCode = "0303493036",
                IsVerified = true
            },
            new Company
            {
                Name = "KMS Technology",
                Description = "KMS Technology là công ty hàng đầu về dịch vụ phần mềm, tư vấn công nghệ và phát triển sản phẩm với thị trường chính tại Mỹ và Châu Á Thái Bình Dương.",
                Address = "123 Cộng Hòa, Phường 12, Quận Tân Bình, TP. Hồ Chí Minh",
                Website = "https://www.kms-technology.com",
                Industry = "Software Development",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "careers@kms-technology.com",
                TaxCode = "0308078901",
                IsVerified = true
            },
            new Company
            {
                Name = "MISA Joint Stock Company",
                Description = "MISA là nhà cung cấp hàng đầu các giải pháp chuyển đổi số, phần mềm kế toán, ERP và quản trị doanh nghiệp tại Việt Nam với hơn 25 năm kinh nghiệm.",
                Address = "Tòa nhà MISA, Lô 5, Công viên phần mềm Quang Trung, Quận 12, TP. Hồ Chí Minh",
                Website = "https://www.misa.com.vn",
                Industry = "Enterprise Software",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "hr@misa.com.vn",
                TaxCode = "0101243150",
                IsVerified = true
            },
            new Company
            {
                Name = "TMA Solutions",
                Description = "TMA Solutions là một trong những công ty phần mềm lớn nhất Việt Nam, chuyên cung cấp các giải pháp phần mềm chất lượng cao cho các đối tác toàn cầu tại hơn 30 quốc gia.",
                Address = "111 Nguyễn Đình Chiểu, Phường Võ Thị Sáu, Quận 3, TP. Hồ Chí Minh",
                Website = "https://www.tmasolutions.com",
                Industry = "Software Outsourcing",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "recruit@tma.com.vn",
                TaxCode = "0301438902",
                IsVerified = true
            },
            new Company
            {
                Name = "Rikkeisoft",
                Description = "Rikkeisoft cung cấp dịch vụ phát triển phần mềm chất lượng cao cho đối tác Nhật Bản và toàn cầu. Là một trong những công ty IT có tốc độ tăng trưởng nhanh nhất Việt Nam.",
                Address = "Tòa nhà Sudico, Mễ Trì, Quận Nam Từ Liêm, Hà Nội",
                Website = "https://rikkeisoft.com",
                Industry = "IT Services & Software Outsourcing",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "recruitment@rikkeisoft.com",
                TaxCode = "0105847362",
                IsVerified = true
            },
            new Company
            {
                Name = "NashTech Vietnam",
                Description = "NashTech là một phần của tập đoàn Harvey Nash toàn cầu, chuyên cung cấp các giải pháp công nghệ, phát triển phần mềm và quy trình kinh doanh (BPO) chất lượng cao.",
                Address = "Tòa nhà Etown, 364 Cộng Hòa, Phường 13, Quận Tân Bình, TP. Hồ Chí Minh",
                Website = "https://nashtechglobal.com",
                Industry = "IT Consulting & Outsourcing",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "careers-vn@nashtechglobal.com",
                TaxCode = "0302837461",
                IsVerified = true
            },
            new Company
            {
                Name = "CMC Corporation",
                Description = "Tập đoàn Công nghệ CMC là một trong những tập đoàn công nghệ hàng đầu tại Việt Nam hoạt động trong các lĩnh vực Hạ tầng số, Giải pháp công nghệ và Dịch vụ số toàn cầu.",
                Address = "Tòa nhà CMC, Phố Duy Tân, Quận Cầu Giấy, Hà Nội",
                Website = "https://www.cmc.com.vn",
                Industry = "System Integration & Cloud Service",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "tuyendung@cmc.com.vn",
                TaxCode = "0100244120",
                IsVerified = true
            },
            new Company
            {
                Name = "MoMo (M-Service)",
                Description = "MoMo là siêu ứng dụng thanh toán hàng đầu Việt Nam, cung cấp giải pháp tài chính số toàn diện, thanh toán một chạm cho hàng chục triệu người dùng.",
                Address = "Tòa nhà Phú Mỹ Hưng, 8 Hoàng Văn Thái, Quận 7, TP. Hồ Chí Minh",
                Website = "https://momo.vn",
                Industry = "Fintech & Mobile Payments",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "jobs@mservice.com.vn",
                TaxCode = "0305289153",
                IsVerified = true
            },
            new Company
            {
                Name = "Tiki Corporation",
                Description = "Tiki là một trong những sàn thương mại điện tử uy tín và được yêu thích nhất tại Việt Nam, sở hữu hệ thống logistics Tikinow thông minh và hiện đại.",
                Address = "Tòa nhà Viettel, 285 Cách Mạng Tháng Tám, Quận 10, TP. Hồ Chí Minh",
                Website = "https://tiki.vn",
                Industry = "E-commerce & Logistics Tech",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "talents@tiki.vn",
                TaxCode = "0309532909",
                IsVerified = true
            },
            new Company
            {
                Name = "Shopee Vietnam",
                Description = "Shopee là nền tảng thương mại điện tử hàng đầu tại Đông Nam Á và Đài Loan, cung cấp trải nghiệm mua sắm trực tuyến tích hợp, tiện lợi và an toàn.",
                Address = "Tòa nhà Saigon Centre Tower 2, 67 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
                Website = "https://shopee.vn",
                Industry = "E-commerce & Internet Service",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "careers@shopee.vn",
                TaxCode = "0313597361",
                IsVerified = true
            },
            new Company
            {
                Name = "Grab Vietnam",
                Description = "Grab là siêu ứng dụng hàng đầu tại Đông Nam Á, cung cấp các dịch vụ thiết yếu hàng ngày bao gồm di chuyển, giao nhận thức ăn, hàng hóa và thanh toán số.",
                Address = "Tòa nhà Mapletree Business Centre, 1060 Nguyễn Văn Linh, Quận 7, TP. Hồ Chí Minh",
                Website = "https://www.grab.com/vn",
                Industry = "Ride-hailing & On-demand Services",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "careers.vn@grab.com",
                TaxCode = "0312650437",
                IsVerified = true
            },
            new Company
            {
                Name = "BKAV Corporation",
                Description = "BKAV hoạt động trong các lĩnh vực an ninh mạng, phần mềm diệt virus, nhà thông minh (SmartHome) và thiết bị di động thông minh hàng đầu tại Việt Nam.",
                Address = "Tòa nhà HH1, Khu đô thị Yên Hòa, Cầu Giấy, Hà Nội",
                Website = "https://www.bkav.com.vn",
                Industry = "Cybersecurity & Hardware R&D",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "tuyendung@bkav.com.vn",
                TaxCode = "0101349071",
                IsVerified = true
            },
            new Company
            {
                Name = "Base.vn",
                Description = "Base.vn là nền tảng SaaS đi đầu tại Việt Nam trong lĩnh vực quản trị và vận hành doanh nghiệp toàn diện với các bộ sản phẩm Base Work+, Base Info+ và Base HR+.",
                Address = "Tòa nhà Phú Mỹ Hưng, 8 Hoàng Văn Thái, Quận 7, TP. Hồ Chí Minh",
                Website = "https://base.vn",
                Industry = "SaaS & Enterprise Automation",
                CompanySize = CompanySize.SME,
                ContactEmail = "careers@base.vn",
                TaxCode = "0107538965",
                IsVerified = true
            },
            new Company
            {
                Name = "Axon Active Vietnam",
                Description = "Axon Active là công ty 100% vốn đầu tư Thụy Sĩ, chuyên cung cấp các nhóm kỹ sư phát triển phần mềm theo mô hình Agile chuyên nghiệp cho các khách hàng quốc tế.",
                Address = "Tòa nhà Hải Âu, 39B Trường Sơn, Phường 4, Quận Tân Bình, TP. Hồ Chí Minh",
                Website = "https://www.axonactive.com",
                Industry = "Agile Software Development",
                CompanySize = CompanySize.SME,
                ContactEmail = "career@axonactive.com",
                TaxCode = "0309907153",
                IsVerified = true
            },
            new Company
            {
                Name = "NAB Innovation Centre Vietnam",
                Description = "Trung tâm Đổi mới Sáng tạo của Ngân hàng Quốc gia Úc (NAB), chuyên phát triển các công nghệ ngân hàng hiện đại, điện toán đám mây và dữ liệu lớn.",
                Address = "Tòa nhà Hallmark, KĐT mới Thủ Thiêm, TP. Thủ Đức, TP. Hồ Chí Minh",
                Website = "https://www.nab.com.au",
                Industry = "Fintech & Banking Technology",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "vietnam.recruitment@nab.com.au",
                TaxCode = "0317208945",
                IsVerified = true
            },
            new Company
            {
                Name = "Techcombank (Technology Division)",
                Description = "Bộ phận Công nghệ của Techcombank đi đầu trong việc thúc đẩy chuyển đổi số ngành ngân hàng tại Việt Nam thông qua các nền tảng số hóa vượt trội.",
                Address = "119 Trần Hưng Đạo, Quận Hoàn Kiếm, Hà Nội",
                Website = "https://www.techcombank.com",
                Industry = "Banking & Digital Finance",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "tech.hr@techcombank.com.vn",
                TaxCode = "0100230800",
                IsVerified = true
            },
            new Company
            {
                Name = "VPBank (IT Center)",
                Description = "Trung tâm Công nghệ Thông tin VPBank chịu trách nhiệm phát triển hạ tầng và ứng dụng ngân hàng số tiên phong như VPBank NEO và các ứng dụng nội bộ hiện đại.",
                Address = "89 Láng Hạ, Quận Đống Đa, Hà Nội",
                Website = "https://www.vpbank.com.vn",
                Industry = "Banking Technology",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "tuyendung@vpbank.com.vn",
                TaxCode = "0100233583",
                IsVerified = true
            },
            new Company
            {
                Name = "Vietcombank (IT Center)",
                Description = "Khối Công nghệ Thông tin Vietcombank vận hành hệ thống Core Banking lớn nhất Việt Nam và phát triển các sản phẩm ngân hàng số phục vụ hàng triệu khách hàng cá nhân và doanh nghiệp.",
                Address = "198 Trần Quang Khải, Quận Hoàn Kiếm, Hà Nội",
                Website = "https://www.vietcombank.com.vn",
                Industry = "Banking Technology",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "recruit.it@vietcombank.com.vn",
                TaxCode = "0100112437",
                IsVerified = true
            },
            new Company
            {
                Name = "One Mount Group",
                Description = "One Mount xây dựng hệ sinh thái công nghệ lớn nhất Việt Nam, kết nối người dân và doanh nghiệp qua các ứng dụng VinID, VinShop và OneHousing.",
                Address = "Tòa nhà Times City, 458 Minh Khai, Quận Hai Bà Trưng, Hà Nội",
                Website = "https://onemount.com",
                Industry = "Technology Ecosystem",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "talent@onemount.com",
                TaxCode = "0108927361",
                IsVerified = true
            },
            new Company
            {
                Name = "KiotViet",
                Description = "KiotViet là phần mềm quản lý bán hàng phổ biến nhất tại Việt Nam hiện nay, hỗ trợ đắc lực cho hơn 200.000 cửa hàng kinh doanh vừa và nhỏ.",
                Address = "Tòa nhà Mipec, 229 Tây Sơn, Quận Đống Đa, Hà Nội",
                Website = "https://www.kiotviet.vn",
                Industry = "SaaS & Retail Tech",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "hr@kiotviet.com",
                TaxCode = "0106325983",
                IsVerified = true
            },
            new Company
            {
                Name = "Haravan",
                Description = "Haravan cung cấp các giải pháp xây dựng website thương mại điện tử, quản lý bán hàng đa kênh (Omnichannel) và các công cụ marketing tối ưu.",
                Address = "Tòa nhà Flemington, 182 Lê Đại Hành, Quận 11, TP. Hồ Chí Minh",
                Website = "https://www.haravan.com",
                Industry = "E-commerce Platform & SaaS",
                CompanySize = CompanySize.SME,
                ContactEmail = "recruitment@haravan.com",
                TaxCode = "0312739850",
                IsVerified = true
            },
            new Company
            {
                Name = "Sapo Technology",
                Description = "Sapo là nền tảng quản lý và bán hàng đa kênh hàng đầu Việt Nam, giúp các doanh nghiệp bán lẻ và thương mại điện tử vận hành kinh doanh hiệu quả.",
                Address = "Tòa nhà Ladeco, 266 Đội Cấn, Quận Ba Đình, Hà Nội",
                Website = "https://www.sapo.vn",
                Industry = "SaaS & E-commerce Platform",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "hr@sapo.vn",
                TaxCode = "0104629375",
                IsVerified = true
            },
            new Company
            {
                Name = "Amanotes",
                Description = "Amanotes là nhà phát hành trò chơi âm nhạc di động hàng đầu thế giới với hơn 2 tỷ lượt tải xuống toàn cầu cho các tựa game Magic Tiles, Tiles Hop.",
                Address = "Tòa nhà IPC, 1489 Nguyễn Văn Linh, Quận 7, TP. Hồ Chí Minh",
                Website = "https://amanotes.com",
                Industry = "Mobile Game & Music Tech",
                CompanySize = CompanySize.SME,
                ContactEmail = "careers@amanotes.com",
                TaxCode = "0313158941",
                IsVerified = true
            },
            new Company
            {
                Name = "Sky Mavis",
                Description = "Sky Mavis là studio tạo ra Axie Infinity - trò chơi NFT nổi tiếng nhất thế giới và là nhà phát triển chuỗi khối Ronin chuyên biệt cho gaming.",
                Address = "Tòa nhà Saigon Centre, 65 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
                Website = "https://skymavis.com",
                Industry = "Blockchain & Game Studio",
                CompanySize = CompanySize.SME,
                ContactEmail = "career@skymavis.com",
                TaxCode = "0315482390",
                IsVerified = true
            },
            new Company
            {
                Name = "Coin98 Finance",
                Description = "Coin98 là một cổng giao thức tiền mã hóa phi tập trung, phát triển các sản phẩm DeFi hàng đầu như Coin98 Wallet, Coin98 Exchange và các hạ tầng Web3.",
                Address = "Tòa nhà Landmark 81, 720A Điện Biên Phủ, Bình Thạnh, TP. Hồ Chí Minh",
                Website = "https://coin98.finance",
                Industry = "Blockchain & DeFi Platform",
                CompanySize = CompanySize.SME,
                ContactEmail = "career@coin98.finance",
                TaxCode = "0316827361",
                IsVerified = true
            },
            new Company
            {
                Name = "VTI Group",
                Description = "VTI là tập đoàn công nghệ thông tin hàng đầu cung cấp các giải pháp chuyển đổi số cho doanh nghiệp Nhật Bản, Hàn Quốc và Việt Nam.",
                Address = "Tòa nhà Mễ Trì Plaza, Mễ Trì, Quận Nam Từ Liêm, Hà Nội",
                Website = "https://vti.com.vn",
                Industry = "IT Outsourcing & Cloud Solutions",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "recruitment@vti.com.vn",
                TaxCode = "0107489371",
                IsVerified = true
            },
            new Company
            {
                Name = "Sun Asterisk",
                Description = "Sun* là một Digital Creative Studio chuyên hỗ trợ phát triển các startup và chuyển đổi số cho doanh nghiệp thông qua tư vấn thiết kế và lập trình.",
                Address = "Tòa nhà Keangnam Landmark 72, Phạm Hùng, Nam Từ Liêm, Hà Nội",
                Website = "https://sun-asterisk.vn",
                Industry = "Digital Consulting & Development",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "recruitment@sun-asterisk.com",
                TaxCode = "0105938506",
                IsVerified = true
            },
            new Company
            {
                Name = "VNLife (VNPAY)",
                Description = "VNLife là công ty mẹ của VNPAY, chuyên xây dựng hệ sinh thái công nghệ, giải pháp thanh toán điện tử bằng mã QR hàng đầu tại Việt Nam.",
                Address = "Tòa nhà Thành Công, 57 Láng Hạ, Quận Đống Đa, Hà Nội",
                Website = "https://vnlife.vn",
                Industry = "Fintech & Digital Ecosystem",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "tuyendung@vnpay.vn",
                TaxCode = "0102187361",
                IsVerified = true
            },

            // ── MULTINATIONAL R&D CENTERS & TECH GLOBAL BRANDS ────────────────────
            new Company
            {
                Name = "Samsung Vietnam Mobile R&D Center (SVMC)",
                Description = "Trung tâm Nghiên cứu & Phát triển Điện thoại Di động Samsung lớn nhất tại khu vực Đông Nam Á, tập trung nghiên cứu công nghệ viễn thông và ứng dụng di động.",
                Address = "Khu đô thị Tây Hồ Tây, Quận Bắc Từ Liêm, Hà Nội",
                Website = "https://www.samsung.com/vn",
                Industry = "Mobile Technology & Hardware R&D",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "svmc.recruitment@samsung.com",
                TaxCode = "0100632598",
                IsVerified = true
            },
            new Company
            {
                Name = "Intel Products Vietnam",
                Description = "Nhà máy kiểm định và đóng gói chip bán dẫn lớn nhất trong mạng lưới toàn cầu của tập đoàn Intel, nằm tại Khu Công nghệ cao TP.HCM.",
                Address = "Lô I2, Đường D1, Khu Công nghệ cao, Quận 9, TP. Hồ Chí Minh",
                Website = "https://www.intel.vn",
                Industry = "Semiconductor Manufacturing",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "vietnamjobs@intel.com",
                TaxCode = "0304382590",
                IsVerified = true
            },
            new Company
            {
                Name = "Bosch Global Software Technologies",
                Description = "Bosch cung cấp các dịch vụ phát triển phần mềm ô tô, hệ thống nhúng thông minh, IoT và các giải pháp chuyển đổi số cho tập đoàn Bosch toàn cầu.",
                Address = "Tòa nhà Etown, 364 Cộng Hòa, Phường 13, Quận Tân Bình, TP. Hồ Chí Minh",
                Website = "https://www.bosch-softwaretechnologies.com",
                Industry = "Embedded Systems & IoT Development",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "career.bgst@vn.bosch.com",
                TaxCode = "0309963845",
                IsVerified = true
            },
            new Company
            {
                Name = "Hitachi Digital Services",
                Description = "Hitachi cung cấp dịch vụ tư vấn kỹ thuật số và phát triển phần mềm tích hợp hệ thống cho thị trường Nhật Bản, Mỹ và các quốc gia Châu Âu.",
                Address = "Tòa nhà Flemington, 182 Lê Đại Hành, Quận 11, TP. Hồ Chí Minh",
                Website = "https://www.hitachids.com",
                Industry = "IT Services & Consulting",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "jobs.vn@hitachids.com",
                TaxCode = "0305481729",
                IsVerified = true
            },
            new Company
            {
                Name = "Fujitsu Vietnam",
                Description = "Nhà cung cấp hàng đầu các giải pháp hạ tầng CNTT, giải pháp phần mềm tích hợp và dịch vụ kỹ thuật mạng cao cấp từ Nhật Bản.",
                Address = "Tòa nhà Landmark, 56 Láng Hạ, Quận Đống Đa, Hà Nội",
                Website = "https://www.fujitsu.com/vn/",
                Industry = "IT Infrastructure & Solutions",
                CompanySize = CompanySize.SME,
                ContactEmail = "recruitment@fujitsu.com.vn",
                TaxCode = "0100984523",
                IsVerified = true
            },
            new Company
            {
                Name = "NTT DATA Vietnam",
                Description = "Thành viên của tập đoàn NTT DATA Nhật Bản, chuyên cung cấp các giải pháp phần mềm ERP, phát triển ứng dụng kinh doanh cho thị trường toàn cầu.",
                Address = "Tòa nhà Landmark 72, Phạm Hùng, Quận Nam Từ Liêm, Hà Nội",
                Website = "https://www.nttdata.com/vn",
                Industry = "ERP Consulting & IT Services",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "careers@nttdata.com.vn",
                TaxCode = "0102654329",
                IsVerified = true
            },
            new Company
            {
                Name = "Accenture Vietnam",
                Description = "Công ty tư vấn dịch vụ công nghệ, vận hành doanh nghiệp và phát triển phần mềm toàn cầu hàng đầu thế giới với văn phòng đại diện lớn tại TP.HCM.",
                Address = "Tòa nhà Bitexco Financial Tower, 2 Hải Triều, Quận 1, TP. Hồ Chí Minh",
                Website = "https://www.accenture.com",
                Industry = "Management Consulting & Tech Services",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "accenture.recruit@accenture.com",
                TaxCode = "0308945321",
                IsVerified = true
            },
            new Company
            {
                Name = "IBM Vietnam",
                Description = "Một trong những tập đoàn công nghệ thông tin hàng đầu thế giới, cung cấp các giải pháp siêu máy tính, điện toán đám mây lai (Hybrid Cloud) và trí tuệ nhân tạo (Watson AI).",
                Address = "Tòa nhà Pacific Place, 83B Lý Thường Kiệt, Quận Hoàn Kiếm, Hà Nội",
                Website = "https://www.ibm.com/vn-vi",
                Industry = "Enterprise AI & Hybrid Cloud Solutions",
                CompanySize = CompanySize.SME,
                ContactEmail = "ibmrecruit@vn.ibm.com",
                TaxCode = "0100249850",
                IsVerified = true
            },
            new Company
            {
                Name = "Line Technology Vietnam",
                Description = "Trung tâm phát triển phần mềm chuyên nghiệp của LINE Plus Corporation, chịu trách nhiệm xây dựng nền tảng ứng dụng LINE và phát triển các hệ thống nhắn tin quy mô cực lớn.",
                Address = "Tòa nhà Lotte Center, 54 Liễu Giai, Cống Vị, Ba Đình, Hà Nội",
                Website = "https://linecorp.com",
                Industry = "Mobile App & High-scale Platforms",
                CompanySize = CompanySize.SME,
                ContactEmail = "recruitment_ltv@linecorp.com",
                TaxCode = "0107693856",
                IsVerified = true
            },
            new Company
            {
                Name = "LG Electronics Development Vietnam",
                Description = "Trung tâm R&D chuyên biệt của LG Electronics tại Việt Nam, tập trung phát triển các hệ thống phần mềm nhúng giải trí cao cấp cho xe hơi (In-Vehicle Infotainment).",
                Address = "Tòa nhà Landmark 72, Phạm Hùng, Quận Nam Từ Liêm, Hà Nội",
                Website = "https://www.lg.com",
                Industry = "Automotive Systems & Embedded software",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "lgedv.recruit@lge.com",
                TaxCode = "0106983745",
                IsVerified = true
            },
            new Company
            {
                Name = "Siemens Vietnam",
                Description = "Siemens dẫn đầu toàn cầu về công nghiệp điện hóa, tự động hóa và số hóa nhà máy thông qua các giải pháp phần mềm quản trị vòng đời sản phẩm (PLM) tiên tiến.",
                Address = "Tòa nhà Landmark, 56 Láng Hạ, Quận Đống Đa, Hà Nội",
                Website = "https://www.siemens.com/vn",
                Industry = "Industrial Automation & Digital Enterprise",
                CompanySize = CompanySize.SME,
                ContactEmail = "hr.siemens@siemens.com",
                TaxCode = "0100938562",
                IsVerified = true
            },

            // ── FAST-GROWING STARTUPS & SMEs ──────────────────────────────────────
            new Company
            {
                Name = "ELSA Speak Vietnam",
                Description = "ELSA sở hữu công nghệ nhận diện giọng nói bằng AI hàng đầu thế giới, phát triển ứng dụng học tiếng Anh ELSA Speak phổ biến toàn cầu.",
                Address = "Tòa nhà Dreamplex, 195 Điện Biên Phủ, Bình Thạnh, TP. Hồ Chí Minh",
                Website = "https://elsaspeak.vn",
                Industry = "AI Edtech Platform",
                CompanySize = CompanySize.SME,
                ContactEmail = "careers@elsaland.com",
                TaxCode = "0314093821",
                IsVerified = true
            },
            new Company
            {
                Name = "Giao Hàng Nhanh (GHN)",
                Description = "GHN là nhà cung cấp dịch vụ logistics chuyên nghiệp cho các sàn thương mại điện tử, phát triển hệ thống quản lý phân loại hàng tự động dựa trên công nghệ cao.",
                Address = "405/15 Xô Viết Nghệ Tĩnh, Phường 24, Bình Thạnh, TP. Hồ Chí Minh",
                Website = "https://ghn.vn",
                Industry = "Logistics Tech",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "tuyendung@ghn.vn",
                TaxCode = "0311802934",
                IsVerified = true
            },
            new Company
            {
                Name = "Giao Hàng Tiết Kiệm (GHTK)",
                Description = "GHTK ứng dụng công nghệ di động và phân tích dữ liệu lớn để tối ưu hóa quy trình vận chuyển cho hàng triệu shop online trên khắp 63 tỉnh thành.",
                Address = "Tòa nhà GHTK, Phạm Hùng, Mễ Trì, Nam Từ Liêm, Hà Nội",
                Website = "https://giaohangtietkiem.vn",
                Industry = "Logistics Tech",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "jobs@ghtk.vn",
                TaxCode = "0106183921",
                IsVerified = true
            },
            new Company
            {
                Name = "GotIt Vietnam",
                Description = "GotIt sở hữu nền tảng dịch vụ tư vấn kỹ thuật qua ứng dụng di động theo yêu cầu thời gian thực, có đội ngũ kỹ sư chất lượng cao hàng đầu tại Việt Nam.",
                Address = "Tòa nhà Lotte Center, 54 Liễu Giai, Ba Đình, Hà Nội",
                Website = "https://www.gotitapp.com",
                Industry = "On-demand Tech & QA",
                CompanySize = CompanySize.SME,
                ContactEmail = "jobs-vn@gotitapp.com",
                TaxCode = "0107389271",
                IsVerified = true
            },
            new Company
            {
                Name = "OnPoint Vietnam",
                Description = "OnPoint cung cấp giải pháp hỗ trợ bán hàng thương mại điện tử toàn diện cho các thương hiệu quốc tế tại thị trường Đông Nam Á.",
                Address = "Tòa nhà Saigon Centre, 65 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh",
                Website = "https://onpoint.vn",
                Industry = "E-commerce Enabler",
                CompanySize = CompanySize.SME,
                ContactEmail = "careers@onpoint.vn",
                TaxCode = "0314798365",
                IsVerified = true
            },
            new Company
            {
                Name = "Luvina Software",
                Description = "Luvina chuyên đào tạo và cung cấp dịch vụ phát triển phần mềm chất lượng cao cho thị trường Nhật Bản, hoạt động theo tiêu chuẩn quản lý quốc tế.",
                Address = "Tòa nhà Toyota Thanh Xuân, 315 Trường Chinh, Thanh Xuân, Hà Nội",
                Website = "https://luvina.net",
                Industry = "Software Outsourcing (Japan Market)",
                CompanySize = CompanySize.ENTERPRISE,
                ContactEmail = "recruitment@luvina.net",
                TaxCode = "0101538942",
                IsVerified = true
            },
            new Company
            {
                Name = "DEHA Vietnam",
                Description = "DEHA phát triển các giải pháp phần mềm, chuyển đổi số doanh nghiệp sử dụng trí tuệ nhân tạo (AI) và công nghệ Web3 hiện đại.",
                Address = "Tòa nhà Charmvit, 117 Trần Duy Hưng, Cầu Giấy, Hà Nội",
                Website = "https://deha-software.com",
                Industry = "Software Development & AI Solutions",
                CompanySize = CompanySize.SME,
                ContactEmail = "careers@deha.vn",
                TaxCode = "0107593845",
                IsVerified = true
            }
        };

        var now = DateTimeOffset.UtcNow;

        foreach (var c in rawCompanies)
        {
            // Kiểm tra xem công ty cùng tên đã tồn tại chưa (không phân biệt hoa thường để an toàn)
            var exists = await db.Companies.IgnoreQueryFilters()
                .AnyAsync(x => x.Name.ToLower() == c.Name.ToLower() || (c.TaxCode != null && x.TaxCode == c.TaxCode));

            if (!exists)
            {
                // Sử dụng deterministic Guid tạo từ tên để tránh thay đổi ngẫu nhiên mỗi lần chạy
                c.Id = CreateDeterministicGuid(c.Name);
                c.CreatedDate = now;
                c.CreatedBy = "system";
                c.IsDeleted = false;
                
                await db.Companies.AddAsync(c);
            }
        }

        await db.SaveChangesAsync();
    }

    private static Guid CreateDeterministicGuid(string input)
    {
        using (var md5 = MD5.Create())
        {
            byte[] hash = md5.ComputeHash(Encoding.UTF8.GetBytes(input.Trim().ToLowerInvariant()));
            return new Guid(hash);
        }
    }
}
