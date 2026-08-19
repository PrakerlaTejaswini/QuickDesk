import React, {
  useEffect,
  useState
} from "react";

import {
  createRoot
} from "react-dom/client";

import "./style.css";


const API = "http://127.0.0.1:8000";


type User = {
  id: number;
  name: string;  email: string;
  role: "employee" | "agent";
};


type Ticket = {
  id: number;
  employee_id: number;
  employee_name: string;

  title: string;
  description: string;

  category: string;
  priority: string;

  ai_category: string;
  ai_priority: string;

  ai_draft: string | null;
  final_reply: string | null;

  citations: string[];

  status: string;

  created_at: string;
  resolved_at: string | null;
};


function App() {

  const [token, setToken] =
    useState(
      localStorage.getItem("token")
    );

  const [user, setUser] =
    useState<User | null>(
      JSON.parse(
        localStorage.getItem("user") || "null"
      )
    );

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [tickets, setTickets] =
    useState<Ticket[]>([]);

  const [title, setTitle] =
    useState("");

  const [description, setDescription] =
    useState("");

  const [selectedTicket, setSelectedTicket] =
    useState<Ticket | null>(null);

  const [draft, setDraft] =
    useState("");

  const [message, setMessage] =
    useState("");


  async function login() {
  try {
    const response = await fetch(
      `${API}/api/login`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      }
    );

    const data = await response.json();

    console.log("LOGIN STATUS:", response.status);
    console.log("LOGIN RESPONSE:", data);

    if (!response.ok) {
      setMessage(data.detail || "Invalid email or password");
      return;
    }

    localStorage.setItem(
      "token",
      data.access_token
    );

    localStorage.setItem(
      "user",
      JSON.stringify(data.user)
    );

    setToken(data.access_token);
    setUser(data.user);

  } catch (error) {
    console.error("LOGIN ERROR:", error);
    setMessage("Cannot connect to backend");
  }
}


  async function loadTickets() {

    if (!token || !user)
      return;

    const endpoint =
      user.role === "agent"
        ? "/api/tickets"
        : "/api/my-tickets";

    const response = await fetch(
      `${API}${endpoint}`,
      {
        headers: {
          Authorization:
            `Bearer ${token}`
        }
      }
    );

    if (response.ok) {

      setTickets(
        await response.json()
      );
    }
  }


  async function createTicket() {

    const response = await fetch(
      `${API}/api/tickets`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          Authorization:
            `Bearer ${token}`
        },

        body: JSON.stringify({
          title,
          description
        })
      }
    );

    if (response.ok) {

      setTitle("");

      setDescription("");

      setMessage(
        "Ticket created successfully"
      );

      loadTickets();
    }
  }


  async function generateDraft(
    ticket: Ticket
  ) {

    const response = await fetch(
      `${API}/api/tickets/${ticket.id}/draft`,
      {
        method: "POST",

        headers: {
          Authorization:
            `Bearer ${token}`
        }
      }
    );

    const data =
      await response.json();

    setDraft(data.draft);

    setSelectedTicket({
      ...ticket,
      ai_draft: data.draft,
      citations: data.citations
    });
  }


  async function sendReply() {

    if (!selectedTicket)
      return;

    const response = await fetch(
      `${API}/api/tickets/${selectedTicket.id}/reply`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          Authorization:
            `Bearer ${token}`
        },

        body: JSON.stringify({
          reply: draft
        })
      }
    );

    if (response.ok) {

      setMessage(
        "Reply sent. Ticket resolved."
      );

      setSelectedTicket(null);

      loadTickets();
    }
  }


  function logout() {

    localStorage.clear();

    setToken(null);

    setUser(null);

    setTickets([]);
  }


  useEffect(() => {

    if (!token)
      return;

    loadTickets();

    const socket =
      new WebSocket(
        "ws://localhost:8000/ws"
      );

    socket.onmessage = () => {

      loadTickets();
    };

    return () => {

      socket.close();
    };

  }, [token]);


  if (!token || !user) {

    return (
      <div className="login">

        <div className="card">

          <h1>QuickDesk</h1>

          <p>
            AI-Assisted Helpdesk
          </p>

          <input
            placeholder="Email"
            value={email}
            onChange={
              e => setEmail(e.target.value)
            }
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={
              e => setPassword(e.target.value)
            }
          />

          <button
            onClick={login}
          >
            Login
          </button>

          <p>
            Demo Agent:
            agent@quickdesk.local
            / agent123
          </p>

          <p>
            Demo Employee:
            employee@quickdesk.local
            / employee123
          </p>

          <small>
            {message}
          </small>

        </div>

      </div>
    );
  }


  return (
    <div className="app">

      <header>

        <div>
          <h1>QuickDesk</h1>

          <span>
            {user.role}
          </span>
        </div>

        <button
          onClick={logout}
        >
          Logout
        </button>

      </header>


      <main>

        {user.role === "employee" && (

          <section className="card">

            <h2>
              Create Ticket
            </h2>

            <input
              placeholder="Ticket title"
              value={title}
              onChange={
                e => setTitle(e.target.value)
              }
            />

            <textarea
              placeholder="Describe your problem"
              value={description}
              onChange={
                e =>
                  setDescription(
                    e.target.value
                  )
              }
            />

            <button
              onClick={createTicket}
            >
              Submit Ticket
            </button>

          </section>

        )}


        <section>

          <h2>
            {user.role === "agent"
              ? "All Tickets"
              : "My Tickets"}
          </h2>

          {tickets.map(ticket => (

            <div
              className="ticket"
              key={ticket.id}
              onClick={() =>
                user.role === "agent"
                  && setSelectedTicket(ticket)
              }
            >

              <div>

                <h3>
                  #{ticket.id}{" "}
                  {ticket.title}
                </h3>

                <p>
                  {ticket.description}
                </p>

              </div>

              <div>

                <span>
                  {ticket.category}
                </span>

                <span>
                  {ticket.priority}
                </span>

                <strong>
                  {ticket.status}
                </strong>

              </div>

            </div>

          ))}

        </section>


        {selectedTicket && (

          <section className="card">

            <h2>
              Ticket #
              {selectedTicket.id}
            </h2>

            <h3>
              {selectedTicket.title}
            </h3>

            <p>
              {selectedTicket.description}
            </p>

            <p>
              Employee:
              {" "}
              {selectedTicket.employee_name}
            </p>

            <p>
              AI Category:
              {" "}
              {selectedTicket.ai_category}
            </p>

            <p>
              AI Priority:
              {" "}
              {selectedTicket.ai_priority}
            </p>


            <button
              onClick={() =>
                generateDraft(
                  selectedTicket
                )
              }
            >
              Generate AI Draft
            </button>


            <textarea
              value={draft}
              onChange={
                e =>
                  setDraft(
                    e.target.value
                  )
              }
              placeholder="AI draft will appear here"
            />


            <p>
              Citations:
              {" "}
              {selectedTicket.citations.join(
                ", "
              )}
            </p>


            <button
              onClick={sendReply}
            >
              Send Reply & Resolve
            </button>

          </section>

        )}

        <p>
          {message}
        </p>

      </main>

    </div>
  );
}


createRoot(
  document.getElementById("root")!
).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);