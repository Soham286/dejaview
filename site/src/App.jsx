import { AnimatePresence, motion } from "motion/react";
import { useEffect, useState } from "react";
import BlurText from "./bits/BlurText.jsx";
import CountUp from "./bits/CountUp.jsx";
import LightRays from "./bits/LightRays.jsx";
import Noise from "./bits/Noise.jsx";
import SpotlightCard from "./bits/SpotlightCard.jsx";

const REPO = "https://github.com/Soham286/dejaview";
const AMBER = "#f2b04a";

// real queries and scores from the Dejaview API
const DEMOS = [
  { query: "thieves sneak into dreams to plant an idea", film: "Inception", meta: "2010 · Christopher Nolan", score: "0.66", next: "Army of Thieves", nextScore: "0.57" },
  { query: "man who can't make new memories hunts his wife's killer", film: "Memento", meta: "2000 · Christopher Nolan", score: "0.67", next: "Longlegs", nextScore: "0.53" },
  { query: "lonely garbage robot on an abandoned earth falls in love", film: "WALL-E", meta: "2008 · Andrew Stanton", score: "0.69", next: "Lost in Space", nextScore: "0.46" },
];

const RESULTS = [
  ["Inception", "2010 · Christopher Nolan"],
  ["Army of Thieves", "2021 · Matthias Schweighöfer"],
  ["Aladdin and the King of Thieves", "1996 · Tad Stones"],
  ["Armored", "2009 · Nimród Antal"],
  ["Dreamscape", "1984 · Joseph Ruben"],
  ["Thieves", "1977 · John Berry"],
  ["The Instigators", "2024 · Doug Liman"],
  ["Dreams", "1990 · Akira Kurosawa"],
  ["Total Recall", "2012 · Len Wiseman"],
  ["Henry's Crime", "2010 · Malcolm Venville"],
];

// public-domain stills, loaded straight from Wikimedia Commons (it allows hotlinking)
const C = "https://upload.wikimedia.org/wikipedia/commons/";
const STILL = {
  moon: C + "d/db/A_Trip_to_the_Moon_%28Le_Voyage_dans_la_Lune%29.jpg",
  metropolis: C + "f/f9/Metropolis_%281927%29_-_Hel.jpg",
  nosferatu: C + "thumb/f/f2/Nosferatu_%281922%29_-_Count_Orlok_Standing_In_A_Wooden_Doorway_%28Greyscale%29.png/960px-Nosferatu_%281922%29_-_Count_Orlok_Standing_In_A_Wooden_Doorway_%28Greyscale%29.png",
  caligari: C + "thumb/c/c6/Publicity_still_for_The_Cabinet_of_Dr._Caligari_%281920%29_03.jpg/960px-Publicity_still_for_The_Cabinet_of_Dr._Caligari_%281920%29_03.jpg",
  general: C + "thumb/f/fb/Buster_Keaton_on_the_cow-catcher_in_The_General.jpg/960px-Buster_Keaton_on_the_cow-catcher_in_The_General.jpg",
  goldrush: C + "thumb/f/ff/Chaplin_the_gold_rush_boot.jpg/960px-Chaplin_the_gold_rush_boot.jpg",
};
const STILLS = [
  ["moon", "A Trip to the Moon", 1902],
  ["caligari", "The Cabinet of Dr. Caligari", 1920],
  ["nosferatu", "Nosferatu", 1922],
  ["goldrush", "The Gold Rush", 1925],
  ["general", "The General", 1926],
  ["metropolis", "Metropolis", 1927],
];

const STACK = [
  ["python", "Python"], ["sqlite", "SQLite"], ["fastapi", "FastAPI"], ["pytorch", "PyTorch"],
  ["hugging-face", "Hugging Face"], ["react", "React"], ["vitejs", "Vite"], ["wikipedia", "Wikipedia"],
];

const FAQ = [
  ["Can I try Dejaview without installing it?", "Not yet. Dejaview runs on your own computer; there is no hosted version. The code is public on GitHub."],
  ["Which films can it find?", "12,543 American films from Wikipedia's yearly lists, 1970 to 2025, plus a few older ones those lists link to. Films from other countries are not indexed yet."],
  ["How long does Dejaview take to set up?", "About nine hours of computer time on a laptop, mostly unattended: five to crawl, an hour and a half to parse, three to embed the plots."],
  ["Does Dejaview send my searches anywhere?", "No. The index, the ranking and the model all run locally. The model downloads once, about 90 MB."],
  ["Why does a film title sometimes win?", "Titles count three times in the index, so \"weatherman\" can rank The Weather Man above Groundhog Day. Lowering that weight is the next change."],
];

