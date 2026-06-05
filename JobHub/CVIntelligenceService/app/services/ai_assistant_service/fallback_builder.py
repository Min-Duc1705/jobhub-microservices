# app/services/ai_assistant_service/fallback_builder.py
"""
Xây dựng fallback text từ actions_taken khi Gemini không trả về response hợp lệ.
"""
import logging

logger = logging.getLogger(__name__)


def build_fallback_message(actions_taken: list) -> str:
    """
    Tạo fallback text từ dữ liệu của các actions đã thực hiện.
    Trả về chuỗi rỗng nếu không có dữ liệu phù hợp.
    """
    for action in actions_taken:
        tool_name = action.tool_name
        data = action.data
        if not data:
            continue

        if tool_name in ["search_jobs", "get_my_jobs"]:
            jobs = data.get("jobs", []) if isinstance(data, dict) else []
            if not jobs and isinstance(data, list):
                jobs = data
            if jobs:
                job_lines = []
                for j in jobs[:5]:
                    salary_str = ""
                    if j.get("salaryMin") or j.get("salaryMax"):
                        min_sal = j.get("salaryMin")
                        max_sal = j.get("salaryMax")
                        curr = j.get("salaryCurrency", "VND")
                        if min_sal and max_sal:
                            salary_str = f" ({min_sal}-{max_sal} {curr})"
                        elif min_sal:
                            salary_str = f" (Từ {min_sal} {curr})"
                        elif max_sal:
                            salary_str = f" (Lên đến {max_sal} {curr})"
                    company = j.get("companyName") or "Chưa rõ công ty"
                    loc = j.get("location") or "Toàn quốc"
                    job_lines.append(f"- **{j.get('name')}** tại *{company}* - {loc}{salary_str}")

                msg = "Tôi đã tìm kiếm cơ sở dữ liệu và dưới đây là một số tin tuyển dụng phù hợp:\n\n" + "\n".join(job_lines)
                if len(jobs) > 5:
                    msg += f"\n\n*(Và {len(jobs) - 5} công việc khác. Hãy hỏi tôi chi tiết nếu cần!)*"
                return msg

        elif tool_name == "get_job_detail":
            job = data.get("job") if isinstance(data, dict) else data
            if isinstance(job, dict) and job.get("name"):
                name = job.get("name")
                desc = job.get("description", "Không có mô tả")[:200]
                reqs = job.get("requirements", "Không có yêu cầu")[:200]
                comp = job.get("companyName") or "Chưa rõ công ty"
                loc = job.get("location") or "Toàn quốc"
                return (
                    f"Dưới đây là chi tiết công việc **{name}** tại **{comp}**:\n"
                    f"- **Địa điểm:** {loc}\n"
                    f"- **Mô tả ngắn:** {desc}...\n"
                    f"- **Yêu cầu:** {reqs}...\n\n"
                    f"*(Nếu bạn muốn ứng tuyển hoặc xem đầy đủ hơn, vui lòng báo cho tôi!)*"
                )

        elif tool_name == "predict_salary":
            pred = data
            if isinstance(pred, dict) and (pred.get("predictedSalary") or pred.get("salary_range")):
                sal = pred.get("predictedSalary") or pred.get("predicted_salary")
                sal_range = (
                    pred.get("salary_range") or
                    (f"{pred.get('minSalary')}-{pred.get('maxSalary')}" if pred.get('minSalary') else "")
                )
                title = pred.get("jobTitle") or "vị trí yêu cầu"
                msg = (
                    f"Kết quả phân tích mức lương cho **{title}**:\n"
                    f"- Mức lương dự đoán trung bình: **{sal:,} VND**\n"
                )
                if sal_range:
                    msg += f"- Dải lương phổ biến: **{sal_range}**\n"
                return msg

        elif tool_name == "search_candidates":
            cands = data.get("candidates", []) if isinstance(data, dict) else []
            if not cands and isinstance(data, list):
                cands = data
            if cands:
                cand_lines = []
                for c in cands[:5]:
                    name = c.get("fullName") or c.get("name") or "Ẩn danh"
                    pos = c.get("position") or "Chưa cập nhật vị trí"
                    exp = c.get("yearsOfExperience", 0)
                    cand_lines.append(f"- **{name}** - {pos} ({exp} năm kinh nghiệm)")
                return "Tôi tìm thấy một số ứng viên phù hợp với tiêu chí của bạn:\n\n" + "\n".join(cand_lines)

        elif tool_name == "get_my_company_info":
            comp = data.get("company") if isinstance(data, dict) else data
            if isinstance(comp, dict) and comp.get("name"):
                return (
                    f"Thông tin công ty của bạn:\n"
                    f"- **Tên công ty:** {comp.get('name')}\n"
                    f"- **Ngành nghề:** {comp.get('industry', 'Chưa cập nhật')}\n"
                    f"- **Quy mô:** {comp.get('size', 'Chưa cập nhật')} nhân sự\n"
                    f"- **Địa chỉ:** {comp.get('address', 'Chưa cập nhật')}"
                )

        elif tool_name == "search_companies":
            comps = data.get("companies", []) if isinstance(data, dict) else []
            if not comps and isinstance(data, list):
                comps = data
            if comps:
                comp_lines = []
                for c in comps[:5]:
                    name = c.get("name")
                    ind = c.get("industry") or "Chưa rõ ngành"
                    addr = c.get("address") or "Chưa cập nhật"
                    comp_lines.append(f"- **{name}** ({ind}) - *{addr}*")
                return "Tôi tìm thấy một số công ty phù hợp với tìm kiếm của bạn:\n\n" + "\n".join(comp_lines)

        elif tool_name == "get_my_resumes":
            resumes = data.get("result", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            if resumes:
                res_lines = []
                for r in resumes[:5]:
                    name = r.get("title") or r.get("name") or "CV không tên"
                    is_def = " (Mặc định)" if r.get("isDefault") else ""
                    res_lines.append(f"- **{name}**{is_def}")
                return "Danh sách các CV của bạn:\n\n" + "\n".join(res_lines)

        elif tool_name == "get_my_applications":
            apps = data.get("result", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            if apps:
                app_lines = []
                for a in apps[:5]:
                    j_name = a.get("jobName") or "Công việc không tên"
                    status = a.get("status") or "Đang chờ duyệt"
                    app_lines.append(f"- **{j_name}** - Trạng thái: *{status}*")
                return "Danh sách các đơn ứng tuyển của bạn:\n\n" + "\n".join(app_lines)

    return ""
