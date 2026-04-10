import re

def analyze_full_document_chunking():
    # Giả lập một đoạn văn bản luật dài gồm nhiều Điều
    full_legal_document = """
#### Điều 1. Phạm vi điều chỉnh
Bộ luật Lao động quy định tiêu chuẩn lao động; quyền, nghĩa vụ, trách nhiệm của người lao động...

#### Điều 2. Đối tượng áp dụng
1. Người lao động Việt Nam, người học nghề, tập nghề và người lao động khác...
2. Người sử dụng lao động.

#### Điều 3. Giải thích từ ngữ
1. Người lao động là người làm việc cho người sử dụng lao động...
Độ tuổi lao động tối thiểu của người lao động là đủ 15 tuổi...

#### Điều 4. Chính sách của Nhà nước về lao động
1. Bảo đảm quyền và lợi ích hợp pháp, chính đáng của người lao động...
2. Khuyến khích những thỏa thuận bảo đảm cho người lao động có những điều kiện thuận lợi hơn...
"""

    # --- LOGIC XỬ LÝ TOÀN BỘ (FULL CHUNKING) ---
    # 1. Tách thành các Parent (Mỗi Điều là 1 Parent)
    parent_articles = re.split(r'\n(?=####? Điều \d+\.)', full_legal_document.strip())
    
    total_child_chunks = 0
    total_parent_chars = 0
    total_child_chars = 0
    
    # Giả lập việc lưu trữ và đếm
    for article in parent_articles:
        total_parent_chars += len(article)
        
        # Tách nhỏ mỗi Điều thành các Child (Khoản/Dòng)
        children = [c.strip() for c in re.split(r'\n(?=-?\s?(?:\d+\.|[a-z]\)))', article) if c.strip()]
        total_child_chunks += len(children)
        total_child_chars += sum(len(c) for c in children)

    # --- TÍNH TOÁN CHỈ SỐ ---
    num_parents = len(parent_articles)
    avg_parent_len = total_parent_chars // num_parents
    avg_child_len = total_child_chars // total_child_chunks

    # --- IN KẾT QUẢ ---
    print("\n" + "="*85)
    print(f"{'Tài liệu':<20} | {'Strategy':<15} | {'Chunk Count':<12} | {'Avg Length':<12} | {'Preserves Context?'}")
    print("-" * 85)
    
    # Kết quả cho Child (Hệ thống tìm kiếm)
    print(f"{'luat_lao_dong.md':<20} | {'Small (Child)':<15} | {total_child_chunks:<12} | {avg_child_len:<12} | No (Granular Search)")
    
    # Kết quả cho Parent (Hệ thống trả lời)
    print(f"{'luat_lao_dong.md':<20} | {'Big (Parent)':<15} | {num_parents:<12} | {avg_parent_len:<12} | Yes (Full Article Context)")
    print("="*85)

    print(f"\n[PHÂN TÍCH TỔNG THỂ]")
    print(f"- Hệ thống đã tự động nhận diện {num_parents} Điều luật khác nhau.")
    print(f"- Từ {num_parents} Điều này, hệ thống tạo ra {total_child_chunks} 'điểm tìm kiếm' nhỏ.")
    print(f"- Khi bạn hỏi, AI sẽ tìm trong {total_child_chunks} điểm này nhưng luôn trả về 1 trong {num_parents} nội dung gốc.")

if __name__ == "__main__":
    analyze_full_document_chunking()
    