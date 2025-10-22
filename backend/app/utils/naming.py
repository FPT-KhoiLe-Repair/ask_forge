import re

def format_index_name(raw_name: str, prefix: str = "askforge_") -> str:
    """
    Chuẩn hóa index_name từ user để phù hợp với quy tắc của ChromaDB.

    - Loại bỏ ký tự đặc biệt, chỉ giữ [a-zA-Z0-9._-]
    - Thay khoảng trắng bằng "_"
    - Đảm bảo bắt đầu & kết thúc bằng ký tự hợp lệ
    - Thêm prefix nếu chưa có

    Args:
        raw_name (str): tên index gốc từ người dùng
        prefix (str): tiền tố hệ thống (mặc định là "askforge_")

    Returns:
        str: Tên hợp lệ theo chuẩn ChromaDB
    """
    if not raw_name:
        raise ValueError("Index name cannot be empty")

    # Bỏ khoảng trắng đầu/cuối và chuyển lowercase
    name = raw_name.strip().lower()

    # Thay khoảng trắng hoặc chuỗi liên tiếp bằng "_"
    name = re.sub(r"\s+", "_", name)

    # Loại bỏ ký tự không hợp lệ
    name = re.sub(r"[^a-zA-Z0-9._-]", "", name)

    # Đảm bảo không bắt đầu/kết thúc bằng ký tự không hợp lệ
    name = re.sub(r"^[^a-zA-Z0-9]+", "", name)
    name = re.sub(r"[^a-zA-Z0-9]+$", "", name)

    # Nếu tên quá ngắn thì thêm fallback
    if len(name) < 3:
        name = f"idx_{name or 'default'}"

    # Gắn prefix nếu chưa có
    if not name.startswith(prefix):
        name = prefix + name

    return name