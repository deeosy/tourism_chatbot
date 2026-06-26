import { useState, useRef } from "react"
// lucide-react provides SVG icons as React components
import {
  Menu,
  X,
  Home,
  Compass,
  Heart,
  MessageCircle,
  ArrowRight,
  Castle,
  PartyPopper,
} from "lucide-react"

// Data for the top navigation bar items (desktop + mobile)
const navItems = [
  { id: "home", label: "Home", icon: Home },
  { id: "explore", label: "Compass", icon: Compass },
  { id: "favorites", label: "Hearts", icon: Heart },
]

// Data for the featured destination sections shown below the hero
const sections = [
  {
    id: "castles",
    title: "Cape Coast Castle",
    subtitle: "A profound journey into history",
    description:
      "Walk through the Door of No Return and stand where history shaped the modern world. Our guided tours bring centuries of stories to light.",
    image:
      "https://lh3.googleusercontent.com/pw/AP1GczPkz9gQ5x6y7R8aBcDeFgHiJkLmNoPqRsTuVwXyZa1234567890abcdefghijklmnopqrstuvwxyz",
    icon: Castle,
  },
  {
    id: "kakum",
    title: "Kakum National Park",
    subtitle: "Walk among the canopy",
    description:
      "Soar above the rainforest on Africa's only canopy walkway. Spot monkeys, butterflies, and birds in their natural habitat.",
    image:
      "https://lh3.googleusercontent.com/pw/AP1GczPkz9gQ5x6y7R8aBcDeFgHiJkLmNoPqRsTuVwXyZa1234567890abcdefghijklmnopqrstuvwxyz",
    icon: PartyPopper,
  },
]

// URL of the Python/Gradio backend streaming endpoint.
// The backend runs on localhost:7860 and exposes a function called "chat_fn".
const API_BASE = "http://127.0.0.1:7860/gradio_api/call/chat_fn"

