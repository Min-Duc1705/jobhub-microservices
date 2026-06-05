# app/services/ai_assistant_service/tools.py
import re
import google.generativeai as genai

_ALL_TOOL_DEFS = [
    {
        "name": "search_jobs",
        "description": "Tìm kiếm danh sách tin tuyển dụng trong hệ thống JobHub. Hỗ trợ lọc theo từ khóa, cấp độ (level), kỹ năng, địa điểm và mức lương.",
        "permissions_required": [("GET", "/api/v1/jobs")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Từ khóa tìm kiếm chung (tên vị trí, công ty). Tránh đưa các từ khóa chỉ cấp độ như 'junior', 'senior' vào đây, thay vào đó hãy dùng tham số 'level' tương ứng."},
                "level": {"type": "string", "description": "Cấp độ công việc. Chỉ nhận một trong các giá trị: INTERN, JUNIOR, MIDDLE, SENIOR, LEAD, DIRECTOR. Hãy phân tích câu hỏi của user để trích xuất cấp độ phù hợp."},
                "location": {"type": "string", "description": "Địa điểm làm việc cần lọc (ví dụ: 'Hà Nội', 'Hồ Chí Minh')"},
                "salaryMin": {"type": "number", "description": "Mức lương tối thiểu yêu cầu (ví dụ: 15)"},
                "salaryMax": {"type": "number", "description": "Mức lương tối đa yêu cầu (ví dụ: 30)"},
                "skills": {"type": "array", "items": {"type": "string"}, "description": "Mảng danh sách tên các kỹ năng cần lọc (ví dụ: ['React', 'Java', 'Nodejs'])"},
                "pageSize": {"type": "integer", "description": "Số lượng kết quả trả về (mặc định 10)"},
            },
            "required": []
        }
    },
    {
        "name": "get_job_detail",
        "description": "Xem chi tiết thông tin một tin tuyển dụng cụ thể theo ID",
        "permissions_required": [("GET", "/api/v1/jobs")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID của tin tuyển dụng"}
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "preview_create_job",
        "description": "Tạo bản xem trước (preview) nội dung tin tuyển dụng từ mô tả của HR hoặc từ ảnh JD. Chưa thực sự tạo job, chỉ hiển thị để HR xem lại và xác nhận",
        "permissions_required": [("POST", "/api/v1/jobs")],
        "action_type": "preview",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Tên vị trí tuyển dụng"},
                "description": {"type": "string", "description": "Mô tả công việc chi tiết"},
                "requirements": {"type": "string", "description": "Yêu cầu ứng viên"},
                "benefits": {"type": "string", "description": "Quyền lợi và phúc lợi"},
                "location": {"type": "string", "description": "Địa điểm làm việc"},
                "salary_min": {"type": "number", "description": "Mức lương tối thiểu. Nếu tiền tệ là VND thì điền số triệu (ví dụ: 15), nếu là USD thì điền số USD thực tế (ví dụ: 1000)"},
                "salary_max": {"type": "number", "description": "Mức lương tối đa. Nếu tiền tệ là VND thì điền số triệu (ví dụ: 25), nếu là USD thì điền số USD thực tế (ví dụ: 2500)"},
                "salary_currency": {"type": "string", "description": "Loại tiền tệ của mức lương, chỉ nhận 'VND' hoặc 'USD'. Mặc định là 'VND'."},
                "quantity": {"type": "integer", "description": "Số lượng tuyển dụng"},
                "deadline": {"type": "string", "description": "Hạn nộp hồ sơ (YYYY-MM-DD)"},
                "skill_names": {"type": "array", "items": {"type": "string"}, "description": "Danh sách kỹ năng yêu cầu"},
                "experience_required": {"type": "string", "description": "Kinh nghiệm yêu cầu (ví dụ: '2 năm', 'Không yêu cầu', '1-3 năm')"},
                "category": {"type": "string", "description": "Ngành nghề công việc. BẮT BUỘC chọn một trong các giá trị sau: 'Software Development', 'Frontend Development', 'Backend Development', 'Fullstack Development', 'Mobile Development', 'DevOps & Cloud', 'Data Engineering', 'Data Science & AI', 'Cybersecurity', 'QA & Testing', 'UI/UX Design', 'Product Management', 'Business Analysis', 'ERP & Enterprise Systems', 'Network & Sysadmin', 'IT Support', 'Game Development', 'Blockchain & Web3', 'Embedded & IoT', 'Engineering', 'Marketing', 'Sales', 'Other'."}
            },
            "required": ["name", "salary_currency"]
        }
    },
    {
        "name": "delete_job",
        "description": "Tạo bản xem trước (preview) xác nhận xóa tin tuyển dụng theo ID. Công cụ này chỉ tạo preview hiển thị giao diện xác nhận xóa cho HR, không thực sự xóa ngay lập tức.",
        "permissions_required": [("DELETE", "/api/v1/jobs/{id}")],
        "action_type": "preview",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID của tin tuyển dụng cần xóa"},
                "job_name": {"type": "string", "description": "Tên của tin tuyển dụng cần xóa (dùng để hiển thị trong preview xác nhận)"}
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "search_candidates",
        "description": "Tìm kiếm ứng viên phù hợp với tiêu chí của HR (tên, kỹ năng, địa điểm, trạng thái tìm việc)",
        "permissions_required": [("GET", "/api/v1/customers")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Từ khóa tìm kiếm theo tên hoặc kỹ năng"},
                "pageSize": {"type": "integer", "description": "Số lượng kết quả"}
            },
            "required": []
        }
    },
    {
        "name": "get_applications_for_job",
        "description": "Xem danh sách hồ sơ ứng tuyển của một tin tuyển dụng, bao gồm trạng thái review",
        "permissions_required": [("GET", "/api/v1/applications")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID tin tuyển dụng cần xem hồ sơ"}
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "predict_salary",
        "description": "Dự đoán mức lương thị trường dựa trên vị trí, kỹ năng, kinh nghiệm và địa điểm làm việc",
        "permissions_required": [],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "job_title": {"type": "string", "description": "Tên vị trí công việc"},
                "experience_years": {"type": "number", "description": "Số năm kinh nghiệm"},
                "skills": {"type": "array", "items": {"type": "string"}, "description": "Danh sách kỹ năng"},
                "location": {"type": "string", "description": "Địa điểm làm việc"}
            },
            "required": ["job_title"]
        }
    },
    {
        "name": "get_my_company_info",
        "description": "Lấy thông tin công ty của HR đang đăng nhập (tên công ty, mô tả, logo, số lượng nhân viên)",
        "permissions_required": [("GET", "/api/v1/companies")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_my_jobs",
        "description": "Xem danh sách tin tuyển dụng do HR đang đăng nhập tạo ra",
        "permissions_required": [("GET", "/api/v1/jobs")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "pageSize": {"type": "integer", "description": "Số lượng tin hiển thị"}
            },
            "required": []
        }
    },
    {
        "name": "navigate_to_page",
        "description": "Chuyển hướng hoặc mở một trang cụ thể trên website JobHub theo yêu cầu của người dùng (ví dụ: trang quản lý tuyển dụng, trang cài đặt hồ sơ, dashboard admin, v.v.).",
        "permissions_required": [],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "page_name": {
                    "type": "string",
                    "description": "Tên định danh của trang cần mở. Chỉ nhận các giá trị: 'home', 'jobs', 'companies', 'job_detail', 'salary_predictor', 'profile_settings', 'resume_manager', 'applied_jobs', 'saved_jobs', 'hr_jobs', 'hr_hire_agent', 'admin_dashboard', 'admin_jobs', 'admin_users', 'admin_skills', 'admin_companies', 'admin_resumes', 'admin_applications'"
                },
                "path": {
                    "type": "string",
                    "description": (
                        "Đường dẫn URL tương đối của trang cần mở. Bạn BẮT BUỘC phải điền đúng đường dẫn tương ứng với page_name như sau:\n"
                        "- 'home': '/'\n"
                        "- 'jobs': '/jobs'\n"
                        "- 'companies': '/companies'\n"
                        "- 'job_detail': '/jobs/{jobId}' (ví dụ: '/jobs/6d7f2b74-d7d5-41ee-94f5-ca58973bf3a0')\n"
                        "- 'salary_predictor': '/salary-predict'\n"
                        "- 'profile_settings': '/candidate/profile'\n"
                        "- 'resume_manager': '/candidate/resume'\n"
                        "- 'applied_jobs': '/candidate/applied-jobs'\n"
                        "- 'saved_jobs': '/candidate/saved-jobs'\n"
                        "- 'hr_jobs': '/hr/jobs'\n"
                        "- 'hr_hire_agent': '/hr/hire-agent'\n"
                        "- 'admin_dashboard': '/admin/dashboard'\n"
                        "- 'admin_jobs': '/admin/jobs'\n"
                        "- 'admin_users': '/admin/customers'\n"
                        "- 'admin_skills': '/admin/skills'\n"
                        "- 'admin_companies': '/admin/companies'\n"
                        "- 'admin_resumes': '/admin/resumes'\n"
                        "- 'admin_applications': '/admin/applications'\n"
                        "Đối với trang chi tiết công ty, dùng định dạng: '/companies/{companyId}' (ví dụ: '/companies/6d7f2b74-d7d5-41ee-94f5-ca58973bf3a0')."
                    )
                }
            },
            "required": ["page_name", "path"]
        }
    },
    {
        "name": "search_companies",
        "description": "Tìm kiếm thông tin danh sách các công ty trong hệ thống theo tên hoặc từ khóa (ví dụ: 'Viettel', 'FPT', 'Lazada', v.v.). Công cụ này giúp tìm kiếm ID của công ty.",
        "permissions_required": [],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "Tên công ty hoặc từ khóa cần tìm (ví dụ: 'Viettel')"
                },
                "pageSize": {
                    "type": "integer",
                    "description": "Số lượng kết quả tối đa (mặc định 10)"
                }
            },
            "required": ["keyword"]
        }
    },
    {
        "name": "update_my_profile",
        "description": "Cập nhật thông tin hồ sơ cá nhân của người dùng đang đăng nhập (như tên hiển thị username, họ tên fullName, số điện thoại phone, địa chỉ address, giới thiệu bản thân summary, số năm kinh nghiệm yearsOfExperience, mức lương mong muốn expectedSalary, giới tính gender, chức vụ position, trạng thái tìm việc jobSearchStatus).",
        "permissions_required": [("PUT", "/api/v1/customers/me")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "Tên hiển thị (username) mới của tài khoản"},
                "fullName": {"type": "string", "description": "Họ và tên đầy đủ mới của bạn"},
                "phone": {"type": "string", "description": "Số điện thoại liên hệ mới"},
                "address": {"type": "string", "description": "Địa chỉ liên hệ mới"},
                "summary": {"type": "string", "description": "Mô tả giới thiệu bản thân ngắn gọn"},
                "yearsOfExperience": {"type": "integer", "description": "Số năm kinh nghiệm làm việc"},
                "expectedSalary": {"type": "number", "description": "Mức lương mong muốn kỳ vọng (VNĐ/tháng)"},
                "gender": {"type": "string", "description": "Giới tính mới. Chỉ nhận một trong các giá trị: 'MALE', 'FEMALE', hoặc 'OTHER'"},
                "position": {"type": "string", "description": "Vị trí chức vụ hiện tại (ví dụ: 'Developer', 'HR Manager')"},
                "jobSearchStatus": {"type": "string", "description": "Trạng thái tìm việc. Chỉ nhận một trong các giá trị: 'ACTIVELY_LOOKING' (đang tìm việc), 'OPEN_TO_OFFERS' (sẵn sàng đón nhận cơ hội), hoặc 'NOT_LOOKING' (không tìm việc)"}
            },
            "required": []
        }
    },
    {
        "name": "get_my_saved_jobs",
        "description": "Lấy danh sách các tin tuyển dụng đã lưu của ứng viên đang đăng nhập",
        "permissions_required": [("GET", "/api/v1/saved-jobs")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "pageSize": {"type": "integer", "description": "Số lượng kết quả tối đa (mặc định 10)"}
            },
            "required": []
        }
    },
    {
        "name": "save_job",
        "description": "Lưu tin tuyển dụng vào danh sách việc làm đã lưu của ứng viên",
        "permissions_required": [("POST", "/api/v1/saved-jobs/{jobId}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID tin tuyển dụng cần lưu"},
                "note": {"type": "string", "description": "Ghi chú tùy chọn khi lưu tin tuyển dụng"}
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "unsave_job",
        "description": "Bỏ lưu tin tuyển dụng khỏi danh sách việc làm đã lưu của ứng viên",
        "permissions_required": [("DELETE", "/api/v1/saved-jobs/{jobId}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID tin tuyển dụng cần bỏ lưu"}
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "get_my_resumes",
        "description": "Lấy danh sách các CV (Resumes) của ứng viên đang đăng nhập",
        "permissions_required": [("GET", "/api/v1/resumes")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "pageSize": {"type": "integer", "description": "Số lượng kết quả tối đa (mặc định 10)"}
            },
            "required": []
        }
    },
    {
        "name": "set_default_resume",
        "description": "Đặt một CV làm mặc định để nộp tuyển cho ứng viên đang đăng nhập",
        "permissions_required": [("PATCH", "/api/v1/resumes/{id}/set-default")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "resume_id": {"type": "string", "description": "ID của CV cần đặt làm mặc định"}
            },
            "required": ["resume_id"]
        }
    },
    {
        "name": "delete_resume",
        "description": "Xóa một CV theo ID của ứng viên đang đăng nhập",
        "permissions_required": [("DELETE", "/api/v1/resumes/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "resume_id": {"type": "string", "description": "ID của CV cần xóa"}
            },
            "required": ["resume_id"]
        }
    },
    {
        "name": "get_my_applications",
        "description": "Lấy danh sách các đơn ứng tuyển (Applications) của người dùng đang đăng nhập",
        "permissions_required": [("GET", "/api/v1/applications")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "pageSize": {"type": "integer", "description": "Số lượng kết quả tối đa (mặc định 10)"}
            },
            "required": []
        }
    },
    {
        "name": "apply_job",
        "description": "Nộp đơn ứng tuyển vào một tin tuyển dụng sử dụng một CV cụ thể của ứng viên",
        "permissions_required": [("POST", "/api/v1/applications")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID của tin tuyển dụng cần ứng tuyển"},
                "resume_id": {"type": "string", "description": "ID của CV dùng để ứng tuyển"},
                "cover_letter": {"type": "string", "description": "Thư xin việc đi kèm (tùy chọn)"}
            },
            "required": ["job_id", "resume_id"]
        }
    },
    {
        "name": "cancel_application",
        "description": "Hủy đơn ứng tuyển vào một tin tuyển dụng của ứng viên",
        "permissions_required": [("DELETE", "/api/v1/applications/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "application_id": {"type": "string", "description": "ID của đơn ứng tuyển cần hủy"}
            },
            "required": ["application_id"]
        }
    },
    {
        "name": "review_application",
        "description": "HR cập nhật trạng thái duyệt/từ chối đơn ứng tuyển của ứng viên",
        "permissions_required": [("PATCH", "/api/v1/applications/{id}/status")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "application_id": {"type": "string", "description": "ID của đơn ứng tuyển cần cập nhật trạng thái"},
                "status": {"type": "string", "description": "Trạng thái mới. Chỉ nhận một trong các giá trị: 'PENDING', 'REVIEWING', 'APPROVED', 'REJECTED'"},
                "review_note": {"type": "string", "description": "Ghi chú nhận xét của nhà tuyển dụng (tùy chọn)"}
            },
            "required": ["application_id", "status"]
        }
    },
    {
        "name": "update_company_info",
        "description": "HR cập nhật thông tin chi tiết của công ty đang quản lý",
        "permissions_required": [("PUT", "/api/v1/companies/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "ID của công ty cần cập nhật thông tin"},
                "name": {"type": "string", "description": "Tên công ty mới"},
                "description": {"type": "string", "description": "Mô tả giới thiệu chi tiết công ty"},
                "address": {"type": "string", "description": "Địa chỉ trụ sở công ty"},
                "companySize": {"type": "string", "description": "Quy mô nhân sự công ty. Chỉ nhận: 'STARTUP', 'SME', hoặc 'ENTERPRISE'"},
                "industry": {"type": "string", "description": "Lĩnh vực ngành nghề công ty"},
                "website": {"type": "string", "description": "Địa chỉ website công ty"},
                "contactEmail": {"type": "string", "description": "Email liên hệ tuyển dụng của công ty"},
                "taxCode": {"type": "string", "description": "Mã số thuế doanh nghiệp"}
            },
            "required": ["company_id"]
        }
    },
    {
        "name": "get_my_hire_agent_campaigns",
        "description": "Lấy danh sách các chiến dịch tuyển dụng bằng AI (Hire Agent Campaigns) của HR đang đăng nhập",
        "permissions_required": [],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "create_hire_agent_campaign",
        "description": "Tạo một chiến dịch tuyển dụng bằng AI cho tin tuyển dụng cụ thể để tự động sàng lọc và liên hệ ứng viên",
        "permissions_required": [],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID tin tuyển dụng muốn tạo chiến dịch"},
                "job_name": {"type": "string", "description": "Tên tin tuyển dụng"},
                "job_description": {"type": "string", "description": "Mô tả yêu cầu tuyển dụng chi tiết"},
                "target_count": {"type": "integer", "description": "Số lượng ứng viên muốn liên hệ sàng lọc (mặc định 5)"},
                "job_location": {"type": "string", "description": "Địa điểm tuyển dụng (tỉnh/thành phố)"},
                "job_type": {"type": "string", "description": "Loại hình công việc. Chỉ nhận: 'REMOTE', 'HYBRID', 'FULL_TIME', 'PART_TIME', hoặc 'INTERNSHIP'"}
            },
            "required": ["job_id", "job_name", "job_description"]
        }
    },
    {
        "name": "schedule_campaign_interview",
        "description": "Đặt lịch hẹn phỏng vấn cho ứng viên trong chiến dịch tuyển dụng AI cụ thể",
        "permissions_required": [],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string", "description": "ID chiến dịch tuyển dụng AI tương ứng"},
                "interview_date": {"type": "string", "description": "Thời gian hẹn phỏng vấn dạng ISO 8601 (ví dụ: '2026-06-15T09:00:00+07:00')"}
            },
            "required": ["campaign_id", "interview_date"]
        }
    },
    {
        "name": "broadcast_notification",
        "description": "Gửi thông báo hệ thống (broadcast) tới toàn bộ người dùng hoặc một nhóm đối tượng cụ thể (HR, Candidate)",
        "permissions_required": [("POST", "/api/v1/users/notifications/broadcast")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Tiêu đề thông báo"},
                "message": {"type": "string", "description": "Nội dung chi tiết thông báo"},
                "type": {"type": "string", "description": "Loại thông báo. Chỉ nhận các giá trị: 'default', 'recommend', 'invite', 'view'. Mặc định là 'default'."},
                "target_group": {"type": "string", "description": "Nhóm đối tượng nhận thông báo. Chỉ nhận các giá trị: 'ALL' (tất cả người dùng), 'HR' (chỉ nhà tuyển dụng), 'CANDIDATE' (chỉ ứng viên). Mặc định là 'ALL'."}
            },
            "required": ["title", "message"]
        }
    },
]

