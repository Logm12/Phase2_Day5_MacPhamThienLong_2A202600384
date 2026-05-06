# Lab Guide: Multi-Agent Research System

## Scenario

Bạn cần xây dựng một research assistant có thể nhận câu hỏi dài, tìm thông tin, phân tích và viết câu trả lời cuối cùng. Lab yêu cầu so sánh hai cách làm:

1. **Single-agent baseline**: một agent làm toàn bộ.
2. **Multi-agent workflow**: Supervisor điều phối Researcher, Analyst, Writer.

## Quy tắc quan trọng

- Không thêm agent nếu không có lý do rõ ràng.
- Mỗi agent phải có responsibility riêng.
- Shared state phải đủ rõ để debug.
- Phải có trace hoặc log cho từng bước.
- Phải benchmark, không chỉ nhìn output bằng cảm tính.

## Milestone 1: Baseline

File gợi ý:

- `src/multi_agent_research_lab/cli.py`
- `src/multi_agent_research_lab/services/llm_client.py`

TODO(student): thay baseline placeholder bằng một call LLM thật.

## Milestone 2: Supervisor

File gợi ý:

- `src/multi_agent_research_lab/agents/supervisor.py`
- `src/multi_agent_research_lab/graph/workflow.py`

TODO(student): implement routing policy.

Gợi ý câu hỏi thiết kế:

- Khi nào gọi Researcher?
- Khi nào gọi Analyst?
- Khi nào gọi Writer?
- Khi nào stop?
- Nếu agent fail thì retry hay fallback?

## Milestone 3: Worker agents

File gợi ý:

- `agents/researcher.py`
- `agents/analyst.py`
- `agents/writer.py`

TODO(student): implement từng worker.

## Milestone 4: Trace và benchmark

File gợi ý:

- `observability/tracing.py`
- `evaluation/benchmark.py`
- `evaluation/report.py`

Benchmark tối thiểu:

| Metric | Cách đo gợi ý |
|---|---|
| Latency | wall-clock time |
| Cost | token usage hoặc provider usage |
| Quality | rubric 0-10 do peer review |
| Citation coverage | số claims có source / tổng claims chính |
| Failure rate | số query fail / tổng query |

## 4. Exit Ticket

### Câu hỏi 1: Trường hợp nào nên sử dụng Multi-Agent? Vì sao?
Nên sử dụng kiến trúc Multi-Agent đối với các tác vụ nghiên cứu khoa học chuyên sâu, phân tích dữ liệu phức tạp đòi hỏi tính toàn vẹn thông tin cao và yêu cầu trích dẫn bằng chứng nguồn thực tế xác thực (như phân tích tài chính, đối chiếu tài liệu y học, báo cáo nghiên cứu công nghệ mới).
- **Lý do kỹ thuật:** Kết quả Benchmark thực nghiệm chỉ ra điểm chất lượng báo cáo tăng từ **1.9/10** (Single-Agent) lên đến **4.8/10** (Multi-Agent). Việc cô lập vai trò của tác nhân Writer độc lập giúp triệt tiêu hiện tượng trôi ngữ cảnh (context drift), tập trung tối đa vào việc làm sâu luận điểm định lượng dựa trên thông tin thô được Researcher và Analyst xử lý chuyên biệt trước đó.

### Câu hỏi 2: Trường hợp nào không nên sử dụng Multi-Agent? Vì sao?
Không nên sử dụng kiến trúc Multi-agent cho các tác vụ đơn giản, yêu cầu phản hồi nhanh tức thì (real-time/low latency) hoặc có giới hạn ngân sách vận hành chặt chẽ (như chatbot hỏi đáp thông thường, tóm tắt bài viết ngắn, tìm kiếm thông tin nhanh).
- **Lý do kỹ thuật:** Số liệu đo lường thực tế chứng minh hệ thống Multi-Agent có thời gian xử lý tăng lên tới **62.30 giây** (gấp **2.28 lần** so với **27.36 giây** của Baseline) và tổng chi phí API phát sinh tăng lên **$0.003819** (gấp **4.90 lần** so với **$0.000779** của Baseline). Do đó, đối với các bài toán có tính thời gian thực cao, Single-agent gọn nhẹ mang lại hiệu quả kinh tế và tốc độ phản hồi tối ưu hơn vượt trội.
