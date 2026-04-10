# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** [Truong Minh SOn]
**Nhóm:** [F1-C401]
**Ngày:** [10/4/2026]

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> *Viết 1-2 câu:* Cosine similarity (trong đại số tuyến tính) được sử dụng để tính mức độ giống nhau giữa 2 vector.

**Ví dụ HIGH similarity:**
- Sentence A: "Tôi thích ăn phở vào buổi sáng."
- Sentence B: "Buổi sáng tôi rất thích ăn phở." 
- Tại sao tương đồng: Hai câu diễn đạt cùng một ý nghĩa, chỉ khác thứ tự từ nên vector embedding rất gần nhau.

**Ví dụ LOW similarity:**
- Sentence A: "Tôi thích ăn phở vào buổi sáng." 
- Sentence B: "Hôm nay trời mưa rất to." 
- Tại sao khác: Nội dung hai câu hoàn toàn khác nhau (một câu về sở thích ăn uống, một câu về thời tiết) nên vector embedding khác xa nhau

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> *Viết 1-2 câu:* Cosine similarity đo góc giữa các vector nên tập trung vào ý nghĩa (hướng) hơn là độ dài, giúp so sánh ngữ nghĩa tốt hơn trong khi Euclidean distance dễ bị ảnh hưởng bởi độ lớn vector.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* 
$$Step = 500 - 50 = 450$$ => 
>n = Total - overlap / chunk_size - overlap => n = 10000 - 50 / 500 - 50 = 22,11 => 23 chunks
> *Đáp án:* 23 chunks 

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
Tương tự: 10000 - 100/ 500 - 100 = 25 chunks 
> *Viết 1-2 câu:* Overlap nhiều giúp giảm nguy cơ mất ngữ cảnh tại điểm cắt giữa hai chunk (ví dụ: một câu quan trọng bị chia làm đôi), đảm bảo thông tin liên quan luôn xuất hiện cùng nhau trong ít nhất một chunk để vector search tìm kiếm chính xác hơn

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn


**Domain:** Luật lao động Việt Nam


**Tại sao nhóm chọn domain này?**
> Luật lao động Việt Nam là một lĩnh vực phức tạp với nhiều quy định khác nhau. Việc áp dụng RAG cho domain này sẽ giúp người dùng dễ dàng tra cứu thông tin và giải đáp các thắc mắc liên quan đến luật lao động.
### Data Inventory


| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 |Bộ luật lao động 2019 | https://datafiles.chinhphu.vn/cpp/files/vbpq/2019/12/45.signed.pdf | 193202 | Không có |


### Metadata Schema

| Trường metadata   | Kiểu   | Ví dụ giá trị                          | Tại sao hữu ích cho retrieval? |
|-------------------|--------|----------------------------------------|--------------------------------|
| document_name     | String | "Bộ luật Lao động 2019"               | Cho phép filter theo từng văn bản cụ thể, tránh nhiễu khi database chứa nhiều luật khác nhau. |
| chuong            | String | "Chương III HỢP ĐỒNG LAO ĐỘNG"        | Giúp thu hẹp phạm vi truy vấn theo nhóm chủ đề lớn, hỗ trợ pre-filtering theo ngữ cảnh. |
| muc               | String | "Mục 3 CHẤM DỨT HỢP ĐỒNG"             | Tổ chức nội dung ở mức chi tiết hơn chương, giúp tăng độ chính xác khi truy xuất các điều liên quan. |
| dieu              | String | "Điều 15", "Điều 34"                  | Hỗ trợ truy vấn chính xác bằng keyword (exact match) cho các câu hỏi tra cứu điều luật cụ thể. |
| tieu_de_dieu      | String | "Các trường hợp chấm dứt hợp đồng"    | Cung cấp tóm tắt ngữ nghĩa của nội dung, giúp cải thiện embedding và tăng độ chính xác khi tìm kiếm semantic. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:


| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Luật lao động Việt Nam | FixedSizeChunker (`fixed_size`) | 1074 | 199.87 | Không |
| Luật lao động Việt Nam | SentenceChunker (`by_sentences`) | 554 | 346.92 | Có |
| Luật lao động Việt Nam | RecursiveChunker (`recursive`) | 1652 | 115.27 | Có |