def normalize_path(path: str) -> str:
    """Chuẩn hóa path parameters dạng {id}, {job_id}, {jobId}... về {id}."""
    path = path.strip().lower()
    path = re.sub(r'\{[^}]+\}', '{id}', path)
    return path

def _filter_tools_by_permission(user_permissions: list[dict], user_role: str = "USER") -> list[dict]:
    """Lọc danh sách tools dựa trên permissions thực tế của user."""
    role_upper = (user_role or "USER").upper()
    # Bypass gán tất cả quyền cho ADMIN (tương ứng logic trong C# backend)
    if role_upper == "ADMIN":
        return _ALL_TOOL_DEFS

    # Tạo tập hợp các quyền đã được normalize
    user_perms_set = set()
    for p in user_permissions:
        method = p.get("method", "").upper()
        path = normalize_path(p.get("apiPath", ""))
        user_perms_set.add((method, path))

    available = []
    for tool_def in _ALL_TOOL_DEFS:
        req_perms = tool_def.get("permissions_required", [])
        if not req_perms:
            # Không yêu cầu quyền -> công cụ công khai
            available.append(tool_def)
            continue

        # Kiểm tra xem user có đủ tất cả các quyền yêu cầu của tool hay không
        has_all_perms = True
        for req_method, req_path in req_perms:
            norm_req_path = normalize_path(req_path)
            if (req_method.upper(), norm_req_path) not in user_perms_set:
                has_all_perms = False
                break

        if has_all_perms:
            available.append(tool_def)

    return available

def _build_gemini_tools(available_tool_defs: list[dict]) -> list:
    """Build Gemini FunctionDeclaration objects from tool definitions."""
    function_declarations = []
    for td in available_tool_defs:
        # Build properties schema supporting string, integer, number, and array
        properties = {}
        for k, v in td["parameters"].get("properties", {}).items():
            param_type = v.get("type", "string")
            if param_type == "array":
                properties[k] = genai.protos.Schema(
                    type=genai.protos.Type.ARRAY,
                    description=v.get("description", ""),
                    items=genai.protos.Schema(type=genai.protos.Type.STRING)
                )
            else:
                properties[k] = genai.protos.Schema(
                    type=genai.protos.Type.STRING if param_type == "string" else
                         genai.protos.Type.INTEGER if param_type == "integer" else
                         genai.protos.Type.NUMBER if param_type == "number" else
                         genai.protos.Type.STRING,
                    description=v.get("description", "")
                )

        decl = genai.protos.FunctionDeclaration(
            name=td["name"],
            description=td["description"],
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties=properties,
                required=td["parameters"].get("required", [])
            )
        )
        function_declarations.append(decl)

    if not function_declarations:
        return []

    return [genai.protos.Tool(function_declarations=function_declarations)]
