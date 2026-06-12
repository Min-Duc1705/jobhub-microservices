namespace NotificationService.Services.Helpers;

/// <summary>
/// Tiện ích xử lý địa chỉ/tỉnh thành (normalize, extract, so khớp).
/// Dùng chung cho HireAgent outreach filtering và bất kỳ service nào cần location matching.
/// </summary>
public static class LocationHelper
{
    private static readonly string[] _provinces =
    {
        "ho chi minh", "ha noi", "da nang", "can tho", "hai phong",
        "binh duong", "dong nai", "ba ria vung tau", "vung tau",
        "long an", "tien giang", "ben tre", "tra vinh", "vinh long",
        "dong thap", "an giang", "kien giang", "hau giang", "soc trang",
        "bac lieu", "ca mau", "tay ninh", "binh phuoc", "binh thuan",
        "ninh thuan", "khanh hoa", "nha trang", "phu yen", "binh dinh",
        "quang ngai", "quang nam", "hoi an", "thua thien hue", "hue",
        "quang tri", "quang binh", "ha tinh", "nghe an", "vinh",
        "thanh hoa", "ninh binh", "nam dinh", "thai binh", "ha nam",
        "hung yen", "hai duong", "bac ninh", "vinh phuc", "phu tho",
        "tuyen quang", "yen bai", "lao cai", "ha giang", "cao bang",
        "bac kan", "lang son", "thai nguyen", "bac giang", "quang ninh",
        "ha long", "dien bien", "lai chau", "son la", "hoa binh",
        "dak lak", "buon ma thuot", "dak nong", "gia lai", "pleiku",
        "kon tum", "lam dong", "da lat", "binh long", "thu duc",
    };

    /// <summary>
    /// Extract tên tỉnh/thành phố đầu tiên tìm thấy trong văn bản CV hoặc địa chỉ.
    /// </summary>
    public static string ExtractProvince(string text)
    {
        if (string.IsNullOrWhiteSpace(text)) return "";
        var normalized = Normalize(text);
        foreach (var province in _provinces)
            if (normalized.Contains(province))
                return province;
        return "";
    }

    /// <summary>
    /// So khớp địa điểm job với địa điểm ứng viên.
    /// Trả về true nếu khớp, hoặc nếu thiếu thông tin để chặn (fail-open).
    /// </summary>
    public static bool IsLocationMatch(string jobLocation, string candidateLocation)
    {
        if (string.IsNullOrWhiteSpace(jobLocation) || string.IsNullOrWhiteSpace(candidateLocation))
            return true;

        var jobNorm  = Normalize(jobLocation);
        var candNorm = Normalize(candidateLocation);
        return candNorm.Contains(jobNorm) || jobNorm.Contains(candNorm);
    }

    /// <summary>
    /// Normalize text: bỏ dấu tiếng Việt, lowercase, chuẩn hóa alias phổ biến.
    /// </summary>
    public static string Normalize(string text)
    {
        if (string.IsNullOrWhiteSpace(text)) return "";
        var s = text.ToLowerInvariant().Trim();

        // Bỏ dấu tiếng Việt
        s = s.Replace("à","a").Replace("á","a").Replace("ả","a").Replace("ã","a").Replace("ạ","a")
             .Replace("ă","a").Replace("ắ","a").Replace("ặ","a").Replace("ằ","a").Replace("ẵ","a").Replace("ẳ","a")
             .Replace("â","a").Replace("ấ","a").Replace("ầ","a").Replace("ẩ","a").Replace("ẫ","a").Replace("ậ","a")
             .Replace("đ","d")
             .Replace("è","e").Replace("é","e").Replace("ẻ","e").Replace("ẽ","e").Replace("ẹ","e")
             .Replace("ê","e").Replace("ế","e").Replace("ề","e").Replace("ể","e").Replace("ễ","e").Replace("ệ","e")
             .Replace("ì","i").Replace("í","i").Replace("ỉ","i").Replace("ĩ","i").Replace("ị","i")
             .Replace("ò","o").Replace("ó","o").Replace("ỏ","o").Replace("õ","o").Replace("ọ","o")
             .Replace("ô","o").Replace("ố","o").Replace("ồ","o").Replace("ổ","o").Replace("ỗ","o").Replace("ộ","o")
             .Replace("ơ","o").Replace("ớ","o").Replace("ờ","o").Replace("ở","o").Replace("ỡ","o").Replace("ợ","o")
             .Replace("ù","u").Replace("ú","u").Replace("ủ","u").Replace("ũ","u").Replace("ụ","u")
             .Replace("ư","u").Replace("ứ","u").Replace("ừ","u").Replace("ử","u").Replace("ữ","u").Replace("ự","u")
             .Replace("ỳ","y").Replace("ý","y").Replace("ỷ","y").Replace("ỹ","y").Replace("ỵ","y");

        // Chuẩn hóa alias
        s = s.Replace("tp. ho chi minh","ho chi minh").Replace("tp.ho chi minh","ho chi minh")
             .Replace("tp ho chi minh","ho chi minh").Replace("thanh pho ho chi minh","ho chi minh")
             .Replace("sai gon","ho chi minh").Replace("tphcm","ho chi minh").Replace("hcm","ho chi minh")
             .Replace("thu do ha noi","ha noi").Replace("thanh pho da nang","da nang")
             .Replace("bien hoa","dong nai").Replace("thu duc","ho chi minh");

        return s.Trim();
    }
}