### Strategy Của Tôi

**Loại:** Loại: FixedSizeChunker (Parent–Child Strategy)

**Mô tả cách hoạt động:**
Strategy này chia tài liệu thành các parent chunks có kích thước cố định (1200 ký tự), sau đó mỗi parent chunk được chia tiếp thành child chunks nhỏ hơn (300 ký tự).

Các child chunks được đưa vào hệ thống embedding để thực hiện vector similarity search khi có truy vấn từ người dùng. Sau khi tìm được các child chunks liên quan nhất, hệ thống sẽ truy ngược về parent chunk tương ứng để lấy ngữ cảnh đầy đủ hơn.

Cách tiếp cận này giúp hệ thống tăng độ chính xác của retrieval vì embedding được thực hiện trên các đoạn nhỏ, nhưng khi cung cấp context cho mô hình LLM thì vẫn có đầy đủ thông tin ở mức đoạn lớn hơn.

**Tại sao tôi chọn strategy này cho domain nhóm?**
>Domain của nhóm là văn bản pháp luật (Bộ luật Lao động 2019). Các tài liệu pháp luật thường có cấu trúc dài, nhiều điều khoản và nội dung liên quan trải dài trong cùng một đoạn văn lớn.

Nếu chunk quá nhỏ, hệ thống có thể mất ngữ cảnh pháp lý quan trọng. Vì vậy, chiến lược parent–child chunking giúp giữ lại ngữ cảnh đầy đủ của điều luật, đồng thời vẫn cho phép tìm kiếm chính xác thông qua các child chunks nhỏ hơn.

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| | best baseline | Recursive|1652  |115.27 | 8.5/10|
| | **của tôi** |Parent–Child |892   |287.34 | 8.3/10|

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi |Parent–Child |892 | 287.34| 8.3/10|Trả lời câu hỏi, tìm chunks khá chính xác, (Top-1 thường chứa đáp án).| Test thêm queries, có queries bị lan man không đúng trọng tâm dù tìm đúng đoạn chunk đoạn thông tin cần trả lời, có case bị lost-track information. Top-K còn nhiều chunk không liên quan → context bị nhiễu
| [Mạc Phương Nga] |FixedSizeChunker |10  | Xử lý đơn giản, nhanh. Kiểm soát được lượng token đưa vào LLM |Phụ thuộc nhiều vào chunk_size và overlap, cần kiểm thử nhiều lần để tìm cặp thông số tối ưu |
| [Lại Gia Khánh] |Semantic Chunking | 8| Giữ nguyên đơn vị nghĩa (câu/điều), cải thiện độ chính xác truy vấn và khả năng trích dẫn nguồn; giảm nhiễu khi trả lời câu hỏi chuyên sâu.|  Phụ thuộc vào chất lượng embedding và ngưỡng similarity; cần tinh chỉnh threshold; tốn tài nguyên hơn và có thể tạo chunk kích thước không đồng đều. |
| Duy Anh | Custom Strategy (Regex Based Chunking) | 8.5 | Bảo toàn ngữ cảnh tốt | Khi điều luật quá dài, đoạn chunk sinh ra sẽ vượt qua giới hạn context window. Hao phí khi embedding. Sự thừa thãi khi truy xuất.  |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *Viết 2-3 câu:*Recursive chunking cho kết quả tốt hơn vì nó chia văn bản dựa trên ranh giới ngữ nghĩa tự nhiên như đoạn văn và câu, giúp mỗi chunk giữ được ý nghĩa hoàn chỉnh. Điều này giúp embedding biểu diễn nội dung chính xác hơn, nên vector search tìm được đoạn liên quan dễ dàng hơn. Ngược lại, Parent–Child chunking chia văn bản theo kích thước ký tự cố định, nên nhiều chunk có thể bị cắt giữa câu hoặc giữa điều luật. Vì vậy embedding chứa thông tin không đầy đủ hoặc bị nhiễu, dẫn đến chất lượng retrieval thấp hơn.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> *Viết 2-3 câu: dùng regex gì để detect sentence? Xử lý edge case nào?*
>SentenceChunker.chunk: Sử dụng Regex (?<=[.!?])\s+ để tách câu mà không làm mất dấu kết thúc. Giải quyết edge case các câu hỏi/cảm thán và đảm bảo mỗi chunk kết thúc trọn vẹn ở cuối câu.
**`RecursiveChunker.chunk` / `_split`** — approach:
> *Viết 2-3 câu: algorithm hoạt động thế nào? Base case là gì?*
>RecursiveChunker.chunk: Sử dụng thuật toán đệ quy tách văn bản theo thứ tự ưu tiên: Đoạn (\n\n) -> Dòng (\n) -> Câu (. ) -> Từ ( ). Base case là khi đoạn văn bản nhỏ hơn chunk_size, giúp giữ tối đa ngữ cảnh liền mạch.
### EmbeddingStore
=
**`add_documents` + `search`** — approach:
> *Viết 2-3 câu: lưu trữ thế nào? Tính similarity ra sao?*
>>add_documents + search: Lưu trữ dữ liệu dưới dạng danh sách Dictionary (ID, nội dung, vector). Tìm kiếm bằng cách tính sản phẩm vô hướng (dot product) giữa query và database, sau đó sắp xếp lấy top_k kết quả cao nhất.
**`search_with_filter` + `delete_document`** — approach:
*Viết 2-3 câu: filter trước hay sau? Delete bằng cách nào?*
>search_with_filter + delete_document: Thực hiện Pre-filtering (lọc metadata trước khi search) để tối ưu tốc độ. Xóa tài liệu bằng cách lọc danh sách và loại bỏ các bản ghi khớp với doc_id được cung cấp.
### KnowledgeBaseAgent

