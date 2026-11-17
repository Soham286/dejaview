import { useEffect, useRef, useState } from "react";
import "./app.css";

const EXAMPLES = [
  "blue hedgehog runs fast",
  "woman stalked by her invisible ex",
  "doctor who talks to animals",
  "miami detectives hunt a cartel",
];

function useSearch(query) {
  const [state, setState] = useState({ status: "idle", data: null });
  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setState({ status: "idle", data: null });
      return;
    }
    const ctrl = new AbortController();
    // wait for a pause in typing; the cleanup cancels both the wait and any request in flight
    const timer = setTimeout(async () => {
      setState((s) => ({ ...s, status: "loading" }));
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&k=12`, { signal: ctrl.signal });
        if (!res.ok) throw new Error(res.status);
        setState({ status: "done", data: await res.json() });
      } catch (e) {
        if (e.name !== "AbortError") setState({ status: "error", data: null });
      }
    }, 200);
    return () => {
      clearTimeout(timer);
      ctrl.abort();
    };
  }, [query]);
  return state;
}

// shortcut: approximates the server's plural stripping; have the API return match offsets if they drift apart
const norm = (word) => word.toLowerCase().replace(/(es|s)$/, "");

function Highlight({ text, query }) {
  const terms = new Set(query.split(/\W+/).filter((w) => w.length > 2).map(norm));
  return text.split(/(\w+)/).map((part, i) => (terms.has(norm(part)) ? <mark key={i}>{part}</mark> : part));
}

const hue = (text) => [...text].reduce((h, c) => (h * 31 + c.charCodeAt(0)) % 360, 7);

// feeds the cursor position to the card's CSS so its glow follows the mouse
function spotlight(e) {
  const r = e.currentTarget.getBoundingClientRect();
  e.currentTarget.style.setProperty("--x", `${e.clientX - r.left}px`);
  e.currentTarget.style.setProperty("--y", `${e.clientY - r.top}px`);
}

function Poster({ title, year }) {
  const h = hue(title);
  const background = `linear-gradient(140deg, hsl(${h} 55% 34%), hsl(${(h + 50) % 360} 65% 14%))`;
  return (
    <div className="poster" style={{ background }} aria-hidden="true">
      <span className="poster-initial">{title[0]}</span>
      <span className="poster-year">{year ?? ""}</span>
    </div>
  );
}

function FilmDialog({ id, onClose }) {
  const ref = useRef(null);
  const [film, setFilm] = useState(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    ref.current.showModal();
    let live = true;
    fetch(`/api/film/${id}`)
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((f) => live && setFilm(f))
      .catch(() => live && setFailed(true));
    return () => {
      live = false;
    };
  }, [id]);
  return (
    <dialog ref={ref} onClose={onClose} onClick={(e) => e.target === ref.current && ref.current.close()}>
      <div className="dialog-body">
        <button className="close" onClick={() => ref.current.close()} aria-label="Close">
          ×
        </button>
        {failed && <p role="alert">Couldn't load this film.</p>}
        {film && (
          <>
            <h2>
              {film.title} {film.year && <span className="year">{film.year}</span>}
            </h2>
            <p className="credits">
              Directed by {film.director.join(", ")}
              {film.cast.length > 0 && <> · {film.cast.join(", ")}</>}
            </p>
            {(film.plot || film.lead).split("\n").map((para, i) => (
              <p key={i}>{para}</p>
            ))}
            <a href={film.url} target="_blank" rel="noreferrer">
              Read on Wikipedia ↗
            </a>
          </>
        )}
      </div>
    </dialog>
  );
}

export default function App() {
  const [query, setQuery] = useState(() => new URLSearchParams(location.search).get("q") ?? "");
  const [openId, setOpenId] = useState(null);
  const { status, data } = useSearch(query);
  const results = data?.results ?? [];
  const top = results[0]?.score || 1;

  useEffect(() => {
    // keep the query in the address bar so a search can be shared as a link
    history.replaceState(null, "", query ? `?q=${encodeURIComponent(query)}` : location.pathname);
  }, [query]);

  return (
    <main className={query.trim() ? "searching" : ""}>
      <div className="aurora" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <header>
        <p className="eyebrow">
          <span className="eyebrow-dot" /> Search engine for half-remembered films
        </p>
        <h1>
          Deja<em>view</em>
        </h1>
        <p className="tagline">Describe a scene, a character or the ending. We'll find the film.</p>
        <label className={status === "loading" ? "search loading" : "search"}>
          <span className="sr-only">Describe a film</span>
          <svg className="search-icon" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" />
          </svg>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="that movie where…"
            maxLength={200}
            autoFocus
          />
        </label>
        {!query.trim() && (
          <div className="examples">
            {EXAMPLES.map((ex) => (
              <button key={ex} onClick={() => setQuery(ex)}>
                {ex}
              </button>
            ))}
          </div>
        )}
      </header>

      <p className="status" aria-live="polite">
        {status === "error" && "Search is unavailable. Is the API running?"}
        {status === "done" && results.length === 0 && "Nothing matched. Try describing a scene, a character or the ending."}
        {status === "done" && results.length > 0 && `${results.length} films · ${data.took_ms} ms`}
      </p>

      <ol className="results">
        {results.map((film, i) => (
          <li key={film.id} style={{ "--i": i }}>
            <button className="card" onClick={() => setOpenId(film.id)} onMouseMove={spotlight}>
              <Poster title={film.title} year={film.year} />
              <div className="card-text">
                <h2>
                  <span className="rank">{i + 1}</span> {film.title}
                </h2>
                <p className="credits">
                  {film.director.join(", ")}
                  {film.cast.length > 0 && <> · {film.cast.slice(0, 3).join(", ")}</>}
                </p>
                <p className="snippet">
                  <Highlight text={film.snippet} query={query} />…
                </p>
                <div className="score" title={`Score ${film.score}`}>
                  <div style={{ width: `${(film.score / top) * 100}%` }} />
                </div>
              </div>
            </button>
          </li>
        ))}
      </ol>

      {openId !== null && <FilmDialog id={openId} onClose={() => setOpenId(null)} />}

      <footer>Film text from Wikipedia (CC BY-SA).</footer>
    </main>
  );
}