// --- ChatWindow: the floating chat panel ---
// Receives an `onClose` callback so the parent (App) can hide it.
function ChatWindow({ onClose }) {
  // All messages displayed in the chat, each with a role ("user" | "bot") and text
  const [messages, setMessages] = useState([
    { role: "bot", text: "Akwaaba! Welcome to Ghana. How can I help plan your trip?" },
  ])
  // Current text in the input box
  const [input, setInput] = useState("")
  // True while waiting for a backend response
  const [loading, setLoading] = useState(false)

  // Ref instead of state so we can read the latest history inside closures
  // without triggering re-renders. Stores pairs of [userMessage, botReply].
  const chatHistoryRef = useRef([])
  // Reference to the active EventSource so we can close it if needed
  const eventSourceRef = useRef(null)

  // Sends the user's message to the Gradio backend and streams back the reply.
  const handleSend = async () => {
    // Ignore empty input or if we're already waiting for a response
    if (!input.trim() || loading) return

    const userMsg = input.trim()
    setInput("") // clear the input box immediately
    // Append the user's message visually
    setMessages((prev) => [...prev, { role: "user", text: userMsg }])
    setLoading(true)

    try {
      // Step 1 ― POST to the backend to start a prediction.
      // The payload is { data: [message, history] } (Gradio's standard format).
      const resp = await fetch(API_BASE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: [userMsg, chatHistoryRef.current] }),
      })
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)

      // The response contains an event_id we'll use to read the SSE stream
      const { event_id } = await resp.json()

      // Step 2 ― Open an SSE (Server-Sent Events) stream to receive the reply.
      eventSourceRef.current = new EventSource(`${API_BASE}/${event_id}`)

      // Listen for the "complete" event, which carries the final response.
      // The data is a JSON array: [responseText, additionalData]
      eventSourceRef.current.addEventListener("complete", (e) => {
        const data = JSON.parse(e.data)
        const reply = data[0] // first element is the chatbot's text reply
        // Save to conversation history so the backend gets context next time
        chatHistoryRef.current = [...chatHistoryRef.current, [userMsg, reply]]
        // Add the bot reply to the displayed messages
        setMessages((prev) => [...prev, { role: "bot", text: reply }])
        // Clean up the SSE connection
        eventSourceRef.current.close()
        setLoading(false)
      })

      // If the SSE connection fails, just stop loading
      eventSourceRef.current.onerror = () => {
        eventSourceRef.current.close()
        setLoading(false)
      }
    } catch {
      // Show a friendly error if the backend is unreachable
      setMessages((prev) => [...prev, {
        role: "bot",
        text: "Sorry, I'm having trouble connecting to the server. Please make sure the backend is running (python main.py) and try again.",
      }])
      setLoading(false)
    }
  }

  return (
    // Chat panel fixed to the bottom-right of the screen
    <div className="fixed bottom-24 right-6 z-50 w-80 sm:w-96 h-[32rem] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-outline-variant">
      {/* Header bar with title and close button */}
      <div className="bg-primary text-white px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
            <MessageCircle size={16} />
          </div>
          <div>
            <p className="font-semibold text-sm">Ghana Guide</p>
            <p className="text-xs text-white/70">Online</p>
          </div>
        </div>
        <button onClick={onClose} className="hover:bg-white/20 rounded-lg p-1.5 transition-colors">
          <X size={18} />
        </button>
      </div>

      {/* Scrollable message area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-surface">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-primary text-white rounded-br-md" // user bubbles: green, right-aligned
                  : "bg-white border border-outline-variant text-on-surface rounded-bl-md" // bot bubbles: white, left-aligned
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {/* Typing indicator (three bouncing dots) shown while loading */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-outline-variant text-on-surface rounded-2xl rounded-bl-md px-4 py-2.5">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-on-surface-variant rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 bg-on-surface-variant rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 bg-on-surface-variant rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input bar at the bottom */}
      <div className="border-t border-outline-variant p-3 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !loading && handleSend()}
            disabled={loading}
            placeholder="Ask about Ghana..."
            className="flex-1 px-4 py-2.5 rounded-xl border border-outline-variant text-sm bg-surface text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={loading}
            className="bg-primary text-white p-2.5 rounded-xl hover:bg-primary-variant transition-colors disabled:opacity-50"
          >
            <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}

// --- App: the root page component ---
function App() {
  // Which nav item is currently active ("home", "explore", "favorites")
  const [activeNav, setActiveNav] = useState("home")
  // Whether the floating chat window is visible
  const [isChatOpen, setIsChatOpen] = useState(false)
  // Whether the mobile hamburger menu is open
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-surface text-on-surface">
      {/* ===== Top Navigation Bar ===== */}
      <nav className="fixed top-0 left-0 right-0 z-40 bg-white/80 backdrop-blur-md border-b border-outline-variant">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-white font-bold text-sm">GH</span>
            </div>
            <span className="font-semibold text-lg text-on-surface">Ghana Guide</span>
          </div>

          {/* Desktop nav links (hidden on mobile) */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveNav(item.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeNav === item.id
                      ? "bg-primary/10 text-primary"
                      : "text-on-surface-variant hover:text-on-surface hover:bg-surface-alt"
                  }`}
                >
                  <Icon size={16} />
                  {item.label}
                </button>
              )
            })}
          </div>

          {/* Hamburger button (visible only on mobile) */}
          <button
            className="md:hidden p-2 rounded-lg hover:bg-surface-alt transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Mobile nav dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-outline-variant bg-white px-4 py-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveNav(item.id)
                    setMobileMenuOpen(false)
                  }}
                  className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    activeNav === item.id
                      ? "bg-primary/10 text-primary"
                      : "text-on-surface-variant hover:text-on-surface"
                  }`}
                >
                  <Icon size={16} />
                  {item.label}
                </button>
              )
            })}
          </div>
        )}
      </nav>

      {/* ===== Hero Section ===== */}
      <section className="relative pt-16">
        <div className="relative h-[70vh] min-h-[500px] overflow-hidden">
          <img
            src="https://lh3.googleusercontent.com/pw/AP1GczPkz9gQ5x6y7R8aBcDeFgHiJkLmNoPqRsTuVwXyZa1234567890abcdefghijklmnopqrstuvwxyz"
            alt="Ghana landscape"
            className="w-full h-full object-cover"
          />
          {/* Dark gradient overlay so text is readable */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />
          <div className="absolute bottom-0 left-0 right-0 p-6 sm:p-12 max-w-4xl mx-auto">
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-white mb-3 leading-tight">
              Discover Ghana
            </h1>
            <p className="text-lg sm:text-xl text-white/80 max-w-xl mb-6">
              From the castles of Cape Coast to the canopy of Kakum — let our AI guide plan your
              perfect journey.
            </p>
            <button
              onClick={() => setIsChatOpen(true)}
              className="inline-flex items-center gap-2 bg-secondary text-on-surface font-semibold px-6 py-3 rounded-xl hover:bg-secondary-variant transition-colors shadow-lg"
            >
              <MessageCircle size={18} />
              Plan Your Trip
            </button>
          </div>
        </div>
      </section>

      {/* ===== Featured Destination Sections ===== */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16 space-y-20">
        {sections.map((section) => {
          const Icon = section.icon
          return (
            <div key={section.id} className="flex flex-col md:flex-row gap-8 items-center">
              {/* Text content */}
              <div className="flex-1 space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                    <Icon size={20} className="text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-text-secondary uppercase tracking-wider">
                      {section.subtitle}
                    </p>
                    <h2 className="text-2xl sm:text-3xl font-bold text-on-surface">
                      {section.title}
                    </h2>
                  </div>
                </div>
                <p className="text-on-surface-variant leading-relaxed">{section.description}</p>
                <button className="inline-flex items-center gap-2 text-primary font-medium text-sm hover:underline">
                  Learn more <ArrowRight size={14} />
                </button>
              </div>
              {/* Image */}
              <div className="flex-1 w-full">
                <div className="rounded-2xl overflow-hidden shadow-lg">
                  <img
                    src={section.image}
                    alt={section.title}
                    className="w-full h-64 sm:h-80 object-cover"
                  />
                </div>
              </div>
            </div>
          )
        })}
      </section>

      {/* ===== Call-to-Action Section (dark background) ===== */}
      <section className="bg-inverse-surface text-inverse-on-surface py-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center space-y-6">
          <h2 className="text-3xl sm:text-4xl font-bold">Ready to explore Ghana?</h2>
          <p className="text-lg text-inverse-on-surface/70 max-w-xl mx-auto">
            Ask our AI guide anything — from the best jollof spots in Accra to planning a week-long
            itinerary through the Ashanti Region.
          </p>
          <button
            onClick={() => setIsChatOpen(true)}
            className="inline-flex items-center gap-2 bg-secondary text-on-surface font-semibold px-8 py-3.5 rounded-xl hover:bg-secondary-variant transition-colors shadow-lg text-lg"
          >
            <MessageCircle size={20} />
            Start Chatting
          </button>
        </div>
      </section>

      {/* ===== Footer ===== */}
      <footer className="border-t border-outline-variant py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center text-sm text-text-secondary">
          <p>© 2026 Ghana Tourism Guide. Built with care for travelers.</p>
        </div>
      </footer>

      {/* ===== Floating Chat Button (FAB) ===== */}
      <button
        onClick={() => setIsChatOpen(!isChatOpen)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-primary text-white shadow-xl hover:bg-primary-variant transition-all flex items-center justify-center"
      >
        {isChatOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>

      {/* ===== Chat Window (conditionally rendered) ===== */}
      {isChatOpen && <ChatWindow onClose={() => setIsChatOpen(false)} />}
    </div>
  )
}

export default App