**`answer`** — approach:
> *Viết 2-3 câu: prompt structure? Cách inject context?*
>Prompt được cấu trúc gồm: Chỉ dẫn (System role) + Ngữ cảnh (Retrieved Context) + Câu hỏi. Context được inject trực tiếp vào prompt để LLM trả lời chính xác
### Test Results

```
# Paste output of: pytest tests/ -v
```============================================================================== 42 passed in 0.23s ===============================================================================

**Số tests pass:** 42/42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

## 5. Similarity Predictions — Cá nhân

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Bộ luật Lao động 2019 có hiệu lực từ ngày 01/01/2021. | Luật Lao động 2019 bắt đầu áp dụng từ ngày 1 tháng 1 năm 2021. | high | 0.92 | Yes |
| 2 | Người lao động được nghỉ 02 ngày dịp Quốc khánh. | Lao động được nghỉ lễ Quốc khánh 2 ngày và vẫn hưởng lương. | high | 0.88 | Yes |
| 3 | Thời gian thử việc tối đa là 180 ngày. | Người quản lý doanh nghiệp có thể thử việc tối đa 180 ngày. | high | 0.90 | Yes |
| 4 | Người lao động phải tuân thủ nội quy lao động. | Doanh nghiệp phải đảm bảo an toàn lao động. | low | 0.42 | Yes |
| 5 | Hợp đồng lao động có hai loại chính. | Người lao động được tham gia bảo hiểm xã hội. | low | 0.28 | Yes |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Kết quả bất ngờ nhất là cặp câu số 4 có điểm similarity trung bình dù nội dung không hoàn toàn giống nhau. Điều này cho thấy embeddings không chỉ dựa trên từ giống nhau mà còn dựa trên ngữ cảnh chung của chủ đề lao động. Embeddings có khả năng nắm bắt ý nghĩa tổng quát của câu thay vì chỉ so sánh từng từ riêng lẻ.
---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)
## Benchmark Queries

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Bộ luật Lao động năm 2019 chính thức có hiệu lực từ ngày nào? | 01 tháng 01 năm 2021 |
| 2 | Theo Bộ luật Lao động 2019, hợp đồng lao động có mấy loại chính? | 2 loại: hợp đồng lao động không xác định thời hạn và hợp đồng lao động xác định thời hạn |
| 3 | Không áp dụng thử việc với loại hợp đồng lao động nào? | Hợp đồng lao động có thời hạn dưới 01 tháng |
| 4 | Thời gian thử việc tối đa đối với người quản lý doanh nghiệp là bao nhiêu ngày? | Không quá 180 ngày |
| 5 | Dịp Quốc khánh 02/9 người lao động được nghỉ bao nhiêu ngày? | 02 ngày (02/9 và 01 ngày liền kề trước hoặc sau) |