const rise = {
  initial: { opacity: 0, y: 28 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.3 },
  transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] },
};

function useTyped(text, speed = 38) {
  const [n, setN] = useState(0);
  useEffect(() => {
    setN(0);
    const id = setInterval(() => setN((v) => (v >= text.length ? v : v + 1)), speed);
    return () => clearInterval(id);
  }, [text, speed]);
  return [text.slice(0, n), n >= text.length];
}

function HeroSearch() {
  const [i, setI] = useState(0);
  const demo = DEMOS[i];
  const [typed, done] = useTyped(demo.query);
  useEffect(() => {
    if (!done) return;
    const id = setTimeout(() => setI((v) => (v + 1) % DEMOS.length), 3600);
    return () => clearTimeout(id);
  }, [done]);

  return (
    <div className="hs">
      <div className="hs__box">
        <SearchIcon />
        <span className="hs__text">{typed}<span className="caret" /></span>
        <kbd>Enter</kbd>
      </div>
      <div className="hs__results">
        <AnimatePresence mode="wait">
          {done && (
            <motion.div key={demo.film} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.4 }}>
              <div className="hs__row hs__row--top">
                <span className="rank">1</span>
                <span className="hs__film"><b>{demo.film}</b><small>{demo.meta}</small></span>
                <span className="score">{demo.score}</span>
              </div>
              <div className="hs__row">
                <span className="rank">2</span>
                <span className="hs__film">{demo.next}</span>
                <span className="score score--dim">{demo.nextScore}</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function SearchIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
    </svg>
  );
}

function Nav() {
  return (
    <header className="nav">
      <a className="logo" href="#top"><span className="logo__mark">D</span>Dejaview</a>
      <nav className="nav__links" aria-label="Sections">
        <a href="#demo">Demo</a><a href="#how">How it works</a><a href="#results">Results</a><a href="#faq">Questions</a>
      </nav>
      <a className="btn btn--small" href={REPO}>Get the code</a>
    </header>
  );
}

function Hero() {
  return (
    <section className="hero" id="top">
      <img className="hero__still" src={STILL.moon} alt="" />
      <div className="hero__shade" />
      <div className="hero__rays"><LightRays raysOrigin="top-center" raysColor={AMBER} raysSpeed={0.6} lightSpread={0.9} rayLength={2.2} followMouse mouseInfluence={0.08} intensity={0.9} /></div>
      <div className="hero__inner">
        <motion.p className="eyebrow" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>12,543 American films · 1970 to 2025</motion.p>
        <div className="hero__title" role="heading" aria-level={1}>
          <BlurText text="Film search for vague memories" delay={90} animateBy="words" direction="top" trigger="load" />
        </div>
        <motion.p className="hero__sub" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7, duration: 0.6 }}>
          Describe a scene, a character or the ending. Dejaview ranks films by keywords and by meaning, and puts the right one first in 66% of tests.
        </motion.p>
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.9, duration: 0.6 }}>
          <HeroSearch />
        </motion.div>
        <motion.div className="hero__ctas" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.1 }}>
          <a className="btn" href={REPO}>Get the code</a>
          <a className="btn btn--ghost" href="#how">See how it works</a>
        </motion.div>
      </div>
    </section>
  );
}

