import { useState, useRef } from "react"
import { useAuth } from "./auth/AuthContext"
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
  LogOut,
} from "lucide-react"
import heroImage1 from "../src/asset/modern_architectural_photography_of_the_black_star_gate_in_accra_ghana.jpg"
import capeCoastCastle from "../src/asset/cape_coast_castle.jpg"
import kakumNationalPark from "../src/asset/kakum_national_park.jpg"
import ghanaGuideFavicon from "../src/asset/GhanaGuideFavicon.jpg"

const navItems = [
  { id: "home", label: "Home", icon: Home },
  { id: "explore", label: "Compass", icon: Compass },
  { id: "favorites", label: "Hearts", icon: Heart },
]

const sections = [
  {
    id: "castles",
    title: "Cape Coast Castle",
    subtitle: "A profound journey into history",
    description:
      "Walk through the Door of No Return and stand where history shaped the modern world. Our guided tours bring centuries of stories to light.",
    image: capeCoastCastle,
    icon: Castle,
  },
  {
    id: "kakum",
    title: "Kakum National Park",
    subtitle: "Walk among the canopy",
    description:
      "Soar above the rainforest on Africa's only canopy walkway. Spot monkeys, butterflies, and birds in their natural habitat.",
    image: kakumNationalPark,
    icon: PartyPopper,
  },
]

// Backend URL for the chat API (FastAPI, not Gradio anymore)
const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:7860"

// --- ChatWindow ---
// The floating chat panel. Sends messages via POST /api/chat with JWT auth.
function ChatWindow({ onClose }) {
  const { token } = useAuth()

  const [messages, setMessages] = useState([
    { role: "bot", text: "Akwaaba! Welcome to Ghana. How can I help plan your trip?" },
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const chatHistoryRef = useRef([])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMsg = input.trim()
    setInput("")
    setMessages((prev) => [...prev, { role: "user", text: userMsg }])
    setLoading(true)

    try {
      const resp = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: userMsg,
          history: chatHistoryRef.current,
        }),
      })

      if (!resp.ok) {
        if (resp.status === 401) {
          throw new Error("Session expired. Please log in again.")
        }
        throw new Error(`HTTP ${resp.status}`)
      }

      const data = await resp.json()
      chatHistoryRef.current = [...chatHistoryRef.current, [userMsg, data.reply]]
      setMessages((prev) => [...prev, { role: "bot", text: data.reply }])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: err.message.includes("Session expired")
            ? err.message
            : "Sorry, I'm having trouble connecting to the server. Please try again.",
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed bottom-24 right-6 z-50 w-80 sm:w-96 h-[32rem] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-outline-variant">
      {/* Header */}
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

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-surface">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-primary text-white rounded-br-md"
                  : "bg-white border border-outline-variant text-on-surface rounded-bl-md"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
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

      {/* Input */}
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
  const { user, logout } = useAuth()
  const [activeNav, setActiveNav] = useState("home")
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-surface text-on-surface">
      {/* ===== Top Navigation Bar ===== */}
      <nav className="fixed top-0 left-0 right-0 z-40 bg-white/80 backdrop-blur-md border-b border-outline-variant">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-16 h-16 rounded-full bg-primary flex items-center justify-center">
              <img src={ghanaGuideFavicon} alt="Ghana Guide Logo" className="w-full h-full object-cover rounded-lg" />
            </div>
            <div>
              <span className="font-semibold text-3xl text-on-surface">
                Ghana <span className="font-semibold text-green-800">Guide</span>
              </span>
              <div className="flex justify-between items-center">
                <span className="text-[8px] text-red-800">—</span>
                <span className="text-[8px] text-green-800">EXPLORE. DISCOVER. EXPERIENCE GHANA</span>
                <span className="text-[8px] text-green-800">—</span>
              </div>
            </div>
          </div>

          {/* Desktop nav + user menu */}
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

            {/* User info + logout */}
            <div className="ml-3 pl-3 border-l border-outline-variant flex items-center gap-3">
              <span className="text-sm text-on-surface-variant">
                {user?.name || user?.email}
              </span>
              <button
                onClick={logout}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
              >
                <LogOut size={14} />
                Logout
              </button>
            </div>
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden p-2 rounded-lg hover:bg-surface-alt transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Mobile dropdown */}
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
            {/* Mobile logout */}
            <button
              onClick={() => {
                setMobileMenuOpen(false)
                logout()
              }}
              className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
            >
              <LogOut size={16} />
              Logout ({user?.name || user?.email})
            </button>
          </div>
        )}
      </nav>

      {/* ===== Hero Section ===== */}
      <section className="relative pt-16">
        <div className="relative h-[70vh] min-h-[500px] overflow-hidden">
          <img
            src={heroImage1}
            alt="Ghana landscape"
            className="w-full h-full object-cover"
          />
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

      {/* ===== Featured Sections ===== */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16 space-y-20">
        {sections.map((section) => {
          const Icon = section.icon
          return (
            <div key={section.id} className="flex flex-col md:flex-row gap-8 items-center">
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

      {/* ===== CTA Section ===== */}
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
          <p>&copy; 2026 Ghana Tourism Guide. Built with care for travelers.</p>
        </div>
      </footer>

      {/* ===== Floating Chat Button ===== */}
      <button
        onClick={() => setIsChatOpen(!isChatOpen)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-primary text-white shadow-xl hover:bg-primary-variant transition-all flex items-center justify-center"
      >
        {isChatOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>

      {/* ===== Chat Window ===== */}
      {isChatOpen && <ChatWindow onClose={() => setIsChatOpen(false)} />}
    </div>
  )
}

export default App
