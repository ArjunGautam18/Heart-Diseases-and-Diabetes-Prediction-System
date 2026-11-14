import { API_BASE } from "../utils/api";
import { useState, useEffect, useRef } from "react";

function HealthCoachChat({ disease, riskLevel, inputData }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);
  const quickQuestions = disease === "heart"
    ? [
        "What does my heart risk level mean?",
        "What lifestyle changes can lower my heart risk?",
        "What heart symptoms need urgent care?",
      ]
    : [
        "What does my diabetes risk level mean?",
        "What foods can help manage blood sugar?",
        "What diabetes symptoms need urgent care?",
      ];

  const fetchAdvice = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/advice`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ disease, risk_level: riskLevel, data: inputData }),
      });
      const advice = await response.json();

      const dietText = advice.diet_recommendations?.length
        ? "🥗 Diet tips:\n" + advice.diet_recommendations.map((t) => `• ${t}`).join("\n")
        : "";
      const exerciseText = advice.exercise_recommendations?.length
        ? "🏃 Exercise tips:\n" + advice.exercise_recommendations.map((t) => `• ${t}`).join("\n")
        : "";

      setMessages([
        { from: "bot", text: `Based on your ${riskLevel.toLowerCase()} risk result, here's some guidance:` },
        { from: "bot", text: dietText },
        { from: "bot", text: exerciseText },
        { from: "bot", text: `ℹ️ ${advice.disclaimer}` },
        { from: "bot", text: "You can also ask me a question below — e.g. \"what snacks are okay?\"" },
      ]);
    } catch (err) {
      setMessages([{ from: "bot", text: "Sorry, I couldn't load recommendations right now." }]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (disease && riskLevel) {
      fetchAdvice();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [disease, riskLevel]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (question = chatInput) => {
    const text = question.trim();
    if (!text || sending) return;

    setMessages((prev) => [...prev, { from: "user", text }]);
    setChatInput("");
    setSending(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          message: text,
          disease,
          risk_level: riskLevel,
          data: inputData,
        }),
      });
      const result = await response.json();
      setMessages((prev) => [...prev, { from: "bot", text: result.reply }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { from: "bot", text: "Sorry, something went wrong sending that message." },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      className="chat-card"
      style={{
        marginTop: "1rem",
        border: "1px solid #e2e8f0",
        borderRadius: "10px",
        padding: "1rem",
        background: "#fafafa",
      }}
    >
      <h4 style={{ marginTop: 0 }}>💬 Health Coach</h4>

      <div className="coach-quick-questions">
        <span>Quick questions</span>
        <div>
          {quickQuestions.map((question) => (
            <button
              key={question}
              type="button"
              onClick={() => handleSend(question)}
              disabled={sending}
            >
              {question}
            </button>
          ))}
        </div>
      </div>

      <div style={{ maxHeight: "300px", overflowY: "auto", marginBottom: "0.75rem" }}>
        {loading && <p>Thinking...</p>}
        {messages.map(
          (m, i) =>
            m.text && (
              <div
                key={i}
                style={{
                  whiteSpace: "pre-line",
                  background: m.from === "bot" ? "#eef2ff" : "#dbeafe",
                  padding: "0.6rem 0.8rem",
                  borderRadius: "8px",
                  marginBottom: "0.5rem",
                  fontSize: "0.9rem",
                  marginLeft: m.from === "user" ? "20%" : 0,
                  marginRight: m.from === "bot" ? "20%" : 0,
                }}
              >
                {m.text}
              </div>
            )
        )}
        {sending && (
          <div style={{ fontSize: "0.85rem", color: "#666", fontStyle: "italic" }}>
            Health Coach is typing...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={{ display: "flex", gap: "0.5rem" }}>
        <input
          type="text"
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question, e.g. 'What snacks are okay?'"
          style={{
            flex: 1,
            padding: "0.5rem 0.75rem",
            borderRadius: "6px",
            border: "1px solid #cbd5e1",
          }}
          disabled={sending}
        />
        <button
          onClick={handleSend}
          disabled={sending || !chatInput.trim()}
          style={{
            padding: "0.5rem 1rem",
            borderRadius: "6px",
            border: "none",
            background: "#4f46e5",
            color: "white",
            cursor: sending ? "not-allowed" : "pointer",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default HealthCoachChat;