---

## Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|---------------------------------|-------|-----------|------------------------|
| 1 | Hiệu lực của Bộ luật Lao động 2019 | Điều 20: Bộ luật có hiệu lực từ **01/01/2021** | 0.8355 | Yes | 01/01/2021 |
| 2 | Các loại hợp đồng lao động | Điều 20: Hợp đồng lao động gồm các loại khác nhau | 0.7895 | Yes | 2 loại: xác định thời hạn và không xác định thời hạn |
| 3 | Trường hợp không áp dụng thử việc | Nội dung về quy định lao động (chunk chứa phần liên quan thử việc) | ~0.78 | Yes (top-3) | Model trả lời chưa chính xác |
| 4 | Thời gian thử việc tối đa | Quy định thời gian thử việc tối đa | ~0.77 | Yes | 180 ngày |
| 5 | Nghỉ lễ Quốc khánh | Nội dung về lịch nghỉ lễ quốc khách (nhưng không nói rõ quy chế) | 0.76 | Yes | trả về kết quả đúng 2 ngày như dự đoán nhưng trích dẫn một số đoạn không liên quan |

---

### Đánh giá Retrieval

**Bao nhiêu queries trả về chunk relevant trong top-3?**

**4 / 5 queries** (tuy nhiên sau 3 lần test thử nhiều model và tinh chỉnh em đã hoàn thành được 5 queries (tuy trả về một số chunks khá là irrelevant em lưu file rag_answer.txt))

Giải thích:

- Q1: chunk chứa điều luật hiệu lực → relevant  
- Q2: chunk chứa điều luật về loại hợp đồng → relevant  
- Q3: chunk liên quan thử việc xuất hiện trong top-3 → relevant  
- Q4: chunk chứa quy định 180 ngày → relevant  
- Q5: Có case chạy bị quá quota (sau khi thử 3 lần (rag_answer.txt em có ghi lại log đầy đủ))

---

 ## 7. What I Learned

**Điều hay nhất em học được từ thành viên khác trong nhóm:**
> Em học được cách thiết kế pipeline RAG rõ ràng hơn, từ bước chunking, embedding cho đến retrieval và trả lời bằng LLM. Thành viên trong nhóm cũng giúp em hiểu tầm quan trọng của việc log Top-K retrieval để kiểm tra xem hệ thống có tìm đúng context hay không. Điều này giúp việc debug và cải thiện chất lượng trả lời dễ dàng hơn.

**Điều hay nhất Em học được từ nhóm khác (qua demo):**
> Em học được rằng việc chọn chiến lược chunking phù hợp với loại tài liệu là rất quan trọng. Một số nhóm sử dụng recursive chunking để giữ ranh giới ngữ nghĩa tốt hơn, giúp embedding biểu diễn nội dung chính xác hơn. 

**Nếu làm lại, Em sẽ thay đổi gì trong data strategy?**
> Nếu làm lại, Em sẽ thử tối ưu chiến lược chunking tốt hơn, ví dụ sử dụng recursive chunking thay vì fixed-size để tránh cắt giữa câu. EM cũng sẽ thử điều chỉnh kích thước chunk và giá trị top-k để giảm nhiễu trong context trả về. Ngoài ra, Em sẽ chuẩn bị dataset sạch và có cấu trúc rõ ràng hơn để giúp hệ thống retrieval chính xác hơn.
---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 8 / 10 |
| Chunking strategy | Nhóm | 12 / 15 |
| My approach | Cá nhân | 8.5 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 8 / 10 |
| Core implementation (tests) | Cá nhân | 25 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **75.5 / 90** |
