import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { experiences, projects, skillGroups } from './content'
import './App.css'

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
type Repository = { id: number; name: string; description: string | null; url: string; language: string | null; stars: number; updated_at: string; topics: string[] }
type Feed = { repositories: Repository[]; source: 'live' | 'cache' | 'snapshot'; fetched_at: string; message: string | null }
const Arrow = ({ diagonal = false }: { diagonal?: boolean }) => <span aria-hidden="true">{diagonal ? '↗' : '→'}</span>

function ExternalLink({ href, children, className = '' }: { href: string; children: ReactNode; className?: string }) {
  return <a href={href} target="_blank" rel="noreferrer" className={className}>{children}</a>
}

function GithubLab() {
  const [feed, setFeed] = useState<Feed | null>(null)
  const [loading, setLoading] = useState(true)
  const [refresh, setRefresh] = useState(0)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [language, setLanguage] = useState('All languages')
  const [sort, setSort] = useState('updated')
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      setLoading(true)
      setError('')
      try {
        const response = await fetch(`${API_BASE}/api/github`, { signal: controller.signal })
        if (!response.ok) throw new Error('API unavailable')
        const data: Feed = await response.json()
        if (!Array.isArray(data.repositories)) throw new Error('Invalid API response')
        setFeed(data)
      } catch {
        if (controller.signal.aborted) return
        try {
          const response = await fetch('/github-snapshot.json', { signal: controller.signal })
          if (!response.ok) throw new Error('Snapshot unavailable')
          const data: Feed = await response.json()
          if (!Array.isArray(data.repositories)) throw new Error('Invalid snapshot')
          setFeed({ ...data, source: 'snapshot' })
        } catch {
          if (!controller.signal.aborted) setError('The explorer is unavailable. You can still explore my work on GitHub.')
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }
    void load()
    return () => controller.abort()
  }, [refresh])

  const languages = [...new Set(feed?.repositories.map(repo => repo.language).filter((value): value is string => Boolean(value)))].sort()
  const filtered = (feed?.repositories || []).filter(repo =>
    `${repo.name} ${repo.description || ''} ${repo.topics.join(' ')}`.toLowerCase().includes(query.toLowerCase()) &&
    (language === 'All languages' || repo.language === language),
  ).sort((a, b) => sort === 'stars' ? b.stars - a.stars || a.name.localeCompare(b.name) : sort === 'name' ? a.name.localeCompare(b.name) : b.updated_at.localeCompare(a.updated_at))
  const shown = showAll ? filtered : filtered.slice(0, 6)

  return <section id="lab" className="lab section">
    <div className="section-heading"><div><p className="eyebrow">03 / THE LIVE LAB</p><h2>Less telling.<br />More building.</h2></div><p>A little window into what I build.<br />Explore my public repositories, right here.</p></div>
    <div className="pipeline" aria-label="React calls FastAPI, which calls GitHub"><span><i className="dot" /> React</span><span aria-hidden="true">↔</span><span>FastAPI</span><span aria-hidden="true">↔</span><span>GitHub API</span><span className={`feed-status ${feed?.source === 'live' ? 'is-live' : ''}`} role="status">{loading ? 'Connecting…' : feed?.source === 'live' ? 'Live data' : feed?.source === 'cache' ? 'Cached data' : 'Saved snapshot'}</span></div>
    <div className="lab-body">
      <div className="lab-toolbar"><label className="search"><span aria-hidden="true">⌕</span><span className="sr-only">Search repositories</span><input value={query} onChange={e => { setQuery(e.target.value); setShowAll(false) }} placeholder="Find a project, topic, or idea…" /></label><label><span className="sr-only">Repository language</span><select value={language} onChange={e => { setLanguage(e.target.value); setShowAll(false) }}><option>All languages</option>{languages.map(item => <option key={item}>{item}</option>)}</select></label><label><span className="sr-only">Sort repositories</span><select value={sort} onChange={e => setSort(e.target.value)}><option value="updated">Recently updated</option><option value="stars">Most starred</option><option value="name">Name A–Z</option></select></label><button className="refresh" aria-label="Refresh repositories" disabled={loading} onClick={() => setRefresh(value => value + 1)}>↻</button></div>
      <p className="lab-caption" aria-live="polite">{loading ? 'Fetching repositories…' : `${filtered.length} ${filtered.length === 1 ? "repository" : "repositories"} found`}{feed && !loading && <span>Fetched {new Date(feed.fetched_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}{feed.source === 'snapshot' ? ' · Saved data; live backend unavailable' : feed.source === 'cache' ? ' · Served from the API cache' : ' · Public GitHub data'}</span>}</p>
      {error ? <div className="empty-state"><p>{error}</p><ExternalLink href="https://github.com/sparekh14">Visit GitHub <Arrow diagonal /></ExternalLink><button className="text-button" onClick={() => setRefresh(value => value + 1)}>Try again</button></div> : loading ? <div className="repo-grid" aria-label="Loading repositories">{[1, 2, 3].map(item => <div key={item} className="skeleton" />)}</div> : <><div className="repo-grid">{shown.map(repo => <ExternalLink key={repo.id} href={repo.url} className="repo-card"><div className="repo-title"><span aria-hidden="true">⌘</span><h3>{repo.name.replaceAll('-', ' ')}</h3><Arrow diagonal /></div><p>{repo.description || 'An experiment, a project, a new idea. Explore the code on GitHub.'}</p><div className="repo-meta"><span><i className={`language-dot ${repo.language?.toLowerCase()}`} />{repo.language || 'Other'}</span><span>☆ {repo.stars}</span></div></ExternalLink>)}</div>{filtered.length === 0 && <div className="empty-state"><p>No matches yet. Try another search or language.</p><button className="text-button" onClick={() => { setQuery(''); setLanguage('All languages') }}>Clear filters</button></div>}{filtered.length > 6 && <button className="text-button show-more" onClick={() => setShowAll(value => !value)}>{showAll ? 'Show fewer repositories ↑' : `Show all ${filtered.length} repositories ↓`}</button>}</>}
      <details className="under-hood"><summary>Curious how this works? <span aria-hidden="true">+</span></summary><p>React fetches <code>/api/github</code>. My Python backend calls GitHub, keeps a five-minute cache, and sends back just the fields this interface needs. Search and sorting happen in React. If the backend is offline, this page clearly labels a saved snapshot so you can still explore.</p></details>
    </div>
  </section>
}

