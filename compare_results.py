from src.chunking import ChunkingStrategyComparator

# Đọc nội dung file luật
with open("luat_lao_dong.md", "r", encoding="utf-8") as f:
    text = f.read()

# Chạy bộ so sánh
comparator = ChunkingStrategyComparator()
results = comparator.compare(text, chunk_size=200)

# In kết quả ra để điền vào bảng
for strategy, stats in results.items():
    print(f"Strategy: {strategy}")
    print(f" - Chunk Count: {stats['count']}")
    print(f" - Avg Length: {stats['avg_length']:.2f}")