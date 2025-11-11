from src.core.memory import MemoryManager

memory = MemoryManager()

memory.save_memory(
    user_id="user_123",
    session_id="session_abc",
    question="Tôi tên là Trung và tôi thích lập trình.",
    answer="Cảm ơn bạn đã chia sẻ, Trung!"
)

memory.save_memory(
    user_id="user_123",
    session_id="session_abc",
    question="Trí tuệ nhân tạo là gì?",
    answer="Trí tuệ nhân tạo là một lĩnh vực của khoa học máy tính tập trung vào việc tạo ra các hệ thống có khả năng thực hiện các tác vụ mà thường cần đến trí tuệ con người."
)

memory.save_memory(
    user_id="user_123",
    session_id="session_abc",
    question="Tôi vừa mới học lập trình Python.",
    answer="Thật tuyệt vời! Python là một ngôn ngữ lập trình rất mạnh mẽ và dễ học."
)

memory.save_memory(
    user_id="user_123",
    session_id="session_abc",
    question="Tôi làm thế nào để cải thiện kỹ năng lập trình của mình?",
    answer="Bạn có thể cải thiện kỹ năng lập trình bằng cách thực hành thường xuyên, tham gia các dự án mã nguồn mở, đọc tài liệu và sách về lập trình, và học hỏi từ cộng đồng lập trình viên."
)

memory.save_memory(
    user_id="user_123",
    session_id="session_abc",
    question="Tôi cần giúp đỡ về một dự án lập trình.",
    answer="Chắc chắn rồi! Hãy cho tôi biết chi tiết về dự án của bạn và những khó khăn bạn đang gặp phải."
)

memories = memory.get_memory(
    user_id="user_123",
    session_id="session_abc",
    top_k=5)

print("=== Retrieved Memories ===")
for idx, mem in enumerate(memories, 1):
    print(f"{idx}. Q: {mem['question']}\n   A: {mem['answer']}\n")

conversation = memory.get_memory_as_conversation(
    user_id="user_123",
    session_id="session_abc",
    top_k=5
)

print("=== Conversation Format ===")
print(conversation)
# agent = AgentWithMCP(tools, "You are a helpful assistant.")