function App() {
  const [category, setCategory] = useState('All work')
  const [activeExperience, setActiveExperience] = useState(0)
  const [copied, setCopied] = useState(false)
  const [copyError, setCopyError] = useState(false)
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem('samarth-theme') === 'dark' ? 'dark' : 'light' } catch { return 'light' }
  })
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('samarth-theme', theme) } catch { /* Theme works without storage. */ }
  }, [theme])
  useEffect(() => {
    if (!copied) return
    const timeout = window.setTimeout(() => setCopied(false), 2500)
    return () => window.clearTimeout(timeout)
  }, [copied])

  async function copyEmail() {
    try { await navigator.clipboard.writeText('samarth.parekh05@gmail.com'); setCopied(true); setCopyError(false) } catch { setCopyError(true) }
  }

  return <>
    <a className="skip-link" href="#main">Skip to content</a>
    <header className="site-header"><a className="wordmark" href="#home" aria-label="Samarth Parekh home">sp<span>.</span></a><nav aria-label="Main navigation"><a href="#work">Work</a><a href="#experience">Experience</a><a href="#lab">Live lab <i className="dot" /></a></nav><div className="header-actions"><button className="theme-toggle" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}>{theme === 'light' ? '◐' : '☀'}</button><a className="header-contact" href="#contact">Let’s talk <Arrow diagonal /></a></div></header>
    <main id="main">
      <section className="hero section" id="home"><div className="hero-copy"><p className="eyebrow"><span className="line" /> SAMARTH PAREKH / SOFTWARE ENGINEER</p><h1>Thoughtful code.<br />Real-world<br /><em>impact.</em></h1><p className="hero-description">I turn complex problems into useful software.<br className="desktop-break" /> From financial infrastructure to quantum computing,<br className="desktop-break" /> I’m here to build things that matter.</p><div className="hero-actions"><a className="button primary" href="#work">Explore my work <Arrow /></a><a className="button secondary" href="/Samarth_Parekh_resume.pdf" target="_blank" rel="noreferrer">View resume <span aria-hidden="true">↓</span></a></div><div className="hero-note"><span className="location-icon" aria-hidden="true">⌖</span><span>Computer Science @ University of Maryland<br /><span className="muted">Mathematics minor · Class of December 2026</span></span></div></div><div className="hero-visual"><div className="photo-frame"><img src="/images/profile.jpg" alt="Samarth Parekh" width="640" height="800" fetchPriority="high" /><div className="photo-label"><span><i className="dot" /> ALWAYS CURIOUS</span><span>01 — SP</span></div></div><div className="floating-note"><span aria-hidden="true">↗</span><div>From ideas<br /><strong>to something real.</strong></div></div><div className="photo-coordinate">COLLEGE PARK, MARYLAND</div></div></section>
      <div className="experience-strip"><p>PLACES I’VE CONTRIBUTED</p><div><span className="stripe-word">stripe</span><span className="stonex-word">StoneX</span><span className="ionq-word">IonQ</span><span className="fda-word">FDA</span><span>Warriors Legacy Care</span></div></div>
      <section id="work" className="section work"><div className="section-heading"><div><p className="eyebrow">01 / SELECTED WORK</p><h2>Built with purpose.</h2></div><p>Different problems. A shared approach:<br />make something useful, and make it work well.</p></div><div className="filter-tabs" aria-label="Filter projects">{['All work', 'Full stack', 'AI & data'].map(item => <button key={item} onClick={() => setCategory(item)} aria-pressed={category === item} className={category === item ? 'active' : ''}>{item}</button>)}</div><div className="projects-grid" aria-live="polite">{projects.filter(project => category === 'All work' || project.category === category).map(project => <article className="project-card" key={project.name}><div className={`project-art ${project.art}`} aria-hidden="true">{project.art === 'wedding' ? <><div className="wedding-ring ring-one" /><div className="wedding-ring ring-two" /><span className="art-label">BETTER, TOGETHER.</span><div className="art-chip">Shared vendors. Shared savings.</div></> : project.art === 'route' ? <><svg viewBox="0 0 500 240"><path className="map-road" d="M0 60H500M0 140H500M0 220H500M80 0V240M200 0V240M340 0V240M450 0V240" /><path className="map-route" d="M80 180V140Q80 60 160 60H280Q340 60 340 120V180" /><circle cx="80" cy="180" r="9" /><circle cx="340" cy="180" r="9" /></svg><span className="route-chip">A smarter way forward ↗</span></> : project.art === 'cards' ? <><div className="flashcard back-card" /><div className="flashcard front-card"><span>LEARN SOMETHING NEW</span><strong>Small cards.<br />Big ideas.</strong><span>01 / ∞</span></div></> : <><div className="finance-chart"><i /><i /><i /><i /><i /><i /></div><span className="art-label">A CLEARER PICTURE.</span><div className="art-chip">Your money, organized.</div></>}</div><div className="project-content"><div className="project-topline"><span>{project.category.toUpperCase()}</span><span>{project.number}</span></div><h3><ExternalLink href={project.url}>{project.name} <Arrow diagonal /></ExternalLink></h3><p>{project.description}</p><div className="tags">{project.technologies.map(tech => <span key={tech}>{tech}</span>)}</div><ExternalLink className="project-link" href={project.url}>{project.linkLabel} <Arrow /></ExternalLink></div></article>)}</div></section>
      <section id="experience" className="section experience"><div className="section-heading"><div><p className="eyebrow">02 / THE JOURNEY</p><h2>Learning by doing.<br />Building along the way.</h2></div><a className="text-link" href="/Samarth_Parekh_resume.pdf" target="_blank" rel="noreferrer">The full story, on paper <Arrow diagonal /></a></div><div className="experience-layout"><div className="experience-list" aria-label="Experience">{experiences.map((item, index) => <button key={item.company} aria-pressed={activeExperience === index} aria-controls="experience-detail" onClick={() => setActiveExperience(index)} className={activeExperience === index ? 'selected' : ''}><img src={item.logo} alt="" /><div><strong>{item.company}</strong><span>{item.shortDate}</span></div><span aria-hidden="true">↗</span></button>)}</div><article id="experience-detail" aria-live="polite" className="experience-detail"><p className="eyebrow">{experiences[activeExperience].date} · {experiences[activeExperience].location}</p><h3>{experiences[activeExperience].role}</h3><div className="tags">{experiences[activeExperience].technologies.map(item => <span key={item}>{item}</span>)}</div><ul>{experiences[activeExperience].details.map(item => <li key={item}>{item}</li>)}</ul></article></div><div className="skills"><p className="eyebrow">THE TOOLKIT</p>{skillGroups.map(group => <div key={group.name}><h3>{group.name}</h3><p>{group.skills.join(' · ')}</p></div>)}</div></section>
      <GithubLab />
      <section id="contact" className="section contact"><p className="eyebrow">04 / LET’S CONNECT</p><div className="contact-layout"><div><h2>Good things start<br />with a <em>conversation.</em></h2><p>Have an interesting problem, an idea to explore,<br />or just want to say hello? I’d love to hear from you.</p><a className="contact-email" href="mailto:samarth.parekh05@gmail.com">samarth.parekh05@gmail.com <Arrow diagonal /></a><div><button className="text-button" onClick={() => void copyEmail()}>{copied ? '✓ Copied to clipboard' : 'Copy email address'}</button><span className="sr-only" role="status">{copied ? 'Email copied' : copyError ? 'Could not copy. Use the email link above.' : ''}</span>{copyError && <p>Copy unavailable. Use the email link above.</p>}</div></div><div className="contact-links"><ExternalLink href="https://github.com/sparekh14"><span>GitHub</span><Arrow diagonal /></ExternalLink><ExternalLink href="https://www.linkedin.com/in/samarth-parekh/"><span>LinkedIn</span><Arrow diagonal /></ExternalLink><a href="/Samarth_Parekh_resume.pdf" target="_blank" rel="noreferrer"><span>Resume</span><span aria-hidden="true">↓</span></a></div></div></section>
    </main><footer className="site-footer"><a className="wordmark" href="#home">sp<span>.</span></a><p>© {new Date().getFullYear()} Samarth Parekh</p><p>Made with curiosity. Built with React + FastAPI.</p><a href="#home">Back to top ↑</a></footer>
  </>
}

export default App