function FilmStrip() {
  const frames = [...STILLS, ...STILLS];
  return (
    <section className="strip" aria-label="Classic film stills">
      <div className="strip__track">
        {frames.map(([file, title, year], k) => (
          <figure className="frame" key={k} aria-hidden={k >= STILLS.length}>
            <img src={STILL[file]} alt={k < STILLS.length ? `${title}, ${year}` : ""} loading="lazy" />
            <figcaption>{title} <span>{year}</span></figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}

function Demo() {
  const [active, setActive] = useState(0);
  return (
    <section className="section" id="demo">
      <motion.div className="head" {...rise}>
        <p className="eyebrow">The app</p>
        <h2>Ranked films beside the plot that matched</h2>
        <p className="lede">Type what you remember. Dejaview scores every candidate, lists the best ten and opens the plot with your words marked.</p>
      </motion.div>
      <motion.div {...rise}>
        <SpotlightCard className="app" spotlightColor={AMBER} intensity={0.12} spotlightSize={520}>
          <div className="app__bar">
            <span className="dots"><i /><i /><i /></span>
            <div className="app__search"><SearchIcon /> thieves sneak into dreams to plant an idea</div>
          </div>
          <div className="app__body">
            <ol className="app__list">
              {RESULTS.map(([t, m], k) => (
                <li key={t}>
                  <button className={k === active ? "is-active" : ""} onClick={() => setActive(k)} type="button">
                    <span className="rank">{k + 1}</span>
                    <span className="hs__film"><b>{t}</b><small>{m}</small></span>
                  </button>
                </li>
              ))}
            </ol>
            <article className="app__doc">
              {active === 0 ? (
                <>
                  <p className="doc__meta">Inception · 2010 · Plot</p>
                  <h3>Inception</h3>
                  <p>Dom Cobb and Arthur are professional <mark>thieves</mark> who perform corporate espionage using experimental <mark>dream</mark>-sharing technology to infiltrate their targets' subconscious and extract information.</p>
                  <p>Their latest target Saito offers to hire Cobb for the ostensibly impossible job of performing "inception": implanting Robert Fischer with the <mark>idea</mark> to dissolve his father's conglomerate.</p>
                  <div className="doc__scores"><span>Keywords <b>12.9</b></span><span>Meaning <b>0.44</b></span><span className="hl">Score <b>0.66</b></span></div>
                </>
              ) : (
                <>
                  <p className="doc__meta">{RESULTS[active][1]}</p>
                  <h3>{RESULTS[active][0]}</h3>
                  <p className="muted">Ranked {active + 1} of 10 for this description. In the app, the plot opens here with the matching words marked.</p>
                </>
              )}
            </article>
          </div>
        </SpotlightCard>
      </motion.div>
    </section>
  );
}

function Statement() {
  return (
    <section className="statement">
      <div className="statement__title" role="heading" aria-level={2}>
        <BlurText text="That movie where…" delay={120} animateBy="words" direction="bottom" />
      </div>
      <motion.p className="lede" {...rise}>You remember the scene, not the title. Most search boxes want the title's words; Dejaview starts from the scene.</motion.p>
    </section>
  );
}

function How() {
  return (
    <section className="section" id="how">
      <motion.div className="head" {...rise}>
        <p className="eyebrow">How it works</p>
        <h2>Built in 3 steps, from scratch</h2>
      </motion.div>
      <div className="cards">
        <motion.div {...rise}>
          <SpotlightCard className="card" spotlightColor={AMBER}>
            <span className="card__num">01</span>
            <h3>Crawl</h3>
            <p>A polite crawler reads one Wikipedia page a second across 56 film lists and resumes where it stopped.</p>
            <div className="big"><CountUp to={12543} separator="," duration={2} /><small>films from 12,763 pages</small></div>
          </SpotlightCard>
        </motion.div>
        <motion.div {...rise} transition={{ ...rise.transition, delay: 0.1 }}>
          <SpotlightCard className="card" spotlightColor={AMBER}>
            <span className="card__num">02</span>
            <h3>Index</h3>
            <p>Each word points to the films using it, so a search reads only its own words.</p>
            <ul className="steps">
              <li>Lowercase, drop accents</li><li>Skip the, and, of</li><li>Heists becomes heist</li><li>Count titles three times</li>
            </ul>
            <div className="big"><CountUp to={87771} separator="," duration={2} /><small>word lists</small></div>
          </SpotlightCard>
        </motion.div>
        <motion.div {...rise} transition={{ ...rise.transition, delay: 0.2 }}>
          <SpotlightCard className="card" spotlightColor={AMBER}>
            <span className="card__num">03</span>
            <h3>Rank</h3>
            <p>BM25 scores the keywords; MiniLM reads every plot, so a description with no shared words still finds the film.</p>
            <div className="mini">
              <p className="mini__q">dinosaurs escape a theme park</p>
              <p><span>Jurassic Park, 1993</span><b>0.80</b></p>
              <p><span>Jurassic World, 2015</span><b>0.71</b></p>
              <p><span>The Lost World, 1997</span><b>0.69</b></p>
            </div>
          </SpotlightCard>
        </motion.div>
      </div>
    </section>
  );
}

const BARS = [["Keywords only", 54], ["Weight 0.2", 58], ["Weight 0.4", 60], ["Weight 0.6, used", 66]];

function Results() {
  return (
    <section className="section" id="results">
      <motion.div className="head" {...rise}>
        <p className="eyebrow">Evaluation</p>
        <h2>Tested on 50 film descriptions</h2>
        <p className="lede">Each description avoids the title and the names, and is tied to one Wikipedia page.</p>
      </motion.div>
      <div className="stats">
        {[[66, "%", "right film first"], [72, "%", "in the top 3"], [90, "%", "in the top 10"], [30, " ms", "median search time"]].map(([n, s, l]) => (
          <motion.div className="stat" key={l} {...rise}>
            <span className="stat__n"><CountUp to={n} duration={1.6} />{s}</span>
            <span className="stat__l">{l}</span>
          </motion.div>
        ))}
      </div>
      <motion.div className="chart" {...rise}>
        <p className="chart__t">Right film first, by meaning weight</p>
        {BARS.map(([label, v], k) => (
          <div className={`bar${k === BARS.length - 1 ? " bar--hl" : ""}`} key={label}>
            <span className="bar__l">{label}</span>
            <span className="bar__track">
              <motion.span className="bar__fill" initial={{ width: 0 }} whileInView={{ width: `${v}%` }} viewport={{ once: true }} transition={{ duration: 1.1, delay: k * 0.12, ease: [0.22, 1, 0.36, 1] }} />
            </span>
            <span className="bar__v">{v}%</span>
          </div>
        ))}
        <p className="muted small">The blend was tuned on these same 50, so a fresh set will likely score a little lower.</p>
      </motion.div>
    </section>
  );
}

function Stack() {
  return (
    <section className="section" id="stack">
      <motion.div className="head" {...rise}>
        <p className="eyebrow">Stack</p>
        <h2>Runs on Python and React, on your own computer</h2>
        <p className="lede">The crawler, index and ranking use only Python's standard library and SQLite. The model runs locally, so a search never leaves your machine.</p>
      </motion.div>
      <div className="logos">
        {STACK.map(([icon, name], k) => (
          <motion.div className="logo-tile" key={icon} initial={{ opacity: 0, scale: 0.9 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} transition={{ delay: k * 0.05 }}>
            <img src={`icons/${icon}.svg`} alt="" width="32" height="32" /><span>{name}</span>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

function Faq() {
  return (
    <section className="section section--narrow" id="faq">
      <motion.div className="head" {...rise}>
        <p className="eyebrow">Questions</p>
        <h2>What people ask about Dejaview</h2>
      </motion.div>
      <div className="faq">
        {FAQ.map(([q, a]) => (
          <details key={q}><summary>{q}</summary><p>{a}</p></details>
        ))}
      </div>
      <p className="muted">Something not covered? <a className="link" href={`${REPO}/issues`}>Open an issue on GitHub</a></p>
    </section>
  );
}

function Close() {
  return (
    <section className="close">
      <img className="close__still" src={STILL.metropolis} alt="" loading="lazy" />
      <div className="close__shade" />
      <motion.div className="close__inner" {...rise}>
        <h2>Find the film you half remember</h2>
        <a className="btn" href={REPO}>Get the code</a>
      </motion.div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <a className="logo" href="#top"><span className="logo__mark">D</span>Dejaview</a>
      <p>
        Film text from Wikipedia, CC BY-SA 4.0. Stills from A Trip to the Moon, The Cabinet of Dr. Caligari, Nosferatu, The Gold Rush, The General and Metropolis are in the public domain, via Wikimedia Commons. Animated parts from React Bits. Product names and logos are trademarks of their owners.
      </p>
    </footer>
  );
}

export default function App() {
  return (
    <>
      <Noise fixed opacity={0.035} dust={0.15} scratches={0.08} flicker={0.02} />
      <Nav />
      <main>
        <Hero />
        <FilmStrip />
        <Demo />
        <Statement />
        <How />
        <Results />
        <Stack />
        <Faq />
        <Close />
      </main>
      <Footer />
    </>
  );
}
