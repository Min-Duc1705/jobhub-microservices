# app/services/ai_assistant_service/tools/definitions.py
"""
Danh sách tất cả AI Tool definitions.
Mỗi tool định nghĩa: name, description, permissions_required, action_type, parameters.
"""

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
        # Dùng POST /api/v1/jobs làm gate: permission này chỉ HR có (CANDIDATE không có)
        # → Chỉ HR/ADMIN thấy tool này, CANDIDATE không thấy
        "permissions_required": [("POST", "/api/v1/jobs")],
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
        # Dùng POST /api/v1/jobs làm gate: permission này chỉ HR có (CANDIDATE không có)
        "permissions_required": [("POST", "/api/v1/jobs")],
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
        # Dùng DELETE /api/v1/jobs/{id} làm gate: chỉ HR/ADMIN có permission này
        "permissions_required": [("DELETE", "/api/v1/jobs/{id}")],
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
    # ── Company ──────────────────────────────────────────────────────────────
    {
        "name": "create_company",
        "description": "Tạo mới một công ty trong hệ thống. Chỉ Admin mới có quyền tạo công ty.",
        "permissions_required": [("POST", "/api/v1/companies")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "name":         {"type": "string", "description": "Tên công ty (bắt buộc)"},
                "description":  {"type": "string", "description": "Mô tả giới thiệu công ty"},
                "address":      {"type": "string", "description": "Địa chỉ trụ sở công ty"},
                "industry":     {"type": "string", "description": "Lĩnh vực ngành nghề (ví dụ: 'Technology', 'Finance', 'Healthcare')"},
                "companySize":  {"type": "string", "description": "Quy mô công ty. Chỉ nhận: 'STARTUP', 'SME', hoặc 'ENTERPRISE'"},
                "website":      {"type": "string", "description": "Địa chỉ website công ty"},
                "contactEmail": {"type": "string", "description": "Email liên hệ tuyển dụng"},
                "taxCode":      {"type": "string", "description": "Mã số thuế doanh nghiệp"},
            },
            "required": ["name"]
        }
    },
    # ── Skills — Admin quản trị ───────────────────────────────────────────────
    {
        "name": "get_all_skills",
        "description": "Lấy danh sách tất cả kỹ năng trong hệ thống (dùng cho Admin hoặc HR tra cứu).",
        "permissions_required": [("GET", "/api/v1/skills")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword":  {"type": "string", "description": "Từ khóa tìm kiếm tên kỹ năng (ví dụ: 'React', 'Java')"},
                "pageSize": {"type": "integer", "description": "Số lượng kết quả trả về (mặc định 20)"},
            },
            "required": []
        }
    },
    {
        "name": "create_skill",
        "description": "Tạo mới một kỹ năng trong hệ thống. Chỉ Admin mới có quyền thực hiện.",
        "permissions_required": [("POST", "/api/v1/skills")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "name":        {"type": "string", "description": "Tên kỹ năng (ví dụ: 'React', 'Java Spring Boot')"},
                "description": {"type": "string", "description": "Mô tả ngắn về kỹ năng"},
            },
            "required": ["name"]
        }
    },
    {
        "name": "update_skill",
        "description": "Cập nhật tên hoặc mô tả của một kỹ năng theo ID. Chỉ Admin mới có quyền thực hiện.",
        "permissions_required": [("PUT", "/api/v1/skills/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_id":    {"type": "string", "description": "ID của kỹ năng cần cập nhật"},
                "name":        {"type": "string", "description": "Tên mới của kỹ năng"},
                "description": {"type": "string", "description": "Mô tả mới của kỹ năng"},
            },
            "required": ["skill_id"]
        }
    },
    {
        "name": "delete_skill",
        "description": "Xóa một kỹ năng khỏi hệ thống theo ID. Chỉ Admin mới có quyền thực hiện.",
        "permissions_required": [("DELETE", "/api/v1/skills/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_id": {"type": "string", "description": "ID của kỹ năng cần xóa"},
            },
            "required": ["skill_id"]
        }
    },
    # ── Skills — Cá nhân (HR + CANDIDATE) ────────────────────────────────────
    {
        "name": "add_my_skill",
        "description": "Thêm một kỹ năng vào hồ sơ cá nhân của người dùng đang đăng nhập (HR hoặc Candidate). Cần có skill_id — dùng get_all_skills để tra cứu ID trước.",
        # POST /api/v1/skills/me — không yêu cầu permission đặc biệt (chỉ cần đăng nhập)
        # Dùng GET /api/v1/jobs làm gate chung cho mọi user đã đăng nhập có trong DB
        "permissions_required": [("GET", "/api/v1/jobs")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_id": {"type": "string", "description": "ID của kỹ năng muốn thêm vào hồ sơ (lấy từ get_all_skills)"},
            },
            "required": ["skill_id"]
        }
    },
    {
        "name": "remove_my_skill",
        "description": "Xóa một kỹ năng khỏi hồ sơ cá nhân của người dùng đang đăng nhập (HR hoặc Candidate).",
        # DELETE /api/v1/skills/me/{skillId} — không yêu cầu permission đặc biệt
        "permissions_required": [("GET", "/api/v1/jobs")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_id": {"type": "string", "description": "ID của kỹ năng muốn xóa khỏi hồ sơ"},
            },
            "required": ["skill_id"]
        }
    },
    # ── Jobs — HR update & status ─────────────────────────────────────────────
    {
        "name": "update_job",
        "description": "HR cập nhật thông tin chi tiết của một tin tuyển dụng theo ID (tên, mô tả, yêu cầu, lương, hạn nộp, kỹ năng...)",
        "permissions_required": [("PUT", "/api/v1/jobs/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id":              {"type": "string",  "description": "ID tin tuyển dụng cần cập nhật"},
                "name":                {"type": "string",  "description": "Tên vị trí tuyển dụng mới"},
                "description":         {"type": "string",  "description": "Mô tả công việc mới"},
                "requirements":        {"type": "string",  "description": "Yêu cầu ứng viên mới"},
                "benefits":            {"type": "string",  "description": "Quyền lợi mới"},
                "location":            {"type": "string",  "description": "Địa điểm làm việc mới"},
                "salary_min":          {"type": "number",  "description": "Mức lương tối thiểu mới"},
                "salary_max":          {"type": "number",  "description": "Mức lương tối đa mới"},
                "salary_currency":     {"type": "string",  "description": "Loại tiền tệ: 'VND' hoặc 'USD'"},
                "quantity":            {"type": "integer", "description": "Số lượng tuyển mới"},
                "deadline":            {"type": "string",  "description": "Hạn nộp hồ sơ mới (YYYY-MM-DD)"},
                "skill_names":         {"type": "array", "items": {"type": "string"}, "description": "Danh sách kỹ năng mới"},
                "experience_required": {"type": "string",  "description": "Kinh nghiệm yêu cầu mới"},
                "category":            {"type": "string",  "description": "Ngành nghề mới (xem giá trị hợp lệ như preview_create_job)"},
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "change_job_status",
        "description": "HR/Admin thay đổi trạng thái của tin tuyển dụng (DRAFT → PUBLISHED, PUBLISHED → CLOSED, v.v.)",
        "permissions_required": [("PATCH", "/api/v1/jobs/{id}/status")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "ID của tin tuyển dụng cần đổi trạng thái"},
                "status": {"type": "string", "description": "Trạng thái mới. Chỉ nhận: 'DRAFT', 'PUBLISHED', hoặc 'CLOSED'"},
            },
            "required": ["job_id", "status"]
        }
    },
    # ── Admin — User management ───────────────────────────────────────────────
    {
        "name": "get_all_users",
        "description": "Admin xem danh sách toàn bộ tài khoản user trong hệ thống (có thể lọc theo email, trạng thái, role)",
        "permissions_required": [("GET", "/api/v1/users")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword":  {"type": "string",  "description": "Từ khóa tìm theo email hoặc username"},
                "status":   {"type": "string",  "description": "Lọc theo trạng thái: 'ACTIVE' hoặc 'INACTIVE'"},
                "pageSize": {"type": "integer", "description": "Số lượng kết quả (mặc định 20)"},
            },
            "required": []
        }
    },
    {
        "name": "get_user_detail",
        "description": "Admin xem thông tin chi tiết của một tài khoản user theo ID",
        "permissions_required": [("GET", "/api/v1/users/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "ID của user cần xem chi tiết"},
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "update_user",
        "description": "Admin cập nhật thông tin tài khoản user (username, email, role, trạng thái active)",
        "permissions_required": [("PUT", "/api/v1/users/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id":  {"type": "string",  "description": "ID của user cần cập nhật"},
                "username": {"type": "string",  "description": "Username mới"},
                "email":    {"type": "string",  "description": "Email mới"},
                "roleId":   {"type": "string",  "description": "ID của role mới (dùng get_all_roles để tra cứu)"},
                "isActive": {"type": "boolean", "description": "Trạng thái kích hoạt tài khoản (true/false)"},
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "delete_user",
        "description": "Admin xóa tài khoản user theo ID",
        "permissions_required": [("DELETE", "/api/v1/users/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "ID của user cần xóa"},
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "reset_user_password",
        "description": "Admin đặt lại mật khẩu cho tài khoản user theo ID",
        "permissions_required": [("PATCH", "/api/v1/users/{id}/reset-password")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id":      {"type": "string", "description": "ID của user cần reset mật khẩu"},
                "new_password": {"type": "string", "description": "Mật khẩu mới (tối thiểu 8 ký tự, nên có chữ hoa, số, ký tự đặc biệt)"},
            },
            "required": ["user_id", "new_password"]
        }
    },
    # ── Admin — Roles ─────────────────────────────────────────────────────────
    {
        "name": "get_all_roles",
        "description": "Admin xem danh sách tất cả role trong hệ thống (ADMIN, HR, CANDIDATE, v.v.)",
        "permissions_required": [("GET", "/api/v1/roles")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword":  {"type": "string",  "description": "Từ khóa tìm kiếm tên role"},
                "pageSize": {"type": "integer", "description": "Số lượng kết quả (mặc định 50)"},
            },
            "required": []
        }
    },
    # ── Admin — Permissions ───────────────────────────────────────────────────
    {
        "name": "get_all_permissions",
        "description": "Admin xem danh sách tất cả permission trong hệ thống, có thể lọc theo module hoặc method",
        "permissions_required": [("GET", "/api/v1/permissions")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword":  {"type": "string",  "description": "Từ khóa tìm theo tên permission hoặc api path"},
                "module":   {"type": "string",  "description": "Lọc theo module: 'JOB', 'COMPANY', 'PROFILE', 'SKILL', 'USER', 'ROLE', 'PERMISSION', 'RESUME', 'APPLICATION', 'NOTIFICATION'"},
                "method":   {"type": "string",  "description": "Lọc theo HTTP method: 'GET', 'POST', 'PUT', 'PATCH', 'DELETE'"},
                "pageSize": {"type": "integer", "description": "Số lượng kết quả (mặc định 100)"},
            },
            "required": []
        }
    },
    # ── Admin — Company actions ───────────────────────────────────────────────
    {
        "name": "verify_company",
        "description": "Admin xác minh công ty (đánh dấu isVerified = true). Sau khi xác minh, công ty sẽ hiển thị badge verified.",
        "permissions_required": [("PATCH", "/api/v1/companies/{id}/verify")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "ID của công ty cần xác minh"},
            },
            "required": ["company_id"]
        }
    },
    {
        "name": "delete_company",
        "description": "Admin xóa công ty khỏi hệ thống theo ID",
        "permissions_required": [("DELETE", "/api/v1/companies/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "ID của công ty cần xóa"},
            },
            "required": ["company_id"]
        }
    },
    # ── Admin — Customer actions ──────────────────────────────────────────────
    {
        "name": "delete_customer",
        "description": "Admin xóa hồ sơ customer (profile) theo ID",
        "permissions_required": [("DELETE", "/api/v1/customers/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "ID của customer cần xóa"},
            },
            "required": ["customer_id"]
        }
    },
    # ── Admin — Tất cả jobs (bao gồm DRAFT, CLOSED) ───────────────────────────
    {
        "name": "get_admin_jobs",
        "description": "Admin xem toàn bộ tin tuyển dụng trong hệ thống bao gồm mọi trạng thái (DRAFT, PUBLISHED, CLOSED) — không bị giới hạn như endpoint public",
        "permissions_required": [("GET", "/api/v1/admin/jobs")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword":   {"type": "string",  "description": "Từ khóa tìm kiếm tên tin tuyển dụng hoặc công ty"},
                "status":    {"type": "string",  "description": "Lọc theo trạng thái: 'DRAFT', 'PUBLISHED', hoặc 'CLOSED'"},
                "companyId": {"type": "string",  "description": "Lọc theo ID công ty"},
                "pageSize":  {"type": "integer", "description": "Số lượng kết quả (mặc định 20)"},
            },
            "required": []
        }
    },
    # ── Auth — Thông tin tài khoản ────────────────────────────────────────────
    {
        "name": "get_my_account",
        "description": "Lấy thông tin tài khoản đang đăng nhập (email, role, trạng thái tài khoản từ AuthService)",
        # Endpoint GET /api/v1/auth/account không cần permission đặc biệt (chỉ cần login)
        "permissions_required": [("GET", "/api/v1/jobs")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    # ── Admin — Role CRUD ─────────────────────────────────────────────────────
    {
        "name": "create_role",
        "description": "Admin tạo role mới trong hệ thống và gán danh sách permissions cho role đó",
        "permissions_required": [("POST", "/api/v1/roles")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "name":          {"type": "string", "description": "Tên role mới (ví dụ: 'MODERATOR', 'RECRUITER')"},
                "description":   {"type": "string", "description": "Mô tả chức năng của role"},
                "permissionIds": {"type": "array", "items": {"type": "string"}, "description": "Danh sách ID permissions gán cho role (dùng get_all_permissions để tra cứu)"},
            },
            "required": ["name"]
        }
    },
    {
        "name": "update_role",
        "description": "Admin cập nhật tên, mô tả hoặc danh sách permissions của một role theo ID",
        "permissions_required": [("PUT", "/api/v1/roles/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "role_id":       {"type": "string",  "description": "ID của role cần cập nhật"},
                "name":          {"type": "string",  "description": "Tên role mới"},
                "description":   {"type": "string",  "description": "Mô tả mới"},
                "isActive":      {"type": "boolean", "description": "Kích hoạt/vô hiệu hóa role (true/false)"},
                "permissionIds": {"type": "array", "items": {"type": "string"}, "description": "Danh sách ID permissions mới cho role"},
            },
            "required": ["role_id"]
        }
    },
    {
        "name": "delete_role",
        "description": "Admin xóa role theo ID. Lưu ý: không thể xóa role đang được gán cho user.",
        "permissions_required": [("DELETE", "/api/v1/roles/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "role_id": {"type": "string", "description": "ID của role cần xóa"},
            },
            "required": ["role_id"]
        }
    },
    # ── Admin — Permission CRUD ───────────────────────────────────────────────
    {
        "name": "create_permission",
        "description": "Admin tạo permission mới trong hệ thống (định nghĩa HTTP method + api path + module)",
        "permissions_required": [("POST", "/api/v1/permissions")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "name":     {"type": "string", "description": "Tên permission mô tả hành động (ví dụ: 'Xem danh sách việc làm')"},
                "api_path": {"type": "string", "description": "Đường dẫn API (ví dụ: '/api/v1/jobs')"},
                "method":   {"type": "string", "description": "HTTP method: 'GET', 'POST', 'PUT', 'PATCH', hoặc 'DELETE'"},
                "module":   {"type": "string", "description": "Module phân loại: 'JOB', 'COMPANY', 'PROFILE', 'SKILL', 'USER', 'ROLE', 'PERMISSION', 'RESUME', 'APPLICATION', 'NOTIFICATION'"},
            },
            "required": ["name", "api_path", "method", "module"]
        }
    },
    {
        "name": "update_permission",
        "description": "Admin cập nhật thông tin của một permission theo ID",
        "permissions_required": [("PUT", "/api/v1/permissions/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "permission_id": {"type": "string", "description": "ID của permission cần cập nhật"},
                "name":          {"type": "string", "description": "Tên mới của permission"},
                "api_path":      {"type": "string", "description": "Đường dẫn API mới"},
                "method":        {"type": "string", "description": "HTTP method mới: 'GET', 'POST', 'PUT', 'PATCH', 'DELETE'"},
                "module":        {"type": "string", "description": "Module phân loại mới"},
            },
            "required": ["permission_id"]
        }
    },
    {
        "name": "delete_permission",
        "description": "Admin xóa permission theo ID",
        "permissions_required": [("DELETE", "/api/v1/permissions/{id}")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {
                "permission_id": {"type": "string", "description": "ID của permission cần xóa"},
            },
            "required": ["permission_id"]
        }
    },
    # ── Import tools (Admin) — File upload qua Admin UI ───────────────────────
    {
        "name": "import_users",
        "description": "Hướng dẫn Admin import danh sách user từ file Excel/CSV. AI sẽ chỉ dẫn đến trang Admin UI để thực hiện upload file.",
        "permissions_required": [("POST", "/api/v1/users/import")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "import_skills",
        "description": "Hướng dẫn Admin import danh sách kỹ năng từ file Excel/CSV. AI sẽ chỉ dẫn đến trang Admin UI để thực hiện upload file.",
        "permissions_required": [("POST", "/api/v1/skills/import")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "import_companies",
        "description": "Hướng dẫn Admin import danh sách công ty từ file Excel/CSV. AI sẽ chỉ dẫn đến trang Admin UI để thực hiện upload file.",
        "permissions_required": [("POST", "/api/v1/companies/import")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "import_jobs",
        "description": "Hướng dẫn Admin import danh sách tin tuyển dụng từ file Excel/CSV. AI sẽ chỉ dẫn đến trang Admin UI để thực hiện upload file.",
        "permissions_required": [("POST", "/api/v1/admin/jobs/import")],
        "action_type": "read",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
]
